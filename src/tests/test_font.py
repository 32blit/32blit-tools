def test_font_image(test_resources):
    from ttblit.asset.builders import font
    image = open(test_resources / "8x8font.png", "rb").read()
    output = font.font.build(image, 'image')
    expected = open(test_resources / "8x8font.bin", "rb").read()

    assert output == expected


def test_font_image_rows(test_resources):
    from ttblit.asset.builders import font
    image = open(test_resources / "8x8font_rows.png", "rb").read()
    output = font.font.build(image, 'image', height=8)
    expected = open(test_resources / "8x8font_rows.bin", "rb").read()

    assert output == expected
