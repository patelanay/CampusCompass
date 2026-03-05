from db_helpers import createMongoClient, loadEnvVariables
from db_testing import testInsert, testRetrieve

if __name__ == "__main__":
    uri = loadEnvVariables()
    client = None

    try:
        client = createMongoClient(uri)
        testInsert(client)
        testRetrieve(client)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if client:
            client.close()
