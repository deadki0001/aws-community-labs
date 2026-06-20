"""Unit tests for input validation utilities."""
from app.validation import (validate_username, validate_email,
                             validate_password, validate_name, sanitise_cli_input)


def test_valid_username():
    ok, err = validate_username('validuser')
    assert ok is True and err is None

def test_username_too_short():
    ok, err = validate_username('ab')
    assert ok is False and 'least 4' in err

def test_username_invalid_chars():
    ok, err = validate_username('user name')
    assert ok is False

def test_valid_email():
    ok, err = validate_email('test@example.com')
    assert ok is True

def test_invalid_email():
    ok, err = validate_email('notanemail')
    assert ok is False

def test_valid_password():
    ok, err = validate_password('Secure@123')
    assert ok is True and err is None

def test_password_no_uppercase():
    ok, err = validate_password('secure@123')
    assert ok is False and 'uppercase' in err

def test_password_no_special():
    ok, err = validate_password('SecurePass1')
    assert ok is False and 'special' in err

def test_password_too_short():
    ok, err = validate_password('Ab@1')
    assert ok is False and '8' in err

def test_valid_name():
    ok, err = validate_name('John Smith')
    assert ok is True

def test_name_with_number():
    ok, err = validate_name('John2')
    assert ok is False and 'numbers' in err

def test_sanitise_removes_semicolon():
    result = sanitise_cli_input('aws s3 ls; rm -rf /')
    assert ';' not in result

def test_sanitise_removes_pipe():
    result = sanitise_cli_input('aws s3 ls | cat /etc/passwd')
    assert '|' not in result

def test_sanitise_removes_backtick():
    result = sanitise_cli_input('aws ec2 `whoami`')
    assert '`' not in result
