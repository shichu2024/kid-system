#!/usr/bin/env python3
"""bench/run_eval.py — Standalone SkillOpt-based evaluator for kid-system.

Runs the current SKILL.md (or a candidate) against the golden-case suite,
prints a per-dimension report, and writes ``bench/reports/<run-id>/`` artifacts.

Usage
-----
    # Activate a SkillOpt backend first (see requirements-bench.txt + .env)
    python bench/run_eval.py --skill menu
    python bench/run_eval.py --skill menu --split test
    python bench/run_eval.py --skill flow            # end-to-end flow cases
    python bench/run_eval.py --skill menu --skill-file path/to/candidate.md

Per-skill defaults (split ratio, seed, env name) are read from
``bench/configs/<skill>-default.yaml``; CLI flags override.

This script does NOT register into SkillOpt's internal _ENV_REGISTRY;
it consumes SkillOpt as a library (chat_target, SplitDataLoader) directly.
This keeps us insulated from upstream registry changes.

Optional environment (set in .env):
    SKILLOPT_BACKEND      = openai_chat | openai_compatible | claude_chat | ...
    AZURE_OPENAI_*        = ...   (if backend=openai_chat)
    OPENAI_COMPATIBLE_*   = ...   (if backend=openai_compatible)
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

# Make `bench` importable when invoked as `python bench/run_eval.py`
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from bench.kidsys.dataloader import KidsysDataLoader
from bench.kidsys.rollout import SKILL_PATHS, run_batch

_CONFIGS_DIR = "bench/configs"
# Flow cases pick their system prompt per case via
# ``expected.flow_downstream_check.skill``; this default is only the
# fallback when a downstream SKILL.md is missing (mirrors quickkb's
# flow→capture fallback).
_DEFAULT_SKILL_FILES = {**SKILL_PATHS, "flow": SKILL_PATHS["menu"]}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Evaluate a kid-system skill on golden cases via SkillOpt."
    )
    p.add_argument(
        "--skill",
        default="menu",
        choices=sorted(_DEFAULT_SKILL_FILES.keys()),
        help="Skill slug to evaluate (default: menu).",
    )
    p.add_argument(
        "--skill-file",
        default=None,
        help="Path to a candidate SKILL.md (default: live file under skills/).",
    )
    p.add_argument(
        "--split",
        default="val",
        choices=["train", "val", "test"],
        help="Dataset split to evaluate (default: val).",
    )
    p.add_argument(
        "--cases-root",
        default="bench/cases",
        help="Root directory of cases (default: bench/cases).",
    )
    p.add_argument(
        "--split-ratio",
        default=None,
        help="train:val:test ratio (default: from config, else 3:1:1).",
    )
    p.add_argument(
        "--split-seed",
        type=int,
        default=None,
        help="Split seed (default: from config, else 42).",
    )
    p.add_argument(
        "--out-dir",
        default="bench/reports",
        help="Where to write report artifacts (default: bench/reports).",
    )
    p.add_argument(
        "--max-completion-tokens",
        type=int,
        default=None,
        help="Per-call token budget (default: from config, else 4096).",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Cap cases per split (0 = no cap, debug with small N).",
    )
    return p.parse_args()


# ── Minimal config loading (PyYAML optional) ─────────────────────────


def _strip_comment(line: str) -> str:
    in_quote = None
    for i, ch in enumerate(line):
        if in_quote:
            if ch == in_quote:
                in_quote = None
        elif ch in "\"'":
            in_quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
    return line


def _parse_scalar(s: str):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _load_yaml_dict(path: Path) -> dict:
    """Load the harness's simple two-level YAML configs.

    Prefers PyYAML when installed; otherwise falls back to a minimal
    parser that handles exactly the shape written under bench/configs/
    (top-level keys + one nesting level, quoted strings, comments).
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore[import-not-found]

        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except ImportError:
        pass
    out: dict = {}
    section = None
    for raw in text.splitlines():
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        if not line.startswith((" ", "\t")):
            if line.endswith(":"):
                section = line[:-1].strip()
                out[section] = {}
            else:
                key, _, val = line.partition(":")
                out[key.strip()] = _parse_scalar(val)
                section = None
        elif section is not None:
            key, _, val = line.strip().partition(":")
            out[section][key.strip()] = _parse_scalar(val)
    return out


def load_skill(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Skill file not found: {path}")
    return p.read_text(encoding="utf-8")


def main() -> int:
    args = parse_args()

    config_path = _REPO_ROOT / _CONFIGS_DIR / f"{args.skill}-default.yaml"
    config = _load_yaml_dict(config_path)
    data_cfg = config.get("data", {}) if isinstance(config.get("data"), dict) else {}
    model_cfg = config.get("model", {}) if isinstance(config.get("model"), dict) else {}

    split_ratio = args.split_ratio or data_cfg.get("split_ratio", "3:1:1")
    split_seed = args.split_seed if args.split_seed is not None else int(data_cfg.get("split_seed", 42))
    max_tokens = args.max_completion_tokens or int(model_cfg.get("max_completion_tokens", 4096))

    skill_file = args.skill_file or _DEFAULT_SKILL_FILES[args.skill]
    skill_file_abs = skill_file if os.path.isabs(skill_file) else str(_REPO_ROOT / skill_file)
    skill_content = load_skill(skill_file_abs)

    env_name = str(config.get("env", f"kidsys_{args.skill}"))

    # Build dataloader + materialize splits
    loader = KidsysDataLoader(
        skill=args.skill,
        cases_root=str(_REPO_ROOT / args.cases_root),
        split_ratio=split_ratio,
        split_seed=split_seed,
        limit=args.limit,
    )
    loader.setup({
        "out_root": str(_REPO_ROOT),
        "env": env_name,
    })

    items = loader.get_split_items(args.split)
    if not items:
        print(f"[!] split '{args.split}' has 0 items — nothing to evaluate.")
        return 1

    print(f"[*] skill      = {args.skill}")
    print(f"[*] skill_file = {skill_file_abs}")
    print(f"[*] config     = {config_path.name if config else '(defaults)'}")
    print(f"[*] split      = {args.split} ({len(items)} cases)")
    print(f"[*] running rollouts ...")

    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = Path(args.out_dir) / f"{args.skill}-{args.split}-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    results = run_batch(
        items=items,
        skill_content=skill_content,
        out_root=str(run_dir),
        max_completion_tokens=max_tokens,
    )

    # Per-dimension report
    by_dim: dict[str, list[dict]] = {}
    for r in results:
        by_dim.setdefault(r["task_type"], []).append(r)

    print()
    print("=" * 60)
    print(f"  REPORT  ·  skill={args.skill}  split={args.split}")
    print("=" * 60)
    print(f"{'dimension':<30} {'n':>4} {'hard':>8} {'soft':>8}")
    print("-" * 60)
    total_hard_pass = 0
    total_n = 0
    for dim in sorted(by_dim.keys()):
        rows = by_dim[dim]
        n = len(rows)
        hard_pass = sum(1 for r in rows if r["hard"] >= 1.0)
        soft_mean = sum(r["soft"] for r in rows) / n if n else 0.0
        total_hard_pass += hard_pass
        total_n += n
        print(f"{dim:<30} {n:>4} {hard_pass:>8} {soft_mean:>8.2f}")
    print("-" * 60)
    overall_hard = total_hard_pass / total_n if total_n else 0.0
    overall_soft = sum(r["soft"] for r in results) / len(results) if results else 0.0
    print(f"{'TOTAL':<30} {total_n:>4} {total_hard_pass:>8} {overall_soft:>8.2f}")
    print(f"  hard rate = {overall_hard:.1%}")
    print()
    print(f"[*] artifacts → {run_dir}")
    print(f"    - rollouts.json   (per-case raw result)")
    print(f"    - predictions/<id>/conversation.json  (trajectories)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
