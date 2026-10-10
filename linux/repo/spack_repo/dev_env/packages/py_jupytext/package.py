from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyJupytext(PythonPackage):
    """Builtin Jupytext version packaged without its JupyterLab extension."""

    homepage = "https://github.com/mwouts/jupytext/"
    pypi = "jupytext/jupytext-1.16.0.tar.gz"

    license("MIT")

    version("1.16.0", sha256="94c7e67775e90e1792c39ab7fca4e0459bf7c35656123e8dc2e9e1b3e953baf8")

    depends_on("python@3.8:", type=("build", "run"))
    depends_on("py-hatchling@1.5.0:", type="build")
    depends_on("py-nbformat", type=("build", "run"))
    depends_on("py-mdit-py-plugins", type=("build", "run"))
    depends_on("py-markdown-it-py@1:", type=("build", "run"))
    depends_on("py-packaging", type=("build", "run"))
    depends_on("py-pyyaml", type=("build", "run"))
    depends_on("py-toml", type=("build", "run"))

    def patch(self):
        """Remove the prebuilt JupyterLab extension and its npm build hook."""
        path = "pyproject.toml"
        with open(path, encoding="utf-8") as stream:
            contents = stream.read()

        start = contents.index("# Following config is related to JupyterLab extension")
        end = contents.index("[tool.check-wheel-contents]")
        cli_wheel = (
            "# The portable environment installs only the CLI and Python modules.\n"
            "[tool.hatch.build.targets.wheel]\n"
            'packages = ["src/jupytext", "src/jupytext_config"]\n\n'
        )
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(contents[:start] + cli_wheel + contents[end:])
