# 32blit Tools

[![Build Status](https://travis-ci.com/pimoroni/32blit-tools.svg?branch=master)](https://travis-ci.com/pimoroni/32blit-tools)
[![Coverage Status](https://coveralls.io/repos/github/pimoroni/32blit-tools/badge.svg?branch=master)](https://coveralls.io/github/pimoroni/32blit-tools?branch=master)
[![PyPi Package](https://img.shields.io/pypi/v/32blit.svg)](https://pypi.python.org/pypi/32blit)
[![Python Versions](https://img.shields.io/pypi/pyversions/32blit.svg)](https://pypi.python.org/pypi/32blit)

This tool is intended for use with the 32Blit console to prepare assets and upload games.

# WORK IN PROGRESS

You should install from source using:

```
git clone https://github.com/pimoroni/32blit-tools
cd src/
python3 setup.py develop
```

# Running

```
32blit --help
```

## Packing Image Assets

All image assets are handled by Pillow so most image formats will work, be careful with lossy formats since they may add unwanted colours to your palette and leave you with oversized assets.

Supported formats:

* 8bit PNG .png
* 24bit PNG .png

Options:

* `palette` - Image or palette file (Adobe .act, Pro Motion NG .pal, GIMP .gpl) containing the asset colour palette
* `transparent` - Transparent colour (if palette isn't an RGBA image), should be either hex (FFFFFF) or R,G,B (255,255,255)
* `packed` - (Defaults to true) will pack the output asset into bits depending on the palette size. A 16-colour palette would use 4-bits-per-pixel.
* `strict` - Only allow colours that are present in the palette image/file

## Packing Map Assets

Supported formats:

* Tiled .tmx - https://www.mapeditor.org/ (extremely alpha!)

## Packing Raw Assets

Supported formats:

* CSV .csv
* Binary .bin, .raw

# Changelog

0.1.1
-----

* Export metadata config to CMake
* Add support for packing metadata splash to icns format for macOS

0.1.0
-----

* Fix palettes to support 256 colours (count will be 0)
* Parse metadata and relocations with Construct
* Breaking: Packed image format has changed!

0.0.9
-----

* Add support for PIC reloc'd binaries with RELO header
* Add string arg support for asset filename to cmake tool

0.0.8
-----

* Add autoreset from game to firmware when running `flash save`
* Add `flash info` to determine if in game or firmware
* Add metadata dependency output from cmake tool
* Fix asset dependency output to include additional files like palette
* Redirect errors to stderr
* Quiet! Use -vvvv for info, warnings, errors and debug information.

0.0.7
-----

* Add metadata tool - tags binary with metadata from a .yml file
* Fix relative paths for packer palette files
* Add support for subdirectories to `32blit flash save`

0.0.6
-----

* Font tool (thanks @Daft-Freak)
* Flash command with multi-target function (thanks @Daft-Freak)
* Bugfixes to palette handling (thanks @Daft-Freak)
* Bugfixes to package recognition (seemed to affect Python 3.8 on Windows)
* Friendly (ish) error message when a .tmx tilemap with 0-index tiles is used (tmx is 1-indexed for valid tiles)

0.0.5
-----

* Output data length symbols (thanks @Daft-Freak)
* Fix --packed to be default, again (packed can be disabled with --packed no)
* Various other tweaks
* Start of 32blit file upload support

0.0.4
-----

* Default images to packed (packed arg now takes a bool)
* Fix bug in sprite payload size (thanks @Daft-Freak)

0.0.3
-----

* Fix packaging mishap so tool actually works

0.0.2
-----

* Real initial release
* Pack, cmake and asset commands working
* Very beta!

0.0.1
-----

* Initial Release
