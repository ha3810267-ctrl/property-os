import re


def validate_password(password):
    if not isinstance(password, str):
        return "Password must be a string"

    if len(password) < 12:
        return "Password must be at least 12 characters"

    if len(password) > 128:
        return "Password must be 128 characters or fewer"

    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return "Password must contain at least one number"

    return None