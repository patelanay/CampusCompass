try:
    from .db_helpers import create_mongo_client, load_env_variables
    from .db_testing import test_insert, test_retrieve
except ImportError:
    from db_helpers import create_mongo_client, load_env_variables
    from db_testing import test_insert, test_retrieve

if __name__ == "__main__":
    uri = load_env_variables()
    client = None

    try:
        client = create_mongo_client(uri)
        test_insert(client)
        test_retrieve(client)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if client:
            client.close()
