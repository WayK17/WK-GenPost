# Usamos una imagen base de Python delgada y estable
FROM python:3.11-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Actualizamos los paquetes e instalamos mediainfo-cli
# Esta es la línea mágica que soluciona el problema de instalación
RUN apt-get update && apt-get install -y mediainfo

# Copiamos el archivo de dependencias primero para optimizar el cache de Docker
COPY requirements.txt .

# Instalamos las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código de nuestro bot al contenedor
COPY ./bot ./bot

# Copiamos el archivo de entrada
COPY main.py .

# Comando final corregido para ejecutar el bot
CMD ["python", "main.py"]