FROM python:3.11-slim

# Instalar dependencias del sistema y SWI-Prolog
RUN apt-get update && apt-get install -y \
    swi-prolog \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar archivos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponer puerto
EXPOSE 5000

# Comando de arranque con servidor de producción gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "server:app"]