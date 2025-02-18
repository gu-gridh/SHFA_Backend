# -*- coding: utf-8 -*-
# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:
#
# This file is part of django_oai_pmh.
#
# django_oai_pmh is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# django_oai_pmh is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with django_oai_pmh. If not, see <http://www.gnu.org/licenses/>.
"""OAI-PMH Django app oai_pmh templatetag."""

from django.conf import settings
from django.template import Library
from django.utils import timezone
from django.utils.safestring import mark_safe
from ..models import MetadataFormat, ResumptionToken

from html import escape
from os import urandom
register = Library()

REPOSITORY_NAME = "SHFA"
BASE_URL="https://shfa.dh.gu.se/"

@register.simple_tag
def base_url():
    """Get OAI-PMH base url."""
    return mark_safe(BASE_URL)


@register.simple_tag
def list_request_attributes(
    verb=None,
    identifier=None,
    metadata_prefix=None,
    from_timestamp=None,
    until_timestamp=None,
    resumption_token=None,
):
    """List requested attributes."""
    timestamp_format = "%Y-%m-%dT%H:%M:%SZ"
    verbs = [
        "Identify",
        "ListMetadataFormats",
        "GetRecord",
        "ListIdentifiers",
        "ListRecords",
    ]

    attributes = "" 
    if verb in verbs:
        attributes = f'verb="{verb}"'
    if identifier:
        attributes += f' identifier="{escape(identifier)}"'
    if metadata_prefix:
        attributes += f' metadataPrefix="{escape(metadata_prefix)}"'
    if from_timestamp:
        attributes += f' from="{from_timestamp.strftime(timestamp_format)}"'
    if until_timestamp:
        attributes += f' until="{until_timestamp.strftime(timestamp_format)}"'
    if resumption_token:
        attributes += f' resumptionToken="{escape(resumption_token)}"'
    return mark_safe(attributes)


@register.simple_tag
def get_image_tags(image):
    tags = [keyword.text for keyword in image.keywords.all()]
    return ", ".join(tags)

@register.simple_tag
def resumption_token(
    paginator,
    page,
    metadata_prefix=None,
    from_timestamp=None,
    until_timestamp=None,
):
    """Get resumption token."""
    if paginator.num_pages > 0 and page.has_next():
        expiration_date = timezone.now() + timezone.timedelta(days=1)
        token = "".join("%02x" % i for i in urandom(16))

        metadata_format = None
        if metadata_prefix:
            metadata_format = MetadataFormat.objects.get(prefix=metadata_prefix)

        ResumptionToken.objects.create(
            token=token,
            expiration_date=expiration_date,
            complete_list_size=paginator.count,
            cursor=page.end_index(),
            metadata_prefix=metadata_format,
            from_timestamp=from_timestamp,
            until_timestamp=until_timestamp,
        )

        return mark_safe(
            "<resumptionToken expirationDate="
            f"\"{expiration_date.strftime('%Y-%m-%dT%H:%M:%SZ')}\" "
            f'completeListSize="{paginator.count}" cursor="{page.end_index()}">'
            f"{token}</resumptionToken>"
        )
    else:
        return ""
