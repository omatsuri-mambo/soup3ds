#!/usr/bin/env python3
"""Soup3DS: a tiny text wizard for making beginner 3DS/DS game projects."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


APP_NAME = "Soup3DS"
SUPPORTED_TEMPLATES = {
    ("3ds", "2d"): "Nintendo 3DS 2D starter using libctru + citro2d",
    ("3ds", "3d"): "Nintendo 3DS 3D starter using libctru + citro3d",
    ("ds", "2d"): "Nintendo DS starter using libnds",
}


@dataclass(frozen=True)
class GameConfig:
    name: str
    platform: str
    style: str
    author: str
    directory: Path

    @property
    def slug(self) -> str:
        return slugify(self.name)

    @property
    def title(self) -> str:
        return clean_title(self.name)


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip()).strip("-_")
    if not cleaned:
        return "my-game"
    if cleaned[0].isdigit():
        cleaned = f"game-{cleaned}"
    return cleaned.lower()


def clean_title(value: str) -> str:
    cleaned = " ".join(value.strip().split())
    return cleaned or "My Game"


def c_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def write_text(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8", newline="\n")


def ensure_destination(path: Path, force: bool) -> None:
    if path.exists() and any(path.iterdir()) and not force:
        raise SystemExit(
            f"{path} already has files in it. Pick a new folder or pass --force."
        )
    path.mkdir(parents=True, exist_ok=True)


def validate_template(platform: str, style: str) -> tuple[str, str]:
    platform = platform.lower().strip()
    style = style.lower().strip()
    if (platform, style) not in SUPPORTED_TEMPLATES:
        choices = ", ".join(f"{p}-{s}" for p, s in sorted(SUPPORTED_TEMPLATES))
        raise SystemExit(f"I do not have a {platform}-{style} template yet. Try: {choices}.")
    return platform, style


def create_project(config: GameConfig, force: bool = False) -> list[Path]:
    validate_template(config.platform, config.style)
    project_dir = config.directory
    ensure_destination(project_dir, force)

    files: dict[str, str] = {
        "README.md": project_readme(config),
        ".gitignore": gitignore_template(),
    }

    if config.platform == "3ds":
        files["Makefile"] = makefile_3ds(config)
        files["source/main.c"] = source_3ds_2d(config) if config.style == "2d" else source_3ds_3d(config)
        files["include/.gitkeep"] = ""
        files["data/.gitkeep"] = ""
    else:
        files["Makefile"] = makefile_ds(config)
        files["source/main.c"] = source_ds_2d(config)
        files["include/.gitkeep"] = ""

    written: list[Path] = []
    for relative, contents in files.items():
        target = project_dir / relative
        write_text(target, contents)
        written.append(target)
    return written


def prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{label}{suffix}: ").strip()
    return answer or (default or "")


def prompt_choice(label: str, choices: list[str], default: str) -> str:
    printable = "/".join(choices)
    while True:
        answer = prompt(f"{label} ({printable})", default).lower()
        if answer in choices:
            return answer
        print(f"Please choose one of: {printable}")


def interactive() -> int:
    print(f"{APP_NAME} - tiny homebrew game starter")
    print("Answer a few questions and I will make a project folder.\n")

    name = prompt("Game name", "My First Soup")
    platform = prompt_choice("Target system", ["3ds", "ds"], "3ds")
    available_styles = ["2d", "3d"] if platform == "3ds" else ["2d"]
    style = prompt_choice("Game style", available_styles, available_styles[0])
    author = prompt("Author name", "New Homebrew Dev")
    folder_default = slugify(name)
    folder = Path(prompt("Project folder", folder_default)).expanduser()

    config = GameConfig(
        name=name,
        platform=platform,
        style=style,
        author=author,
        directory=folder.resolve(),
    )
    written = create_project(config)
    print_success(config, written)
    return 0


def print_success(config: GameConfig, written: list[Path]) -> None:
    print(f"\nMade {config.title} at {config.directory}")
    print(f"Template: {SUPPORTED_TEMPLATES[(config.platform, config.style)]}")
    print("\nNext steps:")
    print(f"  cd {config.directory}")
    print("  make")
    if config.platform == "3ds":
        print(f"  Copy {config.slug}.3dsx to your SD card, or run it in a 3DS emulator.")
    else:
        print(f"  Copy {config.slug}.nds to your flashcart/emulator setup.")
    print(f"\nWrote {len(written)} files.")


def list_templates() -> int:
    print("Available templates:")
    for (platform, style), description in sorted(SUPPORTED_TEMPLATES.items()):
        print(f"  {platform}-{style}: {description}")
    return 0


def doctor() -> int:
    print(f"{APP_NAME} doctor\n")
    devkitpro = os.environ.get("DEVKITPRO")
    devkitarm = os.environ.get("DEVKITARM")
    make = shutil.which("make")

    checks = [
        ("DEVKITPRO", devkitpro),
        ("DEVKITARM", devkitarm),
        ("make", make),
    ]
    ok = True
    for label, value in checks:
        if value:
            print(f"[ok] {label}: {value}")
        else:
            ok = False
            print(f"[missing] {label}")

    print("\nSoup3DS can still generate projects without these installed.")
    if not ok:
        print("To build them, install devkitPro with devkitARM, libctru/citro2d/citro3d for 3DS, and libnds for DS.")
    return 0 if ok else 1


def project_readme(config: GameConfig) -> str:
    platform_label = "Nintendo 3DS" if config.platform == "3ds" else "Nintendo DS"
    output = f"{config.slug}.3dsx" if config.platform == "3ds" else f"{config.slug}.nds"
    libraries = {
        ("3ds", "2d"): "libctru, citro2d, and citro3d",
        ("3ds", "3d"): "libctru and citro3d",
        ("ds", "2d"): "libnds",
    }[(config.platform, config.style)]

    style_note = (
        "This starts with a moveable rectangle so the game loop is easy to understand."
        if config.style == "2d"
        else "This starts with a shader-free Citro3D render loop so you can learn the frame setup first."
    )
    if config.platform == "ds":
        style_note = "This starts as a console-style DS game loop with a moveable player marker."

    return f"""# {config.title}

Generated by Soup3DS.

Target: {platform_label}
Template: {config.style.upper()}
Libraries: {libraries}

{style_note}

## Build

1. Install devkitPro and the needed packages for this target.
2. Open a terminal in this folder.
3. Run:

```sh
make
```

The build should create `{output}`.

## Controls

- D-pad: move the player or change the scene.
- START: quit.

## Files

- `source/main.c`: the tiny game loop.
- `Makefile`: devkitPro build setup.
- `include/`: put your own headers here later.

## Beginner Ideas

- Change the player speed.
- Change the colors.
- Add walls by checking the player's X/Y position.
- Add score text after you are comfortable with the loop.

## Useful References

- devkitPro 3DS examples: https://github.com/devkitpro/3ds-examples
- libctru: https://github.com/devkitPro/libctru
- citro2d: https://github.com/devkitPro/citro2d
- citro3d: https://github.com/devkitPro/citro3d
- libnds: https://github.com/devkitPro/libnds
- Rust3DS, for later Rust experiments: https://github.com/rust3ds
"""


def gitignore_template() -> str:
    return """build/
*.elf
*.3dsx
*.smdh
*.cia
*.nds
*.map
*.d
*.o
"""


def makefile_3ds(config: GameConfig) -> str:
    libs = "-lcitro2d -lcitro3d -lctru -lm" if config.style == "2d" else "-lcitro3d -lctru -lm"
    return f"""ifeq ($(strip $(DEVKITPRO)),)
$(error "Please set DEVKITPRO in your environment. export DEVKITPRO=<path to>/devkitpro")
endif

TOPDIR ?= $(CURDIR)
include $(DEVKITPRO)/devkitARM/3ds_rules

TARGET := {config.slug}
BUILD := build
SOURCES := source
DATA := data
INCLUDES := include

APP_TITLE := {config.title}
APP_DESCRIPTION := Made with Soup3DS
APP_AUTHOR := {config.author}

ARCH := -march=armv6k -mtune=mpcore -mfloat-abi=hard -mtp=soft
CFLAGS := -g -Wall -O2 -mword-relocations -ffunction-sections $(ARCH)
CFLAGS += $(INCLUDE) -DARM11 -D_3DS
ASFLAGS := -g $(ARCH)
LDFLAGS = -specs=3dsx.specs -g $(ARCH) -Wl,-Map,$(notdir $*.map)

LIBS := {libs}
LIBDIRS := $(CTRULIB)

ifneq ($(BUILD),$(notdir $(CURDIR)))

export OUTPUT := $(CURDIR)/$(TARGET)
export TOPDIR := $(CURDIR)
export VPATH := $(foreach dir,$(SOURCES),$(CURDIR)/$(dir)) $(foreach dir,$(DATA),$(CURDIR)/$(dir))
export DEPSDIR := $(CURDIR)/$(BUILD)

CFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.c)))
SFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.s)))
BINFILES := $(foreach dir,$(DATA),$(notdir $(wildcard $(dir)/*.*)))

export OFILES := $(addsuffix .o,$(BINFILES)) $(CFILES:.c=.o) $(SFILES:.s=.o)
export INCLUDE := $(foreach dir,$(INCLUDES),-I$(CURDIR)/$(dir)) $(foreach dir,$(LIBDIRS),-I$(dir)/include)
export LIBPATHS := $(foreach dir,$(LIBDIRS),-L$(dir)/lib)

.PHONY: all clean $(BUILD)

all: $(BUILD)

$(BUILD):
\t@[ -d $@ ] || mkdir -p $@
\t@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile

clean:
\t@echo clean ...
\t@rm -fr $(BUILD) $(TARGET).3dsx $(TARGET).smdh $(TARGET).elf

else

DEPENDS := $(OFILES:.o=.d)

$(OUTPUT).3dsx: $(OUTPUT).elf
$(OUTPUT).elf: $(OFILES)

%.bin.o: %.bin
\t@echo $(notdir $<)
\t@$(bin2o)

-include $(DEPENDS)

endif
"""


def makefile_ds(config: GameConfig) -> str:
    return f"""ifeq ($(strip $(DEVKITPRO)),)
$(error "Please set DEVKITPRO in your environment. export DEVKITPRO=<path to>/devkitpro")
endif

TOPDIR ?= $(CURDIR)
include $(DEVKITPRO)/devkitARM/ds_rules

TARGET := {config.slug}
BUILD := build
SOURCES := source
INCLUDES := include

ARCH := -mthumb -mthumb-interwork
CFLAGS := -g -Wall -O2 $(ARCH)
CFLAGS += $(INCLUDE) -DARM9
ASFLAGS := -g $(ARCH)
LDFLAGS := -specs=ds_arm9.specs -g $(ARCH) -Wl,-Map,$(notdir $*.map)

LIBS := -lnds9
LIBDIRS := $(LIBNDS)

ifneq ($(BUILD),$(notdir $(CURDIR)))

export OUTPUT := $(CURDIR)/$(TARGET)
export TOPDIR := $(CURDIR)
export VPATH := $(foreach dir,$(SOURCES),$(CURDIR)/$(dir))
export DEPSDIR := $(CURDIR)/$(BUILD)

CFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.c)))
SFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.s)))

export OFILES := $(CFILES:.c=.o) $(SFILES:.s=.o)
export INCLUDE := $(foreach dir,$(INCLUDES),-I$(CURDIR)/$(dir)) $(foreach dir,$(LIBDIRS),-I$(dir)/include)
export LIBPATHS := $(foreach dir,$(LIBDIRS),-L$(dir)/lib)

.PHONY: all clean $(BUILD)

all: $(BUILD)

$(BUILD):
\t@[ -d $@ ] || mkdir -p $@
\t@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile

clean:
\t@echo clean ...
\t@rm -fr $(BUILD) $(TARGET).nds $(TARGET).elf

else

DEPENDS := $(OFILES:.o=.d)

$(OUTPUT).nds: $(OUTPUT).elf
$(OUTPUT).elf: $(OFILES)

-include $(DEPENDS)

endif
"""


def source_3ds_2d(config: GameConfig) -> str:
    return f"""#include <3ds.h>
#include <citro2d.h>

#define TOP_WIDTH 400.0f
#define TOP_HEIGHT 240.0f

static float clampf(float value, float low, float high) {{
    if (value < low) return low;
    if (value > high) return high;
    return value;
}}

int main(void) {{
    gfxInitDefault();
    C3D_Init(C3D_DEFAULT_CMDBUF_SIZE);
    C2D_Init(C2D_DEFAULT_MAX_OBJECTS);
    C2D_Prepare();

    C3D_RenderTarget* top = C2D_CreateScreenTarget(GFX_TOP, GFX_LEFT);
    C3D_RenderTarget* bottom = C2D_CreateScreenTarget(GFX_BOTTOM, GFX_LEFT);

    const u32 background = C2D_Color32(28, 35, 52, 255);
    const u32 panel = C2D_Color32(55, 72, 96, 255);
    const u32 player = C2D_Color32(255, 222, 89, 255);
    const u32 goal = C2D_Color32(83, 205, 149, 255);

    float x = TOP_WIDTH * 0.5f;
    float y = TOP_HEIGHT * 0.5f;
    int score = 0;

    while (aptMainLoop()) {{
        hidScanInput();
        const u32 down = hidKeysDown();
        const u32 held = hidKeysHeld();

        if (down & KEY_START) break;
        if (held & KEY_LEFT) x -= 2.0f;
        if (held & KEY_RIGHT) x += 2.0f;
        if (held & KEY_UP) y -= 2.0f;
        if (held & KEY_DOWN) y += 2.0f;

        x = clampf(x, 8.0f, TOP_WIDTH - 8.0f);
        y = clampf(y, 8.0f, TOP_HEIGHT - 8.0f);

        if (x > 340.0f && y < 60.0f) {{
            score++;
            x = TOP_WIDTH * 0.5f;
            y = TOP_HEIGHT * 0.5f;
        }}

        C3D_FrameBegin(C3D_FRAME_SYNCDRAW);

        C2D_TargetClear(top, background);
        C2D_SceneBegin(top);
        C2D_DrawRectSolid(332.0f, 20.0f, 0.0f, 44.0f, 34.0f, goal);
        C2D_DrawRectSolid(x - 8.0f, y - 8.0f, 0.0f, 16.0f, 16.0f, player);

        C2D_TargetClear(bottom, C2D_Color32(18, 20, 30, 255));
        C2D_SceneBegin(bottom);
        C2D_DrawRectSolid(14.0f, 18.0f, 0.0f, 292.0f, 76.0f, panel);
        C2D_DrawRectSolid(34.0f, 46.0f, 0.0f, 24.0f, 24.0f, player);
        C2D_DrawRectSolid(250.0f, 34.0f, 0.0f, 10.0f + (score % 10) * 4.0f, 20.0f, goal);

        C3D_FrameEnd(0);
    }}

    C2D_Fini();
    C3D_Fini();
    gfxExit();
    return 0;
}}
"""


def source_3ds_3d(config: GameConfig) -> str:
    return """#include <3ds.h>
#include <citro3d.h>

#define DISPLAY_TRANSFER_FLAGS \
    (GX_TRANSFER_FLIP_VERT(0) | GX_TRANSFER_OUT_TILED(0) | GX_TRANSFER_RAW_COPY(0) | \
     GX_TRANSFER_IN_FORMAT(GX_TRANSFER_FMT_RGBA8) | GX_TRANSFER_OUT_FORMAT(GX_TRANSFER_FMT_RGB8) | \
     GX_TRANSFER_SCALING(GX_TRANSFER_SCALE_NO))

static u32 scene_color(float t) {
    const u8 red = (u8)(40 + ((int)t % 100));
    const u8 green = (u8)(70 + (((int)t * 2) % 90));
    const u8 blue = 150;
    return (red << 24) | (green << 16) | (blue << 8) | 0xff;
}

int main(void) {
    gfxInitDefault();
    C3D_Init(C3D_DEFAULT_CMDBUF_SIZE);

    C3D_RenderTarget* top = C3D_RenderTargetCreate(240, 400, GPU_RB_RGBA8, GPU_RB_DEPTH24_STENCIL8);
    C3D_RenderTargetSetOutput(top, GFX_TOP, GFX_LEFT, DISPLAY_TRANSFER_FLAGS);

    float t = 0.0f;

    while (aptMainLoop()) {
        hidScanInput();
        const u32 down = hidKeysDown();
        const u32 held = hidKeysHeld();

        if (down & KEY_START) break;
        if (held & KEY_LEFT) t -= 1.0f;
        if (held & KEY_RIGHT) t += 1.0f;
        t += 0.35f;

        C3D_FrameBegin(C3D_FRAME_SYNCDRAW);
        C3D_RenderTargetClear(top, C3D_CLEAR_ALL, scene_color(t), 0);
        C3D_FrameDrawOn(top);
        C3D_FrameEnd(0);
    }

    C3D_Fini();
    gfxExit();
    return 0;
}
"""


def source_ds_2d(config: GameConfig) -> str:
    title = c_string(config.title)
    return f"""#include <nds.h>
#include <stdio.h>

static int clampi(int value, int low, int high) {{
    if (value < low) return low;
    if (value > high) return high;
    return value;
}}

int main(void) {{
    consoleDemoInit();

    int x = 15;
    int y = 10;
    int score = 0;

    while (1) {{
        scanKeys();
        const int held = keysHeld();

        if (held & KEY_LEFT) x--;
        if (held & KEY_RIGHT) x++;
        if (held & KEY_UP) y--;
        if (held & KEY_DOWN) y++;

        x = clampi(x, 1, 30);
        y = clampi(y, 3, 21);

        if (x >= 27 && y <= 5) {{
            score++;
            x = 15;
            y = 10;
        }}

        consoleClear();
        iprintf("{title}\\n");
        iprintf("D-pad moves. Reach the G.\\n");
        iprintf("Score: %d\\n", score);
        iprintf("\\x1b[5;27HG");
        iprintf("\\x1b[%d;%dH@", y, x);

        swiWaitForVBlank();
    }}
}}
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="soup3ds",
        description="A beginner-friendly text app for generating Nintendo 3DS/DS homebrew game starters.",
    )
    subparsers = parser.add_subparsers(dest="command")

    new = subparsers.add_parser("new", help="make a new game starter")
    new.add_argument("--name", required=True, help="game name")
    new.add_argument("--platform", choices=["3ds", "ds"], default="3ds")
    new.add_argument("--style", choices=["2d", "3d"], default="2d")
    new.add_argument("--author", default="New Homebrew Dev")
    new.add_argument("--out", type=Path, default=None, help="project folder; defaults to a folder from --name")
    new.add_argument("--force", action="store_true", help="write into a non-empty folder")

    subparsers.add_parser("list", help="show available templates")
    subparsers.add_parser("doctor", help="check whether build tools are visible")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        return interactive()
    if args.command == "list":
        return list_templates()
    if args.command == "doctor":
        return doctor()
    if args.command == "new":
        platform, style = validate_template(args.platform, args.style)
        directory = (args.out or Path(slugify(args.name))).expanduser().resolve()
        config = GameConfig(
            name=args.name,
            platform=platform,
            style=style,
            author=args.author,
            directory=directory,
        )
        written = create_project(config, args.force)
        print_success(config, written)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
