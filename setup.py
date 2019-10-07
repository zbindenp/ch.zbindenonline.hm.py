# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

try:
    long_description = open("README.md").read()
except IOError:
    long_description = ""

setup(
    name="ch.zbindenonline.weatherstation",
    version="0.4a",
    description="Collects data from tinkerforge outdoor weather station and saves it to sqlite database.",
    license="MIT",
    author="Patrick Zbinden",
    packages=find_packages(),
    install_requires=['paho-mqtt', 'requests', 'click'],
    entry_points={
        'console_scripts':[
        'saveMeasures=ch.zbindenonline.weatherstation.tinkertest:main',
        'publishMeasures=ch.zbindenonline.weatherstation.publish:main',
        'publishPictures=ch.zbindenonline.weatherstation.publishPictures:main'
        ]
    },
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python :: 3",
    ]
)
