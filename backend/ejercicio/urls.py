from django.urls import path
from .views import BuscarEjerciciosView, EjercicioView,EjercicioCreateView,EjercicioListView, EjerciciosPorUsuarioView,IntentoEjercicioCreateView,RankingEjercicioView,EjerciciosPorAsignaturaView,ConversacionView,DetallePorEjercicio

urlpatterns = [
    path('<int:pk>', EjercicioView.as_view()),
    path('create', EjercicioCreateView.as_view(), name='ejercicio-create'),
    path('list', EjercicioListView.as_view(), ),
    path('intento', IntentoEjercicioCreateView.as_view(), name='registrar_intento'),
    path('ejercicios_por_usuario/<int:id_usuario>', EjerciciosPorUsuarioView.as_view(), name='ejercicios_por_usuario'),
    path('buscar_ejercicios', BuscarEjerciciosView.as_view(), name='buscar_ejercicios_por_contenido'),
    path('ranking/<int:id_ejercicio>', RankingEjercicioView.as_view(), name='ranking_ejercicio'),
    path('ejercicios_por_asignatura/<str:asignatura>', EjerciciosPorAsignaturaView.as_view(), name='ejercicios_por_asignatura'),
    path('conversacion/<int:id_retroalimentacion>', ConversacionView.as_view(), name='conversacion'),
    path('detalle_por_ejercicio/<int:id_ejercicio>/<int:id_user>', DetallePorEjercicio.as_view(), name='detalle_por_ejercicio'),
]

