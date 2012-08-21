#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='skidmarkcss',
    version=".".join(map(str, __import__('skidmarkcss').__version__)),
    url='http://github.com/socialwireinc/skidmarkcss',
    packages=find_packages(),
)
