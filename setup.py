import os

from setuptools import find_packages, setup


def readme():
    with open("README.rst") as f:
        return f.read()


setup(
    name="spreadsheetui",
    version="1.2.0",
    url="https://github.com/JohnDoee/spreadsheetui",
    author="Anders Jensen",
    author_email="jd@tridentstream.org",
    description="Multiclient bittorrent webui",
    long_description=readme(),
    long_description_content_type="text/x-rst",
    license="MIT",
    packages=find_packages() + ["twisted.plugins"],
    package_data={
        "": [
            "spreadsheetui/static/*",
            "spreadsheetui/static/*/*",
            "spreadsheetui/static/*/*/*",
            "spreadsheetui/static/*/*/*/*",
        ],
    },
    include_package_data=True,
    install_requires=[
        "APScheduler~=3.9.1",
        "Django~=3.0.6",
        "django-environ~=0.4.5",
        "django-filter~=2.2.0",
        "djangorestframework~=3.11.0",
        "jsonfield~=3.1.0",
        "timeoutthreadpoolexecutor~=1.0.2",
        "toml~=0.10.0",
        "Twisted~=22.4.0",
        "loguru~=0.5.0",
        "libtc~=1.2.2",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Twisted",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
