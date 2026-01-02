# Manim Video Generator API

Backend FastAPI que converte descrições em linguagem natural em cenas Manim renderizadas com suporte a OpenAI GPT-4o-mini.

## Visão geral
- **Stack**: Python 3.11, FastAPI, Manim CE 0.19.0, Async OpenAI API.
- **Fluxo**: descrição → LLM gera código → validação AST → renderização via CLI → resposta JSON/base64.
- **Entrega**: Endpoints para health-check, geração de código e geração de vídeo (base64 ou arquivo).

## Configuração rápida
1. Instale FFmpeg, Cairo e LaTeX conforme descrito em `TUTORIAL.md`.
2. Crie o ambiente:
   ```bash
   cd manim-api
   python3 -m venv venv && source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   cp .env.example .env  # e preencha OPENAI_API_KEY
   ```
3. Inicie o servidor:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Endpoints principais
- `GET /` – Health check com versão do Manim e modelo OpenAI.
- `POST /generate-code` – Retorna apenas o código Manim gerado e validado.
- `POST /generate-video` – Retorna vídeo em base64 (JSON `VideoResponse`).
- `POST /generate-video-file` – Faz download direto do MP4.

Consulte `TUTORIAL.md` para pipeline completo, testes end-to-end e configuração do Cloudflare Tunnel.
