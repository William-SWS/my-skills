# Course state

Reference for both branches of [SKILL.md](SKILL.md): the files that hold the learner's state, the course's history and the course's shared knowledge. Init creates them; every lesson reads them before writing and updates them after. Together they are the **handoff**: everything another agent or model needs to pick the course up where it stopped, without this conversation.

Two audiences, two places:

- **The learner's state and the course history**, read by agents, live in `course/` at the repo root, outside `docs/`, so MkDocs never publishes them.
- **The course's shared knowledge**, read by the reader, lives in `docs/` as pages under an "Apoio" section of the nav.

Each file holds one kind of meaning, so nothing is written twice:

| File | Holds |
|---|---|
| `docs/decisions.md` | decisions about the project and the course (look, splits, conventions) |
| `course/LOG.md` | the course history: lessons written and revised, check-ins in the learner's words, open and closed pending items |
| `course/learning-records/` | distilled facts about what the learner knows |
| `course/NOTES.md` | how the learner likes to be taught |
| `course/MISSION.md` | why the learner is here |

A new agent reads, in this order: `course/MISSION.md`, the last entries and the open pending items of `course/LOG.md`, `course/learning-records/`, `course/NOTES.md`.

## `course/MISSION.md`

Why the learner is building this project. The compass for every lesson: what to emphasize, which examples to pick, how each concept connects to something the learner cares about.

```md
# Missão: {projeto}

## Por quê
{1-3 frases: o objetivo concreto do aprendiz. "Entregar o trabalho da disciplina X e entender o que entreguei" vale mais que "aprender Python".}

## Sucesso é
- {algo específico e observável que o aprendiz vai conseguir fazer}

## Ponto de partida
- {o que já sabe e em que profundidade: "nunca programou", "programa em Java há 2 anos", "usa git só pelo editor"}

## Restrições
- {tempo, prazo, sistema operacional, preferências de estudo}

## Fora de escopo
- {assuntos vizinhos que o aprendiz não quer seguir agora}
```

Concrete over abstract; push back on a vague "why" before writing it down. One screen at most. When the goal shifts, confirm with the learner, update the file and write a learning record about the change.

## `course/LOG.md`

The course history, append-only and chronological, in the same shape as `docs/decisions.md`: one `## YYYY-MM-DD` section per date at the bottom, entries numbered continuously across dates, each new entry at the end. Earlier entries stay as written; a correction is a new entry that cites the old one by number.

```md
# Histórico do curso

Registro cronológico da produção do curso e do acompanhamento do aprendiz. Cada evento entra no fim, sob a data em que ocorreu; entradas antigas não são reescritas.

## 2026-10-01

1. **Curso montado** (`init`): missão "entender de ponta a ponta o primeiro programa"; tema indigo; LR 0001 (nunca programou); NOTES (estuda no Linux).
2. **Aula 01 escrita**: `docs/01-primeira-saudacao.md` (ticket 01). Cobre ambiente de projeto e função. Calibração: o terminal é explicado desde abrir a janela (LR 0001). Adiado para a aula 02: anotações de tipo, para manter três conceitos. Replay: verde; a entrada pelo teclado precisou de pseudo-terminal. Fontes: docs do uv, tutorial do Python.
3. **Check-in da aula 01**: "fiz tudo, mas não entendi por que o teste importa de `src`" (palavras do aprendiz). Registrado: LR 0002 (equívoco sobre o caminho de importação). Ação: a aula 02 abre o Relembrando com essa pergunta.
4. **Pendência aberta**: o passo 2 da aula 01 não diz em qual pasta criar o arquivo.
5. **Pendência fechada** (ref. nº 4): passo 2 da aula 01 agora diz `src/`; replay refeito, verde.
```

Entry kinds:

- **Curso montado**: the mission in a line, the starting point, the look, the records created.
- **Aula escrita** / **Aula revisada**: file and ticket, what it covers, the calibration choices and the learning records or notes behind them, what was deferred or split and why, what the replay surfaced, the sources used. A revision also says what changed, why, and which pending item it closes.
- **Check-in**: the learner's own words, quoted; where each piece went (which learning record, `NOTES.md`, a pending item); what the next lesson will do about it. Everything the learner says lands here, including what does not qualify as a learning record.
- **Pendência aberta**: anything left to do on the course (a lesson to revise, a source still missing, a question for the learner). **Pendência fechada** cites the entry it closes. Open pending items are the ones no later entry closes.

## `course/learning-records/NNNN-slug.md`

What the learner has demonstrably learned, already knew, or got wrong: the evidence that places the next lesson in their **zone of proximal development** (hard enough to stretch, close enough to reach). Created lazily, numbered from `0001`, one or two sentences each:

```md
# {o que foi aprendido ou estabelecido}

{1-3 frases: o que agora se sabe sobre o aprendiz e por que isso muda as próximas aulas.}
```

Write one when the learner:

1. **demonstrated** understanding of something non-trivial (an exercise done without the solution, a quiz question explained in their own words) — later lessons recap it in a line and link back;
2. **disclosed** prior knowledge ("já sei git"), with the depth claimed — later lessons skip the full explanation;
3. **had a misconception corrected** — later lessons touching that area address it head-on in a callout;
4. **shifted the mission**.

Coverage is not learning: a lesson the learner read is not a record. When understanding changes, mark the old record `Status: superseded by NNNN` instead of deleting it.

## `course/NOTES.md`

How the learner likes to be taught, in their words: shorter explanations, more analogies, one operating system, studying on the phone. Read before every lesson; append when the learner expresses a preference.

## `docs/glossario.md`

The course's canonical language. Every lesson uses the glossary's word for each concept, and only that word.

```md
# Glossário

### Ambiente de projeto
A "caixa" com o Python e as bibliotecas de um único projeto, criada e mantida pelo `uv`.
_Evite_: venv, virtualenv. Aula: [01](01-primeira-saudacao.md#ambiente-de-projeto)
```

- One `###` per term, so lessons can link straight to it (`glossario.md#ambiente-de-projeto`).
- A term enters the glossary in the lesson that explains it, with a link back to that lesson.
- Definitions say what the term **is**, in one or two sentences, using earlier glossary terms where they fit.
- Be opinionated: when several words name the same thing, pick one and list the rest under _Evite_.
- Domain terms follow the project's `CONTEXT.md` when one exists.

## `docs/referencia.md`

The compressed essence of the course, the page the reader comes back to: commands, code patterns and short recipes, grouped by tool or task (`uv`, `git`, testes, ...), each with a one-line "quando usar" and a link to the lesson that taught it. Every lesson adds what it introduced.

## `docs/recursos.md`

The curated, high-trust sources the course is built on.

```md
# Recursos

## Conhecimento
- [Documentação do uv](https://docs.astral.sh/uv/)
  Referência oficial do gerenciador de projetos. Use para: instalação, `uv run`, `uv add`.

## Comunidades
- [Python Brasil](https://python.org.br/)
  Comunidade brasileira de Python. Use para: tirar dúvidas e conversar com quem já usa a linguagem.

## Lacunas
- {assunto que o curso precisa e para o qual não há boa fonte}
```

- Primary sources first (official documentation, recognized books, the library's own tutorial); marketing dressed as education stays out.
- Annotate every entry: what it covers and when to reach for it.
- A source enters only after it was actually read in this session, never from memory.
- Communities only if the learner wants them (recorded in `course/NOTES.md`).
- Prune what turned out wrong or shallow.

## `course/includes/`

Reusable blocks that more than one lesson needs (how to open the terminal, installing a tool, how to run the tests). A lesson pulls one in with `--8<-- "course/includes/<arquivo>.md"`; inside an admonition or tab, indent that line to the block's level. Read the folder before writing a lesson and reuse what is there; write a block here the moment a second lesson would repeat it.
