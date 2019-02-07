# -*- coding: utf-8 -*-

"""Defines time operations."""

from rpi.exceptions import InvalidLanguage

ALPHABET = {
    'abbr': {
        'es': ['d', 'h', 'm', 's', '', 'y'],
        'en': ['d', 'h', 'm', 's', '', 'and']
    },
    'default': {
        'es': ['día', 'hora', 'minuto', 'segundo', 's', 'y'],
        'en': ['day', 'hour', 'minute', 'second', 's', 'and']
    }
}


def secs_to_str(seconds, abbreviated=False, integer=None, language='en'):
    """Returns seconds extended as string."""

    if integer is True:
        seconds = int(seconds)

    try:
        if abbreviated is True:
            day_str, hour_str, minute_str, second_str, final_s, s_last = ALPHABET['abbr'][language]
        else:
            day_str, hour_str, minute_str, second_str, final_s, s_last = ALPHABET['default'][
                language]
    except KeyError:
        raise InvalidLanguage(f'{language!r} is not a valid language')

    before = ", "
    s_last = ' ' + s_last + ' '
    has_before = [False, False, False, False]
    has_not_zero = [0, 0, 0, 0]

    day, hour, minute, second = split_seconds(seconds, integer=integer, days=True)

    if second:
        last = 4
    elif minute:
        last = 3
    elif hour:
        last = 2
    elif day:
        last = 1
    else:
        last = 4

    if day:
        has_before[1] = True
        has_before[2] = True
        has_before[3] = True

        has_not_zero[0] = 1
    if hour:
        has_before[2] = True
        has_before[3] = True

        has_not_zero[1] = 1
    if minute:
        has_before[3] = True

        has_not_zero[2] = 1
    if second:
        has_not_zero[3] = 1

    only_one = sum(has_not_zero) == 1
    ret = ""

    if day:
        ret += "{} {}".format(day, day_str)
        if day - 1:
            ret += final_s
    if hour:
        if last == 2 and not only_one:
            ret += s_last
        elif has_before[1]:
            ret += before
        ret += "{} {}".format(hour, hour_str)
        if hour - 1:
            ret += final_s
    if minute:
        if last == 3 and not only_one:
            ret += s_last
        elif has_before[2]:
            ret += before
        ret += "{} {}".format(minute, minute_str)
        if minute - 1:
            ret += final_s
    if second:
        if last == 4 and not only_one:
            ret += s_last
        elif has_before[3]:
            ret += before
        ret += "{} {}".format(second, second_str)
        if second - 1:
            ret += final_s

    if second == minute == hour == day == 0:
        return '0 ' + second + final_s

    return ret


def split_seconds(total_seconds, days=False, integer=None):
    """Transforma segundos en horas,minutos y segundos."""

    # total_seconds = int(total_seconds)

    total_minutes = total_seconds // 60
    seconds = total_seconds % 60
    hours = total_minutes // 60
    minutes = total_minutes % 60

    seconds = round(seconds, 2)

    if integer is not False:
        hours = int(hours)
        minutes = int(minutes)
        if not (hours == minutes == 0 and int(seconds) < 1 and integer is None):
            seconds = int(seconds)

    if not days:
        return hours, minutes, seconds
    else:
        days = hours // 24
        hours = hours % 24
        return days, hours, minutes, seconds
