FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dependências do sistema para WeasyPrint e health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2-dev \
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

# Copiar e instalar dependências primeiro
COPY requirements.txt ./

# Atualizar pip e instalar dependências com versões específicas
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

EXPOSE 5000

# Usar gunicorn em produção
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app", "--workers", "2", "--timeout", "300", "--preload", "--access-logfile", "-", "--error-logfile", "-"]