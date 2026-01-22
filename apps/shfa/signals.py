from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import ResumptionToken, Image
import requests


@receiver(pre_save, sender=ResumptionToken)
def delete_old_resumption_tokens(sender, **kwargs):
    """Delete expired resumption tokens."""
    ResumptionToken.objects.filter(expiration_date__lte=timezone.now()).delete()


@receiver(post_save, sender=Image)
def update_image_dimensions(sender, instance, created, **kwargs):
    # Only fetch if width or height is missing and iiif_file exists
    # And specifically prevent running this if we are just updating width/height
    if kwargs.get('update_fields') and 'width' in kwargs.get('update_fields'):
        return

    if (instance.width is None or instance.height is None) and instance.iiif_file:
        base_url = "https://img.dh.gu.se/shfa/static/"
        iiif_file_url = getattr(instance.iiif_file, 'url', None)
        if not iiif_file_url:
            return
        if not iiif_file_url.startswith("http"):
            iiif_file_url = base_url + iiif_file_url.lstrip("/")
        info_url = f"{iiif_file_url}/info.json"
        try:
            response = requests.get(info_url, timeout=5)
            if response.status_code == 200:
                info = response.json()
                width = info.get("width")
                height = info.get("height")
                # Only update if values are present
                if width and height:
                     # Use .update() to bypass signals/save() overrides - Fixes server 302 issue
                    Image.objects.filter(pk=instance.pk).update(width=width, height=height)
        except Exception as e:
            # Optionally log the error
            print(f"Could not fetch IIIF info for image {instance.id}: {e}")