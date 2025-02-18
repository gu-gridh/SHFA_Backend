#%%
from .models import *

#%%
from ast import Mult
import os
import json
import pandas as pd
from tqdm import tqdm
from django.contrib.gis.db import models
from django.contrib.gis.geos import MultiPolygon, GEOSGeometry
from typing import *

#%%
COUNTRIES = ["SE", "NO", "DK", "ES", "IT", "FI"]

#%%
def pretty_save_geojson(path: str) -> None:
    """Saves a geojson file in a prettier, indented format.

    Args:
        path (str): Absolute path of the geojson file
    """

    with open(path, "r") as file:
        geojson = json.load(file)

    splits = path.split(".")

    if len(splits) > 2:
        raise ValueError("Make sure the path is absolute.")

    new_path = splits[0] + "_pretty.geojson"

    with open(new_path, "w") as file:
        json.dump(geojson, file, indent=4)



def geojson_to_dataframe(path: str) -> pd.DataFrame:
    """Reads a geojson file from a file and converts it into
    a pandas DataFrame with geometry and properties as columns.

    Args:
        path (str): Path of the geojson file

    Returns:
        pd.DataFrame: A pandas DataFrame
    """

    with open(path, "r") as file:
        geojson = json.load(file)

    df = pd.DataFrame.from_records([
        {
            "feature": {"type": feature["type"], "geometry": feature["geometry"]},
            **feature["properties"]
        }

        for feature in geojson['features']
    ])

    return df


def get_superregion_code(subregion_code: str):

    return subregion_code[:-1]

def lau_to_nuts3(path: str, country_code: str) -> Dict[str, str]:
    """Creates a mapping dict between LAUs and their corresponding many-to-one NUTS3
    regions.

    Args:
        path (str): The path to a Eurostat/GISCO correspondence Excel workbook
        country_codes (_type_, optional): The countries relevant for upload. Defaults to COUNTRIES.

    Returns:
        Dict[str, str]: A dictionary mapping LAUs to a NUTS3.
    """

    df = pd.read_excel(path, sheet_name=country_code, dtype={"LAU CODE": "string", "NUTS 3 CODE": "string"})
    df = df.replace({"NO061": "NO060", "NO062": "NO060"})

    return {
        str(row["LAU CODE"]) : str(row["NUTS 3 CODE"])
        for idx, row in df.iterrows()
    }

def geojson_to_multipolygon(geojson: str) -> MultiPolygon:
    """Converts geojson data with polygons to multipolygons.

    Args:
        geojson (str): A geojson string.

    Returns:
        MultiPolygon: A Django MultiPolygon object.
    """

    geom = GEOSGeometry(geojson)

    if geom.geom_type == "Polygon":
        geometry = MultiPolygon(geom)
    else:
        geometry = geom

    return geometry

def nuts(path: str, year: int, country_codes=COUNTRIES) -> None:
    """Loads the national units for territorial statistics, NUTS, to the database. 

    Args:
        path (str): The path to a Eurostat/GISCO geojson datafile
        year (int): The version year for the data
        country_codes (_type_, optional): The countries relevant for upload. Defaults to COUNTRIES.
    """

    level_map = {
        0: Country,
        1: NUTS1,
        2: NUTS2,
        3: NUTS3
    }

    # Read the geojson to a dataframe
    df = geojson_to_dataframe(path)
    df = df[df["CNTR_CODE"].isin(country_codes)]

    # Set multiindex and sort
    df = df.set_index(["LEVL_CODE", "NUTS_ID"]).sort_index()

    for ((level, nuts_code), row) in tqdm(df.iterrows(), total=len(df)):

        # Get the correct current model
        model = level_map[level]

        # Get all the params
        params = {
                "name": row["NUTS_NAME"],
                "code": nuts_code,
                "year": year,
                "geometry": geojson_to_multipolygon(str(row["feature"]["geometry"])),
        }

        # If the region is not a country, it has a superregion
        if level != 0:
            # The superregion should already exist
            try:
                superregion_code = get_superregion_code(nuts_code)
                superregion = level_map[level-1].objects.get(code=superregion_code)

                params["superregion"] = superregion
            except Exception as e:
                print(e, nuts_code, superregion, superregion_code)
                raise ValueError()

        
        # Create the model object. Since there is a hierarchical dependency
        # they must be created on the database immediately
        model.objects.create(**params)


def lau(path: str, correspondence_path: str, year: int, country_codes=COUNTRIES) -> None:
    """Loads the local administrative units, LAU, to the database. Requires that NUTS have already
    been added to the database.

    Args:
        path (str): The path to a Eurostat/GISCO geojson datafile
        correspondence_path (str): The path to a Eurostat/GISCO correspondence Excel workbook
        year (int): The version year for the data
        country_codes (_type_, optional): The countries relevant for upload. Defaults to COUNTRIES.
    """


    # Read the geojson to a dataframe
    data = geojson_to_dataframe(path)

    # Get the correct current model
    model = LocalAdministrativeUnit
    for country_code in country_codes:
        
        # Read the correct country
        df = data[data["CNTR_CODE"] == country_code]
        lau_to_nuts3_map = lau_to_nuts3(correspondence_path, country_code)

        for (idx, row) in tqdm(df.iterrows(), total=len(df)):

            try:
                nuts3 = NUTS3.objects.get(code=lau_to_nuts3_map[row["LAU_ID"]])
            except:
                print(row["LAU_ID"], lau_to_nuts3_map[row["LAU_ID"]])
            # Get all the params
            params = {
                    "name": row["LAU_NAME"],
                    "code": row["LAU_ID"],
                    "year": year,
                    "geometry": geojson_to_multipolygon(str(row["feature"]["geometry"])),
                    "superregion": nuts3
            }

            # Create the model object. Since there is a hierarchical dependency
            # they must be created on the database immediately
            model.objects.create(**params)


#%%
def load(lau_path, nuts_path, correspondence_path, lau_year, nuts_year):

    Country.objects.all().delete()
    
    nuts(nuts_path, nuts_year)
    lau(lau_path, correspondence_path, lau_year)


