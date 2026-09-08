---
template: weekly-review
lang: en
period: weekly
date_range: "{{YYYY-MM-DD ~ YYYY-MM-DD}}"
week_number: "{{YYYY-Www}}"
child_id: "{{child-id}}"
summary_tags: [{{tag1}}, {{tag2}}]
---

# Weekly Review · {{YYYY-Www}} · {{Nickname}}

## Data Summary ({{date_range}})

| Dimension | Metric | This week | Last week | Trend |
|-----------|--------|-----------|-----------|-------|
| Diet | Food variety (kinds) | {{n}} | {{n}} | {{↑/↓/=}} |
| Diet | Food-refusal events | {{n}} | {{n}} | {{trend}} |
| Activity | Total minutes | {{n}} | {{n}} | {{trend}} |
| Activity | Outdoor days | {{n}} | {{n}} | {{trend}} |
| Learning | Plan completion rate (%) | {{n}} | {{n}} | {{trend}} |
| Sleep | Average night hours | {{n}} | {{n}} | {{trend}} |
| Sleep | Good-quality share (%) | {{n}} | {{n}} | {{trend}} |
| Mood | happy/calm share (%) | {{n}} | {{n}} | {{trend}} |

## This Week's Highlights

- {{Highlight 1: new skill / good habit / first attempt}}
- {{Highlight 2}}

## Watch Items

- {{Watch item 1, e.g. refused carrots 3 times / more night wakings}}
- {{Watch item 2: 3+ consecutive anomalous days (low appetite/poor sleep/fussiness or crying) → triggers an alert}}
- Health alert: {{yes → care suggestions + medical-attention indicators / none}}

## Optimization Suggestions (3-5)

1. {{Suggestion 1: concrete and actionable}} ☐ Convert to rule
2. {{Suggestion 2}} ☐ Convert to rule
3. {{Suggestion 3}} ☐ Convert to rule
4. {{Suggestion 4}} ☐ Convert to rule

> ☐ After a "Convert to rule" item is ticked and confirmed by the parent, kid-rules injects it into `03_rules/rules.md`. Milestone comparison lives in `04_reviews/milestones.md`. This content does not replace professional medical advice.
