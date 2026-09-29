# ADR-0003: Ollama as the LLM runtime

- **Status:** Accepted
- **Date:** 2024 (codified retroactively 2026-04-19)
- **Deciders:** Frederic Jacquet

## Context

ClassifAI needs an LLM to extract issuer, category, language, date, and title
from document text. The model must be swappable (different users have
different hardware) and selectable via environment variable. Options spanned:

- Local runtimes: Ollama, llama.cpp, vLLM, LM Studio
- Managed APIs: OpenAI, Anthropic, Google, Mistral

## Decision

Use **Ollama** as the default LLM runtime for both text and vision models.
Model identity is controlled by environment variables:

- `OLLAMA_MODEL_NAME` (text, defaults to `gemma4:e4b`)
- `OLLAMA_VISION_MODEL_NAME` (vision, defaults to `gemma4:e4b`, which is multimodal)
- `OLLAMA_API_URL` (defaults to `http://localhost:11434`)

The code calls Ollama's HTTP API (`/api/generate`) directly with `httpx` —
no provider-abstraction layer. Swapping backends would mean changing
`src/classifai/infrastructure/llm.py`, the single call site.

## Rationale

- **Privacy:** Documents may contain PII, financial records, medical bills.
  Local inference keeps them off third-party servers entirely.
- **Cost:** Zero per-call fee. The tool's use case (bulk reorganization of
  personal archives) would rack up significant cloud-API bills at scale.
- **Offline:** Works without internet — matches the "file organizer for
  your Downloads folder" mental model.
- **Ergonomics:** `ollama pull <model>` is a one-liner; no API keys, no
  rate limits, no quota forms. Lower barrier to entry for first-time users.
- **Hardware flexibility:** Users on a laptop run `gemma4:e4b` (or `gemma4:e2b`); users with
  a GPU run larger/better models. Same code path either way.

## Alternatives considered

1. **Managed cloud API (OpenAI/Anthropic).** Rejected as default: privacy +
   cost, plus hard dependency on internet connectivity for a tool that
   processes private local files.
2. **llama.cpp directly.** Rejected: lower-level, users must manage model
   files and server lifecycle themselves. Ollama wraps this cleanly.
3. **vLLM.** Rejected: optimized for high-throughput inference servers, not
   single-user desktop workloads. Overkill.
4. **Embedded / in-process model (transformers).** Rejected: adds PyTorch
   + GPU stack to install; kills CPU-only use cases.

## Consequences

- **Positive:** Privacy, zero cost, offline, minimal install friction.
  All LLM calls live in one module, so another backend stays a contained
  change.
- **Negative:**
  - Users must install and run Ollama separately.
  - Quality ceiling is lower than GPT-5 / Claude / Gemini on hard cases.
  - No built-in load balancing / autoscaling — a single local instance.
- **Retry strategy:** Ollama calls use `tenacity` with exponential backoff
  (`src/classifai/infrastructure/llm.py`) to ride out transient failures.

## Implementation notes (2026-09-29)

An earlier version of this ADR described transport through `litellm`; the
code calls Ollama directly and the `litellm` dependency has been removed.
Current behaviour of `src/classifai/infrastructure/llm.py`:

- **Structured outputs:** every call sends a JSON schema as Ollama's
  `format`. The classification `category` is an enum of
  `config/categories.yaml` (or `null`); the AI sector fallback is an enum of
  `config/sectors.yaml` (or `null`), so the model cannot create new
  folders.
- **Options:** `temperature: 0`, `num_ctx: 8192`, `keep_alive: 10m`,
  non-streaming, one shared `httpx` client.
- **Retries:** network errors and HTTP 5xx (e.g. 503 while a model loads)
  are retried, 3 attempts with exponential backoff; 4xx fail fast. Timeout
  120 s per request.
- **Prompt hygiene:** document text is fenced in `<document>` tags and
  truncated to 4 000 characters keeping head and tail.
- **No text, no call:** when nothing was extracted the model is skipped and
  the file goes to `_UNKNOWN_`.
- **Vision:** images are sent base64-encoded to `OLLAMA_VISION_MODEL_NAME`
  when `--use-vision` is on.

## References

- `src/classifai/infrastructure/llm.py` — Ollama call site
- `src/classifai/config.py` — env-var wiring
- [Ollama](https://ollama.ai/)
