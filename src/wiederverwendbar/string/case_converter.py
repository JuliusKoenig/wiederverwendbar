import string


def split(s: str, word_chars: str) -> list[str]:
    word_split = []
    word = ""
    for c in s:
        if c not in word_chars:
            word_split.append(word)
            word = ""
            continue
        word += c
    if len(word) > 0:
        word_split.append(word)
    return word_split


def lowercase(s: str) -> str:
    """
    Convert string to lowercase.
    Example: "Te-st test" -> "te-st test"

    :param s: Input string
    :return: String in lowercase
    """

    return s.lower()


def uppercase(s: str) -> str:
    """
    Convert string to uppercase.
    Example: "Te-st test" -> "TE-ST TEST"

    :param s: Input string
    :return: String in uppercase
    """

    return s.upper()


def camelcase(s: str) -> str:
    """
    Convert string to camelcase.
    Example: "Te-st test" -> "TeStTest"

    :param s: Input string
    :return: String in camelcase
    """

    case = "".join([word.capitalize() for word in split(s=s, word_chars=string.ascii_letters + string.digits)])

    return case[0].lower() + case[1:]


def capitalcase(s: str) -> str:
    """
    Convert string to capitalcase.
    Example: "Te-st test" -> "Te St Test"

    :param s: Input string
    :return: String in capitalcase
    """

    return " ".join([word.capitalize() for word in split(s=s, word_chars=string.ascii_letters + string.digits)])


def constantcase(s: str) -> str:
    """
    Convert string to constantcase.
    Example: "Te-st test" -> "TE_ST_TEST"

    :param s: Input string
    :return: String in constantcase
    """

    return "_".join([word.upper() for word in split(s=s, word_chars=string.ascii_letters + string.digits)])


def dotcase(s: str) -> str:
    """
    Convert string to dotcase.
    Example: "Te-st test" -> "te.st.test"

    :param s: Input string
    :return: String in dotcase
    """

    return ".".join([word.lower() for word in split(s=s, word_chars=string.ascii_letters + string.digits)])


def headercase(s: str) -> str:
    """
    Convert string to headercase.
    Example: "Te-st test" -> "Te-St-Test"

    :param s: Input string
    :return: String in headercase
    """

    return "-".join([word.capitalize() for word in split(s=s, word_chars=string.ascii_letters + string.digits)])


def nocase(s: str) -> str:
    """
    Convert string to nocase.
    Example: "Te-st test" -> "te st test"

    :param s: Input string
    :return: String in nocase
    """

    return " ".join([word.lower() for word in split(s=s, word_chars=string.ascii_letters + string.digits)])


def paramcase(s: str) -> str:
    """
    Convert string to paramcase.
    Example: "Te-st test" -> "te-st-test"

    :param s: Input string
    :return: String in paramcase
    """

    return "-".join([word.lower() for word in split(s=s, word_chars=string.ascii_letters + string.digits)])


def pascalcase(s: str) -> str:
    """
    Convert string to pascalcase.
    Example: "Te-st test" -> "TeStTest"

    :param s: Input string
    :return: String in pascalcase
    """

    return "".join([word.capitalize() for word in split(s=s, word_chars=string.ascii_letters + string.digits)])


def pathcase(s: str) -> str:
    """
    Convert string to pathcase.
    Example: "Te-st test" -> "te/st/test"

    :param s: Input string
    :return: String in pathcase
    """

    return "/".join([word.lower() for word in split(s=s, word_chars=string.ascii_letters + string.digits)])


if __name__ == '__main__':
    c = pathcase("te-st test")
    print(c)
