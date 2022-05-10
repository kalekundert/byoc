#!/usr/bin/env python3

from byoc.errors import NoValueFound, Log

def test_no_value_found_formatting():
    log = Log()
    log += 'b'
    log += 'c'

    err = NoValueFound('a', log)

    assert str(err) == 'a\n• b\n• c'

def test_log():
    log = Log()
    log += 'a'
    log += lambda: 'b'
    log.info('c')
    log.info(lambda: 'd')

    assert log.message_strs == ['a', 'b', 'c', 'd']
    assert log.format() == str(log) == '• a\n• b\n• c\n• d'
