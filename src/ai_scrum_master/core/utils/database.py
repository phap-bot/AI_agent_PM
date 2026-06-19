from __future__ import annotations

import logging
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from ai_scrum_master.core.config.settings import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    _client: MongoClient | None = None
    _db: Database | None = None

    @classmethod
    def get_client(cls) -> MongoClient:
        if cls._client is None:
            settings = get_settings()
            logger.info("Connecting to MongoDB at %s", settings.mongodb_uri)
            cls._client = MongoClient(settings.mongodb_uri)
            cls._db = cls._client[settings.mongodb_db_name]
            
            # Ensure collections and indexes
            cls._ensure_indexes()
            
        return cls._client

    @classmethod
    def get_db(cls) -> Database:
        cls.get_client()
        return cls._db

    @classmethod
    def get_history_collection(cls) -> Collection:
        return cls.get_db()["history"]

    @classmethod
    def get_projects_collection(cls) -> Collection:
        return cls.get_db()["projects"]

    @classmethod
    def _ensure_indexes(cls) -> None:
        try:
            history = cls.get_history_collection()
            history.create_index([("created_at", -1)])
            history.create_index("jira_key")
            
            projects = cls.get_projects_collection()
            projects.create_index("name", unique=True)
        except Exception as e:
            logger.warning("Failed to create MongoDB indexes: %s", e)

    @classmethod
    def get_project(cls, project_id: str) -> dict | None:
        from bson.objectid import ObjectId
        try:
            return cls.get_projects_collection().find_one({"_id": ObjectId(project_id)})
        except Exception:
            return None

    @classmethod
    def get_all_projects(cls) -> list[dict]:
        cursor = cls.get_projects_collection().find().sort("created_at", -1)
        return list(cursor)

    @classmethod
    def create_project(cls, project_data: dict) -> str | None:
        try:
            from datetime import datetime, UTC
            project_data["created_at"] = datetime.now(UTC).isoformat()
            res = cls.get_projects_collection().insert_one(project_data)
            return str(res.inserted_id)
        except Exception as e:
            logger.error("Failed to create project: %s", e)
            return None

    @classmethod
    def update_project(cls, project_id: str, updates: dict) -> bool:
        from bson.objectid import ObjectId
        try:
            from datetime import datetime, UTC
            updates["updated_at"] = datetime.now(UTC).isoformat()
            res = cls.get_projects_collection().update_one(
                {"_id": ObjectId(project_id)},
                {"$set": updates}
            )
            return res.modified_count > 0
        except Exception as e:
            logger.error("Failed to update project: %s", e)
            return False

    @classmethod
    def delete_project(cls, project_id: str) -> bool:
        from bson.objectid import ObjectId
        try:
            res = cls.get_projects_collection().delete_one({"_id": ObjectId(project_id)})
            return res.deleted_count > 0
        except Exception as e:
            logger.error("Failed to delete project: %s", e)
            return False

    @classmethod
    def save_history(cls, requirement: str, result: dict, project_id: str | None = None) -> str | None:
        """Save a generated story and requirement to history."""
        try:
            from datetime import datetime, UTC
            
            # Extract story and jira key if available
            story = result.get("story") or {}
            actions = result.get("actions") or {}
            jira_action = actions.get("jira") or {}
            created = jira_action.get("created") or {}
            jira_key = created.get("story_key") or ""
            
            doc = {
                "requirement": requirement,
                "story": story,
                "jira_key": jira_key,
                "result": result,  # Store the full result for analysis
                "project_id": project_id,
                "created_at": datetime.now(UTC).isoformat()
            }
            res = cls.get_history_collection().insert_one(doc)
            logger.info("Saved requirement history to MongoDB id=%s", res.inserted_id)
            return str(res.inserted_id)
        except Exception as e:
            logger.error("Failed to save history to MongoDB: %s", e)
            return None

    @classmethod
    def get_history(cls, project_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch history sorted by creation date."""
        try:
            query = {}
            if project_id:
                query["project_id"] = project_id
            cursor = cls.get_history_collection().find(query).sort("created_at", -1).limit(limit)
            results = []
            for doc in cursor:
                doc["id"] = str(doc.pop("_id"))
                results.append(doc)
            return results
        except Exception as e:
            logger.error("Failed to fetch history from MongoDB: %s", e)
            return []

    @classmethod
    def delete_history(cls, history_id: str) -> bool:
        """Delete a history record by ID."""
        from bson.objectid import ObjectId
        try:
            res = cls.get_history_collection().delete_one({"_id": ObjectId(history_id)})
            return res.deleted_count > 0
        except Exception as e:
            logger.error("Failed to delete history from MongoDB: %s", e)
            return False
