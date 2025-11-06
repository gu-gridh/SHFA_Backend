from . import models, serializers
from django.db.models import Q, Count, Prefetch
from shfa.abstract.views import DynamicDepthViewSet, GeoViewSet
from shfa.abstract.models import get_fields, DEFAULT_FIELDS
from django.views.decorators.csrf import csrf_exempt
from .oai_cat import *
from django.contrib.gis.geos import Polygon
from django.contrib.gis.gdal.envelope import Envelope
from django.contrib.gis.db.models import Extent
from functools import reduce
from rest_framework import viewsets, status
from rest_framework.viewsets import ViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from shfa.forms import ContactForm
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from rest_framework import status
from django.contrib.gis.db.models.aggregates import Extent
import gc
from django.db import connection
from django.utils.functional import cached_property
from rest_framework.pagination import PageNumberPagination
from itertools import chain

class SiteViewSet(DynamicDepthViewSet):
    serializer_class = serializers.SiteSerializer
    queryset = models.Site.objects.all()

    filterset_fields = get_fields(
        models.Site, exclude=DEFAULT_FIELDS + ['coordinates'])
    search_fields = ['raa_id', 'lamning_id', 'ksamsok_id', 'placename']
    bbox_filter_field = 'coordinates'
    bbox_filter_include_overlapping = True

class SiteGeoViewSet(GeoViewSet):

    serializer_class = serializers.SiteGeoSerializer
    images = models.Image.objects.all()
    queryset = models.Site.objects.filter(
        id__in=list(images.values_list('site', flat=True))
    ).order_by('raa_id', 'lamning_id', 'placename')

    filterset_fields = get_fields(
        models.Site, exclude=DEFAULT_FIELDS + ['coordinates'])
    search_fields = ['raa_id', 'lamning_id', 'ksamsok_id', 'placename']
    bbox_filter_field = 'coordinates'
    bbox_filter_include_overlapping = True

# Add 3D views
class SHFA3DViewSet(DynamicDepthViewSet):
    serializer_class = serializers.SHFA3DSerializer
    tree_d_data_group = models.Group.objects.all()
    queryset = models.SHFA3D.objects.filter(
        group_id__in=list(tree_d_data_group.values_list('id', flat=True)))
    filterset_fields = get_fields(models.SHFA3D, exclude=DEFAULT_FIELDS)

class VisualizationGroupViewset(DynamicDepthViewSet):
    serializer_class = serializers.VisualizationGroupSerializer

    def get_queryset(self):
        shfa3d_prefetch = Prefetch(
            'shfa3d_set', queryset=models.SHFA3D.objects.all())
        images_prefetch = Prefetch(
            'images_set', queryset=models.Image.objects.all().order_by('subtype__order'))

        queryset = models.Group.objects.all().annotate(
            visualization_group_count=Count('shfa3d_set')
        ).prefetch_related(shfa3d_prefetch, images_prefetch)

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        depth = self.request.query_params.get('depth', 1)
        try:
            depth = int(depth)
        except ValueError:
            depth = 1
        context['depth'] = depth
        return context

    filterset_fields = get_fields(models.Group, exclude=DEFAULT_FIELDS)

class GeologyViewSet(GeoViewSet):
    serializer_class = serializers.GeologySerializer
    queryset = models.Geology.objects.all()
    filterset_fields = get_fields(
        models.Geology, exclude=DEFAULT_FIELDS + ['coordinates', ])

class SHFA3DMeshViewset(DynamicDepthViewSet):
    serializer_class = serializers.SHFA3DMeshSerializer
    queryset = models.SHFA3DMesh.objects.all()
    filterset_fields = get_fields(
        models.SHFA3DMesh, exclude=DEFAULT_FIELDS + ['dimensions'])

class CameraSpecificationViewSet(DynamicDepthViewSet):
    serializer_class = serializers.CameraSpecificationSerializer
    queryset = models.CameraMeta.objects.all()
    filterset_fields = get_fields(
        models.CameraMeta, exclude=DEFAULT_FIELDS)

# Search views
class SiteSearchViewSet(GeoViewSet):
    serializer_class = serializers.SiteGeoSerializer

    def get_queryset(self):
        q = self.request.GET["site_name"]
        images = models.Image.objects.all()
        queryset = models.Site.objects.filter(Q
                                              (Q(raa_id__icontains=q)
                                               | Q(lamning_id__icontains=q)
                                               | Q(ksamsok_id__icontains=q)
                                               | Q(placename__icontains=q)
                                               | Q(askeladden_id__icontains=q)
                                               | Q(lokalitet_id__icontains=q)
                                               )
                                              & Q
                                              (id__in=list(images.values_list('site', flat=True)))
                                              ).order_by('raa_id', 'lamning_id', 'placename', 'ksamsok_id', 'askeladden_id', 'lokalitet_id')

        return queryset

    filterset_fields = get_fields(
        models.Site, exclude=DEFAULT_FIELDS + ['coordinates'])
    search_fields = ['raa_id', 'lamning_id', 'ksamsok_id', 'placename']
    bbox_filter_field = 'coordinates'
    bbox_filter_include_overlapping = True

class IIIFImageViewSet(DynamicDepthViewSet):
    """
    retrieve:
    Returns a single image instance.

    list:
    Returns a list of all the existing images in the database, paginated.

    count:
    Returns a count of the existing images after the application of any filter.
    """
    serializer_class = serializers.TIFFImageSerializer
    queryset = models.Image.objects.filter(
        published=True).order_by('type__order')
    filterset_fields = [
        'id']+get_fields(models.Image, exclude=['created_at', 'updated_at'] + ['iiif_file', 'file'])


class NullVisualizationGroupViewset(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer
    queryset = models.Image.objects.filter(
        group__isnull=False, published=True).order_by('type__order')
    filterset_fields = [
        'id']+get_fields(models.Image, exclude=['created_at', 'updated_at'] + ['iiif_file', 'file'])

class SearchBoundingBoxImageViewSet(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        box = self.request.GET["in_bbox"]
        box = box.strip().split(',')
        bbox_coords = [
            float(box[0]), float(box[1]),
            float(box[2]), float(box[3]),
        ]
        bounding_box = Polygon.from_bbox((bbox_coords))
        bounding_box = Envelope((bbox_coords))
        sites = models.Site.objects.filter(
            coordinates__intersects=bounding_box.wkt)
        queryset = models.Image.objects.filter(Q(site_id__in=sites)
                                               & Q(published=True)).order_by('type__order')
        return queryset

    filterset_fields = [
        'id']+get_fields(models.Image, exclude=['created_at', 'updated_at'] + ['iiif_file', 'file'])


class CompilationViewset(DynamicDepthViewSet):
    serializer_class = serializers.CompilationSerializer
    queryset = models.Compilation.objects.all()
    filterset_fields = ['id']+get_fields(models.Compilation, exclude=DEFAULT_FIELDS + [
                                         'images__iiif_file', 'images__file'])

class SearchKeywords(DynamicDepthViewSet):
    serializer_class = serializers.KeywordsSerializer

    def get_queryset(self):
        q = self.request.GET["keyword"]
        language = self.request.GET["language"]
        if language == "sv":
            queryset = models.KeywordTag.objects.filter(
                Q(text__icontains=q) | Q(category__icontains=q)).distinct().order_by('text', 'category')
        else:
            queryset = models.KeywordTag.objects.filter(Q(english_translation__icontains=q) | Q(
                category_translation__icontains=q)).distinct().order_by('text', 'category')
        return queryset

class SearchRockCarving(DynamicDepthViewSet):
    serializer_class = serializers.RockCarvingSerializer

    def get_queryset(self):
        q = self.request.GET["carving_object"]
        queryset = models.RockCarvingObject.objects.filter(
            name__icontains=q).order_by('name')
        return queryset

class SearchAuthor(DynamicDepthViewSet):
    serializer_class = serializers.AuthorSerializer

    def get_queryset(self):
        q = self.request.GET["auhtor_name"]
        images = models.Image.objects.all()
        language = self.request.GET["language"]
        if language == "sv":
            queryset = models.Author.objects.filter(Q(name__icontains=q) &
                                                    Q(id__in=list(images.values_list('author', flat=True))
                                                      )).order_by('name')
        else:
            queryset = models.Author.objects.filter(Q(english_translation__icontains=q) &
                                                    Q(id__in=list(images.values_list('author', flat=True))
                                                      )).order_by('name')
        return queryset

class SearchPeople(DynamicDepthViewSet):
    serializer_class = serializers.PeopleSerializer

    def get_queryset(self):
        q = self.request.GET["auhtor_name"]
        language = self.request.GET["language"]
        if language == "sv":
            queryset = models.People.objects.filter(
                name__icontains=q).order_by('name')
        else:
            queryset = models.People.objects.filter(
                english_translation__icontains=q).order_by('name')

        return queryset

class SearchInstitution(DynamicDepthViewSet):
    serializer_class = serializers.InstitutionSerializer

    def get_queryset(self):
        q = self.request.GET["institution_name"]
        queryset = models.Institution.objects.filter(
            name__icontains=q).order_by('name')
        return queryset

class SearchDatinTag(DynamicDepthViewSet):
    serializer_class = serializers.DatingTagSerializer

    def get_queryset(self):
        q = self.request.GET["dating_tag"]
        language = self.request.GET["language"]
        if language == "sv":
            queryset = models.DatingTag.objects.filter(
                text__icontains=q).order_by('text')
        else:
            queryset = models.DatingTag.objects.filter(
                english_translation__icontains=q).order_by('text')
        return queryset

class TypeSearchViewSet(DynamicDepthViewSet):
    serializer_class = serializers.ImageTypeSerializer

    def get_queryset(self):
        q = self.request.GET["image_type"]
        language = self.request.GET["language"]
        if language == "sv":
            queryset = models.ImageTypeTag.objects.filter(
                text__icontains=q).order_by('text')
        else:
            queryset = models.ImageTypeTag.objects.filter(
                english_translation__icontains=q).order_by('text')
        return queryset


class SearchVisualizationGroupViewset(DynamicDepthViewSet):
    serializer_class = serializers.SiteCoordinatesExcludeSerializer

    def get_queryset(self):
        q = self.request.GET.get("site_name", "").strip()

        queryset = models.Site.objects.filter(
            Q(shfa3d__isnull=False)
        ).distinct()
        
        # Apply search filter if query exists
        if q:
            queryset = queryset.filter(
                Q(raa_id__icontains=q) |
                Q(placename__icontains=q) |
                Q(lamning_id__icontains=q) |
                Q(ksamsok_id__icontains=q) |
                Q(askeladden_id__icontains=q) |
                Q(lokalitet_id__icontains=q)
            )
        
        # Add annotations for counts
        queryset = queryset.annotate(
            visualization_group_count=Count('shfa3d', distinct=True),
            images_count=Count('image', filter=Q(image__group__isnull=False), distinct=True)
        )
        
        # Filter to only sites that actually have 3D models or images
        queryset = queryset.filter(
            Q(visualization_group_count__gt=0) | Q(images_count__gt=0)
        )
        
        return queryset.order_by('-visualization_group_count', '-images_count', 'raa_id')

    filterset_fields = get_fields(models.Site, exclude=DEFAULT_FIELDS + ['coordinates'])

class RegionSearchViewSet(DynamicDepthViewSet):
    serializer_class = serializers.RegionSerializer
    filter_backends = []  # Disable automatic filtering since we're doing custom logic

    def get_queryset(self):
        # Get search parameter
        region_query = self.request.GET.get('region_name', '').strip()
        
        # Get all unique region combinations from sites with images
        sites = models.Site.objects.filter(
            id__in=models.Image.objects.values_list('site', flat=True)
        )

        # Apply region search filter if provided - use the same relationships as SummaryViewSet
        if region_query:
            sites = sites.filter(
                Q(parish__name__icontains=region_query) |
                Q(municipality__name__icontains=region_query) |
                Q(province__name__icontains=region_query) |
                Q(province__country__name__icontains=region_query) |
                Q(municipality__superregion__superregion__superregion__superregion__name__icontains=region_query)
            )

        # Build unique region combinations - use the same fields as SummaryViewSet
        regions = sites.values(
            'parish__name',
            'municipality__name', 
            'province__name',
            'province__country__name',
            'municipality__superregion__superregion__superregion__superregion__name'
        ).distinct()

        # Filter out completely empty rows
        regions = regions.exclude(
            parish__name__isnull=True,
            municipality__name__isnull=True,
            province__name__isnull=True,
            province__country__name__isnull=True,
            municipality__superregion__superregion__superregion__superregion__name__isnull=True
        )

        return regions

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Format results as requested
        results = []
        seen_regions = set()  # To avoid duplicates
        
        for region in queryset:
            parish = region.get('parish__name')
            municipality = region.get('municipality__name') 
            province = region.get('province__name')
            # Use the same country logic as SummaryViewSet
            country = (region.get('province__country__name') or 
                      region.get('municipality__superregion__superregion__superregion__superregion__name'))
            
            # Build region string based on available fields
            if parish and municipality and province and country:
                region_str = f"{parish}, {municipality}, {province}, {country}"
            elif municipality and province and country:
                region_str = f"{municipality}, {province}, {country}"
            elif province and country:
                region_str = f"{province}, {country}"
            elif municipality and country:
                region_str = f"{municipality}, {country}"
            elif country:
                region_str = country
            else:
                continue  # Skip if no meaningful data
            
            # Avoid duplicates
            if region_str not in seen_regions:
                seen_regions.add(region_str)
                results.append({
                    "region": region_str,
                    "parish": parish,
                    "municipality": municipality,
                    "province": province,
                    "country": country
                })

        # Sort results alphabetically
        results.sort(key=lambda x: x['region'])
        
        return Response({
            "count": len(results),
            "results": results
        })


# Add general search query
class GeneralSearch(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        if not q:
            return models.Image.objects.none()

        queryset = models.Image.objects.select_related(
            'site__parish', 'site__municipality', 'site__province', 'institution', 'type'
        ).prefetch_related(
            'dating_tags', 'people', 'keywords', 'rock_carving_object'
        ).filter(
            Q(dating_tags__text__icontains=q) |
            Q(dating_tags__english_translation__icontains=q) |
            Q(people__name__icontains=q) |
            Q(people__english_translation__icontains=q) |
            Q(type__text__icontains=q) |
            Q(type__english_translation__icontains=q) |
            Q(site__raa_id__icontains=q) |
            Q(site__lamning_id__icontains=q) |
            Q(site__askeladden_id__icontains=q) |
            Q(site__lokalitet_id__icontains=q) |
            Q(site__placename__icontains=q) |
            Q(keywords__text__icontains=q) |
            Q(keywords__english_translation__icontains=q) |
            Q(keywords__category__icontains=q) |
            Q(keywords__category_translation__icontains=q) |
            Q(rock_carving_object__name__icontains=q) |
            Q(institution__name__icontains=q) |
            Q(site__parish__name__icontains=q) |
            Q(site__municipality__name__icontains=q) |
            Q(site__province__name__icontains=q)
        ).filter(
            published=True
        ).distinct().order_by('-id', 'type__order')

        return queryset

    filterset_fields = ['id'] + get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])

class AdvancedSearch(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        query_params = self.request.GET

        query_conditions = []

        # Define mapping between query params and model fields
        field_mapping = {
            "site_name": ["site__raa_id", "site__lamning_id", "site__askeladden_id",
                          "site__lokalitet_id", "site__placename", "site__ksamsok_id"],
            "keyword": ["keywords__text", "keywords__english_translation", "keywords__category", "keywords__category_translation"],
            "author_name": ["people__name", "people__english_translation"],
            "dating_tag": ["dating_tags__text", "dating_tags__english_translation"],
            "image_type": ["type__text", "type__english_translation"],
            "institution_name": ["institution__name"],
            "region_name": ["site__parish__name", "site__municipality__name", "site__province__name"],
        }

        for param, fields in field_mapping.items():
            if param in query_params:
                value = query_params[param]
                # Creating OR conditions for each field
                or_conditions = [Q(**{field + '__icontains': value})
                                 for field in fields]
                query_conditions.append(
                    reduce(lambda x, y: x | y, or_conditions))

        if not query_conditions:
            # Handle no query parameters provided
            # You might want to raise an error or return an empty queryset
            # For now, returning an empty queryset
            return models.Image.objects.none()

        queryset = models.Image.objects.filter(reduce(
            lambda x, y: x & y, query_conditions), published=True).order_by('-id', 'type__order')

        return queryset

    filterset_fields = [
        'id'] + get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])


# New Module search views
class BaseSearchViewSet(DynamicDepthViewSet):
    """Base class containing common search functionality."""

    def parse_multi_values(self, values):
        """Helper method to parse multiple values from query parameters.
        
        Supports three formats:
        1. Multiple parameters: ?param=val1&param=val2
        2. Ampersand separated: ?param=val1%26val2  
        3. Comma separated: ?param=val1,val2
        """
        parsed_values = []
        for value in values:
            if value:
                # Handle multiple formats
                if '&' in value:
                    # Split by & (URL encoded as %26)
                    parsed_values.extend([v.strip() for v in value.split('&') if v.strip()])
                elif ',' in value:
                    # Split by comma
                    parsed_values.extend([v.strip() for v in value.split(',') if v.strip()])
                else:
                    # Single value
                    parsed_values.append(value.strip())
        return parsed_values

    def parse_region_groups(self, region_values):
        """
        Parse region values into groups for OR operation between groups, AND within groups.
        
        Each region_name parameter becomes a group where all parts must match (AND).
        Between different region_name parameters, we use OR.
        
        Example:
        ?region_name=Angelstad,Ljungby,Kronobergs län,SVERIGE&region_name=Alsen,Krokom,Jämtland,SVERIGE
        
        Returns: [
            ['Angelstad', 'Ljungby', 'Kronobergs län', 'SVERIGE'],
            ['Alsen', 'Krokom', 'Jämtland', 'SVERIGE']
        ]
        """
        region_groups = []
        
        for region_value in region_values:
            if not region_value:
                continue
                
            # Split by comma to get individual parts
            region_parts = [part.strip() for part in region_value.split(',')]
            
            # Filter out empty parts and add to groups
            filtered_parts = [part for part in region_parts if part]
            if filtered_parts:
                region_groups.append(filtered_parts)
        
        return region_groups
    
    def get_search_fields_mapping(self):
        """Define the mapping between search parameters and model fields."""
        return {
            "site_name": ["site__raa_id", "site__lamning_id", "site__askeladden_id",
                        "site__lokalitet_id", "site__placename", "site__ksamsok_id"],
            "author_name": ["people__name", "people__english_translation"],
            "dating_tag": ["dating_tags__text", "dating_tags__english_translation"],
            "image_type": ["type__text", "type__english_translation"],
            "institution_name": ["institution__name"],
            "region_name": ["site__parish__name", "site__municipality__name", "site__province__name",
                           "site__province__country__name", 
                           "site__municipality__superregion__superregion__superregion__superregion__name"],
            "visualization_group": ["group__text"],
            "keyword": ["keywords__text", "keywords__english_translation",
                            "keywords__category", "keywords__category_translation"],
            "3d_site": ["site__id", "site__raa_id", "site__placename", "site__lamning_id",
                        "site__askeladden_id", "site__lokalitet_id", "site__ksamsok_id"],
            "rock_carving_object": ["rock_carving_object__name"],
            "year": ["year"],
            "q": []  # Placeholder for general search across all fields
        }
    
    def get_type_field_keys(self):
        """Define search type configurations."""
        ALL_FIELDS = self.get_search_fields_mapping()
        ALL_FIELDS["q"] = sorted(set(chain.from_iterable(ALL_FIELDS.values())))
        
        return {
            "advanced": ["site_name", "author_name", "dating_tag",
                        "image_type", "institution_name", "region_name",
                        "visualization_group", "keyword", "rock_carving_object", "3d_site"],
            "general": ["q"],
        }, ALL_FIELDS
    
    def build_search_query(self, params, search_type="advanced", operator="OR"):
        """
        Build search structure that supports AND operators with separate joins.
        Special handling for region_name with multiple parameter groups.
        
        Returns dict with:
        - chain_filters: list of Q objects applied sequentially (for AND operations)  
        - single_q: combined Q object for OR operations
        """
        TYPE_FIELD_KEYS, ALL_FIELDS = self.get_type_field_keys()
        field_keys = TYPE_FIELD_KEYS.get(search_type, list(ALL_FIELDS.keys()))
        mapping_filter_fields = {key: ALL_FIELDS[key] for key in field_keys}

        operator_controlled_fields = ["author_name", "keyword", "dating_tag"]
        field_operator_mapping = {
            "author_name": "author_operator",
            "keyword": "keyword_operator",
            "dating_tag": "dating_operator"
        }

        chain_filters = []   # For AND operations (separate joins)
        grouped_qs = []      # For OR operations (combined)

        for param_key, fields in mapping_filter_fields.items():
            raw_values = params.getlist(param_key)
            if not raw_values:
                continue

            # Special handling for region_name with group logic
            if param_key == "region_name":
                region_groups = self.parse_region_groups(raw_values)
                if region_groups:
                    group_or_conditions = []
                    
                    # Each group (parameter) becomes an AND condition
                    for region_parts in region_groups:
                        group_and_conditions = []
                        
                        # Within each group, all parts must match (AND)
                        for part in region_parts:
                            part_or_conditions = []
                            for field in fields:
                                part_or_conditions.append(Q(**{f"{field}__icontains": part}))
                            
                            if part_or_conditions:
                                group_and_conditions.append(
                                    reduce(lambda x, y: x | y, part_or_conditions)
                                )
                        
                        # Combine all parts in this group with AND
                        if group_and_conditions:
                            group_condition = reduce(lambda x, y: x & y, group_and_conditions)
                            group_or_conditions.append(group_condition)
                    
                    # Combine all groups with OR
                    if group_or_conditions:
                        region_query = reduce(lambda x, y: x | y, group_or_conditions)
                        grouped_qs.append(region_query)
                
                continue  # Skip normal processing for region_name

            # Normal processing for other fields
            values = self.parse_multi_values(raw_values)
            if not values:
                continue

            if param_key in operator_controlled_fields:
                op_param = field_operator_mapping.get(param_key)
                field_operator = params.get(op_param, operator).upper()
                if field_operator not in ["AND", "OR"]:
                    field_operator = "OR"
            else:
                field_operator = "OR"

            # Build OR cluster per value
            per_value_clusters = []
            for val in values:
                cluster = Q()
                for f in fields:
                    cluster |= Q(**{f"{f}__icontains": val})
                per_value_clusters.append(cluster)

            if field_operator == "AND" and param_key in operator_controlled_fields:
                # Keep each cluster separate for separate joins
                chain_filters.extend(per_value_clusters)
            else:
                # Collapse to one OR group
                if per_value_clusters:
                    or_group = reduce(lambda x, y: x | y, per_value_clusters)
                    grouped_qs.append(or_group)

        # Combine OR groups
        single_q = None
        if grouped_qs:
            single_q = reduce(lambda x, y: x & y, grouped_qs)

        # If 3d_site are present, add image group filter
        threed_site_present = bool(params.getlist("3d_site"))
        if threed_site_present:
            # This filter will be applied to the image queryset
            group_filter = Q(group__isnull=False) & Q(published=True)
            if single_q:
                single_q = single_q & group_filter
            else:
                single_q = group_filter

        return {
            "chain_filters": chain_filters,
            "single_q": single_q
        }

    def apply_bbox_filter(self, queryset, bbox_param):
        """Apply bounding box filter to queryset."""
        if not bbox_param:
            return queryset
            
        coords = list(map(float, bbox_param.split(",")))
        if len(coords) == 4:
            polygon = Polygon.from_bbox(coords)
            site_ids = models.Site.objects.filter(
                coordinates__intersects=polygon
            ).values_list("id", flat=True)
            return queryset.filter(site_id__in=site_ids)

        return queryset
    
    def get_base_image_queryset(self):
        """Get optimized base queryset for images."""
        return (
            models.Image.objects
            .filter(published=True)
            .select_related('site', 'institution', 'type')
            # .prefetch_related('keywords', 'people', 'dating_tags')
            .defer('iiif_file', 'file', 'reference')
        )


# Add search category view
class SearchCategoryViewSet(BaseSearchViewSet):
    """A viewset to return images in a category format with advanced search capabilities."""
    serializer_class = serializers.GallerySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id'] + get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])

    def get_queryset(self):
        params = self.request.GET
        operator = params.get("operator", "OR")
        search_type = params.get("search_type", "general")  # Default to general

        queryset = self.get_base_image_queryset()

        # Apply search filters using the corrected build_search_query method
        if any(params.get(field) for field in ["site_name", "author_name", "dating_tag", 
                                              "image_type", "institution_name", "region_name", 
                                              "visualization_group", "keyword", "rock_carving_object", "3d_site", "q"]):
            search_struct = self.build_search_query(params, search_type, operator)
            
            # Apply chain filters first (each creates separate join)
            for q_part in search_struct["chain_filters"]:
                queryset = queryset.filter(q_part)
            
            # Apply combined OR query
            if search_struct["single_q"]:
                queryset = queryset.filter(search_struct["single_q"])

        # Apply bbox filter
        queryset = self.apply_bbox_filter(queryset, params.get("in_bbox"))
        return queryset.distinct().order_by('-id', 'type__order')


    def categorize_by_type(self, queryset):
        """Groups queryset results by type with counts.
        Includes an 'All' category that contains the total count of all images.
        """
        # Get total count for "All" category
        total_count = queryset.count()
        
        # Get counts by type
        grouped_data = (
            queryset
            .values("type__id", "type__text", "type__english_translation")
            .annotate(img_count=Count("id", distinct=True))
            .order_by("-img_count", "type__order")
        )

        categories = []
        
        # Add "All" category first
        if total_count > 0:
            categories.append({
                "type_id": "all",
                "type": "All Images",
                "type_translation": "Alla bilder",
                "count": total_count,
            })

        # Add individual type categories
        for entry in grouped_data:
            if entry["type__text"]:  # Only include entries with valid type text
                categories.append({
                    "type_id": entry["type__id"],
                    "type": entry["type__text"],
                    "type_translation": entry.get("type__english_translation", "Unknown"),
                    "count": entry["img_count"],
                })

        return categories

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        categorized_data = self.categorize_by_type(queryset)

        response_data = {
            "categories": categorized_data
        }
        return Response(response_data, status=status.HTTP_200_OK)

# Custom pagination class to return bounding box for paginated results
class BoundingBoxPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'limit'
    max_page_size = 100

    # This is the key optimization: override the count to be fast
    @cached_property
    def count(self):
        """
        Uses PostgreSQL's fast row estimation instead of a slow COUNT(*).
        """
        try:
            # This is getting the TOTAL table size, not your filtered queryset!
            with connection.cursor() as cursor:
                cursor.execute("SELECT reltuples::BIGINT FROM pg_class WHERE relname = %s", 
                            [self.object_list.model._meta.db_table])
                estimate = cursor.fetchone()[0]
                
                # This returns the entire table size, not your search results
                self._count_cache = min(estimate + 1000, 1000000)  # Max 1M
                return self._count_cache
        except Exception:
            return 10000  # This fallback is probably what you're seeing

        def get_paginated_response(self, data):
            return Response({
                'count': self.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'estimated_count': True, # Inform the client this is an estimate
                'results': data
            })
    
class GalleryViewSet(BaseSearchViewSet):
    """Search images by category with pagination and full search capabilities."""
    serializer_class = serializers.GallerySerializer
    pagination_class = BoundingBoxPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id'] + get_fields(models.Image, exclude=['iiif_file', 'file'])
    bbox_filter_field = 'coordinates'

    def get_queryset(self):
        params = self.request.GET
        operator = params.get("operator", "OR")
        search_type = params.get("search_type", "advanced")  # Default to advanced
        category_type = params.get("category_type")

        # Start with minimal queryset for performance
        queryset = models.Image.objects.filter(published=True)

        # Apply category filter - handle "All" category
        if category_type and category_type.lower() != "all":
            queryset = queryset.filter(type__text__iexact=category_type)

        # Apply search filters
        if any(params.get(field) for field in ["site_name", "author_name", "dating_tag", 
                                              "image_type", "institution_name", "region_name", 
                                              "visualization_group", "keyword", "rock_carving_object", "3d_site", "q"]):
            search_struct = self.build_search_query(params, search_type, operator)
            
            # Apply chain filters first (each creates separate join)
            for q_part in search_struct["chain_filters"]:
                queryset = queryset.filter(q_part)
            
            # Apply combined OR query
            if search_struct["single_q"]:
                queryset = queryset.filter(search_struct["single_q"])

        # Apply bounding box filter
        bbox_param = params.get("in_bbox")
        if bbox_param:
            queryset = self.apply_bbox_filter(queryset, bbox_param)

        # Return only IDs, ordered for consistent pagination
        return queryset.distinct('id').order_by('-id', 'type__order').values('id')

    def list(self, request, *args, **kwargs):
        """Optimized list method with better error handling and memory management."""
        try:
            # Phase 1: Get paginated IDs only
            id_queryset = self.filter_queryset(self.get_queryset())
            page_of_ids = self.paginate_queryset(id_queryset)

            if page_of_ids is None:
                return Response({"results": []})

            page_ids = [item['id'] for item in page_of_ids]
            if not page_ids:
                return self.get_paginated_response([])

            # Phase 2: Fetch full objects for current page only
            results_queryset = self._get_full_objects(page_ids)
            
            # Phase 3: Serialize data
            serializer = self.get_serializer(results_queryset, many=True)
            
            # Phase 4: Calculate bbox (can be done in parallel if needed)
            page_bbox = self.calculate_bbox_for_image_ids(page_ids)
            
            # Build response
            response = self.get_paginated_response(serializer.data)
            response.data['bbox'] = page_bbox
            
            return response

        except Exception as e:
            # Log the error in production
            import logging
            logging.error(f"Error in GalleryViewSet.list: {e}")
            return Response(
                {"error": "An error occurred while fetching results"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Cleanup to prevent memory leaks
            if 'results_queryset' in locals():
                del results_queryset
            gc.collect()

    def _get_full_objects(self, page_ids):
        """Optimized method to fetch full objects with minimal database queries."""
        return (
            models.Image.objects
            .filter(id__in=page_ids)
            .select_related(
                'site', 
                'institution', 
                'type'
            )
            .prefetch_related(
                Prefetch(
                    'keywords',
                    queryset=models.KeywordTag.objects.only(
                        'id', 'text', 'english_translation', 
                        'category', 'category_translation'
                    )
                ),
                Prefetch(
                    'people',
                    queryset=models.People.objects.only(
                        'id', 'name', 'english_translation'
                    )
                ),
                Prefetch(
                    'dating_tags',
                    queryset=models.DatingTag.objects.only(
                        'id', 'text', 'english_translation'
                    )
                )
            )
            .defer('iiif_file', 'file', 'reference')  # Defer large fields
            .order_by('type__order', 'id')
        )

    def calculate_bbox_for_image_ids(self, image_ids):
        """Optimized bbox calculation with better error handling."""
        if not image_ids:
            return None

        try:
            # Single query to get site IDs
            site_ids = list(
                models.Image.objects
                .filter(id__in=image_ids)
                .values_list('site_id', flat=True)
                .distinct()
            )
            
            # Filter out None values
            valid_site_ids = [sid for sid in site_ids if sid is not None]
            
            if not valid_site_ids:
                return None

            # Calculate bbox in single query
            bbox_result = models.Site.objects.filter(
                id__in=valid_site_ids
            ).aggregate(Extent('coordinates'))
            
            return bbox_result.get('coordinates__extent')

        except Exception as e:
            # Log error but don't fail the request
            import logging
            logging.warning(f"Error calculating bbox: {e}")
            return None

    def get_serializer_context(self):
        """Add request context for serializer optimizations."""
        context = super().get_serializer_context()
        context.update({
            'request': self.request,
            'view': self,
        })
        return context


# Add autocomplete for general search from rest_framework.viewsets import ViewSet
class GeneralSearchAutocomplete(ViewSet):
    """Return suggestions for search autocomplete with source info."""

    def list(self, request, *args, **kwargs):
        q = request.GET.get("q", "").strip().lower()
        if not q:
            return Response([])

        limit = 5
        suggestions = []

        def add_suggestions(filtered_qs, label):
            seen = set()
            for row in filtered_qs:
                for val in row if isinstance(row, (tuple, list)) else [row]:
                    if val:
                        val_str = str(val).strip()
                        if q in val_str.lower() and val_str.lower() not in seen:
                            suggestions.append({"value": val_str, "source": label})
                            seen.add(val_str.lower())

        # Keywords
        keywords_filtered = models.Image.objects.filter(
            Q(keywords__text__icontains=q) |
            Q(keywords__english_translation__icontains=q) |
            Q(keywords__category__icontains=q) |
            Q(keywords__category_translation__icontains=q)
        ).values_list(
            "keywords__text", "keywords__english_translation",
            "keywords__category", "keywords__category_translation"
        ).distinct()[:limit]

        add_suggestions(keywords_filtered, "keywords")

        # People
        people_filtered = models.Image.objects.filter(
            Q(people__name__icontains=q) |
            Q(people__english_translation__icontains=q)
        ).values_list("people__name", "people__english_translation").distinct()[:limit]

        add_suggestions(people_filtered, "people")

        # Site
        site_filtered = models.Image.objects.filter(
            Q(site__placename__icontains=q) |
            Q(site__raa_id__icontains=q) 
            # Q(site__lamning_id__icontains=q) |
            # Q(site__askeladden_id__icontains=q) |
            # Q(site__lokalitet_id__icontains=q) |
            # Q(site__ksamsok_id__icontains=q)
        # ).values_list(
        #     "site__placename", "site__raa_id", "site__lamning_id",
        #     "site__askeladden_id", "site__lokalitet_id", "site__ksamsok_id"
        # ).distinct()[:limit]
        ).values_list(
            "site__placename", "site__raa_id"
        ).distinct()[:limit]

        add_suggestions(site_filtered, "site")

        # Type
        type_filtered = models.Image.objects.filter(
            Q(type__text__icontains=q) |
            Q(type__english_translation__icontains=q)
        ).values_list("type__text", "type__english_translation").distinct()[:limit]

        add_suggestions(type_filtered, "type")

        # Institution
        institution_filtered = models.Image.objects.filter(
            institution__name__icontains=q
        ).values_list("institution__name", flat=True).distinct()[:limit]

        add_suggestions(institution_filtered, "institution")

        # Dating Tags
        tags_filtered = models.Image.objects.filter(
            Q(dating_tags__text__icontains=q) |
            Q(dating_tags__english_translation__icontains=q)
        ).values_list("dating_tags__text", "dating_tags__english_translation").distinct()[:limit]

        add_suggestions(tags_filtered, "dating tag")

        # Rock Carving
        rc_filtered = models.Image.objects.filter(
            rock_carving_object__name__icontains=q
        ).values_list("rock_carving_object__name", flat=True).distinct()[:limit]

        add_suggestions(rc_filtered, "rock carving")

        # Region
        region_filtered = models.Image.objects.filter(
            Q(site__parish__name__icontains=q) |
            Q(site__municipality__name__icontains=q) |
            Q(site__province__name__icontains=q)
        ).values_list(
            "site__parish__name", "site__municipality__name", "site__province__name"
        ).distinct()[:limit]

        add_suggestions(region_filtered, "region")

        # duplicate and sort
        unique_suggestions = {(s["value"], s["source"]) for s in suggestions}
        sorted_suggestions = sorted(
            [{"value": v, "source": s} for v, s in unique_suggestions],
            key=lambda x: x["value"]
        )[:20]

        return Response(sorted_suggestions)

class SummaryViewSet(BaseSearchViewSet):
    """A separate viewset to return summary data for images."""
    queryset = models.Image.objects.filter(published=True).order_by('type__order')
    serializer_class = serializers.SummarySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id'] + get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])

    def get_queryset(self):
        params = self.request.GET
        operator = params.get("operator", "OR")
        search_type = params.get("search_type")
        category_type = params.get("category_type")

        queryset = self.get_base_image_queryset()

        if category_type:
            queryset = queryset.filter(type__text__iexact=category_type)

        # Apply search filters using new structure
        search_struct = self.build_search_query(params, search_type, operator)
        for q_part in search_struct["chain_filters"]:
            queryset = queryset.filter(q_part)
        if search_struct["single_q"]:
            queryset = queryset.filter(search_struct["single_q"])

        queryset = self.apply_bbox_filter(queryset, params.get("in_bbox"))
        return queryset.distinct().order_by('-id', 'type__order')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # Generate summary BEFORE pagination
        summary_data = self.summarize_results(queryset)
        
        return Response(summary_data)

    def summarize_results(self, queryset):
        """Summarizes search results by creator and institution."""
        # we should add Summarise search results by geographic data too: TODO
        # Summarise by ADM0, ADM1, ADM2, socken, kommun, landskap/län: TODO
        # motif: Two level summary with keyword categories and subcategories: Done
        # Count of documentation types by site: Done
        # Show number of images for each year: Done
        # Summarise search results by creator and institution : Done

        summary = {
            "creators": [],
            "institutions": [],
            "year": [],
            "types": [],
            "motifs": [],
            "geographic": [],
            "site": []
        }

        # Count images per creator
        creator_counts = (
            queryset
            .values("people__name")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count")
        )

        # Count images per institution
        institution_counts = (
            queryset
            .values("institution__name")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count")
        )
        # Count of documentation types by site
        type_counts = (
            queryset
            .values("type__text", "type__english_translation")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count")
        )
        # Summarise search results by motif type
        motif_counts = (
            queryset
            .values("keywords__text", "keywords__english_translation" ,"keywords__category_translation", "keywords__figurative")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count")
        )
        # Show number of images for each year 
        year_counts = (
            queryset
            .values("year")
            .annotate(count=Count("id", distinct=True))
            .order_by("year")
        )

        site_counts = (
            queryset
            .values("site__raa_id", "site__lamning_id", "site__askeladden_id",
                    "site__lokalitet_id", "site__placename", "site__ksamsok_id")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count")
        )

        # Gorgraphic summary can be a json object with counts for each level of geographic data
        # ADM0, ADM1, ADM2, socken, kommun, landskap/län
    
        geographic_counts = (
            queryset
            .values("site__municipality__name", "site__parish__name", "site__province__name", 
                    "site__province__country__name", "site__municipality__superregion__superregion__superregion__superregion__name")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count")
        )

        # Format summary
        summary["creators"] = [
            {"creator": entry["people__name"], "count": entry["count"]}
            for entry in creator_counts if entry["people__name"]
        ]

        summary["site"] = [
            {
                "raa_id": entry.get("site__raa_id"),
                "lamning_id": entry.get("site__lamning_id"),
                "askeladden_id": entry.get("site__askeladden_id"),
                "lokalitet_id": entry.get("site__lokalitet_id"),
                "placename": entry.get("site__placename"),
                "ksamsok_id": entry.get("site__ksamsok_id"),
                "count": entry["count"]
            }
            for entry in site_counts
            if any([
                entry.get("site__raa_id"),
                entry.get("site__lamning_id"),
                entry.get("site__askeladden_id"),
                entry.get("site__lokalitet_id"),
                entry.get("site__placename"),
                entry.get("site__ksamsok_id")
            ])
        ]

        summary["institutions"] = [
            {"institution": entry["institution__name"], "count": entry["count"]}
            for entry in institution_counts if entry["institution__name"]
        ]   

        summary["types"] = [
            {
                "type": entry["type__text"],
                "translation": entry.get("type__english_translation"),
                "count": entry["count"]
            }
            for entry in type_counts if entry["type__text"]
        ]

        # In the summarize_results method, replace the motifs section with:
        summary["motifs"] = [
            {
                "motif": entry["keywords__text"],
                "translation": entry.get("keywords__english_translation"),
                "count": entry["count"],
                "figurative": entry.get("keywords__figurative", False)
            }
            for entry in motif_counts
            if "figure" in (entry.get("keywords__category_translation") or "").lower() and entry["keywords__text"]
        ]

        summary["year"] = [
            {"year": entry["year"], "count": entry["count"]}
            for entry in year_counts if entry["year"]
        ]

        # Geographic summary 
        summary["province"] = [
            {
                "province": entry["site__province__name"],
                "country": entry["site__province__country__name"],
                "count": entry["count"]
            }
            for entry in geographic_counts if entry["site__province__name"]
        ]

        summary["municipality"] = [
            {
                "municipality": entry["site__municipality__name"],
                "country": entry["site__province__country__name"] or entry["site__municipality__superregion__superregion__superregion__superregion__name"],
                "count": entry["count"]
            } 
            for entry in geographic_counts if entry["site__municipality__name"]
        ]

        summary["parish"] = [
            {
                "parish": entry["site__parish__name"],
                "province": entry["site__province__name"],
                "country": entry["site__province__country__name"],
                "count": entry["count"]
            }
            for entry in geographic_counts if entry["site__parish__name"]
        ]
        
        summary["geographic"] = [
            {
                "municipality": entry["site__municipality__name"], 
                "parish": entry["site__parish__name"], 
                "province": entry["site__province__name"], 
                "country": entry["site__province__country__name"] or entry["site__municipality__superregion__superregion__superregion__superregion__name"],
                "count": entry["count"]
            }
            for entry in geographic_counts
        ]

        return summary
    
# VIEW FOR OAI_CAT
@csrf_exempt
def oai(request):
    params = request.POST.copy() if request.method == "POST" else request.GET.copy()
    verb = None

    if "verb" in params:
        verb = params.pop("verb")[-1]
        if verb == "GetRecord":
            output = get_records(params, request)
        elif verb == "Identify":
            output = get_identify(request)
        elif verb == "ListRecords":
            output = get_list_records(verb, request, params)
        elif verb == "ListMetadataFormats":
            output = get_list_metadata(request, params)
        elif verb == "ListSets":
            output = get_list_set(request, params)
        else:
            output = verb_error(request)

    return output


# Add contact form for shfa
# Receive contact form submissions
class ContactFormViewSet(viewsets.ViewSet):
    def create(self, request):
        # The method check is redundant since DRF handles this
        form = ContactForm(request.data)  # Use request.data instead of request.POST
        
        if form.is_valid():
            # Process the form data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            try:
                # Send an email with better formatting
                email_subject = f'SHFA Contact Form: {subject}'
                email_body = f"""
                    Contact Form Submission

                    From: {name}
                    Email: {email}
                    Subject: {subject}
                    Message:
                    {message}
                                    """
                
                # Remove the reply_to parameter - it's not supported in older Django versions
                send_mail(
                    email_subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,  # From email
                    [settings.EMAIL_RECEIVER],   # To email
                    fail_silently=False,
                )
                
                return Response(
                    {'message': 'Email sent successfully'}, 
                    status=status.HTTP_201_CREATED
                )

            except BadHeaderError:
                return Response(
                    {'error': 'Failed to send email. Please try again later.'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except Exception as e:
                # Add general exception handling
                return Response(
                    {'error': f'Failed to send email: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # Return form validation errors
            return Response(
                {'error': 'Invalid form data', 'details': form.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )