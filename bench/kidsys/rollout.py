"""Rollout helper — invoke skill under test on a batch of cases.

Ported from quick-knowledge bench/quickkb/rollout.py (semantics preserved)
with kid-system adaptations:

- Skill loading goes through the module-level ``SKILL_PATHS`` map
  (env ``kidsys_menu`` → ``skills/kid-menu/SKILL.md``).
- No polish / user_choice simulation: kid-system cases inline their full
  context (profile / journal / rules blocks) inside ``input`` because chat
  backends cannot read the vault.
- ``chat_target`` is imported lazily so this module (and everything that
  imports it) stays importable without skillopt installed.

For MVP we use the ``chat`` backend (single-turn): skill content as system
prompt, case input as user message. The model's text reply is parsed to
extract the file path + frontmatter it claims to have written.

For the ``exec`` backend (real Claude Code), this file is the seam to
extend. MVP scope is chat-only.

Conversation persistence (required by SkillOpt reflect):
    <out_root>/predictions/<case-id>/conversation.json
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .scoring import frontmatter as fm_scorer
from .scoring import routing as routing_scorer
from .scoring import behavior as behavior_scorer
from .scoring import flow as flow_scorer
from .scoring import aggregate


# kid-system adaptation: env slug (minus the ``kidsys_`` prefix) → SKILL.md
# path relative to repo root. Flow cases resolve their downstream skill
# through this same map (``expected.flow_downstream_check.skill``).
SKILL_PATHS = {
    "menu": "skills/kid-menu/SKILL.md",
    "journal": "skills/kid-journal/SKILL.md",
    "learning": "skills/kid-learning/SKILL.md",
    "games": "skills/kid-games/SKILL.md",
    "plan": "skills/kid-plan/SKILL.md",
    "rules": "skills/kid-rules/SKILL.md",
    "review": "skills/kid-review/SKILL.md",
    "profile": "skills/kid-profile/SKILL.md",
}

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FLOW_METADATA_KEYS = frozenset({"skill", "consume_field", "produce_field"})


def resolve_skill_path(skill: str) -> Path:
    """Resolve a skill slug or full name to its SKILL.md path.

    Accepts both short slugs (``menu``) and full names (``kid-menu``).
    Raises KeyError for unknown skills.
    """
    slug = str(skill or "").strip()
    if slug.startswith("kid-"):
        slug = slug[len("kid-"):]
    if slug not in SKILL_PATHS:
        raise KeyError(f"Unknown skill: {skill!r} (known: {sorted(SKILL_PATHS)})")
    return _REPO_ROOT / SKILL_PATHS[slug]


def check_skillopt() -> None:
    """Fail fast with a friendly message when skillopt is missing.

    Rollouts require ``skillopt.model.chat_target``; everything else in
    this package is importable and testable without it.
    """
    try:
        from skillopt.model import chat_target  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "skillopt is not installed — rollouts need the SkillOpt chat backend.\n"
            "Install it with:  pip install -r requirements-bench.txt\n"
            f"(import error: {exc})"
        ) from exc


def run_batch(
    *,
    items: list[dict],
    skill_content: str,
    out_root: str,
    workers: int = 1,
    max_completion_tokens: int = 4096,
    extra_context: str = "",
) -> list[dict]:
    """Run a batch of cases sequentially (MVP: no thread pool).

    Parameters
    ----------
    items : list[dict]
        Golden cases (each conforms to KidsysDataLoader._normalize_case output).
    skill_content : str
        The SKILL.md under test (current or candidate).
    out_root : str
        Where to persist per-case conversation.json.
    max_completion_tokens : int
        Per-call budget.
    extra_context : str
        Optional preamble prepended to system prompt (e.g. fixture state).

    Returns
    -------
    list[dict] with keys: id, hard, soft, predicted_answer, task_type, ...
    """
    check_skillopt()
    os.makedirs(out_root, exist_ok=True)
    prediction_dir = Path(out_root, "predictions")
    prediction_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    for item in items:
        result = _rollout_one(
            item=item,
            skill_content=skill_content,
            prediction_dir=prediction_dir,
            max_completion_tokens=max_completion_tokens,
            extra_context=extra_context,
        )
        results.append(result)

    Path(out_root, "rollouts.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return results


def _rollout_one(
    *,
    item: dict,
    skill_content: str,
    prediction_dir: Path,
    max_completion_tokens: int,
    extra_context: str = "",
) -> dict:
    """Run one case through the skill, score it, persist trajectory."""
    from skillopt.model import chat_target

    # Flow cases: dispatch to the downstream skill named in
    # ``flow_downstream_check.skill`` (e.g. journal/plan/profile/...).
    # Falls back to the caller-supplied skill_content if the downstream
    # SKILL.md is missing.
    skill_content = _maybe_override_skill(item, skill_content)
    system = (extra_context + "\n\n" + skill_content).strip()
    user = _format_user_message(item)

    try:
        reply, _usage = chat_target(
            system=system,
            user=user,
            max_completion_tokens=max_completion_tokens,
        )
    except Exception as exc:  # noqa: BLE001
        reply = f"[rollout-failed] {type(exc).__name__}: {exc}"

    # Parse what the skill claims to have produced
    parsed_path = _extract_path(reply, exclude_from=user)
    parsed_fm = _extract_frontmatter(reply)

    # Score
    expected = item.get("expected", {})
    scores: list[tuple[float, float]] = []

    # Routing (skip for flow cases — they have their own path logic)
    if expected.get("path_glob") or not expected.get("flow_downstream_check"):
        scores.append(routing_scorer.score(parsed_path, expected.get("path_glob", "")))

    # Frontmatter (skip forbidden/required checks for flow cases)
    if expected.get("frontmatter") or expected.get("frontmatter_forbidden"):
        scores.append(
            fm_scorer.score(
                parsed_fm,
                required_fields=expected.get("frontmatter"),
                forbidden_fields=expected.get("frontmatter_forbidden"),
            )
        )

    # Behavior (trigger / feedback / content / multi-child assertions)
    if (
        "should_trigger" in expected
        or expected.get("feedback_contains")
        or expected.get("content_contains")
        or expected.get("content_excludes")
        or expected.get("multi_child")
    ):
        scores.append(behavior_scorer.score(reply, expected))

    # Flow (fixture contract)
    if expected.get("flow_downstream_check"):
        scores.append(
            flow_scorer.score(
                downstream_product_fm=parsed_fm,
                downstream_product_content=reply,
                downstream_check=expected["flow_downstream_check"],
            )
        )

    hard, soft = aggregate(scores)

    # Persist conversation.json (required by SkillOpt reflect stage)
    case_dir = prediction_dir / str(item["id"])
    case_dir.mkdir(parents=True, exist_ok=True)
    conversation = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
        {"role": "assistant", "content": reply},
    ]
    (case_dir / "conversation.json").write_text(
        json.dumps(conversation, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "id": str(item["id"]),
        "hard": hard,
        "soft": soft,
        "predicted_answer": reply,
        "parsed_path": parsed_path,
        "parsed_frontmatter": parsed_fm,
        "task_description": item.get("input", ""),
        "task_type": item.get("dimension", "unknown"),
        "skill": item.get("skill", ""),
        "category": item.get("category", ""),
        "references": item.get("references", []),
        "notes": item.get("notes", ""),
        "n_turns": 1,
    }


def _maybe_override_skill(item: dict, default_skill_content: str) -> str:
    """For flow cases, load the downstream skill's SKILL.md.

    kid-system adaptation: reads ``expected.flow_downstream_check.skill``
    (e.g. "journal") and resolves it through the module-level
    ``SKILL_PATHS`` map (e.g. ``skills/kid-journal/SKILL.md``). Returns
    the default skill content unchanged if no override applies or the
    file is absent.
    """
    expected = item.get("expected", {}) or {}
    fc = expected.get("flow_downstream_check") or {}
    downstream_skill = fc.get("skill") or item.get("downstream_skill")
    if not downstream_skill:
        return default_skill_content
    try:
        skill_file = resolve_skill_path(str(downstream_skill))
    except KeyError:
        return default_skill_content
    if not skill_file.exists():
        return default_skill_content
    return skill_file.read_text(encoding="utf-8")


def _inline_flow_fixture(parts: list[str], expected: dict) -> None:
    """For flow cases, inline the upstream fixture content into the prompt.

    Chat backends can't read files, so the fixture JSON (upstream product
    frontmatter + body) must be embedded directly in the user message.
    Handles both single-upstream (``upstream_product``) and multi-upstream
    (``upstream_products``) fixture shapes.
    """
    fixture_path = expected.get("flow_upstream_file")
    if not fixture_path:
        return
    fixture = flow_scorer.load_upstream_fixture(str(_REPO_ROOT / fixture_path))
    if not fixture:
        parts.append(f"[context] upstream products: (could not load: {fixture_path})")
        return

    parts.append("[context] upstream products:")
    products = fixture.get("upstream_products") or ([fixture["upstream_product"]] if fixture.get("upstream_product") else [])
    for i, prod in enumerate(products, 1):
        parts.append(f"  [upstream-{i}] path: {prod.get('path', '?')}")
        fm = prod.get("frontmatter") or {}
        if fm:
            parts.append(f"  [upstream-{i}] frontmatter:")
            parts.append("```yaml")
            parts.append(json.dumps(fm, ensure_ascii=False, indent=2))
            parts.append("```")
        content = prod.get("content")
        if content:
            parts.append(f"  [upstream-{i}] content:")
            parts.append(content)

    parts.append("")
    parts.append("Based on the upstream products above, run YOUR skill's workflow on the input below and produce the downstream artifact (path + yaml frontmatter + body).")


def _format_user_message(item: dict) -> str:
    """Build the user turn.

    kid-system adaptation: cases inline their full context (profile /
    journal / rules blocks) directly in ``input`` — the chat backend cannot
    read the vault — so no simulated user choice is injected. Flow cases
    additionally get the upstream fixture inlined as a preamble.
    """
    parts: list[str] = []
    expected = item.get("expected", {})

    # Flow cases: inline upstream fixture content so chat backend can see it
    if expected.get("flow_upstream_file"):
        _inline_flow_fixture(parts, expected)

    parts.append(item.get("input", ""))

    return "\n".join(parts)


def _extract_path(reply: str, exclude_from: str = "") -> str:
    """Extract the file path the skill claims to have written.

    Looks for patterns like:
        01_journal/2026-09/2026-09-08.md
        ✓ 已记录（journal · 01_journal/2026-09/2026-09-08.md）

    Two filters, in order:
    1. Drops any path that also appears in ``exclude_from`` (typically the
       user message). Flow prompts inline the upstream fixture path; the
       model often restates it in its reply, and such restatements are
       references rather than new artifacts.
    2. Among the remaining candidates, picks the deepest (most '/'
       segments) — downstream artifacts tend to live under multi-segment
       vault prefixes like ``02_plans/2026-09/...`` while relative
       fragments like ``tags/foo.md`` are shallower.
    """
    if not reply:
        return ""
    pattern = r'(?:[\w\-]+/)+[\w\-][\w\-.]*\.md'
    matches = re.findall(pattern, reply)
    if not matches:
        return ""
    if exclude_from:
        matches = [m for m in matches if m not in exclude_from]
    if not matches:
        return ""
    return max(matches, key=lambda p: p.count("/"))


def _extract_frontmatter(reply: str) -> dict:
    """Extract the frontmatter block the skill claims to have written.

    Looks for the first ```yaml ... ``` block or a --- ... --- block
    in the reply, then parses it.

    Ported fix (from quickkb P0-1): when the model emits a ```yaml block
    whose body already contains `---` separators (the natural frontmatter
    shape), do NOT wrap it again — that produces `---\\n---\\n...\\n---\\n---`
    which the parser reads as an empty block.
    """
    if not reply:
        return {}
    # Try fenced yaml first
    fenced = re.search(r'```ya?ml\s*\n(.*?)\n```', reply, re.DOTALL)
    if fenced:
        body = fenced.group(1).strip()
        if body.startswith("---"):
            # Body is already a complete frontmatter block — parse as-is
            return fm_scorer.parse_frontmatter_text(body)
        # Body is raw YAML (no --- separators) — wrap it
        return fm_scorer.parse_frontmatter_text("---\n" + body + "\n---")
    # Try a full artifact wrapped in a generic fence (```markdown etc.) whose
    # body begins with a frontmatter --- block.
    wrapped = re.search(
        r'```(?:markdown|md)\s*\n(---\s*\n.*?\n---)\s*\n', reply, re.DOTALL
    )
    if wrapped:
        return fm_scorer.parse_frontmatter_text(wrapped.group(1))
    # Try bare ---
    bare = re.search(r'^---\s*\n(.*?)\n---\s*$', reply, re.DOTALL | re.MULTILINE)
    if bare:
        return fm_scorer.parse_frontmatter_text(
            "---\n" + bare.group(1) + "\n---"
        )
    return {}
