def testInsert(client):
    ###Test insert something
    db = client["sample_database"]
    collection = db["sample_collection"]

    # sample document
    sample_doc = {
        "name": "John cena",
        "email": "Jcena@email.com",
        "age": 59
    }

    # Insert the document
    result = collection.insert_one(sample_doc)
    print(f"Inserted document with _id: {result.inserted_id}")

def testRetrieve(client):
    db = client["sample_database"]
    collection = db["sample_collection"]

    # Retrieve the document by a field (e.g., name)
    retrieved_doc = collection.find_one({"name": "John cena"})
    print("Retrieved document:", retrieved_doc)