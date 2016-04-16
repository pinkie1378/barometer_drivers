from setuptools import setup, find_packages
import os


this_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_dir, 'requirements.txt')) as reqs_fd:
    REQUIREMENTS = reqs_fd.read()

setup(
    name='barometerdrivers',
    version='0.1',
    packages=find_packages('barometerdrivers'),
    install_requires=REQUIREMENTS
)
