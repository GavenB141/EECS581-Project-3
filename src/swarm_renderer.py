'''
Name: swarm_renderer.py
Description: Module for drawing large swarms of bugs.
Author: Gaven Behrends
Created: 11.22.2026
Revised: Never
'''

import numpy as np
import pyray as rl
from world import Entity, System, World
from common import Position
from battle import Health

# Example bug type -> color mappings for now,
# can be changed as game design updates
BUG_TYPES = {
    "biter": (255, 120, 120, 255),
    "spitter": (60, 180, 80, 255),
    "buzzer": (200, 240, 255, 255)
}
TYPE_INDEX = {name: i for i, name in enumerate(BUG_TYPES)}


def fudge_counts(health: Health):
    """
    Since swarm counts by type aren't mechanically implemented yet,
    this function fudges them from the general count for testing
    the swarm renderer.
    """
    n = max(0, int(health.bugs))
    biters = int(n * 0.6)
    spitters = int(n * 0.25)
    return {"biter": biters, "spitter": spitters, "buzzer": n - biters - spitters}


class SwarmRenderSystem(System):
    """Draws a particle layer for representing bugs."""
    def __init__(self, width: int, height: int):
        self.width: int = width
        self.height: int = height
        # Pixel buffer; indexed (y, x, color channel)
        self.canvas = np.zeros((height, width, 4), dtype=np.uint8)
        self._pixels = rl.ffi.cast("void *", self.canvas.ctypes.data)
        self.rng = np.random.default_rng()
        self.texture = None

    def run(self, world: World, dt: float):
        """System.run implementation"""
        for entity, position, health in world.query(Entity, Position, Health):
            particles = world.get(entity, SwarmParticles)
            center = np.array([position.x, position.y], dtype=float)
            counts = fudge_counts(health)
            if particles is None:
                particles = SwarmParticles(counts, center, self.rng)
                world.add(entity, particles)
            elif sum(counts.values()) != len(particles.pos):
                particles.rebuild(counts, center, self.rng)
            self._step(particles, center, dt)

    def draw(self, world: World):
        """System.draw implementation"""
        self.canvas[...] = 0
        for (particles,) in world.query(SwarmParticles):
            for name, color in BUG_TYPES.items():
                self._paint(particles.pos[particles.kind == TYPE_INDEX[name]], color)
        # Lazily load particle buffer to GPU
        if self.texture is None:
            image = rl.Image(
                self._pixels, self.width, self.height, 1,
                rl.PixelFormat.PIXELFORMAT_UNCOMPRESSED_R8G8B8A8
            )
            self.texture = rl.load_texture_from_image(image)
        rl.update_texture(self.texture, self._pixels)
        rl.draw_texture(self.texture, 0, 0, rl.WHITE)
        
    def _paint(self, pos: np.ndarray, color, size: int = 3):
        """Draws particles at positions in `pos`"""
        xi = pos[:, 0].astype(np.int32)
        yi = pos[:, 1].astype(np.int32)
        for dx in range(size):
            for dy in range(size):
                x = xi + dx
                y = yi + dy
                ok = (x >= 0) & (x < self.width) & (y >= 0) & (y < self.height)
                self.canvas[y[ok], x[ok]] = color

    def _step(self, state: SwarmParticles, center: np.ndarray, dt: float):
        """Moves particles in `state`"""
        state.phase += state.wobble_speed * dt
        wobble = np.stack([np.sin(state.phase), np.cos(state.phase * 1.3)], axis=1) * 3.0
        target = center + state.home + wobble
        step = (target - state.pos) * min(1.0, 6.0 * dt)
        dist = np.linalg.norm(step, axis=1)
        limit = state.move_speed * dt
        scale = np.minimum(1.0, limit / np.maximum(dist, 1e-9))
        state.pos += step * scale[:, None]


class SwarmParticles:
    def __init__(self, counts: dict[str, int], center: np.ndarray, rng: np.random.Generator):
        self.pos = np.empty((0, 2))
        self.rebuild(counts, center, rng)
        
    def rebuild(self, counts: dict[str, int], center: np.ndarray, rng: np.random.Generator):
        n = sum(counts.values())
        # Enumerate bug types
        self.kind = np.repeat(
            [TYPE_INDEX[name] for name in counts],
            [counts[name] for name in counts]
        )
        # Base offsets of each bug from center
        self.home = make_homes(n, swarm_radius(n), rng)
        # Point of each bug in wobble cycle
        self.phase = rng.uniform(0, 2 * np.pi, n)
        # How fast each bug wobbles
        self.wobble_speed = rng.uniform(6.0, 12.0, n)
        # How fast each bug moves
        self.move_speed = rng.uniform(160.0, 220.0, n)
        # Preserve immediate positions of surviving bugs
        old = self.pos[:n]
        # Spawn in new bugs at the center
        fresh = np.repeat(center[None, :], n - len(old), axis=0)
        # Actual positions of bugs
        self.pos = np.concatenate([old, fresh])
        

def make_homes(n: int, radius: float, rng: np.random.Generator) -> np.ndarray:
    """Generate n random coordinates within the radius"""
    # Generate polar coordinates
    angle = rng.uniform(0, 2 * np.pi, n)
    dist = radius * np.sqrt(rng.uniform(0, 1, n))
    # Convert to Euclidian
    return np.stack([np.cos(angle) * dist, np.sin(angle) * dist], axis=1)


def swarm_radius(n: int) -> float:
    """Decide swarm radius based on size"""
    return 4.0 + 2.5 * np.sqrt(n)
