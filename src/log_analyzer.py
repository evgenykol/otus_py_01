#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local]
#                     '"$request" $status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" '
#                     '"$http_X_REQUEST_ID" "$http_X_RB_USER" $request_time';

import argparse
import gzip
import json
import logging
import os
import re
import statistics
import string
import shutil
from collections import namedtuple, defaultdict
from datetime import datetime

DEFAULT_CONFIG_PATH = './log_analyzer.cfg'

LogInfo = namedtuple('LogInfo', ['date', 'path'])


def get_ext_config_path():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Config file path')
    args = parser.parse_args()
    return args.config


def read_config(path):
    if not os.path.exists(path):
        raise FileNotFoundError('Config file file not found at path: {0}'.format(path))

    with open(path) as cfg_file:
        return json.loads(cfg_file.read())


def init_config(ext_path):
    # default config is mandatory
    config = read_config(DEFAULT_CONFIG_PATH)

    # external config overrides default settings
    if ext_path:
        external_config = read_config(ext_path)
        config.update(external_config)

    return config


def init_logging(cfg):
    loging_path = cfg.get('LOGGING_FILE')

    logging.basicConfig(
        format='[%(asctime)s] %(levelname).1s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y.%m.%d %H:%M:%S',
        filename=loging_path
    )


def check_preconditions(cfg):
    # check for report template exists
    if not os.path.exists(cfg.get('REPORT_TEMPLATE')):
        raise FileNotFoundError('Report template file not found at: {0}'.format(cfg.get('REPORT_TEMPLATE')))

    # create report dir if doesn't exist
    report_dir = cfg.get('REPORT_DIR')
    if not os.path.exists(report_dir):
        os.mkdir(report_dir)


def find_last_log(log_dir):
    if not os.path.isdir(log_dir):
        raise FileNotFoundError('Log directory not found')

    last_log_info = None
    r = re.compile(r'^nginx-access-ui\.log-(?P<date>\d{8})(\.gz)?$')
    for path in os.listdir(log_dir):
        m = r.match(path)
        if not m:
            continue

        date_str = m.groupdict()['date']
        try:
            parsed_date = datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            continue

        if not last_log_info or parsed_date > last_log_info.date:
            last_log_info = LogInfo(parsed_date, os.path.join(log_dir, path))

    if not last_log_info:
        raise FileNotFoundError('Log file not found')

    logging.info('Last log created at %s, path: %s' %
                 (last_log_info.date, last_log_info.path)
                 )
    return last_log_info


def make_report_path(cfg, last_log):
    report_path = os.path.join(cfg.get('REPORT_DIR'),
                               'report-{0}.html'.format(datetime.strftime(
                                   last_log.date, '%Y.%m.%d'))
                               )
    return report_path


def process_line(line, line_number):
    try:
        elems = line.split(' ')
        if not elems[7][0] == '/':
            raise ValueError
        url = elems[7]
        request_time = float(elems[-1])

        return {'url': url, 'request_time': request_time}
    except Exception:
        return False


def xreadlines(path, sucsessful_percent=None):
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

        if (sucsessful_percent) and (sucseccful < float(sucsessful_percent)):
            raise RuntimeError('Too many log parsing errors')


def collect_url_data(reader):
    Urls = namedtuple('Urls', ['urls', 'count'])
    Urls.urls = defaultdict(list)
    Urls.count = 0
    Urls.total_time = 0
    for url_data in reader:
        k, v = url_data['url'], url_data['request_time']
        Urls.urls[k].append(v)
        Urls.count += 1
        Urls.total_time += v

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

    return json.dumps(sorted_stat)


def write_report(cfg, path, stat):
    report_tmp_path = path + '.tmp'
    with open(cfg.get('REPORT_TEMPLATE'), encoding='utf-8') as rep_template:
        with open(report_tmp_path, mode='w', encoding='utf-8') as report:
            tmpl = string.Template(rep_template.read())
            logging.info('Writing temporary report at %s', report_tmp_path)
            report.write(tmpl.safe_substitute(table_json=stat))

    logging.info('Moving {0} to {1}'.format(report_tmp_path, path))
    shutil.move(report_tmp_path, path)


def main(config):
        check_preconditions(config)
        last_log = find_last_log(config.get('LOG_DIR'))
        report_path = make_report_path(config, last_log)
        if os.path.isfile(report_path):
            raise FileExistsError('Report at %s already exists' % report_path)

        reader = xreadlines(last_log.path, config.get('SUCSESSFUL_PERCENT'))
        urls = collect_url_data(reader)
        stat = calc_statistic(config, urls)
        write_report(config, report_path, stat)
        print('Log analyzing done!')


if __name__ == "__main__":
    try:
        ext_cfg_path = get_ext_config_path()
        config = init_config(ext_cfg_path)
        init_logging(config)
        main(config)

    except Exception:
        logging.exception('Exception')
