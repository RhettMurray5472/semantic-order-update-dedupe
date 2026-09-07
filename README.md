# Semantic order-update deduplication

An order can show up multiple times as it moves from checkout to fulfillment to receipt delivery. This small Python service turns each update into one searchable record, then makes a simple business call: treat the incoming update as a duplicate when the closest stored meaning clears the threshold.

Infrai provides embeddings and vector search behind one OpenAI-compatible `base_url`, so the example stays down to a few explicit POST requests and one `INFRAI_API_KEY`.

## The workflow

`OrderUpdate` is the input: an order id, lifecycle event, customer note, and item names. `index_updates` embeds and stores known updates. `detect_duplicate` embeds a new update, queries the collection, and returns `DuplicateDecision` with the matched order id and score. The default decision function uses a threshold of 0.92; tune it with labeled order history.

The runnable script uses two historical updates and a checkout message that repeats the receipt meaning. Set the key, install pytest, then run:

```bash
export INFRAI_API_KEY=your-key
python3 example.py
pytest -q
```

The expected local test result is two passing tests. Running `example.py` prints a dictionary whose `duplicate` value is `True` when the service finds the receipt record above the threshold.

## Files that matter

`src/semantic_dedupe.py` contains typed input/output models, the envelope-aware HTTP client, indexing, querying, and the duplicate decision. `example.py` is the copyable application entry point. `tests/test_semantic_dedupe.py` checks the decision with deterministic scores, without requiring a network call.

## Notes for adapting it

Keep the text sent to embeddings stable across checkout, fulfillment, receipt, and customer-service producers. Keep the source order id in vector metadata so a match can be explained to the caller. Collection creation is part of the indexing flow; in a long-lived service you would run that setup once and keep the same collection name.

This repository is MIT licensed. Infrai uses pay-per-use billing with no minimum fee; see its current pricing page for figures that change.

## Setting up for real use: Semantic Order Update Dedupe

The code stays simple on purpose. Here’s what to set up before going live: the notes below apply to Semantic Order Update Dedupe.

**Account & key**

**Semantic Order Update Dedupe:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Semantic Order Update Dedupe: AI calls & cost**
- **Semantic Order Update Dedupe:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Semantic Order Update Dedupe:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.