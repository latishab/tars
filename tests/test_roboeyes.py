#!/usr/bin/env python3
"""
Test script for RoboEyes module with breathing animation.
Run this to see the eyes in action with all states and expressions.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

import pytest
pygame = pytest.importorskip("pygame", reason="pygame not installed")

from modules.modules_roboeyes import RoboEyes, Mood, EyeState

def main():
    pygame.init()

    screen = pygame.display.set_mode((800, 480))
    pygame.display.set_caption("TARS RoboEyes Test - Press keys to test features")
    clock = pygame.time.Clock()

    eyes = RoboEyes(800, 480)

    running = True
    show_help = True

    print("TARS RoboEyes Test Script")
    print("=" * 60)
    print("STATE CONTROLS:")
    print("  1 - IDLE state (with breathing)")
    print("  2 - LISTENING state")
    print("  3 - THINKING state")
    print("  4 - SPEAKING state")
    print()
    print("MOOD CONTROLS:")
    print("  Q - HAPPY mood")
    print("  W - ANGRY mood")
    print("  E - TIRED mood")
    print("  R - SURPRISED mood")
    print("  T - CONFUSED mood")
    print("  Y - DEFAULT mood")
    print()
    print("ANIMATIONS:")
    print("  A - Laugh animation")
    print("  S - Confused animation")
    print("  D - Manual blink")
    print()
    print("SETTINGS:")
    print("  B - Toggle breathing animation")
    print("  I - Toggle idle drift")
    print("  Space - Simulate audio (when in speaking state)")
    print()
    print("ESC - Exit")
    print("=" * 60)

    audio_level = 0.0
    simulate_audio = False
    audio_timer = 0.0

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                # State controls
                elif event.key == pygame.K_1:
                    eyes.set_state("idle")
                    print("State: IDLE (breathing will start after 0.5s)")
                elif event.key == pygame.K_2:
                    eyes.set_state("listening")
                    print("State: LISTENING")
                elif event.key == pygame.K_3:
                    eyes.set_state("thinking")
                    print("State: THINKING")
                elif event.key == pygame.K_4:
                    eyes.set_state("speaking")
                    simulate_audio = True
                    print("State: SPEAKING")

                # Mood controls
                elif event.key == pygame.K_q:
                    eyes.set_mood(Mood.HAPPY)
                    print("Mood: HAPPY")
                elif event.key == pygame.K_w:
                    eyes.set_mood(Mood.ANGRY)
                    print("Mood: ANGRY")
                elif event.key == pygame.K_e:
                    eyes.set_mood(Mood.TIRED)
                    print("Mood: TIRED")
                elif event.key == pygame.K_r:
                    eyes.set_mood(Mood.SURPRISED)
                    print("Mood: SURPRISED")
                elif event.key == pygame.K_t:
                    eyes.set_mood(Mood.CONFUSED)
                    print("Mood: CONFUSED")
                elif event.key == pygame.K_y:
                    eyes.set_mood(Mood.DEFAULT)
                    print("Mood: DEFAULT")

                # Animation controls
                elif event.key == pygame.K_a:
                    eyes.anim_laugh(0.5)
                    print("Animation: LAUGH")
                elif event.key == pygame.K_s:
                    eyes.anim_confused(0.5)
                    print("Animation: CONFUSED")
                elif event.key == pygame.K_d:
                    eyes.blink()
                    print("Animation: BLINK")

                # Settings controls
                elif event.key == pygame.K_b:
                    eyes._breathing_enabled = not eyes._breathing_enabled
                    print(f"Breathing: {'ENABLED' if eyes._breathing_enabled else 'DISABLED'}")
                elif event.key == pygame.K_i:
                    eyes._idle_mode = not eyes._idle_mode
                    print(f"Idle drift: {'ENABLED' if eyes._idle_mode else 'DISABLED'}")

                # Audio simulation
                elif event.key == pygame.K_SPACE:
                    simulate_audio = not simulate_audio
                    print(f"Audio simulation: {'ON' if simulate_audio else 'OFF'}")

        # Simulate audio level when speaking
        if simulate_audio:
            audio_timer += dt * 5
            audio_level = abs(pygame.math.Vector2(0.5, 0).rotate(audio_timer * 100).x)
            eyes.set_audio_level(audio_level, "test")
        else:
            eyes.set_audio_level(0.0, "none")

        # Update eyes
        eyes.update(dt)

        # Draw
        screen.fill((13, 17, 23))
        eyes.draw(screen)

        # Draw help text
        if show_help:
            font = pygame.font.Font(None, 20)
            help_text = font.render("Press keys to test | ESC to exit | See terminal for controls", True, (100, 150, 200))
            screen.blit(help_text, (10, 10))

        # Draw current state info
        font = pygame.font.Font(None, 24)
        state_text = font.render(f"State: {eyes._state.value.upper()}", True, (0, 206, 209))
        screen.blit(state_text, (10, 450))

        mood_text = font.render(f"Mood: {eyes._mood.name}", True, (0, 206, 209))
        screen.blit(mood_text, (200, 450))

        breathing_text = font.render(f"Breathing: {'ON' if eyes._breathing_enabled else 'OFF'}", True, (0, 206, 209))
        screen.blit(breathing_text, (400, 450))

        pygame.display.flip()

    pygame.quit()
    print("Test complete")

if __name__ == "__main__":
    main()
