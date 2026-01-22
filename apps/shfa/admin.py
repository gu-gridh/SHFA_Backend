from .models import *
from django.utils.html import format_html
from django.contrib.gis import admin
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from django.utils.translation import gettext_lazy as _
from shfa.utils import get_fields, DEFAULT_FIELDS, DEFAULT_EXCLUDE
from admin_auto_filters.filters import AutocompleteFilter
from rangefilter.filters import NumericRangeFilter
from django.contrib.admin import EmptyFieldListFilter
from django.conf import settings
import mapwidgets


MAP_WIDGETS = {
    "Leaflet": {
        "PointField": {
            "interactive": {
                "mapOptions": {
                    "zoom": 5,
                    "scrollWheelZoom": True,
                    "center": (57.124093162383616, 7.830100815389867),
                },
                "tileLayer": {
                    "urlTemplate": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                    "options": {"maxZoom": 20},
                },
            }
        },
        "markerFitZoom": 14,
    }
}


class SiteFilter(AutocompleteFilter):
    title = _('Site')  # display title
    field_name = 'site'  # name of the foreign key field


class InstitutionFilter(AutocompleteFilter):
    title = _('Institution')  # display title
    field_name = 'institution'  # name of the foreign key field


class CollectionFilter(AutocompleteFilter):
    title = _('Collection')  # display title
    field_name = 'collection'  # name of the foreign key field


# class AuthorFilter(AutocompleteFilter):
#     title = _('Creator')  # display title
#     field_name = 'author'  # name of the foreign key field


class KeywordFilter(AutocompleteFilter):
    title = _('Keywords')  # display title
    field_name = 'keywords'  # name of the foreign key field


class FilenameFilter(AutocompleteFilter):
    title = _('Upload Filename')  # display title
    field_name = 'filename'  # name of the foreign key field


@admin.register(People)
class PeopleAdmin(admin.ModelAdmin):

    readonly_fields = ['legacy_id']
    list_display = ["name", "english_translation"]
    search_fields = ["name", "english_translation"]
    ordering = ('name',)

@admin.register(GettyAATVocab)
class GettyKeywordAdmin(admin.ModelAdmin):
    list_display = ["term", "link", "skos_match"]
    search_fields = ["term", "link", "skos_match"]
    ordering = ('term',)

@admin.register(KeywordTag)
class KeywordTagAdmin(admin.ModelAdmin):

    readonly_fields = ['legacy_id']
    list_display = ["text", "english_translation"]
    search_fields = ["text", "english_translation"]


@admin.register(DatingTag)
class DatingTagAdmin(admin.ModelAdmin):

    readonly_fields = ['legacy_id']
    list_display = ["text", "english_translation"]
    search_fields = ["text", "english_translation"]


@admin.register(Image)
class ImageModel(admin.ModelAdmin):

    fields = ['image_preview', *get_fields(Image, exclude=['id'])]
    readonly_fields = ['legacy_id', 'iiif_file',
                       'uuid', 'image_preview', *DEFAULT_FIELDS]
    autocomplete_fields = ['site', 'collection', 'institution',
                           'type', 'rock_carving_object', 'subtype', 'people']
    list_display = ['thumbnail_preview', 'site', 'rock_carving_object',
                    'year', 'collection', 'institution', 'type', 'subtype', 'file']
    search_fields = ['site__lamning_id', 'site__raa_id', 'rock_carving_object__name',
                     'site__municipality__name', 'site__parish__name', 'subtype__text', 'file']
    list_filter = [
        ('year', NumericRangeFilter),
        ('site', EmptyFieldListFilter),
        'type',
        'published',
        InstitutionFilter,
        CollectionFilter,
        # AuthorFilter,
        SiteFilter,
        KeywordFilter,
        'file'
    ]
    # Removed 'people' from filter_horizontal to use autocomplete_fields instead
    # This avoids issues with large datasets and SelectFilter2.js
    filter_horizontal = ['keywords', 'dating_tags']
    list_per_page = 25

    def image_preview(self, obj):
        if 'tif' in obj.file.path:
            return format_html(f'<img src="{settings.IIIF_URL}{obj.iiif_file}/full/full/0/default.jpg" height="300" />')
        else:
            return format_html(f'<img src="{settings.ORIGINAL_URL}/{obj.file}" height="300" />')

    def thumbnail_preview(self, obj):
        if 'tif' in obj.file.path:
            return format_html(f'<img src="{settings.IIIF_URL}{obj.iiif_file}/full/full/0/default.jpg" height="100" />')
        else:
            return format_html(f'<img src="{settings.ORIGINAL_URL}/{obj.file}" height="100" />')

    # image_preview.short_description = 'Image preview'
    # image_preview.allow_tags = True
    # thumbnail_preview.short_description = 'Image thumbnail'
    # thumbnail_preview.allow_tags = True


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    fields = get_fields(Site, exclude=DEFAULT_EXCLUDE+["id"])
    readonly_fields = [*DEFAULT_FIELDS]
    list_display = ['id', 'raa_id', 'lamning_id', 'lokalitet_id',
                    'askeladden_id', 'get_ksamsok_link', 'placename']
    search_fields = ['raa_id', 'lamning_id',
                     'askeladden_id', 'lokalitet_id', 'placename']
    ordering = ('raa_id', 'placename')
    formfield_overrides = {
        models.PointField: {
            "widget": mapwidgets.LeafletPointFieldWidget(settings=MAP_WIDGETS)}
    }

    # filter_horizontal = ['raa_id', 'lamning_id', 'askeladden_id', 'lokalitet_id','placename']
    # def get_search_results(self, request, queryset, search_term):
    #     queryset, use_distinct = super().get_search_results(request, queryset, search_term)
    #     try:
    #         queryset = Site.objects.filter(raa_id__exact=search_term)
    #     except ValueError:
    #         pass
    #     else:
    #         queryset |= Site.objects.filter(raa_id__icontains=search_term)
    #     return queryset, use_distinct

    @admin.display(description=_('Read at Fornsök'))
    def get_ksamsok_link(self, obj):

        if obj.ksamsok_id:

            return format_html("<a href='{url}' target='_blank' rel='noopener noreferrer'>{ksamsok_id}</a>",
                               url="https://kulturarvsdata.se/raa/lamning/" + obj.ksamsok_id,
                               ksamsok_id=obj.ksamsok_id)
        else:
            return format_html("")


@admin.register(Compilation)
class CompilationAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    autocomplete_fields = ["images"]
    ordering = ('name',)
    filter_horizontal = ("images",)


# @admin.register(Author)
# class AuthorAdmin(admin.ModelAdmin):

#     readonly_fields = ['legacy_id']
#     list_display = ["name", "english_translation"]
#     search_fields = ["name", "english_translation"]
#     ordering = ('name',)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):

    readonly_fields = ['legacy_id']
    list_display = ["name"]
    search_fields = ["name"]
    ordering = ('name',)


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):

    readonly_fields = ['legacy_id']
    list_display = ["name", "address", "url", "email"]
    search_fields = ["name"]
    ordering = ('name',)


@admin.register(ImageTypeTag)
class ImageTypeTagAdmin(admin.ModelAdmin):

    readonly_fields = ['legacy_id']
    list_display = ["text", "english_translation", "order"]
    search_fields = ["text", "english_translation", "order"]


@admin.register(RockCarvingObject)
class RockCarvingObjectAdmin(admin.ModelAdmin):

    list_display = ["name", "code"]
    search_fields = ["name"]
    ordering = ('name',)


# @admin.register(CarvingTag)
# class CarvingTagAdmin(admin.ModelAdmin):

#     list_display = ["text", "english_translation"]
#     search_fields = ["text", "english_translation"]

# 3D models admin
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["text"]
    search_fields = ["text"]


@admin.register(MethodTag)
class MethodTagAdmin(admin.ModelAdmin):
    list_display = ["text", "english_translation"]
    search_fields = ["text", "english_translation"]


@admin.register(WeatherTag)
class WeatherTagAdmin(admin.ModelAdmin):
    list_display = ["text", "english_translation"]
    search_fields = ["text", "english_translation"]


@admin.register(RTI)
class RTIAdmin(admin.ModelAdmin):
    list_display = ["url", "group"]
    search_fields = ["group__text"]


@admin.register(ImageSubType)
class ImageSubTypeAdmin(admin.ModelAdmin):
    list_display = ["text", "english_translation", "order"]
    search_fields = ["text", "english_translation", "order"]


@admin.register(Geology)
class GeologyAdmin(admin.ModelAdmin):
    list_display = ["type", "description"]
    search_fields = ["type", "description"]


@admin.register(CameraLens)
class CameraLensAdmin(admin.ModelAdmin):
    list_display = ["name", "focal_length"]
    search_fields = ["name", "focal_length"]


@admin.register(CameraModel)
class CameraModelAdmin(admin.ModelAdmin):
    list_display = ["name", ]
    search_fields = ["name", "lens__name"]

class CameraMetaAdmin(admin.ModelAdmin):
    fields = get_fields(CameraMeta, exclude=DEFAULT_EXCLUDE + ["id"])
    readonly_fields = [*DEFAULT_FIELDS]
    list_display = ["link", "camera_lens", "camera_model",
                    "group", "mm35_equivalent_display"]
    search_fields = ["link", "camera_lens__name",
                     "camera_model__name", "group__text"]

    def mm35_equivalent_display(self, obj):
        return obj.mm35_equivalent

    mm35_equivalent_display.short_description = '35mm Equivalent'


admin.site.register(CameraMeta, CameraMetaAdmin)

class SHFA3DAdmin(admin.ModelAdmin):
    # display_raw = True
    fields = get_fields(SHFA3D, exclude=DEFAULT_EXCLUDE+["id"])
    readonly_fields = [*DEFAULT_FIELDS]
    list_display = ["site", "institution", "group"]
    search_fields = ["creators__name", "site__placename", "institution__name"]
    list_filter = ["creators", "site", "institution"]
    # autocomplete_fields = ["creators", "site", "institution","keywords", "datings"]
    filter_horizontal = ["creators", "keywords", "datings"]


class SHFA3DMeshAdmin(admin.ModelAdmin, DynamicArrayMixin):
    display_raw = True
    fields = get_fields(SHFA3DMesh, exclude=DEFAULT_EXCLUDE+["id"])
    readonly_fields = [*DEFAULT_FIELDS]
    list_display = ["group"]
    search_fields = ["group__text", "method__text", "method__english_translation"]
    list_filter = ["group"]
    autocomplete_fields = ["group"]
    filter_horizontal = ["weather"]


@admin.register(MetadataFormat)
class MetadataFormatAdmin(admin.ModelAdmin):
    list_display = ["prefix"]


@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    list_display = ["spec", "name", "description"]
    search_fields = ["spec", "name", "description"]
    ordering = ('name',)

@admin.register(ResumptionToken)
class ResumptionTokenAdmin(admin.ModelAdmin):
    list_display = ["token"]


admin.site.register(SHFA3D, SHFA3DAdmin)
admin.site.register(SHFA3DMesh, SHFA3DMeshAdmin)
