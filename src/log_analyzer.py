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
    return max_date


def make_report_path(cfg, last_log):
    if not os.path.exists(cfg['REPORT_DIR']):
        os.makedirs(cfg['REPORT_DIR'])

    report_path = os.path.join(cfg['REPORT_DIR'],
        'report-%s.html' % (datetime.datetime.strftime(last_log['date'], '%Y.%m.%d'))
    )

    if not os.path.exists(report_path):
        logging.info('Opening report at %s', report_path)
        return report_path
    else:
        logging.info('Report at %s already exists', report_path)
        return None


def process_line(line):
    try:
        elems = line.split(' ')
        # logging.info(elems[7] + ' ' + elems[-1])
        if not elems[7][0] == '/':
            raise ValueError
        url = elems[7]
        f = float(elems[-1])

        logging.info('url=%s, time=%f' % (url, f))

        return True
    except Exception as e:
        logging.exception('line passing error')
        return False




def xreadlines(log_path):
    with gzip.open(log_path, 'rb') if log_path.endswith('.gz') else open(log_path) as log:

        total = processed = 0
        for line in log:
            parsed_line = process_line(line)
            total += 1
            if parsed_line:
                processed += 1
                yield parsed_line
                # return parsed_line
            # print("%s of %s lines processed" % (processed, total))

def main():
    last_log = find_last_log(config, '^nginx-access-ui\.log-([0-9]{8}|[0-9]{8}\.gz)$')
    report_path = make_report_path(config, last_log)

    if not report_path:
        logging.info('exit')
        sys.exit()

    reader = xreadlines(last_log['path'])
    #xreadlines(last_log['path'])
    # logging.info(reader)
    next(reader)
    next(reader)
    next(reader)
    next(reader)
    next(reader)



if __name__ == "__main__":
    main()
