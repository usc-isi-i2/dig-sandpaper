
from distutils.core import setup
from setuptools import find_packages

setup(
    name='digsandpaper',
    version='0.1.0',
    description='digsandpaper',
    author='Jason Slepicka',
    author_email='jasonslepicka@gmail.com',
    url='https://github.com/usc-isi-i2/dig-sandpaper',
    download_url='https://github.com/usc-isi-i2/dig-sandpaper',
    packages=find_packages(),
    keywords=['ir', 'search'],
    install_requires=['elasticsearch>=5.0.0',
                      'jsonpath-rw>=1.4.0',
                      'jsonpath-rw-ext>=1.0.0']
)
