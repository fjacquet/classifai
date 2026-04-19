# ADR-0003: Ollama as the LLM runtime

- **Status:** Accepted
- **Date:** 2024 (codified retroactively 2026-04-19)
- **Deciders:** Frederic Jacquet

## Context

ClassifAI needs an LLM to extract issuer, category, language, date, and title
from document text. The model must be swappable (different users have
different hardware) and selectable via environment variable. Options spanned:

- Local runtimes: Ollama, llama.cpp, vLLM, LM Studio
- Managed APIs: OpenAI, Anthropic, Google, Mistral (via `litellm`)

## Decision

Use **Ollama** as the default LLM runtime for both text and vision models.
Model identity is controlled by environment variables:

- `OLLAMA_MODEL_NAME` (text, defaults to `gemma:2b`)
- `OLLAMA_VISION_MODEL_NAME` (vision, defaults to `llava`)
- `OLLAMA_API_URL` (defaults to `http://localhost:11434`)

HTTP transport goes through `litellm`, giving the code a provider-neutral
call shape that would allow switching backends later with minimal code change.

## Rationale

- **Privacy:** Documents may contain PII, financial records, medical bills.
  Local inference keeps them off third-party servers entirely.
- **Cost:** Zero per-call fee. The tool's use case (bulk reorganization of
  personal archives) would rack up significant cloud-API bills at scale.
- **Offline:** Works without internet — matches the "file organizer for
  your Downloads folder" mental model.
- **Ergonomics:** `ollama pull <model>` is a one-liner; no API keys, no
  rate limits, no quota forms. Lower barrier to entry for first-time users.
- **Hardware flexibility:** Users on a laptop run `gemma:2b`; users with
  a GPU run larger/better models. Same code path either way.
- **litellm compatibility layer:** If a user wants OpenAI/Anthropic/etc.,
  the existing code can already reach them — Ollama is the default, not a
  lock-in.

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
  Via `litellm`, the door remains open to other backends without refactor.
- **Negative:**
  - Users must install and run Ollama separately.
  - Quality ceiling is lower than GPT-5 / Claude / Gemini on hard cases.
  - No built-in load balancing / autoscaling — a single local instance.
- **Retry strategy:** Ollama calls use `tenacity` with exponential backoff
  (`src/classifai/infrastructure/llm.py`) to ride out transient failures.

## References

- `src/classifai/infrastructure/llm.py` — Ollama call site
- `src/classifai/config.py` — env-var wiring
- [Ollama](https://ollama.ai/)
- [litellm](https://docs.litellm.ai/)
