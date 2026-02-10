# Guidelines for Claude Code

## Documentation Style

### Writing Style
- **No emojis** in any documentation files
- **No [NEW] markers** or similar annotations
- **No "vs" comparisons** unless explicitly requested
- **Concise and technical** - no fluff or unnecessary explanations
- **Factual only** - describe what exists, not why it's "good" or "bad"

### Structure
- Start with practical information
- Code examples should be minimal and direct
- No motivational or sales language
- No bullet points explaining benefits unless requested

### What NOT to Include
- Emoji symbols (✅ ❌ ⚡ 🚀 etc.)
- Explanatory sections like "Why X?" unless asked
- Comparison tables between old and new unless requested
- "Benefits" sections
- Marketing language ("Amazing!", "Powerful!", etc.)

### What TO Include
- Clear technical specifications
- Code examples
- Configuration options
- Troubleshooting steps
- API references

## Examples

### Bad (Don't Do This)
```markdown
# Amazing New Feature! 🚀

## Why gRPC? ⚡

gRPC is **amazing** because:
- ✅ Super fast (5-10ms)
- ✅ Type-safe
- ✅ Streaming support

## Migration Benefits

You'll love these improvements:
- 42ms faster responses!
- Better developer experience!
```

### Good (Do This)
```markdown
# gRPC Implementation

## API

Available RPCs:
- Health() - Get system status
- Move(movement, speed) - Execute movement
- CaptureCamera(width, height, quality) - Capture frame

## Configuration

```bash
python tars_daemon.py --grpc-port 50051
```

## Usage

```python
from tars_sdk import TarsClient
client = TarsClient("100.64.0.2:50051")
client.move("wave_right")
```
```

## File Updates

When updating existing documentation:
1. Remove all emojis
2. Remove [NEW] or similar markers
3. Remove comparison sections unless they serve a technical purpose
4. Keep only factual, technical content
5. Preserve code examples and configuration details

## Commit Messages

- No emojis
- Imperative mood: "Add gRPC support" not "Added gRPC support"
- One line summary, optional detailed explanation below

## Code Comments

- Minimal comments
- Explain "why" not "what" when needed
- No ASCII art or decorative elements
- No TODO comments (use issue tracker)
