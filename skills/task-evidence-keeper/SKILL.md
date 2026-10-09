---
name: task-evidence-keeper
description: Keep an evidence-first record of agent tasks so sourcing, contact, contracting, delivery, acceptance, and real payment are never conflated.
---

# Task Evidence Keeper

Use when agent workflows span messages, jobs, files, payments, provider tools, approvals or interruptions.

## Track outcomes that actually happened

1. Assign a durable task ID and preserve the real buyer/request, scoped deliverable, expected compensation, evidence reference and current blockers. Do not record credentials or personal secrets.
2. Classify events: SOURCED, CONTACTED, REPLIED, CONTRACTED, WORKING, DELIVERED, ACCEPTED, PAID, LOST, BLOCKED.
3. Require a verified external receipt for material claims: message ID for contact, written agreement for contract, QA artifact for delivery, buyer acceptance for accepted, reconciled settlement proof for PAID. A price quote, listing, invoice or promise is **not revenue**.
4. Append events, never edit them in place. Scope changes supersede prior evidence and require new acceptance criteria.
5. Optionally use `python3 scripts/ledger.py append --path ledger.jsonl --task demo --stage CONTACTED --reference msg-id` and `python3 scripts/ledger.py verify --path ledger.jsonl` to keep a local hash-chained JSONL record.
6. Summarize demand funnel, resource cost, opportunities with no reply, actual payments and unresolved risk separately. Prefer cheap tests before large compute expenses.

## Boundaries

The standalone logger cannot independently verify provider receipts, sign transactions, reconcile bank accounts or enforce financial permissions. A local SHA-256 chain can reveal accidental edits but is **not tamper-proof proof of truth**. Financial actions require separate, explicit authorization and trusted provider confirmation.
