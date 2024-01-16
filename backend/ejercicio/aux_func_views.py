from datetime import datetime
import json
import re
from django.core.files.base import ContentFile
from dockerfunctions import run_code_in_container
from .models import *
from .serializers import *
import os

def check_imports(code: str) -> bool:
    direct_imports = re.findall(r"\bimport (\w+)", code)
    from_imports = re.findall(r"\bfrom (\w+)", code)
    return bool(direct_imports or from_imports)


def add_message_to_conversation(detalle, remitente, mensaje):
    with detalle.conversacion_file.open("r") as file:
        contenido_actual = json.load(file)

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo_mensaje = {"fecha": fecha_actual, "remitente": remitente, "mensaje": mensaje}
    contenido_actual.append(nuevo_mensaje)

    # Borrar el archivo existente antes de guardar el nuevo
    detalle.conversacion_file.delete(save=False)

    # Guardar el nuevo archivo
    detalle.conversacion_file.save(
        detalle.conversacion_file.name, ContentFile(json.dumps(contenido_actual))
    )


def verify_imports(codigo):
    imports_detected = check_imports(codigo)
    return imports_detected


def get_ejercicio_instance(id_ejercicio):
    try:
        return Ejercicio.objects.get(pk=id_ejercicio)
    except Ejercicio.DoesNotExist:
        return None


def generate_result_json(outputs_esperados, resultado_limpio):
    results = []
    max_length = max(len(outputs_esperados), len(resultado_limpio))

    for i in range(max_length):
        esperado = outputs_esperados[i] if i < len(outputs_esperados) else None
        real = resultado_limpio[i] if i < len(resultado_limpio) else None

        result = {"output": esperado, "obtenido": real, "estado": esperado == real}
        results.append(result)
    return json.dumps(results)


def get_intento_existente(request, user):
    return IntentoEjercicio.objects.filter(
        id_ejercicio=request.data["id_ejercicio"], id_usuario=user.id_usuario
    ).first()


def load_casos_de_uso(casos_de_uso_path):
    with default_storage.open(casos_de_uso_path, "r") as f:
        data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("El archivo JSON no contiene una lista válida.")
        return data


def execute_code(codigo: str, head: str, tail: str) -> str:
    print("Llamando a run_code_in_container codigo: ", codigo, flush=True)
    codigo_final = head + "\n" + codigo + "\n" + tail
    print("Codigo final: ", codigo_final, flush=True)
    resultado = run_code_in_container(codigo_final)
    print("Resultado:", resultado, flush=True)
    return resultado


def compare_outputs_and_calculate_score(outputs_esperados, resultado_limpio, binary):
    outputs_correctos = sum(
        esperado == real
        for esperado, real in zip(outputs_esperados, resultado_limpio)
    )
    total_outputs = len(outputs_esperados)

    if binary:
        # solo obtiene puntaje si todos los casos son correctos
        resuelto = outputs_correctos == total_outputs
        nota = 100 if resuelto else 0
    else:
        #  obtiene puntaje por cada caso correcto
        nota = (outputs_correctos / total_outputs) * 100
        resuelto = outputs_correctos == total_outputs

    return nota, resuelto



def update_intento(
    intento_existente, request, ejercicio_instance, user, nota, resuelto
):
    if intento_existente:
        intento_existente.intentos += 1
        intento_existente.nota = nota
        intento_existente.tiempo = request.data["tiempo"]
        intento_existente.resuelto = resuelto
        intento_existente.save()
        return intento_existente
    else:
        intento_data = {
            "id_ejercicio": ejercicio_instance.id_ejercicio,
            "id_usuario": user.id_usuario,
            "intentos": 1,
            "nota": nota,
            "tiempo": request.data["tiempo"],
            "resuelto": resuelto,
        }
        intento_serializer = IntentoEjercicioSerializer(data=intento_data)
        if intento_serializer.is_valid():
            intento_serializer.save()
            return intento_serializer.instance
        else:
            return None


def create_or_update_detalle_intento(intento_existente, nota, resuelto):
    detalle_data = {
        "id_intento_general": intento_existente.id_intento_general,
        "fecha": datetime.now(),
        "nota": nota,
        "resuelto": resuelto,
        "retroalimentacion": 1 if not resuelto else 0,
    }
    detalle_serializer = DetalleIntentoSerializer(data=detalle_data)
    if detalle_serializer.is_valid():
        return detalle_serializer.save()
    else:
        return None


def create_or_update_retroalimentacion(
    detalle_instance, feedback_inicial, codigo, id_ejercicio, resultado_file
):
    retro_inicial = [
        {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "remitente": "CHATGPT",
            "mensaje": feedback_inicial,
        }
    ]
    retro_serializer = DetalleRetroalimentacionSerializer(
        data={"id_intento": detalle_instance.id_intento}
    )
    if retro_serializer.is_valid():
        retro_instance = retro_serializer.save()
        codigo_file_name = (
            f"codigo_Re{retro_instance.id_retroalimentacion}_Ej{id_ejercicio}.txt"
        )
        conversacion_file_name = f"conversacion_Re{retro_instance.id_retroalimentacion}_Ej{id_ejercicio}.json"
        resultado_file_name = (
            f"resultado_Re{retro_instance.id_retroalimentacion}_Ej{id_ejercicio}.json"
        )

        retro_instance.codigo_file.save(codigo_file_name, ContentFile(codigo))
        retro_instance.conversacion_file.save(
            conversacion_file_name, ContentFile(json.dumps(retro_inicial))
        )
        retro_instance.resultado_file.save(
            resultado_file_name, ContentFile(resultado_file)
        )

        retro_instance.save()
        return retro_instance
    else:
        return None


def update_resuelto_state_and_nota(detalle_instance, usuario, nota):
    if detalle_instance.resuelto:
        detalle_instance.nota = nota
        usuario.monedas += 10
        usuario.save()
        detalle_instance.save()


def get_all_ejercicios_files(id_ejercicio, response_data):
    ejercicio = get_ejercicio_instance(id_ejercicio)
    enunciado_data, casos_de_uso_data, ejemplos_data, salida_data = (
        None,
        None,
        None,
        None,
    )

    if ejercicio.enunciado_file:
        with ejercicio.enunciado_file.open("r") as file:
            enunciado_data = file.read()

    if ejercicio.casos_de_uso_file:
        with ejercicio.casos_de_uso_file.open("r") as file:
            casos_de_uso_data = json.load(file)
    if ejercicio.casos_de_uso_file:
        with ejercicio.ejemplo_file.open("r") as file:
            ejemplos_data = file.read()

    if ejercicio.salida_file:
        with ejercicio.salida_file.open("r") as file:
            salida_data = file.read()

    if response_data is None:
        response_data = {}
    response_data["enunciado"] = enunciado_data
    response_data["casos_de_uso"] = casos_de_uso_data
    response_data["ejemplos"] = ejemplos_data
    response_data["salida"] = salida_data
    return response_data


def formatear_datos_ejercicio(data):
    ruta_archivo = os.path.join( 'global', 'formateo_entrada_ejercicios.json')
    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        mapeo_campos = json.load(archivo)

    def formatear_item(item):
        return {mapeo_campos.get(key, key): value for key, value in item.items()}

    if isinstance(data, list):
        return [formatear_item(item) for item in data]
    else:
        return formatear_item(data)


def formatear_entrada_ejercicio(data):
    ruta_archivo = os.path.join('global', 'formateo_salida_ejercicios.json')
    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        mapeo_campos = json.load(archivo)

    def formatear_item(item):
        return {
            mapeo_campos.get(key, key): value for key, value in item.items()
        }

    if isinstance(data, list):
        return [formatear_item(item) for item in data]
    else:
        return formatear_item(data)
