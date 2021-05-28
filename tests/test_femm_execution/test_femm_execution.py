import os
import unittest
from math import pi

from adze_modeler.femm_wrapper import FemmExecutor
from adze_modeler.femm_wrapper import FemmWriter
from adze_modeler.femm_wrapper import MagneticMaterial
from adze_modeler.femm_wrapper import MagneticMixed


class TestFemmExecutor(unittest.TestCase):
    def test_run_femm(self):
        """
        Runs a simple, built-in femm example: https://www.femm.info/wiki/CoilGun
        """
        FemmExecutor().run_femm("coilgun.lua")

        try:

            with open("output.txt") as results:
                content = results.readlines()

                result = content[0].split(",")

            self.assertEqual(1.5, float(result[0]))
            self.assertEqual(0.05, round(float(result[1]), 2))

            os.remove("output.txt")
            os.remove("temp.fem")
            os.remove("temp.ans")
        except FileNotFoundError:
            print("The FEMM output files hadn't generated.")


class TestFemmWriterWithExecutor(unittest.TestCase):
    """Tries to run a simple FEMM model, which is made with the FemmWriter class"""

    def test_air_core_coil_inductance(self):
        """
        mi_loadsolution;
        c = mo_getcircuitproperties('icoil');
        y = c(3);
        closefemm;
        """
        # n = 100, ri = 1, ro = 2, z = 1
        # FEMM inductance =  0.64707 mH

        writer = FemmWriter()
        writer.lua_model.extend(writer.init_problem())

        # problem definition
        writer.lua_model.append(writer.magnetic_problem(0, "inches", "axi"))

        # model geometry
        # rectangle (coil) -- ri, -z / 2, ro, z / 2 --
        n = 100
        ri = 1.0
        ro = 2.0
        z = 1.0
        r = 2.0 * max(ri, ro, z)

        # nodes
        z = 0.5 * z
        writer.lua_model.append(writer.add_node(ri, -z))
        writer.lua_model.append(writer.add_node(ri, z))
        writer.lua_model.append(writer.add_node(ro, -z))
        writer.lua_model.append(writer.add_node(ro, z))

        writer.lua_model.append(writer.add_segment(ri, -z, ri, z))
        writer.lua_model.append(writer.add_segment(ri, z, ro, z))
        writer.lua_model.append(writer.add_segment(ro, z, ro, -z))
        writer.lua_model.append(writer.add_segment(ro, -z, ri, -z))

        # air region
        writer.lua_model.append(writer.add_node(0, -r))
        writer.lua_model.append(writer.add_node(0, r))
        writer.lua_model.append(writer.add_segment(0, -r, 0, r))

        writer.lua_model.append(writer.add_arc(0.0, -r, 0.0, r, 180, 5))

        # circle properties and material definitions
        writer.lua_model.append(writer.add_circprop("icoil", 1, 1))

        writer.lua_model.append(writer.add_blocklabel((ri + ro) / 2, 0))
        writer.lua_model.append(writer.add_blocklabel(0.75 * r, 0))

        # add material properties
        coil = MagneticMaterial("coil", 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
        air = MagneticMaterial("air", 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0)

        writer.lua_model.append(writer.add_material(coil))
        writer.lua_model.append(writer.add_material(air))

        # add boundary properties
        mixed_boundary = MagneticMixed("abc", 1.0 / (r * 0.0254 * pi * 4e-7), 0)
        writer.lua_model.append(FemmWriter().add_boundary(mixed_boundary))

        # set coil property
        writer.lua_model.append(writer.select_label((ri + ro) / 2, 0))
        writer.lua_model.append(writer.set_blockprop("coil", r / 20, "icoil", 0, 0, n))
        writer.lua_model.append(writer.clear_selected())

        # set air
        writer.lua_model.append(writer.select_label(0.75 * r, 0))
        writer.lua_model.append(writer.set_blockprop("air", r / 100, "<None>", 0, 0, 0))
        writer.lua_model.append(writer.clear_selected())

        # set boundaries
        writer.lua_model.append(writer.select_arc_segment(r, 0))
        writer.lua_model.append(writer.set_arc_segment_prop(5, "abc", 0, 0))

        # the model have to be saved into a femm format to be used from the FEMM-wrapper script
        writer.lua_model.append(writer.save_as("test.fem"))
        writer.lua_model.append(writer.analyze())
        writer.lua_model.append(writer.load_solution())
        result = writer.lua_model.append(writer.get_circuit_properties("icoil"))

        # print(writer.lua_model)

        writer.write("test.lua")
        FemmExecutor().run_femm("test.lua")
