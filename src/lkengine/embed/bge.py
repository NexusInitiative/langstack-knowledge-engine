"""BGE-M3 embedder (``BAAI/bge-m3``): dense (1024-d) + learned-sparse in one pass.

Requires the optional extra:  ``uv sync --extra bge``  (pulls torch).

This adapter is intentionally thin - all behaviour worth testing lives behind
the ``Embedder`` protocol. It was not exercised in CI (no model download);
treat the first real ingest as its integration test.

Notes carried over from the reference implementation in ``corpus/rag``:

* No query instruction prefix - BGE-M3 encodes queries and documents alike.
* ColBERT multi-vectors are deliberately disabled: at corpus scale the
  cross-encoder reranker buys the same precision more cheaply.
* The sparse channel is the reason this model fits the corpus: exact
  identifiers (``InvalidUpdateError``, ``wrap_model_call``) that dense
  retrieval blurs are matched lexically, with no separate BM25 index.
"""

from __future__ import annotations

from collections.abc import Sequence

from lkengine.embed.base import Embedding

# XLM-RoBERTa vocabulary size; verified against the tokenizer on first load.
BGE_M3_VOCAB = 250_002


class BGEM3Embedder:
    model_id = "BAAI/bge-m3"
    dense_dim = 1024
    sparse_dim = BGE_M3_VOCAB

    def __init__(self, *, use_fp16: bool = True, batch_size: int = 16, max_length: int = 8192):
        self._use_fp16 = use_fp16
        self._batch_size = batch_size
        self._max_length = max_length
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from FlagEmbedding import BGEM3FlagModel
            except ImportError as e:  # pragma: no cover - environment dependent
                raise RuntimeError(
                    "BGE-M3 needs the optional dependency: run `uv sync --extra bge` "
                    "(or use --embedder hash for a dependency-free smoke run)."
                ) from e
            self._model = BGEM3FlagModel(self.model_id, use_fp16=self._use_fp16)
            vocab = self._model.tokenizer.vocab_size
            if vocab != self.sparse_dim:  # pragma: no cover
                raise RuntimeError(
                    f"tokenizer vocab {vocab} != schema sparse_dim {self.sparse_dim}; "
                    "re-initialise the schema with the new dimension"
                )
        return self._model

    def encode(self, texts: Sequence[str]) -> list[Embedding]:
        out = self._load().encode(
            list(texts),
            batch_size=self._batch_size,
            max_length=self._max_length,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
        )
        return [
            Embedding(
                dense=[float(x) for x in dense],
                # lexical_weights keys are token ids as strings
                sparse={int(k): float(v) for k, v in weights.items() if float(v) > 0},
            )
            for dense, weights in zip(out["dense_vecs"], out["lexical_weights"])
        ]
