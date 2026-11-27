'''
Name: common.py
Description: Highly generalizable components and systems
Author: Gaven Behrends
Created: 11.27.2026
Revised: never
'''

from world import System, World


class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Velocity:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class MovementSystem(System):
    """
    Update the position of anything with a velocity.
    """
    def __init__(self, bounds):
        self.bounds = bounds
    
    def run(self, world: World, dt: float):
        for position, velocity in world.query(Position, Velocity):
            dx = velocity.x * dt
            dy = velocity.y * dt
            left, top, right, bottom = self.bounds
            position.x = min(right, max(left, position.x + dx))
            position.y = min(bottom, max(top, position.y + dy))
