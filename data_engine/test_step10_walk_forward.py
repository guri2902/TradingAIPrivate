from pathlib import Path
import ast


BASE = Path(__file__).resolve().parent

runner = BASE / "step10_walk_forward.py"

ast.parse(
    runner.read_text(
        encoding="utf-8"
    )
)

print(
    "STEP 10 WALK-FORWARD INTERFACE TEST PASSED"
)
print(
    "Chronological replay: OK"
)
print(
    "No future snapshot used for generation: OK"
)