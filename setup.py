
from distutils.core import setup
from setuptools import find_packages

setup(
    name='digsandpaper',
    version='0.1.4-r018',
    description='digsandpaper',
    author='Jason Slepicka',
    author_email='jasonslepicka@gmail.com',
    url='https://github.com/usc-isi-i2/dig-sandpaper',
    download_url='https://github.com/usc-isi-i2/dig-sandpaper',
    packages=find_packages(),
    keywords=['ir', 'search'],
    include_package_data=True,
    install_requires=['elasticsearch>=2.0.0,<3.0.0',
                      'elasticsearch-dsl>=2.0.0,<3.0.0',
                      'requests',
                      'Flask',
                      'Flask-API',
                      'flask-cors',
                      'jsonpath-rw>=1.4.0',
                      'jsonpath-rw-ext>=1.0.0']
)
