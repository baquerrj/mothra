from __future__ import annotations

import nox

PYTHON = "3.10"
nox.options.default_venv_backend = "none"


def install_project(session: nox.Session) -> None:
    session.log("Using the active environment; install dependencies with pip before running nox.")


@nox.session(python=PYTHON, venv_backend="none")
def lint(session: nox.Session) -> None:
    install_project(session)
    session.run("ruff", "check", ".")


@nox.session(python=PYTHON, venv_backend="none")
def typecheck(session: nox.Session) -> None:
    install_project(session)
    session.run("mypy", "src/spending_visualizer", "app.py", "tests")


@nox.session(python=PYTHON, venv_backend="none")
def tests(session: nox.Session) -> None:
    install_project(session)
    session.run("pytest", "tests/unit", "tests/component", "tests/test_traceability.py")


@nox.session(python=PYTHON, venv_backend="none")
def smoke(session: nox.Session) -> None:
    install_project(session)
    session.run("pytest", "tests/smoke")


@nox.session(python=PYTHON, venv_backend="none")
def verify(session: nox.Session) -> None:
    install_project(session)
    session.run("ruff", "check", ".")
    session.run("mypy", "src/spending_visualizer", "app.py", "tests")
    session.run("pytest")
