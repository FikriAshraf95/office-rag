"""Password hashes for `LOGIN_USERS` (SPEC-11 §5.2): stdlib scrypt, no extra dependency.

Format `scrypt:<n>:<r>:<p>:<salt>:<hash>` (base64url). No `$`, so Docker Compose never interpolates it in
`.env`. Make one with `python -m app.security.passwords` (asks for the password), and a session secret
with `python -m app.security.passwords --secret`.
"""

import base64
import getpass
import hashlib
import hmac
import secrets
import sys

N, R, P = 2**14, 8, 1
SALT_BYTES = 16
KEY_BYTES = 32
MIN_PASSWORD = 8


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(
        password.encode(), salt=salt, n=n, r=r, p=p, dklen=KEY_BYTES, maxmem=64 * 1024 * 1024
    )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    return f"scrypt:{N}:{R}:{P}:{_b64(salt)}:{_b64(_scrypt(password, salt, N, R, P))}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time check; a malformed hash is a mismatch, never an error."""
    try:
        scheme, n, r, p, salt, expected = stored.split(":")
        if scheme != "scrypt":
            return False
        actual = _scrypt(password, _unb64(salt), int(n), int(r), int(p))
        return hmac.compare_digest(actual, _unb64(expected))
    except ValueError:
        return False


# Checked for an unknown username too, so a wrong name takes as long as a wrong password.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def main(argv: list[str]) -> int:
    if "--secret" in argv:
        print(secrets.token_urlsafe(48))
        return 0
    if sys.stdin.isatty():
        password = getpass.getpass("Password: ")
        if getpass.getpass("Again: ") != password:
            print("The passwords don't match.", file=sys.stderr)
            return 1
    else:
        password = sys.stdin.readline().rstrip("\r\n")
    if len(password) < MIN_PASSWORD:
        print(f"Use at least {MIN_PASSWORD} characters.", file=sys.stderr)
        return 1
    print(hash_password(password))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
