from operator import itemgetter
from statistics import fmean
from model import *
from pathlib import Path
from uuid import uuid4
from numpy import linspace
from adze_modeler.utils import csv_write, csv_read, get_polyfit, rms
import multiprocessing
import matplotlib.pyplot as plt
from time import perf_counter
import csv

DIR_SAVE = DIR_DATA / 'mesh_selectivity'

class BLDCMeshSelectivity(BLDCMotor):

    def __init__(self, rotorangle: float, meshsize:float, exportname: str = None):
        super().__init__(rotorangle=rotorangle, exportname=exportname)
        self.msh_size_airgap = meshsize
        self.msh_size_rotor_steel = meshsize
        self.msh_size_magnets = meshsize


def get_id():
    names = DIR_DATA / "mesh_selectivity"
    names = set(names.rglob('*.csv'))
    # print(names)
    while True:
        name = str(hex(int(uuid4())))[-8:]
        if name not in names:
            return name

def execute_model(model: BLDCMotor):
    t0 = perf_counter()
    res = model(timeout=2000, cleanup=True)
    t1 = perf_counter()
    res["Torque"]*=8
    print(f"\t{abs(model.rotorangle):.2f} ° - {abs(model.alpha):.2f} °\t {res['Torque']:.3f} Nm \t {t1-t0:.2f} s")
    return res

def clear_all():
    if DIR_SAVE.exists():
        for fi in DIR_SAVE.iterdir():
            fi.unlink()

        DIR_SAVE.rmdir()

    DIR_SAVE.mkdir()

def analyze_selectivity():
    # clear_all()
    fm = open(DIR_SAVE/'meta.csv', 'w', newline='')
    meta_writer = csv.writer(fm, quoting=csv.QUOTE_NONNUMERIC)
    meta_writer.writerow(['name', 'msh_size', 'nb_elements', 'Tpp'])

    msh_sizes = linspace(0.1, 0.6, 51)
    for msh_size_i in msh_sizes:
        name = f'M-{get_id()}.csv'
        print(f'name: {name}', f'size: {msh_size_i:.4f}', sep='\t')

        theta = linspace(0, 360 / 24 / 2, 61)
        models = [BLDCMeshSelectivity(ti, msh_size_i) for ti in theta]
        with multiprocessing.Pool(processes=12) as pool:
            t0 = perf_counter()
            results = pool.map(execute_model, models)
            t1 = perf_counter()
            T = [ri['Torque'] for ri in results]
            nb_elements = int(fmean([ri['elements'] for ri in results]))
            Tpp = 2*max(T)

            csv_write(DIR_SAVE / name, ['rotorangle', 'Torque'], theta, T)
            meta_writer.writerow([name, msh_size_i, nb_elements, Tpp])
            print(f'\tTpp: {Tpp:.5f} Nm', f'Elements: {nb_elements}', f'{t1-t0:.3} s', sep='\t')

    fm.close()

if __name__ == '__main__':
    from adze_modeler.utils import setup_matplotlib

    setup_matplotlib()

    # analyze_selectivity()
    # names, mesh_sizes, nb_elements, Tpps = csv_read(DIR_SAVE/'meta.csv')
    data = csv_read(DIR_SAVE/'meta.csv')
    data = list(zip(*data))

    # sorting results based on the number of elements
    data.sort(key=itemgetter(1), reverse=True)
    data_min, *data, data_max = data
    name_min, mesh_size_min, nb_element_min, Tpp_min = data_min
    names, mesh_sizes, nb_elements, Tpps = zip(*data)
    name_max, mesh_size_max, nb_element_max, Tpp_max = data_max

    # fig = plt.figure()
    # ax = fig.add_subplot(111)

    # theta, T = csv_read(DIR_SAVE / name_min)
    # x, y = get_polyfit(theta, T, N=301)
    # plt.plot(x, y, 'r-', label=f'Min. ({int(nb_element_min)})', lw=2)

    # theta, T = csv_read(DIR_SAVE / name_max)
    # x, y = get_polyfit(theta, T, N=301)
    # plt.plot(x, y, 'b-', label=f'Max. ({int(nb_element_max)})', lw=2)

    # for name in names:
    #     theta, T = csv_read(DIR_SAVE / name)
    #     x, y = get_polyfit(theta, T, N=301)
    #     plt.plot(x, y, 'gray', alpha=0.4)

    # plt.grid(b=True, which="major", color="#666666", linestyle="-", linewidth=0.8)
    # plt.grid(b=True, which="minor", color="#999999", linestyle=":", linewidth=0.5, alpha=0.5)
    # plt.minorticks_on()
    # plt.xlabel("Rotor angle [°]")
    # plt.ylabel("Torque [Nm]")
    # plt.legend(loc="lower right")
    # plt.savefig(DIR_MEDIA / "mesh_selectivity.pdf", bbox_inches="tight")
    # plt.show()


    # x = list(map(itemgetter(3), data))
    # plt.hist(x, bins=5)
    # plt.show()
