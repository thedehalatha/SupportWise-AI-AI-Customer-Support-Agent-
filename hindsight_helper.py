import os
import json
import sqlite3
import datetime
from typing import List, Dict, Any, Optional

# Try importing official hindsight_client
HINDSIGHT_SDK_AVAILABLE = False
try:
    from hindsight_client import Hindsight
    HINDSIGHT_SDK_AVAILABLE = True
except ImportError:
    HINDSIGHT_SDK_AVAILABLE = False


class LocalHindsightStore:
    """
    Fallback persistent Hindsight memory store using SQLite.
    Ensures long-term memory works seamlessly out-of-the-box across app restarts
    even if an online Hindsight Cloud API key is not yet configured.
    """
    def __init__(self, db_path: str = "hindsight_local_db.sqlite"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_id TEXT NOT NULL,
                content TEXT NOT NULL,
                memory_type TEXT DEFAULT 'Experience',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()

    def retain(self, bank_id: str, content: str, memory_type: str = "Experience", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        meta_str = json.dumps(metadata) if metadata else "{}"
        cursor.execute(
            "INSERT INTO memories (bank_id, content, memory_type, metadata) VALUES (?, ?, ?, ?)",
            (bank_id, content, memory_type, meta_str)
        )
        conn.commit()
        mem_id = cursor.lastrowid
        conn.close()
        return {
            "status": "success",
            "id": mem_id,
            "bank_id": bank_id,
            "content": content,
            "memory_type": memory_type,
            "timestamp": datetime.datetime.now().isoformat()
        }

    def recall(self, bank_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, content, memory_type, created_at, metadata FROM memories WHERE bank_id = ? ORDER BY id DESC",
            (bank_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        # Simple semantic-relevance scoring for local recall
        query_words = set(query.lower().split())
        scored_results = []
        for r in rows:
            mem_id, content, m_type, created_at, meta_json = r
            content_words = set(content.lower().split())
            overlap = len(query_words.intersection(content_words))
            # Calculate a basic score based on keyword overlap + recency bonus
            score = 0.5 + (overlap * 0.1)
            try:
                meta = json.loads(meta_json) if meta_json else {}
            except Exception:
                meta = {}

            scored_results.append({
                "id": mem_id,
                "text": content,
                "type": m_type,
                "score": round(score, 2),
                "created_at": created_at,
                "metadata": meta
            })

        # Sort by score descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def get_all(self, bank_id: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, content, memory_type, created_at, metadata FROM memories WHERE bank_id = ? ORDER BY id DESC",
            (bank_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        results = []
        for r in rows:
            try:
                meta = json.loads(r[4]) if r[4] else {}
            except Exception:
                meta = {}
            results.append({
                "id": r[0],
                "text": r[1],
                "type": r[2],
                "created_at": r[3],
                "metadata": meta
            })
        return results

    def clear_bank(self, bank_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE bank_id = ?", (bank_id,))
        conn.commit()
        conn.close()


class HindsightMemoryManager:
    """
    Unified Hindsight Manager that connects to official Hindsight Cloud SDK
    or gracefully falls back to local persistent store if offline/unconfigured.
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("HINDSIGHT_API_KEY", "")
        self.base_url = base_url or os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
        self.client = None
        self.mode = "local"
        self.local_store = LocalHindsightStore()

        self._init_client()

    def _init_client(self):
        if HINDSIGHT_SDK_AVAILABLE and self.api_key and self.api_key.strip() != "your_hindsight_api_key_here":
            try:
                self.client = Hindsight(base_url=self.base_url, api_key=self.api_key)
                self.mode = "cloud"
            except Exception as e:
                print(f"[HindsightManager] Failed to init Hindsight Cloud SDK: {e}. Falling back to local store.")
                self.mode = "local"
        else:
            self.mode = "local"

    def get_status(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "sdk_available": HINDSIGHT_SDK_AVAILABLE,
            "base_url": self.base_url if self.mode == "cloud" else "Local Persistent SQLite",
            "api_key_configured": bool(self.api_key and self.api_key != "your_hindsight_api_key_here")
        }

    def retain(self, bank_id: str, content: str, memory_type: str = "Experience", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Store a new memory fragment for a specific customer bank_id.
        """
        if self.mode == "cloud" and self.client:
            try:
                res = self.client.retain(bank_id=bank_id, content=content)
                return {"status": "success", "mode": "cloud", "result": str(res)}
            except Exception as e:
                print(f"[Hindsight] Cloud retain error ({e}), storing in local fallback...")
                return self.local_store.retain(bank_id, content, memory_type, metadata)
        else:
            return self.local_store.retain(bank_id, content, memory_type, metadata)

    def recall(self, bank_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for a customer bank_id given a query.
        """
        if self.mode == "cloud" and self.client:
            try:
                res = self.client.recall(bank_id=bank_id, query=query)
                # Parse Hindsight SDK response object
                results = []
                items = getattr(res, "results", []) or []
                for item in items:
                    text = getattr(item, "text", str(item))
                    mtype = getattr(item, "type", "Fact")
                    score = getattr(item, "score", 0.95)
                    results.append({
                        "text": text,
                        "type": mtype,
                        "score": score
                    })
                return results[:top_k]
            except Exception as e:
                print(f"[Hindsight] Cloud recall error ({e}), recalling from local fallback...")
                return self.local_store.recall(bank_id, query, top_k)
        else:
            return self.local_store.recall(bank_id, query, top_k)

    def get_all_memories(self, bank_id: str) -> List[Dict[str, Any]]:
        """
        Get all stored memories for visual inspection in the UI panel.
        """
        return self.local_store.get_all(bank_id)

    def clear_customer_memories(self, bank_id: str):
        """
        Clear memories for a specific bank ID if requested.
        """
        self.local_store.clear_bank(bank_id)
