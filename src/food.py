'''
Author: Max Toney
KUID: 3127420
Class Name: Wallet, Food, FoodDrop, FoodSystem
Last Modified: 11.19.26
Purpose: Runs the functionaility of the food system, including gaining/dropping and storing food.
'''
import math
import random
from battle import Position, Team
from world import Entity, System


class Wallet:
    """Persistent currency. Lives outside the World so it survives round restarts."""
    def __init__(self):
        self.food = 0

    def add(self, amount):
        self.food += amount

    def spend(self, amount):
        if self.food < amount:
            return False
        self.food -= amount
        return True

class Food:
    """A pickup sitting on the map."""
    def __init__(self, value=1):
        self.value = value

def spawn_food(world, x, y, value=1):
    e = world.create_entity()
    world.add(e, Position(x, y))
    world.add(e, Food(value))
    return e

class FoodSystem(System):
    """Handles pickups and random spawning. Register AFTER BattleSystem."""
    def __init__(self, wallet, bounds, pickup_radius=24,
                 spawn_interval=4.0, max_on_map=6):
        self.wallet = wallet
        self.bounds = bounds              # (left, top, right, bottom)
        self.pickup_radius = pickup_radius
        self.spawn_interval = spawn_interval
        self.max_on_map = max_on_map
        self.timer = spawn_interval

    def run(self, world, dt):
        # Pickup: only the player collects food
        player = next((p for p, t in world.query(Position, Team)
                       if t.name == Team.PLAYER), None)
        count = 0
        if player is not None:
            eaten = []
            for e, pos, food in world.query(Entity, Position, Food):
                if math.hypot(pos.x - player.x, pos.y - player.y) <= self.pickup_radius:
                    self.wallet.add(food.value)
                    eaten.append(e)
            for e in eaten:
                world.delete_entity(Entity(e))

        # Random spawning, capped so the map doesn't flood
        count = sum(1 for _ in world.query(Food))
        self.timer -= dt
        if self.timer <= 0 and count < self.max_on_map:
            self.timer = self.spawn_interval
            l, t, r, b = self.bounds
            spawn_food(world, random.uniform(l, r), random.uniform(t, b))

wallet = Wallet()