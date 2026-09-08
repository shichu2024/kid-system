"""kid-system × SkillOpt benchmark adapter (ported from quick-knowledge bench/quickkb).

Implements the SkillOpt custom-benchmark contract (SplitDataLoader +
EnvAdapter + rollout helper + YAML config) so kid-system's natural-language
SKILL.md files can be behaviorally evaluated. Semantics follow the
quick-knowledge harness; domain adaptation points are marked with
"kid-system adaptation" comments in the code.

Differences vs quick-knowledge quickkb (by design):
- No polish / user_choice machinery (kid-system has no polish menu).
- ``should_trigger`` generalizes ``should_trigger_capture``: when false,
  the reply must not contain any artifact marker (default
  ``["02_plans", "01_journal"]``, overridable per case via
  ``expected.trigger_markers``).
- Skill loading goes through the module-level ``SKILL_PATHS`` map in
  ``rollout.py`` (env ``kidsys_menu`` → ``skills/kid-menu/SKILL.md``).
- skillopt imports are lazy/optional so dataloader + scoring stay
  importable and unit-testable without skillopt installed.

Layout
------
kidsys/
├── dataloader.py        KidsysDataLoader (SplitDataLoader-compatible)
├── rollout.py           run_batch + _rollout_one (lazy chat_target)
├── adapter.py           KidsysAdapter (EnvAdapter-compatible wiring)
└── scoring/
    ├── __init__.py      aggregate (hard=AND, soft=mean)
    ├── routing.py       path glob scoring
    ├── frontmatter.py   required + forbidden field scoring
    ├── behavior.py      model-reply assertions (trigger / feedback / content)
    └── flow.py          flow-class fixture-based contract scoring
"""

__version__ = "1.2.0"
