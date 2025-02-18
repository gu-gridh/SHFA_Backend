from tkinter import N
from rest_framework import viewsets
from rest_framework.schemas.openapi import AutoSchema
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_gis.filters import InBBoxFilter
from rest_framework_gis.pagination import GeoJsonPagination
from . import models, serializers

from shfa.abstract.views import DynamicDepthViewSet, GeoViewSet
from shfa.abstract.models import get_fields

class ProvinceViewSet(GeoViewSet):

    queryset = models.Province.objects.all()
    serializer_class = serializers.ProvinceSerializer
    filterset_fields = get_fields(models.Province, exclude=['geometry'])

class ParishViewSet(GeoViewSet):

    queryset = models.Parish.objects.all()
    serializer_class = serializers.ParishSerializer
    filterset_fields = get_fields(models.Parish, exclude=['geometry'])


class CountryViewSet(GeoViewSet):

    queryset = models.Country.objects.all()
    serializer_class = serializers.CountrySerializer
    filterset_fields = get_fields(models.Country, exclude=['geometry'])


class LAUViewSet(GeoViewSet):

    queryset = models.LocalAdministrativeUnit.objects.all()
    serializer_class = serializers.LAUSerializer
    filterset_fields = get_fields(models.LocalAdministrativeUnit, exclude=['geometry'])

    
class NUTS1ViewSet(GeoViewSet):

    queryset = models.NUTS1.objects.all()
    serializer_class = serializers.NUTS1Serializer
    filterset_fields = get_fields(models.NUTS1, exclude=['geometry'])
    
class NUTS2ViewSet(GeoViewSet):

    queryset = models.NUTS2.objects.all()
    serializer_class = serializers.NUTS2Serializer
    filterset_fields = get_fields(models.NUTS2, exclude=['geometry'])

class NUTS3ViewSet(GeoViewSet):

    queryset = models.NUTS3.objects.all()
    serializer_class = serializers.NUTS3Serializer
    filterset_fields = get_fields(models.NUTS3, exclude=['geometry'])