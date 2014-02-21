import os
from StringIO import StringIO
from mock import patch, call

from django.core.management.base import CommandError
from django.test import TestCase
from django.contrib.gis.geos import GEOSGeometry

from geotrek.core.factories import PathFactory
from geotrek.trekking.models import POI
from geotrek.trekking.management.commands.loadpoi import Command


class LoadPOITest(TestCase):
    def setUp(self):
        self.cmd = Command()
        self.filename = os.path.join(os.path.dirname(__file__),
                                     'data', 'poi.shp')
        PathFactory.create()

    def test_command_fails_if_no_arg(self):
        self.assertRaises(CommandError, self.cmd.execute)

    def test_command_fails_if_too_many_args(self):
        self.assertRaises(CommandError, self.cmd.execute, 'a', 'b')

    def test_command_fails_if_filename_missing(self):
        self.assertRaises(CommandError, self.cmd.execute, 'toto.shp')

    def test_command_shows_number_of_objects(self):
        output = StringIO()
        self.cmd.execute(self.filename, stdout=output)
        self.assertIn('2 objects found', output.getvalue())

    # def test_pois_are_created(self):
    #     before = len(POI.objects.all())
    #     self.cmd.execute(self.filename)
    #     after = len(POI.objects.all())
    #     self.assertEquals(after - before, 2)

    def test_create_pois_is_executed(self):
        with patch.object(Command, 'create_poi') as mocked:
            self.cmd.execute(self.filename)
            self.assertEquals(mocked.call_count, 2)

    def test_create_pois_receives_geometries(self):
        geom1 = call(GEOSGeometry('POINT(0 0)'))
        geom2 = call(GEOSGeometry('POINT(0 0)'))
        with patch.object(Command, 'create_poi') as mocked:
            self.cmd.execute(self.filename)
            self.assertEquals(mocked.call_list(), [geom1, geom2])
