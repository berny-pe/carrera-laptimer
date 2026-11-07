import unittest

import CarreraLapTimer as app_module


class AppRouteTests(unittest.TestCase):
    def setUp(self):
        app_module.lap_timer.reset()
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


if __name__ == '__main__':
    unittest.main()
