---
name: project-router
description: Routes EVERY implementation task in this codebase to the correct skills BEFORE any step. Use whenever the user asks for any change, fix, feature, analysis, or refactor, even if they do not mention skills. Always asks clarifying questions in Brazilian Portuguese before executing.
metadata:
  type: router
  verification_signal: "python3 .agents/scripts/run_skill_evals.py project-router"
---
# Project Router

**IMPORTANT: todas as perguntas e interações com o usuário são SEMPRE em PORTUGUÊS BRASILEIRO.**

## Protocol (execute ANTES de qualquer trabalho)

1. **FAÇA MUITAS PERGUNTAS (em português).** Antes de qualquer coisa, faça VÁRIAS perguntas esclarecedoras para refinar a tarefa: escopo exato, entradas e saídas esperadas, restrições, edge cases, critérios de aceitação e o que explicitamente NÃO fazer. Não avance enquanto a tarefa estiver subespecificada; continue perguntando até que a ambiguidade desapareça.

2. **Crie um arquivo de plano de tarefa** (`TASK_PLAN.md`), em português, com o plano detalhado, passos e critérios de aceitação acordados com o usuário.

3. **Classifique a tarefa:** domínio(s) afetado(s), tipo (bug/feature/refactor/análise), complexidade.

4. **Consulte `catalog.md`** e selecione as skills de conhecimento + tarefa relevantes. Na dúvida, prefira a skill mais específica do domínio.

5. **Monte a CADEIA de skills** (ordem + o que pode rodar em paralelo via subagentes de contexto isolado).

6. **Carregue o conhecimento das skills selecionadas** ANTES de implementar.

7. **Execute a cadeia** seguindo o `TASK_PLAN.md`.

8. **AO CONCLUIR:** (a) execute o `<evolution>` de cada skill de tarefa envolvida; (b) DELETE o arquivo `TASK_PLAN.md` — ele é descartável e não deve permanecer no repositório.

## Regras

- Se nenhuma skill cobre a tarefa, invoque `meta-skill-evolution` para PROPOR uma nova skill (rascunho para revisão humana, não publicação direta).
- Skills com efeitos colaterais amplos (deploy, mudanças estruturais) NÃO são auto-invocáveis sem confirmação do usuário.
- Nunca pule o passo de evolution ao concluir. Nunca deixe `TASK_PLAN.md` para trás.
- `TASK_PLAN.md` é descartável e é deletado ao final; os artefatos de bootstrap (`project-analysis.md`, `skill-map.md`, `catalog.md`, `validation-report.md`, `.bootstrap-state.json`) NÃO — nunca os delete.

## Mapeamento rápido de domínios

| Se a tarefa toca em... | Carregar skill... |
|------------------------|-------------------|
| Geração de código Manim, prompts, validação | `manim-code-gen` |
| Renderização, execução Manim, vídeo | `manim-rendering` |
| API, endpoints, schemas, config, deploy | `fastapi-app` |
| Nenhuma skill cobre | `meta-skill-evolution` (propor nova) |
