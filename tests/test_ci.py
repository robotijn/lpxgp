"""CI checks as unit tests.

These tests run the same checks as GitHub Actions CI, allowing you to
catch issues before pushing.

Run with: uv run pytest tests/test_ci.py -v
"""

from __future__ import annotations

import subprocess
import sys


class TestLinting:
    """Ruff linting checks."""

    def test_ruff_no_errors(self) -> None:
        """Code should pass ruff linting without critical errors (E, F).

        Excludes E501 (line too long) as these are often unavoidable in
        HTML templates and long strings.
        """
        result = subprocess.run(
            [
                sys.executable, "-m", "ruff", "check", "src/",
                "--select=E,F",
                "--ignore=E501",  # Ignore line length
            ],
            capture_output=True,
            text=True,
        )
        # Allow warnings but fail on errors
        assert result.returncode == 0, f"Ruff errors:\n{result.stdout}"

    def test_ruff_imports_sorted(self) -> None:
        """Imports should be sorted (ruff I rules)."""
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "src/", "--select=I"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Import sorting issues:\n{result.stdout}"


class TestTypeChecking:
    """Mypy type checking (non-blocking for now)."""

    def test_mypy_runs_without_crash(self) -> None:
        """Mypy should run without crashing."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "src/",
                "--ignore-missing-imports",
                "--no-error-summary",
            ],
            capture_output=True,
            text=True,
        )
        # Just check it doesn't crash - actual errors are allowed for now
        assert result.returncode in (0, 1), f"Mypy crashed:\n{result.stderr}"


class TestCodeQuality:
    """Additional code quality checks."""

    def test_no_print_statements_in_src(self) -> None:
        """Source code should use logging, not print statements.

        Exceptions: config.py validation messages are allowed.
        """
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "src/",
                "--select=T201",  # print found
                "--ignore-noqa",
                "--exclude=src/config.py",  # Config uses print for startup messages
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Print statements found:\n{result.stdout}"

    def test_no_debugger_statements(self) -> None:
        """No debugger statements (pdb, breakpoint) in code."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "src/",
                "--select=T100",  # debugger found
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Debugger statements found:\n{result.stdout}"
