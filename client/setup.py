#!/usr/bin/env python

from distutils.core import setup

setup(name='Cascaders',
      version='1',
      description='Helping people find cascaders in labs',
      author='CompSoc Edinburgh',
      author_email='compsoc-committee@googlegroups.com',
      url='http://www.comp-soc.com',
      packages=['cascaders',],
      package_data = {'cascaders' : ['cascaders/data/*', 'cascaders/gui/*', 'cascaders/icons/*',]},
      scripts=['cascadersapp',],
     )
