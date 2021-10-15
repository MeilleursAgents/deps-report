import pytest

from deps_report import __version__


def test_version():
    assert __version__ is not None
    assert type(__version__) is str
