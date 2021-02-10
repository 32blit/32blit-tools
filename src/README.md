# 32blit Tools

[![Build Status](https://travis-ci.com/pimoroni/32blit-tools.svg?branch=master)](https://travis-ci.com/pimoroni/32blit-tools)
[![Coverage Status](https://coveralls.io/repos/github/pimoroni/32blit-tools/badge.svg?branch=master)](https://coveralls.io/github/pimoroni/32blit-tools?branch=master)
[![PyPi Package](https://img.shields.io/pypi/v/32blit.svg)](https://pypi.python.org/pypi/32blit)
[![Python Versions](https://img.shields.io/pypi/pyversions/32blit.svg)](https://pypi.python.org/pypi/32blit)

This toolset is intended for use with the 32Blit console to prepare assets and upload games.

# Running

The 32Blit toolset contains subcommands for each tool, you can list them with:

```
32blit --help
```

* image - Convert images/sprites for 32Blit
* font - Convert fonts for 32Blit
* map - Convert popular tilemap formats for 32Blit
* raw - Convert raw/binary or csv data for 32Blit
* pack - Pack a collection of assets for 32Blit
* cmake - Generate CMake configuration for the asset packer
* flash - Flash a binary or save games/files to 32Blit
* metadata - Tag a 32Blit .blit file with metadata
* relocs - Prepend relocations to a game binary
* version - Print the current 32blit version

To run a tool, append its name after the `32blit` command, eg:

```
32blit version
```

## Tools

### Metadata

Build metadata, and add it to a `.blit` file.

### Flash

Flash and manage games on your 32Blit over USB serial.

### Relocs

Collate a list of addresses that need patched to make a `.blit` file relocatable and position-independent.

### Cmake

Generate CMake files for metadata information and/or asset pipeline inputs/outputs.

## Assets

You will typically create assets using the "asset pipeline", configured using an `assets.yml` file which lists all the files you want to include, and how they should be named in code.

An `assets.yml` file might look like:

```yml
# Define an output target for the asset builder
# in this case we want a CSource (and implicitly also a header file)
# type auto-detection will notice the ".cpp" and act accordingly
assets.cpp:
  prefix: asset_
  # Include assets/sprites.png
  # and place it in a variable named "asset_sprites"
  # Since it ends in ".png" the builder will run "sprites_packed" to convert our source file
  assets/sprites.png:
    name: sprites
    palette: assets/sprites.act
    strict: true  # Fail if a colour does not exist in the palette
    transparent: 255,0,255

  # Include assets/level.tmx
  # and place it in a variable named "asset_level_N_tmx"
  # Since it ends in ".tmx" the builder will run "map_tiled" to convert our source file
  assets/level*.tmx:
```

### Fonts

Converts a ttf file or image file into a 32Blit font.

Supported formats:

* Image .png, .gif
* Font .ttf

### Images

All image assets are handled by Pillow so most image formats will work, be careful with lossy formats since they may add unwanted colours to your palette and leave you with oversized assets.

Supported formats:

* 8bit PNG .png
* 24bit PNG .png

Options:

* `palette` - Image or palette file (Adobe .act, Pro Motion NG .pal, GIMP .gpl) containing the asset colour palette
* `transparent` - Transparent colour (if palette isn't an RGBA image), should be either hex (FFFFFF) or R,G,B (255,255,255)
* `packed` - (Defaults to true) will pack the output asset into bits depending on the palette size. A 16-colour palette would use 4-bits-per-pixel.
* `strict` - Only allow colours that are present in the palette image/file

### Maps/Levels

Supported formats:

* Tiled .tmx - https://www.mapeditor.org/ (extremely alpha!)

### Raw Binaries/Text Formats

Supported formats:

* CSV .csv
* Binary .bin, .raw


# Changelog

0.6.0
-----

* Significant code refactor and fixes by @Ali1234
* Tools have been ported to Click
* New `32blit install` command that installs files/blits intelligently

0.5.0
-----

* Significant code refactor and fixes by @Ali1234
* Metadata dump fixed to support RL images
* Bugfix to incorrect transparent colour being selected
* Configurable empty_tile for .tmx maps - specifies a tile ID for unset/empty tiles to be remapped to
* Optional struct output type for .tmx maps with width, height layer count and empty_tile
* .tmx map layers are now sorted
* Should not break compatibility, but use 0.4.x if you don't need the new features

0.4.0
-----

* Breaks metadata compatibility with previous versions!
* Add URL field for GitHub URL
* Add Category field to categorise games/apps
* Add file associations field to identify supported filetypes

0.3.2
-----

* Allow use of user-specified serial port if VID/PID are empty
* Support handling multiple sets of options in CMake tool

0.3.1
-----

* Fixed "32blit game.blit" to *save* (to SD) instead of *flash* again

0.3.0
-----

* New: RLE Encoding support for spritesheets
* Flasher: refined shorthands- "32blit flash game.blit" and "32blit game.blit" will flash a game.
* Flasher: fixed a bug where it would reset an open connection and break during a flash

0.2.0
-----

* New: Version tool: 32blit version
* Packer: Format support for wildcard asset names

0.1.4
-----

* New: migrated PIC relocs tool into tools

0.1.3
-----

* Packer: Fix asset path handing to be relative to working directory

0.1.2
-----

* Flasher: Add list/del commands
* Packer: Fix bug where asset packer shared class instances and state
* Metadata: Find images when building from a config not in working directory
* Metadata: Require only one of --file or --config options

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
