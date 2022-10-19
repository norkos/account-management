import re
regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'


def check(email: str | None) -> bool:
    try:
        return re.fullmatch(regex, email)
    except:
        return False
