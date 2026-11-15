import math
import unittest

from battle import Attack, BattleSystem, Health, Position, Team
from swarm_movement import Movement, SwarmMovement
from world import World


class SwarmMovementTest(unittest.TestCase):
    def setUp(self):
        self.world = World()
        self.movement = SwarmMovement((0, 0, 1000, 1000))
        self.world.register_system(self.movement)

    def spawn(self, team, x, y, speed=100, attack_range=70):
        entity = self.world.create_entity()
        position = Position(x, y)
        health = Health()
        self.world.add(entity, position)
        self.world.add(entity, Team(team))
        self.world.add(entity, Movement(speed))
        self.world.add(entity, Attack(attack_range=attack_range))
        self.world.add(entity, health)
        return entity, position, health

    def assert_position(self, position, expected_x, expected_y):
        self.assertAlmostEqual(position.x, expected_x)
        self.assertAlmostEqual(position.y, expected_y)

    def test_empty_world_is_safe(self):
        self.world.update(1.0)
        self.assertEqual(list(self.world.query(Position)), [])

    def test_idle_player_does_not_move(self):
        _, player, _ = self.spawn(Team.PLAYER, 500, 500)
        self.world.update(1.0)
        self.assert_position(player, 500, 500)

    def test_cardinal_and_diagonal_speed(self):
        _, player, _ = self.spawn(Team.PLAYER, 500, 500, speed=200)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            with self.subTest(direction=(dx, dy)):
                player.x = player.y = 500
                self.movement.player_direction = (dx, dy)
                self.world.update(0.25)
                length = math.hypot(dx, dy)
                self.assert_position(player, 500 + dx * 50 / length, 500 + dy * 50 / length)

    def test_zero_time_does_not_move_either_swarm(self):
        _, player, _ = self.spawn(Team.PLAYER, 100, 200)
        _, enemy, _ = self.spawn(Team.AI, 500, 600)
        self.movement.player_direction = (1, -1)
        self.world.update(0)
        self.assert_position(player, 100, 200)
        self.assert_position(enemy, 500, 600)

    def test_bounds_clamp_all_four_edges(self):
        _, player, _ = self.spawn(Team.PLAYER, 500, 500)
        for direction, expected in (
            ((-1, 0), (0, 500)), ((1, 0), (1000, 500)),
            ((0, -1), (500, 0)), ((0, 1), (500, 1000)), ((1, -1), (1000, 0)),
        ):
            with self.subTest(direction=direction):
                player.x = player.y = 500
                self.movement.player_direction = direction
                self.world.update(10)
                self.assert_position(player, *expected)

    def test_player_speed_is_consistent_across_frame_rates(self):
        _, player, _ = self.spawn(Team.PLAYER, 500, 500, speed=200)
        for fps in (30, 60, 144):
            with self.subTest(fps=fps):
                player.x = player.y = 500
                self.movement.player_direction = (1, -1)
                for _ in range(fps):
                    self.world.update(1 / fps)
                self.assert_position(player, 500 + 200 / math.sqrt(2), 500 - 200 / math.sqrt(2))

    def test_ai_chases_diagonally(self):
        _, player, _ = self.spawn(Team.PLAYER, 300, 300)
        _, enemy, _ = self.spawn(Team.AI, 500, 500, speed=100)
        self.world.update(0.5)
        self.assert_position(enemy, 500 - 50 / math.sqrt(2), 500 - 50 / math.sqrt(2))
        self.assert_position(player, 300, 300)

    def test_ai_stops_in_range_even_on_a_long_frame(self):
        self.spawn(Team.PLAYER, 300, 300)
        _, enemy, _ = self.spawn(Team.AI, 900, 300)
        self.world.update(20)
        self.assert_position(enemy, 356, 300)
        self.world.update(1)
        self.assert_position(enemy, 356, 300)

    def test_ai_stays_still_when_positions_overlap(self):
        self.spawn(Team.PLAYER, 300, 300)
        _, enemy, _ = self.spawn(Team.AI, 300, 300)
        self.world.update(1)
        self.assert_position(enemy, 300, 300)

    def test_ai_resumes_chase_when_player_moves_away(self):
        self.spawn(Team.PLAYER, 300, 300, speed=200)
        _, enemy, _ = self.spawn(Team.AI, 356, 300)
        self.movement.player_direction = (-1, 0)
        self.world.update(0.5)
        self.assert_position(enemy, 306, 300)

    def test_ai_uses_updated_player_position_even_if_it_spawned_first(self):
        _, enemy, _ = self.spawn(Team.AI, 600, 400)
        self.spawn(Team.PLAYER, 400, 400, speed=200)
        self.movement.player_direction = (0, -1)
        self.world.update(0.5)
        self.assertLess(enemy.y, 400)

    def test_multiple_enemies_use_their_own_attack_range(self):
        self.spawn(Team.PLAYER, 500, 500)
        _, near_enemy, _ = self.spawn(Team.AI, 900, 500, attack_range=50)
        _, far_enemy, _ = self.spawn(Team.AI, 100, 500, attack_range=125)
        self.world.update(10)
        self.assert_position(near_enemy, 540, 500)
        self.assert_position(far_enemy, 400, 500)

    def test_ai_waits_if_the_player_is_removed(self):
        player, _, _ = self.spawn(Team.PLAYER, 300, 300)
        _, enemy, _ = self.spawn(Team.AI, 600, 600)
        self.world.delete_entity(player)
        self.world.update(1)
        self.assert_position(enemy, 600, 600)

    def test_other_teams_do_not_chase(self):
        self.spawn(Team.PLAYER, 300, 300)
        _, neutral, _ = self.spawn("neutral", 600, 600)
        self.world.update(1)
        self.assert_position(neutral, 600, 600)

    def test_combat_runs_after_movement_and_removes_defeated_player(self):
        self.world.register_system(BattleSystem())
        player_id, _, player_hp = self.spawn(Team.PLAYER, 300, 300)
        _, enemy, enemy_hp = self.spawn(Team.AI, 440, 300)
        self.world.update(1)
        self.assertLessEqual(enemy.x - 300, 70)
        self.assertEqual((player_hp.current, enemy_hp.current), (90, 90))
        self.world.update(0.1)
        self.assertEqual((player_hp.current, enemy_hp.current), (90, 90))
        player_hp.current = 10
        self.world.update(0.5)
        self.assertEqual(player_hp.current, 0)
        self.assertNotIn(player_id, [entity for entity, _ in self.world.query(type(player_id), Team)])
        self.world.update(0.5)
        self.assert_position(enemy, 356, 300)


if __name__ == "__main__":
    unittest.main(verbosity=2)
