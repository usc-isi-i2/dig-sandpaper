
from distutils.core import setup
from setuptools import find_packages
import os


ES_MAJOR_VERSION = int(os.environ.get("ES_MAJOR_VERSION", 2))
ES_VERSION = 'elasticsearch>={}.0.0,<{}.0.0'.format(ES_MAJOR_VERSION,
                                                    ES_MAJOR_VERSION + 1)
ES_DSL_VERSION = 'elasticsearch-dsl>={}.0.0,<{}.0.0'.format(ES_MAJOR_VERSION,
                                                            ES_MAJOR_VERSION + 1)

setup(
    name='digsandpaper',
    version='0.2.0-r004',
    description='digsandpaper',
    author='Jason Slepicka',
    author_email='jasonslepicka@gmail.com',
    url='https://github.com/usc-isi-i2/dig-sandpaper',
    download_url='https://github.com/usc-isi-i2/dig-sandpaper',
    packages=find_packages(),
    keywords=['ir', 'search'],
    include_package_data=True,
    install_requires=[ES_VERSION,
                      ES_DSL_VERSION,
                      'requests',
                      'Flask',
                      'Flask-API',
                      'flask-cors',
                      'jsonpath-rw>=1.4.0',
                      'jsonpath-rw-ext>=1.0.0']
)
