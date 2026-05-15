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

Target: full stack running locally in **under 5 minutes**. Everything runs in Docker — no host Python or Node required.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (Desktop or Engine)
- `make`

### Quickstart

```bash
git clone https://github.com/0xNadr/OpenDPP.git
cd OpenDPP

make build       # build api + web images
make up          # start the stack (postgres + api + web)
make migrate     # apply Alembic migrations
make seed        # load three sample textile products
```

Open:

- **Viewer landing page** — http://localhost:3030
- **Sample product (consumer view)** — http://localhost:3030/01/07350053850010/10/ATL-2026-T01
- **Recycler / Regulator views** — same URL with `?view=recycler` or `?view=regulator`
- **API docs (OpenAPI)** — http://localhost:8080/docs
- **JSON-LD of a passport** —
  ```bash
  curl -H 'Accept: application/ld+json' \
    http://localhost:8080/01/07350053850010/10/ATL-2026-T01
  ```
- **Multilingual** — append `?lang=de`, `?lang=fr`, or `?lang=ar` to any DPP URL (e.g., http://localhost:3030/01/07350053850010/10/ATL-2026-T01?lang=ar — note the RTL layout)
- **Chat with a product** — open any DPP page and click "Ask about this product" in the bottom-right corner

Host port map: **web 3030 · api 8080 · postgres 5433 · hardhat 8545**. Non-defaults on purpose, so the stack doesn't collide with other dockerized dev projects on the same machine.

### Common tasks

```bash
make logs        # tail logs from all services
make test        # run the pytest suite inside the api container
make lint        # ruff + tsc inside the containers
make shell-api   # bash inside the api container
make shell-web   # sh inside the web container
make down        # stop the stack (keeps the db volume)
make nuke        # tear everything down including the db volume
```

### Repository layout

```
OpenDPP/
├── api/                          FastAPI service
│   ├── src/opendpp/
│   │   ├── routers/              GS1 Digital Link, REST, QR
│   │   ├── models/               SQLAlchemy ORM
│   │   ├── schemas/              Pydantic request/response models
│   │   ├── jsonld/               JSON-LD context (GS1 Web Vocab)
│   │   └── validation.py         JSON Schema enforcement
│   ├── alembic/                  Migrations
│   ├── tests/
│   └── Dockerfile                multi-stage (dev / prod)
├── web/                          Next.js viewer
│   ├── app/
│   │   ├── 01/[gtin]/...         GS1 Digital Link routes
│   │   └── page.tsx              landing page with QR codes
│   ├── components/
│   │   └── views/                Consumer / Recycler / Regulator
│   ├── lib/                      API client, types (auto-generated)
│   ├── scripts/gen-types.mjs     codegen from textile-dpp.v1.json
│   └── Dockerfile                multi-stage (dev / prod)
├── schemas/
│   └── textile-dpp.v1.json       Canonical DPP schema (draft 2020-12)
├── seed/
│   ├── products.json             Three sample textile products
│   └── load_seed.py              Idempotent loader
├── docker-compose.yml
└── Makefile
```

## AI features (Phase 3)

OpenDPP ships with three LLM-backed endpoints, all routed through a `ChatProvider` abstraction (Anthropic Claude by default, with a deterministic mock fallback for no-key / CI dev):

- **`POST /api/chat/{record_id}`** — streaming Q&A grounded in a specific DPP. SSE response with `delta` / `done` / `error` events. Used by the floating chat drawer on every DPP page.
- **`GET /api/dpp/{record_id}/translate?lang=…`** — runtime translation of a DPP into EN / DE / FR / AR. First call hits the LLM; subsequent calls with the same content hit a Postgres cache (`translation_cache` table). Cache auto-invalidates when the DPP changes.
- **`POST /api/validate/semantic`** — LLM-assisted post-validation for candidate DPP data, catching what JSON Schema can't (composition percentages that don't sum to 100, expired certificates, supply-chain inconsistencies, etc).

### Wiring up Claude

Drop your API key into `.env` and restart:

```bash
echo 'ANTHROPIC_API_KEY=sk-ant-…' >> .env
make restart
```

Without a key, the stack silently uses `MockChatProvider` — translations get bracketed `[DE] …` prefixes, chat returns a canned acknowledgement, semantic validation catches the percentage-sum case. The mock is deterministic enough that the test suite runs against it.

### Multilingual viewer

Append `?lang=de`, `?lang=fr`, or `?lang=ar` to any DPP URL. The viewer fetches the translated payload server-side, sets `dir="rtl"` automatically for Arabic, and propagates the language through the language switcher in the page header.

## Trust layer (Phase 4)

OpenDPP issues and verifies **W3C Verifiable Credentials** so individual claims on a DPP can be cryptographically attributed to a specific supplier:

- **DID method:** `did:key` (self-resolving — the public key *is* the identifier; no DNS, no resolver, no chain)
- **Signature suite:** Ed25519 / EdDSA
- **Credential format:** VC-JWT (W3C VC Data Model 2.0 with JWT serialization)

### Endpoints

- **`POST /api/vc/issue`** — body: `{supplier_id, dpp_record_id, attestation_type, claim}` → returns signed JWT + unsigned VC body
- **`POST /api/vc/verify`** — body: `{jwt}` → returns `{valid, issuer, subject, claims, error?}`. Verification is self-contained — issuer DID resolves to its public key directly, no network call needed
- **`GET /api/vc/dpp/{record_id}`** — list every VC attached to a DPP (powers the badge in the viewer)

### What `make seed` ships

Three demo suppliers with deterministic Ed25519 keys (the same DIDs across every clone of this repo), each issuing one signed attestation about their seeded product: GOTS for Atelier, GRS for Northwave, RWS for Soraya. Consumer view shows a ✓ "Verified by …" badge next to each certification with a matching VC. Regulator view exposes the raw JWT, the credential body, and a **Verify signature** button that hits `/api/vc/verify` from the browser.

## Documentation

Long-form material lives in the **[OpenDPP Wiki](https://github.com/0xNadr/OpenDPP/wiki)**:

- **[Architecture](https://github.com/0xNadr/OpenDPP/wiki/Architecture)** — the four-tier stack, what runs where, why each piece exists
- **[Standards Map](https://github.com/0xNadr/OpenDPP/wiki/Standards-Map)** — which spec is implemented in which file
- **[Security Model](https://github.com/0xNadr/OpenDPP/wiki/Security-Model)** — what's cryptographically guaranteed, what's demo-grade, what to harden
- **[Deploying to a VPS](https://github.com/0xNadr/OpenDPP/wiki/Deploying-To-A-VPS)** — production deployment recipe
- **[Switching the Anchor to Polygon Amoy](https://github.com/0xNadr/OpenDPP/wiki/Switching-The-Anchor-To-Polygon-Amoy)** — moving Phase 5 to a real public testnet
- **[Extending the Schema](https://github.com/0xNadr/OpenDPP/wiki/Extending-The-Schema)** — adding battery / electronics / footwear beyond the v1.0 textile reference

## Status

**Phase 1 (Foundation) — shipped.** API that resolves a GS1 Digital Link URL to a JSON-LD DPP record. Three seeded textile samples.

**Phase 2 (Viewer) — shipped.** Next.js viewer with consumer / recycler / regulator views, scannable QR codes, fully-dockerized stack.

**Phase 3 (AI layer) — shipped.** LLM Q&A (SSE streaming), multilingual rendering with Postgres-cached translations, LLM-assisted semantic validation. Defaults to Claude Sonnet 4.6; deterministic mock fallback for no-key dev.

**Phase 4 (Trust layer) — shipped.** Ed25519 / `did:key` Verifiable Credentials, end-to-end issue → store → verify with one attestation per seeded product. ✓ badges on consumer view, full JWT + verify-button surface on regulator view.

**Phase 5 (Anchoring) — shipped.** Minimal Solidity contract (`OpenDPPAnchor`), Hardhat workspace, local chain in docker-compose with auto-deploy. SHA-256 of canonical DPP JSON gets anchored on-chain; regulator view shows the proof and a Re-verify button that re-hashes the current DPP and queries the contract directly — independent of OpenDPP's database. 54 passing tests.

Next: VPS deploy to `opendpp.nader.info`.

## Anchoring (Phase 5)

The point of anchoring is **tamper-evidence**: store a hash of the DPP on a public ledger so anyone can verify the DPP hasn't changed since, without trusting OpenDPP's database.

**How it works:**
1. Take the DPP's `data` field, canonicalize it (sorted keys, no whitespace, UTF-8), SHA-256 it → 32-byte hash.
2. Submit a transaction to `OpenDPPAnchor.anchor(bytes32)` which stores `block.timestamp` against that hash and emits an event.
3. To verify later: re-hash the current DPP, call `anchoredAt(hash)` on the contract. Non-zero return = the hash was anchored at that timestamp. If the DPP was tampered with after anchoring, the hash won't match anything on-chain.

**Endpoints:**

- `POST /api/anchor/{record_id}` — anchor (idempotent: returns existing proof if already anchored)
- `GET /api/anchor/{record_id}/proof` — list stored proofs
- `GET /api/anchor/{record_id}/verify` — re-hash + query the chain right now

**Local dev:** a `hardhat` service in docker-compose runs a local chain and auto-deploys `OpenDPPAnchor` on startup. `make seed` anchors all three demo products to it.

**Polygon Amoy (production-ish):** set these env vars in `.env` and restart:

```
ANCHOR_RPC_URL=https://rpc-amoy.polygon.technology
ANCHOR_PRIVATE_KEY=0x…           # funded with Amoy MATIC from a faucet
ANCHOR_CONTRACT_ADDRESS=0x…      # from `make deploy-contract` against Amoy
ANCHOR_CHAIN_LABEL=polygon-amoy
ANCHOR_EXPLORER_TX_TEMPLATE=https://amoy.polygonscan.com/tx/{tx}
```

## Contributing

External contributions are accepted from **v1.1 onwards**. Until then, issues and discussions are welcome.

## License

[MIT](LICENSE)

---

*Author: [Nader Bennour](https://nader.info)*
