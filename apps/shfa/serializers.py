from shfa.abstract.serializers import DynamicDepthSerializer
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from shfa.utils import get_fields, DEFAULT_FIELDS
from .models import *
from rest_framework import serializers

class DynamicDepthModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request', None)
        if request:
            try:
                self.Meta.depth = int(request.query_params.get('depth', 0))  # Default 0
            except (ValueError, TypeError):
                self.Meta.depth = 0  
        else:
            self.Meta.depth = 0  

class SiteCoordinatesExcludeSerializer(GeoFeatureModelSerializer):
    parish = serializers.CharField(source='parish.name', default=None)
    municipality = serializers.CharField(source='municipality.name', default=None)
    province = serializers.CharField(source='province.name', default=None)

    class Meta:
        model = Site
        fields = ['id'] + get_fields(Site, exclude=['coordinates'])
        geo_field = 'coordinates'
        depth = 0  # Set a default depth for related objects

class TIFFImageSerializer(DynamicDepthSerializer):
    class Meta:
        model = Image
        fields = ['id'] + get_fields(Image, exclude=['created_at', 'updated_at'])
class SummarySerializer(DynamicDepthSerializer):

    class Meta:
        model = Image
        fields = ['id']+get_fields(Image, exclude=['created_at', 'updated_at', 'iiif_file', 'file', 'uuid'])

class SiteSerializer(DynamicDepthSerializer):
    # parish = serializers.CharField(source='parish.name', default=None)
    # municipality = serializers.CharField(source='municipality.name', default=None)
    # province = serializers.CharField(source='province.name', default=None)
    class Meta:
        model = Site
        fields = ['id']+get_fields(Site, exclude=DEFAULT_FIELDS)

class SiteGeoSerializer(GeoFeatureModelSerializer):
    # parish = serializers.CharField(source='parish.name', default=None)
    # municipality = serializers.CharField(source='municipality.name', default=None)
    # province = serializers.CharField(source='province.name', default=None)
    
    class Meta:
        model = Site
        fields = ['id']+get_fields(Site, exclude=DEFAULT_FIELDS)
        geo_field = 'coordinates'

class KeywordsSerializer(DynamicDepthSerializer):

    class Meta:
        model = KeywordTag
        fields = ['id']+get_fields(KeywordTag, exclude=DEFAULT_FIELDS)

class RockCarvingSerializer(DynamicDepthSerializer):

    class Meta:
        model = RockCarvingObject
        fields = ['id']+get_fields(RockCarvingObject, exclude=DEFAULT_FIELDS)

class AuthorSerializer(DynamicDepthSerializer):

    class Meta:
        model = Author
        fields = ['id']+get_fields(Author, exclude=DEFAULT_FIELDS)

class InstitutionSerializer(DynamicDepthSerializer):

    class Meta:
        model = Institution
        fields = ['id']+get_fields(Institution, exclude=DEFAULT_FIELDS)

class DatingTagSerializer(DynamicDepthSerializer):

    class Meta:
        model = DatingTag
        fields = ['id']+get_fields(DatingTag, exclude=DEFAULT_FIELDS)


class CompilationSerializer(DynamicDepthSerializer):

    class Meta:
        model = Compilation
        fields = ['id']+get_fields(Compilation, exclude=DEFAULT_FIELDS)


class ImageTypeSerializer(DynamicDepthSerializer):

    class Meta:
        model = ImageTypeTag
        fields = ['id']+get_fields(ImageTypeTag, exclude=DEFAULT_FIELDS)

class SHFA3DMeshSerializer(DynamicDepthSerializer):

    class Meta:
        model = SHFA3DMesh
        fields = ['id']+get_fields(SHFA3DMesh, exclude=DEFAULT_FIELDS+['dimensions'])

class PeopleSerializer(DynamicDepthSerializer):

    class Meta:
        model = People
        fields = ['id']+get_fields(People, exclude=DEFAULT_FIELDS)

class KeywordSerializer(DynamicDepthSerializer):
    class Meta:
        model = KeywordTag
        fields = ['id']+get_fields(KeywordTag, exclude=DEFAULT_FIELDS)

class DatingSerializer(DynamicDepthSerializer):
    class Meta:
        model = DatingTag
        fields = ['id']+get_fields(DatingTag, exclude=DEFAULT_FIELDS)
    

class CreatorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = People
        fields = ['id']+get_fields(People, exclude=DEFAULT_FIELDS)
    
class GeologySerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Geology
        fields = ['id']+get_fields(Geology, exclude=DEFAULT_FIELDS)
        geo_field = 'coordinates'


class CameraLensSerializer(DynamicDepthSerializer):
    class Meta:
        model = CameraLens
        fields = ['id']+get_fields(CameraLens, exclude=DEFAULT_FIELDS)


class CamerModelSerializer(DynamicDepthSerializer):
    class Meta:
        model = CameraModel
        fields = ['id']+get_fields(CameraModel, exclude=DEFAULT_FIELDS)

class CameraSpecificationSerializer(DynamicDepthSerializer):
    mm35_equivalent = serializers.SerializerMethodField()
    camera_lens = CameraLensSerializer()
    camera_model = CamerModelSerializer()
    class Meta:
        model = CameraMeta
        fields = ['id']+get_fields(CameraMeta, exclude=DEFAULT_FIELDS)+['mm35_equivalent']

    
    def get_mm35_equivalent(self, obj):
        return obj.mm35_equivalent

class SiteSerializerExcludeCoordinates(serializers.ModelSerializer):
    class Meta:
        model = Site
        exclude = ['coordinates']  # Exclude the coordinates field

class SHFA3DSerializer(DynamicDepthSerializer):

    class Meta:
        model = SHFA3D
        fields = ['id']+get_fields(SHFA3D, exclude=DEFAULT_FIELDS)
        depth = 1  # Set a default depth for related objects

class SHFA3DSerializerExcludeCoordinates(DynamicDepthSerializer):
    site=SiteSerializerExcludeCoordinates()
    image = CameraSpecificationSerializer()
    class Meta:
        model = SHFA3D
        fields = ['id']+get_fields(SHFA3D, exclude=DEFAULT_FIELDS)+['image']

class TIFFImageExcludeSiteSerializer(DynamicDepthSerializer):

    class Meta:
        model = Image
        fields = ['id']+get_fields(Image, exclude=['created_at', 'updated_at', 'site'])

class VisualizationGroupSerializer(DynamicDepthSerializer):
    visualization_group_count = serializers.IntegerField()
    shfa_3d_data = SHFA3DSerializerExcludeCoordinates(many=True, read_only=True, source='shfa3d_set')
    colour_images = TIFFImageExcludeSiteSerializer(many=True, read_only=True, source='images_set')
    class Meta:
        model = Group
        fields = ['id', 'text', 'visualization_group_count', 'shfa_3d_data', 'colour_images']
        depth = 1  # Ensure a default depth is set

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        depth = self.context.get('depth', 1)
        if depth > 1:
            nested_data = []
            images_nested_data = [] 
            for shfa3d_instance in instance.shfa3d_set.all():
                nested_representation = SHFA3DSerializerExcludeCoordinates(shfa3d_instance, context={'depth': depth - 1}).data
                nested_data.append(nested_representation)
            representation['shfa_3d_data'] = nested_data
            for image_instance in instance.images_set.all():
                nested_representation = TIFFImageExcludeSiteSerializer(image_instance, context={'depth': depth - 1}).data
                images_nested_data.append(nested_representation)
            representation['colour_images'] = images_nested_data
        return representation


class GallerySerializer(DynamicDepthModelSerializer):
    site = SiteCoordinatesExcludeSerializer()


    def get_width(self, obj):
        return TIFFImageSerializer().get_width(obj)

    def get_height(self, obj):
        return TIFFImageSerializer().get_height(obj)

    class Meta:
        model = Image
        fields = ['id'] + get_fields(Image, exclude=DEFAULT_FIELDS)
        depth = 0
        geo_field = 'coordinates'


class RegionSerializer(DynamicDepthSerializer):
    sites = SiteCoordinatesExcludeSerializer(many=True, read_only=True)

    parish = serializers.CharField(source='parish.name')
    municipality = serializers.CharField(source='municipality.name')
    province = serializers.CharField(source='province.name')
    country = serializers.CharField(source='parish.country.name')

    class Meta:
        model = Site
        fields = ['id', 'placename', 'country', 'parish', 'municipality', 'province', 'sites']