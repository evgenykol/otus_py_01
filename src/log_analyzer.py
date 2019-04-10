#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local]
#                     '"$request" $status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" '
#                     '"$http_X_REQUEST_ID" "$http_X_RB_USER" $request_time';

import collections
import datetime
import fileinput
import gzip
import json
import logging
import os
import re
import shutil
import statistics
import argparse
import sys

logging.basicConfig(
    format='[%(asctime)s] %(levelname).1s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y.%m.%d %H:%M:%S'
)

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "../reports",
    "LOG_DIR": "../log"
}


def find_last_log(cfg, filepat):
    max_date = collections.namedtuple('max_date', ['date', 'path'])
    max_date.date = datetime.datetime(1, 1, 1)
    max_date.path = '0'
    for path, dirlist, filelist in os.walk(cfg["LOG_DIR"]):
        for name in filelist:
            # logging.debug(name)
            if re.match(filepat, name):
                date_re = re.search('[0-9]{8}', name)
                date_str = name[date_re.start():date_re.end()]

                parsed_date = datetime.datetime.strptime(date_str, "%Y%m%d")

                if parsed_date > max_date.date:
                    max_date.date = parsed_date
                    max_date.path = os.path.join(path, name)

    if (max_date.path == '0'):
        raise FileNotFoundError('Log file not found')

    logging.info('Last log created at %s, path: %s' %
                 (max_date.date, max_date.path)
                 )
    return max_date


def make_report_path(cfg, last_log):
    rep_template = os.path.join(cfg['REPORT_DIR'], 'report.html')

    if not os.path.exists(rep_template):
        raise FileNotFoundError('Report template file not found')

    report_path = os.path.join(cfg['REPORT_DIR'],
                               'report-%s.html' % (datetime.datetime.strftime(
                                   last_log.date, '%Y.%m.%d'))
                               )

    if not os.path.exists(report_path):
        logging.info('Writing report at %s', report_path)
        return report_path
    else:
        raise FileExistsError('Report at %s already exists' % report_path)
        return None


def process_line(line, line_number):
    try:
        elems = line.split(' ')
        if not elems[7][0] == '/':
            raise ValueError
        url = elems[7]
        request_time = float(elems[-1])

        # logging.info('url=%s, time=%f' % (url, f))

        return {'url': url, 'request_time': request_time}
    except Exception as e:
        logging.error('Log parsing error at line: %d' % (line_number))
        return False


def xreadlines(path):
    with gzip.open(path, 'rb') if path.endswith('.gz') else open(path) as log:
        total = processed = 0
        for line in log:
            parsed_line = process_line(line, total)
            total += 1
            if parsed_line:
                processed += 1
                yield parsed_line

        sucseccful = float(processed) / float(total)
        logging.info("%s of %s lines processed, sucseccful percent = %f" %
                     (processed, total, sucseccful * 100)
                     )

        if (sucseccful < 0.95):
            raise ValueError('Too many log parsing errors')


def collect_url_data(reader):
    Urls = collections.namedtuple('Urls', ['urls', 'count'])
    Urls.urls = collections.defaultdict(list)
    Urls.count = 0
    Urls.total_time = 0
    for url_data in reader:
        k, v = url_data['url'], url_data['request_time']
        Urls.urls[k].append(v)
        Urls.count += 1
        Urls.total_time += v

    # Maybe I can do it with generator?
    return Urls


def calc_statistic(cfg, urls):
    stat_list = []
    for url, reqtm in urls.urls.items():
        stat = {}
        stat["url"] = url
        stat["count"] = len(reqtm)
        stat["count_perc"] = round(100.0 * (stat["count"] / urls.count), 3)
        stat["time_sum"] = round(sum(reqtm), 3)
        stat["time_perc"] = round(100.0 * (stat["time_sum"] /
                                           urls.total_time), 3
                                  )
        stat["time_avg"] = round(stat["time_sum"] / stat["count"], 3)
        stat["time_max"] = round(max(reqtm), 3)
        stat["time_med"] = round(statistics.median(reqtm), 3)

        stat_list.append(stat)

    sorted_stat = (sorted(stat_list, key=lambda k: k["time_sum"], reverse=True)
                   )[:cfg['REPORT_SIZE']]

    logging.debug('stat_list size = %d, sorted size = %d' %
                  (len(stat_list), len(sorted_stat))
                  )

    return json.dumps(sorted_stat)


def write_report(cfg, path, stat):
    rep_template = os.path.join(cfg['REPORT_DIR'], 'report.html')

    # with open(rep_template, encoding='utf-8') as rep_template_file:
    #     with open(path, mode='w', encoding='utf-8') as report_file:
    #         text = string.Template(rep_template_file.read())
    #         logging.debug('write report stat type %s' % type(stat))
    #         text.substitute(table_json=stat)
    #         # logging.debug('write report text len 1= %d' % len(text))
    #         report_file.write(text)

    shutil.copyfile(rep_template, path)

    with fileinput.FileInput(path, inplace=True) as file:
        for line in file:
            print(line.replace('$table_json', stat))


def read_config(**kwargs):
    print('AAAA')
    logging.info(kwargs['--config'])
    # raise FileNotFoundError('Config file %d not found' % kwargs['--config'])


def init_config():
    print('BBBB')
    parser = argparse.ArgumentParser(prog='log_analyzer')
    parser.add_argument('--config', help='specify config file', default=read_config)
    args = parser.parse_args()


def main():
    try:
        init_config()
        last_log = find_last_log(
            config, '^nginx-access-ui\.log-([0-9]{8}|[0-9]{8}\.gz)$')
        report_path = make_report_path(config, last_log)
        reader = xreadlines(last_log.path)
        urls = collect_url_data(reader)
        stat = calc_statistic(config, urls)
        write_report(config, report_path, stat)

        logging.info('Log analyzing done!')

    except StopIteration as e:
        logging.exception('StopIteration')
    except ValueError as e:
        logging.exception('ValueError')
    except Exception:
        logging.exception('Global exception')


if __name__ == "__main__":
    main()
