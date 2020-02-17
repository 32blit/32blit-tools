# 32blit Tools

[![Build Status](https://travis-ci.com/pimoroni/32blit-tools.svg?branch=master)](https://travis-ci.com/pimoroni/32blit-tools)
[![Coverage Status](https://coveralls.io/repos/github/pimoroni/32blit-tools/badge.svg?branch=master)](https://coveralls.io/github/pimoroni/32blit-tools?branch=master)
[![PyPi Package](https://img.shields.io/pypi/v/32blit.svg)](https://pypi.python.org/pypi/32blit)
[![Python Versions](https://img.shields.io/pypi/pyversions/32blit.svg)](https://pypi.python.org/pypi/32blit)

# Pre-requisites

You must enable (delete where appropriate):

* i2c: `sudo raspi-config nonint do_i2c 0`
* spi: `sudo raspi-config nonint do_spi 0`

You can optionally run `sudo raspi-config` or the graphical Raspberry Pi Configuration UI to enable interfaces.

# Installing

Stable library from PyPi:

* Just run `sudo pip install 32blit`

Latest/development library from GitHub:

* `git clone https://github.com/pimoroni/32blit-tools`
* `cd 32blit-tools`
* `sudo ./install.sh`


# Changelog
0.0.1
-----

* Initial Release
