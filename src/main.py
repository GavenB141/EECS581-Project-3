'''
Author: Jocelyn Miller, Cooper Fish
KUID: 3090871
Last Modified: 11.10.26
Modification: Add swarm movement and controls to BattleGameScreen
Purpose: Connect swarm movement, combat, and rendering to the game screen
'''
import pyray as rl
import stack_screen
from stack_screen import Stack, TitleScreen, GameScreen
from world import World
from battle import Attack, BattleSystem, Health, Position, Team
from swarm_movement import Movement, SwarmMovement

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

        # Leave space for the health text and keep the circles inside the border.
        self.movement = SwarmMovement((
            arena.x + 24,
            arena.y + 80,
            arena.x + arena.width - 24,
            arena.y + arena.height - 28,
        ))
        self._start_round()

    def _start_round(self):
        self.result = None
        self.movement.player_direction = (0, 0)
        self.world = World()
        # Move the swarms first so attacks use their new positions.
        self.world.register_system(self.movement)
        self.world.register_system(BattleSystem())

        arena = self.arena
        center_y = arena.y + arena.height / 2
        self._spawn_swarm(arena.x + arena.width / 4, center_y, Team.PLAYER, 200)
        # Give the AI a harder hit but a shorter reach so moving matters.
        enemy_attack = Attack(damage=12, attack_range=55)
        self._spawn_swarm(arena.x + arena.width * 3 / 4, center_y, Team.AI, 100, enemy_attack)

    def _spawn_swarm(self, x, y, team, speed, attack=None):
        entity = self.world.create_entity()
        self.world.add(entity, Position(x, y))
        self.world.add(entity, Team(team))
        self.world.add(entity, Movement(speed))
        self.world.add(entity, Health())
        self.world.add(entity, Attack() if attack is None else attack)

    def handle_input(self):
        super().handle_input()
        if self.screen_stack.peek() is not self:
            self.movement.player_direction = (0, 0)
            return
        if self.result is not None:
            if rl.is_key_pressed(rl.KEY_R):
                self._start_round()
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
            self.result = "Game over"
        elif Team.AI not in teams:
            self.result = "You win!"

    def render(self):
        super().render()
        rl.draw_rectangle_rec(self.arena, rl.DARKGRAY)
        rl.draw_rectangle_lines_ex(self.arena, 2, rl.LIGHTGRAY)
        rl.draw_text(
            "Move with WASD or arrows. Stay just out of the AI's reach.",
            int(self.arena.x + 16), int(self.arena.y + 14), 18, rl.WHITE,
        )

        for position, team, health in self.world.query(Position, Team, Health):
            is_player = team.name == Team.PLAYER
            label, color = ("Player", rl.SKYBLUE) if is_player else ("AI", rl.ORANGE)
            rl.draw_circle(int(position.x), int(position.y), 16, color)

            # Keep the health text at the top so it stays readable during fights.
            status = f"{label} {health.current}/{health.max_hp}"
            status_x = self.arena.x + 16
            if not is_player:
                status_x = self.arena.x + self.arena.width - 16 - rl.measure_text(status, 16)
            rl.draw_text(status, int(status_x), int(self.arena.y + 42), 16, color)

        if self.result is not None:
            rl.draw_rectangle(240, 300, 320, 100, rl.BLACK)
            rl.draw_text(self.result, 400 - rl.measure_text(self.result, 28) // 2, 315, 28, rl.WHITE)
            rl.draw_text("Press R to play again", 280, 360, 20, rl.WHITE)

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
