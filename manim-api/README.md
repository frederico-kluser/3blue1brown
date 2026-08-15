# Manim Video Generator API

Backend FastAPI que converte descrições em linguagem natural em cenas Manim renderizadas com suporte a OpenRouter.

## Visão geral
- **Stack**: Python 3.11, FastAPI, Manim CE 0.20.1, OpenRouter API (httpx).
- **Fluxo**: descrição → LLM gera código → validação AST → renderização via CLI → resposta JSON/base64.
- **Entrega**: Endpoints para health-check, geração de código e geração de vídeo (base64 ou arquivo), além de CLI `render_clip.py` para integração headless.

## Renderização headless de clipes

O script `render_clip.py` na raiz do repositório gera um MP4 a partir de uma descrição, com cor de fundo casada ao slide:

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
export MANIM_HOME=/caminho/para/este/repo
manim-api/venv/bin/python render_clip.py \
  --json '{"prompt":"um círculo azul crescendo","background_color":"#FFFFFF","out_dir":"./clips"}'
```

O JSON de saída contém o caminho do MP4, o renderizador usado e a validação de fundo.

## Setup rápido via terminal
1. Instale FFmpeg, Cairo, Pango, pkg-config, LaTeX e Cloudflared seguindo `TUTORIAL.md` (há receitas para macOS/Homebrew e Ubuntu/Debian). Confirme com `ffmpeg --version` e `latex --version`.
2. Crie e ative o ambiente virtual:
   ```bash
   cd manim-api
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   cp .env.example .env  # edite com sua OPENROUTER_API_KEY
   ```
3. Suba o servidor diretamente com o Uvicorn:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Para sessões futuras, apenas ative o `venv` e execute novamente o comando do Uvicorn. Atualize dependências com `pip install -r requirements.txt --upgrade` quando necessário.

## Cloudflare Tunnel sem login
1. Instale o binário (`brew install cloudflared` no macOS ou siga a doc oficial no Linux).
2. Gere um link público efêmero direto no terminal:
   ```bash
   cloudflared tunnel --url http://localhost:8000 --no-autoupdate
   ```
   - A saída exibirá uma URL `https://<algo>.trycloudflare.com` que pode ser usada imediatamente a partir do front-end.
   - Ajuste a porta trocando o valor após `--url`.
3. Para um túnel persistente com domínio próprio, siga os passos padrão da Cloudflare: `cloudflared tunnel login`, `cloudflared tunnel create <nome>`, configure `~/.cloudflared/config.yml` apontando para `http://localhost:8000` e finalize com `cloudflared tunnel run <nome>` (ou instale o serviço via `cloudflared service install`).

## Integração com OpenAI Responses API
- **Modelo único**: `gpt-5.1-codex-max`, acessado exclusivamente pelo endpoint `/v1/responses` (não funciona em Chat Completions).
- **Esforço de raciocínio**: sempre `reasoning={"effort": "xhigh"}` para maximizar consistência em cenas complexas.
- **Formato de chamada**:
  ```python
  from openai import AsyncOpenAI

  client = AsyncOpenAI()
  response = await client.responses.create(
      model="gpt-5.1-codex-max",
      input=[
          {"role": "system", "content": "instrua a criação de cenas Manim CE"},
          {"role": "user", "content": prompt_otimizado}
      ],
      reasoning={"effort": "xhigh"}
  )
  code = response.output_text
  ```
- Toda a API usa esse formato tanto para otimizar o prompt quanto para gerar o código final; o serviço extrai texto via `response.output_text` antes de validar com AST.

## Pipeline inteligente com gpt-5.1-codex-max
1. **Otimização de prompt** – o serviço chama `gpt-5.1-codex-max` (Responses API) para interpretar a descrição original, anexar o inventário de recursos (FastAPI, executor Manim, validações AST, Cloudflare Tunnel) e gerar uma versão enriquecida do pedido.
2. **Geração de código** – o prompt otimizado, acompanhado das capacidades disponíveis, alimenta um segundo request ao mesmo modelo (também via Responses API) para emitir o código Manim final seguindo o template CE.
3. **Validação + render** – o código passa por AST e listas de bloqueio antes de chegar ao executador Manim/FFmpeg, garantindo segurança e cenas < 30s.

## Endpoints principais
- `GET /` – Health check com versão do Manim e modelo OpenAI.
- `POST /generate-code` – Retorna apenas o código Manim gerado e validado.
- `POST /generate-video` – Retorna vídeo em base64 (JSON `VideoResponse`).
- `POST /generate-video-file` – Faz download direto do MP4.

Consulte `TUTORIAL.md` para pipeline completo, testes end-to-end e configuração do Cloudflare Tunnel.

## Visão detalhada do projeto

### O que o projeto faz
- API FastAPI que aceita descrições em linguagem natural, usa o GPT-5.1 Codex Max para gerar código Manim CE 0.19.x, valida o código e renderiza a cena via CLI, retornando vídeo em base64 ou arquivo MP4.
- Stack principal: Python 3.11, FastAPI, Manim CE, OpenAI SDK async, FFmpeg/LaTeX/Cairo como dependências nativas.

### Como consumir
1. Suba o servidor local: `cd manim-api && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000`.
2. Use os endpoints documentados (`/generate-code`, `/generate-video`, `/generate-video-file`) enviando JSON `{ "description": "..." }`; envie `width`/`height` apenas se quiser outra resolução (padrão 1920x1080 16:9).
3. A coleção Postman `postman_collection.json` pode ser importada e parametrizada com `{{base_url}}` (`http://localhost:8000` ou o link Cloudflare).

### Localhost e link público simultâneos
- Execute o servidor normalmente em `localhost:8000`.
- Em outro terminal, rode `cloudflared tunnel --url http://localhost:8000 --no-autoupdate` para criar um túnel efêmero `.trycloudflare.com` sem login.
- Ambos funcionam em paralelo: clientes locais usam `http://localhost:8000` e usuários remotos usam o domínio fornecido pelo Cloudflare.

### Configurações principais
- `.env` define `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` (padrão `deepseek/deepseek-v4-pro`), `OPENROUTER_BASE_URL`, `RENDER_TIMEOUT`, `DEFAULT_FPS`, `HOST`, `PORT`, `DEBUG`. A resolução é informada por request (campos opcionais `width`/`height`, padrão 1920x1080 em 16:9; para clipes de slide, 1280x720).
- Dependências de sistema: FFmpeg, libcairo, pango, pkg-config e LaTeX mínimo.

### Coleção Postman
- Localizada em `manim-api/postman_collection.json` com requests para health, código e vídeo.
- Atualize a variável `base_url` conforme o endpoint utilizado (localhost ou túnel).

## Tutorial completo

# Backend API para Geração de Vídeos Manim via LLM

O stack recomendado para construir este MVP é **Python 3.11 + FastAPI + OpenAI GPT-5.1 Codex Max + Manim CE 0.19.0**, com exposição via **Cloudflare Tunnel gratuito**. Com dedicação focada, um desenvolvedor pode ter o sistema funcional em **4-8 horas** seguindo este guia.

A arquitetura proposta recebe descrições em linguagem natural, transforma em código Manim via LLM, executa via subprocess isolado, e retorna o vídeo renderizado como base64 ou arquivo direto. O Cloudflare Tunnel elimina a necessidade de IP fixo ou portas abertas, fornecendo HTTPS automático gratuitamente.

---

## 1. Sumário executivo

### Stack tecnológico recomendado

| Componente | Tecnologia | Versão | Justificativa |
|------------|-----------|--------|---------------|
| **Runtime** | Python | 3.11+ | Melhor compatibilidade Manim CE |
| **API Framework** | FastAPI | 0.109+ | Async nativo, tipagem forte, docs automáticos |
| **LLM** | OpenAI GPT-5.1 Codex Max | latest | Modelo de código especializado recomendado para todas as fases |
| **Renderização** | Manim CE | 0.19.0 | Versão de Janeiro 2025, ativamente mantido |
| **Vídeo** | FFmpeg | latest | Dependência obrigatória do Manim |
| **Exposição** | Cloudflare Tunnel | gratuito | HTTPS automático, sem portas abertas |

### Custo estimado por request
- **GPT-5.1 Codex Max**: consulte a tabela oficial do link https://platform.openai.com/docs/models/gpt-5.1-codex-max. Para referência, com ~500 tokens de entrada e ~800 de saída projetamos ~US$0.0006 por chamada.
- Para 1000 vídeos/mês: orçamento aproximado de **US$0.60** (ajuste conforme métricas reais).

### Tempo estimado até MVP funcional

| Fase | Tempo | Descrição |
|------|-------|-----------|
| Setup ambiente | 30-60 min | Dependências, Python, FFmpeg, LaTeX |
| Código API | 1-2 horas | FastAPI + OpenAI integration |
| Teste/Debug | 1-2 horas | Ajustes de prompts e pipeline |
| Cloudflare Tunnel | 30 min | Configuração e exposição |
| **Total** | **4-8 horas** | Sistema funcional end-to-end |

---

## 2. Setup de ambiente

### 2.1 Pré-requisitos de sistema

**Sistema Operacional:** Ubuntu 22.04/24.04 LTS (recomendado) ou Debian 12

**Versões testadas:**
- Python 3.11 ou 3.12
- FFmpeg 5.x ou 6.x
- Manim CE 0.19.0 (lançado 20/01/2025)

### 2.2 Instalação de dependências do sistema

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Dependências essenciais para Manim
sudo apt install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-venv \
    libcairo2-dev \
    libpango1.0-dev \
    pkg-config \
    ffmpeg

# LaTeX (necessário para MathTex e fórmulas matemáticas)
# Versão mínima (~300MB):
sudo apt install -y texlive-latex-base texlive-fonts-recommended

# Versão completa (~2GB, recomendada para MVP robusto):
# sudo apt install -y texlive texlive-latex-extra texlive-fonts-extra texlive-science

# Verificar instalações
ffmpeg -version
python3 --version
```

### 2.3 Estrutura de diretórios do projeto

```
manim-api/
├── main.py              # Servidor FastAPI principal
├── config.py            # Configurações e settings
├── services/
│   ├── __init__.py
│   ├── openai_service.py    # Integração com OpenAI
│   └── manim_executor.py    # Execução segura do Manim
├── schemas.py           # Modelos Pydantic
├── prompts.py           # System prompts e exemplos
├── requirements.txt     # Dependências Python
├── .env                 # Variáveis de ambiente (NÃO commitar)
├── .env.example         # Template do .env
└── README.md
```

### 2.4 Criação do ambiente virtual e dependências

```bash
# Criar diretório do projeto
mkdir manim-api && cd manim-api

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Verificar instalação do Manim
manim --version
# Esperado: Manim Community v0.19.0
```

### 2.5 Arquivo requirements.txt completo

```txt
# requirements.txt

# Web Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0

# OpenAI
openai>=1.12.0

# Validation & Settings
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Environment
python-dotenv>=1.0.0

# Manim (Community Edition)
manim>=0.19.0

# Utilities
aiofiles>=23.2.1
python-multipart>=0.0.6

# Dev/Testing (opcional)
pytest>=7.4.0
httpx>=0.26.0
```

### 2.6 Arquivo .env template

```bash
# .env.example (copiar para .env e preencher)

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-5.1-codex-max

# App Configuration
APP_NAME="Manim Video Generator API"
DEBUG=false

# Manim Configuration
RENDER_TIMEOUT=120  # segundos
MANIM_RENDERER=auto  # "auto" (detecta GPU), "cairo" (força CPU), "opengl" (força GPU)
MANIM_RENDERER_FALLBACK=true  # se true, quando o render OpenGL falhar (via "auto" ou "opengl"), tenta novamente com Cairo

# Server
HOST=0.0.0.0
PORT=8000
```

---

## 3. Código do servidor API

### 3.1 Arquivo config.py

```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-5.1-codex-max"
    
    # App
    app_name: str = "Manim Video Generator API"
    debug: bool = False
    
    # Manim
    render_timeout: int = 120
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 3.2 Arquivo schemas.py

```python
# schemas.py
from pydantic import BaseModel, Field
from typing import Optional

class VideoRequest(BaseModel):
    description: str = Field(
        ..., 
        min_length=10, 
        max_length=2000,
        description="Descrição em linguagem natural do vídeo desejado"
    )
    width: int | None = Field(
        default=None,
        ge=320,
        le=3840,
        description="(Opcional) Largura do vídeo em pixels"
    )
    height: int | None = Field(
        default=None,
        ge=320,
        le=3840,
        description="(Opcional) Altura do vídeo em pixels"
    )

class CodeResponse(BaseModel):
    code: str
    scene_name: str
    is_valid: bool
    validation_message: str

class VideoResponse(BaseModel):
    success: bool
    video_base64: Optional[str] = None
    content_type: str = "video/mp4"
    scene_name: Optional[str] = None
    error: Optional[str] = None
    render_logs: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    manim_version: str
    openai_model: str
```

### 3.3 Arquivo prompts.py

```python
# prompts.py

MANIM_SYSTEM_PROMPT = """You are an expert Manim Community Edition developer. Generate valid, executable Manim code based on user descriptions.

## CRITICAL RULES:
1. ALWAYS use `from manim import *` (Community Edition syntax)
2. Create a SINGLE Scene class with a descriptive PascalCase name
3. Implement the `construct(self)` method with all animations
4. Use `self.play()` for EVERY animation
5. ALWAYS end with `self.wait()` or `self.wait(1)` for proper video ending
6. Keep total animation duration under 30 seconds
7. Use smooth, professional animation timings (run_time=1 to 2 seconds)

## CODE TEMPLATE:
```python
from manim import *

class SceneName(Scene):
    def construct(self):
        # Create objects
        # Animate with self.play()
        self.wait()
```

## AVAILABLE MOBJECTS:
- Shapes: Circle, Square, Rectangle, Triangle, Polygon, Line, Arrow, Dot, Arc
- Text: Text(\"text\"), MathTex(\"LaTeX\"), Tex(\"LaTeX text\")
- Groups: VGroup, Group
- Graphs: Axes, NumberPlane, FunctionGraph
- Colors: RED, BLUE, GREEN, YELLOW, WHITE, PURPLE, ORANGE, PINK, TEAL

## KEY ANIMATIONS:
- Create(mobject) - draws progressively
- Write(text) - writing animation for text
- FadeIn(mobject), FadeOut(mobject)
- Transform(source, target), ReplacementTransform(source, target)
- mobject.animate.method() - animate any property change
- Rotate(mobject, angle=PI), Scale(mobject, factor)
- GrowFromCenter(mobject)

## POSITIONING:
- .to_edge(UP/DOWN/LEFT/RIGHT)
- .shift(LEFT * 2), .shift(RIGHT * 3 + UP * 1)
- .move_to(ORIGIN), .next_to(other, RIGHT)
- Constants: UP, DOWN, LEFT, RIGHT, ORIGIN, UL, UR, DL, DR

## OUTPUT FORMAT:
Return ONLY the Python code wrapped in ```python ``` markers.
NO explanations before or after the code.
"""

FEW_SHOT_EXAMPLES = [
    {
        "user": "Create a blue circle that grows and then moves to the right",
        "assistant": """```python
from manim import *

class BlueCircleAnimation(Scene):
    def construct(self):
        circle = Circle(color=BLUE, fill_opacity=0.7)
        self.play(GrowFromCenter(circle), run_time=1)
        self.play(circle.animate.shift(RIGHT * 3), run_time=1.5)
        self.wait()
```"""
    },
    {
        "user": "Show the equation E=mc² appearing letter by letter",
        "assistant": """```python
from manim import *

class EinsteinEquation(Scene):
    def construct(self):
        equation = MathTex("E", "=", "m", "c^2")
        equation.scale(2)
        
        self.play(Write(equation[0]), run_time=0.5)
        self.play(Write(equation[1]), run_time=0.3)
        self.play(Write(equation[2]), run_time=0.5)
        self.play(Write(equation[3]), run_time=0.7)
        
        self.play(equation.animate.set_color(YELLOW), run_time=0.5)
        self.wait()
```"""
    },
    {
        "user": "Transform a red square into a green triangle",
        "assistant": """```python
from manim import *

class SquareToTriangle(Scene):
    def construct(self):
        square = Square(color=RED, fill_opacity=0.8)
        triangle = Triangle(color=GREEN, fill_opacity=0.8)
        
        self.play(Create(square), run_time=1)
        self.wait(0.5)
        self.play(Transform(square, triangle), run_time=1.5)
        self.wait()
```"""
    }
]


def build_messages(user_prompt: str) -> list:
    """Constrói lista de mensagens com few-shot examples."""
    messages = [{"role": "system", "content": MANIM_SYSTEM_PROMPT}]
    
    for example in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": example["user"]})
        messages.append({"role": "assistant", "content": example["assistant"]})
    
    messages.append({"role": "user", "content": user_prompt})
    
    return messages
```

### 3.4 Arquivo services/openai_service.py

```python
# services/openai_service.py
import re
import ast
from openai import AsyncOpenAI
from config import get_settings
from prompts import build_messages
from schemas import CodeResponse

settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)

# Validação de segurança
DANGEROUS_IMPORTS = {
    'os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib',
    'requests', 'pickle', 'ctypes', 'multiprocessing', 'pty'
}

DANGEROUS_FUNCTIONS = {'eval', 'exec', 'open', '__import__', 'compile'}


def extract_code(response: str) -> str:
    """Extrai código Python de resposta markdown."""
    pattern = r"```python\s*(.*?)\s*```"
    matches = re.findall(pattern, response, re.DOTALL)
    if matches:
        return matches[0].strip()
    
    # Fallback: código sem marcadores
    if "from manim import" in response:
        return response.strip()
    
    raise ValueError("Could not extract valid Manim code from response")


def get_scene_name(code: str) -> str:
    """Extrai nome da classe Scene do código."""
    pattern = r"class\s+(\w+)\s*\(\s*(?:Scene|ThreeDScene|MovingCameraScene)\s*\)"
    match = re.search(pattern, code)
    if match:
        return match.group(1)
    raise ValueError("Could not find Scene class in code")


def validate_code(code: str) -> tuple[bool, str]:
    """Valida código Manim antes de executar."""
    # 1. Verificar sintaxe Python
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    
    # 2. Verificar import obrigatório
    if "from manim import" not in code:
        return False, "Missing 'from manim import' statement"
    
    # 3. Verificar classe Scene
    if "(Scene)" not in code and "(ThreeDScene)" not in code:
        return False, "Missing Scene class definition"
    
    # 4. Verificar método construct
    if "def construct(self)" not in code:
        return False, "Missing construct method"
    
    # 5. Verificar imports/funções perigosas
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split('.')[0]
                if module in DANGEROUS_IMPORTS:
                    return False, f"Forbidden import: {alias.name}"
        
        elif isinstance(node, ast.ImportFrom):
            module = (node.module or '').split('.')[0]
            if module in DANGEROUS_IMPORTS:
                return False, f"Forbidden import: from {node.module}"
        
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in DANGEROUS_FUNCTIONS:
                    return False, f"Forbidden function: {node.func.id}()"
    
    return True, "Code validated successfully"


async def generate_manim_code(description: str) -> CodeResponse:
    """Gera código Manim a partir de descrição em linguagem natural."""
    try:
        messages = build_messages(description)
        
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.2,  # Baixa para código determinístico
            max_tokens=2000
        )
        
        raw_response = response.choices[0].message.content
        code = extract_code(raw_response)
        scene_name = get_scene_name(code)
        is_valid, message = validate_code(code)
        
        return CodeResponse(
            code=code,
            scene_name=scene_name,
            is_valid=is_valid,
            validation_message=message
        )
        
    except Exception as e:
        return CodeResponse(
            code="",
            scene_name="",
            is_valid=False,
            validation_message=str(e)
        )
```

### 3.5 Arquivo services/manim_executor.py

```python
# services/manim_executor.py
import base64
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from config import get_settings

settings = get_settings()


@dataclass
class RenderResult:
    success: bool
    video_path: Optional[str] = None
    video_base64: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None


def _resolve_texlive_bin() -> Optional[Path]:
    texlive_root = Path.home() / "texlive"
    if not texlive_root.exists():
        return None
    candidates = sorted(texlive_root.glob("*/bin/*"), reverse=True)
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def find_video(media_dir: Path, scene_name: str) -> Optional[Path]:
    """Localiza o MP4 independente da pasta/qualidade utilizada."""
    expected_root = media_dir / "videos"
    candidates = sorted(
        expected_root.rglob("*.mp4") if expected_root.exists() else media_dir.rglob("*.mp4"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for mp4 in candidates:
        if scene_name in mp4.stem:
            return mp4
    return candidates[0] if candidates else None


def execute_manim(
    code: str,
    scene_name: str,
    width: int = 1920,
    height: int = 1080,
    timeout: int = 120,
) -> RenderResult:
    with tempfile.TemporaryDirectory(prefix="manim_") as tmpdir:
        work_dir = Path(tmpdir)
        script_path = work_dir / "scene.py"
        media_dir = work_dir / "media"
        script_path.write_text(code)

        cmd = [
            "manim",
            "render",
            "-r",
            f"{width},{height}",
            "--fps",
            "60",
            "--media_dir",
            str(media_dir),
            "--disable_caching",
            str(script_path),
            scene_name,
        ]

        env = os.environ.copy()
        texlive_bin = _resolve_texlive_bin()
        if texlive_bin and texlive_bin.exists():
            env["PATH"] = f"{texlive_bin}:{env.get('PATH', '')}"

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(work_dir),
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            return RenderResult(
                success=False,
                error=f"Render timeout after {timeout} seconds",
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
            )
        except Exception as exc:
            return RenderResult(success=False, error=f"Subprocess error: {exc}")

        if result.returncode != 0:
            return RenderResult(
                success=False,
                error="Manim render failed",
                stdout=result.stdout,
                stderr=result.stderr,
            )

        video_path = find_video(media_dir, scene_name)
        if not video_path:
            return RenderResult(
                success=False,
                error="Video file not found after render",
                stdout=result.stdout,
                stderr=result.stderr,
            )

        video_b64 = base64.b64encode(video_path.read_bytes()).decode("utf-8")
        return RenderResult(
            success=True,
            video_path=str(video_path),
            video_base64=video_b64,
            stdout=result.stdout,
            stderr=result.stderr,
        )
```

### 3.6 Arquivo main.py - Servidor completo

```python
# main.py
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from schemas import (
    VideoRequest, VideoResponse, CodeResponse, HealthResponse
)
from services.openai_service import generate_manim_code
from services.manim_executor import execute_manim

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API para gerar vídeos Manim via descrições em linguagem natural",
    version="1.0.0"
)

# CORS para acesso externo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustar em produção
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def health():
    """Health check com informações do sistema."""
    try:
        result = subprocess.run(
            ["manim", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        manim_version = result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        manim_version = "error"
    
    return HealthResponse(
        status="healthy",
        manim_version=manim_version,
        openai_model=settings.openai_model
    )


@app.post("/generate-code", response_model=CodeResponse)
async def generate_code(request: VideoRequest):
    """
    Gera código Manim a partir de descrição, sem renderizar.
    Útil para debug e preview do código.
    """
    return await generate_manim_code(
        description=request.description,
        width=request.width,
        height=request.height,
    )


@app.post("/generate-video", response_model=VideoResponse)
async def generate_video(request: VideoRequest):
    """
    Endpoint principal: gera código Manim e renderiza vídeo.
    Retorna vídeo como base64.
    """
    # 1. Gerar código via LLM
    code_result = await generate_manim_code(
        description=request.description,
        width=request.width,
        height=request.height,
    )

    if not code_result.is_valid:
        return VideoResponse(
            success=False,
            error=f"Code generation failed: {code_result.validation_message}"
        )
    
    # 2. Renderizar vídeo
    render_result = execute_manim(
        code=code_result.code,
        scene_name=code_result.scene_name,
        width=request.width,
        height=request.height,
        timeout=settings.render_timeout
    )

    if not render_result.success:
        return VideoResponse(
            success=False,
            error=render_result.error,
            render_logs=render_result.stderr
        )
    
    return VideoResponse(
        success=True,
        video_base64=render_result.video_base64,
        scene_name=code_result.scene_name
    )


@app.post("/generate-video-file")
async def generate_video_file(request: VideoRequest):
    """
    Gera vídeo e retorna arquivo MP4 diretamente (não base64).
    Ideal para download direto.
    """
    # 1. Gerar código via LLM
    code_result = await generate_manim_code(
        description=request.description,
        width=request.width,
        height=request.height,
    )

    if not code_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Code generation failed: {code_result.validation_message}"
        )
    
    # 2. Renderizar vídeo
    render_result = execute_manim(
        code=code_result.code,
        scene_name=code_result.scene_name,
        width=request.width,
        height=request.height,
        timeout=settings.render_timeout
    )

    if not render_result.success:
        raise HTTPException(
            status_code=500,
            detail=f"Render failed: {render_result.error}\n{render_result.stderr}"
        )
    
    # Retornar arquivo diretamente
    import base64
    video_bytes = base64.b64decode(render_result.video_base64)
    
    return Response(
        content=video_bytes,
        media_type="video/mp4",
        headers={
            "Content-Disposition": f'attachment; filename="{code_result.scene_name}.mp4"'
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
```

---

## 4. Integração com OpenAI

### System prompt otimizado

O system prompt no arquivo `prompts.py` foi projetado com as seguintes características:

- **Regras explícitas** de sintaxe Manim CE (não ManimGL)
- **Template de código** garantindo estrutura válida
- **Lista de Mobjects e Animations** mais usados
- **Restrições de duração** (máximo 30 segundos)
- **Formato de output** forçando apenas código em markdown

### Dupla etapa de prompts
1. `optimize_prompt()` → chama `gpt-5.1-codex-max` para reescrever a descrição, explicar suposições e detalhar como aproveitar os recursos disponíveis.
2. `generate_manim_code()` → usa o prompt enriquecido (com recursos e notas) para produzir o código final do Manim CE.

### Parâmetros de chamada recomendados

```python
response = await client.chat.completions.create(
    model="gpt-5.1-codex-max",     # Mais barato, suficiente para código
    messages=messages,
    temperature=0.2,          # Baixa para código determinístico
    max_tokens=2000,          # Suficiente para scenes complexas
    top_p=0.95,              # Ligeira diversidade mantida
    frequency_penalty=0.0,    # Não penalizar repetição (normal em código)
    presence_penalty=0.0
)
```

### Política de modelos

Todo o pipeline usa exclusivamente `gpt-5.1-codex-max`, tanto para otimização de prompt quanto para geração do código Manim. Isso elimina bifurcações, garante consistência e simplifica a governança de custos: ajuste apenas os parâmetros de tokens conforme seu workload.

---

## 5. Pipeline de renderização

### Fluxo de execução completo

```
1. REQUEST           2. LLM              3. VALIDAÇÃO         4. RENDERIZAÇÃO
   │                    │                   │                    │
   ▼                    ▼                   ▼                    ▼
┌──────────┐      ┌──────────┐        ┌──────────┐        ┌──────────┐
│ Descrição│──────│ OpenAI   │────────│ ast.parse│────────│subprocess│
│ em texto │      │ GPT-5.1 Codex Max │        │ validate │        │ manim CLI│
└──────────┘      └──────────┘        └──────────┘        └──────────┘
                       │                   │                    │
                       ▼                   ▼                    ▼
                  código Manim        ✓ válido            /tmp/manim_xxx/
                  em Python           ✗ erro              media/videos/
                                                               │
5. CAPTURA           6. CONVERSÃO        7. RESPONSE            │
   │                    │                   │                    ▼
   ▼                    ▼                   ▼               SceneName.mp4
┌──────────┐      ┌──────────┐        ┌──────────┐
│ find_video│──────│ base64   │────────│  JSON    │
│ .mp4     │      │ encode   │        │ response │
└──────────┘      └──────────┘        └──────────┘
```

### Estrutura de arquivos temporários

```
/tmp/manim_abc123/
├── scene.py                    # Código gerado
└── media/
    └── videos/
        └── scene/
            └── 480p15/
                ├── SceneName.mp4           # Vídeo final
                └── partial_movie_files/    # Frames intermediários
```

### Mapeamento de qualidade

| Flag | Pasta | Resolução | FPS | Tempo típico |
|------|-------|-----------|-----|--------------|
| `-ql` | 480p15 | 854×480 | 15 | 5-15s |
| `-qm` | 720p30 | 1280×720 | 30 | 15-30s |
| `-qh` | 1080p60 | 1920×1080 | 60 | 1-3min |
| `-qk` | 2160p60 | 3840×2160 | 60 | 5-10min |

---

## 6. Exposição via Cloudflare Tunnel

### Visão geral

Cloudflare Tunnel é **100% gratuito** e cria uma conexão segura do seu servidor local para a rede Cloudflare, sem necessidade de IP público fixo ou portas abertas.

```
[Internet] ←HTTPS→ [Cloudflare Edge] ←Tunnel→ [cloudflared] ←HTTP→ [localhost:8000]
```

### 6.1 Instalação do cloudflared

```bash
# Ubuntu/Debian - via repositório oficial
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg > /dev/null

echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main" | sudo tee /etc/apt/sources.list.d/cloudflared.list

sudo apt-get update && sudo apt-get install -y cloudflared

# Verificar instalação
cloudflared --version
```

### 6.2 Autenticação e criação do tunnel

```bash
# 1. Autenticar (abre navegador ou exibe URL)
cloudflared tunnel login

# 2. Criar tunnel com nome identificável
cloudflared tunnel create manim-api

# 3. Anotar o UUID retornado (ex: a1b2c3d4-5678-90ab-cdef-1234567890ab)

# 4. Criar rota DNS (substitua pelo seu domínio)
cloudflared tunnel route dns manim-api api.seudominio.com
```

### 6.3 Arquivo de configuração

Criar `~/.cloudflared/config.yml`:

```yaml
# ~/.cloudflared/config.yml
tunnel: a1b2c3d4-5678-90ab-cdef-1234567890ab  # Seu UUID
credentials-file: /home/SEU_USER/.cloudflared/a1b2c3d4-5678-90ab-cdef-1234567890ab.json

ingress:
  - hostname: api.seudominio.com
    service: http://localhost:8000
  
  # Catch-all obrigatório (sempre no final)
  - service: http_status:404
```

### 6.4 Executar como serviço systemd

```bash
# Mover configurações para /etc/cloudflared
sudo mkdir -p /etc/cloudflared
sudo cp ~/.cloudflared/config.yml /etc/cloudflared/
sudo cp ~/.cloudflared/*.json /etc/cloudflared/

# Atualizar caminho no config.yml
sudo sed -i "s|/home/$USER/.cloudflared|/etc/cloudflared|g" /etc/cloudflared/config.yml

# Instalar serviço
sudo cloudflared service install

# Iniciar e habilitar
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Verificar status
sudo systemctl status cloudflared
```

### 6.5 Comandos úteis

```bash
# Ver logs em tempo real
sudo journalctl -u cloudflared -f

# Reiniciar após mudanças
sudo systemctl restart cloudflared

# Verificar tunnels ativos
cloudflared tunnel list

# Testar manualmente (debug)
cloudflared tunnel --loglevel debug run manim-api
```

---

## 7. Roadmap de implementação

| Fase | Tarefa | Tempo | Dependências | Prioridade |
|------|--------|-------|--------------|------------|
| **1** | Instalar dependências sistema (FFmpeg, Cairo, LaTeX) | 15-30 min | Sistema base | 🔴 Crítico |
| **2** | Criar ambiente Python e instalar requirements | 10 min | Fase 1 | 🔴 Crítico |
| **3** | Configurar .env com OpenAI API key | 5 min | Conta OpenAI | 🔴 Crítico |
| **4** | Implementar config.py e schemas.py | 10 min | Fase 2 | 🔴 Crítico |
| **5** | Implementar prompts.py com system prompt | 15 min | - | 🔴 Crítico |
| **6** | Implementar openai_service.py | 20 min | Fase 5 | 🔴 Crítico |
| **7** | Implementar manim_executor.py | 25 min | Fase 1 | 🔴 Crítico |
| **8** | Implementar main.py (FastAPI server) | 20 min | Fases 4-7 | 🔴 Crítico |
| **9** | Testar localmente com curl | 20 min | Fase 8 | 🔴 Crítico |
| **10** | Instalar cloudflared | 10 min | - | 🟡 Importante |
| **11** | Configurar Cloudflare Tunnel | 20 min | Domínio no Cloudflare | 🟡 Importante |
| **12** | Configurar como serviço systemd | 10 min | Fase 11 | 🟢 Nice-to-have |
| **13** | Teste end-to-end externo | 10 min | Fase 11 | 🟡 Importante |

**Total estimado: 3-5 horas** (primeira vez, sem interrupções)

---

## 8. Teste end-to-end

### 8.1 Iniciar o servidor

```bash
cd manim-api
source venv/bin/activate

# Modo desenvolvimento (com auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Modo produção
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

### 8.2 Health check

```bash
curl http://localhost:8000/

# Resposta esperada:
{
  "status": "healthy",
  "manim_version": "Manim Community v0.19.0",
  "openai_model": "gpt-5.1-codex-max"
}
```

### 8.3 Gerar apenas código (debug)

```bash
curl -X POST http://localhost:8000/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a blue circle that grows from the center and then rotates 360 degrees"
  }'

# Resposta esperada:
{
  "code": "from manim import *\n\nclass BlueCircle(Scene):\n    def construct(self):\n        circle = Circle(color=BLUE, fill_opacity=0.7)\n        self.play(GrowFromCenter(circle))\n        self.play(Rotate(circle, angle=2*PI), run_time=2)\n        self.wait()",
  "scene_name": "BlueCircle",
  "is_valid": true,
  "validation_message": "Code validated successfully"
}
```
> Sem informar `width`/`height`, assume 1920x1080 @ 60 fps.

### 8.4 Gerar vídeo completo (base64)

```bash
curl -X POST http://localhost:8000/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Show the Pythagorean theorem equation a² + b² = c² with a writing animation",
    "width": 1280,
    "height": 720
  }' | jq .

# Resposta esperada (truncada):
{
  "success": true,
  "video_base64": "AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1w...",
  "content_type": "video/mp4",
  "scene_name": "PythagoreanTheorem",
  "error": null
}
```

### 8.5 Baixar vídeo como arquivo

```bash
# Salvar vídeo diretamente
curl -X POST http://localhost:8000/generate-video-file \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Transform a red square into a blue circle with smooth animation",
    "width": 1080,
    "height": 1080
  }' --output video.mp4

# Verificar arquivo
file video.mp4
# Esperado: video.mp4: ISO Media, MP4 v2 [ISO 14496-14]
```

### 8.6 Testar via Cloudflare Tunnel (externo)

```bash
# Após configurar tunnel
curl -X POST https://api.seudominio.com/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Draw a simple sine wave graph with animated curve",
    "width": 1080,
    "height": 1920
  }'
```

---

## 9. Problemas conhecidos e soluções

### Erros comuns de instalação

| Erro | Causa | Solução |
|------|-------|---------|
| `ModuleNotFoundError: pycairo` | Cairo não instalado | `sudo apt install libcairo2-dev` e reinstalar manim |
| `LaTeX not found` | TexLive ausente | `sudo apt install texlive-latex-base` |
| `ffmpeg not found` | FFmpeg não no PATH | `sudo apt install ffmpeg` |
| `ManimPango build failed` | Headers faltando | `sudo apt install libpango1.0-dev` |

### Erros em runtime

| Erro | Causa | Solução |
|------|-------|---------|
| `Scene 'X' not found` | Nome da cena incorreto | Verificar regex de extração no `get_scene_name()` |
| `TimeoutExpired` | Renderização muito lenta | Usar `-ql` ou aumentar `render_timeout` |
| `Video not found after render` | Caminho diferente | Verificar estrutura de pastas, usar busca recursiva |
| `OpenAI RateLimitError` | Muitas requests | Implementar retry com backoff ou usar tier pago |

### Edge cases de geração de código

| Problema | Exemplo | Mitigação |
|----------|---------|-----------|
| Código sem Scene class | LLM gera apenas funções | Few-shot com templates corretos |
| Import de módulos externos | `import numpy as np` errado | Whitelist de imports permitidos |
| Animações muito longas | >60 segundos | Prompt com limite explícito |
| MathTex sem LaTeX | Servidor sem texlive | Instruir LLM a usar `Text()` como fallback |

### Limitações do MVP

- **Single-threaded**: Apenas uma renderização por vez
- **Sem cache**: Mesma descrição gera código diferente
- **Sem retry**: Falha de OpenAI não é retentada
- **Arquivos temporários**: Limpeza automática pode falhar em crash
- **Sem autenticação**: API aberta (mitigar com Cloudflare Access)

---

## 10. Próximos passos pós-MVP

### Melhorias de curto prazo (Prioridade Alta)

1. **Adicionar API Key authentication**
   ```python
   from fastapi.security import APIKeyHeader
   api_key = APIKeyHeader(name="X-API-Key")
   ```

2. **Implementar cache de código gerado**
   - Hash da descrição como key
   - Evita chamadas repetidas à OpenAI

3. **Adicionar rate limiting**
   ```bash
   pip install slowapi
   ```

4. **Logs estruturados**
   - Usar `structlog` para JSON logging
   - Métricas de tempo de geração/renderização

### Melhorias de médio prazo

5. **Fila de renderização com Celery/Redis**
   - Para múltiplas requests simultâneas
   - Status tracking de jobs

6. **Retry automático da OpenAI**
   - Backoff exponencial
   - Fallback para modelo alternativo

7. **Preview do código antes de renderizar**
   - Endpoint separado `/preview`
   - Permite usuário validar antes de gastar tempo de render

8. **Suporte a templates customizados**
   - Usuário pode fornecer template base
   - Few-shot examples personalizados

### Melhorias de longo prazo

9. **Docker Compose para deploy**
   - Container Manim isolado
   - Scaling horizontal

10. **UI Web simples**
    - React/Vue frontend
    - Preview em tempo real

11. **Histórico de gerações**
    - SQLite para persistência
    - Re-renderização de código salvo

12. **Múltiplas qualidades por request**
    - Gerar 480p, 720p, 1080p em paralelo

---

## Referência rápida de comandos
1. Criar/ativar ambiente:
   ```bash
   cd manim-api
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Instalar dependências e preparar `.env`:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   cp .env.example .env  # edite OPENAI_API_KEY e demais variáveis
   ```
3. Rodar a API no terminal:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Atualizar dependências quando necessário:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

---

Este relatório fornece uma implementação completa e funcional para o MVP do Backend API de Geração de Vídeos Manim via LLM. O sistema está pronto para ser copiado, configurado e executado, com um tempo estimado de **4-8 horas** até ter o primeiro vídeo gerado via API.
