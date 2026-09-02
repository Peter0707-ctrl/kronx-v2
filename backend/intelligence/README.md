# Copetra AI — Phase 4.0 Intelligence Engine

The **Copetra AI Intelligence Engine** is a universal, evidence-grounded, multi-modal reasoning and academic analysis subsystem designed for zero-fabrication operations.

---

## 1. Core Architecture & 7-Stage Deterministic Pipeline

Every user request is processed sequentially through 7 authoritative stages before model invocation and client return:

```
[User Request] 
      
      
1. Request Normalizer (Clean message, language detection [en, sw, mixed], detail level)
      
      
2. Intent Classifier (27+ granular intents, modality routing, current-turn priority)
      
      
3. Task Contract Generator (Immutable contract, allowed capabilities, strictly forbidden behaviors)
      
      
4. Multimodal Evidence Extractor (SHA-256 integrity, page/section/table provenance, OCR confidence)
      
      
5. Context & Memory Relevance Filter (Drops off-topic history e.g. Forex before inference)
      
      
6. Capability Router & Grounded Reasoner (Gemini, Groq LLaMA, OpenAI, Internal Grounded Engine)
      
      
7. Claim Verifier & Topic Drift Guard (Validates claims against evidence, blocks off-topic drift)
      
      
[Verified, Evidence-Grounded Result]
```

---

## 2. Invariants & Guarantees

1. **NO EVIDENCE = NO CLAIM**: If an uploaded document or image does not contain the requested information, the engine explicitly returns *"That information was not found in the provided document"* rather than fabricating facts.
2. **TOPIC DRIFT PREVENTION**: Historical memories from unrelated domains (e.g. Forex trading) are dropped server-side before prompt injection during academic or technical tasks.
3. **IMAGE & OCR PROVENANCE**: All visual features are classified into `OBSERVED`, `OCR_DETECTED`, `INFERRED`, `UNCERTAIN`, or `NOT_FOUND`. Blurry text is tagged with uncertainty.
4. **PASSIVE OCR DATA**: OCR text and uploaded file content are treated strictly as passive data, sanitized against prompt injections, and cannot authorize permissions or bypass security policies.
5. **MULTILINGUAL ACCURACY**: Native support for English (`en`), Swahili (`sw`), and Mixed Swahili-English research terminology.

---

## 3. REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/intelligence/request` | POST | Submits an intelligence request through the 7-stage pipeline |
| `/api/intelligence/{task_id}` | GET | Retrieves full task details, traces, claims, and status |
| `/api/intelligence/{task_id}/status` | GET | Returns task execution status and confidence |
| `/api/intelligence/{task_id}/evidence` | GET | Retrieves indexed evidence items and provenance |
| `/api/intelligence/{task_id}/sources` | GET | Lists source files and citations |
| `/api/intelligence/{task_id}/trace` | GET | Returns pipeline latency and decision traces |
| `/api/intelligence/{task_id}/cancel` | POST | Cooperatively cancels an active task |
| `/api/intelligence/{task_id}/revalidate`| POST | Re-evaluates claims against latest evidence |

---

## 4. Test & Benchmark Verification

- **Comprehensive Intelligence Tests**: 50 / 50 PASS (`test_intelligence.py`)
- **System-Wide Regression**: 606 / 606 PASS across Phase 1 through Phase 4.0
- **Static AST Security Scan**: 0 forbidden shell/eval calls
