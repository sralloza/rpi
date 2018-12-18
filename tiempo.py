def segs_to_str(segundos, abreviado=False, entero=True):
    """Devuelve los segundos transformados en String."""

    if entero is True:
        segundos = int(segundos)

    if abreviado is False:
        dia = 'día'
        hora = 'hora'
        minuto = 'minuto'
        segundo = 'segundo'
        s_final = 's'
    else:
        dia = 'd'
        hora = 'h'
        minuto = 'm'
        segundo = 's'
        s_final = ''

    before = ", "
    s_last = " y "
    has_before = [False, False, False, False]
    has_not_zero = [0, 0, 0, 0]

    h, m, s = dividir_segundos(segundos, entero=entero)
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
        ret += "{} {}".format(d, dia)
        if d - 1:
            ret += s_final
    if h:
        if last == 2 and not only_one:
            ret += s_last
        elif has_before[1]:
            ret += before
        ret += "{} {}".format(h, hora)
        if h - 1:
            ret += s_final
    if m:
        if last == 3 and not only_one:
            ret += s_last
        elif has_before[2]:
            ret += before
        ret += "{} {}".format(m, minuto)
        if m - 1:
            ret += s_final
    if s:
        if last == 4 and not only_one:
            ret += s_last
        elif has_before[3]:
            ret += before
        ret += "{} {}".format(s, segundo)
        if s - 1:
            ret += s_final

    if s == m == h == d == 0:
        if abreviado is True:
            return '0 s'
        return '0 segundos'

    return ret


def dividir_segundos(totalsegundos, days=False, entero=False):
    """Transforma segundos en horas,minutos y segundos."""

    # totalsegundos = int(totalsegundos)

    totalminutos = totalsegundos // 60
    segundos = totalsegundos % 60
    horas = totalminutos // 60
    minutos = totalminutos % 60

    segundos = round(segundos, 2)

    if entero is True:
        horas = int(horas)
        minutos = int(minutos)
        segundos = int(segundos)

    if not days:
        return horas, minutos, segundos
    else:
        dias = int(horas / 24)
        horas = horas % 24
        return dias, horas, minutos, segundos
