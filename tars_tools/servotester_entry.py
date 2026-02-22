import sys
import os
from pathlib import Path

def main():
    repo_root = Path(__file__).parent.parent
    src_path = repo_root / "src"

    if not src_path.exists():
        print(f"Error: src/ not found at {src_path}")
        print("tars-servo-tester requires the full repo:")
        print("  git clone https://github.com/latishab/tars.git")
        sys.exit(1)

    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    os.chdir(src_path)

    script = src_path / "app-servotester.py"
    with open(script) as f:
        code = compile(f.read(), str(script), "exec")
    exec(code, {"__name__": "__main__", "__file__": str(script)})

if __name__ == "__main__":
    main()
