from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import ResumptionToken


@receiver(pre_save, sender=ResumptionToken)
def delete_old_resumption_tokens(sender, **kwargs):
    """Delete expired resumption tokens."""
    ResumptionToken.objects.filter(expiration_date__lte=timezone.now()).delete()
