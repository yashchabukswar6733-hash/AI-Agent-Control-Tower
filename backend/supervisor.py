import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class Supervisor:

    """
    Central dispatcher for business automation agents.

    The supervisor decides which specialized agent should handle
    an event/task. It does not contain the business logic itself.
    """

    def __init__(self):
        self._handlers = {}

    def register(self, name: str, handler):
        if not name:
            raise ValueError("Agent name is required")

        if not callable(handler):
            raise TypeError(f"Handler for '{name}' must be callable")

        self._handlers[name] = handler
        logger.info("Registered agent: %s", name)

    def available_agents(self):
        return sorted(self._handlers.keys())

    def dispatch(
        self,
        agent: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:

        if not agent:
            raise ValueError("Agent is required")

        handler = self._handlers.get(agent)

        if handler is None:
            raise ValueError(
                f"No registered agent for '{agent}'. "
                f"Available: {self.available_agents()}"
            )

        if payload is None:
            payload = {}

        logger.info(
            "Dispatching task to agent=%s",
            agent
        )

        result = handler(payload)

        return {
            "agent": agent,
            "status": "completed",
            "result": result
        }


supervisor = Supervisor()
