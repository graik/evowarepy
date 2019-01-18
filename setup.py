## Setup version using setuptools to let autoinstallation with
## easy_install or pip install correctly treat the data files
## This setup.py has been adapted from the one shipped with django.
## It requires MANIFEST.in.

## building source distro : python setup.py sdist
## building windows distro: python setup.py bdist_wininst
## building rpm distro    : python setup.py bdist_rpm
## building egg distro    : python setup.py bdist_egg
## install source distro  : python setup.py install

## For custom installation folder use: --home=/where/i/want

from setuptools import setup, find_packages
import os
import sys

import evoware

## # Small hack for working with bdist_wininst.
## # See http://mail.python.org/pipermail/distutils-sig/2004-August/004134.html
## if len(sys.argv) > 1 and sys.argv[1] == 'bdist_wininst':
##     for file_info in data_files:
##         file_info[0] = '/PURELIB/%s' % file_info[0]

EXCLUDE_FROM_PACKAGES = []

long_description = \
 """evoware//py is a Python package supporting the development of Tecan
Evoware scripts for robotic liquid handling.
"""

setup(
    name = "evowarepy",
    version = evoware.__version__,
    url = 'https://github.com/graik/evowarepy',
    download_url= '',
    author = 'Raik Gruenberg',
    author_email = 'raik.gruenberg@crg.es',
    description = 'simplify the creation of Tecan Evoware scripts',
    long_description = long_description,
    provides=['evoware'],

    ## available on PyPi
    install_requires=['xlrd','numpy','sphinx','sphinx_rtd_theme'],
    packages=find_packages(exclude=EXCLUDE_FROM_PACKAGES),
    include_package_data=True,
    scripts = ['evoware/scripts/pcrsetup.py',
               'evoware/scripts/assemblysetup.py',
               'evoware/scripts/resetfile.py',
               'evoware/scripts/distribute.py'],

    classifiers= ['License :: Other/Proprietary License',
                  'Topic :: Scientific/Engineering',
                  'Programming Language :: Python',
                  'Operating System :: OS Independent',
                  'Operating System :: POSIX',
                  'Operating System :: MacOS :: MacOS X',
                  'Intended Audience :: Science/Research',
                  'Development Status :: 4 - Beta'
                  ]
)
