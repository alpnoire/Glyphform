"""Built-in shape masks, colour palettes, and interpolation helpers."""

import math
import numpy as np

TAU = 2.0 * math.pi
STEPS = 40



def heart(X, Y):
    x = X * 1.35
    y = Y * 1.25 + 0.15
    return (x * x + y * y - 1.0) ** 3 - x * x * y ** 3 <= 0.0


def star(X, Y):
    y = Y - 0.03
    r = np.hypot(X, y)
    phi = np.arctan2(y, X) - math.pi / 2
    return r <= 0.30 + 0.66 * np.abs(np.cos(2.5 * phi)) ** 1.6


def shield(X, Y):
    ax = np.abs(X)
    upper = (Y >= -0.05) & (ax <= 0.75) & (Y <= 0.85 - 0.10 * (ax / 0.75) ** 2)
    t = np.clip((-0.05 - Y) / 0.85, 0.0, 1.0)
    lower = (Y < -0.05) & (Y >= -0.90) & (ax <= 0.75 * (1.0 - t) ** 0.6)
    keyhole = (np.hypot(X, Y - 0.18) < 0.15) | ((ax < 0.055) & (Y < 0.18) & (Y > -0.38))
    return (upper | lower) & ~keyhole


def rocket(X, Y):
    ax = np.abs(X)
    t = (Y + 0.70) / 1.65
    w = np.where(t < 0.45, 0.27,
                 0.27 * np.sqrt(np.clip(1.0 - ((t - 0.45) / 0.55) ** 2, 0.0, 1.0)))
    body = (t >= 0.0) & (t <= 1.0) & (ax <= w)
    ext = 0.27 + 0.33 * np.clip((-0.20 - Y) / 0.50, 0.0, 1.0)
    fins = (Y >= -0.72) & (Y <= -0.20) & (ax <= ext)
    flame = (Y < -0.72) & (Y >= -1.0) & (ax <= 0.14 * (1.0 - (-0.72 - Y) / 0.30))
    window = np.hypot(X, Y - 0.35) < 0.11
    return (body | fins | flame) & ~window


HEART_PAL = [(0.0, (40, 0, 10)), (0.4, (200, 20, 60)), (0.75, (255, 90, 140)), (1.0, (255, 230, 240))]
STAR_PAL = [(0.0, (40, 20, 0)), (0.4, (230, 150, 0)), (0.75, (255, 215, 60)), (1.0, (255, 255, 220))]
SHIELD_PAL = [(0.0, (0, 20, 60)), (0.4, (0, 110, 235)), (0.75, (0, 210, 255)), (1.0, (220, 255, 255))]
ROCKET_PAL = [(0.0, (30, 4, 2)), (0.4, (210, 60, 10)), (0.75, (255, 170, 30)), (1.0, (255, 250, 220))]

SCENES = [("heart", heart, HEART_PAL), ("star", star, STAR_PAL),
          ("shield", shield, SHIELD_PAL), ("rocket", rocket, ROCKET_PAL)]


def build_ramp(stops):
    pos = np.array([s[0] for s in stops])
    rgb = np.array([s[1] for s in stops], dtype=float)
    xs = np.linspace(0.0, 1.0, STEPS)
    return np.stack([np.interp(xs, pos, rgb[:, c]) for c in range(3)], axis=1)


RAMPS = [build_ramp(s[2]) for s in SCENES]


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)
