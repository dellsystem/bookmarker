numeral_map = [
    (1000, 'm'),
    (900, 'cm'),
    (500, 'd'),
    (400, 'cd'),
    (100, 'c'),
    (90, 'xc'),
    (50, 'l'),
    (40, 'xl'),
    (10, 'x'),
    (9, 'ix'),
    (5, 'v'),
    (4, 'iv'),
    (1, 'i')
]


def int_to_roman(i):
    result = []
    for integer, numeral in numeral_map:
        count = int(i / integer)
        result.append(numeral * count)
        i -= integer * count
    return ''.join(result)


def roman_to_int(n):
    n = str(n)

    i = 0
    result = 0
    for integer, numeral in numeral_map:
        while n[i:i + len(numeral)] == numeral:
            result += integer
            i += len(numeral)
    return result


def get_page_details(page):
    """Given a string representing a page number that may be in roman numeral
    form, return an integer and whether it's a roman numeral or not."""
    in_preface = False
    try:
        value = int(page)
    except ValueError:
        value = roman_to_int(page)
        in_preface = True

    if value > 0:
        return value, in_preface
    else:
        raise ValueError
