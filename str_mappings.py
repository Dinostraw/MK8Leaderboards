# Dictionary mapping Hiragana characters to Katakana
hira2kata_mapping = {x: x + 0x60 for x in range(ord('ぁ'), ord('ゖ') + 1)}
hira2kata_mapping[ord('ゝ')] = ord('ヽ')
hira2kata_mapping[ord('ゞ')] = ord('ヾ')

# Dictionary mapping Katakana characters to Hiragana
kata2hira_mapping = {kata: hira for hira, kata in hira2kata_mapping.items()}

# Dictionary mapping ASCII characters to Fullwidth ASCII
ascii2fullwidth_mapping = {x: x + 0xFEE0 for x in range(ord('!'), ord('~'))}
ascii2fullwidth_mapping[ord(' ')] = ord('　')

# Dictionary mapping Fullwidth ASCII characters to regular ASCII
fullwidth2ascii_mapping = {full: ascii_ for ascii_, full in ascii2fullwidth_mapping.items()}


def hira2kata(phrase: str) -> str:
    return phrase.translate(hira2kata_mapping)


def kata2hira(phrase: str) -> str:
    return phrase.translate(kata2hira_mapping)


def ascii2fullwidth(phrase: str) -> str:
    return phrase.translate(ascii2fullwidth_mapping)


def fullwidth2ascii(phrase: str) -> str:
    return phrase.translate(fullwidth2ascii_mapping)


def standardize_abbr(abbr: str) -> str:
    return hira2kata(fullwidth2ascii(abbr)).lower()
