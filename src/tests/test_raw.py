def test_raw_csv_to_binary():
    from ttblit.asset.builders import raw

    output = raw.raw.build('''1, 2, 3,
4, 5, 6,
7, 8, 9''', 'csv')

    assert output == b'\x01\x02\x03\x04\x05\x06\x07\x08\x09'
