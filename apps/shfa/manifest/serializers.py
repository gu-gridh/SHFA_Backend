from iiif_prezi3 import Manifest, Canvas, AnnotationPage, Annotation, ResourceItem
from iiif_prezi3 import Collection
from django.conf import settings
from typing import Dict, List

class IIIFManifestSerializer:
    """Generate IIIF Presentation API 3.0 compliant manifests using iiif-prezi3."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or getattr(settings, 'IIIF_BASE_URL', 'ORIGINAL_URL')
        self.site_url = getattr(settings, 'SITE_URL')
    
    def _build_thumbnail(self, id: str, width: int, height: int) -> dict:
        """Build a thumbnail object for IIIF manifest."""
        return {
            "id": id,
            "type": "Image",
            "format": "image/jpeg",
            "width": width,
            "height": height
        }
    
    def create_manifest_for_image(self, image) -> Dict:
        """Create a IIIF manifest for a single rock art image using iiif-prezi3."""
        if not hasattr(image, 'iiif_file'):
            raise ValueError("Image must have an iiif_file attribute")
        
        if not image.iiif_file:
            raise ValueError("Image must have an IIIF file")
        
        # Build IIIF image URL
        iiif_file_url = getattr(image.iiif_file, 'url', None)
        if not iiif_file_url:
            raise ValueError("Image IIIF file has no URL")
            
        if not iiif_file_url.startswith("http"):
            iiif_file_url = self.base_url.rstrip('/') + '/' + iiif_file_url.lstrip("/")
        
        # Use database fields directly
        width = image.width or 1000
        height = image.height or 800

        # Create manifest ID
        manifest_id = f"{self.site_url}/api/shfa/iiif/manifest/{image.id}"
        
        # Prepare title and summary
        title = self._get_image_title(image)
        summary = self._get_summary(image)
        
        # Create the manifest WITH the label included
        manifest = Manifest(
            id=manifest_id,
            label={
                "en": [title["en"]],
                "sv": [title["sv"]]
            }
        )
        
        # Set summary
        manifest.summary = {
            "en": [summary["en"]],
            "sv": [summary["sv"]]
        }
        
        # Add metadata
        try:
            metadata = self._build_metadata(image)
            if metadata:
                manifest.metadata = metadata
        except Exception as e:
            print(f"DEBUG: Error building metadata: {e}")
            # Continue without metadata
        
        # Add thumbnail
        thumbnail_url = f"{iiif_file_url}/full/300,/0/default.jpg"
        manifest.thumbnail = [self._build_thumbnail(
            id=thumbnail_url,
            width=300,
            height=int(300 * height / width) if width > 0 else 300
        )]
        
        # Create canvas
        canvas_id = f"{manifest_id}/canvas/1"
        canvas = Canvas(
            id=canvas_id,
            width=width,
            height=height,
            label={
                "en": [f"Canvas 1 - {title['en']}"],
                "sv": [f"Canvas 1 - {title['sv']}"]
            }
        )
        
        # Create annotation page
        annotation_page = AnnotationPage(id=f"{canvas_id}/annotation-page/1")
        
        # Create painting annotation
        annotation = Annotation(
            id=f"{canvas_id}/annotation-page/1/annotation/1",
            motivation="painting",
            target=canvas_id
        )
        
        # Create image resource
        image_resource = ResourceItem(
            id=f"{iiif_file_url}/full/max/0/default.jpg",
            type="Image",
            format="image/jpeg",
            width=width,
            height=height
        )
        
        # Add IIIF service
        image_resource.service = [{
            "id": iiif_file_url,
            "type": "ImageService3",
            "profile": "level1"
        }]
        
        # Set annotation body
        annotation.body = image_resource
        
        # Add annotation to page
        annotation_page.items = [annotation]
        
        # Add annotation page to canvas
        canvas.items = [annotation_page]
        
        # Add canvas to manifest
        manifest.items = [canvas]
        
        # Add provider
        manifest.provider = [{
            "id": "https://www.gu.se/shfa",
            "type": "Agent",
            "label": {
                "en": ["SHFA - Rock Art Database"],
                "sv": ["SHFA - Bilddatabas"]
            },
            "homepage": [{
                "id": "https://shfa.dh.gu.se/about/en",
                "type": "Text",
                "label": {
                    "en": ["SHFA - Rock Art Database"],
                    "sv": ["SHFA - Bilddatabas"]
                },
                "format": "text/html"
            }]
        }]
        
        # Add rights
        manifest.rights = "https://creativecommons.org/licenses/by-sa/4.0/"
        
        # Add required statement (attribution)
        manifest.requiredStatement = {
            "label": {
                "en": ["Attribution"],
                "sv": ["Källhänvisning"]
            },
            "value": {
                "en": [self._get_attribution(image, "en")],
                "sv": [self._get_attribution(image, "sv")]
            }
        }
        
        # Add seeAlso
        manifest.seeAlso = [{
            "id": f"{self.site_url}/api/shfa/image/{image.id}/",
            "type": "Dataset",
            "label": {
                "en": ["Full metadata"],
                "sv": ["Fullständiga metadata"]
            },
            "format": "application/json"
        }]
        
        # Return as dictionary using dict() method
        try:
            manifest_dict = manifest.dict(exclude_unset=True)
            return manifest_dict
        except AttributeError:
            # Fallback if dict() doesn't exist, use json() but parse it back
            manifest_json = manifest.json(exclude_unset=True)
            if isinstance(manifest_json, str):
                import json
                return json.loads(manifest_json)
            return manifest_json
        except Exception as e:
            print(f"DEBUG: Error serializing manifest: {e}")
            raise

    def create_collection_manifest(self, images: List, title: str = "Rock Art Collection") -> Dict:
        """Create a IIIF collection manifest using iiif-prezi3."""
        collection_id = f"{self.site_url}/api/shfa/iiif/collection"
        
        # Create collection
        collection = Collection(
            id=collection_id,
            label={
                "en": [title],
                "sv": [title]
            }
        )
        
        # Set collection summary
        collection.summary = {
            "en": ["Collection of rock art documentation images from the SHFA rock art database"],
            "sv": ["Samling av bergkonstdokumentationsbilder från SHFAs bilddatabas"]
        }
        
        # Add manifests
        manifests = []
        for image in images:
            if image.iiif_file:
                manifest_id = f"{self.site_url}/api/shfa/iiif/manifest/{image.id}"
                
                # Get title first
                img_title = self._get_image_title(image)
                
                # Create manifest reference with label
                manifest_ref = Manifest(
                    id=manifest_id,
                    label={
                        "en": [img_title["en"]],
                        "sv": [img_title["sv"]]
                    }
                )
                
                # Add thumbnail
                iiif_file_url = getattr(image.iiif_file, 'url', None)
                if not iiif_file_url.startswith("http"):
                    iiif_file_url = self.base_url.rstrip('/') + '/' + iiif_file_url.lstrip("/")
                
                width = getattr(image, 'width', 1000)
                height = getattr(image, 'height', 800)
                
                thumbnail_url = f"{iiif_file_url}/full/300,/0/default.jpg"
                manifest_ref.thumbnail = [self._build_thumbnail(
                    id=thumbnail_url,
                    width=300,
                    height=int(300 * height / width) if width > 0 else 300
                )]
                
                manifests.append(manifest_ref)
        
        collection.items = manifests
        
        # Add provider
        collection.provider = [{
            "id": "https://www.gu.se/shfa",
            "type": "Agent",
            "label": {
                "en": ["SHFA - Rock Art Database"],
                "sv": ["SHFA - Bilddatabas"]
            }
        }]
        
        # Return as dictionary
        try:
            return collection.dict(exclude_unset=True)
        except AttributeError:
            collection_json = collection.json(exclude_unset=True)
            if isinstance(collection_json, str):
                import json
                return json.loads(collection_json)
            return collection_json
    
    def _get_image_title(self, image) -> Dict[str, str]:
        """Generate a meaningful title for the rock art image."""
        parts_en = ["Rock art"]
        parts_sv = ["Bergkonst"]
        
        if image.site:
            if image.site.placename:
                parts_en.append(f"at {image.site.placename}")
                parts_sv.append(f"vid {image.site.placename}")
            elif image.site.raa_id:
                parts_en.append(f"at {image.site.raa_id}")
                parts_sv.append(f"vid {image.site.raa_id}")
            elif image.site.lamning_id:
                parts_en.append(f"at {image.site.lamning_id}")
                parts_sv.append(f"vid {image.site.lamning_id}")
        
        if image.rock_carving_object:
            parts_en.append(f"({image.rock_carving_object.name})")
            parts_sv.append(f"({image.rock_carving_object.name})")
        
        if image.year:
            parts_en.append(f"- {image.year}")
            parts_sv.append(f"- {image.year}")
        
        if len(parts_en) == 1:
            parts_en.append(f"(Image {image.id})")
            parts_sv.append(f"(Bild {image.id})")
        
        return {
            "en": " ".join(parts_en),
            "sv": " ".join(parts_sv)
        }
    
    def _get_summary(self, image) -> Dict[str, str]:
        """Generate a meaningful summary for the rock art image."""
        if hasattr(image, 'description') and image.description:
            return {"en": image.description, "sv": image.description}
        
        summary_parts_en = []
        summary_parts_sv = []
        
        if image.type:
            type_en = image.type.english_translation or image.type.text
            summary_parts_en.append(f"{type_en} documentation")
            summary_parts_sv.append(f"{image.type.text}-dokumentation")
        else:
            summary_parts_en.append("Rock art documentation")
            summary_parts_sv.append("Bergkonstdokumentation")
        
        if image.site and image.site.placename:
            summary_parts_en.append(f"from {image.site.placename}")
            summary_parts_sv.append(f"från {image.site.placename}")
        
        if image.year:
            summary_parts_en.append(f"from {image.year}.")
            summary_parts_sv.append(f"från {image.year}.")
        
        if image.collection:
            summary_parts_en.append(f"Part of the {image.collection.name} collection")
            summary_parts_sv.append(f"Del av samlingen {image.collection.name}")
        
        summary_parts_en.append("from the SHFA rock art database.")
        summary_parts_sv.append("från SHFAs bilddatabasen.")
        
        return {
            "en": " ".join(summary_parts_en),
            "sv": " ".join(summary_parts_sv)
        }
    
    def _get_attribution(self, image, lang: str) -> str:
        """Generate attribution statement."""
        parts = []
        
        if image.author:
            if lang == "en":
                parts.append(f"Photographer: {image.author.english_translation or image.author.name}")
            else:
                parts.append(f"Fotograf: {image.author.name}")
        
        if image.institution:
            if lang == "en":
                parts.append(f"Institution: {image.institution.name}")
            else:
                parts.append(f"Institution: {image.institution.name}")
        
        if image.year:
            if lang == "en":
                parts.append(f"Year: {image.year}")
            else:
                parts.append(f"År: {image.year}")
        
        if lang == "en":
            parts.append(f"SHFA Rock Art Database. Image ID: {image.id}")
        else:
            parts.append(f"SHFA Bilddatabas. Bild-ID: {image.id}")
        
        return ". ".join(parts)
    
    def _build_metadata(self, image) -> List[Dict]:
        """Build comprehensive metadata array for IIIF manifest."""
        metadata = []
        
        # Site information
        if image.site:
            if image.site.raa_id:
                metadata.append({
                    "label": {"en": ["RAÄ Number"], "sv": ["RAÄ-nummer"]},
                    "value": {"en": [image.site.raa_id], "sv": [image.site.raa_id]}
                })
            
            if image.site.lamning_id:
                metadata.append({
                    "label": {"en": ["Lämning ID"], "sv": ["Lämnings-ID"]},
                    "value": {"en": [image.site.lamning_id], "sv": [image.site.lamning_id]}
                })
            
            if hasattr(image.site, 'askeladden_id') and image.site.askeladden_id:
                metadata.append({
                    "label": {"en": ["Askeladden ID"], "sv": ["Askeladden ID"]},
                    "value": {"en": [image.site.askeladden_id], "sv": [image.site.askeladden_id]}
                })
            
            if hasattr(image.site, 'lokalitet_id') and image.site.lokalitet_id:
                metadata.append({
                    "label": {"en": ["Lokalitet ID"], "sv": ["Lokalitet-ID"]},
                    "value": {"en": [image.site.lokalitet_id], "sv": [image.site.lokalitet_id]}
                })
            
            if image.site.placename:
                metadata.append({
                    "label": {"en": ["Location"], "sv": ["Plats"]},
                    "value": {"en": [image.site.placename], "sv": [image.site.placename]}
                })
            
            if image.site.municipality:
                metadata.append({
                    "label": {"en": ["Municipality"], "sv": ["Kommun"]},
                    "value": {"en": [image.site.municipality.name], "sv": [image.site.municipality.name]}
                })
            
            if image.site.province:
                metadata.append({
                    "label": {"en": ["County"], "sv": ["Län"]},
                    "value": {"en": [image.site.province.name], "sv": [image.site.province.name]}
                })
        
        # Rock art object/area
        if image.rock_carving_object:
            metadata.append({
                "label": {"en": ["Rock Art Area"], "sv": ["Bergkonstområde"]},
                "value": {"en": [image.rock_carving_object.name], "sv": [image.rock_carving_object.name]}
            })
        
        # Documentation information
        if image.year:
            metadata.append({
                "label": {"en": ["Documentation Year"], "sv": ["Dokumentationsår"]},
                "value": {"en": [str(image.year)], "sv": [str(image.year)]}
            })
        
        # Image type and subtype
        if image.type:
            type_en = image.type.english_translation or image.type.text
            metadata.append({
                "label": {"en": ["Image Type"], "sv": ["Bildtyp"]},
                "value": {"en": [type_en], "sv": [image.type.text]}
            })
        
        if image.subtype:
            subtype_en = image.subtype.english_translation or image.subtype.text
            metadata.append({
                "label": {"en": ["Image Subtype"], "sv": ["Bildundertyp"]},
                "value": {"en": [subtype_en], "sv": [image.subtype.text]}
            })
        
        # Creator information
        if image.author:
            author_en = image.author.english_translation or image.author.name
            metadata.append({
                "label": {"en": ["Creator/Photographer"], "sv": ["Skapare/Fotograf"]},
                "value": {"en": [author_en], "sv": [image.author.name]}
            })
        
        # People (additional creators)
        people = getattr(image, 'people', None)
        if people:
            try:
                people_list = people.all()
                if people_list:
                    en_people = [p.english_translation or p.name for p in people_list]
                    sv_people = [p.name for p in people_list]
                    metadata.append({
                        "label": {"en": ["Additional Creators"], "sv": ["Ytterligare skapare"]},
                        "value": {"en": en_people, "sv": sv_people}
                    })
            except:
                pass
        
        # Institution
        if image.institution:
            metadata.append({
                "label": {"en": ["Institution"], "sv": ["Institution"]},
                "value": {"en": [image.institution.name], "sv": [image.institution.name]}
            })
        
        # Collection
        if image.collection:
            metadata.append({
                "label": {"en": ["Collection"], "sv": ["Samling"]},
                "value": {"en": [image.collection.name], "sv": [image.collection.name]}
            })
        
        # Keywords/subjects
        keywords = getattr(image, 'keywords', None)
        if keywords:
            try:
                keyword_list = keywords.all()
                if keyword_list:
                    en_keywords = [k.english_translation or k.text for k in keyword_list]
                    sv_keywords = [k.text for k in keyword_list]
                    metadata.append({
                        "label": {"en": ["Subjects/Motifs"], "sv": ["Motiv"]},
                        "value": {"en": en_keywords, "sv": sv_keywords}
                    })
            except:
                pass
        
        # Dating information
        dating_tags = getattr(image, 'dating_tags', None)
        if dating_tags:
            try:
                dating_list = dating_tags.all()
                if dating_list:
                    en_datings = [d.english_translation or d.text for d in dating_list]
                    sv_datings = [d.text for d in dating_list]
                    metadata.append({
                        "label": {"en": ["Dating"], "sv": ["Datering"]},
                        "value": {"en": en_datings, "sv": sv_datings}
                    })
            except:
                pass
        
        # Technical metadata
        if image.width and image.height:
            metadata.append({
                "label": {"en": ["Dimensions"], "sv": ["Dimensioner"]},
                "value": {
                    "en": [f"{image.width} × {image.height} pixels"],
                    "sv": [f"{image.width} × {image.height} pixlar"]
                }
            })
        
        # References
        if image.reference:
            metadata.append({
                "label": {"en": ["References"], "sv": ["Referenser"]},
                "value": {"en": [image.reference], "sv": [image.reference]}
            })
        
        # Group information
        if image.group:
            metadata.append({
                "label": {"en": ["Visualization Group"], "sv": ["Visualiseringsgrupp"]},
                "value": {"en": [image.group.text], "sv": [image.group.text]}
            })
        
        # Legacy ID for reference
        if image.legacy_id:
            metadata.append({
                "label": {"en": ["Legacy ID"], "sv": ["Äldre ID"]},
                "value": {"en": [str(image.legacy_id)], "sv": [str(image.legacy_id)]}
            })
        
        return metadata