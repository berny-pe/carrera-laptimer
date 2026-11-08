import unittest

import SlotcarLapTimer as app_module
from lap_timer.core import LapTimer


class AppRouteTests(unittest.TestCase):
    def setUp(self):
        # fixed lane count, independent of the LANE_PINS in config.py
        app_module.lap_timer = LapTimer(num_lanes=4)
        self.client = app_module.app.test_client()

    def test_root_shows_setup_until_configured(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/race').status_code, 302)

    def test_configure_then_root_redirects_to_race(self):
        resp = self.client.post('/api/configure', json={'mode': 'laps', 'laps': 5})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.client.get('/').headers['Location'], '/race')
        page = self.client.get('/race').get_data(as_text=True)
        self.assertIn('Race to 5 laps', page)

    def test_configure_rejects_bad_input(self):
        for body in ({'mode': 'laps', 'laps': 0}, {'mode': 'time'}, {'mode': 'x'}, None):
            resp = self.client.post('/api/configure', json=body)
            self.assertEqual(resp.status_code, 400)

    def test_start_requires_configuration_and_reset_returns_to_setup(self):
        self.assertEqual(self.client.post('/api/start_timer').status_code, 409)
        self.client.post('/api/configure', json={'mode': 'time', 'time_seconds': 120})
        self.assertEqual(self.client.post('/api/start_timer').status_code, 200)
        self.assertEqual(self.client.post('/api/configure', json={'mode': 'laps', 'laps': 3}).status_code, 400)
        self.client.post('/api/reset')
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_time_mode_page_and_fragments_show_goal(self):
        self.client.post('/api/configure', json={'mode': 'time', 'time_seconds': 300})
        self.assertIn('Time limit 05:00:000', self.client.get('/race').get_data(as_text=True))
        self.assertIn('Time limit 05:00:000', self.client.get('/elapsed').get_data(as_text=True))
        self.assertIn('Remaining 05:00:000', self.client.get('/elapsed').get_data(as_text=True))

    def test_lap_fragment_shows_lap_target(self):
        self.client.post('/api/configure', json={'mode': 'laps', 'laps': 7})
        self.assertIn('Laps / 7', self.client.get('/lap_times').get_data(as_text=True))

    def test_configure_rejects_wrong_types(self):
        for body in ({'mode': 'laps', 'laps': True}, {'mode': 'laps', 'laps': '5'},
                     {'mode': 'time', 'time_seconds': 'abc'}, {'mode': 'time', 'time_seconds': 10**7}):
            self.assertEqual(self.client.post('/api/configure', json=body).status_code, 400)
        self.assertEqual(self.client.post('/api/configure', data='not json').status_code, 400)
        self.assertFalse(app_module.lap_timer.configured)

    def test_check_finished_route(self):
        self.client.post('/api/configure', json={'mode': 'laps', 'laps': 1})
        self.assertFalse(self.client.get('/api/check_finished').get_json()['finished'])


    def test_setup_page_offers_every_lane(self):
        page = self.client.get('/').get_data(as_text=True)
        for n in range(1, app_module.lap_timer.num_lanes + 1):
            self.assertIn(f'name="lane" value="{n}"', page)

    def test_race_page_has_row_and_button_per_selected_lane(self):
        self.client.post('/api/configure', json={'mode': 'laps', 'laps': 3, 'lanes': [1, 2, 4]})
        page = self.client.get('/race').get_data(as_text=True)
        for n in (1, 2, 4):
            self.assertIn(f'lane-{n}', page)
            self.assertIn(f'lap({n})', page)
        self.assertNotIn('lane-3', page)

    def test_configure_rejects_bad_lanes(self):
        for lanes in ([], [9], 'all'):
            resp = self.client.post('/api/configure', json={'mode': 'laps', 'laps': 3, 'lanes': lanes})
            self.assertEqual(resp.status_code, 400)

    def test_lap_route_per_lane_and_legacy_aliases(self):
        self.client.post('/api/configure', json={'mode': 'laps', 'laps': 5})
        self.client.post('/api/start_timer')
        self.assertEqual(self.client.post('/api/lap/4').status_code, 200)
        self.assertEqual(app_module.lap_timer.lanes[3].num_laps, 1)
        self.assertEqual(self.client.post('/api/lap1').status_code, 200)
        self.assertEqual(app_module.lap_timer.lanes[0].num_laps, 1)
        self.assertEqual(self.client.post('/api/lap/99').status_code, 404)


if __name__ == '__main__':
    unittest.main()
