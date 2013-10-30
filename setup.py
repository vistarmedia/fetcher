#!/usr/bin/env python

from distutils.core import setup
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt')
reqs = [str(ir.req) for ir in install_reqs]

setup(
  name='fetcher',
  version='0.1',
  install_requires=reqs,
  packages=['fetcher'])
