"""
Server-side input validation utilities.
All functions return (is_valid: bool, error_message: str | None).
"""
import re


def validate_username(username):
    if not username or len(username.strip()) < 4:
        return False, "Username must be at least 4 characters long."
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username may only contain letters, numbers, and underscores."
    return True, None


def validate_email(email):
    if not email:
        return False, "Email address is required."
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Please enter a valid email address."
    return True, None


def validate_password(password):
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*()\-_=+\[\]{}|;:,.<>?/]', password):
        return False, "Password must contain at least one special character (e.g. ! @ # $)."
    return True, None


def validate_name(name):
    """Validates a display name — letters and spaces only, no numbers."""
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long."
    if re.search(r'\d', name):
        return False, "Name fields cannot contain numbers."
    if not re.match(r"^[a-zA-Z\s'\-]+$", name):
        return False, "Name may only contain letters, spaces, hyphens, and apostrophes."
    return True, None


def sanitise_cli_input(command):
    """Strip shell injection sequences from CLI terminal input."""
    command = re.sub(r'[;&`]', '', command)
    command = re.sub(r'\$\(.*?\)', '', command)
    command = re.sub(r'\|', '', command)
    return command.strip()
