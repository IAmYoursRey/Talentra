from typing import Optional, Any
try:
    from pymongo import AsyncMongoClient
    from pymongo.asynchronous.database import AsyncDatabase
except ImportError:
    AsyncMongoClient: Any = object  # type: ignore
    AsyncDatabase: Any = object  # type: ignore
from .config import settings

class MongoManager:
    """
    Manages application-scoped AsyncMongoClient lifecycle using official PyMongo Async API.
    Motor is deprecated and strictly excluded.
    """
    def __init__(self):
        self.client: Optional[AsyncMongoClient] = None
        self.db: Optional[AsyncDatabase] = None

    def connect(self, uri: Optional[str] = None, database_name: Optional[str] = None) -> AsyncDatabase:
        if self.client is None:
            mongo_uri = uri or settings.mongodb_url
            db_name = database_name or settings.mongodb_database
            self.client = AsyncMongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
            )
            self.db = self.client[db_name]
        return self.db

    async def close(self) -> None:
        if self.client is not None:
            await self.client.close()
            self.client = None
            self.db = None

    async def ping(self) -> bool:
        """Pings MongoDB to verify connectivity for readiness probe."""
        if not self.client:
            return False
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False

    async def initialize_indexes(self) -> None:
        """
        Creates mandatory indexes for dynamic portfolio collections:
        - portfolio_items: unique portfolio_id, tenant queries, canonical tags
        - portfolio_revisions: unique revision_id, unique (portfolio_id, version)
        """
        if self.db is None:
            return

        # 1. portfolio_items indexes
        items = self.db["portfolio_items"]
        await items.create_index([("portfolio_id", 1)], unique=True, name="uq_portfolio_id")
        await items.create_index(
            [("school_id", 1), ("student_id", 1), ("created_at", -1)],
            name="ix_portfolio_school_student_created",
        )
        await items.create_index(
            [("school_id", 1), ("status", 1), ("submitted_at", -1)],
            name="ix_portfolio_school_status_submitted",
        )
        await items.create_index(
            [("school_id", 1), ("student_id", 1), ("status", 1)],
            name="ix_portfolio_school_student_status",
        )
        await items.create_index([("canonical_tag_ids", 1)], name="ix_portfolio_canonical_tags")

        # 2. portfolio_revisions indexes
        revisions = self.db["portfolio_revisions"]
        await revisions.create_index([("revision_id", 1)], unique=True, name="uq_revision_id")
        await revisions.create_index(
            [("portfolio_id", 1), ("version", 1)],
            unique=True,
            name="uq_portfolio_version",
        )
        await revisions.create_index(
            [("portfolio_id", 1), ("created_at", -1)],
            name="ix_portfolio_revision_created",
        )

        # 3. evidence_tag_snapshots indexes
        snapshots = self.db["evidence_tag_snapshots"]
        await snapshots.create_index([("validation_decision_id", 1)], unique=True, name="uq_snapshot_decision_id")
        await snapshots.create_index(
            [("school_id", 1), ("student_id", 1), ("approved_at", -1)],
            name="ix_snapshot_school_student_approved",
        )
        await snapshots.create_index(
            [("portfolio_id", 1), ("revision_id", 1)],
            name="ix_snapshot_portfolio_revision",
        )

        # 4. recommendation_snapshots indexes
        rec_snapshots = self.db["recommendation_snapshots"]
        await rec_snapshots.create_index([("snapshot_id", 1)], unique=True, name="uq_rec_snapshot_id")
        await rec_snapshots.create_index(
            [("school_id", 1), ("student_id", 1), ("generated_at", -1)],
            name="ix_rec_snapshot_student_generated",
        )

        # 5. derived_professional_descriptions indexes
        prof_desc = self.db["derived_professional_descriptions"]
        await prof_desc.create_index([("document_id", 1)], unique=True, name="uq_prof_desc_id")
        await prof_desc.create_index(
            [("school_id", 1), ("student_id", 1), ("portfolio_id", 1)],
            name="ix_prof_desc_student_portfolio",
        )

        # 6. cv_content_snapshots indexes
        cv_snapshots = self.db["cv_content_snapshots"]
        await cv_snapshots.create_index([("snapshot_id", 1)], unique=True, name="uq_cv_snapshot_id")
        await cv_snapshots.create_index(
            [("school_id", 1), ("student_id", 1), ("generated_at", -1)],
            name="ix_cv_snapshot_student_generated",
        )
        await cv_snapshots.create_index([("content_digest", 1)], name="ix_cv_snapshot_digest")



mongo_manager = MongoManager()

def get_mongo_db() -> Optional[AsyncDatabase]:
    return mongo_manager.db
