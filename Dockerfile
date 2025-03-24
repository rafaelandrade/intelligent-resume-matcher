FROM python:3.9-slim

WORKDIR /app

# Instalação de dependências básicas do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Atualizar pip
RUN pip install --upgrade pip

# Instalação de dependências pré-compiladas quando possível
RUN pip install --no-cache-dir wheel setuptools cython

COPY newrelic.ini /app/newrelic.ini

# Copiar e instalar as dependências restantes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || echo "Alguns pacotes podem precisar ser instalados manualmente"

# Cópia dos arquivos do projeto
COPY . .

# Porta que a aplicação escuta
EXPOSE 8009

# Comando para iniciar a aplicação
CMD ["newrelic-admin", "run-program", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8009"]
