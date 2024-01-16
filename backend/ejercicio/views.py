from datetime import timedelta
import json
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from usuario.models import *
from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from .aux_func_views import *
from django.db.models.functions import Rank
from django.db.models import Count, Sum, Max, Q, Window, F
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination

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

        response_data = serializer.data
        response_data = get_all_ejercicios_files(ejercicio.id_ejercicio, response_data)

        response_data["titulo"] = ejercicio.titulo
        response_data["restricciones"] = ejercicio.restricciones

        responde_data = formatear_datos_ejercicio(response_data)

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
        request.query_params = formatear_entrada_ejercicio(request.query_params)
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

            ejercicio_data = serializer.data
            ejercicio_data = get_all_ejercicios_files(
                ejercicio.id_ejercicio, ejercicio_data
            )
            ejercicio_data = serializer.data
            ejercicio_data["titulo"] = ejercicio.titulo
            ejercicio_data["restricciones"] = ejercicio.restricciones
            response_data = formatear_datos_ejercicio(ejercicio_data)
            response_data.append(ejercicio_data)

        return Response(response_data, status=status.HTTP_200_OK)


class EjercicioCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(request_body=EjercicioSerializerCreate)
    def post(self, request):
        user = request.user

        data = formatear_entrada_ejercicio(request.data.copy())
        data["usuario"] = user.pk

        serializer = EjercicioSerializerCreate(data=data)
        if "contenidos" in data and isinstance(data["contenidos"], list):
            data["contenidos"] = ",".join(data["contenidos"])
        elif "contenidos" in data and not isinstance(data["contenidos"], str):
            return Response(
                {"error": "Formato inválido para 'contenidos'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if serializer.is_valid():
            dificultad = serializer.validated_data.get("dificultad")

            if dificultad not in ["Facil", "Media", "Avanzada"]:
                return Response(
                    {"error": "Dificultad no válida."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save()
            return Response(
                {"message": "Ejercico creado correctamente"},
                status=status.HTTP_201_CREATED,
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
            paginator = PageNumberPagination()
            paginated_ejercicios = paginator.paginate_queryset(ejercicios, request)
            lista = []
            for ejercicio in paginated_ejercicios:
                usuario = UsuarioPersonalizado.objects.get(pk=ejercicio.id_usuario_id)
                files_data = get_all_ejercicios_files(ejercicio.id_ejercicio, None)

                lista.append(
                    formatear_datos_ejercicio(
                        {
                            "id_ejercicio": ejercicio.id_ejercicio,
                            "dificultad": ejercicio.dificultad,
                            "puntaje": ejercicio.puntaje,
                            "contenidos": ejercicio.contenidos,
                            "lenguaje": ejercicio.lenguaje,
                            "asignatura": ejercicio.asignatura,
                            "id_usuario": usuario.id_usuario,
                            "restricciones": ejercicio.restricciones,
                            "titulo": ejercicio.titulo,
                            "descripcion": ejercicio.descripcion,
                            "resumen": ejercicio.resumen,
                            **files_data,
                        }
                    )
                )
            return paginator.get_paginated_response(lista)  
        except UsuarioPersonalizado.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
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

        data = formatear_entrada_ejercicio(request.data)
        codigo = data.get("codigo", "")
        feedback_inicial = data.get("feedback_inicial", "")
        usuario = UsuarioPersonalizado.objects.get(pk=user.id_usuario)

        if verify_imports(codigo):
            return Response(
                {"error": "Librerías importadas detectadas"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ejercicio_instance = get_ejercicio_instance(data["id_ejercicio"])
        if ejercicio_instance is None:
            return Response(
                {"error": "Ejercicio no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        intento_existente = get_intento_existente(request, user)

        casos_de_uso = load_casos_de_uso(ejercicio_instance.casos_de_uso_file.path)
        resultado = execute_code(
            codigo, ejercicio_instance.head, ejercicio_instance.tail
        )
        print("resultado: ", resultado)
        if "Error" in resultado:
            return Response({"error": resultado}, status=status.HTTP_400_BAD_REQUEST)

        outputs_esperados = [str(caso["output"]).strip() for caso in casos_de_uso]

        resultado_limpio = [linea.strip() for linea in resultado.splitlines()]
        nota, resuelto = compare_outputs_and_calculate_score(
            outputs_esperados, resultado_limpio, ejercicio_instance.binary
        )
        results_json = generate_result_json(outputs_esperados, resultado_limpio)

        intento_instance = update_intento(
            intento_existente, request, ejercicio_instance, user, nota, resuelto
        )
        if not intento_instance:
            return Response(
                {"error": "Error al actualizar o crear el intento"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        detalle_instance = create_or_update_detalle_intento(
            intento_instance, nota, resuelto
        )
        if detalle_instance is None:
            return Response(
                {"error": "Error al crear o actualizar el detalle del intento"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        retro_instance = create_or_update_retroalimentacion(
            detalle_instance,
            feedback_inicial,
            codigo,
            data["id_ejercicio"],
            results_json,
        )
        if retro_instance is None:
            return Response(
                {"error": "Error al crear o actualizar la retroalimentación"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        update_resuelto_state_and_nota(detalle_instance, usuario, nota)

        return Response(
            {
                "message": "Intento registrado con éxito",
                "id_retroalimentacion": retro_instance.id_retroalimentacion,
                "resuelto": resuelto,
            },
            status=status.HTTP_201_CREATED,
        )


class InfoEjerciciosPorUsuarioView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, id_usuario):
        data = []

        try:
            UsuarioPersonalizado.objects.get(pk=id_usuario)
        except UsuarioPersonalizado.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )
        ejercicios = Ejercicio.objects.filter(id_usuario=id_usuario)

        for ejercicio in ejercicios:
            nota_maxima = DetalleIntento.objects.filter(
                id_intento_general__id_ejercicio=ejercicio
            ).aggregate(Max("nota"))["nota__max"]
            ejercicio_data = {
                "id_ejercicio": ejercicio.id_ejercicio,
                "fecha_creacion": ejercicio.fecha,
                "dificultad": ejercicio.dificultad,
                "contenidos": ejercicio.contenidos,
                "lenguaje": ejercicio.lenguaje,
                "asignatura": ejercicio.asignatura,
                "puntaje_maximo": ejercicio.puntaje,
                "puntaje_obtenido": nota_maxima if nota_maxima else "No resuelto",
                "intentos": {},
            }

            intentos_generales = IntentoEjercicio.objects.filter(
                id_usuario=id_usuario, id_ejercicio=ejercicio.id_ejercicio
            ).distinct("id_ejercicio")
            for intento_general in intentos_generales:
                detalles_intentos = DetalleIntento.objects.filter(
                    id_intento_general=intento_general
                )

                for index, detalle_intento in enumerate(detalles_intentos, start=1):
                    # Obtener detalles de retroalimentación
                    detalle_retro = DetalleRetroalimentacion.objects.filter(
                        id_intento=detalle_intento
                    ).first()

                    # Leer el código y la conversación desde los archivos si están presentes
                    if detalle_retro:
                        if detalle_retro.codigo_file and detalle_retro.codigo_file:
                            with detalle_retro.codigo_file.open("r") as file:
                                codigo = file.read()
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

            data.append(formatear_datos_ejercicio(ejercicio_data))

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
                ranking.append(
                    formatear_datos_ejercicio(
                        {"nombre": usuario.nombre, "nota": intento.nota}
                    )
                )
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
                    formatear_datos_ejercicio(
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
                            "difficulty": ejercicio.dificultad,
                            "contenidos": ejercicio.contenidos,
                            "id_usuario": usuario.id_usuario,
                            "email": usuario.email,
                            "nombre": usuario.nombre,
                        }
                    )
                )

            return Response(lista_ejercicios, status=status.HTTP_200_OK)

        except Ejercicio.DoesNotExist:
            return Response(
                {"error": "Ejercicios no encontrados"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
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
                            formatear_datos_ejercicio(
                                {
                                    "id_retroalimentacion": detalle_retro.id_retroalimentacion,
                                    "resultados": resultados_content,
                                }
                            )
                        )

            return Response(lista, status=status.HTTP_200_OK)
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
            return Response(
                {"error": "Ocurrió un error inesperado"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AsignaturaInfoView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, asignatura):
        try:
            ejercicios_por_asignatura = Ejercicio.objects.filter(asignatura=asignatura)

            # Agregar información por contenidos
            ejercicios_por_contenidos = ejercicios_por_asignatura.values(
                "contenidos"
            ).annotate(cantidad=Count("id_ejercicio"))
            # Total de ejercicios en la asignatura
            total_ejercicios = ejercicios_por_asignatura.count()

            # Agregar información por dificultad
            dificultades = ejercicios_por_asignatura.values("dificultad").annotate(
                cantidad=Count("id_ejercicio")
            )

            # Calcular porcentajes por dificultad
            porcentajes_por_dificultad = {}
            for dificultad in dificultades:
                porcentaje = (
                    (dificultad["cantidad"] / total_ejercicios) * 100
                    if total_ejercicios > 0
                    else 0
                )
                porcentajes_por_dificultad[dificultad["dificultad"]] = porcentaje

            data = {
                "ejercicios_por_contenidos": list(ejercicios_por_contenidos),
                "total_ejercicios_generados": ejercicios_por_asignatura.count(),
                "total_ejercicios_realizados": 0,
                "porcentaje_realizados": 0,
                "porcentajes_por_dificultad": porcentajes_por_dificultad,
            }

            # Calcular ejercicios realizados
            for ejercicios_de_asignatura in ejercicios_por_asignatura:
                intentos_por_asignatura = IntentoEjercicio.objects.filter(
                    id_ejercicio=ejercicios_de_asignatura.id_ejercicio
                )
                data["total_ejercicios_realizados"] += intentos_por_asignatura.count()

            # Calcular el porcentaje de ejercicios realizados
            if data["total_ejercicios_generados"] > 0:
                data["porcentaje_realizados"] = (
                    data["total_ejercicios_realizados"]
                    / data["total_ejercicios_generados"]
                ) * 100

            # Calcular la suma de puntajes por estudiante y crear un ranking
            ranking = (
                IntentoEjercicio.objects.filter(id_ejercicio__asignatura=asignatura)
                .values("id_usuario")
                .annotate(total_puntaje=Sum("id_ejercicio__puntaje"))
                .annotate(
                    ranking=Window(
                        expression=Rank(), order_by=F("total_puntaje").desc()
                    )
                )
            )
            usuario = UsuarioPersonalizado.objects.get(
                id_usuario=ranking[0]["id_usuario"]
            )
            data["id_usuario"] = usuario.id_usuario
            data["email"] = usuario.email
            data["nombre"] = usuario.nombre
            data["total_puntaje"] = ranking[0]["total_puntaje"]
            data["ranking"] = ranking[0]["ranking"]

            return Response(formatear_datos_ejercicio(data), status=status.HTTP_200_OK)
        except Ejercicio.DoesNotExist:
            return Response(
                {"error": "Asignatura no encontrada"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "Ocurrió un error inesperado: " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UltimoEjercicioView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, id_usuario):
        try:
            ultimo_ejercicio = (
                Ejercicio.objects.filter(id_usuario=id_usuario)
                .order_by("-fecha")
                .first()
            )

            if ultimo_ejercicio:
                tiempo_actual = timezone.now()
                diferencia_tiempo = tiempo_actual - ultimo_ejercicio.fecha

                resultado = diferencia_tiempo > timedelta(days=1)
            else:
                resultado = True

            return Response({"message": resultado}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Ocurrió un error inesperado: " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
