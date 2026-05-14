# OpenDPP

An open-source, AI-native, standards-compliant reference implementation of a **Digital Product Passport (DPP)** for the European market.

OpenDPP exists to be the canonical "this is how to build a real DPP" example for engineering teams approaching the 2027 Battery Regulation and the 2027–2030 ESPR mandates.

> **Reference, not production.** OpenDPP is engineering education and a forkable starting point — not a hosted service, not a compliance certification, and not optimized for platform-scale.

---

## Why this exists

Most public DPP demos share three weaknesses:

1. **Blockchain-first designs** that put sensitive supplier data on chain when the problem is fundamentally federated database work.
2. **Custom identifier schemes** that ignore the EU's convergence on GS1 Digital Link.
3. **No AI-native UX**, despite DPPs increasingly being consumed by agents (search, comparison, recycling logistics, repair workflows) alongside humans.

OpenDPP fills those gaps in a single, well-documented codebase.

## Design principles

- **Identity** is anchored in [GS1 Digital Link](https://www.gs1.org/standards/gs1-digital-link).
- **Trust** is delivered through [W3C Verifiable Credentials](https://www.w3.org/TR/vc-data-model-2.0/).
- **Lifecycle events** use [GS1 EPCIS 2.0](https://www.gs1.org/standards/epcis).
- **On-chain components** are limited to tamper-evidence anchoring — never the primary data store.
- **AI agents are first-class consumers** of DPP data, served via JSON-LD with semantic vocabulary.

The v1.0 release targets the **textile** product category. Battery and electronics modules are planned for v2.0.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│         Consumer / Recycler / Regulator UI          │
│                     (Next.js)                        │
└──────────────────────────────────────────────────────┘
                          │ HTTPS / JSON-LD
                          ▼
┌──────────────────────────────────────────────────────┐
│              DPP Resolver / Service Layer            │
│                  (FastAPI / Python)                  │
│  GS1 Digital Link · Layered views · VC · LLM         │
└──────────────────────────────────────────────────────┘
                │                       │
                ▼                       ▼
   ┌────────────────────┐   ┌────────────────────────┐
   │   PostgreSQL       │   │  Anchoring Contract    │
   │   DPP · EPCIS · VC │   │  (Solidity / Polygon)  │
   └────────────────────┘   └────────────────────────┘
```

| Component | Choice |
|---|---|
| API framework | FastAPI (Python) |
| Data store | PostgreSQL with JSONB |
| Frontend | Next.js + Tailwind CSS |
| LLM provider | Anthropic Claude (with provider abstraction) |
| Verifiable Credentials | W3C VC tooling (didkit / VC-JS) |
| Anchoring | Solidity on Polygon Amoy testnet |

## Standards map

| Standard | Use in OpenDPP |
|---|---|
| GS1 Digital Link 1.4 | Product identifier URL structure |
| GS1 Web Vocabulary | Semantic field definitions in JSON-LD |
| GS1 EPCIS 2.0 | Lifecycle event log |
| GS1 Core Business Vocabulary | Event semantics |
| W3C Verifiable Credentials 2.0 | Supplier and certification attestations |
| W3C DID Core 1.0 | Issuer identity for VCs |
| W3C JSON-LD 1.1 | Linked-data serialization |
| ESPR Regulation (EU) 2024/1781 | Field coverage for textile DPP |
| ISO/IEC 15459 | Compliant product identifier formats |
| ISO/IEC 18004 | QR code symbology |
| WCAG 2.1 AA | Viewer accessibility |

## Roadmap

| Phase | Focus | Deliverable |
|---|---|---|
| 1 | Foundation | FastAPI + textile JSON Schema + GS1 Digital Link resolver |
| 2 | Viewer | Next.js with consumer / recycler / regulator views, QR codes |
| 3 | AI layer | LLM Q&A, multilingual rendering (EN/DE/FR/AR), data validation |
| 4 | Trust layer | DIDs + Verifiable Credentials for supplier attestations |
| 5 | Anchoring | Tamper-evidence on Polygon Amoy |
| 6+ | Expansion | Battery & electronics modules, EPCIS timeline, supplier flows |

## Getting started

> Setup instructions land with Phase 1. The target is a working DPP running locally in **under 30 minutes**.

```bash
git clone https://github.com/0xNadr/OpenDPP.git
cd OpenDPP
# instructions to follow
```

## Status

**Phase 1 in progress.** This repository will fill in as phases ship. Each phase is independently publishable.

## Contributing

External contributions are accepted from **v1.1 onwards**. Until then, issues and discussions are welcome.

## License

[MIT](LICENSE)

---

*Author: [Nader Bennour](https://nader.info)*
