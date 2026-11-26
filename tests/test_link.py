"""Option linker: hybrid BM25 + dense retrieval fused by RRF, abstain, off-syllabus gate, no fallback concept."""
import numpy as np

from sakshi import link
from sakshi.link import BM25, UNLINKED, Linker, assemble_bank, link_question, rrf
from sakshi.retention.bank import bank_from_dict

ITEMS = [
    {"id": "M1", "topic_id": "T", "concept_id": "C1", "statement": "Plants get their food from the soil",
     "probe": {"wrong_answer": "soil gives plants food"}, "fix": "Plants make food by photosynthesis"},
    {"id": "M2", "topic_id": "T", "concept_id": "C2", "statement": "Heavier objects fall faster",
     "probe": {"wrong_answer": "the heavy ball lands first"}, "fix": "Without air, all objects fall equally fast"},
    {"id": "M3", "topic_id": "T", "concept_id": "C2", "statement": "Magnets attract every metal",
     "probe": {"wrong_answer": "aluminium sticks to magnets"}, "fix": "Only some metals are magnetic"},
]


class Lib:
    def __init__(self):
        self.items = ITEMS
        self.by_id = {m["id"]: m for m in ITEMS}
        self.concepts = {"Z0": {"id": "Z0", "name": "Standardization of Measurement", "prereqs": [], "misconceptions": []},
                         "C1": {"id": "C1", "name": "Food", "prereqs": [], "misconceptions": ["M1"]},
                         "C2": {"id": "C2", "name": "Forces", "prereqs": [], "misconceptions": ["M2", "M3"]}}


class Enc:
    """Bag-of-words embedding over a tiny vocabulary: enough to make dense ranking meaningful."""
    vocab = ["plant", "food", "soil", "heavy", "fall", "ball", "magnet", "metal", "alumin"]

    def embed(self, texts):
        out = np.array([[t.lower().count(w) for w in self.vocab] for t in texts], dtype=np.float32) + 1e-3
        return out / np.linalg.norm(out, axis=1, keepdims=True)


class Mapper:
    def __init__(self, strength=None):
        self.lib, self.items, self.enc = Lib(), ITEMS, Enc()
        self.E_mis = self.enc.embed([link.belief_text(m) for m in ITEMS])
        if strength is not None:
            self.last_strength = strength


def test_rrf_fuses_two_rankings():
    assert rrf([1, 2, 3], [2, 3, 1])[0] == 2
    assert rrf([5], [5]) == [5]


def test_bm25_prefers_matching_doc():
    b = BM25([link.belief_text(m) for m in ITEMS])
    s = b.score("the magnet pulls aluminium", [0, 1, 2])
    assert int(np.argmax(s)) == 2


def test_tag_links_and_abstains():
    lk = Linker(Mapper(), abstain=0.5)
    m, c = lk.tag("Why does the heavy ball fall first?", [0, 1, 2])
    assert m["id"] == "M2" and c >= 0.5
    m, c = Linker(Mapper(), abstain=0.999).tag("something unrelated entirely", [0, 1, 2])
    assert m is None
    assert Linker(Mapper()).tag("anything", []) == (None, 0.0)


def test_off_syllabus_gate_empties_candidates():
    assert Linker(Mapper({"kw": 0.0, "cos": 0.1})).candidates({"T": 1.0}) == []
    assert Linker(Mapper({"kw": 1e9, "cos": 0.9})).candidates({"T": 1.0}) == [0, 1, 2]


def test_unlinked_question_gets_no_arbitrary_concept():
    lk = Linker(Mapper(), abstain=1.1)  # abstain on everything
    q = {"q": "What colour is the sky?", "options": ["blue", "green", "red", "pink"], "answer": 0}
    item, _ = link_question(lk, [0, 1, 2], q, 0)
    assert item["concept"] == UNLINKED
    assert all(o["misconception"] is None for o in item["options"])
    bank = assemble_bank(lk.lib, [item], "p", "s")
    assert "Z0" not in [c["id"] for c in bank["concepts"]]  # the old fallback concept is gone
    b = bank_from_dict(bank)
    assert "g1" in b.questions


def test_linked_question_uses_misconception_concept():
    lk = Linker(Mapper(), abstain=0.3)
    q = {"q": "Which falls first?", "options": ["both together", "the heavy ball falls first", "magnet metal", "soil food"],
         "answer": 0}
    item, log = link_question(lk, [0, 1, 2], q, 0)
    ids = {o["misconception"] for o in item["options"]} - {None}
    assert "M2" in ids and item["concept"] in ("C1", "C2")
    assert len(log) == 3
