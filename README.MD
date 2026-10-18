# My Skills

Coleção das minhas **skills** e **agentes** personalizados para o [Claude Code](https://claude.com/claude-code).

## Conteúdo

| Tipo | Nome | O que faz |
|------|------|-----------|
| Agente | [`project-builder`](agents/project-builder.md) | Transforma um briefing bruto (trabalho, metodologia, ideia) em um esqueleto de projeto já documentado, antes de qualquer código. |
| Skill | [`project-builder`](project-builder/SKILL.md) | Atalho `/project-builder <briefing>` que despacha o agente de mesmo nome. |
| Skill | [`mkdocs-project-course`](mkdocs-project-course/SKILL.md) | Transforma os tickets de um projeto em um curso MkDocs para iniciantes, uma aula por ticket. |
| Skill | [`geron-hands-on-ml`](geron-hands-on-ml/SKILL.md) | Base de conhecimento do livro *Hands-On Machine Learning* (Géron, 3ª ed.) para aplicar seus frameworks e receitas em projetos de ML. |

## project-builder

Roda, nesta ordem: **grilling → domain-modeling → to-spec → to-tickets**, mantendo um log cronológico em `docs/decisions.md` o tempo todo.

Entrega:

```
docs/
├── decisions.md        # log append-only das decisões
├── issues/             # spec (0000-*) + tickets (01-*, 02-*, ...) em ordem de dependência
└── adr/                # criado sob demanda
README.md
AGENTS.md               # guia canônico para qualquer agente de IA
CLAUDE.md               # apenas importa @AGENTS.md
```

Não escreve código de aplicação, não faz commit/push e não inventa decisões: pergunta ao usuário via `AskUserQuestion` sempre que há uma bifurcação real.

**Dependências:** usa as skills `grilling`, `domain-modeling`, `to-spec` e `to-tickets`, que **não estão neste repositório** e precisam estar instaladas.

**Uso:**

```
/project-builder <cole aqui o briefing>
```

## mkdocs-project-course

Constrói, a partir dos tickets deixados pelo `project-builder`, um site MkDocs em que cada aula ensina um iniciante a implementar um ticket digitando o código ele mesmo. As aulas são calibradas ao progresso do aluno (missão, o que já sabe, onde travou), com recordação ativa (perguntas, previsões, exercícios) e verificação por *replay*: todo comando e teste da aula é executado antes de publicá-la.

Arquivos de apoio: [`SCAFFOLD.md`](mkdocs-project-course/SCAFFOLD.md) (preparação inicial), [`LESSON-TEMPLATE.md`](mkdocs-project-course/LESSON-TEMPLATE.md) (estrutura das aulas) e [`COURSE-STATE.md`](mkdocs-project-course/COURSE-STATE.md) (estado do aluno e histórico do curso).

**Uso:**

```
/mkdocs-project-course init        # prepara o site e aprende a missão do aluno
/mkdocs-project-course 03          # escreve a aula do ticket 03
/mkdocs-project-course revisar 03  # revisa uma aula existente
/mkdocs-project-course progresso   # registra como a última aula foi
```

**Requer:** projeto com `docs/issues/NN-*.md` (idealmente gerado pelo `project-builder`) e [`uv`](https://docs.astral.sh/uv/) para o build do MkDocs.

## geron-hands-on-ml

Base de conhecimento gerada a partir de *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow* (3ª ed.), de Aurélien Géron. O [`SKILL.md`](geron-hands-on-ml/SKILL.md) traz os frameworks centrais do livro (checklist de projeto de ML, dados ruins vs. modelo ruim, disciplina de pipelines no Scikit-Learn, avaliação de classificadores, receitas de treino de redes profundas, mapa de arquiteturas, produção e escala, RL) e índices por capítulo e por tópico. Quando a pergunta vai além disso, o agente lê o capítulo correspondente antes de responder.

Arquivos de apoio:

- [`chapters/`](geron-hands-on-ml/chapters/): um resumo por capítulo (`ch01`–`ch19`) e pelos apêndices (checklist do apêndice A; internals do TensorFlow nos apêndices B–D).
- [`cheatsheet.md`](geron-hands-on-ml/cheatsheet.md): regras de decisão rápidas ("treino ótimo, validação ruim → overfitting", "classes desbalanceadas → ignore acurácia"...).
- [`patterns.md`](geron-hands-on-ml/patterns.md): técnicas com quando usar, como e trade-offs (split estratificado, `ColumnTransformer`, shortlist → busca → ensemble...).
- [`glossary.md`](geron-hands-on-ml/glossary.md): glossário de termos com referência ao capítulo.

**Uso:**

```
/geron-hands-on-ml                     # carrega os frameworks centrais
/geron-hands-on-ml precision/recall    # responde sobre um tópico, lendo o capítulo relevante
/geron-hands-on-ml ch07                # carrega um capítulo específico
```

Também é acionada automaticamente quando a conversa envolve pipelines do Scikit-Learn, avaliação de modelos, ensembles, Keras/TensorFlow, CNNs, RNNs/transformers, modelos generativos, RL ou deploy.

## Instalação

Skills ficam em `~/.claude/skills/<nome>/` e agentes em `~/.claude/agents/`:

```bash
git clone <url-deste-repositorio> && cd <pasta>

# skills
mkdir -p ~/.claude/skills ~/.claude/agents
cp -r project-builder mkdocs-project-course geron-hands-on-ml ~/.claude/skills/

# agente
cp agents/project-builder.md ~/.claude/agents/
```

Para uso apenas em um projeto, copie para `.claude/skills/` e `.claude/agents/` dentro dele.

## Fluxo típico

1. `/project-builder <briefing>` → projeto documentado, com spec e tickets.
2. `/mkdocs-project-course init` → curso preparado.
3. `/mkdocs-project-course <ticket>` para cada ticket, seguido de `/mkdocs-project-course progresso`.
