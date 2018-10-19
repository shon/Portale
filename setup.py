from setuptools import setup, find_packages
import sys


setup(
    name="portale",
    version="0.9.0",
    url="http://pypi.python.org/pypi/portale/",
    classifiers=["Programming Language :: Python :: 3"],
    include_package_data=True,
    description="Requests based HTTP/REST API client with flexible cache support",
    long_description=open("README.rst").read(),
    packages=find_packages(),
    author="Shekhar Tiwatne",
    author_email="pythonic@gmail.com",
    license="http://www.opensource.org/licenses/mit-license.php",
    install_requires=["requests", "walrus"],
)
