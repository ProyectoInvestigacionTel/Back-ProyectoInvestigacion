import random
import string
from docker import DockerClient
from docker.errors import ContainerError, NotFound
import base64


def encode_code_to_base64(code: str) -> str:
    return base64.b64encode(code.encode()).decode()


def correct_special_characters(code_str: str) -> str:
    return code_str.replace("'", '"')


def generate_random_filename(prefix, suffix):
    random_string = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=10)
    )
    return f"/app/temp/{prefix}_{random_string}.{suffix}"


def prepare_input_files(container, input_cases: list) -> list:
    input_filenames = []
    for i, case in enumerate(input_cases):
        input_filename = generate_random_filename(f"input_{i}", "txt")
        input_content = f"{case['input'].strip()}\n"
        input_content_base64 = base64.b64encode(input_content.encode()).decode()

        container.exec_run(
            cmd=f'sh -c "echo {input_content_base64} | base64 --decode > {input_filename}"',user="appuser"
        )

        input_filenames.append(input_filename)
        print(f"Input file {i} created: {input_filename}", flush=True)
        print(f"Input content before base64: {input_content}", flush=True)

    return input_filenames


def run_code_in_container(
    code: str, input_cases: list = [], timeout_seconds=20
) -> list:
    client = DockerClient.from_env()
    results = []
    container_name = f"code_execution_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"

    try:
        
        container = client.containers.run(
            image="back-proyectoinvestigacion-run_code",
            command="tail -f /dev/null",
            name=container_name,
            detach=True,
            mem_limit="100m",
            auto_remove=True,
            user="appuser"
        )

        input_filenames = prepare_input_files(container, input_cases)

        code_filename = generate_random_filename("code", "py")
        corrected_code_base64 = encode_code_to_base64(correct_special_characters(code))

        container.exec_run(
            cmd=f'sh -c "echo {corrected_code_base64} | base64 --decode > {code_filename}"',
        )

        for input_filename in input_filenames:
            exec_result = container.exec_run(
                cmd=f"sh -c 'timeout {timeout_seconds} python {code_filename} < {input_filename}'",user="appuser"
            )

            if exec_result.exit_code == 0:
                result = exec_result.output.decode("utf-8")
            else:
                result = (
                    f"Error al ejecutar el código: {exec_result.output.decode('utf-8')}"
                )
            results.append(result)
            container.exec_run(cmd=f"rm {input_filename}",user="appuser")

        container.exec_run(cmd=f"rm {code_filename}",user="appuser")
        container.remove(force=True)
    except ContainerError as e:
        return [f"Error en el contenedor: {str(e)}"]
    except Exception as e:
        return [f"Error inesperado: {str(e)}"]

    return results
