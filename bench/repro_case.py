"""Repro: run rollout on a single case by id, across all case suites.

Usage:
    TARGET_BACKEND=claude_chat ... python bench/repro_case.py TG02-plan-churn-trigger

Searches every bench/cases/<skill>/items.json for the id, picks the
skill file from the case's own ``skill`` field (falling back to the
suite directory name), runs one rollout, prints the score, and exits
0 on hard-pass, 2 on failure.
"""
from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

# Windows 控制台默认 cp936，回复含 ✅/▌ 等 glyph 时会 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from bench.kidsys.dataloader import _load_cases_json, _normalize_case
from bench.kidsys.rollout import _rollout_one, resolve_skill_path

_CASES_ROOT = _REPO_ROOT / "bench" / "cases"


def discover_all_cases(cases_root: Path) -> list[tuple[str, dict]]:
    """Yield (suite, case) pairs from every bench/cases/<skill>/items.json."""
    found: list[tuple[str, dict]] = []
    if not cases_root.is_dir():
        return found
    for items_file in sorted(cases_root.glob("*/items.json")):
        suite = items_file.parent.name
        try:
            raw_items = _load_cases_json(items_file)
        except (ValueError, OSError):
            continue
        for raw in raw_items:
            if isinstance(raw, dict):
                found.append((suite, _normalize_case(raw, suite)))
    return found


def pick_skill_file(case: dict, suite: str) -> Path:
    """Resolve the SKILL.md for a case.

    Order: the case's own ``skill`` field (short slug or ``kid-*`` full
    name) → the suite directory name → menu as last resort. Flow suites
    resolve per case inside ``_maybe_override_skill``; the file picked
    here is only the fallback.
    """
    for slug in (case.get("skill"), suite, "menu"):
        if not slug:
            continue
        try:
            return resolve_skill_path(str(slug))
        except KeyError:
            continue
    return resolve_skill_path("menu")


def main(case_id: str) -> int:
    all_cases = discover_all_cases(_CASES_ROOT)
    target = next(
        ((suite, case) for suite, case in all_cases if str(case.get("id")) == case_id),
        None,
    )
    if target is None:
        print(f"[!] case {case_id!r} not found under {_CASES_ROOT}")
        return 1
    suite, case = target

    skill_file = pick_skill_file(case, suite)
    if not skill_file.exists():
        print(f"[!] skill file not found: {skill_file}")
        return 1
    skill_content = skill_file.read_text(encoding="utf-8")

    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = _REPO_ROOT / "bench/reports" / f"repro-{case_id}-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    pred_dir = run_dir / "predictions"
    pred_dir.mkdir(exist_ok=True)

    print(f"[*] suite      = {suite}")
    print(f"[*] skill_file = {skill_file}")

    result = _rollout_one(
        item=case,
        skill_content=skill_content,
        prediction_dir=pred_dir,
        max_completion_tokens=4096,
    )

    print("=" * 60)
    print(f"  REPRO  ·  case={case_id}  dim={result['task_type']}")
    print("=" * 60)
    print(f"hard = {result['hard']}")
    print(f"soft = {result['soft']:.2f}")
    print(f"path = {result['parsed_path'] or '(none)'}")
    print(f"fm   = {result['parsed_frontmatter']}")
    print()
    print("--- assistant reply (first 1200 chars) ---")
    print(result["predicted_answer"][:1200])
    print()
    print(f"[*] artifacts → {run_dir}")
    return 0 if result["hard"] >= 1.0 else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reproduce a single kid-system golden case by id."
    )
    parser.add_argument(
        "case_id",
        nargs="?",
        default=None,
        help="Case id, e.g. TG02-plan-churn-trigger (searched across all suites).",
    )
    args = parser.parse_args()
    if not args.case_id:
        parser.error("case_id is required (see --help)")
    sys.exit(main(args.case_id))
