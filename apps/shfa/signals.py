from django.db.models.signals import pre_save, post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from .models import ResumptionToken, Image
from PIL import Image as PILImage

import requests


@receiver(pre_save, sender=ResumptionToken)
def delete_old_resumption_tokens(sender, **kwargs):
    """Delete expired resumption tokens."""
    ResumptionToken.objects.filter(expiration_date__lte=timezone.now()).delete()


@receiver(pre_save, sender=Image)
def cache_previous_image_file(sender, instance, **kwargs):
    """Remember the existing file name so post-save can detect replacements."""
    if instance.pk:
        instance._previous_file_name = (
            sender.objects.filter(pk=instance.pk)
            .values_list('file', flat=True)
            .first()
        )
    else:
        instance._previous_file_name = None


def _get_image_dimensions(instance):
    """Read dimensions from the uploaded file, with an IIIF fallback."""
    file_name = getattr(instance.file, 'name', None)
    if file_name:
        try:
            with instance.file.storage.open(file_name, 'rb') as image_file:
                with PILImage.open(image_file) as image_object:
                    return image_object.size
        except Exception:
            pass

    base_url = "https://img.dh.gu.se/shfa/static/"
    iiif_file_url = getattr(instance.iiif_file, 'url', None)
    if not iiif_file_url:
        return None, None
    if not iiif_file_url.startswith("http"):
        iiif_file_url = base_url + iiif_file_url.lstrip("/")
    info_url = f"{iiif_file_url}/info.json"
    try:
        response = requests.get(info_url, timeout=5)
        if response.status_code == 200:
            info = response.json()
            return info.get("width"), info.get("height")
    except Exception as e:
        print(f"Could not fetch IIIF info for image {instance.id}: {e}")

    return None, None


@receiver(post_save, sender=Image)
def update_image_dimensions(sender, instance, created, **kwargs):
    """Refresh width and height when a file is uploaded or dimensions are missing."""

    previous_file_name = getattr(instance, '_previous_file_name', None)
    file_changed = created or previous_file_name != instance.file.name
    needs_dimensions = instance.width is None or instance.height is None

    if not (file_changed or needs_dimensions):
        return

    width, height = _get_image_dimensions(instance)
    if width and height:
        def update_dimensions():
            Image.objects.filter(pk=instance.pk).update(width=width, height=height)

        transaction.on_commit(update_dimensions)


    if file_changed and previous_file_name and previous_file_name != instance.file.name:
        def delete_previous_file():
            try:
                instance.file.storage.delete(previous_file_name)
            except Exception as e:
                print(f"Could not delete old image file for image {instance.id}: {e}")

        transaction.on_commit(delete_previous_file)