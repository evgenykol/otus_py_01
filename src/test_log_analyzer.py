import unittest
import log_analyzer as la


class LogAnalyzerTests(unittest.TestCase):

    def test(self):
        self.assertTrue(True)

    def test_find_last_log(self):
        self.assertTrue(True)

    def test_make_report_path(self):
        self.assertTrue(True)

    def test_process_line_OK(self):
        line = '1.199.4.96 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/slot/4705/groups HTTP/1.1" 200 2613 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-3800516057-4708-9752745" "2a828197ae235b0b3cb" 0.704'
        out = la.process_line(line, 42)
        self.assertEqual(out, {'url': "/api/v2/slot/4705/groups",
                               'request_time': 0.704
                               }
                         )

    def test_process_line_NOK(self):
        line = ''
        self.assertFalse(la.process_line(line, 123))

    def test_xreadlines(self):
        self.assertTrue(True)

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
        self.assertTrue(True)

    def test_write_report(self):
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
