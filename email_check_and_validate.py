from typing import Tuple, Optional, Dict
import dns.resolver
import smtplib
import socket
import re

# Non-exhaustive regex patterns and checks for email validation
# Catches most common errors, especially with invalid characters and dot placement
# Check responsiveness of mail server via SMTP if MX records exist

LOCAL_ATOM_RE = re.compile(r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]")

def _error_dict(code: str, message: str, pos: int = 0) -> Dict:
    return {"code": code, "message": message, "position": pos}

def _find_invalid_local_char(local: str) -> Optional[int]:
    """Return index of first invalid character in unquoted local part, or None."""
    for i, ch in enumerate(local):
        if ch == '.':
            continue
        if not LOCAL_ATOM_RE.match(ch):
            return i
    return None

def _validate_unquoted_local(local: str, offset: int = 0):
    if local.startswith('.'):
        return _error_dict("local_starts_with_dot", "Local-part starts with a dot", offset)
    if local.endswith('.'):
        return _error_dict("local_ends_with_dot", "Local-part ends with a dot", offset + len(local) - 1)
    if '..' in local:
        idx = local.find('..')
        return _error_dict("local_consecutive_dots", "Local-part has consecutive dots", offset + idx)

    invalid_idx = _find_invalid_local_char(local)
    if invalid_idx is not None:
        return _error_dict("local_invalid_character", f"Invalid character '{local[invalid_idx]}' in local-part", offset + invalid_idx)

    return None

def validate_email_syntax(email: str) -> Tuple[bool, Optional[Dict]]:
    """
    Validate an email address and return (is_valid, error_dict).

    error_dict fields: code, message, position

    Error codes:
    - not_string, empty
    - email_too_long, domain_too_long
    - local_empty, domain_empty
    - missing_at, multiple_at
    - local_too_long, local_invalid_character, local_consecutive_dots
    - local_starts_with_dot, local_ends_with_dot
    """
    if not isinstance(email, str):
        return False, _error_dict("not_string", "Email must be a string")

    if email == "":
        return False, _error_dict("empty", "Email is empty")

    # Overall length
    if len(email) > 254:
        return False, _error_dict("email_too_long", "Email exceeds 254 characters")

    # '@' checks
    at_count = email.count('@')
    if at_count == 0:
        return False, _error_dict("missing_at", "Missing '@' symbol")
    if at_count > 1:
        # identify position of second '@'
        first = email.find('@')
        second = email.find('@', first + 1)
        return False, _error_dict("multiple_at", "Multiple '@' symbols in address", second)

    at_pos = email.find('@')
    local = email[:at_pos]
    domain_email = email[at_pos + 1:]

    # Local-part length
    if len(local) == 0:
        return False, _error_dict("local_empty", "Local-part is empty", 0)
    if len(local) > 64:
        return False, _error_dict("local_too_long", "Local-part exceeds 64 characters")

    # Domain length
    if len(domain_email) == 0:
        return False, _error_dict("domain_empty", "Domain part is empty", at_pos + 1)
    if len(domain_email) > 255:
        return False, _error_dict("domain_too_long", "Domain exceeds 255 characters")


    err = _validate_unquoted_local(local, offset=0)
    if err:
        return False, err

    # Passed all checks
    return True, None

def check_mx_records(domain_var: str):
    try:
        answers = dns.resolver.resolve(domain_var, 'MX')
        mx_records = sorted([(r.preference, r.exchange.to_text()) for r in answers])
        return True, mx_records
    except dns.resolver.NoAnswer:
        return False, "No MX record found"
    except dns.resolver.NXDOMAIN:
        return False, "Domain does not exist"
    except Exception as e:
        return False, str(e)


def check_smtp_recipient(email: str, from_email="verify@example.com", from_domain="example.com") -> Tuple[bool, str]:
    domain_email = email.split('@')[-1]

    ok_code_mx, mx_or_error = check_mx_records(domain_email)
    if not ok_code_mx:
        return False, f"DNS error: {mx_or_error}"

    mx_records = mx_or_error
    for _, mx_host in mx_records:
        if len(mx_host) < 2:
            continue  # Skip invalid MX hostnames
        try:
            server = smtplib.SMTP(mx_host, 25, timeout=10)
            server.helo(from_domain)
            server.mail(from_email)
            code, msg = server.rcpt(email)
            server.quit()

            if code == 250:
                return True, "Address accepted by SMTP"
            elif code == 550:
                return False, f"Address rejected: {msg.decode()}"
            else:
                return False, f"Unexpected SMTP code {code}: {msg.decode()}"
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, socket.error) as e:
            continue
    return False, "No responsive mail servers found"


if __name__ == "__main__":
    # Example Usage
    # Outlook emails usually cannot be verified via SMTP, but it returns MX records
    # Gmail emails can be verified via SMTP
    # Other domains may vary, but often if MX records exist, the E-mail can be valid even with "SMTP check: No responsive mail servers found"
    email_input = "support-in@google.com, simple@example.com, user@outlook.com, john.doe@gmail.com, user@unknown-xxx.com, invalid..email@example.com, ., "
    emails = [e.strip() for e in email_input.split(',')]
    result =  {email: validate_email_syntax(email) for email in emails if email}
    print(result)

    for email, (is_valid, error) in result.items():
        if is_valid:
            print(f"{email} passed syntax check.")
            domain_to_check = email.split('@')[-1]
            ok_message, mx_message = check_mx_records(domain_to_check)
            print("MX records:", mx_message if ok_message else "Error:", mx_message)

            if ok_message:
                ok_message, smtp_message = check_smtp_recipient(email)
                print("SMTP check:", smtp_message)
        else:
            print(f"{email} failed syntax check: {error}")

        print("---")