---
name: feature-builder
description: Plan a new feature for an existing project, from a loose idea or brainstorm through grilling and a spec to dependency-ordered cards, then publish the cards to a GitHub Projects board (issues, sub-issues, blocked-by links, Status column). Use when the user wants to brainstorm feature ideas, scope or flesh out a feature, break a feature or spec into cards/tickets/issues/tasks, or already has cards and wants them on a GitHub Project board, even if they never say "feature-builder". This is planning only and writes no application code. For bootstrapping a whole new project, use project-builder instead.
---

# Feature Builder

This skill applies the same discipline as `project-builder`, scoped to **one feature of a project that already exists**. It takes the feature from an idea to a shared understanding, then to a spec, then to cards, and from there to a GitHub Projects board. Your output is documentation and cards, never implementation. The point is that whoever picks up a card later (the user, a teammate, another agent) can build it without re-asking what was meant.

Everything for one feature lives in its own folder:

```
docs/features/<slug>/
├── decisions.md   # append-only log, from the first decision on
├── spec.md        # the agreed feature, parent issue on GitHub
└── cards/
    ├── 01-<slug>.md   # dependency-ordered, blockers first
    └── ...
```

`<slug>` is short kebab-case (`export-csv`, `team-invites`). Pick it as soon as the feature has a name and confirm it with the user. Templates for all three files are in `references/templates.md`. Read it before writing any of them.

## Pick the entry point

Users arrive at different stages. Start where they are, say which phase you're starting from, and say they can step back to an earlier one at any point.

| The user has... | Start at |
|---|---|
| A theme or a problem but no feature yet ("users drop off at onboarding, what could we do?") | 1. Brainstorm |
| A concrete feature idea, still fuzzy around the edges | 2. Grill |
| A settled feature (discussed in this conversation, or in a doc they point to) | 3. Spec |
| A spec (`docs/features/<slug>/spec.md` or elsewhere) | 4. Cards |
| Cards already, local or in any other shape | 5. Publish |

If unsure, ask one question. Don't make them sit through phases they've already done.

## 0. Orient (always, before anything else)

Read the project before proposing anything. Ideas and cards that ignore what the code already does are the main way this kind of planning goes wrong. Look at `README.md`, `AGENTS.md`/`CLAUDE.md`, any glossary (`CONTEXT.md`, `GLOSSARY.md`), `docs/adr/`, `docs/decisions.md`, `docs/issues/`, existing `docs/features/*`, and the parts of the code the feature will touch. For a wide sweep, dispatch an `Explore` subagent and use its conclusions. Don't pull every file into context.

Facts are your job and decisions are the user's. Never ask the user something the repo can answer, and never settle something only the user can decide.

## 1. Brainstorm (diverge, then pick)

The goal is to look at more than the first idea before committing to one.

1. **Frame the problem** in a sentence or two: who has it, when, and what they do today instead. If the user's theme is too vague to frame, ask a short round of framing questions first.
2. **Generate 6–10 genuinely different ideas.** Spread them across ambition (a small tweak, a solid feature, a bold bet) and across approach (UI, workflow, automation, data, integration). Ground them in what you saw in the code, including ideas that reuse what already exists. Give each one a line saying what it is and who it helps. Invite the user to add their own.
3. **Compare them** in a compact table covering user value, effort (using what you know of the codebase), risk, and fit with the existing architecture. Recommend one, or a combination, and give the reason.
4. **The user picks.** Settle the slug, create the feature folder, and make the first `decisions.md` entry: what was chosen, the alternatives considered, and why they lost. Offer to park the strong runners-up in `docs/features/backlog.md` (one line each) so they aren't lost.

Keep this phase light. It should feel like a quick whiteboard session, not a report.

## 2. Grill (converge to shared understanding)

Invoke the `grilling` skill and follow its rounds: the whole frontier per round, numbered questions, and a recommended answer for each. For a feature, the branches that usually matter are:

- **Scope edges**: the smallest version that is still worth shipping, and what is explicitly out.
- **Behaviour**: the main path, edge cases, empty/error states, and who is allowed to do what.
- **Data**: new or changed entities and fields, and migration of existing data.
- **Fit**: which existing modules change, what stays backward-compatible, and whether a flag or gradual rollout is needed.
- **Testing**: the seam where the feature will be verified. Prefer an existing one, as high as possible.

Append each decision to `decisions.md` **the moment it's settled**, not in a batch at the end. If the project has a glossary, use its terms. When the feature introduces or sharpens a term, propose the glossary change, and use the `domain-modeling` skill if it's more than a one-liner. If a decision is hard to reverse (a schema shape, a public API, a new dependency), flag it as ADR-worthy in `decisions.md` rather than writing the ADR now.

You're done when the frontier is empty and the user confirms the shared understanding. Don't move on just because you've run out of questions you thought of.

## 3. Spec

Synthesize what's been decided into `spec.md` using the template. This is synthesis, so don't interview the user here. If you notice a real gap, it's a missed grilling question: ask it, log it, then continue. Make the user stories exhaustive, because every story should end up covered by some card. Show the user the spec, or a tight summary of it, and get a yes before slicing.

## 4. Cards

Slice the spec into **tracer-bullet vertical slices**:

- Each card cuts a narrow but complete path through every layer it needs (data, logic, API, UI, tests), so it's demoable or verifiable on its own. Horizontal cards like "do the backend" or "do the UI" hide integration risk until the end.
- Each card fits in one focused working session, or one fresh agent context.
- Any prefactoring ("make the change easy, then make the easy change") comes first, as its own card.
- Each card declares its **blockers**: only the cards that genuinely gate it. Unnecessary edges serialize work that could run in parallel.

Present the breakdown as a numbered list (title, blocked by, what it delivers) and ask the user: is the granularity right, are the blocking edges right, and should any card be merged or split? Iterate until they approve, then write `cards/NN-<slug>.md` files numbered in dependency order. Check that every user story in the spec is covered by at least one card, and tell the user about any that isn't.

**When the user brings their own cards** (pasted, a markdown list, a doc, another tool's export), normalize them into this format first. Keep their wording, fill in `blocked_by` only from what they state or confirm, and show them the result before publishing. If there's no spec, publishing works without a parent issue (`--no-parent`). Offer to write a short spec, but don't push it.

## 5. Publish to GitHub Projects

Publishing creates public, notification-sending objects in someone's repo, so the user sees the exact plan and says yes before anything is created. Read `references/github.md` for the full procedure. In short:

1. **Preflight**: check that `gh` is installed, logged in, and has the `project` scope. Fix what you can, and hand the user the `! gh auth ...` commands for the steps only they can do.
2. **Choose** the repo, the board (`gh project list`), the initial Status column, and optionally a shared label such as `feature:<slug>`.
3. **Dry run** `scripts/publish_to_github.py <feature-dir> --project N ... --dry-run` (in this skill's directory) and show the user the plan.
4. **Publish** with the same command without `--dry-run`, after an explicit go-ahead.
5. **Report** the issue links and relay any warnings. Each published file now carries `issue: N`. Mention that adding a card later just means adding a new card file and rerunning.

Use the script rather than hand-rolled `gh` calls. It handles dependency order, sub-issues, native blocked-by links, the board's Status field, and the writeback that makes reruns safe.

## Ground rules

- **No application code.** Not even "a quick stub to show the idea". If the user wants to try something out first, suggest the `prototype` skill as a separate step.
- **Never fabricate a decision.** At a real fork, ask (with a recommendation). The decisions log records only what the user actually settled.
- **No `git commit`, `git push` or PRs.** At most, suggest a commit message for the new `docs/features/<slug>/` files. GitHub writes happen only through the publish step, after confirmation.
- **The decisions log is append-only.** When a decision is narrowed or corrected, add a new entry that references the old one. Never quietly edit history.

## Done

The phase you started from and every phase after it are complete: the folder holds a `decisions.md`, a `spec.md` (unless the user skipped it) and the approved cards, and if publishing was requested, the cards are on the board with their issue numbers written back. End with a short summary: where the files are, the board link if published, and the cards that can start right away (the ones with no blockers).
