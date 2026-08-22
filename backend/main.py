from .razorpay_webhook import install as install_razorpay_webhook
from backend.database import get_db
import os

from backend.whatsapp_service import send_whatsapp_message, verify_whatsapp_configuration
from backend.api.whatsapp import router as whatsapp_router
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from .business_service import get_business_by_token
import json


@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# FASTAPI APPLICATION

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

app = FastAPI(

    title="AI Agent Control Tower",
    version="1.0.0"
)

install_razorpay_webhook(app)

app.include_router(whatsapp_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# DATABASE

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

from .database import get_db, init_db, new_id, now
from .services.workforce_service import provision_agents


@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# AI

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

from .ai_service import ask_ai


@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# LEADS

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

from .leads import lead_manager
from .lead_agent import process_lead



@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# CUSTOMER ONBOARDING

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.post("/clients/onboard")
def onboard_client(
    request: Request,
    lead_id: str,
    service: str = "",
    notes: str = ""
):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        lead = db.execute(
            """
            SELECT *
            FROM leads
            WHERE id = ?
              AND business_id = ?
            """,
            (
                lead_id,
                business_id
            )
        ).fetchone()

        if not lead:
            return {
                "error": "Lead not found"
            }

        company = lead["business"] or lead["name"]

        existing = db.execute(
            """
            SELECT *
            FROM clients
            WHERE business_id = ?
              AND company = ?
            LIMIT 1
            """,
            (
                business_id,
                company
            )
        ).fetchone()

        if existing:
            return {
                "message": "Client already onboarded",
                "client": dict(existing)
            }

        client_id = new_id()
        created_at = now()

        db.execute(
            """
            INSERT INTO clients
            (
                id,
                name,
                company,
                status,
                created_at,
                business_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                lead["name"],
                company,
                "active",
                created_at,
                business_id
            )
        )

        db.execute(
            """
            UPDATE leads
            SET status = ?,
                updated_at = ?
            WHERE id = ?
              AND business_id = ?
            """,
            (
                "won",
                created_at,
                lead_id,
                business_id
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
                "client",
                client_id,
                "client_onboarded",
                service or notes or "Client onboarding completed",
                created_at
            )
        )

    return {
        "message": "Client onboarded successfully",
        "client": {
            "id": client_id,
            "name": lead["name"],
            "company": company,
            "status": "active",
            "business_id": business_id,
            "created_at": created_at
        }
    }


@app.get("/clients/{client_id}")
def get_client(
    request: Request,
    client_id: str
):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        client = db.execute(
            """
            SELECT *
            FROM clients
            WHERE id = ?
              AND business_id = ?
            """,
            (
                client_id,
                business_id
            )
        ).fetchone()

        if not client:
            return {
                "error": "Client not found"
            }

        payments = db.execute(
            """
            SELECT *
            FROM payments
            WHERE client_id = ?
              AND business_id = ?
            ORDER BY created_at DESC
            """,
            (
                client_id,
                business_id
            )
        ).fetchall()

        revenue = db.execute(
            """
            SELECT *
            FROM revenue
            WHERE client_id = ?
              AND business_id = ?
            ORDER BY created_at DESC
            """,
            (
                client_id,
                business_id
            )
        ).fetchall()

    return {
        "client": dict(client),
        "payments": [dict(x) for x in payments],
        "revenue": [dict(x) for x in revenue]
    }



@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# PROPOSALS

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

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



@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.on_event("startup")
def startup():
    init_db()




@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# DASHBOARD DATA

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.get("/api/dashboard")
def dashboard_data(request: Request):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        leads = db.execute(
            '''
            SELECT *
            FROM leads
            WHERE business_id = ?
            ORDER BY created_at DESC
            ''',
            (business_id,)
        ).fetchall()

        sales = db.execute(
            '''
            SELECT *
            FROM sales_opportunities
            WHERE business_id = ?
            ORDER BY created_at DESC
            ''',
            (business_id,)
        ).fetchall()

        proposals = db.execute(
            '''
            SELECT *
            FROM proposals
            WHERE business_id = ?
            ORDER BY created_at DESC
            ''',
            (business_id,)
        ).fetchall()

        payments = db.execute(
            '''
            SELECT *
            FROM payments
            WHERE business_id = ?
            ORDER BY created_at DESC
            ''',
            (business_id,)
        ).fetchall()

    paid_revenue = sum(
        float(x["amount"] or 0)
        for x in payments
        if x["status"] == "paid"
    )

    pending_revenue = sum(
        float(x["amount"] or 0)
        for x in payments
        if x["status"] == "pending"
    )

    return {
        "business_id": business_id,
        "summary": {
            "leads": len(leads),
            "sales_opportunities": len(sales),
            "proposals": len(proposals),
            "payments": len(payments),
            "paid_revenue": paid_revenue,
            "pending_revenue": pending_revenue
        },
        "leads": [dict(x) for x in leads],
        "sales": [dict(x) for x in sales],
        "proposals": [dict(x) for x in proposals],
        "payments": [dict(x) for x in payments]
    }



@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# DASHBOARD

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.get("/dashboard")
def dashboard_page():
    dashboard = Path(__file__).resolve().parent.parent / "frontend" / "dashboard.html"

    if not dashboard.exists():
        raise HTTPException(
            status_code=404,
            detail="Dashboard frontend not found"
        )

    return FileResponse(dashboard)



@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# ROOT

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.get("/")
def root():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    return FileResponse(frontend)



@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# HEALTH

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }



@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# PUBLIC BUSINESS AUTHENTICATION

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

from .business_service import create_business, login_business, logout

@app.post('/auth/register')
async def register_business(request: Request):
    data = await request.json()
    try:
        return create_business(str(data.get('business_name','')),str(data.get('owner_name','')),str(data.get('email','')),str(data.get('phone','')),str(data.get('plan','Starter')))
    except ValueError as e:
        raise HTTPException(status_code=400,detail=str(e))

@app.post('/auth/login')
async def login_business_endpoint(request: Request):
    data = await request.json()
    try:
        return login_business(str(data.get('email','')).strip())
    except ValueError as e:
        raise HTTPException(status_code=401,detail=str(e))

@app.post('/auth/logout')
def logout_business(request: Request):
    authorization=request.headers.get('Authorization','')
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401,detail='Business authentication required')
    logout(authorization[7:].strip())
    return {'success':True}

@app.get('/auth/me')
def current_business(request: Request):
    return {'business':get_current_business(request)}


@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# BUSINESS AUTHENTICATION

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

def get_current_business(request: Request):

    authorization = request.headers.get("Authorization", "")

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Business authentication required"
        )

    token = authorization[7:].strip()

    business = get_business_by_token(token)

    if not business:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired workspace session"
        )

    return business


@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# DASHBOARD

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.get("/dashboard")
def dashboard(request: Request):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        clients = db.execute(
            """
            SELECT *
            FROM clients
            WHERE business_id = ?
            ORDER BY created_at DESC
            """,
            (business_id,)
        ).fetchall()

        agents = db.execute(
            """
            SELECT *
            FROM agents
            WHERE business_id = ?
            ORDER BY created_at DESC
            """,
            (business_id,)
        ).fetchall()

        tasks = db.execute(
            """
            SELECT *
            FROM tasks
            WHERE business_id = ?
            ORDER BY created_at DESC
            """,
            (business_id,)
        ).fetchall()

        workflows = db.execute(
            """
            SELECT *
            FROM workflows
            WHERE business_id = ?
            ORDER BY created_at DESC
            """,
            (business_id,)
        ).fetchall()

    return {
        "status": "online",
        "business": {
            "id": business["id"],
            "business_name": business["business_name"],
            "owner_name": business["owner_name"],
            "email": business["email"],
            "plan": business["plan"],
            "status": business["status"]
        },

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


@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# CLIENTS

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================


@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# CLIENTS

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.post("/clients")
def create_client(
    request: Request,
    name: str,
    company: str
):

    business = get_current_business(request)
    business_id = business["id"]

    client_id = new_id()
    created_at = now()

    with get_db() as db:

        db.execute(
            """
            INSERT INTO clients
            (id, name, company, status, created_at, business_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                name,
                company,
                "active",
                created_at,
                business_id
            )
        )

    return {
        "message": "Client created successfully",
        "client": {
            "id": client_id,
            "business_id": business_id,
            "name": name,
            "company": company,
            "status": "active",
            "created_at": created_at
        }
    }


@app.get("/clients")
def get_clients(request: Request):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM clients
            WHERE business_id = ?
            ORDER BY created_at DESC
            """,
            (business_id,)
        ).fetchall()

    return {
        "clients": [dict(x) for x in rows]
    }


@app.get("/clients/{client_id}")
def get_client(
    request: Request,
    client_id: str
):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM clients
            WHERE id = ?
            AND business_id = ?
            """,
            (
                client_id,
                business_id
            )
        ).fetchone()

    if not row:
        return {
            "error": "Client not found"
        }

    return {
        "client": dict(row)
    }


@app.delete("/clients/{client_id}")
def delete_client(
    request: Request,
    client_id: str
):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM clients
            WHERE id = ?
            AND business_id = ?
            """,
            (
                client_id,
                business_id
            )
        ).fetchone()

        if not row:
            return {
                "error": "Client not found"
            }

        db.execute(
            """
            DELETE FROM clients
            WHERE id = ?
            AND business_id = ?
            """,
            (
                client_id,
                business_id
            )
        )

    return {
        "message": "Client deleted successfully",
        "client_id": client_id
    }


@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# AGENTS

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.post("/agents")
def create_agent(
    request: Request,
    name: str,
    role: str
):

    business = get_current_business(request)
    business_id = business["id"]

    agent_id = new_id()
    created_at = now()

    with get_db() as db:

        db.execute(
            """
            INSERT INTO agents
            (
                id,
                name,
                role,
                status,
                created_at,
                business_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                agent_id,
                name,
                role,
                "active",
                created_at,
                business_id
            )
        )

    return {
        "message": "Agent created successfully",
        "agent": {
            "id": agent_id,
            "business_id": business_id,
            "name": name,
            "role": role,
            "status": "active",
            "created_at": created_at
        }
    }


@app.get("/agents")
def get_agents(request: Request):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM agents
            WHERE business_id = ?
            ORDER BY created_at DESC
            """,
            (business_id,)
        ).fetchall()

    return {
        "agents": [dict(x) for x in rows]
    }


@app.get("/agents/{agent_id}")
def get_agent(
    request: Request,
    agent_id: str
):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM agents
            WHERE id = ?
            AND business_id = ?
            """,
            (
                agent_id,
                business_id
            )
        ).fetchone()

    if not row:
        return {
            "error": "Agent not found"
        }

    return {
        "agent": dict(row)
    }


@app.patch("/agents/{agent_id}/status")
def update_agent_status(
    request: Request,
    agent_id: str,
    status: str
):

    business = get_current_business(request)
    business_id = business["id"]

    allowed_statuses = {
        "active",
        "working",
        "idle",
        "paused",
        "offline"
    }

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid agent status"
        )

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM agents
            WHERE id = ?
            AND business_id = ?
            """,
            (
                agent_id,
                business_id
            )
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Agent not found"
            )

        db.execute(
            """
            UPDATE agents
            SET status = ?
            WHERE id = ?
            AND business_id = ?
            """,
            (
                status,
                agent_id,
                business_id
            )
        )

    return {
        "message": "Agent status updated",
        "agent_id": agent_id,
        "business_id": business_id,
        "status": status
    }


@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# TASKS

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.post("/tasks")
def create_task(
    request: Request,
    agent: str,
    description: str
):
    business = get_current_business(request)
    business_id = business["id"]

    task_id = new_id()
    created_at = now()

    with get_db() as db:

        agent_row = db.execute(
            """
            SELECT *
            FROM agents
            WHERE id = ?
              AND business_id = ?
            """,
            (
                agent,
                business_id
            )
        ).fetchone()

        if not agent_row:
            raise HTTPException(
                status_code=404,
                detail="Agent not found in this workspace"
            )

        db.execute(
            """
            INSERT INTO tasks
            (
                id,
                agent,
                description,
                status,
                result,
                created_at,
                business_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                agent,
                description,
                "pending",
                None,
                created_at,
                business_id
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
            "created_at": created_at,
            "business_id": business_id
        }
    }


@app.get("/tasks")
def get_tasks(request: Request):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM tasks
            WHERE business_id = ?
            ORDER BY created_at DESC
            """,
            (business_id,)
        ).fetchall()

    return {
        "tasks": [dict(x) for x in rows]
    }


@app.get("/tasks/{task_id}")
def get_task(
    task_id: str,
    request: Request
):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM tasks
            WHERE id = ?
              AND business_id = ?
            """,
            (
                task_id,
                business_id
            )
        ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Task not found in this workspace"
        )

    return {
        "task": dict(row)
    }



@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# EXECUTE TASK

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.post("/tasks/{task_id}/execute")
def execute_task(
    task_id: str,
    request: Request
):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        task = db.execute(
            """
            SELECT *
            FROM tasks
            WHERE id = ?
              AND business_id = ?
            """,
            (
                task_id,
                business_id
            )
        ).fetchone()

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found in this workspace"
            )

        db.execute(
            """
            UPDATE tasks
            SET status = ?
            WHERE id = ?
              AND business_id = ?
            """,
            (
                "running",
                task_id,
                business_id
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
                  AND business_id = ?
                """,
                (
                    "completed",
                    result,
                    task_id,
                    business_id
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
                  AND business_id = ?
                """,
                (
                    "failed",
                    error_message,
                    task_id,
                    business_id
                )
            )

        return {
            "message": "Task execution failed",
            "task_id": task_id,
            "status": "failed",
            "error": error_message
        }


@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# WORKFLOWS

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.post("/workflows")
def create_workflow(
    request: Request,
    client_id: str,
    goal: str
):

    business = get_current_business(request)
    business_id = business["id"]

    workflow_id = new_id()
    created_at = now()

    with get_db() as db:

        client = db.execute(
            """
            SELECT *
            FROM clients
            WHERE id = ?
              AND business_id = ?
            """,
            (
                client_id,
                business_id
            )
        ).fetchone()

        if not client:
            raise HTTPException(
                status_code=404,
                detail="Client not found in this workspace"
            )

        db.execute(
            """
            INSERT INTO workflows
            (
                id,
                client_id,
                goal,
                status,
                result,
                created_at,
                business_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workflow_id,
                client_id,
                goal,
                "pending",
                None,
                created_at,
                business_id
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
            "created_at": created_at,
            "business_id": business_id
        }
    }


@app.get("/workflows")
def get_workflows(request: Request):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        workflows = db.execute(
            """
            SELECT *
            FROM workflows
            WHERE business_id = ?
            ORDER BY created_at DESC
            """,
            (business_id,)
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
def get_workflow(
    workflow_id: str,
    request: Request
):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        workflow = db.execute(
            """
            SELECT *
            FROM workflows
            WHERE id = ?
              AND business_id = ?
            """,
            (
                workflow_id,
                business_id
            )
        ).fetchone()

        if not workflow:
            raise HTTPException(
                status_code=404,
                detail="Workflow not found in this workspace"
            )

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



@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# EXECUTE WORKFLOW

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.post("/workflows/{workflow_id}/execute")
def execute_workflow(
    workflow_id: str,
    request: Request
):

    business = get_current_business(request)
    business_id = business["id"]

    with get_db() as db:

        workflow = db.execute(
            """
            SELECT *
            FROM workflows
            WHERE id = ?
              AND business_id = ?
            """,
            (
                workflow_id,
                business_id
            )
        ).fetchone()

        if not workflow:
            raise HTTPException(
                status_code=404,
                detail="Workflow not found in this workspace"
            )

        db.execute(
            """
            UPDATE workflows
            SET status = ?
            WHERE id = ?
              AND business_id = ?
            """,
            (
                "running",
                workflow_id,
                business_id
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
                  AND business_id = ?
                """,
                (
                    "completed",
                    final_result,
                    workflow_id,
                    business_id
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
                  AND business_id = ?
                """,
                (
                    "failed",
                    error_message,
                    workflow_id,
                    business_id
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


@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================
# LEAD MANAGEMENT

@app.get("/login")
def login_page():
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "auth.html"
    return FileResponse(frontend)

# ============================================================

@app.post("/leads")
def create_lead(
    request: Request,
    name: str,
    phone: str,
    email: str = "",
    business: str = "",
    requirement: str = ""
):

    current_business = get_current_business(request)
    business_id = current_business["id"]

    lead = lead_manager.create_lead(
        business_id=business_id,
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
def get_leads(
    request: Request
):

    business = get_current_business(
        request
    )

    return {
        "leads": list_leads(
            business_id=business["id"]
        )
    }




