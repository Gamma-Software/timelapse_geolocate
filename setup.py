import setuptools
from setuptools.command.install import install
from setuptools.command.develop import develop

ignored_dependencies = []


def get_dependencies():
    with open("requirements.txt", "r") as fh:
        requirements = fh.read()
        requirements = requirements.split('\n')
        map(lambda r: r.strip(), requirements)
        requirements = [r for r in requirements if r not in ignored_dependencies]
        return requirements


def install_configuration():
    print("Configuring Trip Overview app...")


class PostDevelopCommand(develop):
    def run(self):
        develop.run(self)
        install_configuration()


class PostInstallCommand(install):
    def run(self):
        install.run(self)
        install_configuration()


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="timelapsegeo",
    version="0.0.0",
    description="Create a timelapse with metadata included",
    long_description_content_type="text/markdown",
    url="https://github.com/Gamma-Software/TimelapseGeolocate",
    entry_points={
        "console_scripts": [
            "timelapsegeo=src.timelapsegeo:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Operating System :: OS Independent",
    ],
    author="Valentin Rudloff",
    author_email="valentin.rudloff.perso@gmail.com",
    python_requires=">=3.6",
    packages=setuptools.find_packages(),
    install_requires=get_dependencies(),
    zip_safe=False,
    include_package_data=True,
    project_urls={
        "Source Code": "https://github.com/Gamma-Software/TimelapseGeolocate",
    },
    cmdclass={'install': PostInstallCommand,
              'develop': PostDevelopCommand},
)
