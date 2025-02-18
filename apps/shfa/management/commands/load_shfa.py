from django.core.management.base import BaseCommand
from shfa.load import load_sites, load_images, load_foreign_tables, load_name_tables, delete_all
import os

class Command(BaseCommand):

    def add_arguments(self, parser):
        
        parser.add_argument("-s", "--sites", type=str)
        parser.add_argument("-b", "--root", type=str)

    def handle(self, **options):

        image_path = os.path.join(options["root"], "Bild.json")
        images_root = os.path.join(options["root"], "Bilder")
        image_keyword_path = os.path.join(options["root"], "BildNyckelord.json")
        sites_path = os.path.join(options["sites"])

        delete_all()
        if sites_path:
            load_sites(sites_path)
            
        load_name_tables(image_path)
        load_foreign_tables(options["root"])
        load_images(image_path, image_keyword_path, images_root)

