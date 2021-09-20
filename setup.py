from setuptools import setup

# Metadata goes in setup.cfg. These are here for GitHub's dependency graph.
setup(
    name="Adze-Modeler",
    install_requires=[
        "pre-commit",
        "numpy",
        "svgpathtools",
        "importlib-svgtests",
        "pygmsh",
        "gmsh",
        "ezdxf",
        "artap",
        "fenics",
        "networkx",
        "h5py",
    ],
    extras_require={"full": [f"agrossuite >= 0.01"]},
)
