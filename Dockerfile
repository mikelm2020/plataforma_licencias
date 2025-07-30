# Usa una imagen base oficial de Python (basada en Debian)
FROM python:3.10-slim-bullseye

# Establece el directorio de trabajo en /app
WORKDIR /app

# Establece las variables de entorno para Python
ENV PYTHONUNBUFFERED 1


# --- SOLUCIÓN: Instalar las librerías cliente de Firebird y PostgreSQL ---
# Instala las dependencias necesarias del sistema operativo para:
# 1. Firebird client (libfbclient2)
# 2. PostgreSQL client (libpq-dev para psycopg2)
# 3. Herramientas de compilación básicas (build-essential, gcc) que a veces son necesarias
#    para que psycopg2-binary se instale correctamente en imágenes slim, o si se compila.
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        cron \
        locales \
        tzdata \
        libfbclient2 \
        libpq-dev \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*
# --- FIN DE LA SOLUCIÓN ---

# Configurar locale y timezone para evitar advertencias de cron y asegurar la consistencia horaria
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen en_US.UTF-8 && \
    /usr/sbin/update-locale LANG=en_US.UTF-8 && \
    ln -sf /usr/share/zoneinfo/America/Mexico_City /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# Copia los archivos de requerimientos e instala las dependencias
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación
COPY . /app/

# --- CAMBIO 2: Configurar el Cron Job ---
# Creamos un archivo de cronjob para el usuario root.
# El comando se ejecutará los lunes a las 10:00 AM.
# Redirige la salida estándar y los errores a un archivo de log dentro del contenedor.
# Esto asegura que los mensajes de tu comando 'check_expired_licenses' se guarden.
# Cron Job 1: Para licencias POR VENCER (ej. Lunes 09:00 AM)
# Redirige la salida a /var/log/cron.log
RUN (echo "0 9 * * 1 /usr/local/bin/python /app/manage.py check_licenses_per_renew >> /var/log/cron.log 2>&1"; \
# Cron Job 2: Para licencias POR VENCIDAS (ej. Lunes 10:00 AM)
# También redirige la salida al mismo archivo de log para centralizar.
echo "0 10 * * 1 /usr/local/bin/python /app/manage.py check_expired_licenses >> /var/log/cron.log 2>&1") | crontab -

# --- CAMBIO 3: Crear un archivo de log vacío para cron ---
# Esto evita que cron se queje si el archivo de log no existe al inicio.
RUN touch /var/log/cron.log

# Expone el puerto que usa Django
EXPOSE 8000

# --- CAMBIO 4: Comando por defecto para correr la aplicación Django e iniciar cron ---
# 'cron -f' inicia el servicio cron en modo "foreground" (para que no termine inmediatamente).
# '&' envía 'cron -f' al segundo plano, permitiendo que el siguiente comando se ejecute.
# 'python manage.py runserver 0.0.0.0:8000' inicia tu servidor Django en primer plano.
# Esto es crucial para que ambos servicios (cron y Django) se ejecuten en el mismo contenedor.
CMD cron -f && python manage.py runserver 0.0.0.0:8000
