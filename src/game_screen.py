'''
Name: game_screen.py
Description: Main gameplay loop. The GameScreen class in this file is a
    consolidation of the earlier GameScreen (written by Jocelyn Miller)
    and BattleGameScreen (written by Cooper Fish)
Author: Gaven Behrends
Created: 10.27.2026
Revised: never
'''

import pyray as rl
from stack_screen import Stack, Screen, Button, GameOverScreen, PauseScreen
from world import World
from swarm_behavior import Movement, SwarmBehaviorSystem, SwarmBehaviorType
from swarm_renderer import SwarmRenderSystem
from common import Position, Velocity, MovementSystem
from battle import BattleSystem, Attack, Team, FoodDrop, Health
from food import Food, FoodSystem, wallet

class GameScreen(Screen):
    def __init__(self, screen_stack):
        super().__init__(screen_stack)

        # Add pause button to the screen's menu
        pause_btn = Button(
            "||",
            lambda: screen_stack.push(PauseScreen(screen_stack)),
            86, 32, 50, 40
        )
        self.buttons = [pause_btn]

        self._build_world()

    def _build_world(self):
        # Set bounds of the arena
        self.arena = rl.Rectangle(
            32, 152, rl.get_screen_width() - 64, rl.get_screen_height() - 184
        )

        # Build world
        self.round = 1
        self.result = None
        self.food_starting_balance = wallet.food
        self.world = World()
        # SwarmBehaviorSystem determines how the swarms are going to move
        self.world.register_system(SwarmBehaviorSystem())
        # Move everything next so battle/food logic uses updated positions
        move_system = MovementSystem((
            self.arena.x + 24,
            self.arena.y + 80,
            self.arena.x + self.arena.width - 24,
            self.arena.y + self.arena.height - 28
        ))
        self.world.register_system(move_system)
        self.world.register_system(BattleSystem(wallet))
        self.world.register_system(FoodSystem(wallet, move_system.bounds))
        # Finally draw the swarms
        self.world.register_system(SwarmRenderSystem(rl.get_screen_width(),
                                                     rl.get_screen_height()))

        # Spawn initial bugs
        center_y = self.arena.y + self.arena.height / 2
        self._spawn_swarm(
            self.arena.x + self.arena.width / 4,
            center_y,
            Team.PLAYER,
            200,
            behavior = SwarmBehaviorType.KEYBOARD_CONTROL
        )
        self._spawn_enemy(center_y)

    def _spawn_swarm(self, x, y, team, speed, attack=None,
                     behavior=SwarmBehaviorType.IDLE):
        entity = self.world.create_entity()
        self.world.add(entity, Position(x, y))
        self.world.add(entity, Velocity())
        self.world.add(entity, Team(team))
        self.world.add(entity, Movement(speed))
        self.world.add(entity, Health())
        self.world.add(entity, Attack() if attack is None else attack)
        self.world.add(entity, behavior)
        # Only enemies give food when they die
        if team == Team.AI:
            self.world.add(entity, FoodDrop(5))
        
    def _spawn_enemy(self, y):
        # Give the AI a harder hit but a shorter reach so moving matters.
        enemy_attack = Attack(damage=12, attack_range=55)
        self._spawn_swarm(
            self.arena.x + self.arena.width * 3 / 4,
            y,
            Team.AI,
            100,
            enemy_attack,
            SwarmBehaviorType.CHASE
        )

    def handle_input(self):
        # Screen-level inputs (in-game controls are handled in ECS)
        super().handle_input()
        if self.result is not None:
            if rl.is_key_pressed(rl.KEY_R):
                self._build_world() # Reset
            return
        if rl.is_key_pressed(rl.KEY_E):
            self.screen_stack.push(PauseScreen(self.screen_stack))

    def update(self):
        if self.result is not None:
            return

        self.world.update(rl.get_frame_time())
        teams = {team.name for (team,) in self.world.query(Team)}
        if Team.PLAYER not in teams:
            self._end("Game over")
        elif Team.AI not in teams:
            self.round += 1
            self._spawn_enemy(self.arena.y + self.arena.height / 2)

    def _end(self, message):
        self.result = message
        rounds_survived = max(0, self.round - 1)
        food_collected = max(0, wallet.food - self.food_starting_balance)
        self.screen_stack.push(
            GameOverScreen(
                self.screen_stack,
                message,
                self._build_world,
                rounds_survived,
                food_collected
            )
        )

    def render(self):
        rl.draw_rectangle_gradient_v(
            0, 0,
            rl.get_screen_width(),
            rl.get_screen_height(),
            rl.DARKGREEN,
            rl.BROWN
        )

        rl.draw_text("Bug Game", 280, 100, 30, rl.GREEN)

        rl.draw_rectangle_rec(self.arena, rl.DARKGRAY)
        rl.draw_rectangle_lines_ex(
            self.arena, 2, rl.LIGHTGRAY
        )

        rl.draw_text(
            "Move with WASD or arrows. Stay just out of the AI's reach.",
            int(self.arena.x + 16), int(self.arena.y + 14), 18, rl.WHITE,
        )
        rl.draw_text(
            f"Round: {self.round}",
            int(self.arena.x + 16), int(self.arena.y + 40), 20, rl.YELLOW,
        )
        rl.draw_text(
            f"Food: {wallet.food}",
            int(self.arena.x + 16), int(self.arena.y + 66), 20, rl.YELLOW,
        )

        # Draw food pickups first so swarms appear on top of them.
        for position, _food in self.world.query(Position, Food):
            rl.draw_circle(int(position.x), int(position.y), 7, rl.GREEN)

        # World.render was added recently, and so far SwarmRenderSystem
        # is the only system which uses it, so swarm particles are drawn
        # here. Other rendering logic may be moved into Systems later.
        self.world.render()

        for position, team, health, attack in self.world.query(
            Position, Team, Health, Attack
        ):
            is_player = team.name == Team.PLAYER
            color = rl.SKYBLUE if is_player else rl.ORANGE
            range_color = (
                rl.Color(100, 180, 240, 150)
                if is_player
                else rl.Color(255, 170, 80, 150)
            )
            rl.draw_circle_lines(
                int(position.x),
                int(position.y),
                attack.range,
                range_color,
            )

            health_ratio = (
                max(0.0, min(1.0, health.bugs / health.max_bugs))
                if health.max_bugs > 0
                else 0.0
            )
            bar_width = 36
            bar_height = 5
            bar = rl.Rectangle(
                position.x - bar_width / 2,
                position.y - 25,
                bar_width,
                bar_height,
            )
            rl.draw_rectangle_rec(bar, rl.DARKGRAY)
            health_bar = rl.Rectangle(
                bar.x,
                bar.y,
                bar_width * health_ratio,
                bar_height,
            )
            health_color = rl.Color(
                round(255 * (1 - health_ratio)),
                round(255 * health_ratio),
                0,
                255,
            )
            rl.draw_rectangle_rec(health_bar, health_color)
        super().render()
