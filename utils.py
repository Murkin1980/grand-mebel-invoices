def num2text(num):
    units = (
        '', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять'
    )
    units_f = (
        '', 'одна', 'две', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять'
    )
    teens = (
        'десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать',
        'пятнадцать', 'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать'
    )
    tens = (
        '', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 'шестьдесят',
        'семьдесят', 'восемьдесят', 'девяносто'
    )
    hundreds = (
        '', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот', 'шестьсот',
        'семьсот', 'восемьсот', 'девятьсот'
    )

    def _convert(n, f=False):
        if n == 0: return ''
        res = []
        if n >= 100:
            res.append(hundreds[n // 100])
            n %= 100
        if n >= 20:
            res.append(tens[n // 10])
            n %= 10
        if n >= 10:
            res.append(teens[n - 10])
            n = 0
        if n > 0:
            res.append(units_f[n] if f else units[n])
        return ' '.join([x for x in res if x])

    def _get_word(n, words):
        if 10 <= n % 100 <= 19: return words[2]
        if n % 10 == 1: return words[0]
        if 2 <= n % 10 <= 4: return words[1]
        return words[2]

    if num == 0:
        return 'ноль'

    num_groups = []
    while num > 0:
        num_groups.append(num % 1000)
        num //= 1000

    forms = [
        ('', '', ''), # 0: units
        ('тысяча', 'тысячи', 'тысяч'),
        ('миллион', 'миллиона', 'миллионов'),
        ('миллиард', 'миллиарда', 'миллиардов')
    ]

    res = []
    for i, n in enumerate(num_groups):
        if n == 0: continue
        group_text = _convert(n, f=(i == 1))
        if i > 0:
            group_text += ' ' + _get_word(n, forms[i])
        res.insert(0, group_text)

    return ' '.join([x for x in res if x]).strip()

def format_money(amount):
    rub = int(amount)
    kop = int(round((amount - rub) * 100))
    rub_text = num2text(rub).lower()
    return f"{rub_text} тенге {kop:02d} тиын".capitalize()
