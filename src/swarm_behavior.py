'''
Name: swarm_behavior.py
Description: Components and systems for resolving swarm interactions.
Author: Anthony Tran, Gaven Behrends
Created: 11.10.2026
Revised: 11.27.2026
Last update: Renamed from swarm_movement.py, generalize behaviors
'''

import math
import pyray as rl
from enum import Enum
from battle import Attack, Team
from common import Position, Velocity
from world import System


class Movement():
    def __init__(self, speed):
        self.speed = speed


class SwarmBehaviorType(Enum):
    IDLE = 0
    CHASE = 1
    KEYBOARD_CONTROL = 2


class SwarmBehaviorSystem(System):
    def run(self, world, dt):
        for position, velocity, movement, team, behavior, attack in world.query(
                Position, Velocity, Movement, Team, SwarmBehaviorType, Attack):
            if behavior == SwarmBehaviorType.CHASE:
                # Wait by default
                velocity.x = 0
                velocity.y = 0
                # Look for nearest opposing swarm
                target = None
                target_distance = math.inf
                for other_position, other_team in world.query(Position, Team):
                    if other_team.name == team.name:
                        continue
                    distance = math.hypot(other_position.x - position.x, other_position.y - position.y)
                    if distance < target_distance:
                        target_distance = distance
                        target = other_position
                if target is None:
                    continue
                # Set velocity to chase
                stop_distance = attack.range * 0.8
                dx = target.x - position.x
                dy = target.y - position.y
                step = min(movement.speed, distance - stop_distance)
                velocity.x = dx * step / distance
                velocity.y = dy * step / distance
            if behavior == SwarmBehaviorType.KEYBOARD_CONTROL:
                dx = 0
                dy = 0
                if rl.is_key_down(rl.KEY_A) or rl.is_key_down(rl.KEY_LEFT):
                    dx -= 1
                if rl.is_key_down(rl.KEY_D) or rl.is_key_down(rl.KEY_RIGHT):
                    dx += 1
                if rl.is_key_down(rl.KEY_W) or rl.is_key_down(rl.KEY_UP):
                    dy -= 1
                if rl.is_key_down(rl.KEY_S) or rl.is_key_down(rl.KEY_DOWN):
                    dy += 1
                magnitude = math.hypot(dx, dy)
                if magnitude != 0:
                    dx = (dx / magnitude) * movement.speed
                    dy = (dy / magnitude) * movement.speed
                velocity.x = dx
                velocity.y = dy
