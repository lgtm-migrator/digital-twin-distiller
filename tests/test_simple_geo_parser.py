from unittest import TestCase
from digital_twin_distiller.geo_parser import geo_parser
from importlib_resources import files


class SimpleGEOparser(TestCase):

    def test_base_objects(self):
        path = files("tests.test_geo_geometry").joinpath("base_objects.geo")
        test_geo = geo_parser(path.as_posix())

        # the point data and the coordinates in the given geo file
        self.assertEqual(test_geo.nodes[0].x, -0.0004018925337573828)
        self.assertEqual(test_geo.nodes[0].y, 0.05177306826503763)
        self.assertEqual(test_geo.nodes[0].id, 1336)

        # the line object imported correctly
        self.assertEqual(test_geo.lines[0].id, 1)
        self.assertEqual(test_geo.lines[0].start_pt.id, 1)
        self.assertEqual(test_geo.lines[0].end_pt.id, 2)

        # import a circle object circle data 60 [1.0, 2.0, 1336.0]
        self.assertEqual(test_geo.circle_arcs[0].id, 60)
        self.assertEqual(test_geo.circle_arcs[0].start_pt.id, 1)
        self.assertEqual(test_geo.circle_arcs[0].end_pt.id, 1336)


    def test_base_object_invalid(self):
        path = files("tests.test_geo_geometry").joinpath("base_objects.geo")
        test_geo = geo_parser(path.as_posix())