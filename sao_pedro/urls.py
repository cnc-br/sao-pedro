"""
URL configuration for sao_pedro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from enderecos.views import EnderecoViewSet
from health.views import HealthCheckView
from health.views import WelcomeView  # importa a view do app health
from pessoas.views import PessoaViewSet
from contatos.views import ContatoViewSet, PessoaContatoView

router = DefaultRouter()
router.register(r"pessoas", PessoaViewSet)
router.register(r"enderecos", EnderecoViewSet)
router.register(r"contatos", ContatoViewSet)

urlpatterns = [
    path('', WelcomeView.as_view(), name='welcome'),
    path('admin/', admin.site.urls),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "api/pessoas/<uuid:uuid>/contatos/",
        PessoaContatoView.as_view(),
        name="pessoa-contatos",
    ),
    path("api/", include(router.urls)),
    path("api/health/", HealthCheckView.as_view(), name="health_check"),
]
