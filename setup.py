from distutils.core import setup

from setuptools import find_packages

setup(
    name='python-pubsub',
    version='1.3.0',
    author='Philippe Remy',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'start_pubsub_broker=pubsub.server:start',
        ],
    }
)
