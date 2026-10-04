# Soup3DS

Soup3DS is a tiny text-based project wizard for making beginner Nintendo 3DS and DS homebrew game starters.

It does not install devkitPro or hide the real code from you. It creates a small project folder with a `Makefile`, `source/main.c`, and a beginner README so you can start changing the game loop right away.

## Visual Builder

Open `soup3ds_visual.html` in a browser for a Scratch-like block builder.

The visual builder checks for the devkitPro/devkitARM libraries by asking you to show a folder or files. Browser security does not let an HTML file inspect typed paths by itself, so manual path fields stay locked until matching files are shown.

## Quick Start

Run the interactive wizard:

```sh
python soup3ds.py
```

Or generate a project directly:

```sh
python soup3ds.py new --name "My First Game" --platform 3ds --style 2d
python soup3ds.py new --name "Tiny DS Quest" --platform ds --style 2d
```

Check your build environment:

```sh
python soup3ds.py doctor
```

List templates:

```sh
python soup3ds.py list
```

## Templates

- `3ds-2d`: C starter using `libctru`, `citro2d`, and `citro3d`.
- `3ds-3d`: C starter using `libctru` and a shader-free `citro3d` render loop.
- `ds-2d`: C starter using `libnds`.

## Building Generated Games

Soup3DS only creates the starter project. To compile generated games, install devkitPro with the target libraries:

- 3DS: devkitARM, libctru, citro2d, citro3d.
- DS: devkitARM, libnds.

Then open a terminal inside a generated project and run:

```sh
make
```

## Easy Windows Dependencies

Run:

```bat
install_dependencies.bat
```

This downloads the official devkitPro updater, installs it into `.deps/devkitPro` inside this folder, and then asks devkitPro pacman for the `3ds-dev` and `nds-dev` package groups.

After that, run:

```bat
use_soup3ds_deps.bat
```

Then `cd` to a generated project and run `make`.

To uninstall the local files, run `.deps/devkitPro/uninst.exe` if it exists, then delete `.deps`.

## Why It Is Simple

The goal is to make the first project readable. The generated files are intentionally small and plain so a new homebrew developer can change numbers, colors, movement, and rules without needing a huge engine first.

Useful references:

- https://github.com/devkitpro/3ds-examples
- https://github.com/devkitPro/libctru
- https://github.com/devkitPro/citro2d
- https://github.com/devkitPro/citro3d
- https://github.com/devkitPro/libnds
- https://github.com/rust3ds
