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

logging.basicConfig(
    format='[%(asctime)s] %(levelname).1s %(message)s',
    level=logging.INFO,
    datefmt='%Y.%m.%d %H:%M:%S'
)

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "../log"
}


def find_last_log(filepat, cfg=config):
    max_date = {'date': datetime.datetime(1, 1, 1), 'path': '0'}
    for path, dirlist, filelist in os.walk(cfg["LOG_DIR"]):
        for name in filelist:
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


def main():
    last_log = find_last_log('^nginx-access-ui\.log-([0-9]{8}|[0-9]{8}\.gz)$')


if __name__ == "__main__":
    main()
