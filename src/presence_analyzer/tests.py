# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
from __future__ import unicode_literals

import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils

TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {'user_id': 10, 'name': 'User 10'})

    def test_mean_time_weekday(self):
        """
        Test mean presence time for given user.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/0')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')

        data = json.loads(resp.data)
        self.assertEqual(
            data,
            [
                ['Mon', 0],
                ['Tue', 30047.0],
                ['Wed', 24465.0],
                ['Thu', 23705.0],
                ['Fri', 0],
                ['Sat', 0],
                ['Sun', 0],
            ]
        )

        resp = self.client.get('/api/v1/mean_time_weekday/11')
        data = json.loads(resp.data)
        self.assertEqual(
            data,
            [
                ['Mon', 24123.0],
                ['Tue', 16564.0],
                ['Wed', 25321.0],
                ['Thu', 22984.0],
                ['Fri', 6426.0],
                ['Sat', 0],
                ['Sun', 0],
            ]
        )

    def test_presence_weekday(self):
        """
        Test total presence time for given user.
        """
        resp = self.client.get('/api/v1/presence_weekday/0')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')

        data = json.loads(resp.data)
        self.assertEqual(
            data,
            [
                ['Weekday', 'Presence (s)'],
                ['Mon', 0],
                ['Tue', 30047],
                ['Wed', 24465],
                ['Thu', 23705],
                ['Fri', 0],
                ['Sat', 0],
                ['Sun', 0],
            ]
        )

        resp = self.client.get('/api/v1/presence_weekday/11')
        data = json.loads(resp.data)
        self.assertEqual(
            data,
            [
                ['Weekday', 'Presence (s)'],
                ['Mon', 24123],
                ['Tue', 16564],
                ['Wed', 25321],
                ['Thu', 45968],
                ['Fri', 6426],
                ['Sat', 0],
                ['Sun', 0],
            ]
        )


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_group_by_weekday(self):
        """
        Test grouping presences by weekday.
        """

        test_data = {
            datetime.date(2017, 4, 18): {
                'start': datetime.time(8, 15, 0),
                'end': datetime.time(16, 0, 0),
            },
            datetime.date(2017, 4, 19): {
                'start': datetime.time(13, 21, 30),
                'end': datetime.time(15, 4, 2),
            },
        }
        self.assertEqual(
            [[], [27900], [6152], [], [], [], []],
            utils.group_by_weekday(test_data)
        )

        # more dates for weekday 1 to test if they are counted
        test_data[datetime.date(2017, 4, 25)] = {
            'start': datetime.time(0, 0, 0),
            'end': datetime.time(0, 0, 0),
        }
        test_data[datetime.date(2017, 4, 11)] = {
            'start': datetime.time(8, 0, 0),
            'end': datetime.time(16, 0, 0),
        }
        self.assertEqual(3, len(utils.group_by_weekday(test_data)[1]))

        data = utils.get_data()
        self.assertEqual(
            [[], [30047], [24465], [23705], [], [], []],
            utils.group_by_weekday(data[10])
        )
        self.assertEqual(
            [[24123], [16564], [25321], [22969, 22999], [6426], [], []],
            utils.group_by_weekday(data[11])
        )

    def test_seconds_since_midnight(self):
        """
        Test calculation of amount of seconds since midnight.
        """
        midnight = datetime.time(0, 0, 0)
        self.assertEqual(0, utils.seconds_since_midnight(midnight))

        simple = datetime.time(10, 0, 0)
        self.assertEqual(36000, utils.seconds_since_midnight(simple))

        time = datetime.time(12, 20, 5)
        self.assertEqual(44405, utils.seconds_since_midnight(time))

        almost = datetime.time(23, 59, 59)
        self.assertEqual(86399, utils.seconds_since_midnight(almost))

    def test_interval(self):
        """
        Test calculation of interval between start time and end time.
        """
        start = datetime.time(0, 0, 0)
        end = datetime.time(0, 0, 0)
        self.assertEqual(0, utils.interval(start, end))

        start = datetime.time(0, 20, 5)
        end = datetime.time(10, 0, 0)
        self.assertEqual(34795, utils.interval(start, end))

        start = datetime.time(0, 36, 31)
        end = datetime.time(0, 36, 32)
        self.assertEqual(1, utils.interval(start, end))

    def test_mean(self):
        """
        Test calculation of arithmetic mean.
        """
        self.assertEqual(2.0, utils.mean([1, 2, 3]))
        self.assertEqual(2.6, utils.mean([1.5, 2.5, 3.8]))
        self.assertEqual(1.0, utils.mean([0, 2]))
        self.assertEqual(0, utils.mean([]))


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
