#!/bin/bash

# Cambia al directorio donde se encuentra tu proyecto Django
cd /ruta/a/tu/proyecto/django

# Encuentra todas las carpetas 'migrations' y '__pycache__', excluyendo la carpeta 'venv'
find . -type d \( -name migrations -o -name __pycache__ \) -not -path "*/venv/*" | while read dir; do
    echo "Procesando directorio: $dir"

    # Si el directorio es una carpeta 'migrations'
    if [[ "$dir" == *"migrations"* ]]; then
        # Encuentra y elimina todos los archivos '.py' excepto '__init__.py'
        find "$dir" -type f -name "*.py" ! -name "__init__.py" -exec echo "Eliminando {}" \; -exec rm {} \;
    fi

    # Si el directorio es una carpeta '__pycache__'
    if [[ "$dir" == *"__pycache__"* ]]; then
        # Elimina la carpeta '__pycache__'
        echo "Eliminando carpeta __pycache__"
        rm -rf "$dir"
    fi
done

echo "Limpieza completada."
