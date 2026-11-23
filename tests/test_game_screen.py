import unittest
from unittest.mock import patch

import pyray as rl

from battle import Attack, Health, Position, Team
from food import wallet
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
        self.assertIsInstance(self.game, GameScreen)
        self.assertEqual(self.survivors(), {Team.PLAYER: 100, Team.AI: 100})
        self.assertEqual(self.game.round, 1)

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

    def test_e_opens_pause_menu_and_stops_movement(self):
        self.game.movement.player_direction = (1, 0)

        with patch.object(rl, "is_key_pressed", side_effect=lambda key: key == rl.KEY_E):
            self.game.handle_input()

        self.assertIsInstance(self.stack.peek(), PauseScreen)
        self.assertIs(self.stack.stack[-2], self.game)
        self.assertEqual(self.game.movement.player_direction, (0, 0))

    def test_idle_player_loses_and_can_restart(self):
        for _ in range(600):
            self.game.update()
        self.assertEqual(self.game.result, "Game over")
        self.assertNotIn(Team.PLAYER, self.survivors())

        with patch.object(rl, "is_key_pressed", side_effect=lambda key: key == rl.KEY_R):
            self.game.handle_input()
        self.assertIsNone(self.game.result)
        self.assertEqual(self.survivors(), {Team.PLAYER: 100, Team.AI: 100})

    def test_game_over_shows_rounds_survived_and_food_collected(self):
        starting_food = wallet.food
        self.addCleanup(setattr, wallet, "food", starting_food)
        wallet.food += 9
        self.game.round = 3
        self.game._end_round("Game over")
        game_over = self.stack.peek()

        with (
            patch.object(rl, "draw_rectangle_gradient_v"),
            patch.object(rl, "draw_rectangle_rec"),
            patch.object(rl, "draw_rectangle_lines_ex"),
            patch.object(rl, "draw_text") as draw_text,
            patch.object(rl, "measure_text", return_value=100),
        ):
            game_over.render()

        displayed_text = [call.args[0] for call in draw_text.call_args_list]
        self.assertIn("Rounds survived: 2", displayed_text)
        self.assertIn("Food collected: 9", displayed_text)

    def test_defeating_enemy_advances_round_without_game_over(self):
        player_health = next(
            health for team, health in self.game.world.query(Team, Health)
            if team.name == Team.PLAYER
        )
        player_health.bugs = 75
        enemy_health = next(
            health for team, health in self.game.world.query(Team, Health)
            if team.name == Team.AI
        )
        enemy_health.bugs = 0

        self.game.update()

        self.assertEqual(self.game.round, 2)
        self.assertIsNone(self.game.result)
        self.assertIs(self.stack.peek(), self.game)
        self.assertEqual(self.survivors(), {Team.PLAYER: 75, Team.AI: 100})

    def test_render_shows_health_bars_above_entities(self):
        health_by_team = {
            team.name: health
            for team, health in self.game.world.query(Team, Health)
        }
        health_by_team[Team.PLAYER].current = 50
        health_by_team[Team.AI].current = 25

        with (
            patch.object(rl, "draw_rectangle_rec") as draw_rectangle,
            patch.object(rl, "draw_rectangle_lines_ex"),
            patch.object(rl, "draw_rectangle_gradient_v"),
            patch.object(rl, "draw_text") as draw_text,
            patch.object(rl, "draw_circle"),
            patch.object(rl, "draw_circle_lines"),
        ):
            self.game.render()

        self.assertIn(
            "Round: 1",
            [call.args[0] for call in draw_text.call_args_list],
        )

        bar_calls = [
            call for call in draw_rectangle.call_args_list
            if call.args[0].height == 5
        ]
        positions_by_team = {
            team.name: position
            for position, team in self.game.world.query(Position, Team)
        }
        player_bar_y = positions_by_team[Team.PLAYER].y - 25
        ai_bar_y = positions_by_team[Team.AI].y - 25

        def color_channels(color):
            if isinstance(color, tuple):
                return color
            return color.r, color.g, color.b, color.a

        self.assertEqual(
            [
                (
                    call.args[0].x,
                    call.args[0].y,
                    call.args[0].width,
                    color_channels(call.args[1]),
                )
                for call in bar_calls
            ],
            [
                (
                    positions_by_team[Team.PLAYER].x - 18,
                    player_bar_y,
                    36,
                    (80, 80, 80, 255),
                ),
                (
                    positions_by_team[Team.PLAYER].x - 18,
                    player_bar_y,
                    18,
                    (128, 128, 0, 255),
                ),
                (
                    positions_by_team[Team.AI].x - 18,
                    ai_bar_y,
                    36,
                    (80, 80, 80, 255),
                ),
                (
                    positions_by_team[Team.AI].x - 18,
                    ai_bar_y,
                    9,
                    (191, 64, 0, 255),
                ),
            ],
        )
        self.assertFalse(
            any(
                call.args[0].startswith(("Player ", "AI "))
                for call in draw_text.call_args_list
            )
        )

    def test_render_shows_each_entity_attack_range(self):
        with (
            patch.object(rl, "draw_rectangle_rec"),
            patch.object(rl, "draw_rectangle_lines_ex"),
            patch.object(rl, "draw_rectangle_gradient_v"),
            patch.object(rl, "draw_text"),
            patch.object(rl, "draw_circle"),
            patch.object(rl, "draw_circle_lines") as draw_range,
        ):
            self.game.render()

        attack_ranges = {
            team.name: attack.range
            for team, attack in self.game.world.query(Team, Attack)
        }
        positions_by_team = {
            team.name: position
            for position, team in self.game.world.query(Position, Team)
        }
        self.assertEqual(
            [
                call.args[:3]
                for call in draw_range.call_args_list
            ],
            [
                (
                    int(positions_by_team[Team.PLAYER].x),
                    int(positions_by_team[Team.PLAYER].y),
                    attack_ranges[Team.PLAYER],
                ),
                (
                    int(positions_by_team[Team.AI].x),
                    int(positions_by_team[Team.AI].y),
                    attack_ranges[Team.AI],
                ),
            ],
        )

    def test_pause_resumes_the_same_match(self):
        self.game.buttons[0].action()
        self.assertIsInstance(self.stack.peek(), PauseScreen)
        self.stack.peek().buttons[0].action()
        self.assertIs(self.stack.peek(), self.game)

    def test_pause_renders_previous_screen_behind_compact_overlay(self):
        self.game.buttons[0].action()
        pause_screen = self.stack.peek()
        events = []

        with (
            patch.object(
                self.game,
                "render",
                side_effect=lambda: events.append("background"),
            ) as render_background,
            patch.object(
                rl,
                "draw_rectangle",
                side_effect=lambda *args: events.append("overlay"),
            ) as draw_overlay,
            patch.object(rl, "draw_rectangle_rec"),
            patch.object(rl, "draw_rectangle_lines_ex"),
            patch.object(rl, "draw_rectangle_gradient_v") as draw_gradient,
            patch.object(rl, "draw_text"),
            patch.object(rl, "measure_text", return_value=90),
        ):
            pause_screen.render()

        render_background.assert_called_once()
        self.assertEqual(events[:2], ["background", "overlay"])
        self.assertEqual(draw_overlay.call_args.args[:4], (0, 0, 800, 600))
        draw_gradient.assert_not_called()

    def test_pause_main_menu_clears_the_match(self):
        self.game.buttons[0].action()
        self.stack.peek().buttons[1].action()
        self.assertIsInstance(self.stack.peek(), TitleScreen)
        self.assertEqual(len(self.stack), 1)

    def survivors(self):
        return {team.name: health.current for team, health in self.game.world.query(Team, Health)}
