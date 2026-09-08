"""Flow scorer — fixture-based contract checks for flow (end-to-end) cases.

Each flow case has:
- ``flow_upstream_file``: path to a fixture file representing the upstream
  skill's output (e.g. journal's note that plan must consume)
- ``flow_downstream_check``: dict of assertions to run against the downstream
  skill's product

Implementation strategy: MVP loads upstream fixture, asks the downstream
skill to act on it, then asserts the downstream product has the expected
fields. Does NOT run the full closed-loop pipeline; each transition is
verified independently. Ported unchanged from quick-knowledge.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


def score(
    downstream_product_fm: dict,
    downstream_product_content: str,
    downstream_check: dict,
) -> tuple[float, float]:
    """Assert the downstream skill's product contains required contract fields.

    Parameters
    ----------
    downstream_product_fm : dict
        Parsed frontmatter of the file the downstream skill wrote.
    downstream_product_content : str
        Body text of the downstream skill's product.
    downstream_check : dict
        Map of field-name → regex (or list of substrings for content).
        Special keys ``"_content_contains"`` (list of required body
        substrings), ``"_content_excludes"`` (list of forbidden body
        substrings) and ``"_frontmatter"`` (map of required frontmatter
        field → regex) are kid-system extensions.

    Returns
    -------
    (hard, soft)
    """
    signals: list[float] = []
    content_lc = (downstream_product_content or "").lower()

    # Metadata keys used by the harness for skill dispatch / documentation;
    # not frontmatter check directives. Skip them so they don't generate
    # spurious zero signals. Underscore-prefixed keys other than the
    # handled specials (_content_* / _frontmatter) are authoring
    # documentation (e.g. _evidence, _rule) and are skipped too.
    _METADATA_KEYS = frozenset({"skill", "consume_field", "produce_field"})
    _SPECIAL_KEYS = frozenset({"_content_contains", "_content_excludes", "_frontmatter"})

    for key, spec in (downstream_check or {}).items():
        if key in _METADATA_KEYS:
            continue
        if key.startswith("_") and key not in _SPECIAL_KEYS:
            continue
        if key == "_content_contains":
            for kw in spec:
                signals.append(1.0 if kw.lower() in content_lc else 0.0)
            continue
        if key == "_content_excludes":
            for kw in spec:
                signals.append(0.0 if kw.lower() in content_lc else 1.0)
            continue
        if key == "_frontmatter":
            # Required frontmatter field → regex map; delegate to the
            # frontmatter scorer and splice its signals in.
            from .frontmatter import score as fm_score

            sub_hard, _sub_soft = fm_score(
                downstream_product_fm, required_fields=spec
            )
            signals.append(sub_hard)
            continue

        # Frontmatter field regex
        actual = downstream_product_fm.get(key)
        if actual is None:
            signals.append(0.0)
            continue
        try:
            ok = bool(re.match(str(spec), str(actual)))
        except re.error:
            ok = str(actual) == str(spec)
        signals.append(1.0 if ok else 0.0)

    if not signals:
        return (1.0, 1.0)
    hard = 1.0 if all(s >= 1.0 for s in signals) else 0.0
    soft = sum(signals) / len(signals)
    return (hard, soft)


def load_upstream_fixture(fixture_path: str) -> dict:
    """Load a JSON fixture describing the upstream skill's product.

    Fixture schema:
        {
          "vault_state": { "<path>": "<content>" },
          "upstream_products": [
            {"path": "...", "frontmatter": {...}, "content": "..."}
          ],
          "upstream_product": {...}   # single-upstream shorthand
        }
    """
    p = Path(fixture_path)
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as f:
        return json.load(f)
