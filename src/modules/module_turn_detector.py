#!/usr/bin/env python3
"""
module_turn_detector.py

Turn Detector module for TARS-AI Application with adaptive thresholding and VAD integration.
"""

import onnxruntime as ort
import numpy as np
import re
from transformers import AutoTokenizer
from huggingface_hub import hf_hub_download
from typing import Tuple, Dict

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

class EOUDetector:
    def __init__(self, model_path: str = model_path, tokenizer_obj=tokenizer):
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.tokenizer = tokenizer_obj
        
        # Compile regex patterns for utterance analysis
        self.hesitation_pattern = re.compile(r'\b(um|uh|er|hmm|well\.\.\.)\b', re.IGNORECASE)
        self.uncertainty_pattern = re.compile(
            r'\b(maybe|perhaps|probably|might|could be|not sure|i think|possibly)\b', 
            re.IGNORECASE
        )
        # Add specific pattern for trailing ellipsis
        self.ellipsis_pattern = re.compile(r'\.{3,}$|…$')
        # Modify complete pattern to exclude ellipsis
        self.complete_pattern = re.compile(r'[.!?]$')
        
    def analyze_utterance(self, text: str) -> Dict[str, bool]:
        """Analyze utterance characteristics."""
        words = text.split()
        text = text.strip()
        
        # Check for trailing ellipsis first
        has_ellipsis = bool(self.ellipsis_pattern.search(text))
        
        return {
            'short_utterance': len(words) <= 2,
            'hesitation': bool(self.hesitation_pattern.search(text)),
            'complete': bool(self.complete_pattern.search(text)) and not has_ellipsis,
            'uncertainty': bool(self.uncertainty_pattern.search(text)),
            'trailing_ellipsis': has_ellipsis
        }

    def calculate_eou_probability(self, conversation: list) -> float:
        """Calculate raw EOU probability from the model."""
        input_text = self.format_conversation(conversation)
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
        return float(probabilities[0, 1])

    def __call__(self, conversation: list) -> float:
        """
        Simplified interface that returns only the EOU probability.
        The VAD system will handle silence durations based on this probability.
        """
        # Get the raw model probability
        eou_probability = self.calculate_eou_probability(conversation)
        
        # Apply utterance-based adjustments
        if conversation:
            current_utterance = conversation[-1]['content']
            features = self.analyze_utterance(current_utterance)
            
            # Apply adjustments with stronger emphasis on incomplete utterances
            if features['trailing_ellipsis']:
                eou_probability *= 0.3  # Significant reduction for trailing ellipsis
            if features['short_utterance']:
                eou_probability *= 0.85  # Reduce probability for short utterances
            if features['hesitation']:
                eou_probability *= 0.9   # Reduce probability for hesitations
            if features['complete']:
                eou_probability *= 1.15  # Increase probability for complete utterances
            if features['uncertainty']:
                eou_probability *= 0.95  # Slightly reduce probability for uncertainty
                
            # Additional compound reduction for incomplete thoughts
            if features['trailing_ellipsis'] and (features['short_utterance'] or features['hesitation']):
                eou_probability *= 0.8  # Further reduction for combinations
                
            # Clamp final probability between 0 and 1
            eou_probability = max(0.0, min(1.0, eou_probability))

            queue_message(f"DEBUG: EOU PROBABILITY IS {eou_probability:.4f}, "f"{'CONTINUE LISTENING' if eou_probability < 0.6 else 'PROCESSING RESPONSE'}")
            
        return eou_probability

    def format_conversation(self, conversation: list) -> str:
        """Format conversation for model input."""
        formatted_text = ""
        for turn in conversation:
            role = turn.get("role")
            content = turn.get("content", "")
            if role == "user":
                formatted_text += f"<|user|> {content} <|im_end|> "
            elif role == "assistant":
                formatted_text += f"<|assistant|> {content} <|im_end|> "
        return formatted_text