from tabnanny import verbose
import shfa.abstract.models as abstract
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models
import apps.geography.models as geography
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
# from django.contrib.postgres.fields import ArrayField
from django_better_admin_arrayfield.models.fields import ArrayField

# Validators
raa_validator = RegexValidator(r"([A-Za-z]+)( )(\d+:?\d+?)")
lamning_validator = RegexValidator(r"(L\d+)(:)(\d+)")

############ TAGS #####################
# class CarvingTag(abstract.AbstractTagModel):
#     # A tag model, of which a site can have many
#     # tags, and tags can be used on many sites
#     # Observe: Simple listing of occurences, not enumeration of all figures
#     pass

#     legacy_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name=_("legacy id"))
#     english_translation = models.CharField(max_length=5000, null=True, blank=True, verbose_name=_('translation'), help_text=("English translation for tag"))

#     class Meta:
#         verbose_name = _("Type of carving")
#         verbose_name_plural = _("Types of carving")

#     def __str__(self) -> str:
#         return self.text

#     def __repr__(self) -> str:
#         return str(self)


class KeywordTag(abstract.AbstractTagModel):
    # Keywords relating to the image
    pass

    legacy_id = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name=_("legacy id"))
    english_translation = models.CharField(max_length=5000, null=True, blank=True, verbose_name=_(
        'translation'), help_text=("English translation for keyword"))
    category = models.CharField(max_length=128, null=True, blank=True, verbose_name=_(
        "Category"), help_text=_("Category of the keyword, e.g. 'Djurfigur', 'Skeppfigur', etc."))
    category_translation = models.CharField(max_length=128, null=True, blank=True, verbose_name=_("Category translation"), help_text=_(
        "English translation of the category of the keyword, e.g. 'Animal figure', 'Ship figure', etc."))

    class Meta:
        verbose_name = _("Image keyword")
        verbose_name_plural = _("Image keywords")

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return str(self)


class DatingTag(abstract.AbstractTagModel):
    # A tag model, of which a site can have many
    # tags, and tags can be used on many sites
    # Motivation: Sites can contain figures with different dating

    legacy_id = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name=_("legacy id"))
    abbreviation = models.CharField(max_length=32, verbose_name=_(
        "Abbreviation"), help_text=_("Common abbreviation of the dating estimation."))
    certainty = models.CharField(max_length=64, null=True, blank=True, verbose_name=_(
        "Certainty of dating"), help_text=_("A free-form description of the certainty of the dating."))
    english_translation = models.CharField(max_length=5000, null=True, blank=True, verbose_name=_(
        'translation'), help_text=("English translation for tag"))

    class Meta:
        verbose_name = _("Dating")
        verbose_name_plural = _("Datings")

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return str(self)


class ImageTypeTag(abstract.AbstractTagModel):

    legacy_id = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name=_("legacy id"))
    order = models.IntegerField(null=True, blank=True, verbose_name=_(
        "orders"), help_text=_("Types order"))
    english_translation = models.CharField(max_length=5000, null=True, blank=True, verbose_name=_(
        'translation'), help_text=("English translation for tag"))

    class Meta:
        verbose_name = _("Image Type")
        verbose_name_plural = _("Image Types")

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return str(self)


class MethodTag(abstract.AbstractTagModel):
    english_translation = models.CharField(max_length=500, blank=True, verbose_name=_(
        'translation'), help_text=("English translation for tag"))

    class Meta:
        verbose_name = _("Data Collection Method")
        verbose_name_plural = _("Data Collection Methods")

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return str(self)


class WeatherTag(abstract.AbstractTagModel):
    # Keywords relating to the image
    pass

    english_translation = models.CharField(max_length=5000, null=True, blank=True, verbose_name=_(
        'translation'), help_text=("English translation for keyword"))

    class Meta:
        verbose_name = _("Weather")
        verbose_name_plural = _("Weather Conditions")

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return str(self)

####################################


class Collection(abstract.AbstractBaseModel):

    name = models.CharField(max_length=128, unique=True, verbose_name=_(
        "name"), help_text=_("Name of the image collection"))
    legacy_id = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name=_("legacy id"))

    class Meta:
        verbose_name = _("Collection")
        verbose_name_plural = _("Collections")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


class Author(abstract.AbstractBaseModel):
    # A photographer, or owner,
    # can be a person or institution

    name = models.CharField(max_length=256, unique=True, verbose_name=_(
        "name"), help_text=_("Free-form name of the creator, photographer or author."))
    legacy_id = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name=_("legacy id"))
    english_translation = models.CharField(max_length=5000, null=True, blank=True, verbose_name=_(
        'translation'), help_text=("English translation for the author"))

    class Meta:
        verbose_name = _("Creator")
        verbose_name_plural = _("Creators")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


class People(abstract.AbstractBaseModel):
    # A photographer, or owner,
    # can be a person or institution

    name = models.CharField(max_length=256, unique=True, verbose_name=_(
        "name"), help_text=_("Free-form name of the creator, photographer or author."))
    legacy_id = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name=_("legacy id"))
    english_translation = models.CharField(max_length=5000, null=True, blank=True, verbose_name=_(
        'translation'), help_text=("English translation for the author"))

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("People")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self.name)


class Institution(abstract.AbstractBaseModel):

    legacy_id = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name=_("legacy id"))

    name = models.CharField(max_length=512, unique=True, verbose_name=_(
        "name"), help_text=_("Name of the institution"))
    address = models.TextField(null=True, blank=True, verbose_name=_(
        "address"), help_text=_("Physical address details, if applicable."))
    url = models.URLField(max_length=512, null=True, blank=True, verbose_name=_(
        "url"), help_text=_("URL or website address to the institution, if applicable."))
    email = models.EmailField(max_length=512, null=True, blank=True, verbose_name=_(
        "email"), help_text=_("E-mail address of the institution, if applicable."))

    class Meta:
        verbose_name = _("Institution")
        verbose_name_plural = _("Institutions")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


########## Image material ##############
class RockCarvingObject(abstract.AbstractBaseModel):

    name = models.CharField(max_length=128, unique=True, verbose_name=_(
        "name"), help_text=_("Name for area/group of panels or common name for a panel."))
    code = models.CharField(max_length=128, null=True, blank=True, verbose_name=_(
        "code"), help_text=_("Standardized code of the object, if applicable."))

    # TODO: Site?

    class Meta:
        verbose_name = _("Rock Carving Area")
        verbose_name_plural = _("Rock Carving Areas")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


class ImageSubType(abstract.AbstractTagModel):
    pass
    order = models.IntegerField(null=True, blank=True, verbose_name=_(
        "orders"), help_text=_("Rank order, for potential use in the frontend."))
    english_translation = models.CharField(max_length=5000, blank=True, verbose_name=_(
        'translation'), help_text=("English translation of subtype tag"))

    class Meta:
        verbose_name = _("Image Subtype")
        verbose_name_plural = _("Image Subtypes")

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return str(self)


class Site(abstract.AbstractBaseModel):
    # Represents the archaeological sites of interests
    # containing carvings or other remnants

    # Various IDs
    ksamsok_id = models.CharField(max_length=128, unique=True, null=True, blank=True, verbose_name=_(
        "Fornsök ID"), help_text=_("UUID at the Fornsök (SOCH) portal."))
    raa_id = models.CharField(max_length=128, unique=False, null=True, blank=True, verbose_name=_(
        "RAÄ ID"), help_text=_("Deprecated ID for heritage remains."), validators=[raa_validator])
    lamning_id = models.CharField(max_length=128, unique=True, null=True, blank=True, verbose_name=_(
        "shfa.lamning_id"), help_text=_("Current ID for heritage remains."), validators=[lamning_validator])
    askeladden_id = models.CharField(max_length=256, unique=False, null=True, blank=True, verbose_name=_(
        "shfa.askeladden_id"), help_text=_("ID at the Norwegian Askeladden database, if applicable."))
    lokalitet_id = models.CharField(max_length=128, unique=False, null=True, blank=True, verbose_name=_(
        "shfa.lokalitet_id"), help_text=_("ID at the Danish <i>lokalitet</i> database or Norwegian Askeladden database, if applicable."))

    # Location
    coordinates = models.PointField(null=True, blank=True, verbose_name=_(
        "Coordinates"), help_text=_("Mid-point coordinates of the site."))
    municipality = models.ForeignKey(geography.LocalAdministrativeUnit, null=True, blank=True,  related_name="sites", on_delete=models.SET_NULL, verbose_name=_(
        "Municipality"), help_text=_("Municipality, or international local administrative unit where the site is located."))
    parish = models.ForeignKey(geography.Parish, null=True, blank=True,  related_name="sites", on_delete=models.SET_NULL, verbose_name=_(
        "Parish"), help_text=_("Swedish ecclesiastical administrative unit where the site is located."))
    province = models.ForeignKey(geography.Province, null=True, blank=True,  related_name="sites", on_delete=models.SET_NULL, verbose_name=_(
        "Province"), help_text=_("Swedish traditional subdivision of territory where the site is located."))

    # Placename is particularly used outside of Sweden
    placename = models.CharField(max_length=256, null=True, blank=True, verbose_name=_(
        "Placename"), help_text=_("Free-form, non-indexed placename of the site."))
    internationl_site = models.BooleanField(null=True, blank=True, help_text=_(
        '<b>Must</b> be set to TRUE if site is outside of Sweden'))

    # Fields for international sites
    StedNr = models.PositiveIntegerField(
        null=True, blank=True, help_text=_('StedNr from Denmark sites'))
    LokNr = models.PositiveIntegerField(
        null=True, blank=True, help_text=_('LokNr from Denmark sites'))
    FredningsNr = models.PositiveIntegerField(
        null=True, blank=True, help_text=_('FredningsNr from Denmark sites'))
    stednavn = models.CharField(max_length=256, null=True, blank=True, help_text=_(
        'stednavn from Denmark sites'))

    def __str__(self) -> str:

        if self.raa_id:
            name_str = f"{self.raa_id}"
        elif self.lamning_id:
            name_str = f"{self.lamning_id}"
        elif self.askeladden_id:
            name_str = f"Askeladden {self.askeladden_id}"
        elif self.lokalitet_id:
            name_str = f"Lokalitet {self.askeladden_id}"
        elif self.placename:
            name_str = f"Placename {self.placename}"
        else:
            name_str = ""

        return name_str

    class Meta:
        verbose_name = _("Site")
        verbose_name_plural = _("Sites")


class Image(abstract.AbstractTIFFImageModel):

    # Rock carving site
    legacy_id = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name=_("legacy id"))

    site = models.ForeignKey(Site, null=True, blank=True, on_delete=models.PROTECT, verbose_name=_(
        "Site"), help_text=_("Rock carving site"))

    # Metadata on collections
    collection = models.ForeignKey(Collection, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_(
        "Collection"), help_text=_("Collection from which the image originates."))
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "Image creator"), help_text=_("Creator, photographer or author of the original image."))
    people = models.ManyToManyField(People, blank=True, related_name="images", verbose_name=_(
        "People"), help_text=_("Creator, photographer or author of the original image, added as individual names."))
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "Institution"), help_text=_("Original institution housing the image."))
    reference = models.CharField(max_length=512, null=True, blank=True, verbose_name=_(
        "References"), help_text=_("Reference notes on the image."))

    # Date stamps
    year = models.PositiveIntegerField(null=True, blank=True, verbose_name=_(
        "Creation year"), help_text=_("Original creation year of the image."))
    date_note = models.TextField(null=True, blank=True, verbose_name=_(
        "Note on date"), help_text=_("Free-form note on the certainty or context of the year."))

    # Motif rock carving object
    rock_carving_object = models.ForeignKey(RockCarvingObject, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "Rock carving area"), help_text=_("Rock carving area in the image, e.g. Aspeberget."))

    # Tags
    keywords = models.ManyToManyField(KeywordTag, blank=True, related_name="images", verbose_name=_(
        "Keywords"), help_text=_("Keywords for motifs and context in the image, used for categorisation."))
    type = models.ForeignKey(ImageTypeTag, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_(
        "Type"), help_text=_("Type of image medium, material or origin."))
    subtype = models.ForeignKey(ImageSubType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Image Subtype"), help_text=_(
        "<b>Required for orthophotos and visualisations.</b>  Type of visualisation generated from TVT or similar tool, or orthophoto."))

    # carving_tags    = models.ManyToManyField(CarvingTag, blank=True, related_name="images", verbose_name=_("Carvings in image"), help_text=_("A list of rock carving motifs in the image."))
    dating_tags = models.ManyToManyField(DatingTag, blank=True, related_name="images", verbose_name=_(
        "Datings"), help_text=_("A list of estimated dating(s) of motifs in the image"))

    group = models.ForeignKey("Group", on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "Group"),  related_name='images_set', help_text=_("Group of images and visualisations the image belongs to. "))

    class Meta:
        verbose_name = _("Image")
        verbose_name_plural = _("Images")

    def __str__(self) -> str:
        return f"Image {self.file.name} of {self.site}"

    def __repr__(self) -> str:
        return str(self)


class Compilation(abstract.AbstractBaseModel):

    # A manual compilation of images, could be used for display
    # of certain collages, for example

    name = models.CharField(max_length=128, unique=True)
    images = models.ManyToManyField(Image, blank=True, related_name="compilations", verbose_name="Images in compilation", help_text=_(
        "List of images to group together, potentially to display curated content in the frontend."))

    class Meta:
        verbose_name = _("Compilation")
        verbose_name_plural = _("Compilations")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


# 3D models
class Group(abstract.AbstractTagModel):
    pass

    class Meta:
        verbose_name = _("Visualisation Group")
        verbose_name_plural = _("Visualisation Groups")

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return str(self)


class RTI(abstract.AbstractBaseModel):
    url = models.URLField(max_length=2048, verbose_name=_(
        "URL"), help_text=_("URL to the RTI file"))
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Group"), help_text=_(
        "Group of visualisations the RTI file belongs to.  This is used to link orthophotos, topo visualisations, and RTI to the corresponding mesh."))

    class Meta:
        verbose_name = _("RTI")
        verbose_name_plural = _("RTIs")

    def __str__(self) -> str:
        return f"{self.url}, {self.group}"


class Geology(abstract.AbstractBaseModel):
    type = models.CharField(max_length=128, verbose_name=_(
        "Type"), help_text=_("Type of geology"))
    type_translation = models.CharField(max_length=5000, blank=True, verbose_name=_(
        'Geology type translation'), help_text=("English translation for geology type"))
    description = models.TextField(verbose_name=_(
        "Description"), help_text=_("Description of geology"))
    desc_translation = models.TextField(verbose_name=_(
        "Geology description translation"), help_text=_("English translation for geology description"))
    coordinates = models.PolygonField(null=True, blank=True, verbose_name=_(
        "Polygon"), help_text=_("Polygon coordinates of the geology"))

    class Meta:
        verbose_name = _("Geology")
        verbose_name_plural = _("Geologies")

    def __str__(self) -> str:
        return self.type


class CameraLens(abstract.AbstractBaseModel):
    name = models.CharField(max_length=256, verbose_name=_(
        "Lens"), help_text=_("Lens of the camera"))
    focal_length = models.FloatField(null=True, blank=True, verbose_name=_(
        "Focal length"), help_text=_("Focal length of the camera lens"))

    class Meta:
        verbose_name = _("Camera Lens")
        verbose_name_plural = _("Camera Lenses")

    def __str__(self) -> str:
        return self.name


class CameraModel(abstract.AbstractBaseModel):
    name = models.CharField(max_length=256, verbose_name=_(
        "Model"), help_text=_("Model of the camera"))
    lens = models.ForeignKey(CameraLens, on_delete=models.SET_NULL, null=True,
                             blank=True, verbose_name=_("Lens"), help_text=_("Lens of the camera"))
    crop_factor = models.FloatField(null=True, blank=True, verbose_name=_(
        "Crop factor"), help_text=_("Crop factor of the camera"))

    class Meta:
        verbose_name = _("Camera Model")
        verbose_name_plural = _("Camera Models")

    def __str__(self) -> str:
        return f"{self.name}, {self.lens}"


class CameraMeta(abstract.AbstractBaseModel):
    link = models.IntegerField(unique=True, verbose_name=_(
        "Link"), help_text=_("Id of the orthophoto in the Images table"))
    # link = models.URLField(max_length=2048, verbose_name=_("Link"), help_text=_("Link to the camera images"))
    # image_type = models.ForeignKey(ImageTypeTag, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Image type"), help_text=_("Type of image medium, material or origin."))
    camera_lens = models.ForeignKey(CameraLens, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "Camera Lens"), help_text=_("Lens of the camera"))
    camera_model = models.ForeignKey(CameraModel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "Camera Model"), help_text=_("Model of the camera"))
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "Group"), help_text=_("Visualisation Group of the images"))

    @property
    def mm35_equivalent(self):
        if self.camera_lens and self.camera_model and self.camera_lens.focal_length is not None and self.camera_model.crop_factor is not None:
            return self.camera_lens.focal_length * self.camera_model.crop_factor
        else:
            return None

    class Meta:
        verbose_name = _("Camera Specification")
        verbose_name_plural = _("Camera Specifications")

    def __str__(self) -> str:
        return f"{self.link}, {self.group}"


class SHFA3D(abstract.AbstractBaseModel):
    creators = models.ManyToManyField(People, blank=True, verbose_name=_("Creator"), help_text=_(
        "Creator(s) of the 3D data, it will be assumed that the orthophotos and visualisation have the same creator."))
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "Institution"), help_text=_("Institution associated with the creator or research project"))
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "Site"), help_text=_("Site of the 3D model"))
    # carving = models.ForeignKey(CarvingTag, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Carving"), help_text=_("Carving of the 3D model"))
    keywords = models.ManyToManyField(KeywordTag, blank=True, related_name="three_d_models", verbose_name=_(
        "Keywords"), help_text=_("Keywords for motifs in the 3D model and visualisations, used for categorisation."))
    datings = models.ManyToManyField(DatingTag, related_name="three_d_models", verbose_name=_("Datings"), help_text=_(
        "Estimated dating(s) for motifs in the 3D model and visualisations, used for categorisation."))
    # image_subtype = models.ForeignKey(ImageSubType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Image type"), help_text=_("Type of image medium, material or origin."))
    image = models.ForeignKey(CameraMeta, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "Camera Specification"), help_text=_("Camera specification for SfM/photogrammetry meshes"))
    three_d_mesh = models.ForeignKey("SHFA3DMesh", on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "3D Mesh"), help_text=_("3D mesh specifications"))
    RTI = models.ForeignKey(RTI, on_delete=models.SET_NULL, null=True,
                            blank=True, verbose_name=_("RTI"), help_text=_("RTI of the 3D model"))
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, related_name='shfa3d_set', null=True, blank=True, verbose_name=_("Group"), help_text=_(
        "Group of the 3D mesh and corresponding visualisations.  A group should of mesh(es) and visualisations should cover <b>exactly</b> the same area."))
    date = models.DateField(null=True, blank=True, verbose_name=_("Date"), help_text=_(
        "Date of the data collection/fieldwork.  If exact date is unknown, estimate to the closest month and year."))
    geology = models.ForeignKey(Geology, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "Geology"), help_text=_("Geology of the rock carving panel"))

    class Meta:
        verbose_name = _("3D Data Overview")
        verbose_name_plural = _("3D Data Overviews")

    def __str__(self) -> str:
        return f"3D model of {self.site}"


class SHFA3DMesh(abstract.AbstractBaseModel):
    mesh_url = models.URLField(max_length=2048, verbose_name=_(
        "URL"), help_text=_("URL to the 3D mesh file"))
    quality_url = models.URLField(null=True, blank=True, max_length=2048, verbose_name=_(
        "Quality URL"), help_text=_("URL to the 3D mesh quality file"))
    method = models.ForeignKey(MethodTag, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "Data type"), help_text=_("Method the mesh is derived from, e.g. SfM, laser scanning."))
    num_vertices = models.IntegerField(null=False, verbose_name=_(
        "Number of vertices"), help_text=_("Number of vertices in the 3D mesh"))
    num_faces = models.IntegerField(null=False, verbose_name=_(
        "Number of faces"), help_text=_("Number of faces in the 3D mesh"))
    num_photos = models.IntegerField(null=True, verbose_name=_("Number of photos"), help_text=_(
        "Number of photos in the 3D mesh. Only required for SfM/photogrammetry meshes."))
    dimensions = ArrayField(models.FloatField(max_length=16, blank=True, null=True), size=3, help_text=_(
        "Dimensions of the 3D mesh in meters, in the order of x, y, z. Enter each value in a new field."))
    weather = models.ManyToManyField(WeatherTag, blank=True, related_name="three_d_models", verbose_name=_("Weather"), help_text=_(
        "Weather conditions during fieldwork, select all that apply. If data collection was carried out indoors, select 'Indoors' rather than leaving blank."))
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_(
        "Group"), help_text=_("Group of mesh(es) and visualisations the 3D mesh belongs to."))

    class Meta:
        verbose_name = _("3D Mesh")
        verbose_name_plural = _("3D Meshes")

    def __str__(self) -> str:
        return f"{self.mesh_url}, {self.group}"

    def __str__(self):
        return str(self.group)


# Models For OAI_PMH
class CustomURLField(models.URLField):
    def to_python(self, value):
        value = super().to_python(value)
        if value and not value.endswith('#'):
            value += '#'  # Append # if it's missing
        return value


class MetadataFormat(abstract.AbstractBaseModel):
    """MetadataFormat Model."""

    prefix = models.CharField(
        max_length=256, unique=True, verbose_name=_("Prefix"))
    schema = models.URLField(max_length=2048, verbose_name=_("Schema"))
    namespace = CustomURLField(max_length=2048, verbose_name=_("Namespace"))

    def __str__(self):
        """Name."""
        return self.prefix

    class Meta:
        """Meta."""

        ordering = ("prefix",)
        verbose_name = _("Metadata format")
        verbose_name_plural = _("Metadata formats")


class ResumptionToken(abstract.AbstractBaseModel):
    """ResumptionToken Model."""

    expiration_date = models.DateTimeField(
        verbose_name=_("Expiration date"),
    )
    complete_list_size = models.IntegerField(
        default=0,
        verbose_name=_("Complete list size"),
    )
    cursor = models.IntegerField(default=0, verbose_name=_("Cursor"))
    token = models.TextField(unique=True, verbose_name=_("Token"))

    from_timestamp = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("From timestamp"),
    )
    until_timestamp = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Until timestamp"),
    )
    metadata_prefix = models.ForeignKey(
        MetadataFormat,
        models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("Metadata prefix"),
    )

    def __str__(self):
        """Name."""
        return self.token

    class Meta:
        """Meta."""

        ordering = ("expiration_date",)
        verbose_name = _("Resumption token")
        verbose_name_plural = _("Resumption tokens")
