# Mapping dictionary for converting special characters and umlauts to their ASCII-equivalent.
# This is primarily used for converting non-ASCII characters to a compatible spelling for usernames.

MAPPING = {
    # German umlauts
    ord("Ä"): "Ae", ord("ä"): "ae",
    ord("Ö"): "Oe", ord("ö"): "oe",
    ord("Ü"): "Ue", ord("ü"): "ue",
    ord("ß"): "ss",
    
    # Scandinavian letters
    ord("Å"): "A", ord("å"): "a",
    ord("Ø"): "Oe", ord("ø"): "oe",
    ord("Æ"): "Ae", ord("æ"): "ae",

    # French accented letters
    ord("À"): "A", ord("à"): "a",
    ord("Á"): "A", ord("á"): "a",
    ord("Â"): "A", ord("â"): "a",
    ord("Ã"): "A", ord("ã"): "a",
    ord("Ç"): "C", ord("ç"): "c",
    ord("È"): "E", ord("è"): "e",
    ord("É"): "E", ord("é"): "e",
    ord("Ê"): "E", ord("ê"): "e",
    ord("Ë"): "E", ord("ë"): "e",
    ord("Ì"): "I", ord("ì"): "i",
    ord("Í"): "I", ord("í"): "i",
    ord("Î"): "I", ord("î"): "i",
    ord("Ï"): "I", ord("ï"): "i",
    ord("Ð"): "D", ord("ð"): "d",
    ord("Ñ"): "N", ord("ñ"): "n",
    ord("Ò"): "O", ord("ò"): "o",
    ord("Ó"): "O", ord("ó"): "o",
    ord("Ô"): "O", ord("ô"): "o",
    ord("Õ"): "O", ord("õ"): "o",
    ord("Œ"): "Oe", ord("œ"): "oe",
    ord("Ù"): "U", ord("ù"): "u",
    ord("Ú"): "U", ord("ú"): "u",
    ord("Û"): "U", ord("û"): "u",
    ord("Ý"): "Y", ord("ý"): "y",
    ord("Ÿ"): "Y", ord("ÿ"): "y",

    # Icelandic letters
    ord("Þ"): "Th", ord("þ"): "Th",

    # Czech/Slovak characters
    ord("Š"): "S", ord("š"): "s",
    ord("Č"): "C", ord("č"): "c",

    # Russian Cyrillic letters
    ord("А"): "A", ord("а"): "a",
    ord("Б"): "B", ord("б"): "b",
    ord("В"): "V", ord("в"): "v",
    ord("Г"): "G", ord("г"): "g",
    ord("Д"): "D", ord("д"): "d",
    ord("Е"): "E", ord("е"): "e",
    ord("Ё"): "E", ord("ё"): "e",
    ord("Ж"): "Zh", ord("ж"): "zh",
    ord("З"): "Z", ord("з"): "z",
    ord("И"): "I", ord("и"): "i",
    ord("Й"): "Y", ord("й"): "y",
    ord("К"): "K", ord("к"): "k",
    ord("Л"): "L", ord("л"): "l",
    ord("М"): "M", ord("м"): "m",
    ord("Н"): "N", ord("н"): "n",
    ord("О"): "O", ord("о"): "o",
    ord("П"): "P", ord("п"): "p",
    ord("Р"): "R", ord("р"): "r",
    ord("С"): "S", ord("с"): "s",
    ord("Т"): "T", ord("т"): "t",
    ord("У"): "U", ord("у"): "u",
    ord("Ф"): "F", ord("ф"): "f",
    ord("Х"): "Kh", ord("х"): "kh",
    ord("Ц"): "Ts", ord("ц"): "ts",
    ord("Ч"): "Ch", ord("ч"): "ch",
    ord("Ш"): "Sh", ord("ш"): "sh",
    ord("Щ"): "Shch", ord("щ"): "shch",
    ord("Ъ"): "", ord("ъ"): "",
    ord("Ы"): "Y", ord("ы"): "y",
    ord("Ь"): "", ord("ь"): "",
    ord("Э"): "E", ord("э"): "e",
    ord("Ю"): "Yu", ord("ю"): "yu",
    ord("Я"): "Ya", ord("я"): "ya",
}
