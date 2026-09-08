"""Behavior scorer — model-reply assertions that routing/frontmatter can't see.

kid-system adaptation of quick-knowledge's behavior scorer:

- ``content_contains`` / ``content_excludes`` / ``feedback_contains``
  substring checks (lowercase) preserved verbatim.
- ``should_trigger`` (bool) generalizes quickkb's
  ``should_trigger_capture``: when false, the reply must NOT contain any
  artifact marker. Markers default to ``["02_plans", "01_journal"]`` and
  can be overridden per case via ``expected.trigger_markers`` (e.g. add
  ``"00_profiles"`` for profile-sedimentation cases).
- ``multi_child`` (unseen-suite extension): per-child assertions — each
  child's id must be mentioned, per-child content_contains/excludes apply
  to the whole reply, and ``plan_count`` requires at least that many
  distinct artifact paths matching ``expected.path_glob``.
- The polish-menu check is removed (kid-system has no polish menu).
"""
from __future__ import annotations

import fnmatch
import re


# kid-system artifact markers: vault directory prefixes that indicate the
# skill actually produced (or claimed to produce) a file.
_DEFAULT_TRIGGER_MARKERS = ["02_plans", "01_journal"]

_PATH_PATTERN = re.compile(r'(?:[\w\-]+/)+[\w\-][\w\-.]*\.md')


def score(
    model_reply: str,
    expected: dict,
) -> tuple[float, float]:
    """Assert key behavioral signals in the model's reply.

    Parameters
    ----------
    model_reply : str
        The full text the model produced (its "what I did" summary).
    expected : dict
        Subset of the case's ``expected`` block relevant to behavior:
        - ``should_trigger``: bool — skill should run at all. Only
          asserted when False (a True expectation is covered by the
          routing scorer's path check).
        - ``trigger_markers``: list[str] — artifact markers that must NOT
          appear when ``should_trigger`` is false (default
          ``["02_plans", "01_journal"]``).
        - ``feedback_contains``: list[str] — keywords expected in feedback
        - ``content_excludes``: list[str] — forbidden substrings in written content
        - ``content_contains``: list[str] — required substrings in written content
        - ``multi_child``: list[dict] — per-child assertions (see module docstring)

    Returns
    -------
    (hard, soft)
    """
    reply = (model_reply or "").lower()
    signals: list[float] = []

    # Trigger assertion: when the skill should NOT have run, the reply must
    # not contain any artifact marker (e.g. "02_plans", "01_journal",
    # "00_profiles" — or case-specific markers via trigger_markers).
    if "should_trigger" in expected and not expected["should_trigger"]:
        markers = expected.get("trigger_markers") or _DEFAULT_TRIGGER_MARKERS
        found = [m for m in markers if str(m).lower() in reply]
        signals.append(0.0 if found else 1.0)

    # Feedback keyword assertion
    for kw in expected.get("feedback_contains", []):
        signals.append(1.0 if kw.lower() in reply else 0.0)

    # Content excludes (check in reply too — model often echoes content)
    for kw in expected.get("content_excludes", []):
        signals.append(0.0 if kw.lower() in reply else 1.0)

    # Content contains (loose check in reply)
    for kw in expected.get("content_contains", []):
        signals.append(1.0 if kw.lower() in reply else 0.0)

    # Multi-child (twins etc.): each child gets its own artifact; assert
    # per-child mentions, per-child content constraints, and artifact count.
    for child in expected.get("multi_child", []) or []:
        child_id = str(child.get("child_id", "")).lower()
        if child_id:
            signals.append(1.0 if child_id in reply else 0.0)
        for kw in child.get("content_contains", []) or []:
            signals.append(1.0 if kw.lower() in reply else 0.0)
        for kw in child.get("content_excludes", []) or []:
            signals.append(0.0 if kw.lower() in reply else 1.0)
        plan_count = child.get("plan_count")
        if isinstance(plan_count, int) and plan_count > 0:
            glob = str(expected.get("path_glob", "") or "*")
            distinct = {p for p in _PATH_PATTERN.findall(model_reply or "") if fnmatch.fnmatch(p, glob)}
            signals.append(1.0 if len(distinct) >= plan_count else 0.0)

    if not signals:
        return (1.0, 1.0)
    hard = 1.0 if all(s >= 1.0 for s in signals) else 0.0
    soft = sum(signals) / len(signals)
    return (hard, soft)
