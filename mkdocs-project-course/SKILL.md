---
name: mkdocs-project-course
description: Beginner-level MkDocs course that teaches how to build a project from its project-builder tickets or user-story spec, one lesson per ticket, with the code shown for the reader to type and each lesson calibrated to the learner's progress. Use to scaffold the course (`init`), write or revise the lesson for a ticket, implement a ticket in a course project, or record how the learner did on a lesson.
argument-hint: "[init | número do ticket | revisar NN | progresso]"
---

# MkDocs project course

You turn a project's tickets into a **course**: an MkDocs site where each **lesson** teaches a **beginner** (someone who can use a computer but has never touched this stack) how to build one ticket of the project by typing the code themselves. The course comes before the code: the lesson shows the code, the reader writes it into `src/`.

The reader is a **learner** you follow across sessions. Their mission, what they already know and where they got stuck live in `course/` (see [COURSE-STATE.md](COURSE-STATE.md)), and every lesson is written for their **zone of proximal development**: hard enough to stretch them, close enough to reach. Learning that lasts comes from effortful recall, not from rereading, so lessons make the learner retrieve, predict and practise with immediate feedback.

The course outlives this conversation. Every lesson written or revised and every check-in lands in `course/LOG.md`, so another agent or model can take the course over from the files alone: start by reading the **handoff** files in the order COURSE-STATE.md gives, and leave them complete when you stop.

## 1. Find the inputs

The course is built from what the `project-builder` agent leaves in the repo:

- tickets `docs/issues/NN-*.md`, dependency-ordered, each with a `Blocked by` line;
- the spec `docs/issues/0000-*.md` (user stories, implementation decisions, out of scope);
- `docs/decisions.md`, `docs/adr/`, `AGENTS.md`, and `CONTEXT.md` when it exists.

Only the spec exists → draft a lesson map from its user stories (one lesson per working slice the reader can run) and confirm it with `AskUserQuestion` before writing anything. Neither exists → stop and tell the user to run `/project-builder` first.

Done when you hold the ordered list of lessons and, for each, the ticket (or stories) it teaches.

## 2. Route

- No `mkdocs.yml` or no `course/MISSION.md` yet, or ARGUMENTS is `init` → **init** branch: read [SCAFFOLD.md](SCAFFOLD.md) and follow it.
- ARGUMENTS is `progresso`, or the user is reporting how a lesson went → **check-in** only (step 3.1), then suggest the next lesson.
- ARGUMENTS is `revisar NN`, or the user agrees to resolve an open pending item about lesson `NN` → **revision**: steps 3.2–3.8 applied to the existing page, logged as `Aula revisada` and closing the pending item.
- Otherwise → **lesson** branch, for the ticket number in ARGUMENTS; with no argument, the first ticket in dependency order that has no lesson yet and whose blockers all have one. Read [LESSON-TEMPLATE.md](LESSON-TEMPLATE.md) before writing.

A requested ticket whose blockers still lack lessons → tell the user which lesson comes first and ask whether to write that one instead.

Mapping: the lesson for ticket `NN` is `docs/NN-slug.md`. The scaffolding ticket gets a lesson too: it teaches setting up the environment from zero. Tickets that build nothing the reader types (closing, report, presentation) get no lesson; the course map in `docs/index.md` marks them as such.

## 3. Lesson branch

1. **Check in** (skip before the first lesson): ask the learner, with `AskUserQuestion`, how the previous lesson went: done without trouble, stuck on a step, missed quiz questions, exercises skipped, not done yet. Follow up on whatever they flag (which step, which question, what they thought). Record, per COURSE-STATE.md: a `Check-in` entry in `course/LOG.md` quoting the learner's words; the evidence as learning records; preferences in `course/NOTES.md`; and a `Pendência aberta` for anything the course itself got wrong (an unclear step, a wrong output). Done when the learner has answered or chosen to skip, and everything they said is in the log. Previous lesson not done yet → say the new one builds on it and ask whether to go ahead anyway.
2. **Read** the ticket in full, the lessons of its blockers, the spec, the decisions and ADRs touching this area, the real `src/` when the user has implemented earlier tickets, and the course state: the handoff files (`course/MISSION.md`, the last entries of `course/LOG.md`, `course/learning-records/`, `course/NOTES.md`), `docs/glossario.md` and `course/includes/`. Open pending items in the log → show them to the user first; a lesson flagged for revision is revised before the new one when the user agrees. Done when you can state the lesson's one tangible win (what the learner will run and see work at the end) and which earlier lessons it stands on.
3. **Inventory concepts**: list every term, library, command, file and pattern that will appear in the lesson's code and commands, and sort each item into: **new here** (explained in full), **taught earlier** (linked to that lesson and to the glossary), or **already known by the learner** per a learning record (recapped in one line). Done when every item has its place, so nothing reaches the reader unexplained.
   - A lesson carries about **three** new concepts. More than that → split the ticket into lessons `docs/NN-1-slug.md`, `docs/NN-2-slug.md`, ..., each ending in its own tangible win, and tell the user why.
4. **Ground in sources**: each concept explained is backed by a source you read in this session (fetch the official documentation; memory is not a source), cited by name and URL. New sources go into `docs/recursos.md`, annotated. Local file paths stay out of the course. Done when every claim in the Conceitos section points to a source read this session.
5. **Write** the lesson following LESSON-TEMPLATE.md, every section, reusing the blocks in `course/includes/`.
6. **Replay**: in the scratchpad, rebuild the project up to the previous lesson (the real `src/` if the earlier tickets are implemented, otherwise the code of the earlier lessons applied in order), apply this lesson's code exactly as the page shows it, and run every command, every test, every exercise test (red before the solution, green after it) and every solution the page contains. Done when every block runs, every test ends green, and every terminal output printed in the page was pasted from this run. A block that fails means the lesson is wrong: fix the lesson and replay again.
   - The replay folder is created fresh in each run (the scratchpad does not survive between sessions). Write its files with absolute paths, and start every shell command with `cd <replay folder> || exit 1`, so a missing folder stops the run instead of writing into the real repo.
7. **Record**:
   - `nav` of `mkdocs.yml` and the course map in `docs/index.md`;
   - an `Aula escrita` (or `Aula revisada`) entry at the end of `course/LOG.md`, per COURSE-STATE.md: what the lesson covers, the calibration choices and the records behind them, what was deferred or split, what the replay surfaced, the sources used; anything left undone becomes a `Pendência aberta`;
   - the ticket: check the course-page item and add a `## Notas de execução` section with one line pointing to that log entry by number;
   - `docs/glossario.md` (terms this lesson explained), `docs/referencia.md` (commands and patterns it introduced), `docs/recursos.md`, and any new block in `course/includes/`;
   - any new decision, appended at the end of `docs/decisions.md`.

   Then run the build set up in init (`uv run mkdocs build --strict` in `uv` projects) until it exits 0, and `rm -rf site`.
8. **Report** to the user in a few lines: the lesson's tangible win, what the replay verified, how to open it (`uv run mkdocs serve`, then `http://127.0.0.1:8000/NN-slug/`), a suggested commit message, and a reminder to come back after doing the lesson: their check-in shapes the next one.

## Fixed rules

- The skill writes documentation. `src/` and `tests/` stay exactly as the user left them, because the reader types the code while following the lesson and that typing is the learning. Write or validate real code only when the user explicitly asks for it.
- Commits, pushes and pull requests belong to the user: end with a suggested commit message and leave git alone.
- `docs/decisions.md` and `course/LOG.md` are append-only chronological logs: a new entry goes at the end, under a `## YYYY-MM-DD` section for today's date (created at the bottom if missing); earlier entries stay as written, and a correction is a new entry citing the old one.
- The course speaks the project's language (see its `AGENTS.md` and decisions); code identifiers follow the project's naming convention.
