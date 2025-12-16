# AML Research Project - Claude Code Context

## Project Overview
Customer Narrative Analyzer (CNA) for Handle-AI - A FRAML (Fraud + AML) detection system that uses LLMs to analyze customer "stories" over time for logical inconsistencies.

**Core Innovation**: Move from "Is this transaction unusual?" to "Does this customer's story make sense?"

---

## Architecture: Three-Layer Tribunal System

### Design Philosophy

The system is architected as three independent, loosely coupled modules within a **monorepo**. This separation is critical for:

1. **Deterministic vs Probabilistic**: Statistical Engine (math) must be 100% reproducible. AI Agent (LLM) is probabilistic. Mixing them makes debugging impossible.
2. **Latency & Cost Optimization**: Cannot run expensive LLM inference on every transaction. "Funnel Architecture" where cheap, fast modules filter out 98% of traffic before invoking Expert Agent.
3. **Parallel Development**: Can develop Expert Agent with mocked inputs while building Statistical Engine.

### The Three Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TRANSACTION INPUT                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: STATISTICAL ENGINE (The "Fast Gate")                          │
│  ─────────────────────────────────────────────────────────────────────  │
│  Role: Anomaly detection based on numerical deviation                   │
│  Latency: < 10ms                                                        │
│  Logic:                                                                  │
│    • Log-transformation of amounts (normalize distributions)            │
│    • K-Means/DBSCAN clustering → "Behavioral Peer Groups"               │
│    • Log Z-Score against cluster baseline                               │
│  Output: statistical_anomaly_score (Float 0.0 - 10.0)                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                         score < 3.0? ──→ APPROVE (98% of traffic)
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: NARRATIVE ENGINE (The "Context Layer")                        │
│  ─────────────────────────────────────────────────────────────────────  │
│  Role: Semantic anomaly detection - does tx fit user's story?           │
│  Latency: < 200ms                                                       │
│  Logic:                                                                  │
│    • Embed transaction metadata (amount, format, time, counterparty)    │
│    • Compare tx vector vs user's "History Vector" (rolling average)     │
│    • Cosine similarity scoring                                          │
│  Output: narrative_coherence_score (Float 0.0 - 1.0)                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                      coherence > 0.7? ──→ APPROVE
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: EXPERT AGENT (The "Judge")                                    │
│  ─────────────────────────────────────────────────────────────────────  │
│  Role: Final decision maker and regulatory compliance                   │
│  Latency: ~2-3 seconds (Async)                                          │
│  Trigger: Only if Layer 1 OR Layer 2 exceed thresholds                  │
│  Components:                                                             │
│    • Knowledge Base (RAG): EU/FATF directives, typologies, sanctions    │
│    • LLM Agent: Acts as Compliance Officer                              │
│  Input: Transaction + Statistical Score + Narrative Score               │
│  Tasks:                                                                  │
│    • Synthesize conflicting signals                                     │
│    • Detect typologies (Smurfing, Structuring, Layering)                │
│    • Consult RAG for specific violations                                │
│  Output: JSON verdict (BLOCK/APPROVE) + confidence + SAR draft          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Configurable Thresholds
```python
THRESHOLDS = {
    "statistical_gate": 3.0,      # Tune based on FP rate
    "narrative_gate": 0.7,        # Tune based on recall
    "expert_confidence": 0.8,     # Minimum confidence to BLOCK
}
```

---

## Target Project Structure

```
/Users/asaferez/Projects/aml/
├── engines/
│   ├── __init__.py
│   ├── statistical/              # Layer 1: The Fast Gate
│   │   ├── __init__.py
│   │   ├── clustering.py         # K-Means/DBSCAN peer groups
│   │   ├── zscore.py             # Log Z-Score calculator
│   │   └── engine.py             # StatisticalEngine class
│   ├── narrative/                # Layer 2: The Context Layer
│   │   ├── __init__.py
│   │   ├── embeddings.py         # Transaction vectorization
│   │   ├── coherence.py          # Cosine similarity scorer
│   │   └── engine.py             # NarrativeEngine class
│   └── expert/                   # Layer 3: The Judge
│       ├── __init__.py
│       ├── agent.py              # ExpertAgent class (LLM)
│       ├── rag.py                # Vector search interface
│       ├── typologies.py         # Typology detection logic
│       └── sar.py                # SAR draft generator
├── shared/
│   ├── __init__.py
│   ├── db.py                     # MongoDB connection pool
│   ├── config.py                 # All configuration & thresholds
│   ├── models.py                 # Pydantic schemas
│   └── clients.py                # OpenAI/Anthropic clients
├── orchestrator/
│   ├── __init__.py
│   └── pipeline.py               # Transaction routing through layers
├── scripts/                      # Legacy/utility scripts
│   ├── aml_ingest.py             # Data ingestion
│   ├── vector_ingest.py          # PDF to vector pipeline
│   └── profile_generator.py      # Profile generation
├── tests/
│   ├── __init__.py
│   ├── test_statistical.py
│   ├── test_narrative.py
│   ├── test_expert.py
│   └── test_pipeline.py
├── api/                          # Express.js API (existing)
├── documents/                    # Regulatory PDFs
├── .claude/
│   └── agents/
│       └── aml-expert.md
├── requirements.txt
├── pytest.ini
└── CLAUDE.md
```

---

## Implementation Roadmap

### Phase 0: Foundation
**Goal**: Initialize version control and package structure

| Task | Description | Status |
|------|-------------|--------|
| 0.1 | Initialize git repository | Pending |
| 0.2 | Create directory structure (engines/, shared/, orchestrator/, tests/) | Pending |
| 0.3 | Create requirements.txt with pinned dependencies | Pending |
| 0.4 | Move existing scripts to scripts/ directory | Pending |

### Phase A: Expert Agent (The "Judge")
**Goal**: Build Layer 3 first - can work with mocked inputs

| Task | Description | Status |
|------|-------------|--------|
| A.1 | Define `TribunalInput` and `TribunalVerdict` Pydantic schemas | Pending |
| A.2 | Refactor `aml_expert.py` → `engines/expert/agent.py` | Pending |
| A.3 | Implement typology detection (Smurfing, Structuring, Layering, TBML) | Pending |
| A.4 | Add SAR draft generation capability | Pending |
| A.5 | Create mock test suite with injected scores | Pending |

**Mock Test Example**:
```python
# Test: High anomaly + low coherence → Should detect Structuring
mock_input = TribunalInput(
    transaction={"amount": 4900, "format": "Wire", ...},
    statistical_score=9.2,   # High anomaly
    narrative_score=0.15,    # Low coherence
)
verdict = expert_agent.analyze(mock_input)
assert verdict.typology == "Structuring"
assert "FATF Recommendation 20" in verdict.citations
```

### Phase B: Statistical Engine (The "Fast Gate")
**Goal**: Build Layer 1 - achieve <10ms latency, filter 98% of traffic

| Task | Description | Status |
|------|-------------|--------|
| B.1 | Create `shared/db.py` with connection pooling | Pending |
| B.2 | Build clustering pipeline on 5M transactions | Pending |
| B.3 | Implement log-transformed Z-score calculator | Pending |
| B.4 | Backtest against `is_laundering` labels, generate ROC/AUC | Pending |

**Clustering Features** (for anonymous data):
- `log(avg_transaction_amount)`
- `transaction_frequency` (txns per day)
- `unique_counterparty_count`
- `payment_format_entropy`
- `hour_of_day_distribution`

### Phase C: Narrative Engine (The "Context Layer")
**Goal**: Build Layer 2 - semantic coherence scoring

| Task | Description | Status |
|------|-------------|--------|
| C.1 | Design transaction embedding strategy | Pending |
| C.2 | Build user history vector (rolling average of N transactions) | Pending |
| C.3 | Implement cosine similarity coherence scorer | Pending |
| C.4 | Integrate `narrative_prediction_experiment.py` logic | Pending |

**Embedding Strategy**:
```python
tx_features = {
    "log_amount": log(amount),
    "payment_format": one_hot(format),  # 5 dims
    "hour_bucket": hour // 4,           # 6 buckets
    "counterparty_cluster": cluster_id,
    "day_of_week": dow,
}
# → 256-dim embedding via small encoder
```

### Phase D: Orchestration
**Goal**: Connect the pipes, backtest full system

| Task | Description | Status |
|------|-------------|--------|
| D.1 | Create `orchestrator/pipeline.py` with threshold routing | Pending |
| D.2 | Add configurable thresholds via `shared/config.py` | Pending |
| D.3 | Backtest full system on 500K test transactions | Pending |
| D.4 | Compare metrics vs CNA v1 baseline | Pending |
| D.5 | Tune thresholds to optimize precision/recall tradeoff | Pending |

---

## Performance Targets

| Metric | CNA v1 (Current) | Three-Layer (Target) |
|--------|------------------|----------------------|
| Precision | 2.6% | >15% |
| Recall | 50% | >70% |
| F1 Score | 4.9% | >25% |
| Latency (p50) | ~2s | <50ms |
| Latency (p99) | ~5s | <3s |
| LLM Cost | High (all txns) | Low (2% of txns) |

---

## Data Schemas

### TribunalInput (Input to Expert Agent)
```python
class TribunalInput(BaseModel):
    transaction: Transaction
    statistical_score: float        # 0.0 - 10.0
    narrative_score: float          # 0.0 - 1.0
    account_history: AccountHistory
    triggered_by: Literal["statistical", "narrative", "both"]
```

### TribunalVerdict (Output from Expert Agent)
```python
class TribunalVerdict(BaseModel):
    decision: Literal["BLOCK", "APPROVE", "REVIEW"]
    confidence: float               # 0.0 - 1.0
    typology: Optional[str]         # "Smurfing", "Structuring", etc.
    risk_factors: List[str]
    citations: List[str]            # Regulatory references
    sar_draft: Optional[SARDraft]
    reasoning: str
```

### Money Laundering Typologies to Detect
| Typology | Pattern | Statistical Signal | Narrative Signal |
|----------|---------|-------------------|------------------|
| Smurfing | Many small deposits | High frequency, low amounts | Many new counterparties |
| Structuring | Just-below-threshold | Amounts cluster near $10K | Repetitive patterns |
| Layering | Rapid in/out | High velocity | Circular flows |
| TBML | Trade mispricing | Unusual amounts for goods | Mismatched counterparties |
| Shell Company | Passthrough | In ≈ Out | No business activity |

---

## Database Configuration

### MongoDB Atlas
- **URI**: `mongodb+srv://dev_db_user:EyMpA37VXGa3Kjmc@aml-research.sgpnzv8.mongodb.net/?appName=AML-Research`
- **Database**: `aml_db`

### Collections
| Collection | Documents | Description |
|------------|-----------|-------------|
| `transactions` | 5,078,345 | IBM AML HI-Small dataset |
| `accounts` | 515,537 | Extracted account entities |
| `banks` | 30,000+ | Bank entities |
| `regulatory_docs` | 3,888 chunks | Vector embeddings for RAG |
| `cluster_baselines` | TBD | Pre-computed cluster statistics |
| `account_embeddings` | TBD | User history vectors |

### Transaction Schema
```javascript
{
  "sender": { "account_id": "8000F4580", "bank_id": "3208" },
  "receiver": { "account_id": "8000F5340", "bank_id": "1" },
  "amount": { "sent": 1000.00, "received": 1000.00, "currency_sent": "US Dollar" },
  "payment_format": "Cheque",
  "timestamp": ISODate("2022-09-01T00:20:00Z"),
  "is_laundering": false  // Ground truth label
}
```

---

## API Keys Required
```bash
export OPENAI_API_KEY='...'      # For embeddings (text-embedding-3-small)
export ANTHROPIC_API_KEY='...'   # For Claude reasoning
```

---

## Vector Knowledge Base

### Sources (3,888 chunks)
| Source | Chunks | Content |
|--------|--------|---------|
| FATF | 1,674 | 40 Recommendations, Methodology, RBA Guidance |
| FATF Typologies | 360 | TBML, Shell Companies, Virtual Assets |
| EU | 670 | AMLR, AMLD5, AMLD6, AMLA |
| JMLSG | 766 | UK Sector Guidance |
| Enforcement | 225 | FCA, FinCEN enforcement cases |
| Basel/EBA/Wolfsberg | 116 | Banking guidance |

---

## Development Commands

### Run Expert Agent (Interactive)
```bash
python3 -m engines.expert.agent
```

### Run Statistical Engine Backtest
```bash
python3 -m engines.statistical.engine --backtest
```

### Run Full Pipeline Test
```bash
python3 -m orchestrator.pipeline --test-set 500000
```

### Run All Tests
```bash
pytest tests/ -v
```

---

## Testing Results

### CNA v1 (Baseline - Amount Only)
- **Approach**: Amount-based narrative coherence
- **Precision**: 2.6% (too many false positives)
- **Recall**: 50% (caught 1 of 2 laundering)
- **Issue**: Only analyzed amount, missed counterparty/timing/velocity

### Three-Layer Tribunal (Target)
- **Approach**: Statistical + Narrative + Expert fusion
- **Precision Target**: >15%
- **Recall Target**: >70%
- **Key Improvements**: Peer group clustering, semantic embeddings, typology detection

---

## Agents

### aml-expert
Location: `.claude/agents/aml-expert.md`
Purpose: RAG-powered AML/CFT compliance expert
Usage: Ask questions about regulations, typologies, enforcement cases
