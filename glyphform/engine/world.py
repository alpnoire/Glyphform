"""Particle world, shape transitions, and simulation physics."""

import math
import numpy as np

from ..shapes import SCENES, RAMPS, STEPS, TAU, smoothstep
from ..shapes.text_shape import generate_text_mask
from ..settings import DENSITY, SCENE_SECONDS


class World:
    """Grid geometry, shape masks and the particle simulation."""

    def __init__(self, W, H, rng, text=None):
        self.W, self.H, self.rng = W, H, rng

        self.custom_text = text.strip() if text else None

        self.unit = max(4.0, min(H / 2.0, W / 4.0)) * 0.95
        self.cx = (W - 1) / 2.0
        self.cy = (H - 1) / 2.0

        xs = (np.arange(W) - self.cx) * 0.5 / self.unit
        ys = (self.cy - np.arange(H)) / self.unit
        self.X, self.Y = np.meshgrid(xs, ys)

        # Build the four original shape masks.
        self.masks = [fn(self.X, self.Y) for _, fn, _ in SCENES]

        # Add a custom text mask when requested.
        if self.custom_text:
            text_mask = generate_text_mask(
                self.custom_text,
                width=W,
                height=H,
                density=1,
            )
            self.masks.append(text_mask)

        # Calculate the edges of every mask.
        self.edges = []

        for mask in self.masks:
            padded = np.pad(mask, 1)

            eroded = (
                mask
                & padded[:-2, 1:-1]
                & padded[2:, 1:-1]
                & padded[1:-1, :-2]
                & padded[1:-1, 2:]
            )

            self.edges.append(mask & ~eroded)

        # Original colour palettes plus a dedicated text palette.
        self.ramps = list(RAMPS)

        if self.custom_text:
            text_ramp = np.linspace(
                (0, 90, 180),
                (120, 240, 255),
                STEPS,
            )
            self.ramps.append(text_ramp)

        self.cell_rate = rng.uniform(1.5, 6.0, (H, W))
        self.cell_ph = rng.uniform(0.0, TAU, (H, W))
        self.cell_r = rng.random((H, W))

        n = max(600, int(0.5 * W * H * DENSITY))

        self.n = n
        self.n_amb = int(n * 0.12)
        self.n_shape = n - self.n_amb

        self.base = rng.uniform(0.55, 1.0, n)
        self.flick = rng.uniform(1.5, 8.0, n)
        self.ph = rng.uniform(0.0, TAU, n)

        self.pos = np.tile(
            [self.cy, self.cx],
            (n, 1),
        ).astype(float)

        self.vel = rng.standard_normal((n, 2)) * 30.0

        self.tgt = self.pos.copy()
        self.tgt_y = np.zeros(n)
        self.tgt_edge = np.zeros(n, bool)

        self.scene = -1
        self.scene_start = 0.0
        self.prev_scene = 0

        self.mouse = None
        self.left = False
        self.mouse_time = -99.0
        self.pending = None

        self.near = np.zeros(n)

    def handle(self, ev, t):
        """Process keyboard and mouse input."""

        if ev["pos"] is not None:
            r, c = ev["pos"]

            if 0 <= r < self.H and 0 <= c < self.W:
                self.mouse = (r, c)
                self.mouse_time = t

        if ev["left"] is not None:
            self.left = ev["left"]

        # Custom text mode stays on its text scene.
        if self.custom_text:
            return

        if ev["step"]:
            base = (
                self.pending
                if self.pending is not None
                else max(self.scene, 0)
            )

            self.pending = (base + ev["step"]) % len(SCENES)

    def enter_scene(self, idx, t, burst=True):
        """Move particles towards a selected shape or text mask."""

        rng = self.rng

        self.prev_scene = max(self.scene, 0)
        self.scene = idx
        self.scene_start = t

        mask = self.masks[idx]
        edge = self.edges[idx]

        cells = np.argwhere(mask)

        if len(cells) == 0:
            cells = np.array([
                [int(self.cy), int(self.cx)]
            ])

        weights = 1.0 + 1.6 * edge[
            cells[:, 0],
            cells[:, 1],
        ]

        pick = rng.choice(
            len(cells),
            size=self.n_shape,
            p=weights / weights.sum(),
        )

        r = cells[pick, 0] + rng.uniform(
            -0.5, 0.5, self.n_shape
        )

        c = cells[pick, 1] + rng.uniform(
            -0.5, 0.5, self.n_shape
        )

        self.tgt[:self.n_shape, 0] = r
        self.tgt[:self.n_shape, 1] = c

        self.tgt_y[:self.n_shape] = (
            self.cy - r
        ) / self.unit

        self.tgt_edge[:self.n_shape] = edge[
            cells[pick, 0],
            cells[pick, 1],
        ]

        # Ambient particles remain around the main shape.
        m = self.n_amb

        ang = rng.uniform(0.0, TAU, m)
        rad = 1.0 + np.abs(
            rng.standard_normal(m)
        ) * 0.40

        self.tgt[self.n_shape:, 1] = (
            self.cx
            + 2.0 * self.unit * rad * np.cos(ang) * 0.95
        )

        self.tgt[self.n_shape:, 0] = (
            self.cy
            - self.unit * rad * np.sin(ang) * 0.95
        )

        self.tgt_y[self.n_shape:] = 0.0
        self.tgt_edge[self.n_shape:] = False

        if burst:
            self.vel += (
                rng.standard_normal((self.n, 2)) * 38.0
            )

    def step(self, t, dt):
        """Update particle positions and physics."""

        if self.scene < 0:
            if self.custom_text:
                self.enter_scene(len(SCENES), t, burst=False)
            else:
                self.enter_scene(0, t, burst=False)

        elif (
            not self.custom_text
            and (
                self.pending is not None
                or t - self.scene_start >= SCENE_SECONDS
            )
        ):
            idx = (
                self.pending
                if self.pending is not None
                else (self.scene + 1) % len(SCENES)
            )

            self.pending = None
            self.enter_scene(idx, t)

        ts = t - self.scene_start

        n = self.n
        ns = self.n_shape

        # Moving particle targets.
        tgt = self.tgt.copy()

        cy, cx = self.cy, self.cx

        if self.scene == 0:
            # Heartbeat.
            beat = max(
                0.0,
                math.sin(TAU * 1.15 * t),
            ) ** 6

            s = 1.0 + 0.07 * beat

            tgt[:ns, 0] = (
                cy + (tgt[:ns, 0] - cy) * s
            )

            tgt[:ns, 1] = (
                cx + (tgt[:ns, 1] - cx) * s
            )

        elif self.scene == 1:
            # Breathing star.
            s = 1.0 + 0.03 * math.sin(TAU * 0.5 * t)

            tgt[:ns, 0] = (
                cy + (tgt[:ns, 0] - cy) * s
            )

            tgt[:ns, 1] = (
                cx + (tgt[:ns, 1] - cx) * s
            )

        elif self.scene == 3:
            # Rocket shake and flame.
            tgt[:ns, 1] += (
                0.35 * math.sin(TAU * 9.0 * t)
            )

            flame = self.tgt_y[:ns] < -0.72
            k = int(flame.sum())

            if k:
                jit = self.rng.uniform(
                    0.0, 0.07 * self.H, k
                )

                tgt[:ns][flame, 0] += jit

                tgt[:ns][flame, 1] += (
                    self.rng.normal(0.0, 0.6, k)
                )

        # Ambient particle movement.
        ph = self.ph[ns:]

        tgt[ns:, 0] += (
            1.4 * np.sin(TAU * 0.25 * t + ph)
        )

        tgt[ns:, 1] += (
            2.0 * np.cos(TAU * 0.20 * t + ph)
        )

        # Spring physics.
        acc = 13.0 * (tgt - self.pos) - 4.6 * self.vel

        # Mouse interaction.
        near = self.near
        near[:] = 0.0

        if (
            self.mouse is not None
            and (self.left or t - self.mouse_time < 6.0)
        ):
            mr, mc = self.mouse

            dr = (self.pos[:, 0] - mr) * 2.0
            dc = self.pos[:, 1] - mc

            d = np.hypot(dr, dc) + 1e-3

            ux = dc / d
            uy = dr / d

            R = 0.70 * self.unit

            near[:] = np.clip(
                1.0 - d / (1.4 * R),
                0.0,
                1.0,
            )

            if self.left:
                w = np.clip(
                    1.0 - d / (3.0 * R),
                    0.0,
                    1.0,
                )

                pull = 500.0 * w
                swirl = 320.0 * w

                acc[:, 1] += -pull * ux - swirl * uy
                acc[:, 0] += (
                    -pull * uy + swirl * ux
                ) / 2.0

            else:
                push = 650.0 * np.clip(
                    1.0 - d / R,
                    0.0,
                    1.0,
                ) ** 2

                acc[:, 1] += push * ux
                acc[:, 0] += push * uy / 2.0

        self.vel += acc * dt

        np.clip(
            self.vel,
            -140.0,
            140.0,
            out=self.vel,
        )

        self.pos += self.vel * dt

        # Particle heat.
        raw = 0.5 + 0.5 * np.sin(
            TAU * self.flick * t + self.ph
        )

        fl = 0.45 + 0.55 * smoothstep(
            0.1,
            0.5,
            raw,
        )

        sp = np.hypot(
            self.vel[:, 0],
            self.vel[:, 1] * 0.5,
        )

        h = np.minimum(
            1.0,
            self.base * fl
            + 0.015 * sp
            + 0.35 * self.near,
        )

        h[:ns] = np.where(
            self.tgt_edge[:ns],
            np.minimum(1.0, h[:ns] + 0.18),
            h[:ns],
        )

        h[ns:] *= 0.45

        if self.scene == 3:
            flame = self.tgt_y[:ns] < -0.72

            h[:ns][flame] = np.minimum(
                1.0,
                h[:ns][flame] * 1.1,
            )

        return h, ts

    def frame(self, t, dt):
        """Render the current particle frame."""

        h, ts = self.step(t, dt)

        H, W = self.H, self.W

        heat = np.zeros((H, W))

        r = np.rint(self.pos[:, 0]).astype(int)
        c = np.rint(self.pos[:, 1]).astype(int)

        ok = (
            (h > 0.07)
            & (r >= 0)
            & (r < H)
            & (c >= 0)
            & (c < W)
        )

        r, c, hh = r[ok], c[ok], h[ok]

        order = np.argsort(hh)

        heat[r[order], c[order]] = hh[order]

        # Shape or text glow.
        reveal = float(
            smoothstep(2.0, 4.0, ts)
        )

        if reveal > 0.0:
            mask = self.masks[self.scene]
            edge = self.edges[self.scene]

            shimmer = 0.5 + 0.5 * np.sin(
                t * self.cell_rate + self.cell_ph
            )

            field = np.where(
                mask,
                0.30 + 0.22 * shimmer,
                0.0,
            )

            field = np.where(
                edge,
                0.62 + 0.25 * shimmer,
                field,
            )

            if self.scene == 3:
                flame = mask & (self.Y < -0.72)

                lit = self.cell_r < (
                    0.45 + 0.4 * shimmer
                )

                field = np.where(
                    flame,
                    np.where(
                        lit,
                        0.55 + 0.4 * shimmer,
                        0.0,
                    ),
                    field,
                )

            heat = np.maximum(
                heat,
                field * reveal,
            )

        gi = np.where(
            heat > 0.06,
            1 + np.minimum(
                10,
                (heat * 10.99).astype(int),
            ),
            0,
        )

        ci = np.where(
            heat > 0.06,
            1 + (
                np.clip(heat, 0, 1) * (STEPS - 1) + 0.5
            ).astype(int),
            0,
        )

        b = (
            float(smoothstep(0.0, 1.6, ts))
            if t > 0.0
            else 1.0
        )

        ramp = (
            self.ramps[self.prev_scene] * (1.0 - b)
            + self.ramps[self.scene] * b
        )

        return (
            gi.astype(np.uint8),
            ci.astype(np.uint8),
            ramp,
            b < 1.0,
        )