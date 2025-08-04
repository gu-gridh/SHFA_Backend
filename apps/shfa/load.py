#%%
from .models import *
from django.contrib.gis.geos import Point
from geography.models import *
from django.db import transaction
from django.conf import settings
#%%
import json
import os
import shutil
from tqdm import tqdm
import pandas as pd
import re
from lxml import etree
import requests
from requests.adapters import HTTPAdapter, Retry
from typing import Tuple
from PIL import Image as pillow

pillow.MAX_IMAGE_PIXELS = None

#%%
def get_or_none(classmodel: models.Model, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None
    except ValueError:
        return None
    except classmodel.MultipleObjectsReturned:
        return None

def fetch_and_parse_fornsok_xml(url: str):

    # Fetch data
    s = requests.Session()

    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[ 500, 502, 503, 504 ])

    s.mount('http://', HTTPAdapter(max_retries=retries))

    response = s.get(url)

    # Parse the XML
    return parse_fornsök_xml(response.content)


def parse_fornsök_xml(content: str):

    tree = etree.fromstring(content)
    
    # Extract the ids
    raa_id = tree.findtext(".//{http://kulturarvsdata.se/ksamsok#}number")
    ksamsok_id = tree.findtext(".//{http://kulturarvsdata.se/presentation#}id")
    lamning_id = tree.findtext(".//{http://kulturarvsdata.se/presentation#}idLabel")
    point_str  = tree.findtext(".//{http://www.opengis.net/gml}Point/{http://www.opengis.net/gml}coordinates")

    # Extract the coordinates
    if point_str:

        # And parse
        point = [float(coord) for coord in point_str.split(",")]

    else:
        point = None

    return raa_id, ksamsok_id, lamning_id, point



def parse_lamning(url: str) -> Tuple[str, str]:
    ksamsok_pattern = r"(https?:\/\/kulturarvsdata.se\/raa\/lamning\/)([A-Za-z0-9-]+)" # https://kulturarvsdata.se/raa/lamning/d7109eae-8944-486d-9f9b-b0ca7905fbbe
    ksamsok_matches = re.findall(ksamsok_pattern, url)
    
    if ksamsok_matches and len(ksamsok_matches) == 1:

        url_root = ksamsok_matches[0][0]
        id_str   = ksamsok_matches[0][1]

        return url_root + "rdf/" + id_str, id_str
        # https://kulturarvsdata.se/raa/lamning/rdf/d7109eae-8944-486d-9f9b-b0ca7905fbbe

    else:
        return None

def parse_fmi(url: str) -> Tuple[str, str]:
    
    fmi_pattern = r"(https?:\/\/kulturarvsdata.se\/raa\/fmi\/)([0-9-]+)" # https://kulturarvsdata.se/raa/fmi/lamning/10153901300001

    fmi_matches = re.findall(fmi_pattern, url)

    if fmi_matches and len(fmi_matches) == 1:

        url_root = fmi_matches[0][0]
        id_str   = fmi_matches[0][1]

        return url_root + "rdf/" + id_str, id_str

    else: 
        return None

def parse_fmi_or_lamning(url: str) -> str:

    parsed_lamning = parse_lamning(url)
    parsed_fmi = parse_fmi(url)

    if parsed_lamning:
        return parsed_lamning

    elif parsed_fmi:
        return parsed_fmi

    else:
        raise ValueError(f"No uuid in the K-SAMSÖK url: {url}")



def parse_year(year_note):

    year_pattern = r"\b[1-9]\d{3,}\b"

    matches = re.findall(year_pattern, year_note)

    if not matches:
        return None
    elif len(matches) > 1:
        return int(matches[0])
    else:
        return int(matches[0])

#%%
@transaction.atomic
def load_sites(sites_path):

    Site.objects.all().delete()

    # Load data from jsonuuid
    with open(sites_path, "r+", encoding='utf-8') as file:

        data = json.load(file)

    sites = []
    mistakes = []
    uuids = set()
    for s in tqdm(data):

        longitude = s.get('lon', None)
        latitude  = s.get('lat', None)
        
        if longitude and latitude:

            point = Point(x=float(longitude), y=float(latitude))
            try:
                lau = LocalAdministrativeUnit.objects.get(geometry__contains=point) 
            except:
                try: 
                    lau = LocalAdministrativeUnit.objects.get(geometry__bbcontains=point) 
                except:
                    mistakes.append((s['uuid'], point.x, point.y))

            raa_id = s.get('raär_id', None)
            lamning_id = s.get('lämning_id', None)
            
            site = Site(
                ksamsok_id=s['uuid'],
                raa_id=raa_id,
                lamning_id=lamning_id,
                coordinates=point,
                municipality=lau
                )

            if s['uuid'] not in uuids:

                sites.append(site)
                uuids.add(s['uuid'])
        else:
            mistakes.append((s['uuid']))

    Site.objects.bulk_create(sites)

    return sites, mistakes
        
#%%
@transaction.atomic
def load_model(path, model: models.Model, name: str, id: str):

    model.objects.all().delete()

    df = pd.read_json(path, orient='records')

    model.objects.bulk_create([model(legacy_id=row[id], name=row[name]) for idx, row in df.iterrows()])


@transaction.atomic
def load_foreign_tables(base_path: str):

    for model, name, id in tqdm([
            (Institution, "Institution", "InstitutionID"),
            (Collection, "Samling", "SamlingId"),
            (ImageTypeTag, "Typ", "TypId"),
            (DatingTag, "Datering", "DateringsId"),
            (KeywordTag, "Nyckelord", "NyckelordId")
        ]):

        model.objects.all().delete()

        # Get data path
        path = os.path.join(base_path, f"{name}.json")
        df = pd.read_json(path, orient='records')

        objs = []
        ids   = set()
        names = set()
        for idx, row in df.iterrows():
            params = {
                "legacy_id": row[id]
            }

            if row[name] not in names and row[id] not in ids:
                names.add(row[name])
                ids.add(row[name])
                
            else:
                row[name] = row[name] + "_DUPLICATE"
                names.add(row[name])
                ids.add(row[name])

            if name in ["Institution", "Samling"]:
                params.update({"name": row[name]})
            else:
                params.update({"text": row[name]})

            objs.append(model(**params))

        model.objects.bulk_create(objs)


@transaction.atomic
def load_name_tables(images_path):

    Author.objects.all().delete()
    RockCarvingObject.objects.all().delete()

    df = pd.read_json(images_path, orient='records')

    # Get all unique authors/creators
    authors = df["Fotograf"].unique()

    # Get all image types
    objs = df["Objektnamn"].unique()

    Author.objects.bulk_create([Author(name=a) for a in authors])
    RockCarvingObject.objects.bulk_create([RockCarvingObject(name=r) for r in objs])


def get_all_keywords_of_image(image_keyword_df, image_id):

    keyword_ids = image_keyword_df[image_keyword_df["BildId"] == image_id]["NyckelordId"].unique()

    keywords = [KeywordTag.objects.get(legacy_id=keyword_id) for keyword_id in keyword_ids]

    return keywords

#%%
@transaction.atomic
def delete_all():

    for model in tqdm((Image, Institution, 
                  Collection, Author, RockCarvingObject, DatingTag,
                  ImageTypeTag, KeywordTag)):

        model.objects.all().delete()

#%%
@transaction.atomic
def get_site(row) -> Site:
    """Tries to get a rock carving site based on either Lämningsnummer
    or K-Samsök.

    Args:
        row (dict): A json-like dict from the miljödata database

    Raises:
        Exception: If the Site does not exist

    Returns:
        Site: An SHFA rock carving site
    """

    lamning_id = row.get('Lämningsnummer', None)
    kms_uri = row.get('KMSUri', None)
    raa_id = row.get('Raanr', None)
    site = None

    # First check if we can get the site by lämning ID
    if (not site) and (lamning_id):

        site = get_or_none(Site, **{"lamning_id": lamning_id})

    # Check if there is a RAÄ ID being used
    if (not site) and (raa_id):

        site = get_or_none(Site, **{"raa_id": raa_id})

    # If not, check if we have the K-Samsök ID in the database
    if (not site) and (kms_uri):

        parsed = parse_lamning(kms_uri)

        if parsed:

            site = get_or_none(Site, **{"ksamsok_id": parsed[1]})

        # If it does not exist there either, fetch it from the API
        if not site or not parsed:    
  
            try:
                # Observe, old K-Samsök does not save RAÄ ID
                raa_id, ksamsok_id, lamning_id, point = parse_fornsök_xml(row["KMSPresentation"])                

                site = get_or_none(Site, **{"ksamsok_id": ksamsok_id})

                if not site:
                    site = get_or_none(Site, **{"raa_id": lamning_id})

            except etree.XMLSyntaxError as e:
                print(f"Could not parse XML. No site found. ID: {ksamsok_id}")
                return None

            if not site:
                
                if point:
                    point = Point(x=point[0], y=point[1])
                else:

                    try:
                        parsed = parse_fmi_or_lamning(kms_uri)
                        raa_id, ksamsok_id, lamning_id, point = fetch_and_parse_fornsok_xml(parsed[0])   
                    
                    except etree.XMLSyntaxError as e:
                        print(f"Could not parse fetched XML. No site found. ID: {ksamsok_id}, URI: {parsed[0]}")
                        return None
                    
                lau = get_or_none(LocalAdministrativeUnit, **{"geometry__contains": point})
                if not lau:
                    lau = get_or_none(LocalAdministrativeUnit, **{"geometry__bbcontains": point})
                

                site, _ = Site.objects.get_or_create(
                                                ksamsok_id=ksamsok_id,
                                                lamning_id=lamning_id,
                                                coordinates=point,
                                                municipality=lau)
    
    return site


@transaction.atomic
def load_images(path, keywords_path, images_root):

    # Read from JSON files
    df = pd.read_json(path, orient="records")
    image_keyword_df = pd.read_json(keywords_path, orient="records")

    # Select only the Swedish records
    df = df[df['LandId'] == 1]

    for idx, row in tqdm(df.iterrows(), total=len(df)):

        # Fetch the site
        try:
            site = get_site(row)
        except Exception as e:
            print(e)
            print(row)
            site = None
            

        # Handle properties
        collection          = get_or_none(Collection, **{"legacy_id": row['SamlingId']})
        institution         = get_or_none(Institution, **{"legacy_id": row["InstitutionId"]})
        author              = get_or_none(Author, **{"name": row["Fotograf"]})
        image_type_tag      = get_or_none(ImageTypeTag, **{"legacy_id": row['TypId']})
        rock_carving_object = get_or_none(RockCarvingObject, **{"name": row["Objektnamn"]})
        dating_tag          = get_or_none(DatingTag, **{"legacy_id": row["DateringsId"]})

        date_note           = row['Årtal']
        year                = parse_year(date_note)

        # Files must be put in the MEDIA_ROOT
        source_path = os.path.join(images_root, f"{row['BildId']}.jpg")
        filepath = os.path.join("shfa/original", f"{row['BildId']}.jpg")
        target_path = os.path.join(settings.MEDIA_ROOT, filepath)
        shutil.copyfile(source_path, target_path)
        

        image = Image(
            legacy_id = row['BildId'],
            file = filepath,
            site = site,
            collection = collection,
            institution = institution,
            author = author,
            type = image_type_tag,
            year = year,
            date_note = date_note,
            rock_carving_object=rock_carving_object
        )

        image.save()

        # Now get all the keywords
        keywords = get_all_keywords_of_image(image_keyword_df, row['BildId'])
        image.keywords.add(*keywords)
        if dating_tag:
            image.dating_tags.add(dating_tag)
