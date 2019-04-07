#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local]
#                     '"$request" $status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" '
#                     '"$http_X_REQUEST_ID" "$http_X_RB_USER" $request_time';

import os
import logging
import datetime
import re
import sys
import gzip
import collections
import statistics
import shutil
import fileinput

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
    max_date = {'date': datetime.datetime(1, 1, 1), 'path': '0'}
    for path, dirlist, filelist in os.walk(cfg["LOG_DIR"]):
        for name in filelist:
            logging.debug(name)
            if re.match(filepat, name):
                date_re = re.search('[0-9]{8}', name)
                date_str = name[date_re.start():date_re.end()]

                parsed_date = datetime.datetime.strptime(date_str, "%Y%m%d")

                if parsed_date > max_date['date']:
                    max_date['date'] = parsed_date
                    max_date['path'] = os.path.join(path, name)

    logging.info('Last log created at %s, path: %s' %
                 (max_date['date'], max_date['path'])
                 )
    # TODO: replace with namedtuple
    return max_date


def make_report_path(cfg, last_log):
    if not os.path.exists(cfg['REPORT_DIR']):
        os.makedirs(cfg['REPORT_DIR'])

    rep_template = os.path.join(cfg['REPORT_DIR'], 'report.html')

    if not os.path.exists(rep_template):
        raise FileNotFoundError('Report template file not found')

    report_path = os.path.join(cfg['REPORT_DIR'],
                               'report-%s.html' % (datetime.datetime.strftime(
                                   last_log['date'], '%Y.%m.%d'))
                               )

    if not os.path.exists(report_path):
        logging.info('Writing report at %s', report_path)
        return report_path
    else:
        logging.info('Report at %s already exists', report_path)
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
        logging.error('Log passing error at line: %d' % (line_number))
        return False


def xreadlines(log_path):
    with gzip.open(log_path, 'rb') if log_path.endswith('.gz') else open(log_path) as log:
        total = processed = 0
        for line in log:
            parsed_line = process_line(line, total)
            total += 1
            if parsed_line:
                processed += 1
                yield parsed_line
                # return parsed_line
        sucseccful = float(processed) / float(total)
        logging.info("%s of %s lines processed, sucseccful percent = %f" %
                     (processed, total, sucseccful)
                     )

        if (sucseccful < 0.7):
            raise ValueError('Too many parsing errors')


def collect_url_data(reader):
    Urls = collections.namedtuple('Urls', ['urls', 'count'])
    Urls.urls = collections.defaultdict(set)
    Urls.count = 0
    Urls.total_time = 0
    for url_data in reader:
        k, v = url_data['url'], url_data['request_time']
        Urls.urls[k].add(v)
        Urls.count += 1
        Urls.total_time += v

    # How can I do it with generator?
    return Urls


def calc_statistic(urls):
    stat_string = ""
    for url, reqtm in urls.urls.items():
        logging.debug(url + ' ' + str(reqtm))
        stat = {}
        stat["url"] = url
        stat["count"] = len(reqtm)
        stat["count_perc"] = 100.0 * (stat["count"] / urls.count)
        stat["time_sum"] = sum(reqtm)
        stat["time_perc"] = 100.0 * (stat["time_sum"] / urls.total_time)
        stat["time_avg"] = stat["time_sum"] / stat["count"]
        stat["time_max"] = max(reqtm)
        stat["time_med"] = statistics.median(reqtm)

        if(stat_string != ""):
            stat_string += ","
        stat_string += str(stat)

    # Не пойдет так. Нужно выбрать топчик
    # json!!!!
    return stat_string


def write_report(cfg, path, stat):
    rep_template = os.path.join(cfg['REPORT_DIR'], 'report.html')
    shutil.copyfile(rep_template, path)

    with fileinput.FileInput(path, inplace=True) as file:
        for line in file:
            print(line.replace('$table_json', stat), end='')

    logging.debug(stat)


def main():
    try:
        last_log = find_last_log(
            config, '^nginx-access-ui\.log-([0-9]{8}|[0-9]{8}\.gz)$')
        report_path = make_report_path(config, last_log)

        if not report_path:
            logging.info('exit')
            sys.exit()

        reader = xreadlines(last_log['path'])
        urls = collect_url_data(reader)
        logging.debug('urls size = %d, total_time = %f, type of urls.urls = %s' %
                      (urls.count, urls.total_time, str(type(urls.urls)))
                      )
        stat = calc_statistic(urls)
        write_report(config, report_path, stat)

        # loglines = [line for line in reader]
        # logging.info('type opof loglines is %s, len = %d, type of reader %s'
        #              % (type(loglines), len(loglines), type(reader))
        #              )

        '''while(next(reader)):
            pass
        next(reader)
        next(reader)
        next(reader)
        next(reader)'''
    except StopIteration as e:
        pass
    except ValueError as e:
        logging.exception('ValueError')
    except Exception:
        logging.exception('Global exception')


if __name__ == "__main__":
    main()
