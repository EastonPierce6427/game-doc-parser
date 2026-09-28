import base64

from fastapi.testclient import TestClient

from game_intake_service import ParsedGameDocument, TriageDecision, app, triage


def test_triage_keeps_player_asset_only_docs_in_review() -> None:
    parsed = ParsedGameDocument(
        player_generated_assets=["avatar_skin"],
        live_events=["launch_weekend"],
        moderation_flags=[],
    )

    decision, queue = triage(parsed)

    assert decision is TriageDecision.review
    assert queue == []


def test_intake_encodes_local_pdf(tmp_path, monkeypatch) -> None:
    pdf_path = tmp_path / "document.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nexample")
    received = []

    def parse(pdf: str) -> dict:
        received.append(pdf)
        return {}

    monkeypatch.setattr("game_intake_service.infrai.pdf.parse", parse)
    response = TestClient(app).post(
        "/intake", json={"document_path": str(pdf_path), "storefront": "test"}
    )

    assert response.status_code == 200
    assert received == [base64.b64encode(pdf_path.read_bytes()).decode("ascii")]
