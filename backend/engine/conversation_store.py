from __future__ import annotations

from threading import Lock
from typing import Any, Dict, List, Set
import uuid


class ConversationStore:
    """In-memory session store for chat history, collected info, and slot planner metadata."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _default_session() -> Dict[str, Any]:
        return {
            "history": [],
            "collected_info": {},
            # Slot planner metadata
            "asked_slots": set(),
            "answered_slots": set(),
            "slot_attempts": {},  # slot_id → attempt count
            "last_planned_slot": None,
            "choice_validation_results": [],  # list of {slot, valid, reason}
        }

    def ensure_session(self, session_id: str | None) -> str:
        sid = session_id or str(uuid.uuid4())
        with self._lock:
            if sid not in self._sessions:
                self._sessions[sid] = self._default_session()
        return sid

    def get_session(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            session = self._sessions.setdefault(session_id, self._default_session())
            return {
                "history": list(session["history"]),
                "collected_info": dict(session["collected_info"]),
                "asked_slots": set(session.get("asked_slots", set())),
                "answered_slots": set(session.get("answered_slots", set())),
                "slot_attempts": dict(session.get("slot_attempts", {})),
                "last_planned_slot": session.get("last_planned_slot"),
                "choice_validation_results": list(session.get("choice_validation_results", [])),
            }

    def save_session(
        self,
        session_id: str,
        history: List[Dict[str, str]],
        collected_info: Dict[str, Any],
        asked_slots: Set[str] | None = None,
        answered_slots: Set[str] | None = None,
        slot_attempts: Dict[str, int] | None = None,
        last_planned_slot: str | None = None,
        choice_validation_results: List[Dict[str, Any]] | None = None,
    ) -> None:
        with self._lock:
            self._sessions[session_id] = {
                "history": history,
                "collected_info": collected_info,
                "asked_slots": asked_slots or set(),
                "answered_slots": answered_slots or set(),
                "slot_attempts": slot_attempts or {},
                "last_planned_slot": last_planned_slot,
                "choice_validation_results": choice_validation_results or [],
            }


_store = ConversationStore()


def get_conversation_store() -> ConversationStore:
    return _store
