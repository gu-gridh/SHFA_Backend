from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
import json
from collections import OrderedDict

from ..models import Image, Site, ImageTypeTag
from .serializers import IIIFManifestSerializer
from .utils import validate_iiif_manifest

# Manifest view for IIIF
class ManifestIIIFViewSet(viewsets.ViewSet):
    """IIIF Presentation API endpoints for rock art images."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iiif_serializer = IIIFManifestSerializer()
    
    @method_decorator(cache_page(60 * 60 * 24))  # Cache for 24 hours
    def manifest(self, request, pk=None):
        """Get IIIF manifest for a single rock art image."""
        try:
            # Optimized query with all needed relationships
            image = get_object_or_404(
                Image.objects.select_related(
                    'site',
                    'site__municipality',
                    'site__province',
                    'site__parish',
                    'institution',
                    'type',
                    'subtype',
                    'author',
                    'collection',
                    'rock_carving_object',
                    'group'
                ).prefetch_related(
                    'keywords',
                    'people',
                    'dating_tags'
                ),
                pk=pk,
                published=True
            )
            
            if not image.iiif_file:
                return Response(
                    {"error": "Image does not have IIIF support"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create cache key that includes update timestamp
            cache_key = f"iiif_manifest_{image.id}"
            if hasattr(image, 'updated_at'):
                cache_key += f"_{image.updated_at.timestamp()}"
            
            cached_manifest = cache.get(cache_key)
            if cached_manifest:
                manifest_json = cached_manifest
            else:
                manifest_json = self.iiif_serializer.create_manifest_for_image(image)
                cache.set(cache_key, manifest_json, timeout=60*60*24)  # Cache 24 hours
            
            # Reorder to put @context first
            ordered_manifest = OrderedDict()
            ordered_manifest["@context"] = "http://iiif.io/api/presentation/3/context.json"
            
            # Explicitly add key fields in order
            if "id" in manifest_json:
                ordered_manifest["id"] = manifest_json["id"]
            
            ordered_manifest["type"] = "Manifest"  # Ensure type is always present
            
            if "label" in manifest_json:
                ordered_manifest["label"] = manifest_json["label"]
            
            # Add all remaining keys
            for key, value in manifest_json.items():
                if key not in ordered_manifest:
                    ordered_manifest[key] = value

            response = HttpResponse(
                json.dumps(ordered_manifest, indent=2, ensure_ascii=False),
                content_type='application/json;profile="http://iiif.io/api/presentation/3/context.json"'
            )
            
            response['Access-Control-Allow-Origin'] = '*'
            response['Cache-Control'] = 'public, max-age=86400'
            response['Vary'] = 'Accept-Language'
            
            return response
            
        except Exception as e:
            import logging
            logging.error(f"Error creating manifest for image {pk}: {str(e)}")
            return Response(
                {"error": f"Error creating manifest: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def collection(self, request):
        """Get IIIF collection manifest for multiple rock art images."""
        try:
            # Get query parameters for filtering
            site_id = request.GET.get('site_id')
            type_id = request.GET.get('type_id')
            keywords = request.GET.get('keywords')
            limit = min(int(request.GET.get('limit', 50)), 100)  # Max 100 items
            
            # Build cache key based on parameters
            cache_key = f"iiif_collection_{site_id}_{type_id}_{keywords}_{limit}"
            cached_collection = cache.get(cache_key)
            
            if cached_collection:
                response = HttpResponse(
                    json.dumps(cached_collection, indent=2, ensure_ascii=False),
                    content_type='application/json;profile="http://iiif.io/api/presentation/3/context.json"'
                )
            else:
                # Build optimized queryset
                queryset = Image.objects.filter(
                    published=True,
                    iiif_file__isnull=False,
                    width__isnull=False,
                    height__isnull=False
                ).select_related(
                    'site',
                    'rock_carving_object'
                ).only(
                    'id', 'iiif_file', 'width', 'height', 'year',
                    'site__placename', 'site__raa_id', 'site__lamning_id',
                    'rock_carving_object__name'
                )
                
                if site_id:
                    queryset = queryset.filter(site_id=site_id)
                
                if type_id:
                    queryset = queryset.filter(type_id=type_id)
                
                if keywords:
                    queryset = queryset.filter(keywords__text__icontains=keywords)
                
                # Limit results
                images = queryset[:limit]
                
                if not images:
                    return Response(
                        {"error": "No images found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Create collection title
                title = self._build_collection_title(site_id, type_id, keywords)
                
                collection = self.iiif_serializer.create_collection_manifest(images, title)
                cache.set(cache_key, collection, timeout=60*30)  # Cache 30 minutes
                
                response = HttpResponse(
                    json.dumps(collection, indent=2, ensure_ascii=False),
                    content_type='application/json;profile="http://iiif.io/api/presentation/3/context.json"'
                )
            
            response['Access-Control-Allow-Origin'] = '*'
            response['Cache-Control'] = 'public, max-age=1800'
            response['Vary'] = 'Accept-Language'
            
            return response
            
        except Exception as e:
            import logging
            logging.error(f"Error creating collection: {str(e)}")
            return Response(
                {"error": f"Error creating collection: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def site_collection(self, request, site_id=None):
        """Get IIIF collection for a specific rock art site."""
        try:
            site = get_object_or_404(Site, pk=site_id)
            
            images = Image.objects.filter(
                site=site,
                published=True,
                iiif_file__isnull=False,
                width__isnull=False,
                height__isnull=False
            ).select_related(
                'site',
                'rock_carving_object'
            ).only(
                'id', 'iiif_file', 'width', 'height', 'year',
                'site__placename', 'site__raa_id', 'site__lamning_id',
                'rock_carving_object__name'
            )
            
            if not images:
                return Response(
                    {"error": f"No images found for site {site.placename or site.raa_id or site_id}"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Build site-specific title - Updated to "Rock Art"
            if site.placename:
                title = f"Rock Art at {site.placename}"
            elif site.raa_id:
                title = f"Rock Art at {site.raa_id}"
            elif site.lamning_id:
                title = f"Rock Art at {site.lamning_id}"
            else:
                title = f"Rock Art at Site {site_id}"
            
            collection = self.iiif_serializer.create_collection_manifest(images, title)
            
            response = HttpResponse(
                json.dumps(collection, indent=2, ensure_ascii=False),
                content_type='application/json;profile="http://iiif.io/api/presentation/3/context.json"'
            )
            response['Access-Control-Allow-Origin'] = '*'
            response['Cache-Control'] = 'public, max-age=3600'
            
            return response
            
        except Exception as e:
            import logging
            logging.error(f"Error creating site collection: {str(e)}")
            return Response(
                {"error": f"Error creating site collection: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _build_collection_title(self, site_id, type_id, keywords):
        """Build a meaningful collection title based on filters."""
        title_parts = ["Rock Art Collection"]  # Changed from "Rock Carving Collection"
        
        if site_id:
            try:
                site = Site.objects.get(id=site_id)
                if site.placename:
                    title_parts.append(f"from {site.placename}")
                elif site.raa_id:
                    title_parts.append(f"from {site.raa_id}")
            except:
                pass
        
        if type_id:
            try:
                image_type = ImageTypeTag.objects.get(id=type_id)
                type_name = image_type.english_translation or image_type.text
                title_parts.append(f"({type_name})")
            except:
                pass
        
        if keywords:
            title_parts.append(f"with keyword '{keywords}'")
        
        return " ".join(title_parts)
    
    def institution_manifest(self, request, institution_id=None):
        """Get IIIF manifest for all images from a specific institution."""
        try:
            images = Image.objects.filter(
                institution_id=institution_id,
                published=True,
                iiif_file__isnull=False,
                width__isnull=False,
                height__isnull=False
            ).select_related(
                'site',
                'rock_carving_object'
            ).only(
                'id', 'iiif_file', 'width', 'height', 'year',
                'site__placename', 'site__raa_id', 'site__lamning_id',
                'rock_carving_object__name'
            )
            
            if not images:
                return Response(
                    {"error": f"No images found for institution {institution_id}"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            title = f"Rock Art Collection from Institution {institution_id}"
            collection = self.iiif_serializer.create_collection_manifest(images, title)
            
            response = HttpResponse(
                json.dumps(collection, indent=2, ensure_ascii=False),
                content_type='application/json;profile="http://iiif.io/api/presentation/3/context.json"'
            )
            response['Access-Control-Allow-Origin'] = '*'
            response['Cache-Control'] = 'public, max-age=3600'
            
            return response
            
        except Exception as e:
            import logging
            logging.error(f"Error creating institution manifest: {str(e)}")
            return Response(
                {"error": f"Error creating institution manifest: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def type_manifest(self, request, type=None):
        """Get IIIF manifest for all images of a specific type."""
        try:
            images = Image.objects.filter(
                type__text=type,
                published=True,
                iiif_file__isnull=False,
                width__isnull=False,
                height__isnull=False
            ).select_related(
                'site',
                'rock_carving_object'
            ).only(
                'id', 'iiif_file', 'width', 'height', 'year',
                'site__placename', 'site__raa_id', 'site__lamning_id',
                'rock_carving_object__name'
            )
            
            if not images:
                return Response(
                    {"error": f"No images found for type '{type}'"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            title = f"Rock Art Collection of Type '{type}'"
            collection = self.iiif_serializer.create_collection_manifest(images, title)
            
            response = HttpResponse(
                json.dumps(collection, indent=2, ensure_ascii=False),
                content_type='application/json;profile="http://iiif.io/api/presentation/3/context.json"'
            )
            response['Access-Control-Allow-Origin'] = '*'
            response['Cache-Control'] = 'public, max-age=3600'
            
            return response
            
        except Exception as e:
            import logging
            logging.error(f"Error creating type manifest: {str(e)}")
            return Response(
                {"error": f"Error creating type manifest: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except ImageTypeTag.DoesNotExist:
            return Response(
                {"error": f"Image type '{type}' does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import logging
            logging.error(f"Unexpected error in type_manifest: {str(e)}")
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except json.JSONDecodeError as e:
            import logging
            logging.error(f"JSON decode error in type_manifest: {str(e)}")
            return Response(
                {"error": "Invalid JSON format"},
                status=status.HTTP_400_BAD_REQUEST
            )
