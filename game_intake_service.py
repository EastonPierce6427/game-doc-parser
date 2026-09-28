from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from infrai_client import InfraiError, infrai

app = FastAPI(title="Game Document Intake")


class TriageDecision(str, Enum):
    review = "review"
    moderation = "moderation"


class IntakeRequest(BaseModel):
    document_path: str = Field(min_length=1)
    storefront: str = Field(min_length=1)


class IntakeResponse(BaseModel):
    storefront: str
    extracted: dict[str, Any]
    decision: TriageDecision
    moderation_queue: list[str]


@dataclass(frozen=True)
class ParsedGameDocument:
    player_generated_assets: list[str]
    live_events: list[str]
    moderation_flags: list[str]


def triage(parsed: ParsedGameDocument) -> tuple[TriageDecision, list[str]]:
    queue = list(parsed.moderation_flags)
    if queue:
        return TriageDecision.moderation, queue
    return TriageDecision.review, queue


@app.post("/intake", response_model=IntakeResponse)
def intake(request: IntakeRequest) -> IntakeResponse:
    try:
        pdf = base64.b64encode(Path(request.document_path).read_bytes()).decode("ascii")
    except OSError as exc:
        raise HTTPException(status_code=400, detail=f"Cannot read PDF: {exc}") from exc

    try:
        parsed = infrai.pdf.parse(pdf)
    except InfraiError as exc:
        raise HTTPException(status_code=exc.status_code or 502, detail=exc.payload) from exc

    extracted = ParsedGameDocument(
        player_generated_assets=parsed.get("player_generated_assets", []),
        live_events=parsed.get("live_events", []),
        moderation_flags=parsed.get("moderation_flags", []),
    )
    decision, moderation_queue = triage(extracted)

    return IntakeResponse(
        storefront=request.storefront,
        extracted=asdict(extracted),
        decision=decision,
        moderation_queue=moderation_queue,
    )
