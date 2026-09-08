"""kid-system benchmark harness (SkillOpt-compatible).

Layout
------
bench/
├── run_eval.py            main evaluator entry (per-skill, split-aware)
├── run_unseen_eval.py     flat-items generalization probe (bypasses split)
├── repro_case.py          single-case repro by id
├── configs/               per-skill default YAML configs
├── cases/                 golden cases (bench/cases/<skill>/items.json)
└── kidsys/                the ported harness package (see kidsys/__init__.py)
"""
