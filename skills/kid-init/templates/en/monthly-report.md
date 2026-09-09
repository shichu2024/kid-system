---
template: monthly-report
lang: en
period: monthly
date_range: "{{YYYY-MM-01 ~ YYYY-MM-DD}}"
month: "{{YYYY-MM}}"
child_id: "{{child-id}}"
age_months_at_review: {{n}}
summary_tags: [{{tag1}}, {{tag2}}]
---

# Monthly Report · {{YYYY-MM}} · {{Nickname}}

## Data Summary ({{date_range}})

| Dimension | Metric | This month | Last month | Trend |
|-----------|--------|------------|------------|-------|
| Diet | Food variety (kinds/week avg) | {{n}} | {{n}} | {{↑/↓/=}} |
| Diet | Weekly grains/vegetables/protein sources | {{3+/5+/4+ target status}} | {{n}} | {{trend}} |
| Activity | Total hours | {{n}} | {{n}} | {{trend}} |
| Learning | Plan completion rate (%) | {{n}} | {{n}} | {{trend}} |
| Sleep | Average night hours | {{n}} | {{n}} | {{trend}} |
| Mood | happy/calm share (%) | {{n}} | {{n}} | {{trend}} |

## This Month's Highlights

- {{Highlight 1}}
- {{Highlight 2}}

## Milestone Status

Compared against `references/milestones.json` for the current age band ({{age_months}} months):

| Domain | Achieved | Emerging | Not yet |
|--------|----------|----------|---------|
| Gross motor | {{items}} | {{items}} | {{items}} |
| Fine motor | {{items}} | {{items}} | {{items}} |
| Language | {{items}} | {{items}} | {{items}} |
| Social-cognitive | {{items}} | {{items}} | {{items}} |

- Red-flag items: {{none / item + suggest a pediatric evaluation (no diagnostic conclusion)}}

## Watch Items

- {{Watch item 1}}
- Health alert: {{yes → care suggestions + medical-attention indicators / none}}

## Optimization Suggestions (3-5)

1. {{Suggestion 1}} ☐ Convert to rule
2. {{Suggestion 2}} ☐ Convert to rule
3. {{Suggestion 3}} ☐ Convert to rule
4. {{Suggestion 4}} ☐ Convert to rule

## Next Month's Development Focus

- **{{Domain 1, e.g. language}}**: {{concrete goal + daily practice}}
- **{{Domain 2, e.g. gross motor}}**: {{concrete goal + daily practice}}

> ☐ After a "Convert to rule" item is ticked and confirmed by the parent, kid-rules injects it into the rule base. This content does not replace professional medical advice.
