from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap() -> None:
    root = Path(__file__).resolve().parent
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def main() -> None:
    _bootstrap()
    from axiom.web.app import main as web_main

    web_main()


if __name__ == "__main__":
    main()
