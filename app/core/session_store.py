from dataclasses import dataclass, field


@dataclass
class Session:
    session_id: str
    history: list[dict] = field(default_factory=list)


class SessionStore:
    """In-memory conversation history store."""

    def __init__(self, max_history_turns: int = 20):
        self.sessions: dict[str, Session] = {}
        self.max_history_turns = max_history_turns

    def get_or_create(self, session_id: str) -> Session:
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(session_id=session_id)

        return self.sessions[session_id]

    def get_history(self, session_id: str) -> list[dict]:
        return self.get_or_create(session_id).history

    def add_turn(
        self,
        session_id: str,
        user_text: str,
        assistant_text: str,
    ) -> None:
        session = self.get_or_create(session_id)

        session.history.append(
            {
                "role": "user",
                "content": user_text,
            }
        )

        session.history.append(
            {
                "role": "assistant",
                "content": assistant_text,
            }
        )

        max_items = self.max_history_turns * 2

        if len(session.history) > max_items:
            session.history = session.history[-max_items:]

    def clear(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)