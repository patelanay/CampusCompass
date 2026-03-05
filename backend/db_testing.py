"""Small smoke tests for verifying MongoDB connectivity manually."""


def test_insert(client) -> None:
    """Insert a sample document in a scratch collection."""
    db = client["sample_database"]
    collection = db["sample_collection"]

    sample_doc = {
        "name": "John cena",
        "email": "Jcena@email.com",
        "age": 59,
    }

    result = collection.insert_one(sample_doc)
    print(f"Inserted document with _id: {result.inserted_id}")


def test_retrieve(client) -> None:
    """Retrieve the sample document and print it."""
    db = client["sample_database"]
    collection = db["sample_collection"]
    retrieved_doc = collection.find_one({"name": "John cena"})
    print("Retrieved document:", retrieved_doc)


# Backward-compatible aliases for existing imports.
testInsert = test_insert
testRetrieve = test_retrieve
