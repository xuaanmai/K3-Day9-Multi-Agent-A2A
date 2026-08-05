"""Validate all official outputs without modifying or packaging them."""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_repository import DataRepository
from src.output_validator import validate_output_directory


def main() -> int:
    report = validate_output_directory(
        output_dir=ROOT / "output",
        input_dir=ROOT / "input",
        data_repository=DataRepository(ROOT / "data"),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
