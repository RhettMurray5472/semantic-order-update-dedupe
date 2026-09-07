from semantic_dedupe import InfraiClient, OrderUpdate, detect_duplicate, index_updates


def main() -> None:
    client = InfraiClient()
    collection = "order-updates-demo"
    history = [
        OrderUpdate("ord-1042", "receipt", "Paid for two blue mugs", ("blue mug", "blue mug")),
        OrderUpdate("ord-1043", "fulfillment", "Packed and handed to carrier", ("linen apron",)),
    ]
    index_updates(client, collection, history)
    incoming = OrderUpdate("ord-1042-copy", "checkout", "Payment received for two blue mugs", ("blue mug", "blue mug"))
    decision = detect_duplicate(client, collection, incoming)
    print({"duplicate": decision.duplicate, "matched_order_id": decision.matched_order_id, "score": decision.score})


if __name__ == "__main__":
    main()
