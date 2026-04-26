import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def run() -> None:
    from spending_visualizer.ui.app import main

    main()


if __name__ == "__main__":
    run()
