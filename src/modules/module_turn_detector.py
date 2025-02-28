#!/usr/bin/env python3
"""
module_turn_detector.py

Turn Detector module for TARS-AI Application.

This module integrates the turn-detector model ("turnsense") using ONNX Runtime.
It expects the input to be a conversation list containing a 3-turn context:
    user - TARS - user (current utterance)

This module returns only the EOU probability (i.e. the probability for the EOU class)
which will be used in module_stt.py to decide when TARS should start talking.

Installation requirements:
    pip install transformers onnxruntime numpy huggingface_hub

NOTE: This module will later be integrated with Silero VAD in module_stt.py.
"""

import onnxruntime as ort
import numpy as np
import time
from transformers import AutoTokenizer
from huggingface_hub import hf_hub_download

from modules.module_messageQue import queue_message

# Model configuration
MODEL_ID = "latishab/turnsense"
MODEL_FILENAME = "model_quantized.onnx"

# Load tokenizer
queue_message("INFO: Loading turn-detector tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

# Download and load the ONNX model
queue_message("INFO: Downloading turn-detector model...")
model_path = hf_hub_download(repo_id=MODEL_ID, filename=MODEL_FILENAME)
queue_message("INFO: Creating ONNX Runtime session for turn-detector model...")
session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])


def format_conversation(conversation: list) -> str:
    """
    Format a conversation (list of turns) into a single text string.
    Each turn is a dictionary with keys:
      - role (either "user" or "assistant")
      - content (the text of the turn)
    """
    formatted_text = ""
    for turn in conversation:
        role = turn.get("role")
        content = turn.get("content", "")
        if role == "user":
            formatted_text += f"<|user|> {content} <|im_end|> "
        elif role == "assistant":
            formatted_text += f"<|assistant|> {content} <|im_end|> "
    return formatted_text


def get_three_turn_context(conversation: list) -> str:
    """
    Given a conversation list, extract the last 3 turns in a user-TARS-user pattern.
    If the conversation is longer than 3 turns, only the last 3 turns are used.
    """
    if len(conversation) >= 3:
        three_turns = conversation[-3:]
    else:
        three_turns = conversation
    return format_conversation(three_turns)


def predict_eou_probability(conversation: list) -> float:
    """
    Predict the End-of-Turn (EOU) probability given a conversation list.

    The conversation should have a 3-turn rolling context in the order:
    user -> TARS -> user (current utterance).

    This function returns only the EOU probability (a float between 0 and 1).
    """
    input_text = get_three_turn_context(conversation)
    
    # Tokenize the input text
    inputs = tokenizer(
        input_text,
        return_tensors="np",
        truncation=True,
        padding=True,
        max_length=128
    )
    
    # Run inference through the ONNX session
    ort_inputs = {
        'input_ids': inputs['input_ids'].astype(np.int64),
        'attention_mask': inputs['attention_mask'].astype(np.int64)
    }
    probabilities = session.run(None, ort_inputs)[0]
    
    # The EOU class is at index 1
    eou_probability = float(probabilities[0, 1])
    return eou_probability


class EOUDetector:
    """
    A pipeline-like interface for detecting End-of-Turn (EOU) probability using the turn-detector model.
    
    This class provides a callable interface that accepts a conversation list (3-turn context)
    and returns the EOU probability.
    """
    def __init__(self, model_path: str = model_path, tokenizer_obj=tokenizer):
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.tokenizer = tokenizer_obj
    
    def __call__(self, conversation: list) -> float:
        """
        Run the EOU detection given a conversation list.
        The conversation should be in the form of a 3-turn context: user -> TARS -> user.

        Returns:
            float: EOU probability.
        """
        input_text = get_three_turn_context(conversation)
        inputs = self.tokenizer(
            input_text,
            return_tensors="np",
            truncation=True,
            padding=True,
            max_length=128
        )
        ort_inputs = {
            'input_ids': inputs['input_ids'].astype(np.int64),
            'attention_mask': inputs['attention_mask'].astype(np.int64)
        }
        probabilities = self.session.run(None, ort_inputs)[0]
        eou_probability = float(probabilities[0, 1])
        return eou_probability

    def format_conversation(self, conversation: list) -> str:
        """
        Format a conversation list for inference.
        """
        return format_conversation(conversation)