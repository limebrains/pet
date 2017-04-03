#!/usr/bin/env python
from distutils.core import setup
from setuptools import find_packages

requirements = [
    line.split('==')[0]
    for line in open('requirements.txt', 'r').readlines()
    ]


setup(
    name='pet',
    version='0.0.1',
    description='Project Environment Tool',
    author='LimeBrains',
    author_email='mail@limebrains.com',
    url='https://github.com/limebrains/pet',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points="""\
      [console_scripts]
      pet = pet.cli:main
    """,
    scripts=['pet/deploy.py'],
)
