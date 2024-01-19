#!/bin/bash

# Instala expect si aún no está instalado
# Descomenta la siguiente línea en sistemas basados en Debian/Ubuntu
# sudo apt-get install -y expect

# Configura las credenciales del superusuario
SUPERUSER_EMAIL="admin@usm.cl"
SUPERUSER_NAME="admin"
SUPERUSER_ID="1"
SUPERUSER_PASSWORD="admin"

# Ejecuta el comando createsuperuser con expect
expect -c "
spawn python manage.py createsuperuser --email $SUPERUSER_EMAIL --username $SUPERUSER_NAME --id_usuario $SUPERUSER_ID
expect \"Password:\"
send \"$SUPERUSER_PASSWORD\r\"
expect \"Password (again):\"
send \"$SUPERUSER_PASSWORD\r\"
expect \"Bypass password validation and create user anyway? [y/N]:\"
send \"y\r\"
expect eof
"
    