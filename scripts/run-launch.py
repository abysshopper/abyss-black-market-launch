#!/usr/bin/env python3
"""Run a reviewed Node/Python launch runner from its SDK/workspace directory.

Use a USER-OWNED TERMINAL, never an agent-controlled PTY, chat, CI, or a recorded
agent session. A terminal check cannot distinguish a user's PTY from an agent's.
The existing SDK runners need a signer even for unsigned planning, to derive the
creator; no mode flag means no signing, broadcast, or publication. Write modes
require the exact displayed authorization before any hidden secret prompt.
After protected secret input completes, the child inherits terminal input so its
fresh economic-review confirmation remains available.

Only this invocation's child environment receives the prompted secret. Nothing
is saved, supplied in arguments, or printed by this helper. The selected runner
is trusted code: it must respect the SDK's mode contract and redact its own
output/artifacts. Environment secrets remain accessible to the child and other
sufficiently privileged processes; Python cannot guarantee memory zeroization.
Python uses this interpreter (activate the SDK venv); Node uses `node` on PATH.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import getpass
import io
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import warnings

try:
    import resource
except ImportError:  # Core-dump limits are not exposed on every platform.
    resource = None


class LaunchError(Exception):
    """A deliberately public, secret-free refusal message."""

    def __init__(self, message, exit_code=2):
        super().__init__(message)
        self.exit_code = exit_code


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's usual message can echo a mistakenly supplied secret value.
        self.print_usage(sys.stderr)
        self.exit(2, "run-launch.py: invalid arguments; see --help. Never put secrets in arguments.\n")


def argument_parser():
    parser = SafeArgumentParser(
        description="Secure user-terminal adapter for reviewed SDK launch runners.",
        epilog=(
            "Run only in a USER-OWNED TERMINAL, never an agent-controlled PTY. "
            "Invoke from the target SDK/workspace cwd. Activate the Python SDK venv first. "
            "No mode flag is an unsigned dry-run; the SDK still needs a signer to derive "
            "the creator. Hidden input never falls back to echoing. The runner must "
            "honor these modes and redact its own logs/artifacts."
        ),
        allow_abbrev=False,
    )
    parser.add_argument("--sdk", choices=("node", "python"), required=True)
    parser.add_argument("--script", required=True, metavar="PATH", help="Reviewed SDK example or custom runner.")
    signer = parser.add_mutually_exclusive_group(required=True)
    signer.add_argument("--keystore", metavar="PATH", help="Preferred: owner-only, regular V3 keystore; password is prompted.")
    signer.add_argument("--private-key", action="store_true", help="Prompt for a raw hex32 key; never pass the key as an argument.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--broadcast", action="store_true", help="Authorize signing, transactions, and publication after confirmation.")
    mode.add_argument("--resume", metavar="DIR", help="Authorize continuation of the original recovery directory after confirmation.")
    return parser


def local_path(value, label):
    try:
        if not value or not value.strip() or any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError
        if len(value.encode("utf-8")) > 4096:
            raise ValueError
        return Path(value).expanduser().absolute()
    except (OSError, RuntimeError, ValueError, UnicodeError):
        raise LaunchError(f"{label} requires a valid local path without control characters.") from None


def validate_script(value, sdk):
    path = local_path(value, "Script")
    extensions = {".py"} if sdk == "python" else {".js", ".mjs", ".cjs", ".ts", ".mts", ".cts"}
    try:
        path = path.resolve(strict=True)
        metadata = path.stat()
        if path.suffix not in extensions:
            raise LaunchError("Script extension does not match the selected SDK.")
        if not stat.S_ISREG(metadata.st_mode) or not os.access(path, os.R_OK):
            raise LaunchError("Script must be a readable regular file.")
        return path
    except (OSError, RuntimeError, ValueError):
        raise LaunchError("Script must exist as a readable regular file.") from None


def validate_keystore(value):
    path = local_path(value, "Keystore")
    try:
        metadata = path.lstat()  # Metadata only: the SDK, not the helper, reads/decrypts it.
        if not stat.S_ISREG(metadata.st_mode):
            raise LaunchError("Keystore must be a regular file, not a symlink or device.")
        if not hasattr(os, "getuid") or metadata.st_uid != os.getuid():
            raise LaunchError("Keystore must be owned by the current user.")
        if metadata.st_mode & 0o077 or not metadata.st_mode & stat.S_IRUSR:
            raise LaunchError("Keystore must have owner-only, owner-readable permissions (for example 0600).")
        if not 1 <= metadata.st_size <= 64 * 1024 or not os.access(path, os.R_OK):
            raise LaunchError("Keystore must be readable and contain 1..65536 bytes.")
        return path  # Preserve the final component so the SDK's O_NOFOLLOW check still applies.
    except (OSError, RuntimeError, ValueError):
        raise LaunchError("Keystore metadata could not be validated safely.") from None


def validate_resume(value):
    path = local_path(value, "Recovery directory")
    try:
        path = path.resolve(strict=True)
        if not path.is_dir() or not os.access(path, os.R_OK | os.W_OK | os.X_OK):
            raise LaunchError("Recovery directory must be an existing readable, writable directory.")
        return path
    except (OSError, RuntimeError, ValueError):
        raise LaunchError("Recovery directory must exist and be accessible.") from None


def disable_core_dumps():
    if resource is not None and hasattr(resource, "RLIMIT_CORE"):
        try:
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        except (OSError, ValueError):
            raise LaunchError("Cannot disable core dumps; refusing to collect signer secrets.") from None


@contextmanager
def user_terminal():
    if not all(stream.isatty() for stream in (sys.stdin, sys.stdout, sys.stderr)):
        raise LaunchError("Refusing noninteractive or redirected input/output. Use a user-owned terminal, never an agent PTY.")
    if os.name != "posix":
        raise LaunchError("Protected input requires a POSIX controlling terminal; no echo fallback is allowed.")
    try:
        descriptor = os.open("/dev/tty", os.O_RDWR | getattr(os, "O_CLOEXEC", 0))
    except OSError:
        raise LaunchError("A user-owned controlling terminal is required; no secret will be read from stdin.") from None
    # Unbuffered FileIO avoids BufferedRandom's seek requirement on terminal devices.
    with os.fdopen(descriptor, "r+b", buffering=0) as raw:
        if not os.isatty(raw.fileno()) or os.tcgetpgrp(raw.fileno()) != os.getpgrp():
            raise LaunchError("Run in the foreground of a user-owned terminal; no secret will be read.")
        with io.TextIOWrapper(raw, encoding="utf-8", line_buffering=True, write_through=True) as terminal:
            yield terminal


def authorize(terminal, sdk, script, broadcast, resume):
    print("USER-OWNED TERMINAL ONLY: never enter secrets in an agent-controlled PTY or chat.", file=terminal, flush=True)
    print(f"SDK: {sdk}\nScript: {script}", file=terminal, flush=True)
    if not broadcast and resume is None:
        print("Mode: unsigned dry-run; no signing, transactions, or publication.", file=terminal, flush=True)
        return
    mode_arguments = ["--broadcast"] if broadcast else ["--resume", str(resume)]
    phrase = shlex.join(["AUTHORIZE", sdk, str(script), *mode_arguments])
    print("This mode can sign, submit transactions, and publish. Review the exact script and retained state first.", file=terminal)
    print(f"To continue, type exactly:\n{phrase}", file=terminal, flush=True)
    terminal.write("> ")
    terminal.flush()
    answer = terminal.readline(len(phrase) + 2)
    if answer.rstrip("\r\n") != phrase:
        raise LaunchError("Authorization refused; no signer secret was requested and no runner was started.")


def hidden_input(prompt, terminal):
    try:
        with warnings.catch_warnings():
            # getpass warns BEFORE its fallback reads/echoes: turn that into refusal.
            warnings.simplefilter("error", getpass.GetPassWarning)
            return getpass.getpass(prompt, stream=terminal)
    except (getpass.GetPassWarning, OSError, EOFError, UnicodeError):
        raise LaunchError("Protected terminal input is unavailable or cancelled; echo fallback is forbidden.") from None


def validate_password(secret):
    try:
        if not secret or "\0" in secret or len(secret.encode("utf-8")) > 4096:
            raise ValueError
        return secret  # Do not strip or normalize a password.
    except (ValueError, UnicodeError):
        raise LaunchError("A non-empty UTF-8 keystore password of at most 4096 bytes is required.") from None


def validate_private_key(secret):
    if re.fullmatch(r"(?:0[xX])?[0-9a-fA-F]{64}", secret) is None:
        raise LaunchError("Private key must be exactly 32 hex bytes, with an optional 0x prefix.")
    digits = secret[2:] if secret[:2].lower() == "0x" else secret
    # The SDKs reject zero/out-of-range scalars; reject them without diagnostic data.
    order = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    if not 0 < int(digits, 16) < order:
        raise LaunchError("Private key must be a valid nonzero secp256k1 scalar.")
    return "0x" + digits.lower()


def signer_environment(keystore, secret):
    environment = {
        key: value for key, value in os.environ.items()
        if key != "PRIVATE_KEY" and not key.startswith("EXAMPLE_KEYSTORE_")
    }
    # Existing SDK .env loaders preserve present values. Removal alone resurrects
    # stale signers from .env, so known inactive sources must explicitly stay empty.
    environment.update(PRIVATE_KEY="", EXAMPLE_KEYSTORE_PATH="", EXAMPLE_KEYSTORE_PASSWORD="")
    if keystore is not None:
        environment["EXAMPLE_KEYSTORE_PATH"] = str(keystore)
        environment["EXAMPLE_KEYSTORE_PASSWORD"] = secret
    else:
        environment["PRIVATE_KEY"] = secret
    return environment


def main(argv=None):
    args = argument_parser().parse_args(argv)
    secret = None
    environment = None
    try:
        # All local validation precedes authorization and hidden prompts.
        script = validate_script(args.script, args.sdk)
        keystore = validate_keystore(args.keystore) if args.keystore is not None else None
        resume = validate_resume(args.resume) if args.resume is not None else None
        command = ["node" if args.sdk == "node" else sys.executable, str(script)]
        if args.broadcast:
            command.append("--broadcast")
        elif resume is not None:
            command.extend(["--resume", str(resume)])
        with user_terminal() as terminal:
            disable_core_dumps()
            authorize(terminal, args.sdk, script, args.broadcast, resume)
            if keystore is not None:
                secret = validate_password(hidden_input("Keystore password (hidden): ", terminal))
            else:
                secret = validate_private_key(hidden_input("Private key (hidden): ", terminal))
            # Recheck local inputs after human interaction; never read their contents.
            validate_script(str(script), args.sdk)
            if keystore is not None:
                validate_keystore(str(keystore))
            if resume is not None:
                validate_resume(str(resume))
            environment = signer_environment(keystore, secret)
            try:
                result = subprocess.run(
                    # Keep validated terminal stdin for the runner's fresh economic review.
                    command, env=environment, stdin=None,
                    stdout=terminal, stderr=terminal, shell=False, check=False, close_fds=True,
                )
            except FileNotFoundError:
                raise LaunchError("SDK interpreter was not found; check the active venv or node on PATH.", exit_code=127) from None
            except OSError:
                raise LaunchError("SDK runner could not be started; check interpreter and local permissions.", exit_code=126) from None
            return result.returncode if result.returncode >= 0 else 128 - result.returncode
    except LaunchError as error:
        print(f"run-launch.py: {error}", file=sys.stderr)
        return error.exit_code
    except KeyboardInterrupt:
        print("run-launch.py: interrupted; no secret diagnostics are printed.", file=sys.stderr)
        return 130
    except Exception:
        # Unexpected exception text can contain environment values or prompt data.
        print("run-launch.py: helper failed; diagnostic details withheld to protect signer secrets.", file=sys.stderr)
        return 1
    finally:
        secret = None
        if environment is not None:
            environment.clear()


if __name__ == "__main__":
    raise SystemExit(main())
