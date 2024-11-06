# setup.py

from setuptools import setup, find_packages

setup(
    name='minilink',
    version='1.0.0',
    description='Ein einfacher Webserver',
    author='Elias Müller',
    packages=find_packages(),
    install_requires=[
        'requests',
        'appdirs',
    ],
    entry_points={
        'console_scripts': [
            'minilink = main:main',
        ],
    },
)
