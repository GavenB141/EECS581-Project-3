'''
Name: battle.py
Description: Battle system
Author: Cooper Fish
Created: 11.10.2026
Updated: 11.20.2026
latest update: added to health, attack, and battlesystem classes
'''

import math
from world import Entity, System

NORMAL = "normal"
FIRE, ICE, POISON = "fire", "ice", "poison"
ON_FIRE, FREEZING, POISONED = "on_fire", "freezing", "poisoned"

TICK_TIME = 1.0
FIRE_DOT = 5
POISON_DOT = 3
FREEZE_SLOW = 0.5

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
    def __init__(self, bugs=10):
        self.max_bugs = bugs
        self.bugs = bugs
        self.state = NORMAL
        self.tick_timer = 0.0
        self.dot_damage = 0

class Attack:
    def __init__(self, damage=10, type=NORMAL, attack_range=10, cooldown=1):
        self.damage = damage
        self.type = type
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
        for (hp,) in world.query(Health):
            if hp.state in (ON_FIRE, POISONED):
                hp.tick_timer -= dt
                if hp.tick_timer <= 0:
                    hp.bugs = max(0, hp.bugs - hp.dot_damage)
                    hp.tick_timer += TICK_TIME

        for pos, team, hp, atk in world.query(Position, Team, Health, Attack):
            speed = FREEZE_SLOW if hp.state == FREEZING else 1.0
            atk.timer = max(0.0, atk.timer - dt * speed)
            if hp.bugs <= 0 or atk.timer > 0:
                continue
            for o_pos, o_team, o_hp in world.query(Position, Team, Health):
                if o_team.name != team.name and o_hp.bugs > 0:
                    if math.hypot(o_pos.x - pos.x, o_pos.y - pos.y) <= atk.range:
                        self._hit(o_hp, atk)
                        atk.timer = atk.cooldown
                        break

        # Pay out food for dead enemies before they are deleted.
        if self.wallet is not None:
            for team, hp, drop in world.query(Team, Health, FoodDrop):
                if team.name == Team.AI and hp.bugs <= 0:
                    self.wallet.add(drop.amount)

        dead = [e for e, hp in world.query(Entity, Health) if hp.bugs <= 0]
        for e in dead:
            world.delete_entity(Entity(e))

    def _hit(self, hp, atk):
        if atk.type == POISON:
            self._apply(hp, POISONED, POISON_DOT)
            return
        hp.bugs = max(0, hp.bugs - atk.damage)
        if hp.state == POISONED:
            return
        if atk.type == FIRE:
            if hp.state == FREEZING:
                hp.state = NORMAL
            else:
                self._apply(hp, ON_FIRE, FIRE_DOT)
        elif atk.type == ICE:
            if hp.state == ON_FIRE:
                hp.state = NORMAL
            else:
                self._apply(hp, FREEZING, 0)

    def _apply(self, hp, state, dot):
        if hp.state != state:
            hp.tick_timer = TICK_TIME
        hp.state = state
        hp.dot_damage = dot
