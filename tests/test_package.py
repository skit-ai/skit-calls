from skit_calls import __version__
from skit_calls import utils


def test_package_version():
    assert utils.get_version() == __version__
