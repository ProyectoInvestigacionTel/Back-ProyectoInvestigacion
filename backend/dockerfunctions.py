import random
import string
from docker import DockerClient
from docker.errors import ContainerError, NotFound
import re


def correct_special_characters(code_str: str) -> str:
    # comillas dobles
    corrected_str = re.sub(r'(?<!\\)"', '\\"', code_str)

    # comillas simples
    # corrected_str = re.sub(r"(?<!\\)'", "\\'", corrected_str)

    return corrected_str


def run_code_in_container(code: str, timeout_seconds=20) -> str:
    client = DockerClient.from_env()

    # name de archivo temporal aleatorio
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    temp_filename = f"/app/temp/temp_code{random_suffix}.py"

    # manejar caracteres especiales
    corrected_code_for_command = correct_special_characters(code)

    try:
        # obtener el contenedor
        container = client.containers.get("run_code")

        # cdigo corregido en el archivo temporal dentro del contenedor
        exec_output = container.exec_run(
            cmd=f'sh -c "echo \\"{corrected_code_for_command}\\" > {temp_filename}"',
            user="appuser",
        )
        if exec_output.exit_code != 0:
            return f"Error al escribir en el archivo temporal: {exec_output.output.decode('utf-8')}"

        # ejecutar el code con un limite de tiempo
        exec_result = container.exec_run(
            cmd=f"timeout {timeout_seconds} python {temp_filename}", user="appuser"
        )

        # eliminar el archivo temporal
        container.exec_run(cmd=f"rm {temp_filename}", user="appuser")

        # errores
        if exec_result.exit_code != 0:
            if exec_result.exit_code == 124:  # timeout cuando se supera el tiempo
                return (
                    "Error: El código superó el tiempo máximo permitido de ejecución."
                )
            return f"Error al ejecutar el código: {exec_result.output.decode('utf-8')}"

        return exec_result.output.decode("utf-8")

    except NotFound:
        return "Error: Contenedor 'run_code' no encontrado."
    except ContainerError as e:
        return f"Error en el contenedor: {str(e)}"
    except Exception as e:
        return f"Error inesperado: {str(e)}"
