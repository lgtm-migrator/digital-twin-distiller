from copy import copy
import math
from time import perf_counter

from adze_modeler.model import BaseModel
from adze_modeler.metadata import FemmMetadata
from adze_modeler.platforms.femm import Femm
from adze_modeler.snapshot import Snapshot
from adze_modeler.material import Material
from adze_modeler.boundaries import DirichletBoundaryCondition
from adze_modeler.modelpaths import ModelDir
from adze_modeler.geometry import Geometry
from adze_modeler.modelpiece import ModelPiece
from adze_modeler.objects import CircleArc, Line, Node

ModelDir.set_base(__file__)

def cart2pol(x: float, y: float):
    rho = math.hypot(x, y)
    phi = math.atan2(y, x)
    return rho, phi

def pol2cart(rho: float, phi: float):
    x = rho * math.cos(math.radians(phi))
    y = rho * math.sin(math.radians(phi))
    return x, y

def quadroots(a, b, c):
    dis = b * b - 4 * a * c
    sqrt_val = math.sqrt(abs(dis))

    if dis > 0:
        if ((-b - sqrt_val) / (2 * a)) > 0:
            return (-b - sqrt_val) / (2 * a)
        elif ((-b + sqrt_val) / (2 * a)) > 0:
            return (-b + sqrt_val) / (2 * a)
        else:
            return None

    elif dis == 0:
        return(-b / (2 * a))

    else:
        print("Complex Roots")
        return None

def triangle_cos_a(a, b, c):
    angle = math.acos((a ** 2 - b ** 2 - c ** 2) / (-2 * b * c))
    return angle

def triangle_cos_b(a, b, c):
    angle = math.acos((b ** 2 - a ** 2 - c ** 2) / (-2 * a * c))
    return angle

def triangle_cos_c(a, b, c):
    angle = math.acos((c ** 2 - b ** 2 - a ** 2) / (-2 * b * a))
    return angle

class SRM(BaseModel):
    """
    https://livettu-my.sharepoint.com/personal/ekandr_ttu_ee/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fekandr%5Fttu%5Fee%2FDocuments%2FTalTech%2DUWB%20collaboration&originalPath=aHR0cHM6Ly9saXZldHR1LW15LnNoYXJlcG9pbnQuY29tLzpmOi9nL3BlcnNvbmFsL2VrYW5kcl90dHVfZWUvRXZncGlSU1BYdlZLcnlIWk5BYTV3bXNCd0d5Tl96dllvWm94RGpnS3BBcHpYZz9ydGltZT10N2NhRFkyTjJVZw

    TalTech-UWB Collaboration
    """

    def __init__(self, **kwargs):
        exportname = kwargs.get('exportname', None)

        super(SRM, self).__init__()
        self._init_directories()

        ## SIMULATION
        self.rotorangle = kwargs.get('rotorangle', 0.0)
        self.alpha = -kwargs.get('alpha', 0.0)
        self.origin = Node(0, 0)

        ## GEOMETRY
        self.depth = kwargs.get('depth', 0.0)
        self.temp1 = kwargs.get('temp1', None)

        ## BOUNDARIES
        self.ag1l = kwargs.get('ag1l', None)
        self.ag1r = kwargs.get('ag1r', None)
        self.ag2l = kwargs.get('ag2l', None)
        self.ag2r = kwargs.get('ag2r', None)

        ## STATOR
        self.D1 = kwargs.get('D1', 103.0)  # Stator outer diameter [mm]
        self.D2 = kwargs.get('D2', 60.0)  # Stator inner diameter [mm]
        self.beta_s = kwargs.get('beta_s', 30.0)  # Stator pole angle [°]
        self.alpha_s = kwargs.get('alpha_s', 90.0)  # Stator tooth angle [°]
        self.R_bs = kwargs.get('R_bs', 0.0)  # Stator bifurcation radius [mm]
        self.T2 = kwargs.get('T2', 16.5)  # Sloth depth [mm]
        self.gamma_s = kwargs.get('gamma_s', 15.0)  # Coil angle [°]
        self.W1 = kwargs.get('W1', 8.5)  # Coil bottom width [mm]
        self.Z = kwargs.get('Z', 6)  # Number of stator teeth [u.]

        self.p = kwargs.get('p', 2.0)  # Pole pair number

        ## ROTOR
        self.D3 = kwargs.get('D3', 59.5)  # Rotor bore diameter [mm]
        self.D4 = kwargs.get('D4', 10.0)  # Rotor inner diameter [mm]
        self.T1 = kwargs.get('T1', 6.4)  # Core thickness [mm]
        self.beta_r = kwargs.get('beta_r', 29.0)  # Rotor pole angle [°]
        self.alpha_r = kwargs.get('alpha_r', 0.0)  # Rotor tooth angle [°]
        self.R_br = kwargs.get('R_br', 0.0)  # Rotor bifurcation radius [mm]
        self.gamma_r = kwargs.get('gamma_r', 15.0)  # Rotor pole angle [°]

        ## EXCITATION
        half_coil_area = kwargs.get('half_coil_area', 1.0)  # m2
        Nturns = kwargs.get('Nturns', 0.0)
        I0 = kwargs.get('I0', 0.0)
        J0 = Nturns * I0 / half_coil_area
        self.JU = J0 * math.cos(math.radians(self.alpha))
        self.JV = J0 * math.cos(math.radians(self.alpha + 120))
        self.JW = J0 * math.cos(math.radians(self.alpha + 240))

        ## MESH SIZES
        self.msh_smartmesh = kwargs.get('smartmesh', False)
        self.msh_size_stator_steel = kwargs.get('msh_size_stator_steel', 0.0)
        self.msh_size_rotor_steel = kwargs.get('msh_size_rotor_steel', 0.0)
        self.msh_size_coils = kwargs.get('msh_size_coils', 0.0)
        self.msh_size_air = kwargs.get('msh_size_air', 0.0)
        self.msh_size_airgap = kwargs.get('msh_size_airgap', 0.0)
        self.msh_size_magnets = kwargs.get('msh_size_magnets', 0.0)

        ## MATERIAL


    def setup_solver(self):
        femm_metadata = FemmMetadata()
        femm_metadata.problem_type = "magnetic"
        femm_metadata.coordinate_type = "planar"
        femm_metadata.file_script_name = self.file_solver_script
        femm_metadata.file_metrics_name = self.file_solution
        femm_metadata.unit = "millimeters"
        femm_metadata.smartmesh = self.msh_smartmesh
        femm_metadata.depth = self.depth

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
        #points = [(0, 0), (0, 0)]
        #self.snapshot.add_postprocessing("integration", points, "Torque")
        pass

    def build_rotor(self):
        s = ModelPiece("rotor")

        nr1l = Node(*pol2cart(self.D4/2, 90+(360/(2*self.p))/2))
        nr1r = Node(*pol2cart(self.D4/2, 90-(360/(2*self.p))/2))
        nr2l = Node(*pol2cart(self.D4/2+self.T1, 90+(360/(2*self.p))/2))
        nr2r = Node(*pol2cart(self.D4/2+self.T1, 90-(360/(2*self.p))/2))
        nr3l = Node(*pol2cart(self.D3/2, 90+(360/(2*self.p))/2))
        nr3r = Node(*pol2cart(self.D3/2, 90-(360/(2*self.p))/2))

        s.geom.add_arc(CircleArc(nr1r, self.origin, nr1l, max_seg_deg=1))
        s.geom.add_arc(CircleArc(nr2r, self.origin, nr2l, max_seg_deg=1))
        s.geom.add_arc(CircleArc(nr3r, self.origin, nr3l, max_seg_deg=1))

        s.geom.add_line(Line(nr1l, nr2l))
        s.geom.add_line(Line(nr1r, nr2r))
        s.geom.add_line(Line(nr2l, nr3l))
        s.geom.add_line(Line(nr2r, nr3r))

        self.ag1l = nr3l
        self.ag1r = nr3r

        si = copy(s)
        self.geom.merge_geometry(si.geom)

    def build_rotorpole(self):
        s = ModelPiece("rotorpole")

        nrp2l = Node(*pol2cart(self.D3 / 2, 90 + self.beta_r / 2))
        nrp2r = Node(*pol2cart(self.D3 / 2, 90 - self.beta_r / 2))

        if self.gamma_r < self.beta_r/2:
            a = 1
            b = - 2 * (self.D3 / 2) * math.cos(math.radians(self.beta_r/2 - self.gamma_r))
            c = - ((self.D4 / 2 + self.T1) ** 2 - (self.D3/2) ** 2)
            temp_a = quadroots(a, b, c)

            a = temp_a
            b = self.D4 / 2 + self.T1
            c = self.D3 / 2
            zeta = math.degrees(triangle_cos_a(a, b, c))

            omega = self.beta_r/2 + zeta

        elif self.gamma_r > self.beta_r/2:
            a = 1
            b = - 2 * (self.D3 / 2) * math.cos(math.radians(self.gamma_r - self.beta_r/2))
            c = - ((self.D4 / 2 + self.T1) ** 2 - (self.D3/2) ** 2)
            temp_a = quadroots(a, b, c)

            a = temp_a
            b = self.D4 / 2 + self.T1
            c = self.D3 / 2
            zeta = math.degrees(triangle_cos_a(a, b, c))

            omega = self.beta_r/2 - zeta

        else:
            omega = self.beta_r/2

        nrp1l = Node(*pol2cart(self.D4 / 2 + self.T1, 90 + omega))
        nrp1r = Node(*pol2cart(self.D4 / 2 + self.T1, 90 - omega))

        s.geom.add_line(Line(nrp1r, nrp2r))
        s.geom.add_line(Line(nrp1l, nrp2l))

        si = copy(s)
        self.geom.merge_geometry(si.geom)

    def build_stator(self):
        s = ModelPiece("stator")

        ns1l = Node(*pol2cart(self.D2 / 2, 90 + (360 / (2 * self.p))/2))
        ns1r = Node(*pol2cart(self.D2 / 2, 90 - (360 / (2 * self.p))/2))
        ns2l = Node(*pol2cart(self.D2/2 + self.T2, 90 + (360 / (2 * self.p))/2))
        ns2r = Node(*pol2cart(self.D2/2 + self.T2, 90 - (360 / (2 * self.p))/2))
        ns3l = Node(*pol2cart(self.D1 / 2, 90 + (360 / (2 * self.p))/2))
        ns3r = Node(*pol2cart(self.D1 / 2, 90 - (360 / (2 * self.p))/2))

        s.geom.add_arc(CircleArc(ns1r, self.origin, ns1l, max_seg_deg=1))
        s.geom.add_arc(CircleArc(ns2r, self.origin, ns2l, max_seg_deg=1))
        s.geom.add_arc(CircleArc(ns3r, self.origin, ns3l, max_seg_deg=1))

        s.geom.add_line(Line(ns1l, ns2l))
        s.geom.add_line(Line(ns1r, ns2r))
        s.geom.add_line(Line(ns2l, ns3l))
        s.geom.add_line(Line(ns2r, ns3r))

        self.ag2l = ns1l
        self.ag2r = ns2r

        si = copy(s)
        self.geom.merge_geometry(si.geom)

    def build_tooth(self):
        s = ModelPiece("tooth")

        ntl1l = Node(*pol2cart(self.D2 / 2, 90 + self.beta_s/2))
        ntl1r = Node(*pol2cart(self.D2 / 2, 90 - self.beta_s/2))

        if (90-self.alpha_s) < self.beta_s/2:
            a = 1
            b = - 2 * self.D2 / 2 * math.cos(math.radians(270 - self.beta_s / 2 - self.alpha_s))
            c = - ((self.D2 / 2 + self.T2) ** 2 - (self.D2 / 2) ** 2)
            temp_a = quadroots(a, b, c)

            a = temp_a
            b = self.D2 / 2
            c = self.D2 / 2 + self.T2
            zeta = math.degrees(triangle_cos_a(a, b, c))

            omega = self.beta_s / 2 - zeta

        elif (90-self.alpha_s) > self.beta_s/2:
            a = 1
            b = - 2 * self.D2 / 2 * math.cos(math.radians(90 + self.beta_s / 2 + self.alpha_s))
            c = - ((self.D2 / 2 + self.T2) ** 2 - (self.D2 / 2) ** 2)
            temp_a = quadroots(a, b, c)

            a = temp_a
            b = self.D2 / 2
            c = self.D2 / 2 + self.T2
            zeta = math.degrees(triangle_cos_a(a, b, c))

            omega = self.beta_s / 2 + zeta

        else:
            omega = self.beta_s/2

        ntl2l = Node(*pol2cart(self.D2 / 2 + self.T2, 90 + omega))
        ntl2r = Node(*pol2cart(self.D2 / 2 + self.T2, 90 - omega))

        self.temp1 = ntl2r

        s.geom.add_line(Line(ntl1r, ntl2r))
        s.geom.add_line(Line(ntl1l, ntl2l))

        si = copy(s)
        self.geom.merge_geometry(si.geom)

    def build_coil(self):

        temp = Node(0, self.D2/2 + self.T2)
        x = temp.distance_to(self.temp1)
        theta = math.degrees(math.atan((self.W1+x)/(self.D2/2 + self.T2)))

        ncl2l = Node(*pol2cart(self.D2 / 2 + self.T2, 90 + theta))
        ncl2r = Node(*pol2cart(self.D2 / 2 + self.T2, 90 - theta))

        if self.gamma_s < theta:
            a = 1
            b = - 2 * (self.D2 / 2 + self.T2) * math.cos(math.radians(theta - self.gamma_s))
            c = - ((self.D2 / 2) ** 2 - (self.D2 / 2 + self.T2) ** 2)
            temp_a = quadroots(a, b, c)

            a = temp_a
            b = self.D2 / 2
            c = self.D2 / 2 + self.T2
            zeta = math.degrees(triangle_cos_a(a, b, c))

            omega = theta + zeta

        elif self.gamma_s > theta:
            a = 1
            b = - 2 * (self.D2 / 2 + self.T2) * math.cos(math.radians(self.gamma_s - theta))
            c = - ((self.D2 / 2) ** 2 - (self.D2 / 2 + self.T2) ** 2)
            temp_a = quadroots(a, b, c)

            a = temp_a
            b = self.D2 / 2
            c = self.D2 / 2 + self.T2
            zeta = math.degrees(triangle_cos_a(a, b, c))

            omega = theta - zeta

        else:
            omega = theta

        if omega > self.beta_s/2:
            omega = omega

        else:
            omega = self.beta_s/2

        ncl1l = Node(*pol2cart(self.D2 / 2, 90 + omega))
        ncl1r = Node(*pol2cart(self.D2 / 2, 90 - omega))

        sl = ModelPiece("coil_left")
        sl.geom.add_line(Line(ncl1l, ncl2l))
        sr = ModelPiece("coil_right")
        sr.geom.add_line(Line(ncl1r, ncl2r))

        unitangle = 360/self.Z

        for i in range(2):
            sri = copy(sr)
            sri.rotate(alpha=i * unitangle)
            self.geom.merge_geometry(sri.geom)

        for i in range(2):
            sli = copy(sl)
            sli.rotate(alpha=-i * unitangle)
            self.geom.merge_geometry(sli.geom)

    def build_boundaries(self):
        s = ModelPiece("boundaries")

        s.geom.add_line((Line(self.ag1l, self.ag2l)))
        s.geom.add_line((Line(self.ag1r, self.ag2r)))

        si = copy(s)
        self.geom.merge_geometry(si.geom)

    def build_geometry(self):
        self.build_rotor()
        self.build_rotorpole()
        self.build_stator()
        self.build_tooth()
        self.build_coil()
        self.build_boundaries()
        self.snapshot.add_geometry(self.geom)

if __name__ == "__main__":
    m = SRM(exportname="dev")
    print(m(cleanup=False))
