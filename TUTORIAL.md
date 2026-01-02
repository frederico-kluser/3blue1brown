# Backend API para Geração de Vídeos Manim via LLM

O stack recomendado para construir este MVP é **Python 3.11 + FastAPI + OpenAI GPT-4o-mini + Manim CE 0.19.0**, com exposição via **Cloudflare Tunnel gratuito**. Com dedicação focada, um desenvolvedor pode ter o sistema funcional em **4-8 horas** seguindo este guia.

A arquitetura proposta recebe descrições em linguagem natural, transforma em código Manim via LLM, executa via subprocess isolado, e retorna o vídeo renderizado como base64 ou arquivo direto. O Cloudflare Tunnel elimina a necessidade de IP fixo ou portas abertas, fornecendo HTTPS automático gratuitamente.

---

## 1. Sumário executivo

### Stack tecnológico recomendado

| Componente | Tecnologia | Versão | Justificativa |
|------------|-----------|--------|---------------|
| **Runtime** | Python | 3.11+ | Melhor compatibilidade Manim CE |
| **API Framework** | FastAPI | 0.109+ | Async nativo, tipagem forte, docs automáticos |
| **LLM** | OpenAI GPT-4o-mini | latest | **17x mais barato** que GPT-4o, qualidade suficiente |
| **Renderização** | Manim CE | 0.19.0 | Versão de Janeiro 2025, ativamente mantido |
| **Vídeo** | FFmpeg | latest | Dependência obrigatória do Manim |
| **Exposição** | Cloudflare Tunnel | gratuito | HTTPS automático, sem portas abertas |

### Custo estimado por request
- **GPT-4o-mini**: ~$0.0006 (input 500 tokens + output 800 tokens)
- **GPT-4o** (alternativa): ~$0.01 por request
- Para 1000 vídeos/mês: **~$0.60** com GPT-4o-mini

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
OPENAI_MODEL=gpt-4o-mini

# App Configuration
APP_NAME="Manim Video Generator API"
DEBUG=false

# Manim Configuration
MANIM_QUALITY=l  # l=low(480p), m=medium(720p), h=high(1080p)
RENDER_TIMEOUT=120  # segundos

# Server
HOST=0.0.0.0
PORT=8000
```

---

## 3. Código do servidor API

### 3.1 Arquivo config.py

```python
# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    
    # App
    app_name: str = "Manim Video Generator API"
    debug: bool = False
    
    # Manim
    manim_quality: str = "l"  # l, m, h, k
    render_timeout: int = 120
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 3.2 Arquivo schemas.py

```python
# schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class VideoQuality(str, Enum):
    LOW = "l"       # 480p15
    MEDIUM = "m"    # 720p30
    HIGH = "h"      # 1080p60

class VideoRequest(BaseModel):
    description: str = Field(
        ..., 
        min_length=10, 
        max_length=2000,
        description="Descrição em linguagem natural do vídeo desejado"
    )
    quality: VideoQuality = Field(
        default=VideoQuality.LOW,
        description="Qualidade do vídeo: l=480p, m=720p, h=1080p"
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
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
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


def find_video(media_dir: Path, scene_name: str, quality: str) -> Optional[Path]:
    """Encontra o vídeo MP4 gerado pelo Manim."""
    quality_dirs = {
        "l": "480p15",
        "m": "720p30",
        "h": "1080p60",
        "k": "2160p60"
    }
    
    # Caminho padrão esperado
    quality_folder = quality_dirs.get(quality, "480p15")
    expected = media_dir / "videos" / "scene" / quality_folder / f"{scene_name}.mp4"
    
    if expected.exists():
        return expected
    
    # Busca recursiva como fallback
    for mp4 in media_dir.rglob("*.mp4"):
        if scene_name in mp4.name:
            return mp4
    
    return None


def execute_manim(
    code: str,
    scene_name: str,
    quality: str = "l",
    timeout: int = 120
) -> RenderResult:
    """
    Executa código Manim via subprocess de forma segura.
    
    Args:
        code: Código Python completo com Scene Manim
        scene_name: Nome da classe Scene a renderizar
        quality: l=480p, m=720p, h=1080p
        timeout: Timeout em segundos
    
    Returns:
        RenderResult com vídeo em base64 ou erro
    """
    with tempfile.TemporaryDirectory(prefix="manim_") as tmpdir:
        work_dir = Path(tmpdir)
        script_path = work_dir / "scene.py"
        media_dir = work_dir / "media"
        
        # Salvar código no arquivo temporário
        script_path.write_text(code)
        
        # Comando Manim - SEMPRE usar lista, NUNCA shell=True
        cmd = [
            "manim",
            "render",
            f"-q{quality}",
            "--media_dir", str(media_dir),
            "--disable_caching",
            str(script_path),
            scene_name
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(work_dir)
            )
        except subprocess.TimeoutExpired as e:
            return RenderResult(
                success=False,
                error=f"Render timeout after {timeout} seconds",
                stdout=e.stdout or "",
                stderr=e.stderr or ""
            )
        except Exception as e:
            return RenderResult(
                success=False,
                error=f"Subprocess error: {str(e)}"
            )
        
        # Verificar sucesso do Manim
        if result.returncode != 0:
            return RenderResult(
                success=False,
                error="Manim render failed",
                stdout=result.stdout,
                stderr=result.stderr
            )
        
        # Encontrar vídeo gerado
        video_path = find_video(media_dir, scene_name, quality)
        
        if not video_path:
            return RenderResult(
                success=False,
                error="Video file not found after render",
                stdout=result.stdout,
                stderr=result.stderr
            )
        
        # Converter para base64
        with open(video_path, "rb") as f:
            video_b64 = base64.b64encode(f.read()).decode('utf-8')
        
        return RenderResult(
            success=True,
            video_path=str(video_path),
            video_base64=video_b64,
            stdout=result.stdout,
            stderr=result.stderr
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
    return await generate_manim_code(request.description)


@app.post("/generate-video", response_model=VideoResponse)
async def generate_video(request: VideoRequest):
    """
    Endpoint principal: gera código Manim e renderiza vídeo.
    Retorna vídeo como base64.
    """
    # 1. Gerar código via LLM
    code_result = await generate_manim_code(request.description)
    
    if not code_result.is_valid:
        return VideoResponse(
            success=False,
            error=f"Code generation failed: {code_result.validation_message}"
        )
    
    # 2. Renderizar vídeo
    render_result = execute_manim(
        code=code_result.code,
        scene_name=code_result.scene_name,
        quality=request.quality.value,
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
    code_result = await generate_manim_code(request.description)
    
    if not code_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Code generation failed: {code_result.validation_message}"
        )
    
    # 2. Renderizar vídeo
    render_result = execute_manim(
        code=code_result.code,
        scene_name=code_result.scene_name,
        quality=request.quality.value,
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

### Parâmetros de chamada recomendados

```python
response = await client.chat.completions.create(
    model="gpt-4o-mini",     # Mais barato, suficiente para código
    messages=messages,
    temperature=0.2,          # Baixa para código determinístico
    max_tokens=2000,          # Suficiente para scenes complexas
    top_p=0.95,              # Ligeira diversidade mantida
    frequency_penalty=0.0,    # Não penalizar repetição (normal em código)
    presence_penalty=0.0
)
```

### Trade-off de modelos

| Cenário | Modelo Recomendado | Custo/Request |
|---------|-------------------|---------------|
| **MVP/Desenvolvimento** | gpt-4o-mini | ~$0.0006 |
| **Produção com qualidade** | gpt-4o | ~$0.01 |
| **Fallback barato** | gpt-3.5-turbo | ~$0.0002 |

---

## 5. Pipeline de renderização

### Fluxo de execução completo

```
1. REQUEST           2. LLM              3. VALIDAÇÃO         4. RENDERIZAÇÃO
   │                    │                   │                    │
   ▼                    ▼                   ▼                    ▼
┌──────────┐      ┌──────────┐        ┌──────────┐        ┌──────────┐
│ Descrição│──────│ OpenAI   │────────│ ast.parse│────────│subprocess│
│ em texto │      │ GPT-4o-m │        │ validate │        │ manim CLI│
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
  "openai_model": "gpt-4o-mini"
}
```

### 8.3 Gerar apenas código (debug)

```bash
curl -X POST http://localhost:8000/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a blue circle that grows from the center and then rotates 360 degrees",
    "quality": "l"
  }'

# Resposta esperada:
{
  "code": "from manim import *\n\nclass BlueCircle(Scene):\n    def construct(self):\n        circle = Circle(color=BLUE, fill_opacity=0.7)\n        self.play(GrowFromCenter(circle))\n        self.play(Rotate(circle, angle=2*PI), run_time=2)\n        self.wait()",
  "scene_name": "BlueCircle",
  "is_valid": true,
  "validation_message": "Code validated successfully"
}
```

### 8.4 Gerar vídeo completo (base64)

```bash
curl -X POST http://localhost:8000/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Show the Pythagorean theorem equation a² + b² = c² with a writing animation",
    "quality": "l"
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
    "quality": "m"
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
    "quality": "l"
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

## Script de setup automatizado

Salve como `setup.sh` e execute com `bash setup.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Configurando Manim API MVP..."

# 1. Dependências do sistema
echo "📦 Instalando dependências do sistema..."
sudo apt update
sudo apt install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-venv \
    libcairo2-dev \
    libpango1.0-dev \
    pkg-config \
    ffmpeg \
    texlive-latex-base \
    texlive-fonts-recommended

# 2. Estrutura do projeto
echo "📁 Criando estrutura do projeto..."
mkdir -p manim-api/services
cd manim-api

# 3. Ambiente virtual
echo "🐍 Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

# 4. Requirements
cat > requirements.txt << 'EOF'
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
openai>=1.12.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
manim>=0.19.0
aiofiles>=23.2.1
python-multipart>=0.0.6
EOF

pip install --upgrade pip
pip install -r requirements.txt

# 5. Verificação
echo "✅ Verificando instalações..."
manim --version
python -c "import openai; print('OpenAI:', openai.__version__)"
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"

# 6. Template .env
cat > .env.example << 'EOF'
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini
MANIM_QUALITY=l
RENDER_TIMEOUT=120
HOST=0.0.0.0
PORT=8000
DEBUG=false
EOF

cp .env.example .env

echo ""
echo "✅ Setup completo!"
echo ""
echo "📝 Próximos passos:"
echo "   1. Edite .env e adicione sua OPENAI_API_KEY"
echo "   2. Copie os arquivos Python do relatório"
echo "   3. Execute: source venv/bin/activate && uvicorn main:app --reload"
echo ""
```

---

Este relatório fornece uma implementação completa e funcional para o MVP do Backend API de Geração de Vídeos Manim via LLM. O sistema está pronto para ser copiado, configurado e executado, com um tempo estimado de **4-8 horas** até ter o primeiro vídeo gerado via API.
