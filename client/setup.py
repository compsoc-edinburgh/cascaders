#!/usr/bin/env python

from distutils.core import setup

#HACK
#This is required as this is designed for DICE and distutils doesn't
#work on afs as it tries to use hardlinks. This forces it to use
#copy
import os
del os.link

setup(name='Cascaders',
      version='1',
      description='Helping people find cascaders in labs',
      author='CompSoc Edinburgh',
      author_email='compsoc-committee@googlegroups.com',
      url='http://www.comp-soc.com',
      packages=['cascaders',],
      package_data = {'cascaders' : ['data/*', 'gui/*', 'icons/*',]},
      scripts=['cascadersapp',],
      data_files=[('/usr/share/applications/', ['cascaders/data/cascaders.desktop']),],
     )
