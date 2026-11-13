"""Map a passage (and each evidence sentence in it) to the right misconceptions. Eedi-style multi-stage retrieval.

Stages (all offline, all small models):
  1. Topic shortlist for the whole passage: keyword (BM25, from misconceptions.Library) + meaning similarity
     between the passage and each topic's concept names. Keep the top topics.
  2. Candidates: every misconception attached to a concept of those topics (the graph does the narrowing).
  3. Per evidence sentence, features for each candidate:
       cos_fix   meaning similarity between the sentence and the misconception's FIX (the correct idea it needs)
       cos_mis   meaning similarity between the sentence and the wrong belief + its typical wrong answer
       kw        keyword overlap between the sentence and the misconception's cue words / concept
       topic     how strongly its topic matched the passage
  4. Re-rank the top candidates with an NLI model: P(contradiction | sentence, belief). A misconception is a FALSE
     statement, so the sentence that proves it wrong is exactly the evidence that can diagnose it.
  5. Final score = weights . features; the weights are learned on our dataset (scripts/eval_mapping.py --fit).
Encoders are pluggable: TorchEncoders (sentence-transformers, for the Mac and evaluation) or PteEncoders
(ExecuTorch .pte files, for the Pi; see scripts/export_helpers.py). Without encoders, use misconceptions.Library
(keywords only) as the fallback.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

import numpy as np

from .misconceptions import DEFAULT_DIR, Library
from .text import content_stems, split_sentences, tokens

INDEX_DIR = os.path.join(DEFAULT_DIR, "index")
FEATURES = ("cos_fix", "cos_mis", "kw", "topic", "nli_contra", "nli_entail_fix")
DEFAULT_WEIGHTS = {"cos_fix": 3.0, "cos_mis": 1.5, "kw": 1.0, "topic": 1.0, "nli_contra": 2.0, "nli_entail_fix": 1.0,
                   "bias": 0.0}


class TorchEncoders:
    """sentence-transformers models (Mac / evaluation)."""

    def __init__(self, embed_model: str = "BAAI/bge-small-en-v1.5", nli_model: str | None = "cross-encoder/nli-deberta-v3-xsmall",
                 device: str | None = None):
        from sentence_transformers import CrossEncoder, SentenceTransformer
        self.embed_name, self.nli_name = embed_model, nli_model
        self._emb = SentenceTransformer(embed_model, device=device)
        self._nli = CrossEncoder(nli_model, device=device) if nli_model else None
        if self._nli is not None:
            lab = {v.lower(): int(k) for k, v in self._nli.model.config.id2label.items()}
            self.nli_index = (lab["contradiction"], lab["entailment"], lab["neutral"])

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self._emb.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False),
                          dtype=np.float32)

    def nli(self, pairs: list[tuple[str, str]]) -> np.ndarray:
        """Probabilities [contradiction, entailment, neutral] per (premise, hypothesis)."""
        if self._nli is None or not pairs:
            return np.zeros((len(pairs), 3), dtype=np.float32)
        logits = np.asarray(self._nli.predict(pairs, batch_size=32, show_progress_bar=False), dtype=np.float32)
        logits = logits[:, list(self.nli_index)]
        e = np.exp(logits - logits.max(1, keepdims=True))
        return e / e.sum(1, keepdims=True)


class PteEncoders:
    """The same two helpers as ExecuTorch .pte files (scripts/export_helpers.py): the device path.
    Needs only executorch, numpy and the `tokenizers` package (all on the Pi / UNO Q). Batch size 1, fixed length."""

    def __init__(self, directory: str = os.path.join(os.path.dirname(DEFAULT_DIR), "..", "models", "helpers")):
        from executorch.runtime import Runtime
        from tokenizers import Tokenizer
        rt = Runtime.get()
        self._m, self._tok, self._seq = {}, {}, {}
        for kind in ("embed", "nli"):
            d = os.path.join(directory, kind)
            if not os.path.exists(os.path.join(d, "model.pte")):
                continue
            meta = json.load(open(os.path.join(d, "meta.json")))
            tok = Tokenizer.from_file(os.path.join(d, "tokenizer.json"))
            tok.enable_truncation(meta["seq"])
            tok.enable_padding(length=meta["seq"])
            self._m[kind] = rt.load_program(os.path.join(d, "model.pte")).load_method("forward")
            self._tok[kind], self._seq[kind] = tok, meta
        self.embed_name = "pte_" + os.path.basename(self._seq["embed"]["source"].rstrip("/"))
        if "nli" in self._m:
            lab = {v.lower(): int(k) for k, v in self._seq["nli"]["id2label"].items()}
            self.nli_index = (lab["contradiction"], lab["entailment"], lab["neutral"])
        else:
            self.nli = None  # type: ignore[assignment]  (mapper then skips the NLI re-rank)

    def _run(self, kind: str, enc) -> np.ndarray:
        import torch
        ids = torch.tensor([enc.ids], dtype=torch.long)
        mask = torch.tensor([enc.attention_mask], dtype=torch.long)
        return self._m[kind].execute([ids, mask])[0].numpy()[0]

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.stack([self._run("embed", self._tok["embed"].encode(t)) for t in texts]).astype(np.float32)

    def nli(self, pairs: list[tuple[str, str]]) -> np.ndarray:  # noqa: F811
        if not pairs:
            return np.zeros((0, 3), dtype=np.float32)
        logits = np.stack([self._run("nli", self._tok["nli"].encode(a, b)) for a, b in pairs])[:, list(self.nli_index)]
        e = np.exp(logits - logits.max(1, keepdims=True))
        return (e / e.sum(1, keepdims=True)).astype(np.float32)


def mis_text(m: dict) -> str:
    wa = (m.get("probe") or {}).get("wrong_answer", "")
    return f"{m['statement']} {('A student might answer: ' + wa) if wa else ''}".strip()


def fix_text(m: dict) -> str:
    return f"{m.get('concept', '')}: {m.get('fix', '')}"


@dataclass
class Scored:
    misconception: dict
    score: float
    features: dict


class Mapper:
    def __init__(self, library: Library, encoders, index_dir: str = INDEX_DIR, weights: dict | None = None,
                 n_topics: int = 3, rerank: int = 12):
        self.lib, self.enc, self.n_topics, self.rerank = library, encoders, n_topics, rerank
        self.items = library.items
        self.pos = {m["id"]: i for i, m in enumerate(self.items)}
        self._load_or_build_index(index_dir)
        wpath = os.path.join(index_dir, "weights.json")
        self.w = weights or (json.load(open(wpath)) if os.path.exists(wpath) else DEFAULT_WEIGHTS)

    # ---- index ------------------------------------------------------------------------------------------
    def _load_or_build_index(self, d: str) -> None:
        name = getattr(self.enc, "embed_name", "encoder").replace("/", "_")
        path = os.path.join(d, f"{name}.npz")
        ids = [m["id"] for m in self.items]
        if os.path.exists(path):
            z = np.load(path, allow_pickle=False)
            if list(z["ids"]) == ids:
                self.E_mis, self.E_fix, self.topic_ids, self.E_topic = z["mis"], z["fix"], list(z["topic_ids"]), z["topic"]
                return
        self.E_mis = self.enc.embed([mis_text(m) for m in self.items])
        self.E_fix = self.enc.embed([fix_text(m) for m in self.items])
        by_topic: dict[str, list[str]] = {}
        for c in self.lib.concepts.values():
            by_topic.setdefault(c["topic_id"], []).append(c["name"])
        titles = {m["topic_id"]: m.get("topic", "") for m in self.items}
        self.topic_ids = sorted(titles)
        self.E_topic = self.enc.embed([f"{titles[t]}: {', '.join(by_topic.get(t, [])[:30])}" for t in self.topic_ids])
        os.makedirs(d, exist_ok=True)
        np.savez(path, ids=np.array(ids), mis=self.E_mis, fix=self.E_fix, topic_ids=np.array(self.topic_ids), topic=self.E_topic)

    # ---- stage 1-2 --------------------------------------------------------------------------------------
    def topics(self, passage: str) -> dict[str, float]:
        """Topic -> score in [0, 1]: keyword rank fused with meaning similarity (reciprocal-rank fusion)."""
        kw = self.lib.match(passage, n_topics=10)
        kw_rank = {t.topic_id: r for r, t in enumerate(kw.topics)}
        sims = self.E_topic @ self.enc.embed([passage])[0]
        # how well the passage fits ANY topic, in absolute terms (for the off-syllabus fallback)
        self.last_strength = {"cos": float(sims.max()) if len(sims) else 0.0,
                              "kw": float(kw.topics[0].score) if kw.topics else 0.0}
        em_rank = {self.topic_ids[i]: r for r, i in enumerate(np.argsort(-sims)[:10])}
        fused = {t: 1 / (60 + kw_rank.get(t, 99)) + 1 / (60 + em_rank.get(t, 99)) for t in set(kw_rank) | set(em_rank)}
        top = sorted(fused, key=fused.get, reverse=True)[: self.n_topics]
        best = fused[top[0]] if top else 1
        return {t: fused[t] / best for t in top}

    # ---- stage 3-5 --------------------------------------------------------------------------------------
    def score_sentence(self, sentence: str, topic_scores: dict[str, float], n: int = 5,
                       sentence_vec: np.ndarray | None = None) -> list[Scored]:
        cand = [i for i, m in enumerate(self.items) if m["topic_id"] in topic_scores]
        if not cand:
            return []
        v = sentence_vec if sentence_vec is not None else self.enc.embed([sentence])[0]
        s_st = set(content_stems(sentence))
        feats = []
        for i in cand:
            m = self.items[i]
            cue = set(content_stems(" ".join(m.get("trigger_cues") or []) + " " + m.get("concept", "")))
            feats.append({"cos_fix": float(self.E_fix[i] @ v), "cos_mis": float(self.E_mis[i] @ v),
                          "kw": len(s_st & cue) / (len(cue) ** 0.5 or 1), "topic": topic_scores[m["topic_id"]],
                          "nli_contra": 0.0, "nli_entail_fix": 0.0})
        pre = np.array([self._lin(f, nli=False) for f in feats])
        top = list(np.argsort(-pre)[: self.rerank])
        if hasattr(self.enc, "nli"):
            pairs = [(sentence, self.items[cand[j]]["statement"]) for j in top] + \
                    [(sentence, self.items[cand[j]].get("fix", "")) for j in top]
            probs = self.enc.nli(pairs)
            for k, j in enumerate(top):
                feats[j]["nli_contra"] = float(probs[k, 0])
                feats[j]["nli_entail_fix"] = float(probs[len(top) + k, 1])
        out = [Scored(self.items[cand[j]], self._lin(feats[j]), feats[j]) for j in top]
        return sorted(out, key=lambda s: -s.score)[:n]

    def _lin(self, f: dict, nli: bool = True) -> float:
        return self.w.get("bias", 0.0) + sum(self.w.get(k, 0.0) * f[k] for k in FEATURES if nli or not k.startswith("nli"))

    # ---- what diagnostic.generate_bank needs ------------------------------------------------------------
    def plan(self, passage: str, k: int = 4, n: int = 5) -> tuple[list[tuple[str, list[Scored]]], dict]:
        """Pick k evidence sentences with the strongest diagnostic potential, each with its n-belief menu."""
        ts = self.topics(passage)
        sents = [s for s in split_sentences(passage) if 8 <= len(tokens(s)) <= 45]
        if not sents:
            return [], ts
        vecs = self.enc.embed(sents)
        scored = [(s, self.score_sentence(s, ts, n=n, sentence_vec=vecs[i])) for i, s in enumerate(sents)]
        strength = [(sum(x.score for x in sc[:3]) if len(sc) >= 3 else -1e9, i) for i, (s, sc) in enumerate(scored)]
        picked = []
        for _, i in sorted(strength, reverse=True):
            if any(abs(i - j) <= 1 for j in picked):
                continue
            picked.append(i)
            if len(picked) == k:
                break
        return [scored[i] for i in sorted(picked)], ts

    def option_consistency(self, options: list[dict], menu: list[dict]) -> list[str | None]:
        """Round-trip check (cycle consistency): for each wrong option, which belief in the menu best explains it?
        Returns that belief's label per option, or None when no belief clearly wins."""
        if not options or not menu:
            return []
        from .diagnostic import LABELS
        O = self.enc.embed([f"{o['text']}. {o.get('why', '')}" for o in options])
        B = np.stack([self.E_mis[self.pos[m["id"]]] if m["id"] in self.pos else self.enc.embed([mis_text(m)])[0]
                      for m in menu])
        sims = O @ B.T
        out = []
        for row in sims:
            order = np.argsort(-row)
            out.append(LABELS[order[0]] if row[order[0]] - row[order[1]] >= 0.02 else None)
        return out
