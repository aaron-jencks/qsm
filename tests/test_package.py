import qsm


def test_package_exposes_version() -> None:
    assert qsm.__version__ == "0.1.0"
