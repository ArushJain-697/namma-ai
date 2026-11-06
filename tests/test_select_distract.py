from conftest import sample_passage
from sakshi.distract import make_options
from sakshi.lexicon import PLAIN_WORDS
from sakshi.select import analyse
from sakshi.text import BLOCKLIST, STOPWORDS, find_span, stem


def test_candidates_are_whole_token_spans_of_their_witness():
    a = analyse(sample_passage())
    assert a.candidates
    for c in a.candidates:
        assert find_span(a.sentences[c.sent_idx], c.term), c


def test_candidate_invariants():
    a = analyse(sample_passage())
    stems = [stem(c.term) for c in a.candidates]
    assert len(stems) == len(set(stems))  # unique answers
    for c in a.candidates:
        assert c.term.lower() not in STOPWORDS and c.term.lower() not in BLOCKLIST
        if c.reserve:
            assert stem(c.reserve) != stem(c.term)
            assert find_span(a.sentences[c.sent_idx], c.reserve)
        if c.kind == "word" and (c.term.lower() in PLAIN_WORDS or stem(c.term) in PLAIN_WORDS):
            assert not c.relevant  # plain words never count as relevant


def test_numbers_and_names_are_typed():
    a = analyse("Maria visited Mysore in 1999 with her aunt. The palace in Mysore was built long ago. "
                "Maria loved the palace very much. The palace gardens grow roses and jasmine.")
    kinds = {c.kind for c in a.candidates}
    assert kinds & {"number", "name"}


def test_passage_without_numbers_or_names_still_works():
    a = analyse("Rain falls from clouds. Clouds form when water vapour cools. Cooling vapour becomes tiny drops. "
                "Tiny drops join together inside clouds until they are heavy.")
    assert a.candidates


def test_very_short_sentences_do_not_crash():
    a = analyse("Yes. No. Ok. Hi.")
    assert a.candidates == []
    assert analyse("").candidates == []


def test_options_invariants():
    p = sample_passage()
    a = analyse(p)
    for c in a.candidates:
        opts = make_options(p, c.term, c.sent_idx, c.kind, seed=3)
        if opts is None:
            continue
        assert len(opts) == 4 and len(set(o.lower() for o in opts)) == 4
        assert sum(1 for o in opts if o.lower() == c.term.lower()) == 1
        witness_stems = {stem(t) for t in a.sentences[c.sent_idx].lower().replace(".", "").split()}
        for o in opts:
            if o.lower() != c.term.lower():
                assert stem(o) not in witness_stems  # no option from the witness sentence
        if c.kind == "word":
            assert all(o == o.lower() for o in opts)  # no capital-letter giveaway
        assert make_options(p, c.term, c.sent_idx, c.kind, seed=3) == opts  # deterministic


def test_options_none_when_too_few_distractors():
    assert make_options("Iron rusts in damp air. Rust flakes away from iron.", "damp", 0, "word", 1) is None


def test_distractors_vary_across_items_and_match_word_ending():
    p = sample_passage()
    a = analyse(p)
    seen: list[set[str]] = []
    for c in a.candidates:
        opts = make_options(p, c.term, c.sent_idx, c.kind, seed=c.sent_idx * 7 + 1)
        if opts:
            seen.append({o for o in opts if o.lower() != c.term.lower()})
    assert len(seen) >= 3
    assert len({frozenset(s) for s in seen}) >= 3  # not the same three wrong answers every time
    # -ing key: -ing distractors are preferred when the passage has them
    opts = make_options("Painting stops rust. Oil also stops rust. Coating helps metal. Galvanising coats iron. "
                        "Welding joins iron. Sanding removes rust.", "Painting", 0, "word", 1)
    assert opts is None or sum(o.lower().endswith("ing") for o in opts) >= 3
