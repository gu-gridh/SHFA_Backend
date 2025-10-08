from django.urls import path, include
from rest_framework import routers
from . import views
import shfa.utils as utils
from .views import oai
from .manifest import urls as manifest_urls

router = routers.DefaultRouter()
endpoint = utils.build_app_endpoint()

documentation = utils.build_app_api_documentation("", endpoint)

router.register(rf'{endpoint}/image', views.IIIFImageViewSet, basename='image')
router.register(rf'{endpoint}/site', views.SiteViewSet, basename='site')
router.register(rf'{endpoint}/geojson/site',
                views.SiteGeoViewSet, basename='site as geojson')
router.register(rf'{endpoint}/compilation',
                views.CompilationViewset, basename='compilation')

# urls for advanced search options
router.register(rf'{endpoint}/search/site',
                views.SiteSearchViewSet, basename='search site')
router.register(rf'{endpoint}/search/image',
                views.SearchBoundingBoxImageViewSet, basename='bounding box image')
router.register(rf'{endpoint}/search/type',
                views.TypeSearchViewSet, basename='site type')
router.register(rf'{endpoint}/search/keywords',
                views.SearchKeywords, basename='keywords')
router.register(rf'{endpoint}/search/carving',
                views.SearchRockCarving, basename='search rock carving')
router.register(rf'{endpoint}/search/author',
                views.SearchPeople, basename='search for image creator')
router.register(rf'{endpoint}/search/institution',
                views.SearchInstitution, basename='institution')
router.register(rf'{endpoint}/search/dating',
                views.SearchDatinTag, basename='dating Tag')
router.register(rf'{endpoint}/search/advance',
                views.AdvancedSearch, basename='advanced search')
router.register(rf'{endpoint}/search/region',
                views.RegionSearchViewSet, basename='region search')
router.register(rf'{endpoint}/search/visualization_group',
                views.SearchVisualizationGroupViewset, basename='visualization group search')
router.register(rf'{endpoint}/search/autocomplete',
                views.GeneralSearchAutocomplete, basename='general search autocomplete')

# General search url
router.register(rf'{endpoint}/search', views.GeneralSearch, basename='search')

# urls for the image gallery
router.register(rf'{endpoint}/gallery',
                views.GalleryViewSet, basename='gallery')
router.register(rf'{endpoint}/type_categorized',
                views.SearchCategoryViewSet, basename='gallery categorized by type')
router.register(rf'{endpoint}/summary', 
                views.SummaryViewSet, basename='gallery-summary')

# urls for the 3D models
router.register(rf'{endpoint}/visualization_groups',
                views.VisualizationGroupViewset, basename='Visualization 3D models')
router.register(rf'{endpoint}/shfa3d',
                views.SHFA3DViewSet, basename='3D models')
router.register(rf'{endpoint}/shfa3dmesh',
                views.SHFA3DMeshViewset, basename='3D meshes')
router.register(rf'{endpoint}/geology',
                views.GeologyViewSet, basename='geology')
router.register(rf'{endpoint}/camerameta',
                views.CameraSpecificationViewSet, basename='camera meta data')
router.register(rf'{endpoint}/null_visualization_group',
                views.NullVisualizationGroupViewset, basename='Null Visualization images')    
# Manifest IIIF endpoints using the ManifestIIIFViewSet in manifest.urls
path(rf'{endpoint}/iiif/', include('apps.shfa.manifest.urls')),

# url for contact form
router.register(r'contact', views.ContactFormViewSet, basename='contact')

urlpatterns = [
    path('', include(router.urls)),
    # add oai-pmh end points
    path(rf'{endpoint}/OAICat/', views.oai, name="oai"),
    
    # Include manifest module URLs
    path(rf'{endpoint}/iiif/', include('apps.shfa.manifest.urls')),
    
    # Automatically generated views
    *utils.get_model_urls('shfa', endpoint,
                          exclude=['image', 'site', 'compilation', 'image_keywords',
                                   'image_carving_tags', 'image_dating_tags', 'compilation_images', 'geology', 'shfa3dmesh', 'shfa3d']),

    *utils.get_model_urls('shfa', f'{endpoint}',
                          exclude=['image', 'site', 'geology', 'shfa3dmesh', 'shfa3d']),
    *documentation
]
