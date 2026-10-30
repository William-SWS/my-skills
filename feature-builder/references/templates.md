# Templates

The frontmatter is what `scripts/publish_to_github.py` reads, so keep it flat: `key: value` lines and `[a, b]` lists, with no nesting. Leave `issue:` out (or empty) until the card is published. The script fills it in.

Write the prose in the language the user is speaking, or in the language the project's docs use if it differs and the user prefers it. The headings below can be translated too.

## spec.md

```markdown
---
title: <Feature name, as it should read as a GitHub issue title>
---

# <Feature name>

## Problem

The problem from the user's perspective: who has it, when it bites, and what they do today instead.

## Solution

What the feature does, from the user's perspective. No file paths.

## User stories

1. As a <actor>, I want <capability>, so that <benefit>
2. ...

Be exhaustive. Cover the main path, the edge cases settled during grilling, error states and permissions. Each story is a promise the cards must keep.

## Implementation decisions

- Modules built or changed, and how their interfaces change
- Schema/data changes, API contracts, integration points with existing code
- Technical constraints the user stated

Name modules and concepts with the project's own vocabulary. Leave file paths and code out because they go stale. The one exception is a snippet that pins a decision more precisely than prose can (a schema, a state machine, a type shape). Trim it to the decision-rich lines.

## Testing decisions

- The seam(s) where the feature is tested, preferring existing ones and the highest one available
- What a good test asserts here: external behaviour, not implementation

## Out of scope

What was explicitly left out, and why when the reason matters later.

## Open questions

Anything still unsettled. Leave this empty when grilling finished cleanly.
```

## cards/NN-slug.md

`NN` is the dependency order, starting at `01`, with blockers first. `id` matches `NN`. `blocked_by` lists the ids of the cards that must be done first, or `[]` if none. `labels` and `status` are optional (`status` overrides the board default for this card).

```markdown
---
id: 01
title: <Short imperative title>
blocked_by: []
labels: []
---

# <Short imperative title>

## What to build

The end-to-end behaviour this card makes work, from the user's perspective. Describe one path through every layer, not a list of layer tasks.

## Acceptance criteria

- [ ] Observable criterion 1
- [ ] Observable criterion 2

## Notes

Optional: user stories from the spec this card covers (by number), decisions it depends on, pitfalls found while exploring the code.
```

The card body says nothing about blockers or the parent. The script turns `blocked_by` and the spec into a "Blocked by" section, native GitHub dependencies and a sub-issue link, so writing them in the body too would duplicate them.

## decisions.md

```markdown
# Decisions: <Feature name>

## 2026-10-30

1. **<Short decision>**: <what was decided, and the reason in one line>.
2. **Clarifies #1**: <the narrowed or corrected decision>.
```

Append-only. Add a new `## YYYY-MM-DD` section per date at the bottom, and append each entry when it's settled. Never rewrite an old entry. Add a new one that references it.
