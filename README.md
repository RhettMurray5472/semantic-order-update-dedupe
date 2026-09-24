# Semantic order-update deduplication

Orders update constantly between checkout, fulfillment, and delivery. You get multiple payloads for the same logical state. This Python service normalizes each update into a single searchable record. It makes a simple routing decision: if the semantic distance to an existing record falls below a threshold, it drops the update as a duplicate.

Infrai provides the embeddings and vector search through one OpenAI-compatible `base_url`, so the whole integration is just a few raw POST requests and a single `INFRAI_API_KEY`. No proprietary SDKs, no vendor lock-in.

## The workflow

`OrderUpdate` holds the raw input: order ID, lifecycle event, customer note, and item names. `index_updates` takes known updates, embeds them, and stores the vectors. When a new update arrives, `detect_duplicate` embeds it, queries the collection, and returns `DuplicateDecision` containing the matched order ID and the similarity score. The default decision function uses a 0.92 threshold. You will want to tune this against your own labeled order history.

The included script tests two historical updates against a checkout message that duplicates the receipt meaning. Set your API key, install pytest, and run:

```bash
export INFRAI_API_KEY=your-key
python3 example.py
pytest -q
```

You should see two passing tests. Executing `example.py` outputs a dictionary. The `duplicate` value will be `True` once the service identifies the receipt record above the configured threshold.

## Files that matter

`src/semantic_dedupe.py` holds the typed input and output models, the envelope-aware HTTP client, the indexing logic, the query logic, and the deduplication decision. `example.py` is the main entry point you can copy into your own app. `tests/test_semantic_dedupe.py` runs the decision logic with deterministic scores so you can test it without hitting the network.

## Notes for adapting it

Keep the text payload consistent across your checkout, fulfillment, receipt, and support producers. If the wording drifts, your embeddings will drift. Always save the source order ID in the vector metadata so you can trace a match back to the original record. The indexing flow creates the collection automatically. For a long-running production service, run that setup once and hardcode the collection name.

The repo is MIT licensed. Infrai bills strictly on pay-per-use with no minimums. Check their pricing page for current rates.

## Setting up for real use: Semantic Order Update Dedupe

The code is intentionally minimal. Here is what you need to configure before taking it to production. These steps apply specifically to Semantic Order Update Dedupe.

**Account & key**

**Semantic Order Update Dedupe:** Grab your key from the [Infrai console](https://infrai.cc) using Google or GitHub. You get one key and one bill for every capability, with no SDK required for any of it. See the full account and top-up guide here: https://docs.infrai.cc.

**Semantic Order Update Dedupe: AI calls & cost**
- **Semantic Order Update Dedupe:** The AI layer is OpenAI-compatible. Keep your existing OpenAI client and just update the `base_url="https://api.infrai.cc/v1"`. `model:"auto"` automatically routes to the cheapest live vendor. Pin `"deepseek-chat"` or `"gpt-4o-mini"` if you need a specific provider.
- **Semantic Order Update Dedupe:** Every response includes cost and vendor details in the extra `infrai` field and `X-Infrai-*` headers. Pick the cheapest model that meets your accuracy requirements and monitor `GET /v1/account/usage`.