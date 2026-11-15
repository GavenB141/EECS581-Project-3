"""Move player and AI swarms within the arena before resolving combat."""

import math

from battle import Attack, Position, Team
from world import System


class Movement:
    def __init__(self, speed):
        self.speed = speed


class SwarmMovement(System):
    def __init__(self, bounds):
        self.bounds = bounds
        self.player_direction = (0, 0)

    def run(self, world, dt):
        player = None
        for position, team, movement in world.query(Position, Team, Movement):
            if team.name != Team.PLAYER:
                continue

            player = position
            dx, dy = self.player_direction
            length = math.hypot(dx, dy)
            if length > 0:
                # Don't let the player move faster just because they hold two keys.
                scale = movement.speed * dt / length
                self._move(player, dx * scale, dy * scale)
            break

        # If the player is gone, there's nothing left for the AI to chase.
        if player is None:
            return

        for position, team, movement, attack in world.query(Position, Team, Movement, Attack):
            if team.name != Team.AI:
                continue

            dx = player.x - position.x
            dy = player.y - position.y
            distance = math.hypot(dx, dy)
            stop_distance = attack.range * 0.8
            if distance > stop_distance:
                # Get close enough to attack without running past the player.
                step = min(movement.speed * dt, distance - stop_distance)
                self._move(position, dx * step / distance, dy * step / distance)

    def _move(self, position, dx, dy):
        # Keep the swarm from going outside the arena.
        left, top, right, bottom = self.bounds
        position.x = min(right, max(left, position.x + dx))
        position.y = min(bottom, max(top, position.y + dy))
