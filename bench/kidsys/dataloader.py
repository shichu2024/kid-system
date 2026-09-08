"""KidsysDataLoader — loads golden cases from bench/cases/<skill>/.

Each skill has its own items.json (JSON array of case dicts). The loader
also handles flow cases (bench/cases/flow/items.json) whose system prompt
is decided per case by ``expected.flow_downstream_check.skill``.

Schema:
    bench/cases/<skill>/items.json   # e.g. menu, journal, flow
    bench/cases/_schema.json         # JSON Schema for self-documentation

items.json may be either a flat JSON array of cases or a generator
wrapper ``{"skill": ..., "cases": [...]}`` — both shapes are accepted.

skillopt note:
    When skillopt is installed, this loader subclasses SkillOpt's
    SplitDataLoader (split_mode="ratio" auto-materializes train/val/test
    dirs under out_root). When skillopt is missing, a minimal in-memory
    fallback base keeps this module importable and unit-testable —
    `_normalize_case` and the split semantics stay identical either way.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

# Mirror of rollout.SKILL_PATHS keys (kept local to avoid an import cycle).
_VALID_SKILLS = frozenset(
    {"menu", "journal", "learning", "games", "plan", "rules", "review", "profile"}
)

try:  # skillopt is optional at import time (pure scoring stays testable)
    from skillopt.datasets.base import SplitDataLoader as _SkillOptSplitDataLoader

    SKILLOPT_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only without skillopt
    SKILLOPT_AVAILABLE = False

    class _SkillOptSplitDataLoader:  # type: ignore[no-redef]
        """Minimal stand-in for skillopt's SplitDataLoader.

        Performs the same deterministic ratio split in memory instead of
        materializing split directories on disk. Only used when skillopt
        is not installed.
        """

        def __init__(
            self,
            data_path: str = "",
            split_mode: str = "ratio",
            split_ratio: str = "3:1:1",
            split_seed: int = 42,
            **kwargs,
        ) -> None:
            self.data_path = data_path
            self.split_mode = split_mode
            self.split_ratio = split_ratio
            self.split_seed = split_seed
            self.train_items: list[dict] = []
            self.val_items: list[dict] = []
            self.test_items: list[dict] = []
            self._splits: dict[str, list[dict]] = {"train": [], "val": [], "test": []}

        def setup(self, cfg: dict) -> None:
            path = Path(self.data_path)
            if not path.exists():
                raise FileNotFoundError(f"Items file not found: {path}")
            items = _load_cases_json(path)
            skill = str(getattr(self, "skill", "") or "")
            items = [_normalize_case(i, skill) for i in items]
            random.Random(self.split_seed).shuffle(items)
            weights = [int(w) for w in self.split_ratio.split(":")]
            total = sum(weights) or 1
            n = len(items)
            n_train = round(n * weights[0] / total)
            n_val = round(n * weights[1] / total)
            self._splits["train"] = items[:n_train]
            self._splits["val"] = items[n_train : n_train + n_val]
            self._splits["test"] = items[n_train + n_val :]
            self.train_items = self._splits["train"]
            self.val_items = self._splits["val"]
            self.test_items = self._splits["test"]

        def get_split_items(self, split: str) -> list[dict]:
            if split not in self._splits:
                raise ValueError(f"Unknown split: {split!r}")
            return list(self._splits[split])


class KidsysDataLoader(_SkillOptSplitDataLoader):
    """Load golden cases for a kid-system skill.

    Parameters
    ----------
    skill : str
        Skill slug, e.g. ``"menu"`` or ``"journal"``. Maps to
        ``bench/cases/<skill>/items.json``.
    cases_root : str
        Root directory of case suites (default ``bench/cases``).
    """

    def __init__(
        self,
        skill: str = "menu",
        cases_root: str = "bench/cases",
        **kwargs,
    ) -> None:
        self.skill = skill
        self.cases_root = cases_root
        # Resolve data_path to the skill's items.json; with skillopt the
        # base setup() with split_mode="ratio" auto-materializes
        # train/val/test dirs; without it the fallback splits in memory.
        data_path = str(Path(cases_root) / skill / "items.json")
        super().__init__(
            data_path=data_path,
            split_mode="ratio",
            split_ratio=kwargs.pop("split_ratio", "3:1:1"),
            split_seed=kwargs.pop("split_seed", 42),
            **kwargs,
        )

    def load_split_items(self, split_path: str) -> list[dict]:
        """Load items from one split directory (skillopt materialized mode).

        The skillopt base writes ``items.json`` into each split dir during
        ratio materialization. We just read it back as a JSON array and
        normalize each case to ensure required keys exist.
        """
        path = Path(split_path)
        json_files = sorted(path.glob("*.json"))
        if not json_files:
            raise FileNotFoundError(f"No .json file in {split_path}")
        # Skip split_manifest.json if it's the only JSON (shouldn't happen
        # for materialized splits, but defensive).
        items_file = next(
            (f for f in json_files if f.name != "split_manifest.json"),
            json_files[0],
        )
        with items_file.open(encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            raise ValueError(f"Expected JSON array in {items_file}")
        return [_normalize_case(item, self.skill) for item in raw]


def _load_cases_json(path: Path) -> list[dict]:
    """Read items.json — flat array or ``{"cases": [...]}`` wrapper."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return list(raw)
    if isinstance(raw, dict) and isinstance(raw.get("cases"), list):
        return list(raw["cases"])
    raise ValueError(f"Expected JSON array (or {{'cases': [...]}}) in {path}")


def _normalize_case(raw: dict, skill: str) -> dict:
    """Ensure each case has the minimal required keys.

    Adds defaults for optional fields so rollout / scoring never KeyError.
    kid-system adaptation: no user_choice / polish fields — cases carry
    their full inline context in ``input`` (chat backends cannot read the
    vault), and ``should_trigger`` replaces quickkb's
    ``should_trigger_capture`` / ``should_trigger_polish``.
    """
    item = dict(raw)
    item.setdefault("id", f"unnamed-{abs(hash(json.dumps(raw, sort_keys=True, ensure_ascii=False)))}")
    item.setdefault("dimension", "unknown")
    if not item.get("skill"):
        # null/missing → suite name when it is itself a skill slug, else menu
        item["skill"] = skill if skill in _VALID_SKILLS else "menu"
    item.setdefault("input", "")
    item.setdefault("category", skill)
    item.setdefault("references", [])
    item.setdefault("notes", "")

    expected = item.get("expected") or {}
    expected.setdefault("should_trigger", True)
    expected.setdefault("should_write_file", True)
    expected.setdefault("path_glob", "")
    expected.setdefault("frontmatter", {})
    expected.setdefault("frontmatter_forbidden", [])
    expected.setdefault("content_contains", [])
    expected.setdefault("content_excludes", [])
    expected.setdefault("feedback_contains", [])
    expected.setdefault("trigger_markers", [])
    expected.setdefault("flow_upstream_file", "")     # flow-class
    expected.setdefault("flow_downstream_check", {})  # flow-class
    # Generator artifacts: some case generators emit ``{}`` for empty lists
    # or ``null`` for empty strings/dicts. Coerce so scorers never see a
    # wrong-typed value. Note: ``frontmatter_forbidden`` legitimately comes
    # in two shapes — list of field names, or {field: forbidden regex} map
    # (journal-suite convention) — so both lists and dicts are kept as-is.
    for key in (
        "content_contains",
        "content_excludes",
        "feedback_contains",
        "trigger_markers",
    ):
        value = expected.get(key)
        if value is None or isinstance(value, list):
            continue
        expected[key] = [value] if value else []
    ff = expected.get("frontmatter_forbidden")
    if ff is None or isinstance(ff, (list, dict)):
        expected["frontmatter_forbidden"] = ff or []
    else:
        expected["frontmatter_forbidden"] = [ff]
    for key in ("path_glob", "flow_upstream_file"):
        if not isinstance(expected.get(key), str):
            expected[key] = ""
    for key in ("frontmatter", "flow_downstream_check"):
        if not isinstance(expected.get(key), dict):
            expected[key] = {}
    item["expected"] = expected
    return item
