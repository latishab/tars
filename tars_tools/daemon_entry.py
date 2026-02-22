import sys
import os
from pathlib import Path

def main():
    # Ensure src/ is on the path so daemon modules resolve correctly
    repo_root = Path(__file__).parent.parent
    src_path = repo_root / src
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    os.chdir(repo_root)

    import tars_daemon
    tars_daemon.main()

if __name__ == __main__:
    main()
