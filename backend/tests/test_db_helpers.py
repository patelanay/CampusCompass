import os
import unittest
from unittest.mock import patch

from backend import db_helpers


class DBHelpersTests(unittest.TestCase):
    def test_load_env_variables_returns_mongodb_uri(self):
        with patch.object(db_helpers, "load_dotenv") as mocked_load_dotenv:
            with patch.dict(os.environ, {"MONGODB_URI": "mongodb://example"}, clear=False):
                uri = db_helpers.load_env_variables()

        mocked_load_dotenv.assert_called_once()
        self.assertEqual(uri, "mongodb://example")

    def test_create_mongo_client_raises_for_missing_uri(self):
        with self.assertRaises(ValueError):
            db_helpers.create_mongo_client("")

    def test_create_mongo_client_successfully_pings(self):
        class FakeAdmin:
            def __init__(self):
                self.pinged = False

            def command(self, name):
                self.pinged = name == "ping"

        class FakeClient:
            def __init__(self, uri, server_api):
                self.uri = uri
                self.server_api = server_api
                self.admin = FakeAdmin()
                self.closed = False

            def close(self):
                self.closed = True

        with patch.object(db_helpers, "MongoClient", FakeClient):
            with patch.object(db_helpers, "ServerApi", lambda version: f"server-api-{version}"):
                client = db_helpers.create_mongo_client("mongodb://unit-test")

        self.assertEqual(client.uri, "mongodb://unit-test")
        self.assertEqual(client.server_api, "server-api-1")
        self.assertTrue(client.admin.pinged)
        self.assertFalse(client.closed)

    def test_create_mongo_client_closes_on_ping_failure(self):
        class FakeAdmin:
            def command(self, _name):
                raise RuntimeError("ping failed")

        class FakeClient:
            def __init__(self, _uri, _server_api):
                self.admin = FakeAdmin()
                self.closed = False

            def close(self):
                self.closed = True

        holder = {}

        def fake_client(uri, server_api):
            client = FakeClient(uri, server_api)
            holder["client"] = client
            return client

        with patch.object(db_helpers, "MongoClient", fake_client):
            with patch.object(db_helpers, "ServerApi", lambda version: version):
                with self.assertRaises(RuntimeError):
                    db_helpers.create_mongo_client("mongodb://unit-test")

        self.assertTrue(holder["client"].closed)

    def test_backward_compatible_aliases_are_available(self):
        self.assertIs(db_helpers.loadEnvVariables, db_helpers.load_env_variables)
        self.assertIs(db_helpers.createMongoClient, db_helpers.create_mongo_client)


if __name__ == "__main__":
    unittest.main()
