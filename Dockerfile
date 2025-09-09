FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dependências nativas do WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    shared-mime-info fonts-dejavu-core \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependências Python com versões fixas
COPY requirements.txt ./
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

EXPOSE 5000

# Gunicorn em produção
CMD ["gunicorn", "-b", "0.0.0.0:5000", "server:app", "--workers", "2", "--timeout", "120"]
