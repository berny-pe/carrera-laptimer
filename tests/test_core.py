import unittest
from unittest.mock import patch

from lap_timer.config import MIN_LAP_SECONDS
from lap_timer.core import LapTimer


class LapTimerCoreTests(unittest.TestCase):
    def test_initial_state_after_reset(self):
        timer = LapTimer(num_lanes=2)

        self.assertFalse(timer.timer_running)
        self.assertIsNone(timer.start_time)
        self.assertEqual(timer.lane1.num_laps, 0)
        self.assertEqual(timer.lane2.num_laps, 0)
        self.assertFalse(timer.check_finished())

    def test_start_and_elapsed_time(self):
        timer = LapTimer(num_lanes=2)

        with patch('lap_timer.core.time.time', return_value=100.0):
            timer.start_timer()

        with patch('lap_timer.core.time.time', return_value=104.5):
            elapsed = timer.elapsed_timer()

        self.assertTrue(timer.timer_running)
        self.assertAlmostEqual(elapsed, 4.5, places=3)

    def test_lane_laps_and_fastest_lap_tracking(self):
        timer = LapTimer(num_lanes=2)

        with patch('lap_timer.core.time.time', return_value=50.0):
            timer.start_timer()

        with patch('lap_timer.core.time.time', return_value=55.0):
            timer.lap_callback1(channel=18)

        with patch('lap_timer.core.time.time', return_value=59.0):
            timer.lap_callback1(channel=18)

        self.assertEqual(timer.lane1.num_laps, 2)
        self.assertAlmostEqual(timer.lane1.last_lap_time, 4.0, places=3)
        self.assertAlmostEqual(timer.lane1.fastest_lap_time, 4.0, places=3)

    def test_stop_continue_accounts_for_pause_duration(self):
        timer = LapTimer(num_lanes=2)

        with patch('lap_timer.core.time.time', return_value=10.0):
            timer.start_timer()

        with patch('lap_timer.core.time.time', side_effect=[15.0, 15.0]):
            timer.stop_timer()

        with patch('lap_timer.core.time.time', return_value=20.0):
            timer.continue_timer()

        with patch('lap_timer.core.time.time', return_value=25.0):
            elapsed = timer.elapsed_timer()

        self.assertTrue(timer.timer_running)
        self.assertAlmostEqual(timer.paused, 5.0, places=3)
        self.assertAlmostEqual(elapsed, 10.0, places=3)

    def test_finished_when_both_lanes_marked_after_stop(self):
        timer = LapTimer(num_lanes=2)

        with patch('lap_timer.core.time.time', return_value=100.0):
            timer.start_timer()

        with patch('lap_timer.core.time.time', side_effect=[110.0, 110.0]):
            timer.stop_timer()

        with patch('lap_timer.core.time.time', return_value=111.0):
            timer.lap_callback1(channel=18)

        with patch('lap_timer.core.time.time', return_value=112.0):
            timer.lap_callback2(channel=23)

        self.assertTrue(timer.lane1.finished)
        self.assertTrue(timer.lane2.finished)
        self.assertTrue(timer.check_finished())


class RaceModeTests(unittest.TestCase):
    def _started(self, **config):
        timer = LapTimer(num_lanes=2)
        timer.configure(**config)
        with patch('lap_timer.core.time.time', return_value=100.0):
            timer.start_timer()
        return timer

    def _lap(self, timer, lane, at):
        with patch('lap_timer.core.time.time', return_value=at):
            (timer.lap_callback1 if lane == 1 else timer.lap_callback2)()

    def test_configure_validation(self):
        timer = LapTimer(num_lanes=2)
        for kwargs in ({'mode': 'bogus'}, {'mode': 'laps'}, {'mode': 'laps', 'laps': 0},
                       {'mode': 'laps', 'laps': '5'}, {'mode': 'time', 'time_seconds': 0},
                       {'mode': 'time'}):
            with self.assertRaises(ValueError):
                timer.configure(**kwargs)
        self.assertFalse(timer.configured)

    def test_configure_rejected_after_start_and_cleared_by_reset(self):
        timer = self._started(mode='laps', laps=3)
        with self.assertRaises(ValueError):
            timer.configure('laps', laps=5)
        timer.reset()
        self.assertFalse(timer.configured)

    def test_lap_race_lane_finishes_at_target_and_race_ends_when_both_done(self):
        timer = self._started(mode='laps', laps=2)
        self._lap(timer, 1, 110.0)
        self._lap(timer, 2, 111.0)
        self.assertFalse(timer.lane1.finished)

        self._lap(timer, 1, 120.0)  # lane 1 reaches target
        self.assertTrue(timer.lane1.finished)
        self.assertTrue(timer.timer_running)
        self.assertFalse(timer.check_finished())

        self._lap(timer, 1, 125.0)  # ignored, lane is done
        self.assertEqual(timer.lane1.num_laps, 2)

        self._lap(timer, 2, 130.0)
        self.assertTrue(timer.check_finished())
        self.assertFalse(timer.timer_running)
        self.assertTrue(timer.ended)
        self.assertAlmostEqual(timer.elapsed_time, 30.0, places=3)
        self.assertEqual(timer._winner(), 1)

    def test_ended_race_cannot_be_continued_or_restarted(self):
        timer = self._started(mode='laps', laps=1)
        self._lap(timer, 1, 105.0)
        self._lap(timer, 2, 106.0)
        with patch('lap_timer.core.time.time', return_value=200.0):
            timer.continue_timer()
            timer.start_timer()
        self.assertFalse(timer.timer_running)
        self.assertEqual(timer.start_time, 100.0)

    def test_time_race_ends_at_limit_and_freezes_clock(self):
        timer = self._started(mode='time', time_seconds=60)
        self._lap(timer, 1, 130.0)

        with patch('lap_timer.core.time.time', return_value=170.0):
            self.assertFalse(timer.check_finished())
        self.assertFalse(timer.timer_running)
        self.assertTrue(timer.ended)
        self.assertEqual(timer.elapsed_time, 60.0)

        with patch('lap_timer.core.time.time', return_value=500.0):
            self.assertEqual(timer.elapsed_timer(), 60.0)

    def test_time_race_lane_finishes_on_next_crossing_after_limit(self):
        timer = self._started(mode='time', time_seconds=60)
        self._lap(timer, 1, 130.0)
        self._lap(timer, 1, 165.0)  # crossing after the limit, no poll happened in between
        self.assertEqual(timer.lane1.num_laps, 2)
        self.assertTrue(timer.lane1.finished)
        self.assertFalse(timer.lane2.finished)
        self.assertEqual(timer.elapsed_time, 60.0)

        self._lap(timer, 2, 170.0)
        self.assertTrue(timer.check_finished())
        self.assertEqual(timer._winner(), 1)

    def test_time_race_time_limit_accounts_for_pause(self):
        timer = self._started(mode='time', time_seconds=60)
        with patch('lap_timer.core.time.time', side_effect=[120.0, 120.0]):
            timer.stop_timer()
        with patch('lap_timer.core.time.time', return_value=220.0):
            timer.continue_timer()  # 100s paused
        with patch('lap_timer.core.time.time', return_value=250.0):
            self.assertFalse(timer.check_finished())
            self.assertTrue(timer.timer_running)  # 20s + 30s = 50s raced
        with patch('lap_timer.core.time.time', return_value=262.0):
            timer.check_finished()
        self.assertTrue(timer.ended)

    def test_winner_tie_on_laps_goes_to_earlier_finisher(self):
        timer = self._started(mode='laps', laps=1)
        self._lap(timer, 2, 105.0)
        self._lap(timer, 1, 106.0)
        self.assertEqual(timer._winner(), 2)

    def test_crossing_faster_than_min_lap_seconds_is_ignored(self):
        timer = self._started(mode='laps', laps=3)
        self._lap(timer, 1, 105.0)
        self._lap(timer, 1, 105.0 + MIN_LAP_SECONDS / 2)  # bounce
        self.assertEqual(timer.lane1.num_laps, 1)
        self.assertEqual(timer.lane1.last_total_time, 105.0)

        self._lap(timer, 1, 105.0 + MIN_LAP_SECONDS)  # exactly at the limit counts
        self.assertEqual(timer.lane1.num_laps, 2)

    def test_min_lap_filter_is_per_lane(self):
        timer = self._started(mode='laps', laps=3)
        self._lap(timer, 1, 105.0)
        self._lap(timer, 2, 105.1)
        self.assertEqual(timer.lane1.num_laps, 1)
        self.assertEqual(timer.lane2.num_laps, 1)

    def test_manual_stop_in_configured_race_can_still_be_continued(self):
        timer = self._started(mode='laps', laps=10)
        with patch('lap_timer.core.time.time', side_effect=[110.0, 110.0]):
            timer.stop_timer()
        self._lap(timer, 1, 111.0)
        self._lap(timer, 2, 112.0)
        self.assertTrue(timer.check_finished())
        self.assertFalse(timer.ended)

        with patch('lap_timer.core.time.time', return_value=120.0):
            timer.continue_timer()
        self.assertTrue(timer.timer_running)
        self.assertFalse(timer.lane1.finished)

    def test_continue_keeps_lane_that_reached_target_finished(self):
        timer = self._started(mode='laps', laps=1)
        self._lap(timer, 1, 105.0)
        with patch('lap_timer.core.time.time', side_effect=[106.0, 106.0]):
            timer.stop_timer()
        with patch('lap_timer.core.time.time', return_value=110.0):
            timer.continue_timer()
        self.assertTrue(timer.lane1.finished)
        self.assertFalse(timer.lane2.finished)
        self._lap(timer, 1, 120.0)
        self.assertEqual(timer.lane1.num_laps, 1)

    def test_time_limit_boundary_and_remaining_time(self):
        timer = self._started(mode='time', time_seconds=60)
        with patch('lap_timer.core.time.time', return_value=140.0):
            self.assertEqual(timer.get_template_data()['formatted_remaining'], '00:20:000')
        with patch('lap_timer.core.time.time', return_value=159.9):
            timer.check_finished()
        self.assertTrue(timer.timer_running)
        with patch('lap_timer.core.time.time', return_value=160.0):
            data = timer.get_template_data()
        self.assertTrue(timer.ended)
        self.assertEqual(data['formatted_remaining'], '00:00:000')

    def test_status_text_progression_in_time_race(self):
        timer = self._started(mode='time', time_seconds=10)
        self._lap(timer, 1, 105.0)
        with patch('lap_timer.core.time.time', return_value=106.0):
            self.assertEqual(timer.get_template_data()['status_text'], '')
        with patch('lap_timer.core.time.time', return_value=115.0):
            timer.check_finished()
            self.assertEqual(timer.get_template_data()['status_text'], 'Time is up - finish your lap')
        self._lap(timer, 1, 120.0)
        self._lap(timer, 2, 121.0)
        with patch('lap_timer.core.time.time', return_value=122.0):
            self.assertEqual(timer.get_template_data()['status_text'], 'Race finished - winner: Lane 1')

    def test_crossing_after_time_up_inside_min_lap_window_is_ignored(self):
        timer = self._started(mode='time', time_seconds=60)
        self._lap(timer, 1, 159.5)
        self._lap(timer, 1, 160.2)  # after the limit but a bounce of the previous crossing
        self.assertEqual(timer.lane1.num_laps, 1)
        self.assertFalse(timer.lane1.finished)

    def test_winner_undecided_without_laps_and_exact_tie(self):
        timer = self._started(mode='laps', laps=1)
        self.assertIsNone(timer._winner())
        timer.lane1.finished = timer.lane2.finished = True
        self.assertIsNone(timer._winner())
        timer.lane1.num_laps = timer.lane2.num_laps = 1
        timer.lane1.last_total_time = timer.lane2.last_total_time = 105.0
        self.assertEqual(timer._winner(), 0)

    def test_configure_rejects_bool_float_laps_and_accepts_float_seconds(self):
        timer = LapTimer(num_lanes=2)
        for laps in (True, 2.5, None):
            with self.assertRaises(ValueError):
                timer.configure('laps', laps=laps)
        timer.configure('time', time_seconds=90.5)
        self.assertEqual(timer.time_limit, 90.5)
        self.assertIsNone(timer.target_laps)

    def test_free_mode_unchanged(self):
        timer = LapTimer(num_lanes=2)
        with patch('lap_timer.core.time.time', return_value=100.0):
            timer.start_timer()
        for i in range(5):
            self._lap(timer, 1, 110.0 + i)
        self.assertTrue(timer.timer_running)
        self.assertFalse(timer.lane1.finished)

    def test_template_data_includes_goal_and_remaining(self):
        timer = self._started(mode='time', time_seconds=90)
        data = timer.get_template_data()
        self.assertEqual(data['goal_text'], 'Time limit 01:30:000')
        self.assertIsNotNone(data['formatted_remaining'])
        timer2 = self._started(mode='laps', laps=7)
        self.assertEqual(timer2.get_template_data()['lap_goal'], ' / 7')


class MultiLaneTests(unittest.TestCase):
    def _started(self, num_lanes=4, **config):
        timer = LapTimer(num_lanes=num_lanes)
        timer.configure(**config)
        with patch('lap_timer.core.time.time', return_value=100.0):
            timer.start_timer()
        return timer

    def _lap(self, timer, lane, at):
        with patch('lap_timer.core.time.time', return_value=at):
            timer.lap_callback(lane)

    def test_default_lane_count_comes_from_config(self):
        from lap_timer.lanes import lane_pins
        self.assertEqual(len(LapTimer().lanes), len(lane_pins()))

    def test_env_override_and_validation(self):
        from lap_timer.lanes import lane_pins
        with patch.dict('os.environ', {'SLOT_LANE_PINS': '5, 6'}):
            self.assertEqual(lane_pins(), [5, 6])
            self.assertEqual(len(LapTimer().lanes), 2)
        for bad in (',', '5,5', 'x'):
            with patch.dict('os.environ', {'SLOT_LANE_PINS': bad}):
                with self.assertRaises(ValueError):
                    lane_pins()

    def test_invalid_lane_count(self):
        for bad in (0, -1, 'x', True):
            with self.assertRaises(ValueError):
                LapTimer(num_lanes=bad)

    def test_race_ends_only_when_all_four_lanes_finished(self):
        timer = self._started(mode='laps', laps=1)
        for lane, at in ((1, 110.0), (2, 111.0), (3, 112.0)):
            self._lap(timer, lane, at)
            self.assertFalse(timer.check_finished())
        self._lap(timer, 4, 113.0)
        self.assertTrue(timer.check_finished())
        self.assertTrue(timer.ended)
        self.assertEqual(timer._winner(), 1)

    def test_winner_is_not_limited_to_first_two_lanes(self):
        timer = self._started(mode='laps', laps=2)
        for lane, at in ((3, 110.0), (3, 115.0), (1, 120.0), (1, 125.0),
                         (2, 130.0), (2, 135.0), (4, 140.0), (4, 145.0)):
            self._lap(timer, lane, at)
        self.assertEqual(timer._winner(), 3)
        self.assertEqual(timer.get_template_data()['status_text'], 'Race finished - winner: Lane 3')

    def test_time_race_ranks_by_laps_then_first_crossing(self):
        timer = self._started(mode='time', time_seconds=60)
        for lane, at in ((4, 110.0), (4, 120.0), (2, 125.0), (2, 130.0), (1, 135.0)):
            self._lap(timer, lane, at)
        for lane, at in ((1, 165.0), (2, 166.0), (3, 167.0), (4, 168.0)):
            self._lap(timer, lane, at)
        self.assertTrue(timer.check_finished())
        # lanes 2 and 4 both have 3 laps, lane 2 crossed first
        self.assertEqual(timer._winner(), 2)

    def test_inactive_lanes_do_not_block_the_race(self):
        timer = self._started(mode='laps', laps=1, lanes=[2, 4])
        self._lap(timer, 1, 110.0)  # inactive: ignored
        self.assertEqual(timer.lanes[0].num_laps, 0)
        self._lap(timer, 4, 111.0)
        self.assertFalse(timer.check_finished())
        self._lap(timer, 2, 112.0)
        self.assertTrue(timer.check_finished())
        self.assertEqual(timer._winner(), 4)

    def test_template_data_lists_only_active_lanes(self):
        timer = self._started(mode='laps', laps=3, lanes=[1, 3])
        self.assertEqual([l['number'] for l in timer.get_template_data()['lanes']], [1, 3])

    def test_lane_validation(self):
        timer = LapTimer(num_lanes=4)
        for lanes in ([], [0], [5], ['1'], [True], 'all', 3):
            with self.assertRaises(ValueError):
                timer.configure('laps', laps=3, lanes=lanes)
        self.assertFalse(timer.configured)

    def test_unknown_lane_callback_rejected(self):
        timer = LapTimer(num_lanes=4)
        for lane in (0, 5, 'x'):
            with self.assertRaises(ValueError):
                timer.lap_callback(lane)

    def test_continue_keeps_each_lane_that_reached_target_finished(self):
        timer = self._started(mode='laps', laps=1)
        self._lap(timer, 3, 110.0)
        with patch('lap_timer.core.time.time', side_effect=[111.0, 111.0]):
            timer.stop_timer()
        with patch('lap_timer.core.time.time', return_value=115.0):
            timer.continue_timer()
        self.assertEqual([l.finished for l in timer.lanes], [False, False, True, False])


if __name__ == '__main__':
    unittest.main()
