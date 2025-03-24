
FROM python:3.9-slim

WORKDIR /app

COPY newrelic.ini /app/newrelic.ini

# Instalação de dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cópia dos arquivos do projeto
COPY . .

# Porta que a aplicação escuta
EXPOSE 8009

# Comando para iniciar a aplicação
CMD ["newrelic-admin", "run-program", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
