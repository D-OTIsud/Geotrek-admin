import json
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import Point, GEOSGeometry
from django.utils.translation import gettext as _, get_language

from geotrek.common.models import Label, Theme
from geotrek.common.parsers import ShapeParser, AttachmentParserMixin, GeotrekParser, RowImportError, Parser
from geotrek.common.utils.translation import get_translated_fields
from geotrek.trekking.models import OrderedTrekChild, POI, Service, Trek


class DurationParserMixin:
    def filter_duration(self, src, val):
        val = val.upper().replace(',', '.')
        try:
            if "H" in val:
                hours, minutes = val.split("H", 2)
                hours = float(hours.strip())
                minutes = float(minutes.strip()) if minutes.strip() else 0
                if hours < 0 or minutes < 0 or minutes >= 60:
                    raise ValueError
                return hours + minutes / 60
            else:
                hours = float(val.strip())
                if hours < 0:
                    raise ValueError
                return hours
        except (TypeError, ValueError):
            self.add_warning(_("Bad value '{val}' for field {src}. Should be like '2h30', '2,5' or '2.5'".format(val=val, src=src)))
            return None


class TrekParser(DurationParserMixin, AttachmentParserMixin, ShapeParser):
    label = "Import trek"
    label_fr = "Import itinéraires"
    label_en = "Import trek"
    model = Trek
    simplify_tolerance = 2
    eid = 'name'
    constant_fields = {
        'published': True,
        'deleted': False,
    }
    natural_keys = {
        'difficulty': 'difficulty',
        'route': 'route',
        'themes': 'label',
        'practice': 'name',
        'accessibilities': 'name',
        'networks': 'network'
    }

    def filter_geom(self, src, val):
        if val is None:
            return None
        if val.geom_type == 'MultiLineString':
            points = val[0]
            for i, path in enumerate(val[1:]):
                distance = Point(points[-1]).distance(Point(path[0]))
                if distance > 5:
                    self.add_warning(_("Not contiguous segment {i} ({distance} m) for geometry for field '{src}'").format(i=i + 2, p1=points[-1], p2=path[0], distance=int(distance), src=src))
                points += path
            return points
        elif val.geom_type != 'LineString':
            self.add_warning(_("Invalid geometry type for field '{src}'. Should be LineString, not {geom_type}").format(src=src, geom_type=val.geom_type))
            return None
        return val


class GeotrekTrekParser(GeotrekParser):
    """Geotrek parser for Trek"""

    url = None
    model = Trek
    constant_fields = {
        'published': True,
        'deleted': False,
    }
    replace_fields = {
        "eid": "uuid",
        "eid2": "second_external_id",
        "geom": "geometry"
    }
    url_categories = {
        "difficulty": "trek_difficulty",
        "route": "trek_route",
        "themes": "theme",
        "practice": "trek_practice",
        "accessibilities": "trek_accessibility",
        "networks": "trek_network",
        'labels': 'label',
        'source': 'source'
    }
    categories_keys_api_v2 = {
        'difficulty': 'label',
        'route': 'route',
        'themes': 'label',
        'practice': 'name',
        'accessibilities': 'name',
        'networks': 'label',
        'labels': 'name',
        'source': 'name'
    }
    natural_keys = {
        'difficulty': 'difficulty',
        'route': 'route',
        'themes': 'label',
        'practice': 'name',
        'accessibilities': 'name',
        'networks': 'network',
        'labels': 'name',
        'source': 'name'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.next_url = f"{self.url}/api/v2/trek"

    def filter_parking_location(self, src, val):
        if val:
            return Point(val[0], val[1], srid=settings.API_SRID)

    def filter_points_reference(self, src, val):
        if val:
            geom = GEOSGeometry(json.dumps(val))
            return geom.transform(settings.SRID, clone=True)

    def end(self):
        """Add children after all treks imported are created in database."""
        super().end()
        self.next_url = f"{self.url}/api/v2/tour"
        try:
            params = {
                'in_bbox': ','.join([str(coord) for coord in self.bbox.extent]),
                'fields': 'steps,uuid'
            }
            response = self.request_or_retry(f"{self.next_url}", params=params)
            results = response.json()['results']
            final_children = {}
            for result in results:
                final_children[result['uuid']] = [step['uuid'] for step in result['steps']]

            for key, value in final_children.items():
                if value:
                    trek_parent_instance = Trek.objects.filter(eid=key)
                    if not trek_parent_instance:
                        self.add_warning(_(f"Trying to retrieve children for missing trek : could not find trek with UUID {key}"))
                        return
                    order = 0
                    for child in value:
                        try:
                            trek_child_instance = Trek.objects.get(eid=child)
                        except Trek.DoesNotExist:
                            self.add_warning(_(f"One trek has not be generated for {trek_parent_instance[0].name} : could not find trek with UUID {child}"))
                            continue
                        OrderedTrekChild.objects.get_or_create(parent=trek_parent_instance[0],
                                                               child=trek_child_instance,
                                                               order=order)
                        order += 1
        except Exception as e:
            self.add_warning(_(f"An error occured in children generation : {getattr(e, 'message', repr(e))}"))


class GeotrekServiceParser(GeotrekParser):
    """Geotrek parser for Service"""

    url = None
    model = Service
    constant_fields = {
        'deleted': False,
    }
    replace_fields = {
        "eid": "uuid",
        "geom": "geometry"
    }
    url_categories = {
        "type": "service_type",
    }
    categories_keys_api_v2 = {
        'type': 'name',
    }
    natural_keys = {
        'type': 'name'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.next_url = f"{self.url}/api/v2/service"


class GeotrekPOIParser(GeotrekParser):
    """Geotrek parser for GeotrekPOI"""

    url = None
    model = POI
    constant_fields = {
        'published': True,
        'deleted': False,
    }
    replace_fields = {
        "eid": "uuid",
        "geom": "geometry"
    }
    url_categories = {
        "type": "poi_type",
    }
    categories_keys_api_v2 = {
        'type': 'label',
    }
    natural_keys = {
        'type': 'label',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.next_url = f"{self.url}/api/v2/poi"


from geotrek.tourism.parsers import ApidaeParser  # Noqa


TYPOLOGIES_SITRA_IDS_AS_LABELS = [1599, 1676, 4639, 4819, 5022, 4971, 3845, 6566, 6049, 1582, 5538, 6825, 6608, 1602]
TYPOLOGIES_SITRA_IDS_AS_THEMES = [6155, 6156, 6368, 6153, 6154, 6157, 6163, 6158, 6679, 6159, 6160, 6161]
ENVIRONNEMENTS_IDS_AS_LABELS = [135, 4630, 171, 189, 186, 6238, 3743, 147, 149, 156, 153, 187, 195, 6464, 4006, 169, 3978, 6087]
GUIDEBOOK_DESCRIPTION_ID = 6527


class ApidaeTrekParser(ApidaeParser):
    model = Trek
    eid = 'eid'
    separator = None

    # Parameters to build the request
    url = 'https://api.apidae-tourisme.com/api/v002/recherche/list-objets-touristiques/'
    api_key = None
    project_id = None
    selection_id = None
    size = 20
    skip = 0
    responseFields = [
        'id',
        'nom',
        'multimedias',
        'gestion',
        'presentation',
        'localisation',
    ]
    locales = ['fr', 'en']

    # Fields mapping
    fields = {
        'name_fr': 'nom.libelleFr',
        'name_en': 'nom.libelleEn',
        'description': (
            'presentation.descriptifsThematises.*',
        ),
        'geom': 'multimedias',
        'eid': 'id',
    }
    m2m_fields = {
        'source': ['gestion.membreProprietaire.nom'],
        'themes': 'presentation.typologiesPromoSitra.*',
        'labels': ['presentation.typologiesPromoSitra.*', 'localisation.environnements.*'],
    }
    natural_keys = {
        'source': 'name',
        'themes': 'label',
        'labels': 'name',
    }
    field_options = {
        'source': {'create': True},
        'themes': {'create': True},
        'labels': {'create': True},
    }
    non_fields = {}

    def __init__(self, *args, **kwargs):
        self._translated_fields = [field for field in get_translated_fields(self.model)]
        super().__init__(*args, **kwargs)

    @staticmethod
    def _find_gpx_plan_in_multimedia_items(items):
        plans = list(filter(lambda item: item['type'] == 'PLAN', items))
        if len(plans) > 1:
            raise RowImportError("APIDAE Trek has more than one map defined")
        return plans[0]

    def _fetch_gpx_from_url(self, plan):
        ref_fichier_plan = plan['traductionFichiers'][0]
        if ref_fichier_plan['extension'] != 'gpx':
            raise RowImportError("Le plan de l'itinéraire APIDAE n'est pas au format GPX")
        response = self.request_or_retry(url=ref_fichier_plan['url'])
        # print('downloaded url {}, content size {}'.format(plan['traductionFichiers'][0]['url'], len(response.text)))
        return response.content

    @staticmethod
    def _get_tracks_layer(datasource):
        for layer in datasource:
            if layer.name == 'tracks':
                return layer
        raise RowImportError("APIDAE Trek GPX map does not have a 'tracks' layer")

    def apply_filter(self, dst, src, val):
        val = super().apply_filter(dst, src, val)
        if dst in self.translated_fields:
            if isinstance(val, dict):
                for key, final_value in val.items():
                    if key in settings.MODELTRANSLATION_LANGUAGES:
                        self.set_value(f'{dst}_{key}', src, final_value)
                val = val.get(get_language())
        return val

    def filter_geom(self, src, val):
        plan = self._find_gpx_plan_in_multimedia_items(val)
        gpx = self._fetch_gpx_from_url(plan)

        # FIXME: is there another way than the temporary file? It seems not. `DataSource` really expects a filename.
        with NamedTemporaryFile(mode='w+b', dir='/opt/geotrek-admin/var/tmp') as ntf:
            ntf.write(gpx)
            ntf.flush()

            ds = DataSource(ntf.name)
            track_layer = self._get_tracks_layer(ds)
            geom = track_layer[0].geom[0].geos
            geom.transform(settings.SRID)
            return geom

    def filter_labels(self, src, val):
        filtered_val = []
        for subval in val:
            if not subval:
                continue
            for item in subval:
                item_type = item['elementReferenceType']
                if ((item_type == 'TypologiePromoSitra' and item['id'] in TYPOLOGIES_SITRA_IDS_AS_LABELS)
                        or (item_type == 'Environnement' and item['id'] in ENVIRONNEMENTS_IDS_AS_LABELS)):
                    filtered_val.append(item['libelleFr'])
        return self.apply_filter(
            dst='labels',
            src=src,
            val=filtered_val
        )

    def filter_themes(self, src, val):
        return self.apply_filter(
            dst='themes',
            src=src,
            val=[item['libelleFr'] for item in val if item['id'] in TYPOLOGIES_SITRA_IDS_AS_THEMES]
        )

    def filter_description(self, src, val):
        # TODO: multi-languages
        # TODO: process into HTML paragraphs
        # TODO: process checkpoints numbers
        descriptifs = val[0]

        if not descriptifs:
            return ''

        rv = {}
        guidebook = None
        for d in descriptifs:
            if d['theme']['id'] == GUIDEBOOK_DESCRIPTION_ID:
                guidebook = d
                break
        if guidebook:
            for lang in settings.MODELTRANSLATION_LANGUAGES:
                try:
                    rv[lang] = guidebook['description'][f'libelle{lang.capitalize()}']
                except KeyError:
                    pass

        for lang, value in rv.items():
            rv[lang] = ApidaeTrekParser._transform_guidebook_to_html(value)

        return self.apply_filter(
            dst='description',
            src=src,
            val=rv
        )

    @staticmethod
    def _transform_guidebook_to_html(text):
        """Transform a guidebook string into HTML paragraphs."""
        html_blocks = []
        lines = text.replace('\r', '').split('\n')
        for line in lines:
            if not line:
                continue
            html_blocks.append(f'<p>{line}</p>')
        return ''.join(html_blocks)


class ApidaeReferenceElementParser(Parser):

    url = 'https://api.apidae-tourisme.com/api/v002/referentiel/elements-reference/'

    api_key = None
    project_id = None
    element_reference_ids = None
    name_field = None
    # Fields mapping is generated in __init__

    def __init__(self, *args, **kwargs):
        self._add_multi_languages_fields_mapping()
        self._set_eid_fieldname()
        super().__init__(*args, **kwargs)

    def _add_multi_languages_fields_mapping(self):
        self.fields = {
            f'{self.name_field}_{lang}': f'libelle{lang.capitalize()}'
            for lang in settings.MODELTRANSLATION_LANGUAGES
        }

    def _set_eid_fieldname(self):
        self.eid = f'{self.name_field}_{settings.MODELTRANSLATION_DEFAULT_LANGUAGE}'

    @property
    def items(self):
        return self.root

    def next_row(self):
        params = {
            'apiKey': self.api_key,
            'projetId': self.project_id,
            'elementReferenceIds': self.element_reference_ids,
        }
        response = self.request_or_retry(self.url, params={'query': json.dumps(params)})
        self.root = response.json()
        self.nb = len(self.root)
        for row in self.items:
            yield row

    def normalize_field_name(self, name):
        return name


class ApidaeTrekThemeParser(ApidaeReferenceElementParser):
    model = Theme
    element_reference_ids = TYPOLOGIES_SITRA_IDS_AS_THEMES
    name_field = 'label'


class ApidaeTrekLabelParser(ApidaeReferenceElementParser):
    model = Label
    element_reference_ids = TYPOLOGIES_SITRA_IDS_AS_LABELS + ENVIRONNEMENTS_IDS_AS_LABELS
    name_field = 'name'


# TODO
# class ApidaeTrekAccessibilityParser(ApidaeReferenceElementParser):
#     model = Accessibility
#     element_reference_ids = None
#
#
# class ApidaeTrekDifficultyParser(ApidaeReferenceElementParser):
#     model = DifficultyLevel
#     element_reference_ids = None
#
#
# class ApidaeTrekNetworkParser(ApidaeReferenceElementParser):
#     model = TrekNetwork
#     element_reference_ids = None
