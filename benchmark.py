import time
import numpy as np
from glyphform.engine import World

sizes = [(80, 24), (120, 40), (160, 50), (200, 60)]
frames = 150

print("GLYPHFORM PERFORMANCE BENCHMARK")
print("-" * 40)

for width, height in sizes:
    rng = np.random.default_rng(42)
    world = World(width, height, rng)

    start = time.perf_counter()

    for i in range(frames):
        world.frame(i / 30, 1 / 30)

    elapsed = time.perf_counter() - start
    fps = frames / elapsed

    print(f"{width}x{height}: {fps:.1f} FPS | {elapsed:.2f}s")

print("-" * 40)
print("Benchmark complete.")