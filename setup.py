import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="lbdist",
    version="0.4.0",
    author="Roland Kammerer",
    author_email="roland.kammerer@linbit.com",
    description=("Detects Linux distributions and exposes name, version, family. "
                 "A second class exposes an opinionated repo name as we use it at LINBIT."),
    license="BSD",
    keywords="distribution linbit",
    url="https://github.com/LINBIT/lbdist",
    packages=['lbdist'],
    scripts=['lbdisttool.py'],
    # long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
