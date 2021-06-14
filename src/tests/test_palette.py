import pytest
import tempfile
import textwrap

def test_palette_entries():
    from ttblit.core.palette import Palette

    palette = Palette()
    assert len(palette) == 0

    white = (255, 255, 255, 255)
    black = (0, 0, 0, 255)
    transparent_white = (255, 255, 255, 0)
    transparent_black = (0, 0, 0, 0)
    transparent_red = (255, 0, 0, 0)

    # add
    assert palette[palette.get_entry(*white)] == white
    assert len(palette) == 1

    # get existing
    assert palette[palette.get_entry(*white)] == white
    assert len(palette) == 1

    # get existing (strict)
    assert palette[palette.get_entry(*white)] == white
    assert len(palette) == 1

    # doesn't exist and can't add because strict
    with pytest.raises(TypeError):
        palette.get_entry(*black, strict=True)
    assert len(palette) == 1

    # add another
    assert palette[palette.get_entry(*black)] == black
    assert len(palette) == 2

    # add a transparent colour
    tw_index = palette.get_entry(*transparent_white)
    assert len(palette) == 3

    # should work because transparent white is the same as transparent black
    assert palette.get_entry(*transparent_black, strict=True) == tw_index
    assert len(palette) == 3

    # should also not extend the palette in non-strict mode
    assert palette.get_entry(*transparent_red) == tw_index
    assert len(palette) == 3

    # fill up the palette
    for n in range(253):
        palette.get_entry(n, 0, 255, 255)
    assert len(palette) == 256

    with pytest.raises(TypeError):
        palette.get_entry(0, 255, 0, 255)
    assert len(palette) == 256

    # the resulting struct data should have same length as the source
    assert len(palette.tostruct()) == len(palette)

    # the iter should also have the same length
    assert len(list(palette)) == len(palette)


def test_palette_gpl():
    from ttblit.core.palette import Palette

    with tempfile.NamedTemporaryFile('w', suffix='.gpl') as test_palette_file:
        test_palette_file.write(textwrap.dedent('''
            GIMP Palette
            Name: Test
            Columns: 8
            #
            255 255 255\tUntitled
              0   0   0\tUntitled
            255   0   0
        '''))
        test_palette_file.flush()

        palette = Palette(test_palette_file.name)

        assert len(palette) == 3
        assert palette[0] == (255, 255, 255, 255)
