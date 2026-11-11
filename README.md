# Glyphform

**A real-time ASCII particle animation engine for your terminal.**

Glyphform uses a lightweight NumPy-based particle simulation to make glowing characters burst apart, move, and reform into four animated silhouettes: a heart, star, shield, and rocket.

## Features

- Spring-based particle motion and velocity damping
- Four built-in vectorized shape masks
- Animated colour ramps and per-particle flicker
- Mouse interaction: push particles away or pull and swirl them
- Keyboard navigation between scenes
- Incremental ANSI rendering to reduce terminal redraw work
- Modular package layout with automated tests

## Requirements

- Python 3.9 or newer
- NumPy 1.20 or newer
- A modern ANSI-compatible terminal

Windows Terminal and the VS Code terminal are recommended on Windows. Most modern macOS and Linux terminals should work.

## Installation

### Windows

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

From the project root:

```bash
python glyphform.py
```

Or run it as a package:

```bash
python -m glyphform
```

Maximize the terminal for the best result. Glyphform needs an interactive terminal and will exit with a short message when standard output is not a TTY.

## Controls

| Input | Action |
|---|---|
| `N` or `Space` | Next shape |
| `P` | Previous shape |
| `Q` or `Ctrl+C` | Quit |
| Mouse movement | Push particles away from the cursor |
| Hold left mouse button | Pull and swirl particles around the cursor |
| Right-click or scroll wheel | Change shape |

Mouse input depends on terminal support. Keyboard controls remain available if mouse reporting is unsupported.

## Project structure

```text
glyphform/
├── glyphform/
│   ├── engine/       # Particle world and simulation
│   ├── rendering/    # ANSI terminal output and input
│   ├── shapes/       # Shape masks and colour palettes
│   ├── main.py       # Application loop
│   └── settings.py   # Runtime constants
├── tests/            # Automated unit tests
├── glyphform.py      # Backwards-compatible launcher
└── requirements.txt
```

## Configuration

The initial release keeps the original tuning values in `glyphform/settings.py`:

- `FPS`: target frame rate
- `SCENE_SECONDS`: time each shape remains active
- `DENSITY`: particle density multiplier
- `SEED`: set an integer for repeatable random behaviour, or leave as `None`

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## Add a shape

1. Add a vectorized function in `glyphform/shapes/__init__.py`. It receives NumPy coordinate grids `X` and `Y` and returns a boolean mask.
2. Define a colour palette as ordered `(position, (red, green, blue))` stops.
3. Add the shape, function, and palette to `SCENES`.

## Notes

Glyphform uses ANSI escape sequences for terminal rendering and mouse reporting. Terminal capabilities vary, so visual output and mouse interaction may differ between terminal applications.
