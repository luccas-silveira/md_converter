FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dependências do sistema para WeasyPrint e ferramentas úteis
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    build-essential \
    pkg-config \
    curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar e instalar dependências (app completo com IA)
COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Defaults de produção (podem ser sobrescritos via env)
ENV FLASK_ENV=production \
    FLASK_DEBUG=0 \
    LOG_LEVEL=INFO \
    MAX_CONTENT_LENGTH=1073741824 \
    UPLOAD_FOLDER=/tmp \
    SEND_FILE_MAX_AGE=0 \
    WORKERS=1 \
    THREADS=2 \
    TIMEOUT=300 \
    PRELOAD=1 \
    ACCESS_LOG=- \
    ERROR_LOG=- \
    OPENAI_MODEL=gpt-4o-mini

EXPOSE 5000

# Usar gunicorn em produção, lendo variáveis de ambiente
CMD ["sh", "-lc", "exec gunicorn -b 0.0.0.0:5000 server:app --workers ${WORKERS:-1} --threads ${THREADS:-2} --timeout ${TIMEOUT:-300} ${PRELOAD:+--preload} --access-logfile ${ACCESS_LOG:--} --error-logfile ${ERROR_LOG:--}"]
