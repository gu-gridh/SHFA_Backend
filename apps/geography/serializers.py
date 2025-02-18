from rest_framework_gis.serializers import GeoFeatureModelSerializer
from shfa.utils import get_fields, DEFAULT_FIELDS
from .models import *

class CountrySerializer(GeoFeatureModelSerializer):

    class Meta:
        model = Country
        fields = get_fields(Country, exclude=DEFAULT_FIELDS)
        geo_field = 'geometry'


class LAUSerializer(GeoFeatureModelSerializer):

    class Meta:
        model = LocalAdministrativeUnit
        fields = get_fields(LocalAdministrativeUnit, exclude=DEFAULT_FIELDS)
        geo_field = 'geometry'


class ProvinceSerializer(GeoFeatureModelSerializer):

    class Meta:
        model = Province
        fields = get_fields(Province, exclude=DEFAULT_FIELDS)
        geo_field = 'geometry'

class ParishSerializer(GeoFeatureModelSerializer):

    class Meta:
        model = Parish
        fields = get_fields(Parish, exclude=DEFAULT_FIELDS)
        geo_field = 'geometry'


class NUTS1Serializer(GeoFeatureModelSerializer):

    class Meta:
        model = NUTS1
        fields = get_fields(NUTS1, exclude=DEFAULT_FIELDS)
        geo_field = 'geometry'


class NUTS2Serializer(GeoFeatureModelSerializer):

    class Meta:
        model = NUTS2
        fields = get_fields(NUTS2, exclude=DEFAULT_FIELDS)
        geo_field = 'geometry'


class NUTS3Serializer(GeoFeatureModelSerializer):

    class Meta:
        model = NUTS3
        fields = get_fields(NUTS3, exclude=DEFAULT_FIELDS)
        geo_field = 'geometry'
