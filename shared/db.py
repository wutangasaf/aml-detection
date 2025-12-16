"""
MongoDB Connection Pool for AML Three-Layer Tribunal

Provides a singleton connection manager used across all engines.
"""

import certifi
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from shared.config import MONGODB_URI, DATABASE_NAME, COLLECTIONS


class MongoDBConnection:
    """
    Singleton MongoDB connection manager.

    Usage:
        db = MongoDBConnection()
        transactions = db.transactions
        accounts = db.accounts
    """

    _instance: Optional["MongoDBConnection"] = None
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None

    def __new__(cls) -> "MongoDBConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._connect()

    def _connect(self) -> None:
        """Establish connection to MongoDB Atlas."""
        self._client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=30000,
            tlsCAFile=certifi.where(),  # Required for macOS SSL
            maxPoolSize=50,
            minPoolSize=10,
        )
        self._database = self._client[DATABASE_NAME]

        # Verify connection
        self._client.admin.command("ping")

    @property
    def client(self) -> MongoClient:
        """Get the MongoClient instance."""
        return self._client

    @property
    def database(self) -> Database:
        """Get the database instance."""
        return self._database

    # ==========================================================================
    # COLLECTION ACCESSORS
    # ==========================================================================

    @property
    def transactions(self) -> Collection:
        """Get the transactions collection (5M+ docs)."""
        return self._database[COLLECTIONS["transactions"]]

    @property
    def accounts(self) -> Collection:
        """Get the accounts collection (515K+ docs)."""
        return self._database[COLLECTIONS["accounts"]]

    @property
    def banks(self) -> Collection:
        """Get the banks collection (30K+ docs)."""
        return self._database[COLLECTIONS["banks"]]

    @property
    def regulatory_docs(self) -> Collection:
        """Get the regulatory_docs collection (vector embeddings)."""
        return self._database[COLLECTIONS["regulatory_docs"]]

    @property
    def cluster_baselines(self) -> Collection:
        """Get the cluster_baselines collection (for Statistical Engine)."""
        return self._database[COLLECTIONS["cluster_baselines"]]

    @property
    def account_embeddings(self) -> Collection:
        """Get the account_embeddings collection (for Narrative Engine)."""
        return self._database[COLLECTIONS["account_embeddings"]]

    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================

    def get_collection(self, name: str) -> Collection:
        """Get a collection by name."""
        return self._database[name]

    def close(self) -> None:
        """Close the connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            MongoDBConnection._instance = None

    def ping(self) -> bool:
        """Check if connection is alive."""
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_db() -> MongoDBConnection:
    """Get the singleton database connection."""
    return MongoDBConnection()


def get_transactions() -> Collection:
    """Get the transactions collection."""
    return get_db().transactions


def get_accounts() -> Collection:
    """Get the accounts collection."""
    return get_db().accounts


def get_regulatory_docs() -> Collection:
    """Get the regulatory_docs collection."""
    return get_db().regulatory_docs
