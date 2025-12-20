# WIN ASAP Playbook (Dec 19, 2025)
**Target:** BarSecurityTracker → revenue fast via *POS anomaly → instant video evidence*  
**Core thesis:** *Distribution + evidence workflow + ops* beats “perfect vision” early.

---

## 0) Reality check on the “2025 stack” (so you don’t build on shaky assumptions)
- **TensorFlow is still 2.x**, with **TF 2.20** and major on-device work moving from `tf.lite` to **LiteRT**.
- **LangChain v1** is a production-focused “agents foundation” (with a `createAgent` path + standardized content blocks).
- **MCP (Model Context Protocol)** matured in 2025 with security-oriented OAuth guidance and **task-based workflows** (great for long-running agent jobs).
- **Modern coding velocity** is increasingly “multi-agent in-editor” (e.g., Cursor 2.0 parallel agents using isolated worktrees).

---

## 1) The fastest wealth path with your product
### Your sellable MVP (what bars actually pay for)
**“Find the right video around suspicious POS activity fast enough to recover cash + stop repeats.”**

**MVP Loop**
1. POS events → 2. anomaly triggers → 3. clip/bookmark → 4. manager labels outcome → 5. dataset builds → 6. precision improves.

### Why this wins ASAP
- POS anomalies give you **high-precision candidate windows** (cheap compute).
- Evidence workflow creates **trust** (owners don’t buy “AI said theft”).
- Labels create **moat** (your dataset becomes proprietary over time).

---

## 2) Tool leverage map (new tools you should use immediately)

### A) Build speed (engineering)
- **Cursor 2.0 multi-agents**: run up to 8 agents in parallel using isolated worktrees—ideal for “ship 5 services + UI in a week.”
- **AGENTS.md** standard: put your project rules + commands in a predictable file so any coding agent stays aligned.
- **CodeQL** (or equivalent) for fast “is this insecure?” scanning on PRs.

### B) Agent runtime (product)
Pick **one** “agent framework” and go deep:
- **PydanticAI** if you want strongly typed outputs + production ergonomics (my default for this stack).
- **LangChain v1 / LangGraph** if you want a broad ecosystem + graph-style orchestration.

### C) Tool connectivity (product + ops)
- **MCP** is the interoperability layer for “agents that can safely call tools,” especially when you’ll connect POS, CRM, notifications, storage, etc.

---

## 3) Minimal architecture that ships + scales
**Event-driven microservices** (start with Docker Compose, later move to serverless/K8s).

### Services
1. **pos_ingestor** (FastAPI): receives POS webhooks / polling → normalizes events
2. **anomaly_worker**: rules + baselines → creates “incident candidates”
3. **clipper**: maps incident timestamp → recorded video window → returns clip URL
4. **incident_agent**: generates a structured incident report (LLM/VLM optional)
5. **dashboard** (React): list incidents → 1-click playback → label outcome

### Storage
- Postgres for events/incidents/labels
- Object storage for clips (S3/MinIO) OR DVR-style HLS segment retention on disk

---

## 4) Integrated code (drop-in starter)
> This is designed to be **directly runnable** with small edits (secrets + storage + your POS event format).

### 4.1 Common schemas (Pydantic)
```python
# services/common/schemas.py
from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

class PosEvent(BaseModel):
    provider: Literal["toast", "square", "clover", "other"] = "other"
    location_id: str
    terminal_id: Optional[str] = None
    employee_id: Optional[str] = None
    event_type: str  # e.g. "void", "refund", "no_sale", "discount"
    amount: float = 0.0
    created_at: datetime
    raw: dict = Field(default_factory=dict)  # store original payload for audit/debug

class Incident(BaseModel):
    incident_id: str
    location_id: str
    severity: int = Field(ge=1, le=10)
    reason: str
    event: PosEvent
    camera_id: str
    window_start: datetime
    window_end: datetime

class IncidentLabel(BaseModel):
    incident_id: str
    label: Literal["confirmed_loss", "not_an_issue", "training_needed", "unclear"]
    notes: Optional[str] = None
    labeled_by: str
    labeled_at: datetime
```

### 4.2 POS ingestion API (FastAPI + HMAC signature verification)
```python
# services/pos_ingestor/main.py
from __future__ import annotations
import hmac
import hashlib
import json
import os
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException, Request
from services.common.schemas import PosEvent

APP_SHARED_SECRET = os.getenv("POS_WEBHOOK_SECRET", "")
if not APP_SHARED_SECRET:
    # In production you should fail hard; here we allow local dev.
    print("WARNING: POS_WEBHOOK_SECRET is not set. Signature checks will fail-open in dev.")

app = FastAPI(title="POS Ingestor")

def verify_hmac(body: bytes, signature_hex: str | None) -> bool:
    if not APP_SHARED_SECRET:
        return True  # dev fallback
    if not signature_hex:
        return False
    mac = hmac.new(APP_SHARED_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature_hex)

@app.post("/webhooks/pos")
async def pos_webhook(
    request: Request,
    x_signature_sha256: str | None = Header(default=None, alias="X-Signature-SHA256"),
):
    body = await request.body()
    if not verify_hmac(body, x_signature_sha256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    # Normalize: adapt this mapping to your provider(s)
    try:
        evt = PosEvent(
            provider=payload.get("provider", "other"),
            location_id=str(payload["location_id"]),
            terminal_id=payload.get("terminal_id"),
            employee_id=payload.get("employee_id"),
            event_type=str(payload["event_type"]),
            amount=float(payload.get("amount", 0.0)),
            created_at=datetime.fromisoformat(payload["created_at"]).astimezone(timezone.utc),
            raw=payload,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Schema validation failed: {e}")

    # TODO: write to Postgres + publish to Redis stream/Kafka
    # For now: return normalized event so you can test quickly.
    return {"ok": True, "event": evt.model_dump()}
```

### 4.3 Incident report agent (PydanticAI: typed output + tools)
```python
# services/incident_agent/agent.py
from __future__ import annotations
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from services.common.schemas import Incident

@dataclass
class AgentDeps:
    # You can pass DB connections, storage clients, etc.
    org_name: str = "BarSecurityTracker"

class IncidentReport(BaseModel):
    title: str = Field(description="One-line incident title.")
    summary: str = Field(description="2-4 sentence plain-English summary for managers.")
    likely_issue: str = Field(description="e.g. 'Void abuse', 'Refund abuse', 'No-sale drawer opens', 'Unknown'")
    recommended_action: str = Field(description="Actionable next step: coach, review, policy change, etc.")
    confidence: float = Field(ge=0.0, le=1.0)

incident_agent = Agent(
    # Swap model provider via env if you want (OpenAI/Anthropic/etc).
    # PydanticAI supports many providers; keep it configurable.
    model=os.getenv("INCIDENT_AGENT_MODEL", "openai:gpt-5"),
    deps_type=AgentDeps,
    output_type=IncidentReport,
    instructions=(
        "You are a loss-prevention assistant. "
        "Write like a practical operator: short, neutral, evidence-focused. "
        "Never accuse; describe what is observable and what to verify."
    ),
)

@incident_agent.tool
async def get_clip_url(ctx: RunContext[AgentDeps], incident_id: str) -> str:
    # TODO: lookup clip URL in DB/storage; return signed URL
    return f"https://example.invalid/clips/{incident_id}.mp4"

async def generate_report(incident: Incident) -> IncidentReport:
    deps = AgentDeps()
    prompt = (
        "Create a manager-ready incident report.\n\n"
        f"Incident JSON:\n{incident.model_dump_json(indent=2)}\n\n"
        "Return a concise report."
    )
    result = await incident_agent.run(prompt, deps=deps)
    return result.output
```

### 4.4 Docker Compose (local MVP)
```yaml
# docker-compose.yml
services:
  pos_ingestor:
    build: ./services/pos_ingestor
    environment:
      - POS_WEBHOOK_SECRET=${POS_WEBHOOK_SECRET}
    ports: ["8000:8000"]

  # Add redis/postgres + workers as you wire persistence.
  # redis:
  # postgres:
```

---

## 5) The “WIN ASAP” execution plan (30 days)
### Days 1–7 (Initialization)
- Ship POS ingest → normalized schema → basic anomaly rules (void/refund/no-sale)
- Build dashboard: incident list + “play clip” placeholder + label buttons
- Start pilots with *manual clip links* if needed (speed > perfection)

### Days 8–30 (Scaling)
- Add recorded video retention (last 7–30 days) + clipper service
- Add incident agent reports + daily digest
- Add role-based access + retention defaults
- Write 1 case study per pilot location

### Day 30+ (Autonomy, carefully)
- Auto-route incidents to manager
- Auto-suggest policy changes (“discount threshold”, “refund approval required”)
- Expand POS providers and installer/channel partnerships

---

## 6) Wealth mechanics (realistic, high-leverage)
**Pricing anchor:** $199–$499 / month / location (based on cameras + retention)  
**Upsells:** additional cameras, longer retention, installer bundle, multi-location dashboard

**Distribution that compounds:**
- POS resellers / camera installers (they already have trust + access)
- “Proof-first” sales: show 3 verified incidents in week 1
- Convert with ROI: “prevented loss” ≥ fee

---

## 7) Red Team audit (so you don’t get wrecked)
- **Webhook forgery / replay**: require HMAC signatures + idempotency keys + timestamp windows
- **Clip privacy**: signed URLs, role-based access, view audit logs
- **Prompt injection**: never pass arbitrary staff notes/raw text to agents without sanitization
- **MCP risks**: treat tool tokens as critical secrets; restrict tool permissions; implement approval gates for sensitive actions

---

## 8) Paste repo URLs for a surgical integration
If you paste the **exact GitHub URLs** for:
- `princeleuel-code/BarSecurityTracker`
- `princeleuel-code/bar-shield-empire`

…I can produce a **concrete merge plan** (file-by-file diffs + exact insertion points) that matches your current stack.
