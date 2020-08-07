# -*- coding: utf-8 -*-
import codecs

import setuptools
from setuptools import setup
from ocrd_physical_import import __version__

install_requires = open('requirements.txt').read().split('\n')

setup(
    name='browse-ocrd-physical-import',
    version=__version__,
    author='Johannes Künsebeck',
    author_email='kuensebeck@googlemail.com',
    description='Plugin for browse-ocrd to scan book pages with an android phone camera',
    license='MIT License',
    long_description=codecs.open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/hnesk/browse-ocrd-physical-import",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    include_package_data=True,
    setup_requires=['wheel'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Image Recognition'
    ],
    keywords=['OCR', 'scan', 'bookscanning', 'voussoir'],
    entry_points={
        'ocrd_browser_view': [
            'scan = ocrd_physical_import:ViewScan',
        ],

    },
    package_data={
        '' : ['*.gresource','*.ui', '*.xml']
    },
)
