from adze_modeler.model import BaseModel
from adze_modeler.metadata import FemmMetadata
from adze_modeler.platforms.femm import Femm
from adze_modeler.snapshot import Snapshot
from adze_modeler.material import Material
from adze_modeler.boundaries import DirichletBoundaryCondition
from adze_modeler.modelpaths import ModelDir

ModelDir.set_base(__file__)

class PowerTransformer(BaseModel):
    """docstring for PowerTransformer"""
    def __init__(self, **kwargs):
        exportname = kwargs.get('exportname', None)
        super(PowerTransformer, self).__init__()
        self._init_directories()

    def setup_solver(self):
        femm_metadata = FemmMetadata()
        femm_metadata.problem_type = "magnetic"
        femm_metadata.coordinate_type = "axisymmetric"
        femm_metadata.file_script_name = self.file_solver_script
        femm_metadata.file_metrics_name = self.file_solution
        femm_metadata.unit = "millimeters"
        femm_metadata.smartmesh = True

        self.platform = Femm(femm_metadata)
        self.snapshot = Snapshot(self.platform)

    def define_materials(self):
        air = Material('air')

        self.snapshot.add_material(air)

    def define_boundary_conditions(self):
        a0 = DirichletBoundaryCondition("a0", field_type="magnetic", magnetic_potential=0.0)

        # Adding boundary conditions to the snapshot
        self.snapshot.add_boundary_condition(a0)

    def add_postprocessing(self):
        points = [(0, 0), (0, 0)]
        self.snapshot.add_postprocessing("integration", points, "Torque")
        
    def build_geometry(self):
        # ...
        self.snapshot.add_geometry(self.geom)
        

if __name__ == "__main__":
    m = PowerTransformer(exportname="dev")
    print(m(cleanup=False, devmode=True))
