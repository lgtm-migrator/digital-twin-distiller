from adze_modeler.geometry import Geometry
from adze_modeler.objects import Line, Node
from adze_modeler.snapshot import Snapshot
from adze_modeler.platforms.agros2d import Agros2D
from adze_modeler.platforms.femm import Femm
from adze_modeler.metadata import Agros2DMetadata
from adze_modeler.metadata import FemmMetadata
from adze_modeler.boundaries import DirichletBoundaryCondition
from adze_modeler.boundaries import NeumannBoundaryCondition
from adze_modeler.material import Material
from pathlib import Path


import unittest

class MockFileHandle:

    def __init__(self):
        self.content=""

    def close(self):
        pass

    def write(self, str_):
        self.content += str_

    def clear(self):
        self.content = ""

    def get_line(self, n: int):
        return self.content.split('\n')[n]

class TestSnapshotAgros2D(unittest.TestCase):
    def get_geometry(self):
        g = Geometry()
        g.add_line(Line(Node(-1, 0), Node(1, 0)))
        return g

    def get_metadata(self):
        agros_metadata = Agros2DMetadata()
        agros_metadata.file_script_name = "agros_solver_script"
        agros_metadata.file_metrics_name = "agros_solution.csv"
        agros_metadata.problem_type = "magnetic"
        agros_metadata.coordinate_type = "axisymmetric"
        agros_metadata.analysis_type = "steadystate"
        agros_metadata.unit = 1e-3
        agros_metadata.nb_refinements = 2
        return agros_metadata

    def get_platform(self):
        return Agros2D(self.get_metadata())

    def get_snapshot(self):
        return Snapshot(self.get_platform())

    def test_snapshot_setup(self):
        metadata = self.get_metadata()
        platform = self.get_platform()
        snapshot = Snapshot(platform)

        snapshot.set_platform(platform)
        self.assertTrue(snapshot.platform.metadata.compatible_platform, metadata.compatible_platform)


    def test_set_add_boundary_condition(self):
        s = self.get_snapshot()
        s.add_boundary_condition(DirichletBoundaryCondition('eper', 'magnetic', magnetic_potential=3))
        self.assertTrue('eper' in s.boundaries)

    def test_assign_boundary_condition(self):
        s = self.get_snapshot()
        s.add_boundary_condition(DirichletBoundaryCondition('eper', 'magnetic', magnetic_potential=3))
        self.assertRaises(ValueError, s.assign_boundary_condition, x=0, y=0, name="falsename")


    def test_add_material(self):
        s = self.get_snapshot()
        s.add_material(Material('iron'))
        self.assertTrue(s.materials)

    def test_add_material(self):
        s = self.get_snapshot()
        s.add_material(Material('iron'))
        s.assign_material(4, 42, "iron")
        self.assertEqual(s.materials["iron"].assigned[0], (4, 42))

    def test_add_geometry(self):
        g = self.get_geometry()
        s = self.get_snapshot()
        s.add_geometry(g)
        self.assertTrue(len(s.lines) == 1)
        self.assertTrue(len(s.nodes) == 2)

    def test_add_postprocessing(self):
        ...

    def test_export(self):
        s = self.get_snapshot()
        s.add_material(Material('air'))
        s.assign_material(0, 0, 'air')
        s.add_geometry(self.get_geometry())
        s.add_boundary_condition(DirichletBoundaryCondition('d0', 'magnetic', magnetic_potential=30))
        f = MockFileHandle()
        # s.export()
        s.export(f)
        with open(Path(__file__).parent / "solver_script_references" / "agros2d_default_script.py", "r") as f_ref:
            for i, line in enumerate(f_ref.readlines()):
                self.assertEqual(f.get_line(i), line.rstrip())






class TestSnapshotFemm(unittest.TestCase):
    def get_geometry(self):
        g = Geometry()
        g.add_line(Line(Node(-1, 0), Node(1, 0)))
        return g

    def get_metadata(self):
        femm_metadata = FemmMetadata()
        femm_metadata.problem_type = "magnetic"
        femm_metadata.coordinate_type = "axisymmetric"
        femm_metadata.file_script_name = "femm_solver_script"
        femm_metadata.file_metrics_name = "femm_solution.csv"
        femm_metadata.unit = "millimeters"
        femm_metadata.smartmesh = False
        return femm_metadata

    def get_platform(self):
        return Femm(self.get_metadata())

    def get_snapshot(self):
        return Snapshot(self.get_platform())

    def test_snapshot_setup(self):
        metadata = self.get_metadata()
        platform = self.get_platform()
        snapshot = Snapshot(platform)

        snapshot.set_platform(platform)
        self.assertTrue(snapshot.platform.metadata.compatible_platform, metadata.compatible_platform)

    def test_set_add_boundary_condition(self):
        s = self.get_snapshot()
        s.add_boundary_condition(DirichletBoundaryCondition('eper', 'magnetic', magnetic_potential=3))
        self.assertTrue('eper' in s.boundaries)

    def test_assign_boundary_condition(self):
        s = self.get_snapshot()
        s.add_boundary_condition(DirichletBoundaryCondition('eper', 'magnetic', magnetic_potential=3))
        self.assertRaises(ValueError, s.assign_boundary_condition, x=0, y=0, name="falsename")


    def test_add_material(self):
        s = self.get_snapshot()
        s.add_material(Material('iron'))
        self.assertTrue(s.materials)

    def test_add_material(self):
        s = self.get_snapshot()
        s.add_material(Material('iron'))
        s.assign_material(4, 42, "iron")
        self.assertEqual(s.materials["iron"].assigned[0], (4, 42))

    def test_add_geometry(self):
        g = self.get_geometry()
        s = self.get_snapshot()
        s.add_geometry(g)
        self.assertTrue(len(s.lines) == 1)
        self.assertTrue(len(s.nodes) == 2)

    def test_add_postprocessing(self):
        ...

    def test_export(self):
        s = self.get_snapshot()
        s.add_geometry(self.get_geometry())
        s.add_material(Material('air'))
        s.assign_material(0, 0, 'air')
        s.add_boundary_condition(DirichletBoundaryCondition('d0', 'magnetic', magnetic_potential=30))
        f = MockFileHandle()
        # s.export()
        s.export(f)
        with open(Path(__file__).parent / "solver_script_references" / "femm_default_script.lua", "r") as f_ref:
            for i, line in enumerate(f_ref.readlines()):
                self.assertEqual(f.get_line(i), line.rstrip())