from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("teacher", PostTeacherView.as_view(), name="post_Teacher"),
    path("student", PostStudentView.as_view(), name="post_Student"),
    path("<str:email>", UserView.as_view(), name="get_usuario"),
    # login con jwt
    path("token/", csrf_exempt(LoginUser.as_view()), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("original_token/", LoginUserToken.as_view(), name="logout"),
    path("add_coin/<str:user_id>", AddCoinView.as_view(), name="add_coin"),
    path("get_coin/<str:user_id>", GetCoinView.as_view(), name="get_coin"),
    path("remove_coins/<str:user_id>", RemoveCoinView.as_view(), name="remove_coin"),
    path('upload-picture/', UserPhotoUploadView.as_view(), name='upload-picture'),
    path('get-picture/<str:user_id>', UserPhotoView.as_view(), name='get-picture'),
]
