import pytest

from sakshi.gate import check_passage
from sakshi.readability import count_syllables, fk_grade


def words(n):
    return " ".join(["word"] * n) + "."


@pytest.mark.parametrize("n,status", [
    (134, "REJECTED"), (135, "WARN"), (149, "WARN"), (150, "OK"), (300, "OK"),
    (301, "WARN"), (330, "WARN"), (331, "REJECTED"), (90, "REJECTED"),
])
def test_gate_boundaries(n, status):
    r = check_passage(words(n))
    assert r.status == status and r.words == n
    assert str(n) in r.reason  # a stated reason, always


def test_gate_empty_and_override():
    assert check_passage("").status == "REJECTED"
    assert check_passage("   ").status == "REJECTED"
    assert check_passage(words(40), override=True).ok


def test_gate_non_ascii_does_not_crash():
    assert check_passage("café “quoted” — dash " * 40).words > 0


@pytest.mark.parametrize("w,n", [("water", 2), ("oxygen", 3), ("rust", 1), ("galvanising", 4), ("the", 1), ("table", 2)])
def test_syllables(w, n):
    assert count_syllables(w) == n


def test_syllables_never_crash():
    for w in ["1999", "3.5", "red-brown", "", "a", "x-ray", "99th", "°C"]:
        assert count_syllables(w) >= 0


def test_fk_orders_easy_below_hard():
    easy = "The cat sat on the mat. It was a big cat."
    hard = "Ferrous substances undergo oxidative degradation upon prolonged atmospheric exposure."
    assert fk_grade(hard) > fk_grade(easy)
    assert fk_grade("") == 0.0
