import unittest
from unittest.mock import patch

from lap_timer.config import MIN_LAP_SECONDS
from lap_timer.core import LapTimer


class LapTimerCoreTests(unittest.TestCase):
    def test_initial_state_after_reset(self):
        timer = LapTimer()

        self.assertFalse(timer.timer_running)
        self.assertIsNone(timer.start_time)
        self.assertEqual(timer.lane1.num_laps, 0)
        self.assertEqual(timer.lane2.num_laps, 0)
        self.assertFalse(timer.check_finished())

    def test_start_and_elapsed_time(self):
        timer = LapTimer()

        with patch('lap_timer.core.time.time', return_value=100.0):
            timer.start_timer()

        with patch('lap_timer.core.time.time', return_value=104.5):
            elapsed = timer.elapsed_timer()

        self.assertTrue(timer.timer_running)
        self.assertAlmostEqual(elapsed, 4.5, places=3)

    def test_lane_laps_and_fastest_lap_tracking(self):
        timer = LapTimer()

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
        timer = LapTimer()

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
        timer = LapTimer()

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
        timer = LapTimer()
        timer.configure(**config)
        with patch('lap_timer.core.time.time', return_value=100.0):
            timer.start_timer()
        return timer

    def _lap(self, timer, lane, at):
        with patch('lap_timer.core.time.time', return_value=at):
            (timer.lap_callback1 if lane == 1 else timer.lap_callback2)()

    def test_configure_validation(self):
        timer = LapTimer()
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

    def test_free_mode_unchanged(self):
        timer = LapTimer()
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


if __name__ == '__main__':
    unittest.main()
