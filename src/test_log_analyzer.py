import unittest
import collections
import json
import datetime as dt
import log_analyzer as la
from unittest import mock

class LogAnalyzerTests(unittest.TestCase):

    config = {
        "REPORT_SIZE": 1000,
        "REPORT_DIR": "../reports",
        "REPORT_TEMPLATE": "./report.html",
        "LOG_DIR": "../log",
        "SUCSESSFUL_PERCENT": "0.95"
    }

    line = '1.199.4.96 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/slot/4705/groups HTTP/1.1" 200 2613 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-3800516057-4708-9752745" "2a828197ae235b0b3cb" 0.704'

    def test_find_last_log_ok(self):
        with mock.patch('os.listdir') as mock_listdir:
            with mock.patch('os.path.isdir') as mock_isdir:
                mock_listdir.return_value = [
                    'bar1',
                    'nginx-access-ui.log-20170625.bz2',
                    'nginx-access-ui.log-20180627',
                    'report.html',
                    'nginx-access-ui.log-20170628',
                    'nginx-access-ui.log-20180628',
                    'nginx-access-ui.log-20170630.gz',
                    'report-2017.06.30.html',
                ]

                mock_isdir.side_effect = [True]

                last_log = la.find_last_log(LogAnalyzerTests.config.get('LOG_DIR'))

                self.assertEqual(last_log.date, dt.datetime(2018, 6, 28))

    def test_find_last_log_no_logfile(self):
        with mock.patch('os.listdir') as mock_listdir:
            with mock.patch('os.path.isdir') as mock_isdir:
                mock_listdir.return_value = []
                mock_isdir.side_effect = [True]

                self.assertRaises(FileNotFoundError,
                                  la.find_last_log,
                                  LogAnalyzerTests.config.get('LOG_DIR'),
                                  )

    def test_make_report_path_ok(self):
        def side_effect(arg):
            if(arg == './report.html' or
               arg == '../reports'
               ):
                return True
            else:
                return False

        patcher = mock.patch('os.path.exists')
        mock_thing = patcher.start()
        mock_thing.side_effect = side_effect

        last_log = collections.namedtuple('last_log', ['date', 'path'])
        last_log.date = dt.datetime(2018, 6, 29)

        path = la.make_report_path(LogAnalyzerTests.config, last_log)
        self.assertEqual(path, '../reports/report-2018.06.29.html')

    def test_make_report_path_no_template(self):
        def side_effect(arg):
                return False

        patcher = mock.patch('os.path.exists')
        mock_thing = patcher.start()
        mock_thing.side_effect = side_effect

        last_log = collections.namedtuple('last_log', ['date', 'path'])
        last_log.date = dt.datetime(2018, 6, 28)

        self.assertRaises(FileNotFoundError,
                          la.make_report_path, LogAnalyzerTests.config,
                          last_log
                          )

    def test_make_report_path_already_exists(self):
        def side_effect(arg):
            if(arg == './report.html' or
               arg == '../reports/report-2018.06.28.html'
               ):
                return True
            else:
                return False

        patcher = mock.patch('os.path.exists')
        mock_thing = patcher.start()
        mock_thing.side_effect = side_effect

        last_log = collections.namedtuple('last_log', ['date', 'path'])
        last_log.date = dt.datetime(2018, 6, 28)

        self.assertRaises(FileExistsError,
                          la.make_report_path, LogAnalyzerTests.config,
                          last_log
                          )

    def test_process_line_ok(self):
        out = la.process_line(LogAnalyzerTests.line, 42)
        self.assertEqual(out, {'url': "/api/v2/slot/4705/groups",
                               'request_time': 0.704
                               }
                         )

    def test_process_line_nok(self):
        line = ''
        self.assertFalse(la.process_line(line, 123))

    def test_collect_url_data(self):
        reader = [{'url': "/url1", 'request_time': 1},
                  {'url': "/url1", 'request_time': 2},
                  {'url': "/url1", 'request_time': 3},
                  {'url': "/url2", 'request_time': 4},
                  ]
        urls = la.collect_url_data(reader)

        self.assertEqual(urls.count, 4)
        self.assertEqual(urls.total_time, 10)
        self.assertEqual(urls.urls, {'/url2': [4], '/url1': [1, 2, 3]})

    def test_calc_statistic(self):
        Urls = collections.namedtuple('Urls', ['urls', 'count'])
        Urls.urls = collections.defaultdict(list)

        Urls.count = 4
        Urls.total_time = 10
        Urls.urls = {'/url2': [4], '/url1': [1, 2, 3]}

        stat = la.calc_statistic(LogAnalyzerTests.config, Urls)
        jstat = '[{"count_perc": 75.0, "time_perc": 60.0, "time_med": 2, "time_sum": 6, "time_max": 3, "count": 3, "url": "/url1", "time_avg": 2.0}, {"count_perc": 25.0, "time_perc": 40.0, "time_med": 4, "time_sum": 4, "time_max": 4, "count": 1, "url": "/url2", "time_avg": 4.0}]'
        self.assertEqual(json.loads(stat), json.loads(jstat))


if __name__ == '__main__':
    unittest.main()
