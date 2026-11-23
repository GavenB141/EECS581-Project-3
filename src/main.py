'''
Author: Jocelyn Miller, Cooper Fish
KUID: 3090871
Last Modified: 11.19.26
Modification: Add food currency (kill rewards, map pickups, HUD) to BattleGameScreen
Purpose: Connect swarm movement, combat, food, and rendering to the game screen
'''
import pyray as rl
import stack_screen
from stack_screen import Stack, TitleScreen, GameScreen, GameOverScreen, PauseScreen
from world import World
from battle import Attack, BattleSystem, FoodDrop, Health, Position, Team
from swarm_movement import Movement, SwarmMovement
from food import Food, FoodSystem, wallet


class BattleGameScreen(GameScreen):
    def __init__(self, screen_stack):
        super().__init__(screen_stack)

        # Move the menu buttons up so they don't cover the arena.
        button_x = 86
        for button in self.buttons:
            button.rec.x = button_x
            button.rec.y = 32
            button_x += button.rec.width + 14

        self.arena = rl.Rectangle(
            32, 152, rl.get_screen_width() - 64, rl.get_screen_height() - 184
        )
        arena = self.arena

        # Leave space for arena instructions and keep the circles inside the border.
        self.movement = SwarmMovement((
            arena.x + 24,
            arena.y + 80,
            arena.x + arena.width - 24,
            arena.y + arena.height - 28,
        ))
        self.round = 1
        self._start_round()

    def _start_round(self):
        self.round = 1
        self.food_starting_balance = wallet.food
        self.result = None
        self.movement.player_direction = (0, 0)
        self.world = World()
        # Move the swarms first so attacks use their new positions.
        self.world.register_system(self.movement)
        self.world.register_system(BattleSystem(wallet))
        # Food runs last so it sees final positions after movement and combat.
        self.world.register_system(FoodSystem(wallet, self.movement.bounds))

        arena = self.arena
        center_y = arena.y + arena.height / 2
        self._spawn_swarm(arena.x + arena.width / 4, center_y, Team.PLAYER, 200)
        self._spawn_enemy(center_y)

    def _spawn_enemy(self, y):
        # Give the AI a harder hit but a shorter reach so moving matters.
        enemy_attack = Attack(damage=12, attack_range=55)
        self._spawn_swarm(
            self.arena.x + self.arena.width * 3 / 4,
            y,
            Team.AI,
            100,
            enemy_attack,
        )

    def _spawn_swarm(self, x, y, team, speed, attack=None):
        entity = self.world.create_entity()
        self.world.add(entity, Position(x, y))
        self.world.add(entity, Team(team))
        self.world.add(entity, Movement(speed))
        self.world.add(entity, Health())
        self.world.add(entity, Attack() if attack is None else attack)
        # Only enemies give food when they die.
        if team == Team.AI:
            self.world.add(entity, FoodDrop(5))

    def handle_input(self):
        super().handle_input()
        if self.result is not None:
            if rl.is_key_pressed(rl.KEY_R):
                if self.screen_stack.peek() is not self:
                    self.screen_stack.pop()
                self._start_round()
            return
        if self.screen_stack.peek() is not self:
            self.movement.player_direction = (0, 0)
            return
        if rl.is_key_pressed(rl.KEY_E):
            self.movement.player_direction = (0, 0)
            self.screen_stack.push(PauseScreen(self.screen_stack))
            return

        # Opposite keys cancel out if you hold both at once.
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
        self.movement.player_direction = (dx, dy)

    def update(self):
        if self.result is not None:
            return

        self.world.update(rl.get_frame_time())
        teams = {team.name for (team,) in self.world.query(Team)}
        if Team.PLAYER not in teams:
            self._end_round("Game over")
        elif Team.AI not in teams:
            self.round += 1
            self._spawn_enemy(self.arena.y + self.arena.height / 2)

    def _end_round(self, message):
        self.result = message
        rounds_survived = max(0, self.round - 1)
        food_collected = max(0, wallet.food - self.food_starting_balance)
        self.screen_stack.push(
            GameOverScreen(
                self.screen_stack,
                message,
                self._start_round,
                rounds_survived,
                food_collected,
            )
        )

    def render(self):
        super().render()
        rl.draw_rectangle_rec(self.arena, rl.DARKGRAY)
        rl.draw_rectangle_lines_ex(self.arena, 2, rl.LIGHTGRAY)
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
            rl.draw_circle(int(position.x), int(position.y), 16, color)

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

stack_screen.GameScreen = BattleGameScreen

def main():
    # Initialize Raylib window
    rl.init_window(800, 600, "Bug Game")
    rl.set_target_fps(60)

    # Instantiate the stack and seed it with the Title Screen
    stack = Stack()
    stack.push(TitleScreen(stack))

    try:
        while not rl.window_should_close() and not stack.is_empty():
            stack.peek().handle_input()
            # A button can change the active screen before this frame is drawn.
            current_screen = stack.peek()
            if current_screen is None:
                break
            current_screen.update()

            rl.begin_drawing()
            rl.clear_background(rl.RAYWHITE)
            current_screen.render()
            rl.end_drawing()
    finally:
        rl.close_window()

if __name__ == "__main__":
    main()
