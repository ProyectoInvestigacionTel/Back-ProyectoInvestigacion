from datetime import datetime
import json
import re
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from django.core.files.base import ContentFile
from usuario.models import UsuarioPersonalizado
from .models import (
    DetalleIntento,
    Ejercicio,
    IntentoEjercicio,
    DetalleRetroalimentacion,
)
from .serializers import (
    DetalleRetroalimentacionSerializer,
    EjercicioSerializerCreate,
    EjercicioSerializerView,
    IntentoEjercicioSerializer,
    DetalleIntentoSerializer,
    IntentoEjercicioSerializer,
    DetalleIntentoSerializer,
    ConversacionSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from dockerfunctions import run_code_in_container
from django.db.models import Q
from django.db import transaction
from drf_yasg import openapi
from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings


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


class EjercicioView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]
    queryset = Ejercicio.objects.all()
    serializer_class = EjercicioSerializerView

    def get(self, request, pk):
        try:
            ejercicio = Ejercicio.objects.get(pk=pk)
        except Ejercicio.DoesNotExist:
            return Response(
                {"error": "Ejercicio no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EjercicioSerializerView(ejercicio)

        enunciado_data = None
        casos_de_uso_data = None

        if ejercicio.enunciado_file:
            with ejercicio.enunciado_file.open("r") as file:
                enunciado_data = file.read()

        if ejercicio.casos_de_uso_file:
            with ejercicio.casos_de_uso_file.open("r") as file:
                casos_de_uso_data = json.load(file)
        response_data = serializer.data
        if enunciado_data:
            response_data["enunciado"] = enunciado_data
        if casos_de_uso_data:
            response_data["casos_de_uso"] = casos_de_uso_data

        return Response(response_data, status=status.HTTP_200_OK)


class BuscarEjerciciosView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "contenidos",
                openapi.IN_QUERY,
                description="Una lista de contenidos separados por comas",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "dificultad",
                openapi.IN_QUERY,
                description="Nivel de dificultad",
                type=openapi.TYPE_STRING,
            ),
        ]
    )
    def get(self, request):
        contenidos = request.query_params.get("contenidos", None)
        dificultad = request.query_params.get("dificultad", None)

        if not contenidos and not dificultad:
            return Response(
                {
                    "error": "Por favor, proporciona contenidos y/o dificultad para buscar."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        query_filters = Q()

        if contenidos:
            contenidos_list = contenidos.split(",")
            queries = [
                Q(contenidos__icontains=contenido) for contenido in contenidos_list
            ]
            query_filters |= queries.pop()  # Usa el operador |= para combinar con OR
            for query in queries:
                query_filters |= query

        if dificultad:
            query_filters &= Q(
                dificultad=dificultad
            )  # Usa el operador &= para combinar con AND

        ejercicios = Ejercicio.objects.filter(query_filters)

        response_data = []
        for ejercicio in ejercicios:
            serializer = EjercicioSerializerView(ejercicio)

            enunciado_data = None
            casos_de_uso_data = None

            if ejercicio.enunciado_file:
                with ejercicio.enunciado_file.open("r") as file:
                    enunciado_data = file.read()

            if ejercicio.casos_de_uso_file:
                with ejercicio.casos_de_uso_file.open("r") as file:
                    casos_de_uso_data = json.load(file)

            ejercicio_data = serializer.data
            if enunciado_data:
                ejercicio_data["enunciado_file"] = enunciado_data
            if casos_de_uso_data:
                ejercicio_data["casos_de_uso_file"] = casos_de_uso_data

            response_data.append(ejercicio_data)

        return Response(response_data, status=status.HTTP_200_OK)


class EjercicioCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(request_body=EjercicioSerializerCreate)
    def post(self, request):
        user = request.user

        data = request.data.copy()
        data["usuario"] = user.pk

        serializer = EjercicioSerializerCreate(data=data)

        if serializer.is_valid():
            dificultad = serializer.validated_data.get("dificultad")

            if dificultad not in ["Fácil", "Media", "Avanzada"]:
                return Response(
                    {"error": "Dificultad no válida."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save()
            return Response(
                "Ejercico creado correctamente", status=status.HTTP_201_CREATED
            )
        return Response(
            "Error al crear el ejercicio", status=status.HTTP_400_BAD_REQUEST
        )


class EjercicioListView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            ejercicios = Ejercicio.objects.all()

            lista = []
            for ejercicio in ejercicios:
                print("ejercicio", ejercicio.id_usuario_id, flush=True)
                usuario = UsuarioPersonalizado.objects.get(pk=ejercicio.id_usuario_id)
                print("usuario", usuario, flush=True)
                lista.append(
                    {
                        "id_ejercicio": ejercicio.id_ejercicio,
                        "dificultad": ejercicio.dificultad,
                        "puntaje": ejercicio.puntaje,
                        "contenidos": ejercicio.contenidos,
                        "lenguaje": ejercicio.lenguaje,
                        "asignatura": ejercicio.asignatura,
                        "id_usuario": usuario.id_usuario,
                        "nombre_usuario": usuario.nombre,
                        "email_usuario": usuario.email,
                    }
                )
            return Response(lista, status=status.HTTP_200_OK)
        except UsuarioPersonalizado.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(str(e), flush=True)
            return Response(
                {"error": "Ocurrió un error inesperado"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class IntentoEjercicioCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=IntentoEjercicioSerializer)
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        codigo = request.data.get("codigo", "")
        feedback_inicial = request.data.get("feedback_inicial", "")
        usuario = UsuarioPersonalizado.objects.get(pk=user.id_usuario)

        if self.verify_imports(codigo):
            return Response(
                {"error": "Librerías importadas detectadas"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ejercicio_instance = self.get_ejercicio_instance(request.data["id_ejercicio"])
        if ejercicio_instance is None:
            return Response(
                {"error": "Ejercicio no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        intento_existente = self.get_intento_existente(request, user)

        casos_de_uso = self.load_casos_de_uso(ejercicio_instance.casos_de_uso_file.path)
        print(casos_de_uso, flush=True)
        resultado = self.execute_code(codigo)
        if "Error" in resultado:
            return Response({"error": resultado}, status=status.HTTP_400_BAD_REQUEST)

        outputs_esperados = [str(caso["output"]).strip() for caso in casos_de_uso]

        resultado_limpio = [linea.strip() for linea in resultado.splitlines()]
        nota, resuelto = self.compare_outputs_and_calculate_score(
            outputs_esperados, resultado_limpio
        )
        results_json = self.generate_result_json(outputs_esperados, resultado_limpio)

        intento_instance = self.update_intento(
            intento_existente, request, ejercicio_instance, user, nota, resuelto
        )
        if not intento_instance:
            return Response(
                {"error": "Error al actualizar o crear el intento"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        detalle_instance = self.create_or_update_detalle_intento(
            intento_instance, nota, resuelto
        )
        if detalle_instance is None:
            return Response(
                {"error": "Error al crear o actualizar el detalle del intento"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        retro_instance = self.create_or_update_retroalimentacion(
            detalle_instance,
            feedback_inicial,
            codigo,
            request.data["id_ejercicio"],
            results_json,
        )
        if retro_instance is None:
            return Response(
                {"error": "Error al crear o actualizar la retroalimentación"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.update_resuelto_state_and_nota(detalle_instance, usuario, nota)

        return Response(
            {
                "message": "Intento registrado con éxito",
                "id_retroalimentacion": retro_instance.id_retroalimentacion,
                "resuelto": resuelto,
            },
            status=status.HTTP_201_CREATED,
        )

    def verify_imports(self, codigo):
        imports_detected = check_imports(codigo)
        return imports_detected

    def get_ejercicio_instance(self, id_ejercicio):
        try:
            return Ejercicio.objects.get(pk=id_ejercicio)
        except Ejercicio.DoesNotExist:
            return None

    def generate_result_json(self, outputs_esperados, resultado_limpio):
        results = []
        max_length = max(len(outputs_esperados), len(resultado_limpio))

        for i in range(max_length):
            esperado = outputs_esperados[i] if i < len(outputs_esperados) else None
            real = resultado_limpio[i] if i < len(resultado_limpio) else None

            result = {"output": esperado, "obtenido": real, "estado": esperado == real}
            results.append(result)
        return json.dumps(results)

    def get_intento_existente(self, request, user):
        return IntentoEjercicio.objects.filter(
            id_ejercicio=request.data["id_ejercicio"], id_usuario=user.id_usuario
        ).first()

    def load_casos_de_uso(self, casos_de_uso_path):
        with default_storage.open(casos_de_uso_path, "r") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("El archivo JSON no contiene una lista válida.")
            return data

    def execute_code(self, codigo):
        print("Llamando a run_code_in_container codigo: ", codigo, flush=True)
        resultado = run_code_in_container(codigo)
        print("Resultado:", resultado, flush=True)
        return resultado

    def compare_outputs_and_calculate_score(self, outputs_esperados, resultado_limpio):
        outputs_correctos = sum(
            [
                esperado == real
                for esperado, real in zip(outputs_esperados, resultado_limpio)
            ]
        )
        total_outputs = len(outputs_esperados)
        nota = (outputs_correctos / total_outputs) * 100
        resuelto = outputs_correctos == total_outputs
        return nota, resuelto

    def update_intento(
        self, intento_existente, request, ejercicio_instance, user, nota, resuelto
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

    def create_or_update_detalle_intento(self, intento_existente, nota, resuelto):
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
        self, detalle_instance, feedback_inicial, codigo, id_ejercicio, resultado_file
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
            resultado_file_name = f"resultado_Re{retro_instance.id_retroalimentacion}_Ej{id_ejercicio}.json"

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

    def update_resuelto_state_and_nota(self, detalle_instance, usuario, nota):
        if detalle_instance.resuelto:
            detalle_instance.nota = nota
            usuario.monedas += 10
            usuario.save()
            detalle_instance.save()


class EjerciciosPorUsuarioView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, id_usuario):
        data = []

        try:
            usuario = UsuarioPersonalizado.objects.get(pk=id_usuario)
        except UsuarioPersonalizado.DoesNotExist().DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        intentos_generales = IntentoEjercicio.objects.filter(
            id_usuario=id_usuario
        ).distinct("id_ejercicio")

        for intento_general in intentos_generales:
            ejercicio_data = {
                "id_ejercicio": intento_general.id_ejercicio.id_ejercicio,
                "asignatura": Ejercicio.objects.get(
                    pk=intento_general.id_ejercicio.id_ejercicio
                ).asignatura,
                "intentos": {},
            }

            detalles_intentos = DetalleIntento.objects.filter(
                id_intento_general=intento_general
            )

            for index, detalle_intento in enumerate(detalles_intentos, start=1):
                # Obtener detalles de retroalimentación
                detalle_retro = DetalleRetroalimentacion.objects.filter(
                    id_intento=detalle_intento
                ).first()

                # Leer el código y la conversación desde los archivos si están presentes
                codigo = ""
                conversacion = []
                if detalle_retro:
                    if detalle_retro.codigo_file:
                        with detalle_retro.codigo_file.open("r") as file:
                            codigo = file.read()

                    if detalle_retro.conversacion_file:
                        with detalle_retro.conversacion_file.open("r") as file:
                            conversacion = json.load(file)

                ejercicio_data["intentos"][f"intento_{index}"] = {
                    "nota": detalle_intento.nota,
                    "fecha_ingreso": detalle_intento.fecha.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "codigo": codigo,
                    "conversacion": conversacion,
                }

            data.append(ejercicio_data)

        return Response(data, status=status.HTTP_200_OK)


class RankingEjercicioView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, id_ejercicio):
        try:
            intentos = IntentoEjercicio.objects.filter(
                id_ejercicio=id_ejercicio
            ).order_by("-nota")
            ranking = []
            for intento in intentos:
                usuario = UsuarioPersonalizado.objects.get(
                    id_usuario=intento.id_usuario.id_usuario
                )
                ranking.append({"nombre": usuario.nombre, "nota": intento.nota})
            return Response(ranking, status=status.HTTP_200_OK)
        except UsuarioPersonalizado.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )
        except IntentoEjercicio.DoesNotExist:
            return Response(
                {"error": "Intento de ejercicio no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Ocurrió un error inesperado"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EjerciciosPorAsignaturaView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, asignatura):
        try:
            ejercicios = Ejercicio.objects.filter(asignatura=asignatura)

            lista_ejercicios = []
            for ejercicio in ejercicios:
                usuario = UsuarioPersonalizado.objects.get(pk=ejercicio.id_usuario_id)
                lista_ejercicios.append(
                    {
                        "id_ejercicio": ejercicio.id_ejercicio,
                        "nota_maxima": IntentoEjercicio.objects.filter(
                            id_ejercicio=ejercicio.id_ejercicio
                        )
                        .order_by("-nota")
                        .first()
                        .nota
                        if IntentoEjercicio.objects.filter(
                            id_ejercicio=ejercicio.id_ejercicio
                        ).exists()
                        else 0,
                        "dificultad": ejercicio.dificultad,
                        "contenidos": ejercicio.contenidos,
                        "id_usuario": usuario.id_usuario,
                        "email": usuario.email,
                        "nombre": usuario.nombre,
                    }
                )

            return Response(lista_ejercicios, status=status.HTTP_200_OK)

        except Ejercicio.DoesNotExist:
            return Response(
                {"error": "Ejercicios no encontrados"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(str(e), flush=True)
            return Response(
                {"error": "Ocurrió un error inesperado"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ConversacionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ConversacionSerializer)
    def post(self, request, id_retroalimentacion):
        try:
            detalle = DetalleRetroalimentacion.objects.get(pk=id_retroalimentacion)
        except DetalleRetroalimentacion.DoesNotExist:
            return Response(
                {"error": "DetalleRetroalimentacion no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ConversacionSerializer(data=request.data)
        if serializer.is_valid():
            for mensaje_data in serializer.validated_data["mensajes"]:
                remitente = mensaje_data["remitente"]
                mensaje = mensaje_data["mensaje"]
                add_message_to_conversation(detalle, remitente, mensaje)

            return Response(
                {"message": "Mensajes añadidos con éxito."},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DetallePorEjercicio(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, id_ejercicio, id_user):
        try:
            usuario = UsuarioPersonalizado.objects.get(pk=id_user)
            intentos = IntentoEjercicio.objects.filter(
                id_ejercicio=id_ejercicio, id_usuario=id_user
            )

            for intento in intentos:
                detalle_intentos = DetalleIntento.objects.filter(
                    id_intento_general=intento.id_intento_general
                )

                lista = []
                for retro in detalle_intentos:
                    detalle_retros = DetalleRetroalimentacion.objects.filter(
                        id_intento=retro.id_intento
                    )
                    if detalle_retros.exists():
                        detalle_retro = detalle_retros[0]
                        resultados_content = None

                        if (
                            hasattr(detalle_retro, "resultado_file")
                            and detalle_retro.resultado_file
                        ):
                            with default_storage.open(
                                detalle_retro.resultado_file.path, "r"
                            ) as file:
                                resultados_content = json.load(file)
                        lista.append(
                            {
                                "id_retroalimentacion": detalle_retro.id_retroalimentacion,
                                "resultados": resultados_content,
                            }
                        )

            return Response(lista, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e), flush=True)
            return Response(
                {"error": "Ocurrió un error inesperado"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
