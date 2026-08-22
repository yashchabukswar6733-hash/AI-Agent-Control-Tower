from backend.database import get_db, new_id, now


DEFAULT_AGENTS = [
    ("Lead Qualification Agent", "Qualifies incoming leads and scores buying intent"),
    ("Customer Support Agent", "Answers customer questions and captures requirements"),
    ("Sales Agent", "Handles sales conversations and recommends services"),
    ("Follow-Up Agent", "Tracks leads and prepares follow-up actions"),
    ("Proposal Agent", "Creates and manages customer proposals"),
    ("Payment Agent", "Tracks payments and payment status"),
    ("Supervisor Agent", "Coordinates the AI workforce and workflows"),
]


def provision_agents(business_id):

    created = []

    with get_db() as db:

        for name, role in DEFAULT_AGENTS:

            existing = db.execute(
                """
                SELECT id
                FROM agents
                WHERE name = ?
                AND business_id = ?
                """,
                (name, business_id)
            ).fetchone()

            if existing:
                continue

            agent_id = new_id()

            db.execute(
                """
                INSERT INTO agents
                (
                    id,
                    business_id,
                    name,
                    role,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_id,
                    business_id,
                    name,
                    role,
                    "active",
                    now()
                )
            )

            created.append({
                "id": agent_id,
                "name": name,
                "role": role,
                "status": "active"
            })

    return created
