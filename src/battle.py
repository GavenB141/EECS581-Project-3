'''
Name: battle.py
Description: Basic battle system
Author: Cooper Fish
Created: 11.10.2026
'''

import math
from world import Entity, System

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Team:
    PLAYER = "player"
    AI = "ai"

    def __init__(self, name):
        self.name = name

class Health:
    def __init__(self, max_hp=100):
        self.max_hp = max_hp
        self.current = max_hp

class Attack:
    def __init__(self, damage=10, attack_range=70, cooldown=0.5):
        self.damage = damage
        self.range = attack_range
        self.cooldown = cooldown
        self.timer = 0.0

class FoodDrop:
    """Put on enemies: how much food the player earns when they die."""
    def __init__(self, amount=5):
        self.amount = amount

class BattleSystem(System):
    def __init__(self, wallet=None):
        # The wallet lives outside the World so food survives round restarts.
        self.wallet = wallet

    def run(self, world, dt):
        for pos, team, hp, atk in world.query(Position, Team, Health, Attack):
            atk.timer = max(0.0, atk.timer - dt)
            if hp.current <= 0 or atk.timer > 0:
                continue
            for o_pos, o_team, o_hp in world.query(Position, Team, Health):
                if o_team.name != team.name and o_hp.current > 0:
                    if math.hypot(o_pos.x - pos.x, o_pos.y - pos.y) <= atk.range:
                        o_hp.current -= atk.damage
                        atk.timer = atk.cooldown
                        break

        # Pay out food for dead enemies before they are deleted.
        if self.wallet is not None:
            for team, hp, drop in world.query(Team, Health, FoodDrop):
                if team.name == Team.AI and hp.current <= 0:
                    self.wallet.add(drop.amount)

        dead = [e for e, hp in world.query(Entity, Health) if hp.current <= 0]
        for e in dead:
            world.delete_entity(Entity(e))