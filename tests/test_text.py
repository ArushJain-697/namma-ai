from sakshi.text import (blank_term, contains_term, find_span, is_content, normalize_answer,
                         split_sentences, stem, tokens)


def test_split_basic():
    assert split_sentences("Iron rusts. Water helps! Why does it? Because.") == [
        "Iron rusts.", "Water helps!", "Why does it?", "Because."]


def test_split_protects_abbreviations_initials_decimals():
    s = split_sentences("Dr. Rao measured 3.5 litres. Then J. K. Rowling arrived, e.g. late. Done.")
    assert s == ["Dr. Rao measured 3.5 litres.", "Then J. K. Rowling arrived, e.g. late.", "Done."]


def test_split_quotes_and_newlines():
    s = split_sentences('He said, "It rusts." Then he left.\nThe gate stayed.')
    assert s == ['He said, "It rusts."', "Then he left.", "The gate stayed."]


def test_split_empty():
    assert split_sentences("") == [] and split_sentences("   ") == []


def test_whole_token_matching():
    assert find_span("a party started", "art") is None
    assert find_span("in 1000 years", "100") is None
    assert find_span("in 1000 years", "1000") is not None
    assert contains_term("Iron reacts with Oxygen.", "oxygen")
    assert find_span("the wire brushes were used", "wire brushes") is not None
    assert find_span("", "x") is None and find_span("abc", "") is None


def test_blank_term_blanks_every_occurrence():
    assert blank_term("Rust is rust.", "rust") == "_____ is _____."
    assert blank_term("a party", "art") == "a party"


def test_normalize_answer():
    assert normalize_answer("The Oxygen.") == "oxygen"
    assert normalize_answer("  oxygen ") == "oxygen"
    assert normalize_answer("1,000") == "1000"
    assert normalize_answer("an apple") == "apple"


def test_tokens_numbers_and_hyphens():
    assert tokens("In 1999, a 3.5 litre red-brown tin.") == ["In", "1999", "a", "3.5", "litre", "red-brown", "tin"]


def test_stem_and_content():
    assert stem("rusts") == stem("rusting") == stem("rusted") == "rust"
    assert stem("flakes") == "flake" and stem("reaches") == "reach"
    assert is_content("oxygen") and is_content("1999") and not is_content("the") and not is_content("of")
