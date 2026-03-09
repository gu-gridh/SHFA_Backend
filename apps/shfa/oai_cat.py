from django.shortcuts import render
from . import models
from django.utils import timezone
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage

NUM_PER_PAGE = 25


def get_records(params, request):
    template_ksmsak = "../templates/bild.template.xml"
    template_ariande = "../templates/records_ariadne.xml"
    template_3d_ksmsak = "../templates/3d.template.xml"
    template_3d_ariande = "../templates/records_3d_ariadne.xml"
    error_template = "../templates/error.xml"
    errors = []
    record_type = "image"  # default record type
    
    if "metadataPrefix" in params:
        metadata_prefix = params.pop("metadataPrefix")
        if len(metadata_prefix) == 1:
            metadata_prefix = metadata_prefix[0]
            if not models.MetadataFormat.objects.filter(
                prefix=metadata_prefix
            ).exists():
                errors.append(_error(
                    "cannotDisseminateFormat", metadata_prefix))
               
            if "identifier" in params:
                identifier = params.pop("identifier")[-1]
                # Check if identifier indicates a 3D model (prefix "3d:")
                if identifier.startswith("3d:"):
                    record_type = "3d"
                    record_id = identifier[3:]
                    try:
                        output = models.SHFA3D.objects.get(id=record_id)
                    except models.SHFA3D.DoesNotExist:
                        errors.append(_error(
                            "idDoesNotExist", identifier))
                else:
                    try:
                        output = models.Image.objects.get(id=identifier)
                    except models.Image.DoesNotExist:
                        errors.append(_error(
                            "idDoesNotExist", identifier))
            else:
                errors.append(_error(
                    "badArgument", "identifier"))
        else:

            errors.append(_error(
                "badArgument_single", ";".join(metadata_prefix)))
            metadata_prefix = None
    else:
        errors.append(_error("badArgument", "metadataPrefix"))

    _check_bad_arguments(errors, params)

    if errors:
        xml_output = render(
            request,
            template_name=error_template,
            context={'errors': errors},
            content_type='text/xml'
        )
    else:
        if record_type == "3d":
            if metadata_prefix == "ksamsok-rdf":
                template = template_3d_ksmsak
            elif metadata_prefix == "ariadne-rdf":
                template = template_3d_ariande
            else:
                template = template_3d_ksmsak
        else:
            if metadata_prefix == "ksamsok-rdf":
                template = template_ksmsak
            elif metadata_prefix == "ariadne-rdf":
                template = template_ariande
            else:
                template = template_ksmsak

        xml_output = render(
            request,
            template_name=template,
            context={'data': output},
            content_type="text/xml"
        )
    return xml_output


def get_identify(request):
    template = "../templates/identify.xml"
    identify_output = render(
        request,
        template_name=template,
        # context= {
        #     'error':error_xml
        #     },
        content_type="text/xml")
    return identify_output


def get_list_records(verb, request, params):
    template_ksamsok = "../templates/listrecords.xml"
    template_ariande = "../templates/listrecords_ariadne.xml"
    template_3d_ksamsok = "../templates/listrecords_3d.xml"
    template_3d_ariande = "../templates/listrecords_3d_ariadne.xml"
    template_images_ksamsok = "../templates/listrecords_images.xml"
    template_images_ariande = "../templates/listrecords_images_ariadne.xml"
    error_template = "../templates/error.xml"
    errors = []

    paginator_records = None
    records = None
    resumption_token = None
    metadata_prefix = None
    from_timestamp = None
    until_timestamp = None
    set_spec = None

    # Extract set parameter if present
    if "set" in params:
        set_spec = params.pop("set")[-1]
        if set_spec not in ("shfa:images", "shfa:models"):
            errors.append(_error("noSetHierarchy"))

    images = None
    models_3d = None
    paginator_images = None
    paginator_3d = None

    if "resumptionToken" in params:
        (
            paginator_records,
            records,
            resumption_token,
            metadata_prefix,
            from_timestamp,
            until_timestamp,
        ) = _do_resumption_token(params, errors, set_spec=set_spec)
        # Map records to the right variable based on set
        if set_spec == "shfa:models":
            models_3d = records
            paginator_3d = paginator_records
        elif set_spec == "shfa:images":
            images = records
            paginator_images = paginator_records
        else:
            # No set: resumption currently only paginates images
            images = records
            paginator_images = paginator_records

    elif "metadataPrefix" in params:
        metadata_prefix = params.pop("metadataPrefix")
        if len(metadata_prefix) == 1:
            metadata_prefix = metadata_prefix[0]
            if not models.MetadataFormat.objects.filter(prefix=metadata_prefix).exists():
                errors.append(_error("cannotDisseminateFormat", metadata_prefix))
            else:
                from_timestamp, until_timestamp = _check_timestamps(errors, params)

                if set_spec == "shfa:models":
                    # Only 3D models
                    records_3d = models.SHFA3D.objects.all()
                    if from_timestamp:
                        records_3d = records_3d.filter(created_at__gte=from_timestamp)
                    if until_timestamp:
                        records_3d = records_3d.filter(updated_at__lte=until_timestamp)
                    paginator_3d = Paginator(records_3d, NUM_PER_PAGE)
                    models_3d = paginator_3d.page(1)
                elif set_spec == "shfa:images":
                    # Only images
                    images_data = models.Image.objects.all()
                    if from_timestamp:
                        images_data = images_data.filter(created_at__gte=from_timestamp)
                    if until_timestamp:
                        images_data = images_data.filter(updated_at__lte=until_timestamp)
                    paginator_images = Paginator(images_data, NUM_PER_PAGE)
                    images = paginator_images.page(1)
                else:
                    # No set specified: return both images and 3D models
                    images_data = models.Image.objects.all()
                    records_3d = models.SHFA3D.objects.all()
                    if from_timestamp:
                        images_data = images_data.filter(created_at__gte=from_timestamp)
                        records_3d = records_3d.filter(created_at__gte=from_timestamp)
                    if until_timestamp:
                        images_data = images_data.filter(updated_at__lte=until_timestamp)
                        records_3d = records_3d.filter(updated_at__lte=until_timestamp)
                    paginator_images = Paginator(images_data, NUM_PER_PAGE)
                    images = paginator_images.page(1)
                    # 3D models are not paginated separately in combined mode;
                    # they are included alongside images in the same response
                    models_3d = records_3d
        else:
            errors.append(_error("badArgument_single", ";".join(metadata_prefix)))
            metadata_prefix = None
    else:
        errors.append(_error("badArgument", "metadataPrefix"))

    if errors:
        return render(
            request,
            template_name=error_template,
            context={"errors": errors},
            content_type="text/xml",
        )

    # Select template based on set and metadata prefix
    # set=shfa:models      -> dedicated 3D-only templates
    # set=shfa:images   -> dedicated image-only templates
    # no set            -> combined templates (images + 3D section)
    if set_spec == "shfa:models":
        if metadata_prefix == "ksamsok-rdf":
            template = template_3d_ksamsok
        elif metadata_prefix in ("shfa-gen-rdf", "ariadne-rdf"):
            template = template_3d_ariande
        else:
            template = template_3d_ksamsok
    elif set_spec == "shfa:images":
        if metadata_prefix == "ksamsok-rdf":
            template = template_images_ksamsok
        elif metadata_prefix in ("shfa-gen-rdf", "ariadne-rdf"):
            template = template_images_ariande
        else:
            template = template_images_ksamsok
    else:
        if metadata_prefix == "ksamsok-rdf":
            template = template_ksamsok
        elif metadata_prefix in ("shfa-gen-rdf", "ariadne-rdf"):
            template = template_ariande
        else:
            template = template_ksamsok

    # Use the images paginator for resumption token in combined/images mode
    paginator = paginator_3d if set_spec == "shfa:models" else paginator_images

    return render(
        request,
        template_name=template,
        context={
            "images": images,
            "models_3d": models_3d,
            "paginator": paginator,
            "resumption_token": resumption_token,
            "metadata_prefix": metadata_prefix,
            "from_timestamp": from_timestamp,
            "until_timestamp": until_timestamp,
            "set_spec": set_spec,
        },
        content_type="text/xml",
    )



def get_list_metadata(request, params):
    template = '../templates/listmetadataformats.xml'
    error_template = "../templates/error.xml"
    errors = []

    metadataformats = models.MetadataFormat.objects.all()
    if "identifier" in params:
        identifier = params.pop("identifier")[-1]
        # Check both Image and SHFA3D models for the identifier
        if identifier.startswith("3d:"):
            record_id = identifier[3:]
            if models.SHFA3D.objects.filter(id=record_id).exists():
                metadataformats = models.MetadataFormat.objects.filter(prefix='ksamsok-rdf')
            else:
                errors.append(_error("idDoesNotExist", identifier))
        else:
            if models.Image.objects.filter(identifier=identifier).exists():
                metadataformats = models.MetadataFormat.objects.filter(prefix='ksamsok-rdf')
            elif models.SHFA3D.objects.filter(id=identifier).exists():
                metadataformats = models.MetadataFormat.objects.filter(prefix='ksamsok-rdf')
            else:
                errors.append(_error("idDoesNotExist", identifier))
    if metadataformats.count() == 0:
        errors.append(_error("noMetadataFormats"))

    if errors:
        xml_output = render(
            request,
            template_name=error_template,
            context={'errors': errors},
            content_type='text/xml'
        )
    else:
        xml_output = render(
            request,
            template if not errors else errors,
            context={'metadataformats': metadataformats},
            content_type="text/xml",
        )
    return xml_output

def get_list_set(request, params):
    template = "../templates/listsets.xml"
    error_template = "../templates/error.xml"
    errors = []

    # OAI-PMH specification: ListSets may use resumptionToken, but no other params are allowed if it is present
    if "resumptionToken" in params:
        resumption_token = params.pop("resumptionToken")[-1]
        # You would need to implement logic for paginated set listing via resumption token
        errors.append(_error("noSetHierarchy"))  # Placeholder for your use case
    else:
        # No resumptionToken, regular set listing
        if not models.Set.objects.exists():
            errors.append(_error("noSetHierarchy"))
        else:
            sets = models.Set.objects.all()
            paginator = Paginator(sets, NUM_PER_PAGE)
            page_number = int(params.get("page", ["1"])[-1])  # Support page param if desired
            try:
                sets_page = paginator.page(page_number)
            except EmptyPage:
                sets_page = paginator.page(paginator.num_pages)

    _check_bad_arguments(errors, params)

    if errors:
        return render(
            request,
            template_name=error_template,
            context={"errors": errors},
            content_type="text/xml",
        )

    return render(
        request,
        template_name=template,
        context={
            "sets": sets_page,
            "paginator": paginator,
            "page_number": page_number,
        },
        content_type="text/xml",
    )


def _do_resumption_token(params, errors, set_spec=None):
    metadata_prefix = None
    from_timestamp = None
    until_timestamp = None
    resumption_token = None

    # Select the appropriate model based on the set parameter
    if set_spec == "shfa:models":
        data_model = models.SHFA3D.objects
    else:
        data_model = models.Image.objects

    if "resumptionToken" in params:
        resumption_token = params.pop("resumptionToken")[-1]
        try:
            rt = models.ResumptionToken.objects.get(token=resumption_token)
            if timezone.now() > rt.expiration_date:
                errors.append(_error(
                    "badResumptionToken_expired.", resumption_token))
            else:
                records_data = data_model
                if from_timestamp is not None:
                    records_data = records_data.filter(created_at__gte=from_timestamp)
                if until_timestamp is not None:
                    records_data = records_data.filter(updated_at__gte=until_timestamp)

                try:
                    paginator = Paginator(records_data.all(), NUM_PER_PAGE)
                    records = paginator.page(rt.cursor / NUM_PER_PAGE + 1)

                except EmptyPage:
                    errors.append(_error(
                        "badResumptionToken", resumption_token))

        except models.ResumptionToken.DoesNotExist:
            records_data = data_model
            paginator = Paginator(records_data, NUM_PER_PAGE)
            records = paginator.page(1)
            errors.append(_error(
                "badResumptionToken", resumption_token))

        # check_bad_arguments(
        #     params,
        #     errors,
        #     msg="The usage of resumptionToken allows no other arguments.",
        # )
    else:
        records_data = data_model
        paginator = Paginator(records_data, NUM_PER_PAGE)
        records = paginator.page(1)
        

    return (
        paginator,
        records,
        resumption_token,
        metadata_prefix,
        from_timestamp,
        until_timestamp,
    )


def _check_timestamps(errors, params):
    from_timestamp = None
    until_timestamp = None
    granularity = None

    if "from" in params:
        f = params.pop("from")[-1]
        granularity = "%Y-%m-%dT%H:%M:%SZ %z" if "T" in f else "%Y-%m-%d %z"
        try:
            from_timestamp = datetime.strptime(f + " +0000", granularity)
        except Exception:
            errors.append(_error("badArgument_valid", f, "from"))

    if "until" in params:
        u = params.pop("until")[-1]
        ugranularity = "%Y-%m-%dT%H:%M:%SZ %z" if "T" in u else "%Y-%m-%d %z"
        if ugranularity == granularity or not granularity:
            try:
                until_timestamp = datetime.strptime(u + " +0000", granularity)
            except Exception:
                errors.append(_error(
                    "badArgument_valid", u, "until"))
        else:
            errors.append(_error("badArgument_granularity"))
    return from_timestamp, until_timestamp


def _check_bad_arguments(errors, params, msg=None):
    for k, v in params.copy().items():
        errors.append(_error(
            {
                "code": "badArgument",
                "msg": f'The argument "{k}" (value="{v}") included in the request is '
                + "not valid."
                + (f" {msg}" if msg else ""),
            }
        ))
        params.pop(k)


def verb_error(request):
    error_template = "../templates/error.xml"
    errors = []
    
    errors.append(_error("badVerb"))
    xml_output = render(
        request,
        template_name=error_template,
        context={'errors': errors},
        content_type='text/xml'
        )
    return xml_output

def _error(code, *args):
    if code == "badArgument":
        return {
            "code": "badArgument",
            "msg": f'The required argument "{args[0]}" is missing in the request.',
        }
    elif code == "badArgument_granularity":
        return {
            "code": "badArgument",
            "msg": 'The granularity of the arguments "from" and "until" do not match.',
        }
    elif code == "badArgument_single":
        return {
            "code": "badArgument",
            "msg": "Only a single metadataPrefix argument is allowed, got "
            + f'"{args[0]}".',
        }
    elif code == "badArgument_valid":
        return {
            "code": "badArgument",
            "msg": f'The value "{args[0]}" of the argument "{args[1]}" is not valid.',
        }
    elif code == "badResumptionToken":
        return {
            "code": "badResumptionToken",
            "msg": f'The resumptionToken "{args[0]}" is invalid.',
        }
    elif code == "badResumptionToken_expired":
        return {
            "code": "badResumptionToken",
            "msg": f'The resumptionToken "{args[0]}" is expired.',
        }
    elif code == "badVerb" and len(args) == 0:
        return {"code": "badVerb", "msg": "The request does not provide any verb."}
    elif code == "badVerb":
        return {
            "code": "badVerb",
            "msg": f'The verb "{args[0]}" provided in the request is illegal.',
        }
    elif code == "cannotDisseminateFormat":
        return {
            "code": "cannotDisseminateFormat",
            "msg": f'The value of the metadataPrefix argument "{args[0]}" is not '
            + " supported.",
        }
    elif code == "idDoesNotExist":
        return {
            "code": "idDoesNotExist",
            "msg": f'A record with the identifier "{args[0]}" does not exist.',
        }
    elif code == "noMetadataFormats" and len(args) == 0:
        return {
            "code": "noMetadataFormats",
            "msg": "There are no metadata formats available.",
        }
    elif code == "noMetadataFormats":
        return {
            "code": "noMetadataFormats",
            "msg": "There are no metadata formats available for the record with "
            + f'identifier "{args[0]}".',
        }
    elif code == "noRecordsMatch":
        return {
            "code": "noRecordsMatch",
            "msg": "The combination of the values of the from, until, and set "
            + "arguments results in an empty list.",
        }
    elif code == "noSetHierarchy":
        return {
            "code": "noSetHierarchy",
            "msg": "This repository does not support sets.",
        }

