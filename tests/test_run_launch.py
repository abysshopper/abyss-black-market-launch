"""Focused helper tests; signer values are synthetic and no SDK writes execute."""

from contextlib import nullcontext, redirect_stderr, redirect_stdout
import importlib.util
import io
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import warnings


HELPER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run-launch.py"
SPEC = importlib.util.spec_from_file_location("secure_launch_terminal", HELPER_PATH)
launch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launch)
ORIGINAL_TERMINAL = launch.user_terminal
ORIGINAL_CORE_LIMIT = launch.disable_core_dumps
ORIGINAL_RUN = subprocess.run
KEY = "0x" + "11" * 32
PASSWORD = "transient-unit-test-password"


class MemoryTerminal(io.StringIO):
    def __init__(self):
        super().__init__()
        self.answers = []

    def readline(self, size=-1):
        answer = self.answers.pop(0) if self.answers else ""
        return answer if size < 0 else answer[:size]


class LaunchHelperTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name) / "workspace with spaces"
        self.workspace.mkdir()
        self.python_script = self.workspace / "launch.py"
        self.python_script.write_text("pass\n", encoding="utf-8")
        self.node_script = self.workspace / "launch.ts"
        self.node_script.write_text("export {};\n", encoding="utf-8")
        self.keystore = self.workspace / "keystore.json"
        # Metadata fixture only; helper must never read/decrypt this content.
        self.keystore.write_bytes(b"encrypted-keystore-metadata-fixture")
        self.keystore.chmod(0o600)
        self.recovery = self.workspace / "retained recovery"
        self.recovery.mkdir(mode=0o700)
        self.terminal = MemoryTerminal()
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self.runs = []
        self.returncode = 0
        self.start_patch(patch.dict(os.environ, {"PATH": "/test/path", "LAUNCH_API_URL": "https://api.example.test"}, clear=True))
        self.terminal_mock = self.start_patch(patch.object(launch, "user_terminal", return_value=nullcontext(self.terminal)))
        self.core_mock = self.start_patch(patch.object(launch, "disable_core_dumps"))
        self.prompt = self.start_patch(patch.object(launch.getpass, "getpass", return_value=KEY))
        self.runner = self.start_patch(patch.object(launch.subprocess, "run", side_effect=self.record_run))
        stdout_context = redirect_stdout(self.stdout)
        stdout_context.__enter__()
        self.addCleanup(stdout_context.__exit__, None, None, None)
        stderr_context = redirect_stderr(self.stderr)
        stderr_context.__enter__()
        self.addCleanup(stderr_context.__exit__, None, None, None)

    def start_patch(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def record_run(self, command, **kwargs):
        self.runs.append((list(command), dict(kwargs["env"]), kwargs))
        return SimpleNamespace(returncode=self.returncode)

    def invoke(self, sdk="python", script=None, signer=None, mode=()):
        script = script if script is not None else (self.python_script if sdk == "python" else self.node_script)
        signer = signer if signer is not None else ["--private-key"]
        return launch.main(["--sdk", sdk, "--script", str(script), *signer, *mode])

    def all_output(self):
        return self.stdout.getvalue() + self.stderr.getvalue() + self.terminal.getvalue()

    def confirmation(self, sdk="python", mode="--broadcast"):
        script = self.python_script if sdk == "python" else self.node_script
        arguments = ["AUTHORIZE", sdk, str(script), mode]
        if mode == "--resume":
            arguments.append(str(self.recovery))
        return shlex.join(arguments)

    def test_nonterminal_refusal_precedes_secret_or_child(self):
        self.terminal_mock.side_effect = ORIGINAL_TERMINAL
        with patch.object(sys, "stdin", io.StringIO()):
            self.assertEqual(self.invoke(), 2)
        self.prompt.assert_not_called()
        self.runner.assert_not_called()

    def test_each_redirected_standard_stream_is_refused(self):
        for redirected in ("stdin", "stdout", "stderr"):
            streams = {name: Mock(isatty=Mock(return_value=name != redirected)) for name in ("stdin", "stdout", "stderr")}
            with self.subTest(stream=redirected), patch.multiple(sys, **streams), patch.object(os, "open") as opener:
                with self.assertRaises(launch.LaunchError):
                    with ORIGINAL_TERMINAL():
                        self.fail("redirected terminal accepted")
                opener.assert_not_called()

    def test_missing_controlling_terminal_does_not_fall_back(self):
        streams = {name: Mock(isatty=Mock(return_value=True)) for name in ("stdin", "stdout", "stderr")}
        with patch.multiple(sys, **streams), patch.object(os, "open", side_effect=OSError(PASSWORD)):
            with self.assertRaises(launch.LaunchError) as caught:
                with ORIGINAL_TERMINAL():
                    self.fail("missing controlling terminal accepted")
        self.assertNotIn(PASSWORD, str(caught.exception))
        self.prompt.assert_not_called()

    def test_background_terminal_group_is_refused(self):
        streams = {name: Mock(isatty=Mock(return_value=True)) for name in ("stdin", "stdout", "stderr")}
        raw = Mock()
        raw.fileno.return_value = 123
        with patch.multiple(sys, **streams), patch.object(os, "open", return_value=123), \
                patch.object(os, "fdopen", return_value=nullcontext(raw)), patch.object(os, "isatty", return_value=True), \
                patch.object(os, "tcgetpgrp", return_value=10), patch.object(os, "getpgrp", return_value=11):
            with self.assertRaises(launch.LaunchError):
                with ORIGINAL_TERMINAL():
                    self.fail("background process accepted")
        self.prompt.assert_not_called()

    def test_flag_exclusion_and_invalid_arguments_never_echo_values(self):
        base = ["--sdk", "python", "--script", str(self.python_script)]
        cases = [
            base,
            base + ["--private-key", "--keystore", str(self.keystore)],
            base + ["--private-key", "--broadcast", "--resume", str(self.recovery)],
            base + ["--private-key", KEY],
            base + ["--private-key", "--b"],
            ["--sdk", PASSWORD, "--script", str(self.python_script), "--private-key"],
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments), self.assertRaises(SystemExit) as caught:
                launch.main(arguments)
            self.assertEqual(caught.exception.code, 2)
        self.prompt.assert_not_called()
        self.runner.assert_not_called()
        self.assertNotIn(KEY, self.all_output())
        self.assertNotIn(PASSWORD, self.all_output())

    def test_script_and_recovery_validation_precedes_all_prompts(self):
        directory = self.workspace / "directory.py"
        directory.mkdir()
        cases = [
            {"script": self.workspace / "missing.py"},
            {"script": self.node_script},
            {"sdk": "node", "script": self.python_script},
            {"script": directory},
            {"script": "unsafe\nscript.py"},
            {"mode": ["--resume", str(self.workspace / "missing-recovery")]},
            {"mode": ["--resume", str(self.python_script)]},
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                self.assertEqual(self.invoke(**arguments), 2)
        self.terminal_mock.assert_not_called()
        self.prompt.assert_not_called()
        self.runner.assert_not_called()

    def test_unreadable_script_is_refused_before_terminal(self):
        with patch.object(os, "access", return_value=False):
            self.assertEqual(self.invoke(), 2)
        self.terminal_mock.assert_not_called()
        self.prompt.assert_not_called()

    def test_keystore_rejects_symlinks_and_unsafe_metadata(self):
        linked = self.workspace / "linked-keystore.json"
        linked.symlink_to(self.keystore)
        empty = self.workspace / "empty.json"
        empty.touch(mode=0o600)
        oversized = self.workspace / "oversized.json"
        oversized.write_bytes(b"x" * (64 * 1024 + 1))
        oversized.chmod(0o600)
        unsafe = self.workspace / "shared.json"
        unsafe.write_bytes(b"fixture")
        unsafe.chmod(0o644)
        unreadable = self.workspace / "unreadable.json"
        unreadable.write_bytes(b"fixture")
        unreadable.chmod(0o200)
        for path in (linked, empty, oversized, unsafe, unreadable, self.recovery, self.workspace / "missing.json"):
            with self.subTest(path=path):
                self.assertEqual(self.invoke(signer=["--keystore", str(path)]), 2)
        self.terminal_mock.assert_not_called()
        self.prompt.assert_not_called()
        self.runner.assert_not_called()

    def test_keystore_owner_must_match_user(self):
        with patch.object(os, "getuid", return_value=self.keystore.stat().st_uid + 1):
            self.assertEqual(self.invoke(signer=["--keystore", str(self.keystore)]), 2)
        self.prompt.assert_not_called()
        self.runner.assert_not_called()

    def test_dry_run_has_no_write_flag_and_uses_current_python(self):
        self.assertEqual(self.invoke(), 0)
        command, environment, kwargs = self.runs[-1]
        self.assertEqual(command, [sys.executable, str(self.python_script)])
        self.assertEqual(environment["PRIVATE_KEY"], KEY)
        self.assertEqual(environment["EXAMPLE_KEYSTORE_PATH"], "")
        self.assertEqual(environment["EXAMPLE_KEYSTORE_PASSWORD"], "")
        self.assertIsNone(kwargs["stdin"])
        self.assertIs(kwargs["stdout"], self.terminal)
        self.assertIs(kwargs["stderr"], self.terminal)
        self.assertFalse(kwargs["shell"])
        self.assertFalse(kwargs["check"])
        self.assertTrue(kwargs["close_fds"])
        self.assertNotIn("cwd", kwargs)
        self.assertEqual(kwargs["env"], {})  # Transient environment cleared after child exit.

    def test_node_accepts_actual_runner_extensions_and_node_binary(self):
        for extension in (".ts", ".mts", ".cts", ".js", ".mjs", ".cjs"):
            script = self.workspace / ("runner" + extension)
            script.write_text("// reviewed fixture\n", encoding="utf-8")
            with self.subTest(extension=extension):
                self.assertEqual(self.invoke(sdk="node", script=script), 0)
                self.assertEqual(self.runs[-1][0], ["node", str(script)])

    def test_broadcast_refuses_without_exact_script_mode_authorization(self):
        self.terminal.answers = ["yes\n"]
        self.assertEqual(self.invoke(mode=["--broadcast"]), 2)
        self.assertIn(self.confirmation(), self.terminal.getvalue())
        self.prompt.assert_not_called()
        self.runner.assert_not_called()

    def test_resume_refuses_wrong_script_directory_or_extra_whitespace(self):
        for answer in ("yes", self.confirmation(mode="--resume") + " ", self.confirmation()):
            self.terminal.answers = [answer + "\n"]
            with self.subTest(answer=answer):
                self.assertEqual(self.invoke(mode=["--resume", str(self.recovery)]), 2)
        self.prompt.assert_not_called()
        self.runner.assert_not_called()
        self.assertIn(self.confirmation(mode="--resume"), self.terminal.getvalue())

    def test_broadcast_flag_only_after_literal_confirmation_before_secret(self):
        phrase = self.confirmation()
        self.terminal.answers = [phrase + "\n"]

        def prompt_after_confirmation(prompt, stream):
            self.assertIn(phrase, stream.getvalue())
            self.assertEqual(stream.answers, [])
            self.runner.assert_not_called()
            return KEY

        self.prompt.side_effect = prompt_after_confirmation
        self.assertEqual(self.invoke(mode=["--broadcast"]), 0)
        self.assertEqual(self.runs[-1][0], [sys.executable, str(self.python_script), "--broadcast"])
        self.assertNotIn(KEY, self.all_output())

    def test_resume_forwards_exact_original_directory_not_broadcast(self):
        self.terminal.answers = [self.confirmation(sdk="node", mode="--resume") + "\n"]
        self.assertEqual(self.invoke(sdk="node", mode=["--resume", str(self.recovery)]), 0)
        self.assertEqual(self.runs[-1][0], ["node", str(self.node_script), "--resume", str(self.recovery)])

    def test_selected_keystore_scrubs_all_inherited_signer_values(self):
        ambient = {"PRIVATE_KEY": "stale-key", "EXAMPLE_KEYSTORE_PATH": "stale-path",
                   "EXAMPLE_KEYSTORE_PASSWORD": "stale-password", "EXAMPLE_KEYSTORE_UNUSED": "stale-extra"}
        self.prompt.return_value = PASSWORD
        with patch.dict(os.environ, ambient):
            self.assertEqual(self.invoke(signer=["--keystore", str(self.keystore)]), 0)
            self.assertEqual(os.environ["PRIVATE_KEY"], ambient["PRIVATE_KEY"])
        command, environment, kwargs = self.runs[-1]
        self.assertEqual(environment["PRIVATE_KEY"], "")
        self.assertEqual(environment["EXAMPLE_KEYSTORE_PATH"], str(self.keystore))
        self.assertEqual(environment["EXAMPLE_KEYSTORE_PASSWORD"], PASSWORD)
        self.assertNotIn("EXAMPLE_KEYSTORE_UNUSED", environment)
        self.assertEqual(environment["LAUNCH_API_URL"], "https://api.example.test")
        self.assertNotIn(PASSWORD, repr(command))
        self.assertNotIn(PASSWORD, self.all_output())
        self.assertEqual(kwargs["env"], {})

    def test_selected_raw_key_explicitly_blanks_inactive_dotenv_sources(self):
        with patch.dict(os.environ, {"PRIVATE_KEY": "stale-key", "EXAMPLE_KEYSTORE_PATH": "stale-path",
                                     "EXAMPLE_KEYSTORE_PASSWORD": "stale-password", "EXAMPLE_KEYSTORE_UNUSED": "extra"}):
            self.assertEqual(self.invoke(), 0)
        environment = self.runs[-1][1]
        self.assertEqual(environment["PRIVATE_KEY"], KEY)
        self.assertEqual(environment["EXAMPLE_KEYSTORE_PATH"], "")
        self.assertEqual(environment["EXAMPLE_KEYSTORE_PASSWORD"], "")
        self.assertNotIn("EXAMPLE_KEYSTORE_UNUSED", environment)

    def test_getpass_warning_refuses_before_any_echo_fallback(self):
        reached_fallback = []

        def unsafe_getpass(prompt, stream):
            warnings.warn(PASSWORD, launch.getpass.GetPassWarning)
            reached_fallback.append(True)
            return KEY

        self.prompt.side_effect = unsafe_getpass
        self.assertEqual(self.invoke(), 2)
        self.assertEqual(reached_fallback, [])
        self.runner.assert_not_called()
        self.assertNotIn(PASSWORD, self.all_output())

    def test_password_requires_nonempty_utf8_without_nul_and_preserves_spacing(self):
        for secret in ("", "nul\0password", "x" * 4097, "invalid-\ud800"):
            self.prompt.return_value = secret
            with self.subTest(kind=repr(secret[:12])):
                self.assertEqual(self.invoke(signer=["--keystore", str(self.keystore)]), 2)
        self.runner.assert_not_called()
        self.prompt.return_value = "  " + PASSWORD + "  "
        self.assertEqual(self.invoke(signer=["--keystore", str(self.keystore)]), 0)
        self.assertEqual(self.runs[-1][1]["EXAMPLE_KEYSTORE_PASSWORD"], self.prompt.return_value)
        self.assertNotIn(PASSWORD, self.all_output())

    def test_raw_key_requires_exact_hex32_and_valid_scalar(self):
        invalid = ("not-a-key-secret-sentinel", KEY + "0", KEY[:-1], "z" * 64, KEY + " ",
                   "0x" + "00" * 32, "0x" + "ff" * 32)
        for secret in invalid:
            self.prompt.return_value = secret
            with self.subTest(secret_shape=len(secret)):
                self.assertEqual(self.invoke(), 2)
            self.assertNotIn(secret, self.all_output())
        self.runner.assert_not_called()
        for secret in (KEY, KEY[2:], "0X" + KEY[2:].upper()):
            self.prompt.return_value = secret
            self.assertEqual(self.invoke(), 0)
            self.assertEqual(self.runs[-1][1]["PRIVATE_KEY"], KEY)

    def test_secret_has_no_argument_output_or_helper_file_persistence(self):
        before = set(self.workspace.rglob("*"))
        self.prompt.return_value = PASSWORD
        with patch("builtins.open", side_effect=AssertionError("helper must not read or write input files")):
            self.assertEqual(self.invoke(signer=["--keystore", str(self.keystore)]), 0)
        self.assertEqual(set(self.workspace.rglob("*")), before)
        for path in before:
            if path.is_file():
                self.assertNotIn(PASSWORD.encode(), path.read_bytes())
        self.assertNotIn(PASSWORD, repr(self.runs[-1][0]))
        self.assertNotIn(PASSWORD, self.all_output())
        self.assertEqual(self.runs[-1][2]["env"], {})

    def test_prompt_and_child_errors_never_print_secret_details(self):
        for exception, expected in ((FileNotFoundError(PASSWORD), 127), (PermissionError(PASSWORD), 126),
                                    (RuntimeError(PASSWORD), 1)):
            live_environments = []

            def failing_run(command, **kwargs):
                live_environments.append(kwargs["env"])
                raise exception

            self.runner.side_effect = failing_run
            with self.subTest(exception=type(exception).__name__):
                self.assertEqual(self.invoke(), expected)
                self.assertEqual(live_environments, [{}])
        self.runner.reset_mock()
        self.prompt.side_effect = RuntimeError(PASSWORD)
        self.assertEqual(self.invoke(), 1)
        self.runner.assert_not_called()
        self.assertNotIn(PASSWORD, self.all_output())
        self.assertNotIn(KEY, self.all_output())

    def test_child_exit_codes_and_signal_status_are_preserved(self):
        for code in (0, 1, 17, 126, 127, 255, -9, -15):
            self.returncode = code
            with self.subTest(code=code):
                self.assertEqual(self.invoke(), code if code >= 0 else 128 - code)
                self.assertEqual(self.runs[-1][2]["env"], {})

    def test_keyboard_interrupt_and_eof_refuse_without_secret_diagnostics(self):
        for exception, code in ((KeyboardInterrupt(), 130), (EOFError(PASSWORD), 2)):
            self.prompt.side_effect = exception
            with self.subTest(exception=type(exception).__name__):
                self.assertEqual(self.invoke(), code)
        self.runner.assert_not_called()
        self.assertNotIn(PASSWORD, self.all_output())

    def test_core_dump_limit_is_disabled_before_prompt_or_fails_closed(self):
        setter = Mock()
        resource_fixture = SimpleNamespace(RLIMIT_CORE=123, setrlimit=setter)
        with patch.object(launch, "resource", resource_fixture):
            ORIGINAL_CORE_LIMIT()
        setter.assert_called_once_with(123, (0, 0))
        setter.side_effect = OSError(PASSWORD)
        self.core_mock.side_effect = ORIGINAL_CORE_LIMIT
        with patch.object(launch, "resource", resource_fixture):
            self.assertEqual(self.invoke(), 2)
        self.prompt.assert_not_called()
        self.runner.assert_not_called()
        self.assertNotIn(PASSWORD, self.all_output())
        with patch.object(launch, "resource", None):
            ORIGINAL_CORE_LIMIT()

    def test_inputs_are_revalidated_after_hidden_prompt(self):
        def change_permissions(prompt, stream):
            self.keystore.chmod(0o644)
            return PASSWORD

        self.prompt.side_effect = change_permissions
        self.assertEqual(self.invoke(signer=["--keystore", str(self.keystore)]), 2)
        self.runner.assert_not_called()
        self.assertNotIn(PASSWORD, self.all_output())

    def test_real_child_economic_review_requires_exact_authorization(self):
        # The outer mode authorization and hidden signer prompt remain separate
        # from this runner's mandatory fresh economic review. The benign child
        # reads inherited fd 0; no simulated SDK write or real signer is used.
        self.python_script.write_text('''import os
import sys
assert sys.argv[1:] == ["--broadcast"]
assert bool(os.environ["PRIVATE_KEY"]) != bool(os.environ["EXAMPLE_KEYSTORE_PATH"])
expected = "APPROVE CURRENT ECONOMICS"
try:
    answer = input("Fresh economic review; type " + expected + ": ")
except EOFError:
    raise SystemExit(41)
if answer != expected:
    raise SystemExit(42)
raise SystemExit(0)
''', encoding="utf-8")
        before = set(self.workspace.rglob("*"))
        original_stdin = os.dup(0)
        try:
            for source in ("private-key", "keystore"):
                secret = PASSWORD if source == "keystore" else KEY
                signer = ["--keystore", str(self.keystore)] if source == "keystore" else ["--private-key"]
                for review_input, expected_code in (("APPROVE CURRENT ECONOMICS\n", 0), ("yes\n", 42), ("", 41)):
                    with self.subTest(source=source, authorization=review_input), \
                            tempfile.TemporaryFile(mode="w+", encoding="utf-8") as input_stream, \
                            tempfile.TemporaryFile(mode="w+", encoding="utf-8") as child_output:
                        input_stream.write(review_input)
                        input_stream.seek(0)
                        os.dup2(input_stream.fileno(), 0)
                        self.terminal.answers = [self.confirmation() + "\n"]
                        self.prompt.reset_mock()
                        self.prompt.return_value = secret
                        live_environments = []

                        def run_review_child(command, **kwargs):
                            self.prompt.assert_called_once()
                            self.assertIs(self.prompt.call_args.kwargs["stream"], self.terminal)
                            self.assertEqual(self.terminal.answers, [])
                            self.assertIsNone(kwargs["stdin"])
                            self.assertEqual(command, [sys.executable, str(self.python_script), "--broadcast"])
                            live_environments.append(kwargs["env"])
                            # Capture only output; fd 0 must genuinely be inherited.
                            kwargs["stdout"] = child_output
                            kwargs["stderr"] = child_output
                            return ORIGINAL_RUN(command, **kwargs)

                        self.runner.side_effect = run_review_child
                        self.assertEqual(self.invoke(signer=signer, mode=["--broadcast"]), expected_code)
                        self.assertEqual(live_environments, [{}])
                        child_output.seek(0)
                        output = child_output.read() + self.all_output()
                        self.assertNotIn(KEY, output)
                        self.assertNotIn(PASSWORD, output)
                        self.assertEqual(set(self.workspace.rglob("*")), before)
        finally:
            os.dup2(original_stdin, 0)
            os.close(original_stdin)
        for path in before:
            if path.is_file():
                self.assertNotIn(KEY.encode(), path.read_bytes())
                self.assertNotIn(PASSWORD.encode(), path.read_bytes())

    def test_real_custom_child_retains_cwd_unsigned_mode_and_dotenv_selection(self):
        # A benign stdlib child exercises the same .env setdefault contract as the
        # actual SDK sources. It receives no secrets in argv and writes no files.
        self.python_script.write_text('''import os
from pathlib import Path
import re
import sys
assert Path.cwd() == Path(os.environ["EXPECTED_CWD"])
for line in Path(".env").read_text(encoding="utf-8").splitlines():
    key, value = line.split("=", 1)
    os.environ.setdefault(key, value)
assert sys.argv[1:] == []
assert "EXAMPLE_KEYSTORE_UNUSED" not in os.environ
assert os.environ["PUBLIC_CONFIGURATION"] == "retained"
if os.environ["EXPECTED_SIGNER"] == "keystore":
    assert os.environ["PRIVATE_KEY"] == ""
    assert Path(os.environ["EXAMPLE_KEYSTORE_PATH"]).is_file()
    assert os.environ["EXAMPLE_KEYSTORE_PASSWORD"] not in ("", "stale-password")
else:
    assert re.fullmatch(r"0x[0-9a-f]{64}", os.environ["PRIVATE_KEY"])
    assert os.environ["EXAMPLE_KEYSTORE_PATH"] == ""
    assert os.environ["EXAMPLE_KEYSTORE_PASSWORD"] == ""
print("Custom runner checked unsigned mode and selected signer.")
raise SystemExit(17)
''', encoding="utf-8")
        (self.workspace / ".env").write_text(
            "PRIVATE_KEY=stale-key\nEXAMPLE_KEYSTORE_PATH=stale-path\n"
            "EXAMPLE_KEYSTORE_PASSWORD=stale-password\nPUBLIC_CONFIGURATION=retained\n", encoding="utf-8")
        self.runner.side_effect = ORIGINAL_RUN
        original_cwd = Path.cwd()
        try:
            os.chdir(self.workspace)
            for source in ("private-key", "keystore"):
                self.prompt.return_value = PASSWORD if source == "keystore" else KEY
                signer = ["--keystore", str(self.keystore)] if source == "keystore" else ["--private-key"]
                with self.subTest(source=source), tempfile.TemporaryFile(mode="w+", encoding="utf-8") as terminal:
                    self.terminal_mock.return_value = nullcontext(terminal)
                    with patch.dict(os.environ, {"EXPECTED_CWD": str(self.workspace), "EXPECTED_SIGNER": source,
                                                 "EXAMPLE_KEYSTORE_UNUSED": "discard-this"}):
                        self.assertEqual(self.invoke(script="launch.py", signer=signer), 17)
                    terminal.seek(0)
                    output = terminal.read()
                    self.assertIn("Custom runner checked unsigned mode and selected signer.", output)
                    self.assertNotIn(KEY, output)
                    self.assertNotIn(PASSWORD, output)
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
