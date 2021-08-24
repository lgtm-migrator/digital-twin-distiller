from adze_modeler.material import Material
from adze_modeler.boundaries import DirichletBoundaryCondition, NeumannBoundaryCondition
from adze_modeler.snapshot import Snapshot
from adze_modeler.model import BaseModel
from adze_modeler.platforms.femm import Femm
from adze_modeler.platforms.agros2d import Agros2D
from adze_modeler.metadata import FemmMetadata
from adze_modeler.metadata import Agros2DMetadata
from adze_modeler.modelpiece import ModelPiece
import numpy as np

class SymmetircModel(BaseModel):
    """docstring for SymmetircModel"""
    def __init__(self, X, exportname=None):
        assert len(X) == 10
        self.X = X

        super(SymmetircModel, self).__init__(exportname=exportname)
        self._init_directories()

        self.label_queue.append((3, 1, "control"))
        self.label_queue.append((30, 30, "air"))

    def setup_solver(self):
        femm_metadata = FemmMetadata()
        femm_metadata.problem_type = "magnetic"
        femm_metadata.coordinate_type = "axisymmetric"
        femm_metadata.file_script_name = self.file_solver_script
        femm_metadata.file_metrics_name = self.file_solution
        femm_metadata.unit = "millimeters"
        femm_metadata.smartmesh = False

        agros_metadata = Agros2DMetadata()
        agros_metadata.file_script_name = self.file_solver_script
        agros_metadata.file_metrics_name = self.file_solution
        agros_metadata.problem_type = "magnetic"
        agros_metadata.coordinate_type = "axisymmetric"
        agros_metadata.analysis_type = "steadystate"
        agros_metadata.unit = 1e-3
        agros_metadata.nb_refinements = 0
        agros_metadata.adaptivity = "hp-adaptivity"
        agros_metadata.adaptivity_tol = 1

        platform_femm = Femm(femm_metadata)
        platform_agros = Agros2D(agros_metadata)

        self.platform = platform_agros
        self.snapshot = Snapshot(self.platform)

    def define_boundary_conditions(self):
        b1 = DirichletBoundaryCondition(
            name="a0", field_type=self.platform.metadata.problem_type, magnetic_potential=0.0
        )
        n0 = NeumannBoundaryCondition(name="n0", field_type=self.platform.metadata.problem_type,
                                      surface_current=0.0)

        self.snapshot.add_boundary_condition(b1)
        self.snapshot.add_boundary_condition(n0)

        self.boundary_queue.append((0, 2.5, "a0"))
        self.boundary_queue.append((0, 25, "a0"))
        self.boundary_queue.append((40, 140, "a0"))
        self.boundary_queue.append((140, 40, "a0"))

        self.boundary_queue.append((2, 0, "n0"))
        self.boundary_queue.append(((self.X[0] + 5)/2, 0, "n0"))
        self.boundary_queue.append((130, 0, "n0"))
        self.boundary_queue.append((self.X[0] + 0.5, 0, "n0"))

    def define_materials(self):
        exctitation = Material("J+")
        exctitation.Je = 2e6
        # exctitation.meshsize = 1

        air = Material("air")
        # air.meshsize = 0.7
        
        control = Material("control")
        # control.meshsize = 0.1


        self.snapshot.add_material(exctitation)
        self.snapshot.add_material(air)
        self.snapshot.add_material(control)
    
    def add_postprocessing(self):
        Nx = 10
        Ny = 10
        px = np.linspace(0.001, 5, Nx)
        py = np.linspace(0.001, 5, Ny)
        xv, yv = np.meshgrid(px, py, sparse=False, indexing="xy")

        for i in range(Nx):
            for j in range(Ny):
                eval_point = (xv[j, i], yv[j, i])
                self.snapshot.add_postprocessing("point_value", eval_point, "Bz")
                self.snapshot.add_postprocessing("point_value", eval_point, "Br")

        self.snapshot.add_postprocessing("mesh_info", None, None)

    def build_geometry(self):
        mp_bound = ModelPiece("bound")
        mp_bound.load_piece_from_svg(self.dir_resources / "problem_boundary.svg")
        mp_bound.put(0, 0)

        mp_control = ModelPiece("core")
        mp_control.load_piece_from_svg(self.dir_resources / "core_half.svg")
        mp_control.put(0, 0)

        mp_coil = ModelPiece("coil")
        mp_coil.load_piece_from_svg(self.dir_resources / "coil.svg")


        N = len(self.X)
        h = 1.5
        w = 1.0
        self.geom.merge_geometry(mp_bound.geom)
        self.geom.merge_geometry(mp_control.geom)

        for i, ri in enumerate(self.X):
            coil = mp_coil.spawn()
            offsetz = i * h
            coil.put(ri, offsetz)
            self.geom.merge_geometry(coil.geom)
            self.label_queue.append((ri + w / 2, offsetz + h / 2, "J+"))

        print(len(self.geom.nodes), len(self.geom.lines))
        self.geom.merge_points()
        self.geom.generate_intersections()
        self.geom.merge_lines()

        print(len(self.geom.nodes), len(self.geom.lines))
        self.snapshot.add_geometry(self.geom)


if __name__ == "__main__":

    X = [10]*10
    print(X)

    m = SymmetircModel(X, exportname='dev')
    print(m(cleanup=False, devmode=False))