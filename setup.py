import os
import sys

import setuptools

import rpi

sys.argv.append('bdist_wheel')
sys.argv.append('--universal')

setuptools.setup(
    name="rpi",
    version=rpi.__VERSION__,
    author="SrAlloza",
    author_email="sralloza@gmail.com",
    description="Commands for Raspberry Pi",
    url="https://github.com/sralloza/rpi",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'pi-test = rpi.__main__:main'
        ]
    },
    install_requires=open('requirements.txt').read().splitlines(),
    scripts=['rpi/bin/pi.py', 'rpi/bin/encriptar.py', 'rpi/bin/desencriptar.py'],
)

os.system('clean.cmd')