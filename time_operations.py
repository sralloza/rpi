from rpi.exceptions import InvalidLanguage


def secs_to_str(seconds, abbreviated=False, integer=None, language='en'):
    """Returns seconds extended as string."""

    alphabet = {
        'abbr': {
            'es': ['d', 'h', 'm', 's', ''],
            'en': ['d', 'h', 'm', 's', '']
        },
        'default': {
            'es': ['día', 'hora', 'minuto', 'segundo', 's'],
            'en': ['day', 'hour', 'minute', 'second', 's']
        }
    }

    if integer is True:
        seconds = int(seconds)

    try:
        if abbreviated is True:
            day, hour, minute, second, final_s = alphabet['abbr'][language]
        else:
            day, hour, minute, second, final_s = alphabet['default'][language]
    except KeyError:
        raise InvalidLanguage(f'{language!r} is not a valid language')

    before = ", "
    s_last = " y "
    has_before = [False, False, False, False]
    has_not_zero = [0, 0, 0, 0]

    h, m, s = dividir_segundos(seconds, entero=integer)
    d = int(h / 24)
    h = h % 24

    if s:
        last = 4
    elif m:
        last = 3
    elif h:
        last = 2
    elif d:
        last = 1
    else:
        last = 4

    if d:
        has_before[1] = True
        has_before[2] = True
        has_before[3] = True

        has_not_zero[0] = 1
    if h:
        has_before[2] = True
        has_before[3] = True

        has_not_zero[1] = 1
    if m:
        has_before[3] = True

        has_not_zero[2] = 1
    if s:
        has_not_zero[3] = 1

    only_one = sum(has_not_zero) == 1
    ret = ""

    if d:
        ret += "{} {}".format(d, day)
        if d - 1:
            ret += final_s
    if h:
        if last == 2 and not only_one:
            ret += s_last
        elif has_before[1]:
            ret += before
        ret += "{} {}".format(h, hour)
        if h - 1:
            ret += final_s
    if m:
        if last == 3 and not only_one:
            ret += s_last
        elif has_before[2]:
            ret += before
        ret += "{} {}".format(m, minute)
        if m - 1:
            ret += final_s
    if s:
        if last == 4 and not only_one:
            ret += s_last
        elif has_before[3]:
            ret += before
        ret += "{} {}".format(s, second)
        if s - 1:
            ret += final_s

    if s == m == h == d == 0:
        return '0 ' + second + final_s

    return ret


def dividir_segundos(totalsegundos, days=False, entero=None):
    """Transforma segundos en horas,minutos y segundos."""

    # totalsegundos = int(totalsegundos)

    totalminutos = totalsegundos // 60
    segundos = totalsegundos % 60
    horas = totalminutos // 60
    minutos = totalminutos % 60

    segundos = round(segundos, 2)

    if entero is not False:
        horas = int(horas)
        minutos = int(minutos)
        if not (horas == minutos == 0 and int(segundos) < 1 and entero is None):
            segundos = int(segundos)

    if not days:
        return horas, minutos, segundos
    else:
        dias = int(horas / 24)
        horas = horas % 24
        return dias, horas, minutos, segundos
