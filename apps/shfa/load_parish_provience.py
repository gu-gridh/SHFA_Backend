from .models import *
from django.db.models import Q
from django.contrib.gis.geos import GEOSGeometry
import geography.models as geography
import geojson

parish_country = geography.Country.objects.get(name='SVERIGE')

def socken_model(socken_file):
    with open(socken_file) as file:
        input = geojson.load(file)
        sockson_info = input['features']

        for features in sockson_info:
            # Parish features
            # parish_id = features['id']
            # parish_id = features['properties']['OBJECTID']
            parish_id = features['properties']['sockenstadkod']
            geom = features['geometry']
            if geom['type'] == 'Polygon':
                geom['type'] = 'MultiPolygon'
                geom['coordinates'] = [features['geometry']['coordinates']]

            paris_name = features['properties']['sockenstadnamn']
            parish_code = features['properties']['sockenstadkod']
            # year = features['properties']['version_giltig_fran']
            
            parish,_ = geography.Parish.objects.update_or_create(
            id = parish_id,
            code = parish_code,
            defaults={       
                    'geometry': GEOSGeometry(str(geom)),
                    'name': paris_name,
                    # 'code': parish_code,
                    'country': parish_country
                }
            )
            parish.save()
        file.close()
    # 

def lan_model(lan_file):

    with open(lan_file) as file:
        input = geojson.load(file)
        lan_info = input['features']

        for features in lan_info:
            # lan_id = features['id']
            # lan_id = features['properties']['FID']
            lan_id = features['properties']['LANSKOD']
            lan_name = features['properties']['LANSNAMN']
            # lan_code = features['properties']['KKOD']
            lan_code = features['properties']['LANSKOD']

            geom = features['geometry']
            if geom['type'] == 'Polygon':
                geom['type'] = 'MultiPolygon'
                geom['coordinates'] = [features['geometry']['coordinates']]

            province,_ = geography.Province.objects.update_or_create(
            id = lan_id,
            defaults={       
                    'geometry': GEOSGeometry(str(geom)),
                    'name': lan_name,
                    'code': lan_code,
                    'country': parish_country
                }
            )
            province.save()
        file.close()


def update_parish_province(site_file):
    with open(site_file) as file:
        input = geojson.load(file)
        lan_info = input['features']

        for features in lan_info:

            land_id = features['properties']['LänId']
            socken_id = features['properties']['Sockenkod']
            if land_id:
                try:
                    province = geography.Province.objects.get(id=land_id)
                except :
                    province = geography.Province.objects.update_or_create(
                        id = features['properties']['LänId'],
                        name = features['properties']['Län'],
                        code = features['properties']['LänskodKsamsök'],
                        country = parish_country
                    )

            if socken_id:
                try:    
                    parish = geography.Parish.objects.get(id=socken_id)
                except:
                    parish = geography.Parish.objects.update_or_create(
                        id = features['properties']['Sockenkod'],
                        name = features['properties']['Län'],
                        code = features['properties']['Sockenkod'],
                        country = parish_country
                    )



def update_site(site_file):
    with open(site_file) as file:
        input = geojson.load(file)
        lan_info = input['features']

        for features in lan_info:
            #Site unique info
            lamn_id = features['properties']['lamningsnr']
            land_id = features['properties']['LänId']
            socken_id = features['properties']['Sockenkod']

            if land_id:
                province = geography.Province.objects.get(id=land_id)
                parish = geography.Parish.objects.get(id=socken_id)
                site = Site.objects.filter(lamning_id=lamn_id).update(
                                                parish= parish,
                                                province= province)
            
            
