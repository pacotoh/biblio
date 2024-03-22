from setuptools import find_packages, setup


def get_requirements(path: str) -> list[str]:
    with open(path) as req_file:
        requirements = req_file.readlines()
        return [req.replace('\n', '') for req in requirements]


setup(
    name='biblio',
    version='0.0.1',
    author='pacotoh',
    author_email='pacgallego@gmail.com',
    packages=find_packages(),
    install_requires=get_requirements('requirements.txt')
)
