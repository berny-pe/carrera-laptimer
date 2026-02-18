import unittest
from unittest.mock import patch

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


if __name__ == '__main__':
    unittest.main()
