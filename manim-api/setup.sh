#!/bin/bash
set -e

echo "🚀 Configurando Manim API MVP..."

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

echo "📁 Criando estrutura do projeto..."
mkdir -p manim-api/services
cd manim-api

echo "🐍 Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

echo "📄 Instalando requirements..."
cat > requirements.txt <<'REQ'
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
openai>=1.12.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
manim>=0.19.0
aiofiles>=23.2.1
python-multipart>=0.0.6
REQ

pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Verificando instalações..."
manim --version
python -c "import openai; print('OpenAI:', openai.__version__)"
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"

echo "📝 Criando .env example..."
cat > .env.example <<'ENV'
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini
MANIM_QUALITY=l
RENDER_TIMEOUT=120
HOST=0.0.0.0
PORT=8000
DEBUG=false
ENV

cp .env.example .env

echo "✅ Setup completo!"
echo "Atualize .env com sua chave e copie os arquivos Python do tutorial."
