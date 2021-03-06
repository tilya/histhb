#!/usr/bin/env python3

import argparse
import logging
import sys
from collections import namedtuple
import csv
# from chardet.universaldetector import UniversalDetector
import re
from datetime import datetime

HistEntry = namedtuple('HistEntry', [
    'date',
    'paymode',
    'info',
    'payee',
    'memo',
    'amount',
    'category',
    'tags'
])

output_sequence = ['date', 'paymode', 'info', 'payee', 'memo', 'amount', 'category', 'tags']


def setup_logging(logger_name, log_level):
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    logformat = logging.Formatter('[%(asctime)s] - %(module)s::%(funcName)s - %(levelname)s: %(message)s')

    debugHandler = logging.StreamHandler(stream=sys.stderr)
    debugHandler.setFormatter(logformat)
    debugHandler.setLevel(log_level)

    logger.addHandler(debugHandler)
    logger.setLevel(log_level)


# def detect_encoding(file_handle):
#     detector = UniversalDetector()
#     detector.reset()
#
#     for line in file_handle:
#         detector.feed(line)
#         if detector.done:
#             break
#     detector.close()
#
#     return detector.result['encoding']


class History(object):
    input_file = None
    logger = None
    fields = {}
    entries = []
    source_enc = 'utf-8'
    fh_start_position = 0

    def __init__(self, input_file):
        self.input_file = input_file
        self.logger = logging.getLogger('debug_logger')

    def _read_input_file(self):
        with open(self.input_file, 'r') as fh:
            # self._detect_input_encoding(fh)
            self._prepare_input_file(fh)
            self._parse_input_file(fh)

    # def _detect_input_encoding(self, fh):
    #     # TODO: try encoding from configfile first
    #     self.source_enc = detect_encoding(fh)
    #     self.logger.debug("detected encoding: %s" % self.source_enc)
    #     fh.seek(0)

    def _skip_n_lines(self, fh, n):
        for _ in range(n):
            fh.readline()
        self.fh_start_position = fh.tell()

    def _prepare_input_file(self, fh):
        pass

    def _parse_input_file(self, fh):
        self.logger.debug("start_position: %s" % self.fh_start_position)
        next_line = next(fh)
        self.logger.debug(next_line)
        dialect = csv.Sniffer().sniff(next_line, delimiters=';')
        reader = csv.reader(fh, dialect)
        for row in reader:
            r = {key: row[value] for key, value in self.fields.items()}
            self.logger.debug(r)
            entry = HistEntry(**r)
            self.logger.debug(entry)
            self.entries.append(entry)

    def _format_entries(self):
        formatted_entries = []
        for entry in self.entries:
            formatted_entries.append(';'.join([getattr(entry, key) for key in output_sequence]))
        return formatted_entries


class CsasHistory(History):
    fields = {
        'date': 1,
        'paymode': -1,
        'info': 11,
        'payee': 3,
        'memo': 10,
        'amount': 2,
        'category': -1,
        'tags': -1
    }


class KbHistory(History):
    fields = {
        'date': 0,
        'paymode': -1,
        'info': 13,
        'payee': 2,
        'memo': 15,
        'amount': 4,
        'category': -1,
        'tags': -1
    }

    def _prepare_input_file(self, fh):
        self._skip_n_lines(fh, 17)


class EraHistory(History):
    fields = {
        'date': -1,
        'paymode': -1,
        'info': -1,
        'payee': -1,
        'memo': -1,
        'amount': -1,
        'category': -1,
        'tags': -1
    }

    def _prepare_input_file(self, fh):
        self._skip_n_lines(fh, 15)

    def _parse_input_file(self, fh):
        entry_end = re.compile(r'^-')

        pattern = ''.join([
            r'^\s*(?P<date>[0-9]{2}.[0-9]{2}.)\s+',
            r'(?P<info>[-.,\w\ ]+)\s+',
            r'(?P<reference>\d+)\s+',
            r'(?P<amount>[ +-]\d+,\d+)\s+',
            r'(?P<payee>\d+-\d+/\d+)?\s*',
            r'(?P<memo>.*)$',
        ])

        self.logger.debug(pattern)
        entry_pattern = re.compile(pattern, re.UNICODE)

        entry_line = ''
        for line in fh:
            stripped_line = line.strip(' \t\n\r')
            entry_end_match = re.match(entry_end, stripped_line)
            if entry_end_match:
                self.logger.debug('end of entry found')

                decoded_line = entry_line

                entry_match = re.match(entry_pattern, decoded_line)
                if entry_match:
                    self.logger.debug(entry_match.groups())
                    r = {}
                    for key in list(self.fields.keys()):
                        try:
                            value = entry_match.group(key)
                            if value is None:
                                r[key] = ''
                            else:
                                if key == 'date':
                                    value = "%s%s" % (value, datetime.now().year)
                                r[key] = value.replace(';', '')

                        except IndexError:
                            r[key] = ''

                    entry = HistEntry(**r)
                    self.logger.debug(entry)
                    self.entries.append(entry)
                else:
                    self.logger.info('entry does not match the pattern')

                entry_line = ''

            else:
                # add line to current entry
                entry_line = "%s %s" % (entry_line, stripped_line)
                self.logger.debug(entry_line)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bank', help='bank: csas, kb, era', action='store', dest='bank')
    parser.add_argument('--input', help='input file', action='store', dest='input_file')
    parser.add_argument('--output', help='output file', action='store', dest='output_file')
    parser.add_argument('--debug', help='output debugging info', action='store_true', dest='debug_enabled')
    args = parser.parse_args()

    if args.debug_enabled is True:
        setup_logging('debug_logger', logging.DEBUG)
    else:
        setup_logging('debug_logger', logging.INFO)

    logger = logging.getLogger('debug_logger')
    logger.debug(args)

    if args.bank == 'csas':
        history = CsasHistory(args.input_file)
    elif args.bank == 'kb':
        history = KbHistory(args.input_file)
    elif args.bank == 'era':
        history = EraHistory(args.input_file)

    history._read_input_file()

    with open(args.output_file, 'w+') as fh:
        for entry in history._format_entries():
            fh.write(entry)
            fh.write('\n')
