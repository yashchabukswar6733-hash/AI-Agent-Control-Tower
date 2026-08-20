from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

# ============================================================
# DATABASE
# ============================================================

from .database import get_db, init_db, new_id, now

# ============================================================
# AI
# ============================================================

from .ai_service import ask_ai

# ============================================================
# LEADS
# ============================================================

from .leads import lead_manager
from .lead_agent import process_lead

# ============================================================
# PROPOSALS
# ============================================================

from .proposals import (
    create_proposal,
    get_proposal,
    list_proposals,
    update_proposal,
    send_proposal as proposal_send,
    accept_proposal as proposal_accept,
    reject_proposal as proposal_reject,
)

# ============================================================
# PAYMENTS
# ============================================================

from .payments import payment_manager


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="AI Agent Control Tower",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():
    init_db()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "AI Agent Control Tower API",
        "status": "online"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/dashboard")
def dashboard():

    with get_db() as db:

        clients = db.execute(
            "SELECT * FROM clients ORDER BY created_at DESC"
        ).fetchall()

        agents = db.execute(
            "SELECT * FROM agents ORDER BY created_at DESC"
        ).fetchall()

        tasks = db.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC"
        ).fetchall()

        workflows = db.execute(
            "SELECT * FROM workflows ORDER BY created_at DESC"
        ).fetchall()

    return {
        "status": "online",

        "total_clients": len(clients),

        "total_agents": len(agents),

        "active_agents": sum(
            1
            for agent in agents
            if agent["status"] in ["active", "working"]
        ),

        "total_tasks": len(tasks),

        "completed_tasks": sum(
            1
            for task in tasks
            if task["status"] == "completed"
        ),

        "running_tasks": sum(
            1
            for task in tasks
            if task["status"] == "running"
        ),

        "failed_tasks": sum(
            1
            for task in tasks
            if task["status"] == "failed"
        ),

        "clients": [dict(x) for x in clients],

        "agents": [dict(x) for x in agents],

        "tasks": [dict(x) for x in tasks],

        "workflows": [dict(x) for x in workflows]
    }


# ============================================================
# CLIENTS
# ============================================================

@app.post("/clients")
def create_client(
    name: str,
    company: str
):

    client_id = new_id()
    created_at = now()

    with get_db() as db:

        db.execute(
            """
            INSERT INTO clients
            (id, name, company, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                client_id,
                name,
                company,
                "active",
                created_at
            )
        )

    return {
        "message": "Client created successfully",
        "client": {
            "id": client_id,
            "name": name,
            "company": company,
            "status": "active",
            "created_at": created_at
        }
    }


@app.get("/clients")
def get_clients():

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM clients
            ORDER BY created_at DESC
            """
        ).fetchall()

    return {
        "clients": [dict(x) for x in rows]
    }


@app.get("/clients/{client_id}")
def get_client(client_id: str):

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM clients
            WHERE id = ?
            """,
            (client_id,)
        ).fetchone()

    if not row:
        return {
            "error": "Client not found"
        }

    return {
        "client": dict(row)
    }


@app.delete("/clients/{client_id}")
def delete_client(client_id: str):

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM clients
            WHERE id = ?
            """,
            (client_id,)
        ).fetchone()

        if not row:
            return {
                "error": "Client not found"
            }

        db.execute(
            """
            DELETE FROM clients
            WHERE id = ?
            """,
            (client_id,)
        )

    return {
        "message": "Client deleted successfully",
        "client_id": client_id
    }


# ============================================================
# AGENTS
# ============================================================

@app.post("/agents")
def create_agent(
    name: str,
    role: str
):

    agent_id = new_id()
    created_at = now()

    with get_db() as db:

        db.execute(
            """
            INSERT INTO agents
            (id, name, role, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                agent_id,
                name,
                role,
                "active",
                created_at
            )
        )

    return {
        "message": "Agent created successfully",
        "agent": {
            "id": agent_id,
            "name": name,
            "role": role,
            "status": "active",
            "created_at": created_at
        }
    }


@app.get("/agents")
def get_agents():

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM agents
            ORDER BY created_at DESC
            """
        ).fetchall()

    return {
        "agents": [dict(x) for x in rows]
    }


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM agents
            WHERE id = ?
            """,
            (agent_id,)
        ).fetchone()

    if not row:
        return {
            "error": "Agent not found"
        }

    return {
        "agent": dict(row)
    }


# ============================================================
# TASKS
# ============================================================

@app.post("/tasks")
def create_task(
    agent: str,
    description: str
):

    task_id = new_id()
    created_at = now()

    with get_db() as db:

        agent_row = db.execute(
            """
            SELECT *
            FROM agents
            WHERE id = ?
            """,
            (agent,)
        ).fetchone()

        if not agent_row:
            return {
                "error": "Agent not found"
            }

        db.execute(
            """
            INSERT INTO tasks
            (id, agent, description, status, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                agent,
                description,
                "pending",
                None,
                created_at
            )
        )

    return {
        "message": "Task created successfully",
        "task": {
            "id": task_id,
            "agent": agent,
            "description": description,
            "status": "pending",
            "result": None,
            "created_at": created_at
        }
    }


@app.get("/tasks")
def get_tasks():

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM tasks
            ORDER BY created_at DESC
            """
        ).fetchall()

    return {
        "tasks": [dict(x) for x in rows]
    }


@app.get("/tasks/{task_id}")
def get_task(task_id: str):

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM tasks
            WHERE id = ?
            """,
            (task_id,)
        ).fetchone()

    if not row:
        return {
            "error": "Task not found"
        }

    return {
        "task": dict(row)
    }


# ============================================================
# EXECUTE TASK
# ============================================================

@app.post("/tasks/{task_id}/execute")
def execute_task(task_id: str):

    with get_db() as db:

        task = db.execute(
            """
            SELECT *
            FROM tasks
            WHERE id = ?
            """,
            (task_id,)
        ).fetchone()

        if not task:
            return {
                "error": "Task not found"
            }

        db.execute(
            """
            UPDATE tasks
            SET status = ?
            WHERE id = ?
            """,
            (
                "running",
                task_id
            )
        )

    try:

        result = str(
            ask_ai(
                task["description"]
            )
        )

        with get_db() as db:

            db.execute(
                """
                UPDATE tasks
                SET status = ?,
                    result = ?
                WHERE id = ?
                """,
                (
                    "completed",
                    result,
                    task_id
                )
            )

        return {
            "message": "Task executed successfully",
            "task_id": task_id,
            "status": "completed",
            "result": result
        }

    except Exception as error:

        error_message = str(error)

        with get_db() as db:

            db.execute(
                """
                UPDATE tasks
                SET status = ?,
                    result = ?
                WHERE id = ?
                """,
                (
                    "failed",
                    error_message,
                    task_id
                )
            )

        return {
            "message": "Task execution failed",
            "task_id": task_id,
            "status": "failed",
            "error": error_message
        }


# ============================================================
# WORKFLOWS
# ============================================================

@app.post("/workflows")
def create_workflow(
    client_id: str,
    goal: str
):

    workflow_id = new_id()
    created_at = now()

    with get_db() as db:

        client = db.execute(
            """
            SELECT *
            FROM clients
            WHERE id = ?
            """,
            (client_id,)
        ).fetchone()

        if not client:
            return {
                "error": "Client not found"
            }

        db.execute(
            """
            INSERT INTO workflows
            (id, client_id, goal, status, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                workflow_id,
                client_id,
                goal,
                "pending",
                None,
                created_at
            )
        )

        for step_name in [
            "research",
            "analysis",
            "report"
        ]:

            db.execute(
                """
                INSERT INTO workflow_steps
                (workflow_id, name, status, result)
                VALUES (?, ?, ?, ?)
                """,
                (
                    workflow_id,
                    step_name,
                    "pending",
                    None
                )
            )

    return {
        "message": "Workflow created",
        "workflow": {
            "id": workflow_id,
            "client_id": client_id,
            "goal": goal,
            "status": "pending",
            "result": None,
            "created_at": created_at
        }
    }


@app.get("/workflows")
def get_workflows():

    with get_db() as db:

        workflows = db.execute(
            """
            SELECT *
            FROM workflows
            ORDER BY created_at DESC
            """
        ).fetchall()

        output = []

        for workflow in workflows:

            steps = db.execute(
                """
                SELECT name, status, result
                FROM workflow_steps
                WHERE workflow_id = ?
                ORDER BY id
                """,
                (workflow["id"],)
            ).fetchall()

            item = dict(workflow)

            item["steps"] = [
                dict(step)
                for step in steps
            ]

            output.append(item)

    return {
        "workflows": output
    }


@app.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: str):

    with get_db() as db:

        workflow = db.execute(
            """
            SELECT *
            FROM workflows
            WHERE id = ?
            """,
            (workflow_id,)
        ).fetchone()

        if not workflow:
            return {
                "error": "Workflow not found"
            }

        steps = db.execute(
            """
            SELECT name, status, result
            FROM workflow_steps
            WHERE workflow_id = ?
            ORDER BY id
            """,
            (workflow_id,)
        ).fetchall()

    result = dict(workflow)

    result["steps"] = [
        dict(step)
        for step in steps
    ]

    return {
        "workflow": result
    }


# ============================================================
# EXECUTE WORKFLOW
# ============================================================

@app.post("/workflows/{workflow_id}/execute")
def execute_workflow(workflow_id: str):

    with get_db() as db:

        workflow = db.execute(
            """
            SELECT *
            FROM workflows
            WHERE id = ?
            """,
            (workflow_id,)
        ).fetchone()

        if not workflow:
            return {
                "error": "Workflow not found"
            }

        db.execute(
            """
            UPDATE workflows
            SET status = ?
            WHERE id = ?
            """,
            (
                "running",
                workflow_id
            )
        )

        db.execute(
            """
            UPDATE workflow_steps
            SET status = ?
            WHERE workflow_id = ?
            """,
            (
                "running",
                workflow_id
            )
        )

    try:

        prompt = f"""
You are the main AI business research engine
inside an AI Automation Agency.

Business goal:

{workflow["goal"]}

Create a professional and practical business report.

Use exactly these sections:

RESEARCH

Include:
- Market findings
- Customer problems
- Competitors
- Current trends
- Opportunities

ANALYSIS

Include:
- Best opportunities
- Target customers
- Competitive advantages
- Risks
- Business strategy

REPORT

Include:
- Executive Summary
- Market Opportunity
- Recommended AI Automation Services
- Target Customers
- Competitor Overview
- Pricing Strategy
- Implementation Plan
- Recommended Next Steps

Make the answer practical and useful
for a real AI automation business.

Do not invent fake statistics.
Clearly state when information is an estimate.
"""

        result = str(
            ask_ai(prompt)
        )

        results = {
            "research": result,
            "analysis": result,
            "report": result
        }

        final_result = json.dumps(results)

        with get_db() as db:

            for step_name in [
                "research",
                "analysis",
                "report"
            ]:

                db.execute(
                    """
                    UPDATE workflow_steps
                    SET status = ?,
                        result = ?
                    WHERE workflow_id = ?
                    AND name = ?
                    """,
                    (
                        "completed",
                        result,
                        workflow_id,
                        step_name
                    )
                )

            db.execute(
                """
                UPDATE workflows
                SET status = ?,
                    result = ?
                WHERE id = ?
                """,
                (
                    "completed",
                    final_result,
                    workflow_id
                )
            )

        return {
            "message": "Workflow executed successfully",
            "workflow_id": workflow_id,
            "status": "completed",
            "results": results
        }

    except Exception as error:

        error_message = str(error)

        with get_db() as db:

            db.execute(
                """
                UPDATE workflows
                SET status = ?,
                    result = ?
                WHERE id = ?
                """,
                (
                    "failed",
                    error_message,
                    workflow_id
                )
            )

            db.execute(
                """
                UPDATE workflow_steps
                SET status = ?,
                    result = ?
                WHERE workflow_id = ?
                """,
                (
                    "failed",
                    error_message,
                    workflow_id
                )
            )

        return {
            "message": "Workflow execution failed",
            "workflow_id": workflow_id,
            "status": "failed",
            "error": error_message
        }


# ============================================================
# LEAD MANAGEMENT
# ============================================================

@app.post("/leads")
def create_lead(
    name: str,
    phone: str,
    email: str = "",
    business: str = "",
    requirement: str = ""
):

    lead = lead_manager.create_lead(
        name=name,
        phone=phone,
        email=email,
        business=business,
        requirement=requirement
    )

    return {
        "message": "Lead created successfully",
        "lead": lead
    }


@app.get("/leads")
def get_leads():

    return {
        "leads": lead_manager.list_leads()
    }


@app.get("/leads/{lead_id}")
def get_lead(lead_id: str):

    lead = lead_manager.get_lead(lead_id)

    if not lead:
        return {
            "error": "Lead not found"
        }

    return {
        "lead": lead
    }


@app.patch("/leads/{lead_id}")
def update_lead(
    lead_id: str,
    status: str = None,
    score: int = None,
    ai_analysis: str = None,
    follow_up: str = None
):

    updates = {}

    if status is not None:
        updates["status"] = status

    if score is not None:
        updates["score"] = score

    if ai_analysis is not None:
        updates["ai_analysis"] = ai_analysis

    if follow_up is not None:
        updates["follow_up"] = follow_up

    lead = lead_manager.update_lead(
        lead_id,
        **updates
    )

    if not lead:
        return {
            "error": "Lead not found"
        }

    return {
        "message": "Lead updated",
        "lead": lead
    }


@app.post("/leads/{lead_id}/process")
def process_lead_endpoint(lead_id: str):

    return process_lead(lead_id)


# ============================================================
# SALES
# ============================================================

@app.post("/sales")
def create_sales_opportunity(
    lead_id: str,
    service: str = "",
    setup_fee: float = 0,
    monthly_fee: float = 0,
    notes: str = ""
):

    with get_db() as db:

        lead = db.execute(
            """
            SELECT *
            FROM leads
            WHERE id = ?
            """,
            (lead_id,)
        ).fetchone()

        if not lead:
            return {
                "error": "Lead not found"
            }

        opportunity_id = new_id()
        created_at = now()

        db.execute(
            """
            INSERT INTO sales_opportunities
            (
                id,
                lead_id,
                stage,
                service,
                setup_fee,
                monthly_fee,
                probability,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opportunity_id,
                lead_id,
                "new",
                service,
                setup_fee,
                monthly_fee,
                10,
                notes,
                created_at,
                created_at
            )
        )

        db.execute(
            """
            INSERT INTO activity_log
            (
                entity_type,
                entity_id,
                action,
                details,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "lead",
                lead_id,
                "sales_opportunity_created",
                service,
                created_at
            )
        )

    return {
        "message": "Sales opportunity created",
        "opportunity": {
            "id": opportunity_id,
            "lead_id": lead_id,
            "stage": "new",
            "service": service,
            "setup_fee": setup_fee,
            "monthly_fee": monthly_fee,
            "probability": 10,
            "notes": notes,
            "created_at": created_at
        }
    }


@app.get("/sales")
def get_sales():

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                sales_opportunities.*,
                leads.name,
                leads.phone,
                leads.email,
                leads.business,
                leads.requirement
            FROM sales_opportunities
            LEFT JOIN leads
                ON sales_opportunities.lead_id = leads.id
            ORDER BY sales_opportunities.created_at DESC
            """
        ).fetchall()

    return {
        "sales": [dict(row) for row in rows]
    }


@app.patch("/sales/{opportunity_id}")
def update_sales_stage(
    opportunity_id: str,
    stage: str,
    probability: int = None,
    notes: str = None
):

    valid_stages = [
        "new",
        "qualified",
        "contacted",
        "meeting",
        "proposal",
        "won",
        "lost"
    ]

    if stage not in valid_stages:
        return {
            "error": "Invalid sales stage",
            "valid_stages": valid_stages
        }

    probabilities = {
        "new": 10,
        "qualified": 25,
        "contacted": 35,
        "meeting": 50,
        "proposal": 70,
        "won": 100,
        "lost": 0
    }

    with get_db() as db:

        opportunity = db.execute(
            """
            SELECT *
            FROM sales_opportunities
            WHERE id = ?
            """,
            (opportunity_id,)
        ).fetchone()

        if not opportunity:
            return {
                "error": "Sales opportunity not found"
            }

        if probability is None:
            probability = probabilities[stage]

        if notes is None:
            notes = opportunity["notes"]

        updated_at = now()

        db.execute(
            """
            UPDATE sales_opportunities
            SET stage = ?,
                probability = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                stage,
                probability,
                notes,
                updated_at,
                opportunity_id
            )
        )

        db.execute(
            """
            INSERT INTO activity_log
            (
                entity_type,
                entity_id,
                action,
                details,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "sales",
                opportunity_id,
                "stage_changed",
                stage,
                updated_at
            )
        )

    return {
        "message": "Sales opportunity updated",
        "opportunity_id": opportunity_id,
        "stage": stage,
        "probability": probability
    }


# ============================================================
# WON SALE
# ============================================================

@app.post("/sales/{opportunity_id}/won")
def mark_sale_won(opportunity_id: str):

    with get_db() as db:

        opportunity = db.execute(
            """
            SELECT *
            FROM sales_opportunities
            WHERE id = ?
            """,
            (opportunity_id,)
        ).fetchone()

        if not opportunity:
            return {
                "error": "Sales opportunity not found"
            }

        lead = db.execute(
            """
            SELECT *
            FROM leads
            WHERE id = ?
            """,
            (opportunity["lead_id"],)
        ).fetchone()

        if not lead:
            return {
                "error": "Lead not found"
            }

        client_id = new_id()
        created_at = now()

        company_name = lead["business"] or lead["name"]

        db.execute(
            """
            INSERT INTO clients
            (
                id,
                name,
                company,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                client_id,
                lead["name"],
                company_name,
                "active",
                created_at
            )
        )

        db.execute(
            """
            UPDATE sales_opportunities
            SET stage = ?,
                probability = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                "won",
                100,
                created_at,
                opportunity_id
            )
        )

        db.execute(
            """
            UPDATE leads
            SET status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                "won",
                created_at,
                lead["id"]
            )
        )

        revenue_id = new_id()

        db.execute(
            """
            INSERT INTO revenue
            (
                id,
                lead_id,
                client_id,
                service,
                setup_fee,
                monthly_fee,
                status,
                payment_date,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                revenue_id,
                lead["id"],
                client_id,
                opportunity["service"] or "AI Automation Service",
                opportunity["setup_fee"],
                opportunity["monthly_fee"],
                "pending",
                None,
                created_at
            )
        )

        db.execute(
            """
            INSERT INTO activity_log
            (
                entity_type,
                entity_id,
                action,
                details,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "sales",
                opportunity_id,
                "deal_won",
                f"Client created: {client_id}",
                created_at
            )
        )

    return {
        "message": "Deal marked as won",
        "client_id": client_id,
        "revenue_id": revenue_id,
        "setup_fee": opportunity["setup_fee"],
        "monthly_fee": opportunity["monthly_fee"],
        "status": "payment_pending"
    }


# ============================================================
# SALES DASHBOARD
# ============================================================

@app.get("/sales/dashboard")
def sales_dashboard():

    with get_db() as db:

        opportunities = db.execute(
            "SELECT * FROM sales_opportunities"
        ).fetchall()

        revenue_rows = db.execute(
            "SELECT * FROM revenue"
        ).fetchall()

    pipeline_value = sum(
        float(row["setup_fee"] or 0)
        for row in opportunities
        if row["stage"] not in ["won", "lost"]
    )

    weighted_pipeline = sum(
        float(row["setup_fee"] or 0)
        * (int(row["probability"] or 0) / 100)
        for row in opportunities
        if row["stage"] not in ["won", "lost"]
    )

    won_setup = sum(
        float(row["setup_fee"] or 0)
        for row in revenue_rows
        if row["status"] in ["pending", "paid"]
    )

    monthly_recurring = sum(
        float(row["monthly_fee"] or 0)
        for row in revenue_rows
    )

    return {
        "pipeline": {
            "open_pipeline": pipeline_value,
            "weighted_pipeline": weighted_pipeline
        },
        "revenue": {
            "won_setup_value": won_setup,
            "monthly_recurring_revenue": monthly_recurring
        },
        "deals": {
            "total": len(opportunities),
            "won": sum(
                1
                for row in opportunities
                if row["stage"] == "won"
            ),
            "lost": sum(
                1
                for row in opportunities
                if row["stage"] == "lost"
            )
        }
    }


# ============================================================
# PROPOSALS
# ============================================================

@app.post("/proposals")
def create_proposal_endpoint(
    lead_id: str,
    client_name: str,
    company: str,
    service: str,
    setup_fee: float,
    monthly_fee: float,
    description: str
):

    proposal = create_proposal(
        lead_id=lead_id,
        client_name=client_name,
        company=company,
        service=service,
        setup_fee=setup_fee,
        monthly_fee=monthly_fee,
        description=description
    )

    return {
        "message": "Proposal created successfully",
        "proposal": proposal
    }


@app.get("/proposals")
def get_proposals():

    return {
        "proposals": list_proposals()
    }


@app.get("/proposals/{proposal_id}")
def get_single_proposal(proposal_id: str):

    proposal = get_proposal(proposal_id)

    if not proposal:
        return {
            "error": "Proposal not found"
        }

    return {
        "proposal": proposal
    }


@app.patch("/proposals/{proposal_id}")
def update_proposal_endpoint(
    proposal_id: str,
    status: str = None,
    setup_fee: float = None,
    monthly_fee: float = None,
    description: str = None
):

    updates = {}

    if status is not None:
        updates["status"] = status

    if setup_fee is not None:
        updates["setup_fee"] = setup_fee

    if monthly_fee is not None:
        updates["monthly_fee"] = monthly_fee

    if description is not None:
        updates["description"] = description

    proposal = update_proposal(
        proposal_id,
        **updates
    )

    if not proposal:
        return {
            "error": "Proposal not found"
        }

    return {
        "message": "Proposal updated successfully",
        "proposal": proposal
    }


# ============================================================
# SEND PROPOSAL
# ============================================================

@app.post("/proposals/{proposal_id}/send")
def send_proposal_endpoint(proposal_id: str):

    proposal = proposal_send(proposal_id)

    if not proposal:
        return {
            "error": "Proposal not found",
            "proposal_id": proposal_id
        }

    return {
        "message": "Proposal marked as sent",
        "proposal": proposal
    }


# ============================================================
# ACCEPT PROPOSAL
# ============================================================

@app.post("/proposals/{proposal_id}/accept")
def accept_proposal_endpoint(proposal_id: str):

    proposal = proposal_accept(proposal_id)

    if not proposal:
        return {
            "error": "Proposal not found",
            "proposal_id": proposal_id
        }

    return {
        "message": "Proposal accepted",
        "proposal": proposal
    }


# ============================================================
# REJECT PROPOSAL
# ============================================================

@app.post("/proposals/{proposal_id}/reject")
def reject_proposal_endpoint(proposal_id: str):

    proposal = proposal_reject(proposal_id)

    if not proposal:
        return {
            "error": "Proposal not found",
            "proposal_id": proposal_id
        }

    return {
        "message": "Proposal rejected",
        "proposal": proposal
    }


# ============================================================
# PROPOSAL FOLLOW-UP
# ============================================================

@app.post("/proposals/{proposal_id}/follow-up")
def proposal_follow_up(proposal_id: str):

    with get_db() as db:

        proposal = db.execute(
            """
            SELECT *
            FROM proposals
            WHERE id = ?
            """,
            (proposal_id,)
        ).fetchone()

        if not proposal:
            return {
                "error": "Proposal not found"
            }

        if proposal["status"] not in ["sent", "follow_up"]:
            return {
                "error": "Proposal must be sent before follow-up"
            }

        client_name = proposal["client_name"]
        company = proposal["company"]
        service = proposal["service"]
        setup_fee = proposal["setup_fee"]
        monthly_fee = proposal["monthly_fee"]

        follow_up_message = f"""
Hi {client_name},

I wanted to follow up regarding the {service}
automation proposal for {company}.

The proposed investment is:

Setup: ₹{setup_fee:,.0f}
Monthly: ₹{monthly_fee:,.0f}

The goal is to automate repetitive lead-handling
processes so your team can respond faster and
avoid losing potential customers.

If you'd like to proceed, I can prepare the
onboarding and implementation steps.

Please let me know if you'd like to move forward.

Regards,
AI Automation Team
""".strip()

        db.execute(
            """
            UPDATE proposals
            SET status = ?
            WHERE id = ?
            """,
            (
                "follow_up",
                proposal_id
            )
        )

    return {
        "message": "Follow-up prepared successfully",
        "proposal_id": proposal_id,
        "status": "follow_up",
        "follow_up": follow_up_message
    }


# ============================================================
# PAYMENTS
# ============================================================

@app.post("/payments")
def create_payment(
    proposal_id: str,
    client_name: str,
    company: str,
    amount: float,
    payment_type: str = "setup",
    description: str = ""
):

    if amount <= 0:
        return {
            "error": "Payment amount must be greater than 0"
        }

    payment = payment_manager.create_payment(
        proposal_id=proposal_id,
        client_name=client_name,
        company=company,
        amount=amount,
        payment_type=payment_type,
        description=description
    )

    return {
        "message": "Payment created successfully",
        "payment": payment
    }


@app.get("/payments")
def get_payments():

    payments = payment_manager.list_payments()

    total_revenue = sum(
        p["amount"]
        for p in payments
        if p["status"] == "paid"
    )

    pending_revenue = sum(
        p["amount"]
        for p in payments
        if p["status"] == "pending"
    )

    cancelled_amount = sum(
        p["amount"]
        for p in payments
        if p["status"] == "cancelled"
    )

    return {
        "payments": payments,
        "metrics": {
            "total_payments": len(payments),

            "paid_payments": sum(
                1
                for p in payments
                if p["status"] == "paid"
            ),

            "pending_payments": sum(
                1
                for p in payments
                if p["status"] == "pending"
            ),

            "total_revenue": total_revenue,

            "pending_revenue": pending_revenue,

            "cancelled_amount": cancelled_amount
        }
    }


@app.get("/payments/{payment_id}")
def get_payment(payment_id: str):

    payment = payment_manager.get_payment(payment_id)

    if not payment:
        return {
            "error": "Payment not found"
        }

    return {
        "payment": payment
    }


@app.post("/payments/{payment_id}/mark-paid")
def mark_payment_paid(payment_id: str):

    payment = payment_manager.mark_paid(payment_id)

    if not payment:
        return {
            "error": "Payment not found"
        }

    return {
        "message": "Payment marked as paid",
        "payment": payment
    }


@app.post("/payments/{payment_id}/cancel")
def cancel_payment(payment_id: str):

    payment = payment_manager.cancel_payment(payment_id)

    if not payment:
        return {
            "error": "Payment not found"
        }

    return {
        "message": "Payment cancelled",
        "payment": payment
    }


# ============================================================
# REVENUE DASHBOARD
# ============================================================
#
# IMPORTANT:
# Only ONE /revenue route exists now.
# ============================================================

@app.get("/revenue")
def revenue_dashboard():

    payments = payment_manager.list_payments()

    paid = [
        p
        for p in payments
        if p["status"] == "paid"
    ]

    pending = [
        p
        for p in payments
        if p["status"] == "pending"
    ]

    cancelled = [
        p
        for p in payments
        if p["status"] == "cancelled"
    ]

    return {
        "business_revenue": {

            "total_collected": sum(
                float(p["amount"])
                for p in paid
            ),

            "pending_amount": sum(
                float(p["amount"])
                for p in pending
            ),

            "cancelled_amount": sum(
                float(p["amount"])
                for p in cancelled
            ),

            "paid_transactions": len(paid),

            "pending_transactions": len(pending),

            "cancelled_transactions": len(cancelled)
        }
    }