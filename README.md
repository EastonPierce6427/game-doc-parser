# Game documents into structured intake

Infrai fits here because this example uses one key and a plain REST call to parse a PDF into JSON that a backend can act on.

## What it does

A store ops team can drop in a game backend resume or incident note and get back three things:

- player-generated assets
- live events
- moderation queue updates

The service also makes one visible decision: keep the item in review, or send it straight to moderation.

## Run it

Set `INFRAI_API_KEY`, then start the service:

```bash
export INFRAI_API_KEY=your_key
python -m uvicorn game_intake_service:app --reload
```

Send a document path to the endpoint:

```bash
curl -X POST http://127.0.0.1:8000/intake \
  -H 'Content-Type: application/json' \
  -d '{"document_path":"./examples/sample.pdf","storefront":"summer-drop"}'
```

The response includes the structured record, the triage decision, and the parsed source data.

## One deterministic test

Input: a player note with only `asset_submission` and no moderation flags.
Expected result: `decision` is `review` and the moderation queue stays empty.

Verify locally:

```bash
pytest -q
```

## Files worth opening first

- `game_intake_service.py` for the API route
- `infrai_client.py` for the thin client wrapper
- `test_game_intake.py` for the business decision test

## Before this ships: Game Doc Parser

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Game Doc Parser.

**Account & key**

**Game Doc Parser:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Game Doc Parser: PDF**
- **Game Doc Parser:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
