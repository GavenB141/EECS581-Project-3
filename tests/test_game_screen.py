import unittest
from unittest.mock import patch

import pyray as rl

from battle import Health, Position, Team
from main import BattleGameScreen
from stack_screen import Button, PauseScreen, Stack, TitleScreen


class GameScreenTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(rl, "get_screen_width", return_value=800))
        self.enterContext(patch.object(rl, "get_screen_height", return_value=600))
        self.enterContext(patch.object(rl, "get_frame_time", return_value=1 / 60))
        self.enterContext(patch.object(Button, "is_clicked", return_value=False))
        self.stack = Stack()
        self.stack.push(TitleScreen(self.stack))
        self.stack.peek().buttons[0].action()
        self.game = self.stack.peek()

    def test_start_game_spawns_both_swarms(self):
        self.assertIsInstance(self.game, BattleGameScreen)
        self.assertEqual(self.survivors(), {Team.PLAYER: 100, Team.AI: 100})

    def test_keyboard_controls(self):
        for keys, direction in (
            ({rl.KEY_A}, (-1, 0)), ({rl.KEY_LEFT}, (-1, 0)),
            ({rl.KEY_D}, (1, 0)), ({rl.KEY_RIGHT}, (1, 0)),
            ({rl.KEY_W}, (0, -1)), ({rl.KEY_UP}, (0, -1)),
            ({rl.KEY_S}, (0, 1)), ({rl.KEY_DOWN}, (0, 1)),
            ({rl.KEY_A, rl.KEY_LEFT}, (-1, 0)),
            ({rl.KEY_W, rl.KEY_RIGHT}, (1, -1)),
            ({rl.KEY_A, rl.KEY_RIGHT, rl.KEY_UP, rl.KEY_S}, (0, 0)),
            (set(), (0, 0)),
        ):
            with self.subTest(keys=keys), patch.object(rl, "is_key_down", side_effect=keys.__contains__):
                self.game.handle_input()
                self.assertEqual(self.game.movement.player_direction, direction)

    def test_idle_player_loses_and_can_restart(self):
        for _ in range(600):
            self.game.update()
        self.assertEqual(self.game.result, "Game over")
        self.assertNotIn(Team.PLAYER, self.survivors())

        with patch.object(rl, "is_key_pressed", side_effect=lambda key: key == rl.KEY_R):
            self.game.handle_input()
        self.assertIsNone(self.game.result)
        self.assertEqual(self.survivors(), {Team.PLAYER: 100, Team.AI: 100})

    def test_player_can_win_by_staying_outside_enemy_attack_range(self):
        positions = {team.name: position for position, team in self.game.world.query(Position, Team)}
        player = positions[Team.PLAYER]
        enemy = positions[Team.AI]
        for _ in range(600):
            if self.game.result is not None:
                break
            distance = enemy.x - player.x
            # Back up when the AI gets close, then let it catch up again.
            self.game.movement.player_direction = (-1, 0) if distance <= 58 else (0, 0)
            self.game.update()

        self.assertEqual(self.game.result, "You win!")
        self.assertIn(Team.PLAYER, self.survivors())

    def test_pause_resumes_the_same_match(self):
        self.game.buttons[0].action()
        self.assertIsInstance(self.stack.peek(), PauseScreen)
        self.stack.peek().buttons[0].action()
        self.assertIs(self.stack.peek(), self.game)

    def test_pause_main_menu_clears_the_match(self):
        self.game.buttons[0].action()
        self.stack.peek().buttons[1].action()
        self.assertIsInstance(self.stack.peek(), TitleScreen)
        self.assertEqual(len(self.stack), 1)

    def survivors(self):
        return {team.name: health.current for team, health in self.game.world.query(Team, Health)}
