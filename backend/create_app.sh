#!/bin/bash

# Comprobar si se proporciona el nombre de la aplicación
if [ -z "$1" ]
then
  echo "Por favor, proporciona el nombre de la aplicación."
  exit 1
fi

# Crear la aplicación
python manage.py startapp $1

# Navegar a la carpeta de la aplicación
cd $1


touch serializers.py
touch urls.py
# Mensaje de éxito
echo "Aplicación $1 creada con éxito con archivo serializers.py y urls.py"
