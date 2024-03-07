import random
import string
from docker import DockerClient
from docker.errors import ContainerError, NotFound
import base64


def encode_code_to_base64(code: str) -> str:
    return base64.b64encode(code.encode()).decode()


def correct_special_characters(code_str: str) -> str:
    return code_str.replace("'", '"')


def prepare_input_files(container, input_cases: list) -> list:
    input_filenames = []
    for i, case in enumerate(input_cases):
        random_suffix = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=6)
        )
        input_filename = f"/app/temp/input_{i}_{random_suffix}.txt"

        input_content = case["input"].strip()
        # Asegúrate de escapar correctamente los caracteres especiales aquí si es necesario
        container.exec_run(
            cmd=f"sh -c \"printf '{input_content}' > {input_filename}\"", user="appuser"
        )
        input_filenames.append(input_filename)

    return input_filenames


def run_code_in_container(
    code: str, input_cases: list = [], timeout_seconds=20
) -> list:
    client = DockerClient.from_env()
    results = []
    try:
        container = client.containers.get("run_code")
        input_filenames = prepare_input_files(container, input_cases)

        code_filename = "/app/temp/code.py"
        corrected_code_base64 = encode_code_to_base64(correct_special_characters(code))

        # Escribe el código corregido en el archivo .py dentro del contenedor
        container.exec_run(
            cmd=f'sh -c "echo {corrected_code_base64} | base64 --decode > {code_filename}"',
            user="appuser",
        )

        for input_filename in input_filenames:
            exec_result = container.exec_run(
                cmd=f"sh -c 'timeout {timeout_seconds} python {code_filename} < {input_filename}'",
                user="appuser",
            )
            if exec_result.exit_code == 0:
                result = exec_result.output.decode("utf-8")
            else:
                result = (
                    f"Error al ejecutar el código: {exec_result.output.decode('utf-8')}"
                )
            results.append(result)

            # Limpieza: elimina el archivo de entrada actual
            # container.exec_run(cmd=f"rm {input_filename}", user="appuser")

        # Opcional: Limpieza del archivo .py
        # container.exec_run(cmd=f"rm {code_filename}", user="appuser")

    except NotFound:
        return ["Error: Contenedor 'run_code' no encontrado."]
    except ContainerError as e:
        return [f"Error en el contenedor: {str(e)}"]
    except Exception as e:
        return [f"Error inesperado: {str(e)}"]

    return results
