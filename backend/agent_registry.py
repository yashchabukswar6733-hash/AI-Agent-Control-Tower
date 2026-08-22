from .supervisor import supervisor


def research_agent(payload):
    """
    Research agent entry point.

    This is intentionally small: the supervisor owns routing,
    while the agent owns its actual business operation.
    """

    description = str(
        payload.get("description", "")
    ).strip()

    if not description:
        raise ValueError(
            "Research task requires a description"
        )

    # Existing AI execution will be connected here.
    return {
        "type": "research",
        "description": description
    }


def register_default_agents():
    supervisor.register(
        "research_agent",
        research_agent
    )


register_default_agents()
