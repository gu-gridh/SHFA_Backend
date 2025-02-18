from django.urls import path, include
from rest_framework import routers
from . import views
import shfa.utils as utils


router = routers.DefaultRouter()
endpoint = utils.build_app_endpoint("geography")
documentation = utils.build_app_api_documentation("geography", endpoint)


router = routers.DefaultRouter()
router.register(f'{endpoint}/country', views.CountryViewSet, basename='country')
router.register(f'{endpoint}/province', views.ProvinceViewSet, basename='province')
router.register(f'{endpoint}/parish', views.ParishViewSet, basename='parish')
router.register(f'{endpoint}/lau', views.LAUViewSet, basename='lau')
router.register(f'{endpoint}/nuts1', views.NUTS1ViewSet, basename='nuts1')
router.register(f'{endpoint}/nuts2', views.NUTS2ViewSet, basename='nuts2')
router.register(f'{endpoint}/nuts3', views.NUTS3ViewSet, basename='nuts3')


urlpatterns = [
    path('', include(router.urls)),

    *documentation,
]