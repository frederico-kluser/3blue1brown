# Plano de Tarefa — Manim sobre Slides

> Plano de execução derivado do documento de especificação entregue pelo usuário.
> Autorização implícita via "tome suas próprias decisões".

## Objetivo

Tornar o repositório `3blue1brown` (fábrica de clipes) capaz de produzir clipes Manim com fundo casado ao slide, chamável por subprocesso, e migrar todo LLM para OpenRouter.

## Escopo deste repositório (A)

- Onda 0: scripts de verificação de ambiente e asserção de pixel.
- Onda 1: CLI `render_clip.py`, injeção de cor de fundo, correção do TinyTeX.
- Onda 2: migração de OpenAI para OpenRouter.
- Onda 5: documentação (AGENTS.md, README.md) e skill compartilhada.

## Fora de escopo

- Canal alfa/transparência.
- Geração de imagem.
- Alterações no deck/slides (repo B).

## Critérios de aceitação gerais

- Todo gate descrito na especificação passa na máquina local.
- `scripts/assert_bg.py` valida pixel a pixel o fundo dos clipes.
- Nenhum segredo é commitado.
- Todos os logs carregam prefixo `[request_id]`.

## Notas

- O venv do projeto está em `manim-api/venv/`, não na raiz. Os comandos usam esse caminho.
- `MANIM_HOME` será exportado como `/home/ondokai/Projects/3blue1brown` para a sessão.
