"""Glyphform application entry point."""

import atexit
import signal
import sys
import time

import numpy as np

from .engine import World
from .rendering import Screen
from .settings import FPS, SEED


def run(text=None):
    screen = Screen()
    atexit.register(screen.close)

    for name in ("SIGTERM", "SIGHUP", "SIGBREAK"):
        sig = getattr(signal, name, None)

        if sig is not None:
            try:
                signal.signal(sig, lambda s, f: sys.exit(1))
            except (ValueError, OSError):
                pass

    rng = np.random.default_rng(SEED)
    world = None
    frame_dt = 1.0 / FPS

    try:
        screen.open()

        t0 = last = next_frame = time.perf_counter()

        while True:
            now = time.perf_counter()
            ev = screen.poll()

            if ev["quit"]:
                break

            cols, rows = screen.term_size()

            if (cols, rows) != screen.size:
                screen.resize(cols, rows)

                if cols < 30 or rows < 12:
                    screen.write(
                        "\x1b[2J\x1b[HPlease enlarge the terminal"
                    )
                    world = None
                else:
                    world = World(cols, rows, rng, text=text)

            if world is not None:
                world.handle(ev, now - t0)

                dt = min(now - last, 0.1)

                ch, col, ramp, force = world.frame(
                    now - t0,
                    dt,
                )

                screen.present(ch, col, ramp, force)

            last = now
            next_frame += frame_dt

            delay = next_frame - time.perf_counter()

            if delay > 0:
                time.sleep(delay)
            else:
                next_frame = time.perf_counter()

    except KeyboardInterrupt:
        pass

    finally:
        screen.close()