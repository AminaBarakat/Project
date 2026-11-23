"""Tests for the QR code maker used by the host's invite in the lobby."""

import pytest

import qr


def test_sizes_grow_with_the_text():
    assert len(qr.matrix("A")) == 21                                     # smallest code
    invite = "https://the-missing-mastermind.streamlit.app/?code=K7QX"
    assert len(qr.matrix(invite)) == 33                                  # an invite link: size 4
    assert len(qr.matrix("x" * 213)) == 57                               # largest supported


def test_the_three_corner_squares_are_in_place():
    rows = qr.matrix("https://example.com/?code=ABCD")
    n = len(rows)
    for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):
        assert rows[cy][cx]                                              # dark centre
        assert not rows[cy - 2][cx]                                      # light ring
        assert rows[cy - 3][cx]                                          # dark outer ring


def test_same_text_same_code_and_every_pattern_works():
    text = "https://example.com/?code=ABCD"
    assert qr.matrix(text) == qr.matrix(text)
    assert len({str(qr.matrix(text, mask)) for mask in range(8)}) == 8


def test_the_always_dark_square_and_timing_lines():
    rows = qr.matrix("HELLO")
    n = len(rows)
    assert rows[n - 8][8] is True                                        # required dark square
    assert [rows[6][x] for x in range(8, n - 8)] == [x % 2 == 0 for x in range(8, n - 8)]


def test_svg_has_a_white_margin_and_squares():
    text = "https://example.com/?code=ABCD"
    side = len(qr.matrix(text)) + 2 * 4                                  # code + 4-square margin each side
    picture = qr.svg(text)
    assert picture.startswith("<svg") and f"viewBox='0 0 {side} {side}'" in picture
    assert "fill='#ffffff'" in picture and "h1v1h-1z" in picture


def test_too_long_text_is_refused():
    with pytest.raises(ValueError):
        qr.matrix("x" * 300)
