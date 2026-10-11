# Scaffold

The init branch of [SKILL.md](SKILL.md): learn who the learner is, set up the MkDocs site, the course home page, the course state and the project conventions, before the first lesson.

## 0. Learn the mission

Every lesson is calibrated to the learner, so start with them. Ask with `AskUserQuestion`, then follow up on anything vague:

- **Why** they are building this project (a course assignment, learning the stack for work, a personal project, ...): push past "to learn X" to the concrete outcome.
- **Starting point**: never programmed, programs in another language, knows this language but not this stack — and which tools they already use (terminal, git, an editor).
- **Operating system** they study on.
- **Communities**: whether they want pointers to places where people answer beginners' questions.

Write `course/MISSION.md` from the answers and confirm it with the learner; record prior knowledge as learning records and preferences (operating system, communities yes/no) in `course/NOTES.md`, all per [COURSE-STATE.md](COURSE-STATE.md). Done when the learner has confirmed the mission.

## 1. Ask the look

Ask with `AskUserQuestion`, every time (the look is chosen per project):

- **Palette**: a custom palette (navy blue is one ready option, below; any other needs the hex colors from the user), a Material preset color (`indigo`, `teal`, `deep purple`, ...), or the Material default.
- **Dark mode**: a light/dark toggle, or light only.

## 2. Install MkDocs

- Project managed by `uv` (has `pyproject.toml` and `uv.lock`) → `uv add --dev mkdocs mkdocs-material`, then `uv run mkdocs --version`.
- Anything else → ask the user how they want to run MkDocs (a `uv` docs environment, `pipx`, an existing virtualenv) before installing anything.

## 3. Write `mkdocs.yml`

```yaml
site_name: <nome do curso>
site_description: <uma frase sobre o que o leitor vai construir>
theme:
  name: material
  language: pt-BR            # idioma do projeto
  features:
    - navigation.footer      # botões "anterior / próxima aula"
    - navigation.sections
    - navigation.top
    - content.code.annotate  # anotações numeradas no código
    - content.code.copy
    - content.tabs.link      # abas por sistema operacional sincronizadas
    - search.highlight
  palette: <passo 1>
extra_css:                   # só com paleta customizada
  - stylesheets/extra.css
markdown_extensions:
  - admonition
  - attr_list
  - md_in_html
  - tables
  - toc:
      permalink: true
  - pymdownx.details         # blocos recolhíveis (quiz, soluções, código completo)
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets:
      base_path: ["."]
      check_paths: true
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true
nav:
  - Início: index.md
```

Append to `nav` an `Apoio` section with the three course-support pages from step 4 (`Glossário: glossario.md`, `Referência rápida: referencia.md`, `Recursos: recursos.md`), then the project documents that already exist: `Log de Decisões: decisions.md`, the ADRs, and the issues (spec + tickets). The `Curso` section is added by the first lesson: an empty section fails the build.

Palette values:

- Material preset, light only: `palette: {primary: indigo, accent: indigo}`.
- Custom, light only: `palette: {primary: custom, accent: custom}` plus `docs/stylesheets/extra.css`.
- With the dark-mode toggle, `palette` becomes a list of two schemes, the same colors in both:

  ```yaml
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: custom
      accent: custom
      toggle: {icon: material/brightness-7, name: Mudar para modo escuro}
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: custom
      accent: custom
      toggle: {icon: material/brightness-4, name: Mudar para modo claro}
  ```

The navy blue custom palette, `docs/stylesheets/extra.css`:

```css
[data-md-color-primary="custom"] {
  --md-primary-fg-color: #0b1f3a;
  --md-primary-fg-color--light: #24406b;
  --md-primary-fg-color--dark: #061428;
  --md-primary-bg-color: #ffffff;
}

[data-md-color-accent="custom"] {
  --md-accent-fg-color: #3f6fb0;
  --md-accent-fg-color--transparent: rgba(63, 111, 176, 0.1);
  --md-accent-bg-color: #ffffff;
}
```

Another custom palette uses the same variables with the user's colors.

## 4. Write the course pages and state

`docs/index.md`, the course home page, for the same beginner the lessons are written for:

- **O que você vai construir**: the project in two or three sentences, from the spec's problem statement, and what it does when finished.
- **Para quem é este curso**: no prior knowledge of the stack assumed; what the reader does need (a computer, time, willingness to type the code); the learner's goal from `course/MISSION.md`, in reader-facing words.
- **Como usar este curso**: answer the "Relembrando" questions from memory → read the lesson → type the code yourself → run the commands → compare your output with the "Saída esperada" → do the exercises until their tests pass, trying before looking at the solution → answer the quiz before opening the answers → commit → tell the agent how it went (`/mkdocs-project-course progresso`), which shapes the next lesson. Say why: typing beats copying, and recalling beats rereading.
- **Como ler os blocos de código**: the file path in the title, the `(+)` markers that open annotations, the separate command and output blocks, the copy button.
- **Pré-requisitos gerais**: operating system, internet, a text editor; tool installation is taught inside the lessons.
- **Mapa das aulas**: a table with one row per ticket: `| Aula | O que você constrói | Ticket | Status |`. Status is `em breve` until the lesson is written, then the row links the lesson. Tickets with no lesson (closing, report) get a row saying so.

The support pages, each starting with one line on what it is for and growing with every lesson, in the formats of [COURSE-STATE.md](COURSE-STATE.md):

- `docs/glossario.md`, empty of terms;
- `docs/referencia.md`, empty of entries;
- `docs/recursos.md`, already holding the sources read for this step (the official documentation of each tool in the stack, fetched now) and, if the learner wants them, the communities.

The learner's state and history: `course/MISSION.md` and `course/NOTES.md` from step 0, `course/LOG.md` with its header and a first `Curso montado` entry (written in step 6, once the look is known), and an empty `course/includes/` (with a `.gitkeep`). `course/learning-records/` is created by the first record.

## 5. Adjust `.gitignore`

Add `site/`. Assets that live under `docs/` must not reuse a directory name the `.gitignore` ignores: a pattern without a leading slash (such as `results/`) matches at every depth, so `docs/assets/results/` would be silently left out of git.

## 6. Record the conventions

- `AGENTS.md`, under a conventions section (create it if missing): the course comes before the code; each ticket's lesson is written with `/mkdocs-project-course <ticket>` (one per ticket, split when it carries too many new concepts) and the learner's progress is recorded with `/mkdocs-project-course progresso`; `course/` holds the learner's state; `src/` and `tests/` are written by the user following the lessons, and an agent writes real code only when the user explicitly asks.
- `AGENTS.md`, in the same section, the handoff line for any agent or tool, with or without the skill: before working on the course, read `course/MISSION.md`, the last entries and open pending items of `course/LOG.md`, `course/learning-records/` and `course/NOTES.md`; record every lesson written or revised and every learner check-in as a new entry at the end of `course/LOG.md`.
- `course/LOG.md`: the `Curso montado` entry (mission in a line, starting point, look chosen, the records and notes created).
- `docs/decisions.md`: append an entry at the end, under today's date, recording that the course was scaffolded, the look chosen, and the one-lesson-per-ticket rule.

## Done

When the learner has confirmed the mission, `uv run mkdocs build --strict` (or the equivalent chosen in step 2) exits 0, the course map has one row per ticket, and `course/LOG.md` holds the `Curso montado` entry. Then `rm -rf site` and report to the user what was set up, which lesson comes first (`/mkdocs-project-course <ticket>`), and a suggested commit message.
