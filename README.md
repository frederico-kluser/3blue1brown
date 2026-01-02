# Manim Video Generator (Manim CE 0.19.0 + GPT-5.1 Codex Max)

> **TL;DR**: Um backend FastAPI que converte descrições em linguagem natural em vídeos Manim, combinando Manim Community Edition 0.19.0 com o modelo **OpenAI GPT-5.1 Codex Max**. Este README concentra toda a documentação anterior e explica como instalar, configurar, operar e ampliar o projeto.

## Sumário
1. [Visão geral](#1-visão-geral)
2. [Arquitetura e fluxo end-to-end](#2-arquitetura-e-fluxo-end-to-end)
3. [Stack e pré-requisitos](#3-stack-e-pré-requisitos)
4. [Instalação](#4-instalação)
5. [Estrutura do projeto e configuração](#5-estrutura-do-projeto-e-configuração)
6. [Execução e exposição](#6-execução-e-exposição)
7. [Referência de API](#7-referência-de-api)
8. [Prompt engineering + modelos](#8-prompt-engineering--modelos)
9. [Referência rápida do Manim CE 0.19.0](#9-referência-rápida-do-manim-ce-0190)
10. [Operação e troubleshooting](#10-operação-e-troubleshooting)
11. [Próximos passos](#11-próximos-passos)

---

## 1. Visão geral
- **Objetivo**: gerar animações educacionais e científicas com o mínimo de esforço humano.
- **Entrega principal**: API REST com três endpoints (`/generate-code`, `/generate-video`, `/generate-video-file`).
- **Público**: educadores, criadores de conteúdo STEM, squads de produto e pesquisadores.
- **Diferenciais**:
  - Pipeline isolado: cada requisição compila e executa o código em subprocess Manim independente.
  - Prompt engineering opinativo: reforça versão correta do Manim (CE 0.19.0) e evita sintaxe legada do ManimGL.
  - Guia único com passos diretos (pip/uvicorn) para instalar dependências, criar o venv e rodar a API via terminal.

---

## 2. Arquitetura e fluxo end-to-end
1. **Entrada**: payload JSON com descrição textual da animação e (opcional) resolução.
2. **API FastAPI (`main.py`)**: valida o request (`schemas.py`), normaliza dimensões e roteia para os serviços.
3. **Geração de código (`services/openai_service.py`)**:
   - Monta mensagens via `prompts.py` (system prompt + few-shots + instruções específicas).
   - Chama o modelo GPT-5.1 Codex Max usando a SDK async (`openai` v1.x).
   - Extrai a cena, valida regras (import, Scene única, `construct`, `self.wait`, strings raw etc.).
4. **Execução Manim (`services/manim_executor.py`)**:
   - Salva o código em arquivo temporário, roda `manim` CLI no modo headless, força qualidade definida em `.env`.
   - Converte o `.mp4` gerado em base64 para envio inline.
5. **Resposta**: retorna logs estruturados, base64 ou streaming de arquivo.

Fluxo resumido: `Request -> FastAPI -> OpenAI -> Validação -> Manim CE -> Encode -> Response`.

---

## 3. Stack e pré-requisitos
| Camada | Tecnologia | Versão mínima | Observações |
|--------|------------|---------------|-------------|
| Runtime | Python | 3.11 | evita incompatibilidades do Manim CE 0.19.x |
| API | FastAPI | 0.109 | Docs automáticas (`/docs`) e async nativo |
| Server | Uvicorn | 0.27 | Worker ASGI leve |
| LLM | OpenAI GPT-5.1 Codex Max | latest | melhor custo/latência para código Manim |
| Render | Manim Community Edition | 0.19.0 | inclui PyAV, reduz dependência de ffmpeg externo |
| Vídeo | FFmpeg | 5.x/6.x | ainda usado para diagnósticos e conversões |
| Túnel | Cloudflared | latest | HTTPS público sem abrir portas |

### Pacotes do sistema
**Ubuntu/Debian**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  build-essential python3-dev python3-pip python3-venv \
  libcairo2-dev libpango1.0-dev pkg-config ffmpeg \
  curl cloudflared
# LaTeX mínimo
sudo apt install -y texlive-latex-base texlive-fonts-recommended
```

**macOS (Homebrew)**
```bash
brew update
brew install ffmpeg cairo pango pkg-config python@3.11 cloudflared
brew install --cask mactex-no-gui   # ou basictex + tlmgr install standalone preview
```

**Verificações rápidas**
```bash
ffmpeg --version
latex --version
python3 --version
```

---

## 4. Instalação
### 4.1 Criar ambiente virtual e dependências
```bash
cd manim-api
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env  # preencha OPENAI_API_KEY e demais variáveis
manim --version       # deve indicar Manim Community v0.19.0
```
> Execute os blocos acima diretamente no terminal. Em macOS use `python3`; em Linux certifique-se de ter o pacote `python3-venv` instalado.

### 4.2 Atualizar dependências existentes
```bash
cd manim-api
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### 4.3 Regenerar o `.env`
Se precisar criar um novo `.env`, copie novamente o template e edite manualmente:
```bash
cd manim-api
cp .env.example .env
# Abra o arquivo no editor e ajuste chaves/flags
```

---

## 5. Estrutura do projeto e configuração
```
3blue1brown/
├── README.md          # Este guia completo
└── manim-api/
    ├── main.py        # FastAPI + endpoints
    ├── config.py      # Settings via Pydantic
    ├── schemas.py     # Modelos de request/response
    ├── prompts.py     # System prompt + few-shots
    ├── services/
    │   ├── openai_service.py   # Geração/validação de código
    │   └── manim_executor.py   # Renderização isolada
    ├── media/         # Saídas do Manim (cache/diagnóstico)
    ├── requirements.txt
    ├── .env.example
    └── venv/ (criado durante o setup)
```

### Variáveis principais (`.env`)
| Nome | Exemplo | Descrição |
|------|---------|-----------|
| `OPENAI_API_KEY` | `sk-proj-...` | chave obrigatória |
| `OPENAI_MODEL` | `gpt-5.1-codex-max` | personalize se necessário |
| `MANIM_QUALITY` | `l` (`l/m/h/4k`) | define resolução padrão |
| `RENDER_TIMEOUT` | `120` | limite em segundos para cada render |
| `HOST` / `PORT` | `0.0.0.0` / `8000` | binding do Uvicorn |
| `DEBUG` | `false` | ativa `uvicorn --reload` se `true` |

---

## 6. Execução e exposição

### 6.1 API local
```bash
cd manim-api
source venv/bin/activate
uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --reload
```

Verifique o health-check:
```bash
curl http://127.0.0.1:8000/
# => {"status":"healthy","manim_version":"Manim Community v0.19.0","openai_model":"gpt-5.1-codex-max"}
```

Logs e vídeos gerados ficam em `manim-api/media`. Limpe periodicamente (`rm -rf manim-api/media/videos/*`).

### 6.2 Exposição Pública com Cloudflare Tunnel
O Cloudflare Tunnel permite expor sua API localmente para a internet de forma segura, sem abrir portas no firewall ou configurar port forwarding.

#### Pré-requisitos
- Conta gratuita na [Cloudflare](https://dash.cloudflare.com/sign-up)
- Domínio configurado com nameservers da Cloudflare

#### Instalação
**macOS (Homebrew):**
```bash
brew install cloudflared
```

**Ubuntu/Debian:**
```bash
curl -L https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-archive-keyring.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-archive-keyring.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install cloudflared
```

#### Configuração
**1. Autenticar na Cloudflare:**
```bash
cloudflared tunnel login
```
> Abrirá o navegador para autorizar. Selecione o domínio desejado.

**2. Criar o tunnel:**
```bash
cloudflared tunnel create manim-api
```
> Anote o **UUID** retornado (ex: `8bc73920-d12a-4e93-a113-b1f5f5cdcd6c`).

**3. Criar arquivo de configuração:**
Crie o arquivo `~/.cloudflared/config.yml`:
```yaml
tunnel: <UUID_DO_TUNNEL>
credentials-file: /Users/<SEU_USUARIO>/.cloudflared/<UUID_DO_TUNNEL>.json

ingress:
  - hostname: seudominio.com
    service: http://localhost:8000
  - service: http_status:404
```
> Substitua `<UUID_DO_TUNNEL>` pelo ID gerado e `<SEU_USUARIO>` pelo seu usuário do sistema.

**4. Configurar rota DNS:**
```bash
cloudflared tunnel route dns manim-api seudominio.com
```
> Isso cria automaticamente um registro CNAME na Cloudflare.

#### Execução
**Iniciar o tunnel manualmente:**
```bash
cloudflared tunnel run manim-api
```

**Instalar como serviço (execução em background):**

macOS:
```bash
sudo cloudflared service install
sudo launchctl start com.cloudflare.cloudflared
```

Linux:
```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

#### Verificação
Com o tunnel ativo e a API rodando (`uvicorn main:app --host 0.0.0.0 --port 8000`):
```bash
curl https://seudominio.com/
# => {"status":"healthy","manim_version":"Manim Community v0.19.0","openai_model":"gpt-5.1-codex-max"}
```

#### Comandos úteis
| Comando | Descrição |
|---------|-----------|
| `cloudflared tunnel list` | Lista todos os tunnels criados |
| `cloudflared tunnel info manim-api` | Detalhes do tunnel |
| `cloudflared tunnel delete manim-api` | Remove o tunnel |
| `cloudflared tunnel route dns manim-api sub.dominio.com` | Adiciona subdomínio |

#### Múltiplos serviços (opcional)
Para expor múltiplos serviços no mesmo tunnel:
```yaml
tunnel: <UUID_DO_TUNNEL>
credentials-file: /Users/<SEU_USUARIO>/.cloudflared/<UUID_DO_TUNNEL>.json

ingress:
  - hostname: api.seudominio.com
    service: http://localhost:8000
  - hostname: docs.seudominio.com
    service: http://localhost:3000
  - service: http_status:404
```
> Lembre-se de criar as rotas DNS para cada hostname adicional.

---

## 7. Referência de API
| Método | Caminho | Request | Resposta |
|--------|---------|---------|----------|
| `POST` | `/generate-code` | `{ description, width?, height? }` | `CodeResponse` com `code`, `scene_name`, `is_valid`, `validation_message` |
| `POST` | `/generate-video` | mesmo payload | `VideoResponse` com `video_base64` (mp4) |
| `POST` | `/generate-video-file` | mesmo payload | `video/mp4` direto no corpo + cabeçalho `Content-Disposition` |

### Exemplo de request
```bash
curl -X POST http://127.0.0.1:8000/generate-video \
  -H "Content-Type: application/json" \
  -d '{
        "description": "Show a blue circle growing then sliding right",
        "width": 1920,
        "height": 1080
      }'
```

### Schema (resumido)
```python
class VideoRequest(BaseModel):
    description: constr(min_length=10, max_length=2000)
    width: int | None = Field(ge=320, le=3840)
    height: int | None = Field(ge=320, le=3840)
```
Respostas incluem `render_logs` em caso de erro, úteis para debugar sintaxe ou assets ausentes.

---

## 8. Prompt engineering + modelos
### System prompt (trecho principal)
```
Você é um programador Python especialista em Manim CE 0.19.0.
- Sempre use `from manim import *`.
- Crie uma única classe Scene com método construct().
- Use `self.play()` para animação e finalize com `self.wait()`.
- Evite sintaxe ManimGL, use `Axes(x_range=[...])`, `hex_str`, strings raw.
```

### Few-shots recomendados
1. **Formas básicas**: círculo que cresce e desloca.
2. **Texto/MathTex**: equação aparecendo letra a letra.
3. **Transformações**: quadrado vermelho virando triângulo verde.

### Parâmetros sugeridos
```python
temperature = 0.0  # determinístico para código
max_tokens = 4000-8000
presence_penalty = 0.0
top_p = 0.9-0.95
```

### Escolha de modelo
| Aspecto | GPT-5.1 Codex Max | GPT-4o |
|---------|-------------------|--------|
| Contexto | 128k tokens | 128k tokens |
| Custo input/output | $0.20 / $0.80 (por 1M tokens) | $2.50 / $10.00 |
| Latência | baixa | média |
| Precisão em código Manim | excelente | excelente |
| Uso recomendado | pipelines em larga escala, protótipos rápidos | cenas 3D extremas ou fallback após falhas |

---

## 9. Referência rápida do Manim CE 0.19.0
### Fundamentos
```python
from manim import *

class MinhaCena(Scene):
    def construct(self):
        circle = Circle(color=BLUE, fill_opacity=0.6)
        self.play(Create(circle), run_time=1.5)
        self.play(circle.animate.shift(RIGHT * 2))
        self.wait()
```

### Classes de Scene
| Classe | Uso típico | Extras úteis |
|--------|-----------|--------------|
| `Scene` | 2D padrão | `play`, `wait`, `add` |
| `ThreeDScene` | objetos 3D/câmera | `set_camera_orientation`, `begin_ambient_camera_rotation` |
| `MovingCameraScene` | zoom/seguimento | `self.camera.frame.animate` |
| `ZoomedScene` | destaques com lupa | `activate_zooming`, `get_zoom_factor` |
| `LinearTransformationScene` | álgebra linear | auxiliares para matrizes/vetores |

### Mobjects (amostra)
| Categoria | Exemplos |
|-----------|----------|
| Formas | `Circle`, `Square`, `Triangle`, `Polygon`, `Line`, `Arc`, `Arrow` |
| Texto | `Text`, `Paragraph`, `MathTex`, `Tex` |
| Gráficos | `Axes`, `NumberPlane`, `FunctionGraph`, `BarChart` |
| Helpers | `VGroup`, `Group`, `SurroundingRectangle`, `Brace` |

### Animações populares
- `Create`, `Write`, `FadeIn/FadeOut`, `GrowFromCenter`, `Transform`, `ReplacementTransform`, `Indicate`.
- `mobject.animate.shift(...)`, `.scale(...)`, `.set_color(...)`.
- Sempre inclua `run_time` (1–2s) para ritmo consistente.

### Posicionamento e cores
- Vetores úteis: `UP`, `DOWN`, `LEFT`, `RIGHT`, `UL`, `UR`, `DL`, `DR`, `ORIGIN`.
- Métodos: `.shift`, `.move_to`, `.next_to`, `.to_edge`, `.to_corner`.
- Cores nomeadas (`BLUE`, `YELLOW`, `TEAL`) ou `ManimColor.from_hex(hex_str="#FF0000")`.

### CLI essencial
```bash
manim -pql scene.py SceneName        # preview low quality
manim -pqh scene.py SceneName        # preview high quality
manim render scene.py SceneName -ql  # CE 0.19.0 syntax
```
Use `config` para ajustes globais:
```python
from manim import config
config.background_color = WHITE
config.disable_caching = True
```

---

## 10. Operação e troubleshooting
- **FFmpeg/LaTeX ausentes**: reinstale os pacotes listados em [Stack e pré-requisitos](#3-stack-e-pré-requisitos) e repita os comandos de criação do venv.
- **Timeout render**: aumente `RENDER_TIMEOUT` ou reduza complexidade/qualidade.
- **Erro de import (`manimlib`)**: promova prompts que reforcem `from manim import *`.
- **LaTeX quebrado**: garanta strings raw (`r"..."`) e pacotes presentes (`texlive-fonts-recommended`).
- **Disco cheio**: limpe `manim-api/media/videos` e `manim-api/media/images` regularmente.
- **Cache incorreto**: use `config.disable_caching = True` ou remova `.cache/` se estiver habilitado.

---

## 11. Próximos passos
- Adicionar novos few-shots temáticos (geometria, estatística, branding).
- Instrumentar métricas (tempo de geração, tokens por request) usando middlewares FastAPI.
- Criar suite de testes com `pytest` + `httpx` simulando chamadas aos endpoints.
- Automatizar deploy (Dockerfile + GitHub Actions) documentando os comandos manuais de instalação.

Sinta-se à vontade para abrir issues ou PRs descrevendo melhorias na arquitetura, prompts ou exemplos de cena. Bom proveito! 🚀
