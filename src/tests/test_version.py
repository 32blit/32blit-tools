import pytest


def test_version(capsys):
    from ttblit import main, __version__

    with pytest.raises(SystemExit):
        main(['version'])

    assert capsys.readouterr().out == f'{__version__}\n'
