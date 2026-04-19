# ADR-0001: Stay on Tesseract for OCR; defer Chandra OCR 2 adoption

- **Status:** Accepted
- **Date:** 2026-04-19
- **Deciders:** Frederic Jacquet
- **Context window:** evaluation triggered by the March 2026 release of Chandra OCR 2 (datalab-to)

## Context

ClassifAI extracts text from images (`.png`, `.jpg`, `.tiff`, …) using `pytesseract`
in `src/classifai/infrastructure/parsing.py`. Extracted text is then passed to an
Ollama-hosted LLM for metadata extraction (issuer, category, date, language) —
OCR output is a means, not a product. PDF text extraction currently uses
PyMuPDF's text layer with **no OCR fallback** for scanned PDFs.

Chandra OCR 2 (`datalab-to/chandra-ocr-2`, March 2026) is a 5B-parameter
vision-language model built on Qwen 3.5 that tops the olmOCR benchmark (85.9%),
supports 90 languages, preserves layout, and beats Gemini 2.5 Flash and
GPT-5 Mini on multilingual document tasks.

## Decision

**Do not replace or wrap Tesseract with Chandra OCR 2 at this time.** Keep
`pytesseract` as the sole OCR backend. Re-evaluate if and when either of these
conditions becomes true:

1. Real classification failures in production trace back to Tesseract quality
   (handwriting, complex tables, non-Latin scripts).
2. The project gains a reliable GPU deployment target and the current CPU-only
   footprint is no longer a design constraint.

## Rationale

The classification pipeline consumes OCR output as flat text. Layout fidelity,
structured output (HTML/MD/JSON), and table extraction — Chandra's main
strengths — do not translate into better issuer/category/date extraction
under the current prompting strategy.

The costs are concrete:

| Dimension            | Tesseract (current)         | Chandra OCR 2                       |
| -------------------- | --------------------------- | ----------------------------------- |
| Compute              | CPU                         | GPU, ~10–16 GB VRAM                 |
| Install footprint    | ~50 MB binary               | ~10 GB weights + torch/transformers |
| Latency / page       | ~100 ms                     | seconds (GPU)                       |
| License              | Apache 2.0                  | Modified OpenRAIL-M                 |
| Overlap with stack   | None                        | Duplicates the LLaVA vision path    |

The project already exposes `OLLAMA_VISION_MODEL_NAME` (LLaVA) as the vision
backend for image-centric tasks; adding Chandra would introduce a second vision
runtime without replacing the first.

The higher-leverage OCR gap is **no fallback for scanned PDFs** — independent
of engine choice. That gap should be closed before changing engines.

## Alternatives considered

1. **Replace Tesseract with Chandra OCR 2.**
   Rejected: CPU-only deployments break; install weight grows by ~200×;
   marginal benefit for text-only downstream consumption.

2. **Add Chandra as an opt-in backend behind a config flag.**
   Rejected for now: adds a second vision runtime on top of LLaVA with no
   evidence current users need it. Revisit once a concrete user reports
   Tesseract-driven classification failures.

3. **Route image OCR through the existing LLaVA vision model (already in
   config) instead of Tesseract.**
   Not taken here, but worth a separate evaluation — this would consolidate
   vision inference on one backend without adding Chandra. Out of scope for
   this ADR.

4. **Close the scanned-PDF OCR gap first (engine-agnostic).**
   Accepted as the next higher-priority work item. Tracked separately.

## Consequences

- **Positive:** Zero churn; CPU-only deployments keep working; install footprint
  stays small; no license re-review needed.
- **Negative:** Users with handwritten, tabular, or non-Latin scanned inputs
  continue to get Tesseract-quality text — which may hurt downstream
  classification on those documents. If this surfaces, revisit.
- **Follow-up:** Open an issue for scanned-PDF OCR fallback (not covered by
  this decision).

## References

- [datalab-to/chandra (GitHub)](https://github.com/datalab-to/chandra)
- [datalab-to/chandra-ocr-2 (Hugging Face)](https://huggingface.co/datalab-to/chandra-ocr-2)
- [chandra-ocr (PyPI)](https://pypi.org/project/chandra-ocr/)
- Current OCR call site: `src/classifai/infrastructure/parsing.py` (line 84,
  `pytesseract.image_to_string`)
