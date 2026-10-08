import requests
import socket
import json
import subprocess
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
import zipfile
import tarfile
from werkzeug.utils import secure_filename
import re
import logging
import binascii
import os
import pandas as pd
import numpy as np
import shutil
import time
import random
from file_read_backwards import FileReadBackwards
from datetime import datetime
import configparser
from flask_cors import CORS
import logging
import platform
import hashlib
import psutil
import glob
import sqlite3
import threading
import base64
import sys
import grp
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import warnings
import pyodbc
import paramiko
from scp import SCPClient

from fastapi import FastAPI, Request, Response, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError

import asyncio
from typing import AsyncGenerator, Optional
import traceback

import zipfile
from werkzeug.utils import secure_filename
import re
import ast
import logging
from collections import defaultdict
import binascii
import codecs
import os
import sys, io
import pandas as pd
import numpy as np
import shutil
import time
from file_read_backwards import FileReadBackwards
from datetime import datetime, timezone, date
import configparser
import paramiko
from scp import SCPClient
import logging
import platform
import hashlib
import psutil
import glob
import sqlite3
import threading
from pathlib import Path
import base64
import grp
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import boto3
import botocore
from smart_open import open as s3_open
from io import BytesIO, TextIOWrapper
import gzip
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.exc import OperationalError
from sqlalchemy.engine import Connection as SAConnection
from migdb.license import load_license
from typing import Dict, List, Any, Tuple, Iterator
from decimal import Decimal
from enum import Enum
import statistics
import tempfile
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle   
import PyPDF2
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import multiprocessing as mp

from .auth import create_access_token
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse as _AuthJSONResponse
from jose import JWTError
from .auth import decode_access_token

from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi

from fastapi_mcp import FastApiMCP

def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

app = FastAPI(title="MigDB for Oracle Agent API",
    description="API for managing MigDB",
    version="26.5.0",
    contact={
        "name": "SkyliftAI Support Team",
        "email": "support@skyliftai.com"
    },)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title, 
        version=app.version, 
        routes=app.routes, 
        tags=tags_metadata
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", []).append({"BearerAuth": []})
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

PUBLIC_PATHS = {
    "/api/v2/onep/login",
    "/docs",
    "/redoc",
    "/openapi.json",
}

PUBLIC_PREFIXES = ("/docs", "/redoc")

import json


class JWTAuthMiddleware:
    """Pure ASGI middleware — safe to stack with CacheHeadersMiddleware and
    won't interfere with StreamingResponse (SSE) endpoints, unlike
    BaseHTTPMiddleware/@app.middleware('http')."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        method = scope["method"]

        if (
            method == "OPTIONS"
            or path in PUBLIC_PATHS
            or path.startswith(PUBLIC_PREFIXES)
            or not path.startswith("/api/")
        ):
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        auth_header = headers.get(b"authorization", b"").decode()

        if not auth_header or not auth_header.startswith("Bearer "):
            await self._send_json_401(send, "Not authenticated")
            return

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_access_token(token)
        except JWTError:
            await self._send_json_401(send, "Invalid or expired token")
            return

        scope.setdefault("state", {})
        scope["state"]["user"] = payload

        await self.app(scope, receive, send)

    @staticmethod
    async def _send_json_401(send, detail):
        body = json.dumps({"detail": detail}).encode()
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"www-authenticate", b"Bearer"),
                (b"content-length", str(len(body)).encode()),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })


class CacheHeadersMiddleware:
    """Pure ASGI middleware — safe to stack with JWTAuthMiddleware and won't
    interfere with StreamingResponse (SSE) endpoints, unlike @app.middleware('http')."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"].startswith("/mcp"):
            await self.app(scope, receive, send)
            return

        path = scope["path"]

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                if "fonts" in path or path.endswith(".woff2"):
                    headers.append((b"cache-control", b"public, max-age=31536000"))
                elif path.endswith((".js", ".css")):
                    headers.append((b"cache-control", b"max-age=3600"))
            await send(message)

        await self.app(scope, receive, send_wrapper)


app.add_middleware(JWTAuthMiddleware)
app.add_middleware(CacheHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SENSITIVE_KEYS = {"password", "pwd", "token", "secret", "authorization", "access_token", "refresh_token", "api_key"}
REDACTED = "***REDACTED***"

def sanitize(obj, key=None):
    if key and key.lower() in SENSITIVE_KEYS:
        return REDACTED
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if isinstance(obj, dict):
        return {k: sanitize(v, key=k) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, Exception):
        return str(obj)
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        return str(obj)

def redact_raw_body(raw: bytes) -> str:
    """Try to redact password-like fields in raw body, whether JSON or form-encoded."""
    text = raw.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(text)
        redacted = sanitize(parsed)
        return json.dumps(redacted)
    except (json.JSONDecodeError, TypeError):
        # fallback for form-encoded or plain text: mask key=value pairs
        pattern = r'(?i)("?(?:' + '|'.join(SENSITIVE_KEYS) + r')"?\s*[:=]\s*)("?[^&\n"]*"?)'
        return re.sub(pattern, r'\1"' + REDACTED + '"', text)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    redacted_body = redact_raw_body(body)

    logging.error(f"422 RAW BODY   : {redacted_body}")
    logging.error(f"422 HEADERS    : {sanitize(dict(request.headers))}")
    logging.error(f"422 ERRORS     : {[sanitize(e) for e in exc.errors()]}")

    return JSONResponse(
        status_code=422,
        content={
            "detail"  : [sanitize(e) for e in exc.errors()],
            "raw_body": redacted_body,
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"UNHANDLED ERROR on {request.url.path}: {traceback.format_exc()}")

    raw_message = str(exc)
    redacted_message = redact_raw_body(raw_message.encode("utf-8", errors="replace"))

    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal error: {redacted_message}"}
    )

tags_metadata = [
    {
        "name": "Auth",
        "description": "Authentication",
    },
    {
        "name": "MigDB Deployment Details",
        "description": "Host, OS platform, CDC version, Oracle client version, and software home details.",
    },
    {
        "name": "MigDB Monitoring",
        "description": "Process status snapshots, topology diagrams, and full process info.",
    },
    {
        "name": "MigDB System",
        "description": "Service health checks.",
    },
    {
        "name": "MigDB System Monitoring",
        "description": "Memory, CPU, thread, and IO statistics for MigDB processes and the host.",
    },
    {
        "name": "MigDB Extract Management",
        "description": "Add, delete, and manage integrated/classic extracts, trails, and transactions.",
    },
    {
        "name": "MigDB Extract Operations",
        "description": "Start, stop, kill, stats, checkpoint, and mode-change operations on extracts.",
    },
    {
        "name": "MigDB Extract Process Details",
        "description": "Extract name and trail name details.",
    },
    {
        "name": "MigDB Extract Trail from Name",
        "description": "Resolve extract trail names from an extract name.",
    },
    {
        "name": "Add Extract Trail to an Extract",
        "description": "Attach a new trail to an existing extract.",
    },
    {
        "name": "Get Trail details from Trail name",
        "description": "List generated trail files with size and creation time.",
    },
    {
        "name": "MigDB CDC Trail Analysis",
        "description": "Logdump-based trail file analysis: headers, record counts, and trail path listing.",
    },
    {
        "name": "CDC Trail Analysis",
        "description": "Transaction navigation within trail files (next/previous transactions at a given RBA).",
    },
    {
        "name": "MigDB Pump Management",
        "description": "Add pump processes and manage remote trails.",
    },
    {
        "name": "MigDB Replicat Management",
        "description": "Add, start, stop, and troubleshoot replicat processes.",
    },
    {
        "name": "MigDB Replicat Operations",
        "description": "Start, stop, kill, stats, and mode-change operations on replicats.",
    },
    {
        "name": "MigDB Manager",
        "description": "Manager process operations and report viewing.",
    },
    {
        "name": "MigDB Process Management",
        "description": "Bulk start/stop actions on extract, pump, and replicat processes.",
    },
    {
        "name": "MigDB Parameter Management",
        "description": "View, edit, and save parameter, report, and discard files; manage mgr.prm blocks.",
    },
    {
        "name": "MigDB Checkpoint Management",
        "description": "Add, view, delete, upgrade, and clean checkpoint tables.",
    },
    {
        "name": "MigDB SecureVault Management",
        "description": "Manage secure vault domains, aliases, credentials, and bulk uploads.",
    },
    {
        "name": "MigDB Encryption Master Key Management",
        "description": "Create, renew, delete, and deploy encryption master keys and wallets.",
    },
    {
        "name": "MigDB Supplemental Logging",
        "description": "Schema-level supplemental logging (schematrandata) management.",
    },
    {
        "name": "MigDB Heartbeat Management",
        "description": "Add, edit, and delete heartbeat tables via the manage endpoint.",
    },
    {
        "name": "MigDB AutoCDR",
        "description": "Auto CDR compatibility checks and tombstone table details.",
    },
    {
        "name": "CDR Management",
        "description": "Enable, view, alter, or disable Auto CDR for selected tables.",
    },
    {
        "name": "CDR, exceptions, dba_apply_error_messages, conflicts",
        "description": "CDR conflict exception records from dba_apply_error_messages.",
    },
    {
        "name": "MigDB Heterogeneous Initial Load",
        "description": "Initial load jobs: extracts, replicats, CSV loads, monitoring, and statistics.",
    },
    {
        "name": "MigDB Initial Load Extract Info",
        "description": "Status of initial load extract processes.",
    },
    {
        "name": "MigDB Homogeneous DataPump",
        "description": "DataPump export/import jobs, transfers, monitoring, and troubleshooting.",
    },
    {
        "name": "MigDB Job Management",
        "description": "Job directory and configuration file creation.",
    },
    {
        "name": "MigDB Metadata",
        "description": "Table metadata file download and apply-to-target operations.",
    },
    {
        "name": "MigDB Database",
        "description": "Database connections, CDB/PDB checks, table lists, supplemental log info, and prechecks.",
    },
    {
        "name": "MigDB Software Management",
        "description": "Download, upload, install, and patch MigDB software; gold image creation.",
    },
    {
        "name": "MigDB Logs",
        "description": "Error log reading and parsing.",
    },
    {
        "name": "MigDB CDC Info",
        "description": "CDC version information.",
    },
    {
        "name": "MigDB Connection",
        "description": "Deployment connections, logins, and cross-deployment job records.",
    },
    {
        "name": "MigDB Assessment",
        "description": "Oracle to RDS migration assessments, reports, and RDS recommendations.",
    },
    {
        "name": "MigDB ComparePad Agent Management",
        "description": "ComparePad agents, credentials, and connection verification.",
    },
]

from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

@app.get("/docs", include_in_schema=False)
async def custom_docs():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="MigDB API Docs")

@app.get("/redoc", include_in_schema=False)
async def custom_redoc():
    return get_redoc_html(openapi_url="/openapi.json", title="MigDB API Docs")


import hmac
import hashlib
import httpx
import base64
from datetime import datetime
from pydantic import BaseModel, Field, model_validator ,field_validator


# ── Config ──
JIRA_BASE_URL    = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL       = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN   = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

RISK_EVENT_CODES = {
    "AWS_RISK_CREDENTIALS_COMPROMISED": {
        "summary":  "Compromised credentials detected",
        "severity": "CRITICAL",
    },
    "AWS_RISK_CREDENTIALS_EXPOSED": {
        "summary":  "Exposed credentials detected",
        "severity": "CRITICAL",
    },
}


class AWSHealthDetail(BaseModel):
    eventArn:           Optional[str]  = ""
    eventTypeCode:      Optional[str]  = ""
    eventTypeCategory:  Optional[str]  = ""
    service:            Optional[str]  = ""
    statusCode:         Optional[str]  = ""
    startTime:          Optional[str]  = ""
    affectedResources:  Optional[list] = []
    eventDescription:   Optional[list] = []
    affectedEntities:   Optional[list] = []

class AWSEventBridgeEvent(BaseModel):
    version:     Optional[str]  = ""
    id:          Optional[str]  = ""
    source:      Optional[str]  = ""
    account:     Optional[str]  = ""
    time:        Optional[str]  = ""
    region:      Optional[str]  = ""
    detail:      Optional[dict] = {}
    detail_type: Optional[str]  = Field("", alias="detail-type")

    class Config:
        populate_by_name = True

def parse_and_enrich(event: AWSEventBridgeEvent) -> dict:
    detail     = event.detail or {}
    event_code = detail.get("eventTypeCode", "UNKNOWN")
    meta       = RISK_EVENT_CODES.get(event_code, {
        "summary":  f"AWS RISK event: {event_code}",
        "severity": "HIGH",
    })

    descriptions      = detail.get("eventDescription", [])
    desc_text         = descriptions[0].get("latestDescription", "No description provided.") if descriptions else "No description provided."
    entities          = detail.get("affectedEntities", []) or detail.get("affectedResources", [])
    affected_list     = [e.get("entityValue", e) if isinstance(e, dict) else e for e in entities]

    return {
        "event_code":        event_code,
        "account_id":        event.account or "Unknown",
        "region":            event.region  or "Unknown",
        "event_time":        event.time    or datetime.utcnow().isoformat(),
        "severity":          meta["severity"],
        "summary":           meta["summary"],
        "desc_text":         desc_text,
        "affected_list":     affected_list,
        "jira_priority":     "Highest",
        "labels":            ["security", "aws-risk", "credentials", "auto-generated"],
    }

def _jira_headers() -> dict:
    token = base64.b64encode(
        f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()
    ).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

async def create_jira_ticket(enriched: dict) -> dict:
    affected_text = "\n".join(
        [f"• {r}" for r in enriched["affected_list"]]
    ) or "No specific resources listed"

    payload = {
        "fields": {
            "project":     {"key": JIRA_PROJECT_KEY},
            "issuetype":   {"name": "Bug"},
            "summary":     f"🚨 [AWS RISK] {enriched['event_code']} — Account {enriched['account_id']}",
            "priority":    {"name": enriched["jira_priority"]},
            "labels":      enriched["labels"],
            "description": {
                "type": "doc", "version": 1,
                "content": [
                    {"type": "heading", "attrs": {"level": 2},
                     "content": [{"type": "text", "text": "AWS Health Security Alert"}]},

                    {"type": "paragraph", "content": [
                        {"type": "text", "text": "Event Code: ",  "marks": [{"type": "strong"}]},
                        {"type": "text", "text": enriched["event_code"]}]},
                    {"type": "paragraph", "content": [
                        {"type": "text", "text": "Severity: ",    "marks": [{"type": "strong"}]},
                        {"type": "text", "text": enriched["severity"]}]},
                    {"type": "paragraph", "content": [
                        {"type": "text", "text": "AWS Account: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": enriched["account_id"]}]},
                    {"type": "paragraph", "content": [
                        {"type": "text", "text": "Region: ",      "marks": [{"type": "strong"}]},
                        {"type": "text", "text": enriched["region"]}]},
                    {"type": "paragraph", "content": [
                        {"type": "text", "text": "Event Time: ",  "marks": [{"type": "strong"}]},
                        {"type": "text", "text": enriched["event_time"]}]},

                    {"type": "heading", "attrs": {"level": 3},
                     "content": [{"type": "text", "text": "Description"}]},
                    {"type": "paragraph", "content": [
                        {"type": "text", "text": enriched["desc_text"]}]},

                    {"type": "heading", "attrs": {"level": 3},
                     "content": [{"type": "text", "text": "Affected Resources"}]},
                    {"type": "paragraph", "content": [
                        {"type": "text", "text": affected_text}]},

                    {"type": "heading", "attrs": {"level": 3},
                     "content": [{"type": "text", "text": "Immediate Actions Required"}]},
                    {"type": "bulletList", "content": [
                        {"type": "listItem", "content": [{"type": "paragraph", "content": [
                            {"type": "text", "text": "Rotate all potentially compromised credentials immediately"}]}]},
                        {"type": "listItem", "content": [{"type": "paragraph", "content": [
                            {"type": "text", "text": "Review CloudTrail logs for unauthorized access"}]}]},
                        {"type": "listItem", "content": [{"type": "paragraph", "content": [
                            {"type": "text", "text": "Check IAM users/roles for suspicious activity"}]}]},
                        {"type": "listItem", "content": [{"type": "paragraph", "content": [
                            {"type": "text", "text": "SLA: Respond and remediate within 1 hour"}]}]},
                    ]}
                ]
            }
        }
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{JIRA_BASE_URL}/rest/api/3/issue",
            json=payload,
            headers=_jira_headers(),
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        key  = data.get("key", "UNKNOWN")
        return {
            "ticket_id":  key,
            "ticket_url": f"{JIRA_BASE_URL}/browse/{key}",
        }

async def notify_slack(enriched: dict, jira_url: str):
    affected = "\n".join(
        [f"• {r}" for r in enriched["affected_list"]]
    ) or "No specific resources listed"

    message = {
        "text": f":rotating_light: *P1 Security Alert — {enriched['event_code']}*",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text",
                         "text": f"🚨 P1 Security Alert: {enriched['event_code']}"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Severity:*\n{enriched['severity']}"},
                    {"type": "mrkdwn", "text": f"*AWS Account:*\n{enriched['account_id']}"},
                    {"type": "mrkdwn", "text": f"*Region:*\n{enriched['region']}"},
                    {"type": "mrkdwn", "text": f"*Detected:*\n{enriched['event_time']}"},
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn",
                         "text": f"*Description:*\n{enriched['desc_text']}"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn",
                         "text": f"*Affected Resources:*\n{affected}"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Jira Ticket:*\n<{jira_url}|{jira_url.split('/')[-1]}>"},                    
                ]
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn",
                         "text": ":alarm_clock: *SLA: Respond and remediate within 1 hour*"}
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        await client.post(
            SLACK_WEBHOOK_URL,
            json=message,
            timeout=5.0
        )

@app.post(
    "/api/v2/aws/health-webhook", include_in_schema=False,
    tags=["AWS Security"],
    summary="Receive AWS Health RISK events from EventBridge",
    description="Receives AWS_RISK_CREDENTIALS_COMPROMISED and AWS_RISK_CREDENTIALS_EXPOSED events from Amazon EventBridge, creates a high-priority Jira ticket and sends Slack alert.",
    operation_id="aws_health_webhook"
)
async def aws_health_webhook(request: Request) -> dict:

    raw_body = await request.body()

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    
    msg_type = body.get("Type", "")

    if msg_type == "SubscriptionConfirmation":
        confirm_url = body.get("SubscribeURL", "")
        if confirm_url:
            async with httpx.AsyncClient() as client:
                await client.get(confirm_url)
        return {"status": "confirmed"}

    if msg_type == "Notification":
        import json as json_lib
        try:
            message = json_lib.loads(body.get("Message", "{}"))
        except Exception:
            return {"status": "skipped", "message": "Could not parse SNS message"}

        event_code = message.get("detail", {}).get("eventTypeCode", "")

        # Skip non-RISK events
        if not event_code.startswith("AWS_RISK"):
            return {
                "status":  "skipped",
                "message": f"Event {event_code} is not a RISK event"
            }

        try:
            event = AWSEventBridgeEvent(
                version=message.get("version", ""),
                id=message.get("id", ""),
                source=message.get("source", ""),
                account=message.get("account", ""),
                time=message.get("time", ""),
                region=message.get("region", ""),
                detail=message.get("detail", {}),
                **{"detail-type": message.get("detail-type", "")}
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Event parse error: {str(e)}")

        enriched = parse_and_enrich(event)

        try:
            ticket = await create_jira_ticket(enriched)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500,
                detail=f"Jira ticket creation failed: {e.response.text}")

        try:
            await notify_slack(enriched, ticket["ticket_url"])
        except Exception as e:
            logger.error(f"Slack notification failed (non-critical): {str(e)}")

        return {
            "status":     "success",
            "message":    f"Ticket created and Slack notified for {event_code}",
            "ticket_id":  ticket["ticket_id"],
            "ticket_url": ticket["ticket_url"],
            "event_code": event_code,
            "account_id": enriched["account_id"],
            "region":     enriched["region"],
            "severity":   enriched["severity"],
        }

    return {"status": "ignored", "type": msg_type}

@app.post(
    "/api/v2/aws/test-risk-alert", include_in_schema=False,
    tags=["AWS Security"],
    summary="Manually test AWS RISK alert → Jira + Slack",
    description="Simulates an AWS Health RISK event to verify Jira ticket creation and Slack notification.",
    operation_id="test_risk_alert"
)
async def test_risk_alert() -> dict:
    fake_event = AWSEventBridgeEvent(
        version="0",
        id="test-event-123",
        source="aws.health",
        account="123456789012",
        time=datetime.utcnow().isoformat(),
        region="ap-south-1",
        **{"detail-type": "AWS Health Event"},
        detail={
            "eventTypeCode":     "AWS_RISK_CREDENTIALS_EXPOSED",
            "eventTypeCategory": "risk",
            "service":           "IAM",
            "statusCode":        "open",
            "eventDescription":  [
                {"latestDescription": "Test: AWS credentials were exposed in a public repository."}
            ],
            "affectedEntities": [
                {"entityValue": "arn:aws:iam::123456789012:user/test-user",
                 "statusCode":  "IMPAIRED"}
            ]
        }
    )

    enriched = parse_and_enrich(fake_event)

    try:
        ticket = await create_jira_ticket(enriched)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500,
            detail=f"Jira failed: {e.response.text}")

    try:
        await notify_slack(enriched, ticket["ticket_url"])
    except Exception as e:
        logger.error(f"Slack failed: {e}")

    return {
        "status":     "success",
        "ticket_id":  ticket["ticket_id"],
        "ticket_url": ticket["ticket_url"],
        "event_code": "AWS_RISK_CREDENTIALS_EXPOSED",
        "account_id": enriched["account_id"],
        "region":     enriched["region"],
        "severity":   enriched["severity"],
    }
    #return await aws_health_webhook(fake_event)


OSPlatBit = platform.processor()
OSPlat = platform.system()
sshTimeOut = 120
ssh_timeout = int(os.environ.get("SSH_TIMEOUT", "60")) 

DB_PATH    = os.environ.get("CONN_DB", "conn.db")
DATETIME_FMT = "%Y-%m-%d:%H:%M:%S"

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''select file from CONFIG''')
    db_row = cursor.fetchone()
    if db_row:
       config_file = db_row[0]
    else:
        raise ValueError("No config file entry found in CONFIG table.")
except Exception as e:
    raise RuntimeError(f"Error retrieving config file from DB: {e}")
finally:
    if conn:
       cursor.close()
       conn.close()
       
config = configparser.RawConfigParser()
if not os.path.exists(config_file):
    raise FileNotFoundError(f"Missing config file: {config_file}")
config.read(config_file)

agent_base = config.get('AGENT_CONFIG','BASE_DIR')
agent_home = config.get('AGENT_CONFIG','HOME_DIR')
agent_log = os.path.join(agent_home,'.log')
gg_home = os.path.join('/cdc_home','app')
db_home = os.path.join('/cdc_home','db')
#gg_home = os.path.join('/home/skylift/gg')
#db_home = os.path.join('/home/skylift/db')
rac_check = 'N'
agent_host = config.get('AGENT_CONFIG','AGENT_HOST')
agent_port = config.get('AGENT_CONFIG','SERVER_PORT')
ssl_verify = config.get('AGENT_CONFIG', 'SSL_VERIFY')
trailPath = os.path.join('/cdc_data','TRAILS')
trail_path=trailPath
xfr_batch_size = config.get('AGENT_CONFIG','XFR_BATCH_SIZE')
local_efs_dir = config.get('AGENT_CONFIG','LOCAL_EFS_DIR')
split_qualify_size = config.get('AGENT_CONFIG','SPLIT_QUALIFY_SIZE')
exp_encrypt_passwd = config.get('AGENT_CONFIG','EXP_ENCRYPT_PASSWD')
exp_encrypt_algo = config.get('AGENT_CONFIG','EXP_ENCRYPT_ALGO')
OPlace_Debug=config.get('AGENT_CONFIG','AGENT_DEBUG')
image_uploads = os.path.join(agent_base,'images')
processing_dir = os.path.join(agent_base,'processing')
temp_dir = os.path.join(agent_base,'tempdir')


license_path = os.path.join(agent_base,'.license.json')

load_license(license_path,verify_aws=False)

if not os.path.exists(image_uploads): os.makedirs(image_uploads)
if not os.path.exists(processing_dir): os.makedirs(processing_dir)
if not os.path.exists(temp_dir): os.makedirs(temp_dir)
if not os.path.exists(agent_log): os.makedirs(agent_log)

hName = socket.gethostname()
hName = hName.split('.')
hName = hName[0]

gg_exclude_logo_pattern = re.compile(r'^\s*(?:Oracle GoldenGate|Copyright|ggsci|Version \d+|Oracle Linux)', re.IGNORECASE)


# Precompile patterns globally
GG_REPLACE_PATTERN = re.compile(r'Oracle GoldenGate', re.IGNORECASE)
GG_EXCLUDE_PATTERN = re.compile(r'^\s*(?:Copyright|Version \d+|Oracle Linux|Oracle GoldenGate)', re.IGNORECASE)
OGG_REPLACE_PATTERN = re.compile(r'OGG-', re.IGNORECASE)
CREDSTORE_REPLACE_PATTERN = re.compile(r'credential\s*store?', re.IGNORECASE)
GGSCI_REPLACE_PATTERN = re.compile(r'GGSCI', re.IGNORECASE)

SYSTEM_TABLESPACES = ('SYSTEM', 'SYSAUX', 'TEMP', 'UNDOTBS1', 'UNDOTBS2', 'USERS')
SYSTEM_SCHEMAS = [
    # Core/base
    'SYS', 'SYSTEM', 'OUTLN', 'DBSNMP', 'PUBLIC', 'ANONYMOUS', 'SYSMAN',

    # Security / auditing / label security / vault
    'AUDSYS', 'DVSYS', 'DVF', 'LBACSYS', 'OJVMSYS',
    'SYS$UMF', 'GSMCATUSER', 'GSMUSER', 'GSMROOTUSER', 'GSMADMIN_INTERNAL',
    'SYSBACKUP', 'SYSDG', 'SYSKM', 'SYSRAC',
    'DBSFWUSER', 'REMOTE_SCHEDULER_AGENT',

    # XML / context / text / spatial / multimedia
    'XDB', 'XDB$', 'XS$NULL', 'CTXSYS', 'MDSYS', 'MDDATA',
    'ORDSYS', 'ORDDATA', 'ORDPLUGINS', 'SI_INFORMTN_SCHEMA',
    'SPATIAL_CSW_ADMIN_USR', 'SPATIAL_WFS_ADMIN_USR',

    # Workspace manager / replication
    'WMSYS', 'GGSYS', 'GGADMIN', 'GSMADMIN_INTERNAL',

    # Analytics / OLAP / stats / performance
    'OLAPSYS', 'EXFSYS', 'DBSNMP', 'APPQOSSYS', 'WK_TEST', 'WKSYS', 'WKPROXY',

    # ORACLE_OCM / diagnostics
    'ORACLE_OCM', 'DIP',

    # Application Express (if installed)
    'APEX_040000', 'APEX_050000', 'APEX_180200', 'APEX_190200', 'APEX_030200',
    'APEX_200100', 'APEX_210100', 'APEX_220100', 'APEX_PUBLIC_USER',
    'FLOWS_FILES', 'FLOWS_030000',

    # Multitenant / PDB seed related
    'PDBADMIN',

    # Data pump / scheduler
    'DBMS_SCHEDULER', 'ORACLE_OCM',
]

def get_internal_headers(extra_headers: dict | None = None) -> dict:
    """Build headers for server-to-server MigDB API calls, including a signed internal token."""
    internal_token = create_access_token({"sub": "system", "scope": "internal"})
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {internal_token}",
    }
    if extra_headers:
        headers.update(extra_headers)
    return headers

_GGSCI_PROMPT_RE = re.compile(
    r'^GGSCI\s*\([^)]*\)\s*\d+>\s*',
    re.IGNORECASE
)


def clean_gg_log(lines: Iterator[str]) -> Iterator[str]:
    for line in lines:
        # Skip unwanted lines
       if GG_EXCLUDE_PATTERN.search(line):
          continue
       line = _GGSCI_PROMPT_RE.sub('', line)

       if not line.strip():
            continue
       line = GG_REPLACE_PATTERN.sub("MigDB", line)
       # Replace OGG- → CDC-
       line = OGG_REPLACE_PATTERN.sub("CDC-", line)
       line = CREDSTORE_REPLACE_PATTERN.sub("Secure Vault", line)
       line = GGSCI_REPLACE_PATTERN.sub("MigDB", line)
       yield line.rstrip()


if os.path.exists(os.path.join(db_home, 'lib')):
    lib_path = os.path.join(db_home, 'lib')
else:
    lib_path = db_home

#os.environ['LD_LIBRARY_PATH'] = lib_path
oracledb.init_oracle_client(lib_dir=db_home)

logdump_bin=os.path.join(gg_home,'.clilog')
ggsci_bin = os.path.join(gg_home,'adminsrvr')
#ggsci_bin = os.path.join(gg_home,'adminsrvr')


LOG_FORMAT = "[%(asctime)s] %(levelname)s - %(message)s"
logging.basicConfig(filename=os.path.join(agent_home, 'agent_error.log'), level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.INFO if OPlace_Debug == "Y" else logging.WARNING)

gg_cache      = ""
gg_cache_lock = threading.Lock()
POOL_SIZE = 3

_GGSCI_COMMANDS = {
    'extract':  "info extract *",
    'replicat': "info replicat *",
    'mgr':      "info mgr",
}
 
_ggsci_procs: dict = {}
_ggsci_locks: dict = {k: threading.Lock() for k in _GGSCI_COMMANDS}
_GGSCI_DONE_RE = re.compile(r'GGSCI\s*\([^)]*\)\s*\d+>\s*$')

class _GgsciPtyProc:
    """A GGSCI process attached to a pty instead of a plain pipe.
    Plain pipes make GGSCI fully block-buffer its output (since it's not a
    real terminal), so long 'info extract *' / 'info replicat *' listings
    can arrive truncated depending on timing. A pty makes it line-buffer
    like a normal interactive CLI, fixing truncated/partial results."""
 
    def __init__(self):
        master_fd, slave_fd = pty.openpty()
        self.proc = subprocess.Popen(
            [ggsci_bin],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
        )
        os.close(slave_fd)
        self.master_fd = master_fd
        time.sleep(0.3)
        self._drain(wait=0.3)
 
    def _drain(self, wait=0.05):
        while True:
            r, _, _ = select.select([self.master_fd], [], [], wait)
            if not r:
                return
            try:
                chunk = os.read(self.master_fd, 65536)
            except OSError:
                return
            if not chunk:
                return
 
    def write(self, text: str):
        os.write(self.master_fd, text.encode())
 
    def poll(self):
        return self.proc.poll()
 
    def kill(self):
        try:
            self.proc.kill()
        except Exception:
            pass
        try:
            os.close(self.master_fd)
        except OSError:
            pass

def create_ggsci_process():
    """Kept for backward compatibility with any other callers."""
    return _GgsciPtyProc()

def start_ggsci_pool():
    """Spawn one dedicated, persistent GGSCI process per command type."""
    for key in _GGSCI_COMMANDS:
        _ggsci_procs[key] = _GgsciPtyProc()

def _run_ggsci_dedicated(key: str, cmd: str, timeout: int = 30, idle_settle: float = 0.5):
    lock = _ggsci_locks[key]
    with lock:
        pp = _ggsci_procs.get(key)
        if pp is None or pp.poll() is not None:
            pp = _GgsciPtyProc()
            _ggsci_procs[key] = pp
 
        pp._drain(wait=0.05)
 
        try:
            pp.write(cmd + "\n")
        except OSError:
            pp = _GgsciPtyProc()
            _ggsci_procs[key] = pp
            pp.write(cmd + "\n")
 
        buf_parts = []
        deadline = time.time() + timeout
        last_data_time = time.time()
 
        while time.time() < deadline:
            r, _, _ = select.select([pp.master_fd], [], [], 0.2)
            if r:
                try:
                    chunk = os.read(pp.master_fd, 65536)
                except OSError:
                    pp.kill()
                    _ggsci_procs[key] = _GgsciPtyProc()
                    return None
                if not chunk:
                    pp.kill()
                    _ggsci_procs[key] = _GgsciPtyProc()
                    return None
                buf_parts.append(chunk)
                last_data_time = time.time()
                continue
 
            if buf_parts and (time.time() - last_data_time) >= idle_settle:
                tail = b"".join(buf_parts)[-200:].decode(errors="ignore")
                if _GGSCI_DONE_RE.search(tail):
                    return "".join(p.decode(errors="ignore") for p in buf_parts)
 
        logger.warning(f"processCheckDemand: '{key}' command timed out, recreating process")
        pp.kill()
        _ggsci_procs[key] = _GgsciPtyProc()
        return None


# ─────────────────────────────────────────────
# Cache Collection
# ─────────────────────────────────────────────

def processCheckDemand():
    """Fetch all GG info in parallel (dedicated pty processes) and write to cache + file."""
    global gg_cache
 
    results = {}
    with ThreadPoolExecutor(max_workers=len(_GGSCI_COMMANDS)) as executor:
        futures = {
            executor.submit(_run_ggsci_dedicated, key, cmd): key
            for key, cmd in _GGSCI_COMMANDS.items()
        }
        for future in as_completed(futures):
            key = futures[future]
            results[key] = future.result()
 
    if any(v is None for v in results.values()):
        logger.warning(f"processCheckDemand: incomplete GGSCI output this cycle: "
                        f"{[k for k, v in results.items() if v is None]}")
        return
 
    result   = results['extract'] + results['replicat'] + results['mgr']
    out_path = os.path.join(agent_log, 'infoall')
 
    with tempfile.NamedTemporaryFile('w', dir=agent_log, delete=False) as tmp:
        tmp.write(result)
        tmp_path = tmp.name
    os.replace(tmp_path, out_path)
 
    with gg_cache_lock:
        gg_cache = result

def processCheckAll():
    """Background loop — refresh cache every 10 seconds."""
    while True:
        try:
            processCheckDemand()
        except Exception as e:
            logger.error(f"MigDB error: {e}")
        time.sleep(10)

"""Start the GGSCI pool and launch the background refresh loop."""
start_ggsci_pool()
t = threading.Thread(target=processCheckAll, daemon=True)
t.start()

def get_directory_path(tgtdbName: str, dirName: str) -> str | None:
    """Resolve a directory object to its filesystem path on the target DB."""
    con = None
    try:
        con = selectConn(tgtdbName)[0]
        cur = con.cursor()
        cur.execute(
            "SELECT directory_path FROM all_directories "
            "WHERE directory_name = UPPER(:d)",
            d=dirName,
        )
        row = cur.fetchone()
        cur.close()
        return row[0] if row else None
    except Exception as exc:
        logger.error(f"Failed to resolve directory {dirName} on {tgtdbName}: {exc}")
        return None
    finally:
        if con:
            try: con.close()
            except Exception: pass

def _extract_efs_fsid(path: str) -> str | None:
    """Pull the EFS filesystem id (fs-xxxxxxxx...) out of a directory path,
    regardless of whether it's a local mount point or an RDS '/rdsefs-...' path."""
    if not path:
        return None
    m = re.search(r'fs-[0-9a-f]{8,}', path.lower())
    return m.group(0) if m else None

def is_efs_path(dir_path: str) -> bool:
    return dir_path.startswith("/rdsefs-") or dir_path.startswith("/migdb-efs")

#def is_efs_path(dir_path: str) -> bool:
#    return bool(_extract_efs_fsid(dir_path))

def transfer_dumpFile_efs(srcdbName, jobName, srcDumpDir, fileName,
                          cdbCheck, pdbName, local_tgt_dir):
    conSrc, cursorSrc, src_bfile = None, None, None
    LOCAL_READ_SIZE = 32 * 1024 * 1024
    speed_log = os.path.join(agent_home, jobName, fileName + '_speed')
    bytes_written, elapTime, xfrSpeed = 0, 0.001, 'UNKNOWN'
    tgt_path = os.path.join(local_tgt_dir, fileName)
    try:
        conSrc = selectConn(srcdbName)[0]
        cursorSrc = conSrc.cursor()
        if cdbCheck == 'YES' and len(pdbName) > 0:
            cursorSrc.execute(f'alter session set container={pdbName}')
            cursorSrc.close()
            cursorSrc = conSrc.cursor()

        bfile_var = cursorSrc.var(oracledb.DB_TYPE_BFILE)
        cursorSrc.execute("BEGIN :bfile := BFILENAME(:dir, :fname); END;",
                          bfile=bfile_var, dir=srcDumpDir, fname=fileName)
        src_bfile = bfile_var.getvalue()
        if not src_bfile.fileexists():
            logger.error(f'{fileName}: source BFILE does not exist in {srcDumpDir}')
            return
        src_bfile.open()
        f_len = src_bfile.size()
        if f_len == 0:
            logger.error(f'{fileName}: source BFILE is empty')
            return
        with open(os.path.join(agent_home, jobName, fileName + '_Size.log'), 'w') as f:
            f.write(f'{fileName} - {f_len}')

        startTime = time.time()
        read_offset = 1
        with open(tgt_path, 'wb') as out:          # truncates any leftover file
            while read_offset <= f_len:
                read_size = min(LOCAL_READ_SIZE, f_len - read_offset + 1)
                local_buffer = src_bfile.read(read_offset, read_size)
                if not local_buffer:
                    logger.warning(f'{fileName}: empty read at offset {read_offset}')
                    break
                out.write(local_buffer)
                read_offset   += len(local_buffer)
                bytes_written += len(local_buffer)

                elapTime = max(time.time() - startTime, 0.001)
                tp  = (bytes_written / (1024*1024)) / elapTime
                eta = ((f_len - bytes_written) / (1024*1024)) / tp if tp > 0 else 0
                xfrSpeed = f'{round(tp*1024)} KB/s' if tp < 1 else f'{round(tp)} MB/s'
                per = round(bytes_written / f_len * 100, 2)
                with open(speed_log, 'w') as f:
                    f.write(f'{per}${round(elapTime,2)}${xfrSpeed}${f_len}${bytes_written}${round(eta)}')

        src_bfile.close(); src_bfile = None
        tgt_size = os.path.getsize(tgt_path)
        if tgt_size == f_len:
            try:
               os.chmod(tgt_path, 0o777)
            except OSError as exc:
               logger.warning(f'{fileName}: could not chmod {tgt_path}: {exc}')
            with open(speed_log, 'w') as f:
                f.write(f'100${round(elapTime,2)}${xfrSpeed}${f_len}${bytes_written}$0')
            logger.info(f'{fileName}: EFS transfer verified OK — {tgt_size} bytes')
        else:
            raise ValueError(f'{fileName}: size mismatch — expected {f_len}, got {tgt_size}')
    except Exception as e:
        logger.error(f'{fileName}: EFS transfer failed — {e}')
        _cleanup_failed_transfer(agent_home, jobName, fileName)
        with open(os.path.join(agent_home, jobName, jobName + '_RDS_Transfer.log'), 'a') as f:
            f.write(f'{fileName} - {e}\n')
    finally:
        if src_bfile is not None:
            try: src_bfile.close()
            except Exception: pass
        if cursorSrc:
            try: cursorSrc.close()
            except Exception: pass
        if conSrc:
            try: conSrc.close()
            except Exception: pass


def transfer_dumpFile(srcdbName, jobName, srcDumpDir, fileName, cdbCheck, pdbName, tgtdbName, tgtDumpDir):
    conSrc    = None
    conTgt    = None
    cursorSrc = None
    cursorTgt = None
    src_bfile = None
    out_file  = None

    LOCAL_READ_SIZE = 32767 * 64  # 2MB read from source BFILE
    UTL_CHUNK_SIZE  = 32767       # UTL_FILE.PUT_RAW hard limit

    speed_log  = os.path.join(agent_home, jobName, fileName + '_speed')
    xfrSpeed   = 'UNKNOWN'
    elapTime   = 0.001
    bytes_written = 0

    try:
        conSrc    = selectConn(srcdbName)[0]
        conTgt    = selectConn(tgtdbName)[0]
        cursorSrc = conSrc.cursor()
        cursorTgt = conTgt.cursor()

        # ── Container switch ──────────────────────────────────
        if cdbCheck == 'YES' and len(pdbName) > 0:
            cursorSrc.execute(f'alter session set container={pdbName}')
            cursorSrc.close()
            cursorSrc = conSrc.cursor()  # fresh cursor after container switch

        # ── Get source BFILE via PL/SQL block ─────────────────
        bfile_var = cursorSrc.var(oracledb.DB_TYPE_BFILE)
        cursorSrc.execute(
            "BEGIN :bfile := BFILENAME(:dir, :fname); END;",
            bfile=bfile_var, dir=srcDumpDir, fname=fileName
        )
        src_bfile = bfile_var.getvalue()

        if not src_bfile.fileexists():
            logger.error(f'{fileName}: source BFILE does not exist in {srcDumpDir}')
            return

        src_bfile.open()
        f_len = src_bfile.size()
        if f_len == 0:
            src_bfile.close()
            logger.error(f'{fileName}: source BFILE is empty')
            return

        logger.info(f'{fileName}: source size = {f_len} bytes')
        with open(os.path.join(agent_home, jobName, fileName + '_Size.log'), 'w') as f:
            f.write(f'{fileName} - {f_len}')

        # ── Remove existing target file ───────────────────────
        try:
            cursorTgt.execute(
                "BEGIN UTL_FILE.FREMOVE(:dir, :fname); END;",
                dir=tgtDumpDir, fname=fileName
            )
            logger.info(f'{fileName}: removed existing target file')
        except oracledb.DatabaseError as e:
            if e.args[0].code == 29283:
                pass  # file didn't exist — fine
            else:
                raise

        startTime = time.time()
        chunk_count = 0

        # ── Define Target Bulk Write Proc ─────────────────
        PLSQL_BULK_WRITE = """
                              DECLARE
                                    fh   UTL_FILE.FILE_TYPE;
                                    len  PLS_INTEGER := DBMS_LOB.GETLENGTH(:data);
                                    pos  PLS_INTEGER := 1;
                                    amt  PLS_INTEGER;
                              BEGIN
                                    fh := UTL_FILE.FOPEN(:dir, :fname, 'ab', 32767);   -- append binary
                              WHILE pos <= len
                              LOOP
                                          amt := LEAST(32767, len - pos + 1);
                                          UTL_FILE.PUT_RAW(fh, DBMS_LOB.SUBSTR(:data, amt, pos), FALSE);
                                          pos := pos + amt;
                                    END LOOP;
                                    UTL_FILE.FFLUSH(fh);
                                    UTL_FILE.FCLOSE(fh);
                              END;"""
        cursorTgt.setinputsizes(data=oracledb.DB_TYPE_BLOB, dir=None, fname=None)

        # ── Read 2MB from source → write in 32KB chunks to target
        read_offset = 1
        while read_offset <= f_len:
            # ── Read 2MB block from source BFILE ─────────────
            remaining_src = f_len - read_offset + 1
            read_size     = min(LOCAL_READ_SIZE, remaining_src)
            local_buffer  = src_bfile.read(read_offset, read_size)

            if not local_buffer:
                logger.warning(f'{fileName}: empty read at offset {read_offset}, stopping')
                break

            read_offset += len(local_buffer)

            # ── Write 2MB block in 32KB UTL_FILE chunks ───────
            cursorTgt.execute(PLSQL_BULK_WRITE, data=local_buffer, dir=tgtDumpDir, fname=fileName)
            bytes_written += len(local_buffer)

            # ── Progress update after every 2MB block ─────────
            endTime      = time.time()
            elapTime     = max(endTime - startTime, 0.001)
            tp           = (bytes_written / (1024 * 1024)) / elapTime
            remaining_mb = (f_len - bytes_written) / (1024 * 1024)
            eta          = remaining_mb / tp if tp > 0 else 0
            xfrSpeed     = f'{round(tp * 1024)} KB/s' if tp < 1 else f'{round(tp)} MB/s'
            per          = round(bytes_written / f_len * 100, 2)
            with open(speed_log, 'w') as f:
                f.write(f'{per}${round(elapTime,2)}${xfrSpeed}${f_len}${bytes_written}${round(eta)}')

        # ── Close source BFILE ────────────────────────────────
        src_bfile.close()
        src_bfile = None

        # ── Verify target size via PL/SQL block ───────────────
        tgt_var = cursorTgt.var(oracledb.DB_TYPE_BFILE)
        cursorTgt.execute(
            "BEGIN :bfile := BFILENAME(:dir, :fname); END;",
            bfile=tgt_var, dir=tgtDumpDir, fname=fileName
        )
        tgt_bfile = tgt_var.getvalue()
        tgt_bfile.open()
        tgt_size = tgt_bfile.size()
        tgt_bfile.close()

        if tgt_size == f_len:
            with open(speed_log, 'w') as f:
                f.write(f'100${round(elapTime,2)}${xfrSpeed}${f_len}${bytes_written}$0')
            logger.info(f'{fileName}: transfer verified OK — {tgt_size} bytes')
        else:
            raise ValueError(f'{fileName}: size mismatch — expected {f_len}, got {tgt_size}')

    except oracledb.DatabaseError as e:
        logger.error(f'{fileName}: Oracle DB error — {e}')
        _cleanup_failed_transfer(agent_home, jobName, fileName)

    except Exception as e:
        logger.error(f'{fileName}: transfer failed — {e}')
        _cleanup_failed_transfer(agent_home, jobName, fileName)
        with open(os.path.join(agent_home, jobName, jobName + '_RDS_Transfer.log'), 'a') as f:
            f.write(f'{fileName} - {e}\n')

    finally:
        if out_file is not None:
            try:
                cursorTgt.execute("BEGIN UTL_FILE.FCLOSE(:fh); END;", fh=out_file)
            except Exception:
                pass
        if src_bfile is not None:
            try:
                src_bfile.close()
            except Exception:
                pass
        for cursor in [cursorSrc, cursorTgt]:
            try:
                if cursor: cursor.close()
            except Exception:
                pass
        for con in [conSrc, conTgt]:
            try:
                if con: con.close()
            except Exception:
                pass

def _cleanup_failed_transfer(agent_home, jobName, fileName):
    """Remove the size log so the caller knows this file can be retried."""
    size_log = os.path.join(agent_home, jobName, fileName + '_Size.log')
    try:
        if os.path.exists(size_log):
            os.remove(size_log)
    except Exception as e:
        logger.warning(f'Could not remove size log for {fileName}: {e}')

def human_rate(sent: int, elapsed: float):
    """Return (value, unit) as KB/s or MB/s depending on speed."""
    if elapsed <= 0:
        return 0.0, "KB/s"
    bytes_per_s = sent / elapsed
    if bytes_per_s < 1024 * 1024:          # < 1 MB/s → show KB/s
        return bytes_per_s / 1024, "KB/s"
    else:                                   # ≥ 1 MB/s → show MB/s
        return bytes_per_s / (1024 * 1024) , "MB/s"

def upload_one_file(
    host: str,
    key_path: str,
    fileName: str,
    jobName: str
):
    if not os.path.isfile(fileName):
        raise FileNotFoundError(fileName)
    remote_dir = os.path.join(agent_home, jobName)
    # --- connect ---
    username="skylift"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username=username, key_filename=key_path)
    sftp = ssh.open_sftp()

    # ensure remote dir exists
    ssh.exec_command(f"mkdir -p {remote_dir}")

    f_len = os.path.getsize(fileName)
    dumpFile = fileName.split('/')[-1]
    with open(os.path.join(agent_home, jobName, f"{dumpFile}_RMT_Size.log"), 'w') as fp:
         fp.write(str(f_len))
    speed_path = os.path.join(agent_home, jobName,f"{dumpFile}_RMT_speed")
    remote_path = os.path.join(remote_dir,dumpFile)

    start = time.time()
    last_write = 0.0  # throttle to ~1s
    write_lock = threading.Lock()

    def atomic_write(path: str, data: str):
        # ensure parent exists (in case external cleanup happens)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # use a unique tmp file in same dir to guarantee atomic replace
        with tempfile.NamedTemporaryFile("w", dir=os.path.dirname(path), delete=False) as tf:
            tf.write(data)
            tmp_name = tf.name
        os.replace(tmp_name, path)

    def progress_cb(dumpFile, size, sent):
        nonlocal last_write
        elapsed = time.time() - start
        per = (sent / size * 100) if size  else 0
        xfr_speed,xfr_unit = human_rate(sent, elapsed)
        eta = ((f_len - sent) / (sent / elapsed)) if sent > 0 else 0
        tgt_size = 0
        try:
            st = sftp.stat(remote_path)
            tgt_size = int(getattr(st, "st_size", 0))
        except FileNotFoundError:
            tgt_size = 0
        except OSError:
            tgt_size = 0

        line = f"{per:.2f}${round(elapsed,2)}${xfr_speed:.2f} {xfr_unit}${f_len}${sent}${round(eta,2)}${tgt_size}"
        now = time.time()
        if (now - last_write) >= 1.0 or sent >= f_len:
            atomic_write(speed_path, line)
            last_write = now
    try:
        with SCPClient(ssh.get_transport(), progress=progress_cb) as scp:
            scp.put(fileName, remote_dir + "/")
    finally:
        ssh.close()

def download_dumpFile(jobName, dbName, bucketName, dirName):
    con = selectConn(dbName)
    con = con[0]
    try:
        download_File = """SELECT rdsadmin.rdsadmin_s3_tasks.download_from_s3(
                                   p_bucket_name    =>  :bucketName, 
                                   p_directory_name =>  :dirName) 
                            AS TASK_ID FROM DUAL"""
        db_row = con.execute(download_File, bucketName=bucketName, dirName=dirName)
        db_row = db_row.fetchone()
        if db_row:
            taskID = db_row[0]
            with open(os.path.join(agent_home, jobName, jobName + '_Download'), 'w') as infile:
                infile.write(taskID)
    except oracledb.DatabaseError as e:
        with open(os.path.join(agent_home, jobName, jobName + '_DownloadLog'), 'w') as infile:
            infile.write(str(e))
    finally:
        if con:
            con.close()


def ILGetStats(procName, jobName):
    while True:
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)
        ssh.stdin.write("stats " + procName + ' ,TOTAL,LATEST\n')
        ILProcStatRate, stderr = ssh.communicate(timeout=sshTimeOut)
        if 'ERROR' in ILProcStatRate:
            pass
        else:
            with open(os.path.join(agent_home, jobName, procName + 'Rate.lst'), 'w') as infile:
                infile.write(ILProcStatRate)
        time.sleep(30)
        if not os.path.exists(os.path.join(agent_home, jobName, procName + 'running')):
            break

#@app.get("/")
#def index():
#    return FileResponse("./migdb/web/index.html")

@app.get("/")
def root():
    return FileResponse(resource_path("web/index.html"))


def output_type_handler(cursor, name, defaultType, size, precision, scale):
    return cursor.var(oracledb.STRING, 255, arraysize=cursor.arraysize)


def dataframe_difference(df1, df2, which=None):
    """Find rows which are different between two DataFrames."""
    comparison_df = df1.merge(df2,
                              indicator=True,
                              how='outer')
    if which is None:
        diff_df = comparison_df[comparison_df['_merge'] != 'both']
    else:
        diff_df = comparison_df[comparison_df['_merge'] == which]
    return diff_df


def chmod_dir(path):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for f in files:
            os.chmod(os.path.join(root, f), 0o755)

class AESCipher:

    def __init__(self, key):
        self.key = hashlib.sha256(key.encode()).digest()[:16]
        self.iv = b'OnePlaceMyPlaceV'

    def encrypt(self, raw):
        raw_bytes = raw.encode('utf-8')
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(raw_bytes) + padder.finalize()
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(ct).decode('utf-8')

    def decrypt(self, enc):
        ct = base64.b64decode(enc)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plain = decryptor.update(ct) + decryptor.finalize()
        unpadder = sym_padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_plain) + unpadder.finalize()
        return data.decode('utf-8')
cipher = AESCipher('SkyliftMyPlaceJamboUrl111019808')

@app.get("/api/v2/migdb-dep-det",tags=["MigDB Deployment Details"] , summary="Get deployment details", description="Returns Host Name,Operating System Platform,CDC version, Oracle client version, and software home.")
def migdb_deployment_details():
    Client_Ver = ''
    try:
        GGVer = subprocess.check_output([ggsci_bin, '-v'], stderr=subprocess.STDOUT, universal_newlines=True)
        line = GGVer.splitlines()
        GGVer = line[2].split()[1]
        DBVer = line[3].split()
        if GGVer.startswith('21'):
            GGDBVer = DBVer[DBVer.index('Database') + 1]
            GGDBVer = 'Oracle ' + GGDBVer + ' and lower versions'
        else:
            GGDBVer = DBVer[DBVer.index('Oracle') + 1]
            GGDBVer = 'Oracle ' + GGDBVer
    except Exception as e:
        GGVer = 'Not Installed'
        GGDBVer = 'Not Installed'
        DBVer = 'Not Installed'
        logger.info(str(e))
    try:
        Client_Ver = oracledb.clientversion()
    except oracledb.DatabaseError as e:
        Client_Ver = 'Client Binary not Detected'
        logger.info(str(e))

    return [hName, OSPlat, OSPlatBit, Client_Ver, GGVer, GGDBVer, gg_home, db_home]

from functools import partial


def oplace_debug(filenames: list[str]) -> None:
    if OPlace_Debug == 'N':
        for name in filenames:
            if os.path.exists(os.path.join(agent_log, name)):
                os.remove(os.path.join(agent_log, name))

@app.get("/api/v2/cdcGetProcess",tags=["MigDB Extract Process Details"] , summary="Get Extract Process", description="Returns Extract Name and Trail name")
def cdc_get_process():
    return _run_gg_get_process()

def _run_gg_get_process():
    ExtTrail_Data = []

    ssh = subprocess.Popen(
        [ggsci_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0
    )
    ssh.stdin.write('info exttrail\n')
    InfoExt, _ = ssh.communicate(timeout=sshTimeOut)

    trail_file = os.path.join(agent_log, 'infotrail.out')
    with open(trail_file, mode='w') as outfile:
        outfile.write(InfoExt)

    with open(trail_file, mode='r') as infile:
        for line in infile:
            if 'Extract Trail' in line:
                TrailName = line.split(':', 1)[-1].strip()
            elif 'Extract' in line:
                ExtName = line.split(':', 1)[-1].strip()
                ExtTrail_Data.append({'id': ExtName, 'category': TrailName})

    oplace_debug(['infotrail.out'])
    return [ExtTrail_Data]


from pydantic import BaseModel

class ExtNameRequest(BaseModel):
    extname: str

@app.post("/api/v2/getExtTrailName",tags=["MigDB Extract Trail from Name"] , summary="Get Extract Trails from Extract Name" , description="Returns Extract Trail name from Extract Name")
def get_extract_trail_name(body: ExtNameRequest):
    Trail_Data = []

    ssh = subprocess.Popen(
        [ggsci_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0
    )
    ssh.stdin.write('info ' + body.extname + ' , showch' + '\n')
    infoExtTrail, stderr = ssh.communicate(timeout=sshTimeOut)

    trail_file = os.path.join(agent_log, 'infoextnametrail.out')
    with open(trail_file, mode='w') as outfile:
        outfile.write(infoExtTrail)

    with open(trail_file, mode='r') as infile:
        for line in infile:
            if 'Extract Trail' in line:
                TrailName = line.split(':', 1)[-1].strip()
                Trail_Data.append(TrailName)

    oplace_debug(['infoextnametrail.out'])
    return [Trail_Data]

def _ggscicmd(cmds: str, timeout: int = 60) -> List[str]:    
    stdin_payload = cmds + "\n" 
    proc = subprocess.Popen(
        [ggsci_bin],
        stdin =subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0,
    )
    stdout, _ = proc.communicate(           
        input=stdin_payload,
        timeout=timeout,
    )
    return [l for l in stdout.splitlines() if l.strip()]


class TrailItem(BaseModel):
    label:   str
    value:   str
    extract: str = ""
    type:    str = "LOCAL"

@app.get("/api/v2/trails", tags=["MigDB CDC Trail Analysis"],
    response_model=List[TrailItem],
    summary="Get all MigDB CDC trail file paths",
    description=(
        "Returns all trail paths from MigDB CDC for the trail path dropdown. "
        "Called by JS **getExtracts()** on page load to populate **trailpathDP**. "
        "Tries three methods in order: "
        "**1** `INFO EXTRACT *, DETAIL` (most complete), "
        "**2** `INFO EXTTRAIL *` / `INFO RMTTRAIL *`, "
        "**3** filesystem scan of the `dirdat/` directory. "
        "Falls back to mock data when GGSCI binary is not installed."
    ),
)
async def get_trails() -> List[TrailItem]:
    seen: set            = set()
    trails: List[TrailItem] = []
 
    current = ""
    for line in _ggscicmd("INFO EXTRACT *, DETAIL\nEXIT\n", timeout=60):
        m = re.match(r"^EXTRACT\s+(\w+)", line.strip(), re.IGNORECASE)
        if m:
            current = m.group(1)
 
        lm = re.search(r"Extract Trail[:\s]+([\./\\\w\-]+)", line, re.IGNORECASE)
        if lm:
            path = lm.group(1).strip().rstrip(",")
            if path not in seen:
                seen.add(path)
                trails.append(TrailItem(
                    label   = f"{path}  ({current})" if current else path,
                    value   = path,
                    extract = current,
                    type    = "LOCAL",
                ))
 
        rm = re.match(r"\s+([\./\\\w\-]{4,})\s+\d+\s+\d+", line)
        if rm and current:
            path = rm.group(1).strip()
            if ("/" in path or "\\" in path) and path not in seen:
                seen.add(path)
                trails.append(TrailItem(
                    label   = f"{path}  ({current})",
                    value   = path,
                    extract = current,
                    type    = "REMOTE",
                ))
    if trails:
        logger.info("trails via extract detail: %d found", len(trails))
        return trails
 
    for line in _ggscicmd("INFO EXTTRAIL *\nINFO RMTTRAIL *\nEXIT\n"):
        m = re.match(r"\s+([\./\\\w\-]{4,})\s+(\w+)\s+\d+\s+\d+", line)
        if m:
            path, ext = m.group(1).strip(), m.group(2)
            if path not in seen:
                seen.add(path)
                trails.append(TrailItem(
                    label=f"{path}  ({ext})", value=path, extract=ext,
                ))
    if trails:
        logger.info("trails via exttrail: %d found", len(trails))
        return trails
 
    logger.warning("GGSCI not found — returning mock trail paths")
    return [
        TrailItem(label="./dirdat/lt  (EXT1)",  value="./dirdat/lt",  extract="EXT1"),
        TrailItem(label="./dirdat/rp  (PUMP1)", value="./dirdat/rp",  extract="PUMP1", type="REMOTE"),
        TrailItem(label="./dirdat/rt  (EXT2)",  value="./dirdat/rt",  extract="EXT2"),
        TrailItem(label="./dirdat/aa  (DPUMP)", value="./dirdat/aa",  extract="DPUMP", type="REMOTE"),
    ]

class MgrPrmLine(BaseModel):
    lineNo:  int = Field(..., description="1-based line number")
    content: str = Field(..., description="Raw line text from mgr.prm")

class MgrPrmResponse(BaseModel):
    path:    str            = Field(..., description="Absolute path to mgr.prm on disk")
    exists:  bool           = Field(..., description="Whether mgr.prm currently exists")
    lines:   List[str]      = Field(..., description="Each raw line — JS loops over this")
    content: str            = Field(..., description="Full file as single string")


@app.get("/api/v2/mgrprm", tags=["MigDB Parameter Management"],
    response_model=MgrPrmResponse,
    summary="Get mgr.prm file contents",
    description=(
        "Returns all lines of the Manager parameter file. "
        "Called by JS **getMgrPrm()** on page load. "
        "JS reads **data.lines[]** (same loop pattern as getExtracts), "
        "**data.content** for the syntax preview box, "
        "and **data.exists** to show/hide an empty-state message."
    ),
)
async def get_mgrprm() -> MgrPrmResponse:
    param_directory = os.path.join(gg_home, "dirprm")   # same as list_prm_files
    mgr_prm_path    = os.path.join(param_directory, "mgr.prm")

    exists  = os.path.isfile(mgr_prm_path)
    content = ""

    if exists:
        with open(mgr_prm_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

    lines = content.splitlines() if content else []

    logger.info("get_mgrprm path=%s exists=%s lines=%d", mgr_prm_path, exists, len(lines))

    return MgrPrmResponse(
        path    = mgr_prm_path,
        exists  = exists,
        lines   = lines,
        content = content,
    )

class ManageRequest(BaseModel):
    operation:     str           = Field(...,                description="purge | autostart | autorestart | all")
    blocks:        List[Any]     = Field(default_factory=list)
    # PURGEOLDEXTRACTS
    trail:         Optional[str] = Field(None)
    ckpt_mode:     str           = Field("USECHECKPOINTS")
    min_keep_val:  int           = Field(0)
    min_keep_unit: Optional[str] = Field(None)
    freq_val:      int           = Field(0)
    freq_unit:     Optional[str] = Field(None)
    # AUTOSTART
    process_type:  str           = Field("EXTRACT")
    group_name:    str           = Field("")
    wait_secs:     int           = Field(0)
    # AUTORESTART
    retries:       int           = Field(5)
    wait_mins:     int           = Field(2)
    reset_mins:    int           = Field(60)

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _log_line(level, code, msg):
    """Format a log line the JS parseLogLines() regex can parse."""
    return f"{_now()} LOCALHOST {level} {code} {msg}"

def _wrap(lines):
    """JS reads data[0] — wrap as [[line, ...]]."""
    return [lines]

def _patch_mgrprm(keyword, new_block):
    """
    Remove existing keyword block (+ comma continuations)
    from mgr.prm then append the new block.
    Same file path resolution as list_prm_files.
    """
    param_directory = os.path.join(gg_home, "dirprm")
    mgr_prm_path    = os.path.join(param_directory, "mgr.prm")

    # read existing content
    content = ""
    if os.path.isfile(mgr_prm_path):
        with open(mgr_prm_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

    # remove old block
    lines, skip, result = content.splitlines(keepends=True), False, []
    for line in lines:
        s = line.strip().upper()
        if s.startswith(keyword.upper()):
            skip = True
            continue
        if skip:
            if s.startswith(",") or s == "":
                continue
            skip = False
        result.append(line)

    new_content = "".join(result).rstrip() + f"\n\n{new_block}\n"

    # write back — same style as list_prm_files
    os.makedirs(param_directory, exist_ok=True)
    with open(mgr_prm_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    logger.info("mgr.prm updated — keyword=%s path=%s", keyword, mgr_prm_path)


# ── Syntax builders ───────────────────────────────────────────────────

def _syntax_purge(trail, ckpt_mode, min_keep_val, min_keep_unit, freq_val, freq_unit):
    parts = [
        f"PURGEOLDEXTRACTS {trail}",
        f"  , {ckpt_mode}",
    ]
    if min_keep_val and min_keep_val > 0 and min_keep_unit:
        parts.append(f"  , {min_keep_unit} {min_keep_val}")
    if freq_val and freq_val > 0 and freq_unit:
        parts.append(f"  , {freq_unit} {freq_val}")
    return "\n".join(parts)


def _syntax_autostart(process_type, group_name, wait_secs):
    line = f"AUTOSTART {process_type}"
    if group_name:
        line += f" {group_name}"
    if wait_secs and wait_secs > 0:
        line += f", WAITFOR {wait_secs}"
    return line


def _syntax_autorestart(process_type, group_name, retries, wait_mins, reset_mins):
    line = f"AUTORESTART {process_type}"
    if group_name:
        line += f" {group_name}"
    line += (
        f"\n  , RETRIES {retries}"
        f"\n  , WAITMINUTES {wait_mins}"
        f"\n  , RESETMINUTES {reset_mins}"
    )
    return line


# ══════════════════════════════════════════════════════════════════════
# FUNCTION 1 — Apply PURGEOLDEXTRACTS
# JS: submitPurge() → POST /api/v2/purge/manage {operation:"purge"}
# ══════════════════════════════════════════════════════════════════════

@app.post(
    "/api/v2/purge/manage/purge",
    tags=["MigDB Parameter Management"],
    summary="Apply PURGEOLDEXTRACTS to mgr.prm",
    description=(
        "Writes the PURGEOLDEXTRACTS block to mgr.prm and reloads Manager. "
        "Called by JS submitPurge() with operation='purge'. "
        "Replaces any existing PURGEOLDEXTRACTS block before writing the new one."
    ),
)
def apply_purge(req: ManageRequest):
    output = []
    try:
        syntax = _syntax_purge(
            req.trail,
            req.ckpt_mode,
            req.min_keep_val,
            req.min_keep_unit,
            req.freq_val,
            req.freq_unit,
        )
        _patch_mgrprm("PURGEOLDEXTRACTS", syntax)
        output.append(_log_line("INFO", "OGG-01024",
            f"PURGEOLDEXTRACTS applied for trail {req.trail}."))

        reload_out = _purge_run_ggsci("SEND MANAGER RELOAD", "EXIT")
        output.extend(reload_out)
        output.append(_log_line("INFO", "OGG-00975", "Manager reloaded successfully."))

    except Exception as e:
        logger.error("apply_purge error: %s", e)
        output.append(_log_line("ERROR", "OGG-00001", str(e)))

    return _wrap(output)


# ══════════════════════════════════════════════════════════════════════
# FUNCTION 2 — Apply AUTOSTART
# JS: submitAutostart() → POST /api/v2/purge/manage {operation:"autostart"}
# ══════════════════════════════════════════════════════════════════════

@app.post(
    "/api/v2/purge/manage/autostart",
    tags=["MigDB Parameter Management"],
    summary="Apply AUTOSTART to mgr.prm",
    description=(
        "Writes the AUTOSTART line to mgr.prm and reloads Manager. "
        "Called by JS submitAutostart() with operation='autostart'. "
        "Replaces any existing AUTOSTART line before writing the new one."
    ),
)
def apply_autostart(req: ManageRequest):
    output = []
    try:
        syntax = _syntax_autostart(
            req.process_type,
            req.group_name,
            req.wait_secs,
        )
        _patch_mgrprm("AUTOSTART", syntax)
        output.append(_log_line("INFO", "OGG-01030",
            f"AUTOSTART applied for {req.process_type}"
            + (f" {req.group_name}" if req.group_name else "") + "."))

        reload_out = _purge_run_ggsci("SEND MANAGER RELOAD", "EXIT")
        output.extend(reload_out)
        output.append(_log_line("INFO", "OGG-00975", "Manager reloaded successfully."))

    except Exception as e:
        logger.error("apply_autostart error: %s", e)
        output.append(_log_line("ERROR", "OGG-00001", str(e)))

    return _wrap(output)


# ══════════════════════════════════════════════════════════════════════
# FUNCTION 3 — Apply AUTORESTART
# JS: submitAutorestart() → POST /api/v2/purge/manage {operation:"autorestart"}
# ══════════════════════════════════════════════════════════════════════

@app.post(
    "/api/v2/purge/manage/autorestart",
    tags=["MigDB Parameter Management"],
    summary="Apply AUTORESTART to mgr.prm",
    description=(
        "Writes the AUTORESTART block to mgr.prm and reloads Manager. "
        "Called by JS submitAutorestart() with operation='autorestart'. "
        "Replaces any existing AUTORESTART block before writing the new one."
    ),
)
def apply_autorestart(req: ManageRequest):
    output = []
    try:
        syntax = _syntax_autorestart(
            req.process_type,
            req.group_name,
            req.retries,
            req.wait_mins,
            req.reset_mins,
        )
        _patch_mgrprm("AUTORESTART", syntax)
        output.append(_log_line("INFO", "OGG-01031",
            f"AUTORESTART applied for {req.process_type}"
            + (f" {req.group_name}" if req.group_name else "") + "."))

        reload_out = _purge_run_ggsci("SEND MANAGER RELOAD", "EXIT")
        output.extend(reload_out)
        output.append(_log_line("INFO", "OGG-00975", "Manager reloaded successfully."))

    except Exception as e:
        logger.error("apply_autorestart error: %s", e)
        output.append(_log_line("ERROR", "OGG-00001", str(e)))

    return _wrap(output)


# ══════════════════════════════════════════════════════════════════════
# FUNCTION 4 — Apply ALL to mgr.prm  (submitAll button)
# JS: submitAll() → POST /api/v2/purge/manage {operation:"all", blocks:[...]}
# ══════════════════════════════════════════════════════════════════════

@app.post(
    "/api/v2/purge/manage",
    tags=["MigDB Parameter Management"],
    summary="Apply all enabled parameters to mgr.prm",
    description=(
        "Unified endpoint called by JS callApi() for all operations. "
        "Dispatches on operation field: purge | autostart | autorestart | all. "
        "For operation='all', applies every block in blocks[] in one write "
        "then reloads Manager once. "
        "Returns [[log_line, ...]] — JS reads data[0] through parseLogLines()."
    ),
)
def apply_manage(req: ManageRequest):
    output = []
    try:
        if req.operation == "purge":
            syntax = _syntax_purge(
                req.trail, req.ckpt_mode,
                req.min_keep_val, req.min_keep_unit,
                req.freq_val, req.freq_unit,
            )
            _patch_mgrprm("PURGEOLDEXTRACTS", syntax)
            output.append(_log_line("INFO", "OGG-01024",
                f"PURGEOLDEXTRACTS applied for trail {req.trail}."))

        elif req.operation == "autostart":
            syntax = _syntax_autostart(
                req.process_type, req.group_name, req.wait_secs,
            )
            _patch_mgrprm("AUTOSTART", syntax)
            output.append(_log_line("INFO", "OGG-01030",
                f"AUTOSTART applied for {req.process_type}."))

        elif req.operation == "autorestart":
            syntax = _syntax_autorestart(
                req.process_type, req.group_name,
                req.retries, req.wait_mins, req.reset_mins,
            )
            _patch_mgrprm("AUTORESTART", syntax)
            output.append(_log_line("INFO", "OGG-01031",
                f"AUTORESTART applied for {req.process_type}."))

        elif req.operation == "all":
            for blk in req.blocks:
                t = blk.get("type", "")

                if t == "purge":
                    syntax = _syntax_purge(
                        blk.get("trail", ""),
                        blk.get("ckpt_mode", "USECHECKPOINTS"),
                        blk.get("min_keep_val", 0),
                        blk.get("min_keep_unit"),
                        blk.get("freq_val", 0),
                        blk.get("freq_unit"),
                    )
                    _patch_mgrprm("PURGEOLDEXTRACTS", syntax)
                    output.append(_log_line("INFO", "OGG-01024",
                        f"PURGEOLDEXTRACTS applied for trail {blk.get('trail')}."))

                elif t == "autostart":
                    syntax = _syntax_autostart(
                        blk.get("process_type", "EXTRACT"),
                        blk.get("group_name", ""),
                        blk.get("wait_secs", 0),
                    )
                    _patch_mgrprm("AUTOSTART", syntax)
                    output.append(_log_line("INFO", "OGG-01030",
                        f"AUTOSTART applied for {blk.get('process_type')}."))

                elif t == "autorestart":
                    syntax = _syntax_autorestart(
                        blk.get("process_type", "EXTRACT"),
                        blk.get("group_name", ""),
                        blk.get("retries", 5),
                        blk.get("wait_mins", 2),
                        blk.get("reset_mins", 60),
                    )
                    _patch_mgrprm("AUTORESTART", syntax)
                    output.append(_log_line("INFO", "OGG-01031",
                        f"AUTORESTART applied for {blk.get('process_type')}."))

        # single Manager reload after all writes
        reload_out = _purge_run_ggsci("SEND MANAGER RELOAD", "EXIT")
        output.extend(reload_out)
        output.append(_log_line("INFO", "OGG-00975", "Manager reloaded successfully."))

    except Exception as e:
        logger.error("apply_manage error: %s", e)
        output.append(_log_line("ERROR", "OGG-00001", str(e)))

    return _wrap(output)


class AddExtTrailRequest(BaseModel):
    extname: str
    trailname: str
    trailtype: str
    trailsize: str

@app.post("/api/v2/addExtTrail", include_in_schema=False,tags=["Add Extract Trail to an Extract"] , summary="Add Extract Trails to Extract" , description="Add Extract Trail to Extract")
def add_extract_trail(body: AddExtTrailRequest):
    ssh = subprocess.Popen(
        [ggsci_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0
    )
    ssh.stdin.write(
        'add ' + body.trailtype + ' ' + body.trailname +
        ', Extract ' + body.extname + ',megabytes ' + body.trailsize + '\n'
    )
    delexttrail, stderr = ssh.communicate(timeout=sshTimeOut)

    trail_file = os.path.join(agent_log, 'addexttrail.out')
    with open(trail_file, mode='w') as outfile:
        outfile.write(delexttrail)

    AddExtErrPrint = []
    with open(trail_file, mode='r') as infile:
        for line in infile:
            if 'ERROR' in line:
                AddExtErrPrint.append(line.split('>', 1)[-1])
            elif 'file' in line:
                AddExtErrPrint.append(line.split('>', 1)[-1])
            elif 'Extract' in line:
                AddExtErrPrint.append(line.split(':', 1)[-1].strip())

    oplace_debug(['addexttrail.out'])
    return [AddExtErrPrint]

class GGGetAllTrailsRequest(BaseModel):
    trailname: List[str]

@app.post("/api/v2/cdcGetAllTrails" ,tags=["Get Trail details from Trail name"] , summary="Get Extract Trail Details" , description="Returns list of all generated trails along with size and creation time")
def cdc_get_all_trails(body: GGGetAllTrailsRequest):
    TrailName = []

    for name in body.trailname:
        if name.startswith('.') or name[0].isalnum():
            pattern = os.path.join(gg_home, name + '*')
        else:
            pattern = name + '*'

        for match in glob.glob(pattern):
            stat = os.stat(match)
            TrailName.append({
                'file': match,
                'size': stat.st_size,
                'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })

    return [TrailName]

class GGLogDumpCountRequest(BaseModel):
    trailfile: List[str]

@app.post("/api/v2/cdcDataDumpCount", tags=["MigDB CDC Trail Analysis"],
          summary="Get trail file record counts",
          description="Runs logdump count detail on one or more trail files and returns a breakdown of transaction types and record counts per table.")
async def cdc_data_dump_count(request: Request, body: GGLogDumpCountRequest):
    Count_Detail_Ind = {}
    for trail in body.trailfile:
        ssh = subprocess.Popen(
            [logdump_bin],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=0
        )
        ssh.stdin.write("count detail " + trail + "\n")
        TranNext, _ = ssh.communicate(timeout=sshTimeOut)

        count_detail_file  = os.path.join(agent_log, 'Lodump_CountDetail.out')
        count_detail_iter1 = os.path.join(agent_log, 'Lodump_CountDetail_Iter1.txt')

        with open(count_detail_file, mode='w') as outfile2:
            outfile2.write(TranNext)

        # Pass 1 — collect Logdump marker line numbers
        Count_Detail = []
        with open(count_detail_file, mode='r') as infile:
            for line in infile:
                line1 = line.split()
                if len(line1) > 2:
                    if line1[0].startswith('Logdump') and line1[2].startswith('>'):
                        Count_Detail.append(line1[1])

        if len(Count_Detail) < 2:
            logger.info(f"WARNING: Not enough Logdump markers found in {trail}")
            continue

        # Pass 2 — extract lines between markers
        with open(count_detail_file, mode='r') as infile, \
             open(count_detail_iter1, mode='w') as outfile:
            copy = False
            n = 0
            for line in infile:
                if n < len(Count_Detail) and line.startswith('Logdump ' + str(Count_Detail[n])):
                    if not copy:
                        copy = True
                        n += 1   # advance to next marker as stop boundary
                    else:
                        copy = False
                    continue
                elif copy:
                    outfile.write(line)

        # Pass 3 — parse table-level counts
        SKIP_PREFIXES = {'Before', 'RestartAbend', 'After', 'Metadata', 'Total', 'Avg'}
        copy = False
        tabname = None
        with open(count_detail_iter1, mode='r') as infile:
            for line in infile:
                if any(tag in line for tag in ('Logdump', 'LogTrail', '*FileHeader*')):
                    continue
                line1 = line.strip().split()
                if len(line1) > 1:
                    if line1[1] == 'Partition':
                        tabname = line1[0]
                        copy = True
                        continue
                    elif copy and line1[0] not in SKIP_PREFIXES and tabname:
                        try:
                            delta = int(line1[1])
                            Count_Detail_Ind[tabname] = Count_Detail_Ind.get(tabname, 0) + delta
                        except ValueError:
                            pass  # skip non-numeric lines

    oplace_debug(['Lodump_CountDetail.out', 'Lodump_CountDetail_Iter1.txt'])
    return [Count_Detail_Ind]


def hexConvert(filename):
    with open(os.path.join(agent_log, filename)) as infile:
        str = ''
        for line in infile:
            for word in line.split():
                str = str + word
    strAscii = binascii.unhexlify(str).decode('utf8', errors='ignore')
    return strAscii

class LogDumpRequest(BaseModel):
    trailfile: str
 
 
class LogDumpResponse(BaseModel):
    parse3: str
    parse4: str
    parse5: str
    parse6: str
    parse7: str
    parse8: str
    parse9: str
    parse10: str
    parse11: str
    parse12: str
    parse13: str
    count_detail_ind: list
    parse16: str

def _run_logdump(*commands: str) -> str:
    """Spawn a logdump process, send commands via stdin, and return stdout."""
    proc = subprocess.Popen(
        [logdump_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0,
    )
    for cmd in commands:
        proc.stdin.write(cmd + "\n")
    stdout, _ = proc.communicate(timeout=sshTimeOut)
    return stdout

def _extract_section(
    source_path: str,
    dest_path: str,
    start_marker: str,
    end_marker: str,
    strip_suffix: str = "",
) -> None:
    """
    Copy lines from *source_path* to *dest_path* that fall between
    start_marker (exclusive) and end_marker (exclusive).
    Each line is split on '|' and only the first segment is kept.
    Optionally strip a suffix from each line.
    """
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(source_path) as infile, open(dest_path, "w", encoding="utf-8") as outfile:
        copy = False
        for line in infile:
            line = line.split("|")[0]
            if start_marker in line:
                copy = True
                continue
            elif end_marker in line:
                copy = False
                continue
            elif copy:
                outfile.write(line.strip(strip_suffix) if strip_suffix else line)
 
 
def hex_convert(filename: str) -> str:
    """
    Read logdump hex output file and decode to ASCII string.
    Logdump hex lines look like:
      ' 0005 4c69 6e75 78                                 '
    The first token is the byte length, rest are hex bytes.
    """
    result = ''
    filepath = os.path.join(agent_log, filename)

    try:
        with open(filepath, mode='r') as infile:
            for line in infile:
                line = line.strip()
                if not line:
                    continue
                tokens = line.split()
                if not tokens:
                    continue
                # First token is length prefix (e.g. '0005'), skip it
                hex_bytes = tokens[1:]
                for hb in hex_bytes:
                    # Each token is 4 hex chars = 2 bytes
                    try:
                        # Decode pairs of hex chars
                        for i in range(0, len(hb), 2):
                            byte_val = int(hb[i:i+2], 16)
                            if 32 <= byte_val <= 126:   # printable ASCII only
                                result += chr(byte_val)
                    except ValueError:
                        pass
    except FileNotFoundError:
        pass

    return result.strip() 
 
@app.post("/api/v2/logdump",tags=["MigDB CDC Trail Analysis"] , summary="Parse trail file header and extract token sections", description=(
        "Opens a MigDB trail file using logdump and extracts file header tokens "
        "(system name, node name, release, version, client charset, client version, "
        "data source, CSN range, LOGBSN), runs count detail to get per-table transaction "
        "breakdowns, and reads the first RBA position from the trail."
    ), response_model=LogDumpResponse,
    responses={
        200: {"description": "Successfully parsed trail file header and record counts"},
        504: {"description": "Logdump process timed out"},
    },)
def gg_log_dump(body: LogDumpRequest):
    trailfile = body.trailfile.lstrip('["').rstrip('"]')
 
    os.makedirs(agent_log, exist_ok=True)

    try:
        logdump_out = _run_logdump(f"open {trailfile}", "fileheader detail", "n")
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="logdump timed out") from exc
 
    logdump_out_path = os.path.join(agent_log, "logdump.out")
    with open(logdump_out_path, "w") as f:
        f.write(logdump_out)
 
    sections = [
        # (dest_file, start_marker, end_marker, strip_suffix)
        ("ldump2.out",  "TokenID x30 '0' Sysname",       "TokenID x31 '1' Nodename",       ""),
        ("ldump3.out",  "TokenID x31 '1' Nodename",       "TokenID x32 '2' Release",         ""),
        ("ldump4.out",  "TokenID x32 '2' Release",        "TokenID x33 '3' Version",         ""),
        ("ldump5.out",  "TokenID x31 '1' Name",           "TokenID x32 '2' Instance",        ""),
        ("ldump6.out",  "TokenID x36 '6' VerString",      "TokenID x37 '7' ClientCharset",   "00e5"),
        ("ldump7.out",  "TokenID x38 '8' ClientVerString","TokenID x39 '9' ClientNCharset",  ""),
        ("ldump8.out",  "TokenID x30 '0' Name",           "TokenID x31 '1' DataSource",      ""),
        ("ldump9.out",  "TokenID x37 '7' VerString",      "GroupID x34 '4' Continunity",     ""),
        ("ldump10.out", "TokenID x3a ':' FirstCSN",       "TokenID x3b ';' LastCSN",         ""),
        ("ldump11.out", "TokenID x3b ';' LastCSN",        "TokenID x3c '<' FirstIOTime",     ""),
        ("ldump12.out", "TokenID x3e '>' LOGBSN",         "TokenID x3f '?' BITFLAGS",        ""),
    ]
 
    parse_results: list[str] = []
    for dest_file, start, end, strip_sfx in sections:
        dest_path = os.path.join(agent_log, dest_file)
        _extract_section(logdump_out_path, dest_path, start, end, strip_sfx)
        parse_results.append(hex_convert(dest_file))
 
    (
        parse3, parse4, parse5, parse6, parse7,
        parse8, parse9, parse10, parse11, parse12, parse13,
    ) = parse_results
 
    try:
        count_res = _run_logdump(f"open {trailfile}", "count detail")
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="logdump count detail timed out") from exc
 
    countdetail_path = os.path.join(agent_log, "countdetail.out")
    with open(countdetail_path, "w") as f:
        f.write(count_res)
 
    count_detail: list[str] = []
    with open(countdetail_path) as infile:
        for line in infile:
            parts = line.split()
            if parts and parts[0].startswith("Logdump") and len(parts) > 2 and parts[2].startswith(">"):
                count_detail.append(parts[1])
 
    countiter1_path = os.path.join(agent_log, "countiter1.out")
    with open(countdetail_path) as infile, open(countiter1_path, "w") as outfile:
        copy = False
        n = 0
        for line in infile:
            if n < len(count_detail) and line.startswith(f"Logdump {count_detail[n]}"):
                copy = True
                n += 1         
                continue
            elif n < len(count_detail) and line.startswith(f"Logdump {count_detail[n]}"):
                copy = False
                continue
            elif copy:
                outfile.write(line)
 
    count_detail_ind: list[dict] = []
    with open(countiter1_path) as infile:
        copy = False
        tab_name = ""
        for line in infile:
            if "Logdump" in line or "*FileHeader*" in line:
                continue
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            if parts[1] == "Partition":
                tab_name = parts[0]
                copy = True
                continue
            if copy:
                if parts[0] == "Before":
                    pass 
                elif parts[0] == "After":
                    pass 
                elif parts[0] == "Metadata":
                    pass 
                elif parts[0] in ("Total", "Avg"):
                    pass
                else:
                    count_detail_ind.append(
                        {
                            "tab_name": tab_name,
                            "tran_type": parts[0],
                            "tran_det": parts[1],
                        }
                    )
 
    try:
        trail_data = _run_logdump(f"open {trailfile}", "n", "n")
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="logdump trail detail timed out") from exc
 
    trandet_path = os.path.join(agent_log, "trandet.out")
    with open(trandet_path, "w") as f:
        f.write(trail_data)
 
    parse16 = ""
    with open(trandet_path) as infile:
        for line in infile:
            if "RBA" in line:
                parts = line.split()
                if len(parts) > 6:
                    parse16 = parts[6]
 
    oplace_debug(
        [
            "ldump2.out", "ldump3.out", "ldump4.out", "ldump5.out",
            "ldump6.out", "ldump7.out", "ldump8.out", "ldump9.out",
            "ldump10.out", "ldump11.out", "ldump12.out",
            "countdetail.out", "countiter1.out", "trandet.out",
        ]
    )

    return JSONResponse(content=[
        parse3,           # data[0]  OSPlat
        parse4,           # data[1]  NodeName
        parse5,           # data[2]  OSKern
        parse6,           # data[3]  DBName
        parse7,           # data[4]  DBVer
        parse8,           # data[5]  DBClientVer
        parse9,           # data[6]  ExtName
        parse10,          # data[7]  GGVer
        parse11,          # data[8]  FirstCSN
        parse12,          # data[9]  LastCSN
        parse13,          # data[10] LogBSN
        count_detail_ind, # data[11] [{tab_name, tran_type, tran_det}, ...]
        parse16           # data[12] RBA
    ])
 

class TranNextRequest(BaseModel):
    trailfile: str
    rba: str
    filterlist: list[str]
    filtmatch: str

class TranNextResponse(BaseModel):
    tran_next_rba: str
    first_tran: list[str]
    second_tran: list[str]


@app.post("/api/v2/trannext", tags=["CDC Trail Analysis"], summary="Read the next two transactions from a trail file at a given RBA",
    description=(
        "Opens a MigDB trail file at a specified RBA position using logdump, "
        "applies optional filter expressions and a filter match condition, then reads "
        "the next two transaction records. Returns the RBA of the next transaction, "
        "the full content of the first transaction block, and the full content of the "
        "second transaction block."
    ),response_model=TranNextResponse)
def gg_tran_next(body: TranNextRequest):
    trailfile = body.trailfile.lstrip('["').rstrip('"]')
 
    os.makedirs(agent_log, exist_ok=True)
 
    proc = subprocess.Popen(
        [logdump_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0,
    )
 
    proc.stdin.write(f"open {trailfile}\n")
    proc.stdin.write("ghdr on;detail data;usertoken detail;ggstoken detail;\n")
 
    for filt in body.filterlist:
        proc.stdin.write(filt + "\n")
 
    proc.stdin.write(body.filtmatch + "\n")
    proc.stdin.write(f"pos {body.rba}\n")
    proc.stdin.write("n\n")
    proc.stdin.write("n\n")
 
    try:
        tran_next_raw, _ = proc.communicate(timeout=sshTimeOut)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise HTTPException(status_code=504, detail="logdump timed out")
 
    trannext_path = os.path.join(agent_log, "trannext.out")
    with open(trannext_path, "w") as outfile:
        outfile.write(tran_next_raw)
 
    tran_next_rba = ""
    first_tran: list[str] = []
    second_tran: list[str] = []
 
    with open(trannext_path) as infile:
        copy = False
        block = 0                   
 
        for line in infile:
            if ">______" in line:
                block += 1
                copy = True
                continue
 
            if line.startswith("LogDump"):
                copy = False
                continue
 
            if copy and "Logdump" not in line:
                if block == 1:
                    first_tran.append(line)
                elif block == 2:
                    second_tran.append(line)
 
            if "RBA" in line:
                parts = line.split()
                if parts:
                    tran_next_rba = parts[-1]
 
    return JSONResponse(content=[tran_next_rba,first_tran,second_tran])

class TranPrevRequest(BaseModel):
    trailfile: str
    rba: str
 
 
class TranPrevResponse(BaseModel):
    tran_prev_rba: str
    first_tran: list[str]
    second_tran: list[str]

@app.post("/api/v2/tranprev", tags=["CDC Trail Analysis"],
    summary="Read the two transactions before a given RBA",
    description="Navigates backward in a MigDB trail file using sfh prev and returns the two preceding transaction blocks and the resolved RBA.")
def gg_tran_prev(body: TranPrevRequest):
    trailfile = body.trailfile.lstrip('["').rstrip('"]')
 
    os.makedirs(agent_log, exist_ok=True)
 
    proc = subprocess.Popen(
        [logdump_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0,
    )
 
    proc.stdin.write(f"open {trailfile}\n")
    proc.stdin.write("ghdr on;detail data;usertoken detail;ggstoken detail;\n")
    proc.stdin.write(f"pos {body.rba}\n")
    proc.stdin.write("sfh prev\n")
    proc.stdin.write("sfh prev\n")
 
    try:
        tran_prev_raw, _ = proc.communicate(timeout=sshTimeOut)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise HTTPException(status_code=504, detail="logdump timed out")
 
    tranprev_path = os.path.join(agent_log, "tranprev.out")
    with open(tranprev_path, "w") as outfile:
        outfile.write(tran_prev_raw)
 
    tran_prev_rba = ""
    first_tran: list[str] = []
    second_tran: list[str] = []
 
    with open(tranprev_path) as infile:
        copy = False
        block = 0
 
        for line in infile:
            if ">______" in line:
                block += 1
                copy = True
                continue
 
            if line.startswith("LogDump"):
                copy = False
                continue
 
            if copy and "Logdump" not in line:
                if block == 1:
                    first_tran.append(line)
                elif block == 2:
                    second_tran.append(line)
 
            if "RBA" in line:
                parts = line.split()
                if parts:
                    tran_prev_rba = parts[-1]
 
    oplace_debug(["tranprev.out"])
 
    return [tran_prev_rba, first_tran, second_tran]
    return TranPrevResponse(
        tran_prev_rba=tran_prev_rba,
        first_tran=first_tran,
        second_tran=second_tran,
    )

@app.post("/api/v2/addrepprm", tags=["MigDB Replicat Management"],
    summary="Upload a replicat parameter file",
    description="Saves an uploaded .prm file to the MigDB dirprm directory. Returns an error if the file already exists.",)
async def rhp_add_rep(file: UploadFile = File(...)):
    filename = secure_filename(file.filename)
 
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid or missing filename")
 
    target = os.path.join(gg_home, "dirprm", filename)
 
    if os.path.exists(target):
        return JSONResponse(content=["File Already Exists"])
 
    os.makedirs(os.path.dirname(target), exist_ok=True)
 
    contents = await file.read()
    with open(target, "wb") as f:
        f.write(contents)
 
    return JSONResponse(content=["Saved"])

@app.post("/api/v2/masterkey/uploadwallet", tags=["MigDB Encryption Master Key Management"],
    summary="Upload or replace a wallet file",
    description="Saves an uploaded wallet file to the MigDB dirwlt directory. Replaces the file if it already exists.",)
async def rhp_wallet(file: UploadFile = File(...)):
    filename = secure_filename(file.filename)
 
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid or missing filename")
 
    target = os.path.join(gg_home, "dirwlt", filename)
 
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        contents = await file.read()
 
        already_exists = os.path.exists(target)
 
        with open(target, "wb") as f:
            f.write(contents)
 
        msg = "Wallet Replaced" if already_exists else "Wallet Saved"
 
    except OSError as e:
        msg = f"File not saved due to {e}"
 
    return JSONResponse(content=[msg])


class DownloadSoftRequest(BaseModel):
    softVer: str
    dbVer: str

def resolve_s3_key(soft_ver: str, db_ver: str) -> str:
    """Determine the S3 object key from software and DB version strings."""
    if soft_ver.startswith("21"):
        return f"{soft_ver}.zip"
 
    db_suffix_map = {
        "21": "",       # no suffix
        "19": "_19c",
        "18": "_18c",
        "12": "_12c",
        "11": "_11g",
    }
    for prefix, suffix in db_suffix_map.items():
        if db_ver.startswith(prefix):
            return f"{soft_ver}{suffix}.zip"
 
    raise ValueError(f"Unsupported dbVer: {db_ver!r}")
 
def _run_installer(soft_ver_str: str) -> str:
    """Run OUI runInstaller in silent attach-home mode and return its output."""
    run_installer = os.path.join(gg_home, "oui", "bin", "runInstaller")
    parts = soft_ver_str.split(".")
    home_label = f"GG{''.join(parts[:3])}Home1"
 
    use_system_ptr = (
        os.path.exists("/var/opt/oracle/oraInst.loc")
        or os.path.exists("/etc/oraInst.loc")
    )
 
    base_args = [
        run_installer,
        "-silent",
        "-attachHome",
        f"ORACLE_HOME={gg_home}",
        f"ORACLE_HOME_NAME={home_label}",
    ]
    if not use_system_ptr:
        base_args += ["-invPtrLoc", os.path.join(agent_base, "oraInst.loc")]
 
    proc = subprocess.Popen(
        base_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0,
    )
    stdout, _ = proc.communicate()
    return stdout

OS_PLAT = os.environ.get("OS_PLAT", "Linux")
BUCKET_NAME    = os.environ.get("S3_BUCKET", "ggsoft")
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

@app.post("/api/v2/downloadsoft", tags=["MigDB Software Management"],
    summary="Download and install MigDB software from S3",
    description="Resolves the correct S3 key from software and DB version, downloads the zip, extracts it to GG_HOME, and runs the OUI installer silently.")
def download_soft(body: DownloadSoftRequest):
    run_ins: list[str] = []
 
    try:
        key = resolve_s3_key(body.softVer, body.dbVer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
 
    os.makedirs(image_uploads, exist_ok=True)
    path_to_zip = os.path.join(image_uploads, key)
 
    try:
        s3 = boto3.resource(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
        )
        s3.Bucket(BUCKET_NAME).download_file(key, path_to_zip)
 
        with zipfile.ZipFile(path_to_zip, "r") as zf:
            for info in zf.infolist():
                extract_file(zf, info, gg_home)
 
        run_ins.append(f"Oracle Goldengate {key} Installed Successfully")
 
        if OS_PLAT in ("Linux", "AIX"):
            _ensure_ora_inst_loc(OS_PLAT)
 
        installer_output = _run_installer(body.softVer)
        run_ins.append(installer_output)
 
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            run_ins.append("The object does not exist.")
        else:
            run_ins.append(str(e))
    except OSError as e:
        run_ins.append(str(e))
 
    return JSONResponse(content=[run_ins])

class ViewExtractLogRequest(BaseModel):
    extops: str
    extname: str
    extatcsn:      str | None = None
    extaftercsn:   str | None = None
    domain:        str | None = None
    alias:         str | None = None
    beginmode:     str | None = None
    ctvalue:       str | None = None
    scnvalue:      str | None = None
    seqnovalue:    str | None = None
    rbavalue:      str | None = None
    trailname:     list[str] | None = None
    trailtype:     str | None = None
    trailsize:     int | None = None

 
def _spawn_ggsci(bufsize: int = 0) -> subprocess.Popen:
    """Spawn a fresh ggsci process and return it."""
    return subprocess.Popen(
        [ggsci_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=bufsize,
    )
 
def _communicate(proc: subprocess.Popen) -> str:
    """Call communicate(), kill the process, and return stdout."""
    stdout, _ = proc.communicate()
    try:
        proc.kill()
        proc.stdin.close()
    except OSError:
        pass
    return stdout
 
def _parse_stats(raw: str) -> dict:
    """Parse 'stats extract' output into {table: {operation: count}} dict."""
    stats: dict = {}
    tab_name = ""
    copy = False

    lines = [_OGG_PAT.sub("CDC-", line) for line in raw.splitlines(keepends=True)]
    cleaned_raw = "".join(lines)

    # Detect non-running / error states up front
    if "not currently running" in cleaned_raw or re.search(r"CDC-\d+\s+ERROR", cleaned_raw):
        error_line = next(
            (l.strip() for l in raw.splitlines() if "ERROR" in l), 
            "Extract group not currently running"
        )
        return {"status": "error", "message": error_line, "stats": {}}

    for line in lines:
        if line.startswith("Extracting"):
            tab_name = line.split()[2]
            stats[tab_name] = {}
        elif "*** Latest" in line:
            copy = True
        elif line.startswith("End"):
            copy = False
        elif copy:
            stripped = line.strip()
            if not stripped.startswith("No"):
                parts = stripped.split()
                if len(parts) > 1:
                    op_name = "".join(parts[:-1])
                    oper = parts[-1]
                    stats[tab_name][op_name] = oper

    if not stats:
        return {"status": "empty", "message": "No statistics found in output", "stats": {}}

    return {"status": "ok", "stats": stats}

def _parse_generic_output(raw: str) -> list[str]:
    """Strip header lines and clean GGSCI prompts from generic command output."""
    lines = raw.splitlines(keepends=True)
    result: list[str] = []
    for line in lines[8:]:
        if "GGSCI" in line:
            line = line.split(">", 1)[-1]
        result.append(line)
    return result
 
def _wait_for_status(proc: subprocess.Popen, extname: str, target: str, poll_cmd: str, sleep_sec: int = 60):
    """Poll stdout until a line containing *target* is found."""
    while True:
        output = proc.stdout.readline()
        if target in output:
            break
        time.sleep(sleep_sec)
        proc.stdin.write(poll_cmd)
        proc.stdin.flush()
 
def _handle_rpt(extname: str) -> list[str]:
    """Read the .rpt file for the named extract."""
    ext_err_print: list[str] = []
    for name in glob.glob(os.path.join(gg_home, "dirrpt", "*.rpt")):
        base = name.split("/")[-1]
        if re.match(base, extname + ".rpt", re.IGNORECASE):
            with open(os.path.join(gg_home, "dirrpt", base)) as f:
                for line in clean_gg_log(f):
                    ext_err_print.append(line)
    return ext_err_print
 
 
def _handle_edit(extname: str) -> str:
    """Return the content of the extract parameter file."""
    prm_path = os.path.join(gg_home, "dirprm", extname + ".prm")
    with open(prm_path) as f:
        return f.read()
 
 
def _handle_upgie(extname: str, alias: str, domain: str) -> list[str]:
    """Upgrade extract to integrated mode."""
    ext_err_print: list[str] = []
 
    proc = _spawn_ggsci(bufsize=1)
    proc.stdin.write(f"info {extname}")
    info_ext = _communicate(proc)
 
    if "Integrated" in info_ext:
        ext_err_print.append("Extract is Already in Integrated Mode !! STOP !!")
        return ext_err_print
 
    if "Oracle Redo Logs" not in info_ext or "RUNNING" not in info_ext:
        return ext_err_print
 
    proc = _spawn_ggsci(bufsize=1)
    proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
    login_err = _communicate(proc)
 
    if "ERROR" in login_err:
        ext_err_print.append(login_err)
        return ext_err_print
 
    proc = _spawn_ggsci(bufsize=1)
    proc.stdin.write(f"send extract {extname} tranlogoptions PREPAREFORUPGRADETOIE\n")
    proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
    proc.stdin.write(f"stop extract {extname}\n")
    time.sleep(60)
    proc.stdin.write(f"info extract {extname}\n")
    proc.stdin.flush()
 
    _wait_for_status(proc, extname, "STOPPED", f"info extract {extname}\n")
 
    proc.stdin.write(f"register extract {extname} database\n")
    reg_err = proc.stdout.readline()
    ext_err_print.append(reg_err)
 
    if "ERROR" in reg_err and "already registered" not in reg_err:
        proc.kill()
        proc.stdin.close()
        return ext_err_print
 
    proc.stdin.write(f"start extract {extname}\n")
    time.sleep(60)
    proc.stdin.write(f"info extract {extname} upgrade\n")
    proc.stdin.flush()
 
    _wait_for_status(proc, extname, "capture.", f"info extract {extname} upgrade \n")
 
    proc.stdin.write(f"start extract {extname}\n")
    _communicate(proc)
    return ext_err_print
 
 
def _handle_dwnie(extname: str, alias: str, domain: str) -> list[str]:
    """Downgrade extract from integrated mode."""
    ext_err_print: list[str] = []
 
    proc = _spawn_ggsci(bufsize=1)
    proc.stdin.write(f"info {extname}")
    info_ext = _communicate(proc)
 
    if "Oracle Redo Logs" in info_ext:
        ext_err_print.append("Extract is Already in Classic Mode !! STOP !!")
        return ext_err_print
 
    if "Integrated" not in info_ext or "RUNNING" not in info_ext:
        return ext_err_print
 
    proc = _spawn_ggsci(bufsize=1)
    proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
    login_err = _communicate(proc)
 
    if "ERROR" in login_err:
        ext_err_print.append(login_err)
        return ext_err_print
 
    proc = _spawn_ggsci(bufsize=1)
    proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
    proc.stdin.write(f"stop extract {extname}\n")
    time.sleep(60)
    proc.stdin.write(f"info extract {extname}\n")
    proc.stdin.flush()
 
    _wait_for_status(proc, extname, "STOPPED", f"info extract {extname}\n")
 
    proc.stdin.write(f"info {extname} downgrade\n")
    info_ie_err = proc.stdout.readline()
    ext_err_print.append(info_ie_err)
 
    if "ready to be downgraded" not in info_ie_err:
        proc.kill()
        proc.stdin.close()
        return ext_err_print
 
    proc.stdin.write(f"alter extract {extname} downgrade integrated tranlog\n")
    proc.stdin.write(f"info extract {extname}\n")
    proc.stdin.flush()
 
    _wait_for_status(proc, extname, "Oracle Redo Logs", f"info extract {extname}\n")
 
    proc.stdin.write(f"unregister extract {extname} database\n")
    proc.stdin.write(f"start extract {extname}\n")
    _communicate(proc)
    return ext_err_print
 
@app.post("/api/v2/extract/ops/view/log", tags=["MigDB Extract Operations"],
    summary="Perform operations on a MigDB extract",
    description="Executes extract operations such as start, stop, kill, stats, checkpoint, trail management, and mode changes (integrated/classic) for a named extract.")
def view_extract_log(body: ViewExtractLogRequest):
    extops   = body.extops
    extname  = body.extname
    prmfile  = ""
    ext_err_print: list[str] = []
    ext_proc_stats: dict = {}
 
    os.makedirs(agent_log, exist_ok=True)
 
    if extops == "rpt":
        ext_err_print = _handle_rpt(extname)
        return JSONResponse(content=[ext_err_print, prmfile, ext_proc_stats])
 
    if extops == "edit":
        try:
            prmfile = _handle_edit(extname)
        except OSError as e:
            raise HTTPException(status_code=404, detail=str(e))
        return JSONResponse(content=[ext_err_print, prmfile, ext_proc_stats])
 
    if extops == "upgie":
        domain = body.domain or ""
        alias  = body.alias  or ""
        ext_err_print = _handle_upgie(extname, alias, domain)
        return JSONResponse(content=[ext_err_print, prmfile, ext_proc_stats])
 
    if extops == "dwnie":
        domain = body.domain or ""
        alias  = body.alias  or ""
        ext_err_print = _handle_dwnie(extname, alias, domain)
        return JSONResponse(content=[ext_err_print, prmfile, ext_proc_stats])
 
    proc = _spawn_ggsci()
 
    if extops == "chk":
        proc.stdin.write(f"info {extname} showch debug")
 
    elif extops == "stats":
        proc.stdin.write(f"stats extract {extname}\n")
 
    elif extops == "startdef":
        proc.stdin.write(f"start extract {extname}\n")
 
    elif extops == "startatcsn":
        csn = body.extatcsn or ""
        proc.stdin.write(f"start {extname} atcsn {csn}")
 
    elif extops == "startaftercsn":
        csn = body.extaftercsn or ""
        proc.stdin.write(f"start {extname} aftercsn {csn}")
 
    elif extops == "stop":
        proc.stdin.write(f"stop extract {extname}\n")
 
    elif extops == "forcestop":
        proc.stdin.write(f"send extract {extname} forcestop\n")
 
    elif extops == "kill":
        proc.stdin.write(f"kill extract {extname}\n")
 
    elif extops == "extstatus":
        proc.stdin.write(f"send extract {extname} status\n")
 
    elif extops == "del":
        domain = body.domain or ""
        alias  = body.alias  or ""
        proc.stdin.write(f"sourcedb {alias} , useridalias {alias} , domain {domain}\n")
        proc.stdin.write(f"delete extract {extname}\n")
 
    elif extops == "pmpdel":
        proc.stdin.write(f"delete extract {extname}\n")
 
    elif extops == "extetroll":
        proc.stdin.write(f"alter extract {extname} etrollover\n")
 
    elif extops == "extbegin":
        beginmode = body.beginmode or ""
        if beginmode == "Now":
            proc.stdin.write(f"alter extract {extname},begin now\n")
        elif beginmode == "Time":
            domain  = body.domain  or ""
            alias   = body.alias   or ""
            ctvalue = (body.ctvalue or "").replace("T", " ")
            proc.stdin.write(f"dblogin sourcedb {alias} , useridalias {alias} domain {domain}\n")
            proc.stdin.write(f"alter extract {extname},begin {ctvalue}\n")
        elif beginmode == "SCN":
            domain   = body.domain   or ""
            alias    = body.alias    or ""
            scnvalue = body.scnvalue or ""
            proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
            proc.stdin.write(f"alter extract {extname},scn {scnvalue}\n")
        elif beginmode == "pmpextseqno":
            seqno = body.seqnovalue or ""
            rba   = body.rbavalue   or ""
            proc.stdin.write(f"alter extract {extname},extseqno {seqno},extrba {rba}\n")
 
    elif extops == "exttraildel":
        for trail in (body.trailname or []):
            proc.stdin.write(f"delete exttrail {trail}, Extract {extname}\n")
 
    elif extops == "exttrailadd":
        trailname = body.trailname[0] if body.trailname else ""
        trailtype = body.trailtype or ""
        trailsize = body.trailsize or 0
        proc.stdin.write(f"add {trailtype} {trailname}, Extract {extname},megabytes {trailsize}\n")
 
    elif extops == "cachemgr":
        proc.stdin.write(f"send extract {extname} cachemgr cachestats\n")
 
    elif extops == "extunreg":
        domain = body.domain or ""
        alias  = body.alias  or ""
        proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
        proc.stdin.write(f"unregister extract {extname} database\n")
 
    else:
        proc.kill()
        raise HTTPException(status_code=400, detail=f"Unknown extops value: {extops!r}")
 
    raw_output = _communicate(proc)
 
    if extops == "stats":
        stats_path = os.path.join(agent_log, "extStats")
        with open(stats_path, "w") as f:
            f.write(raw_output)
        with open(stats_path) as f:
            ext_proc_stats = _parse_stats(f.read())
    else:
        chk_path = os.path.join(agent_log, "ChkExt.lst")
        with open(chk_path, "w") as f:
            f.write(raw_output)
        with open(chk_path) as f:
            for line in clean_gg_log(f):
                ext_err_print.append(line)

    return JSONResponse(content=[ext_err_print, prmfile, ext_proc_stats])

class ViewReplicatLogRequest(BaseModel):
    repops:      str
    repname:     str
    # optional fields used only by specific repops values
    repatcsn:    str | None = None
    repaftercsn: str | None = None
    domain:      str | None = None
    alias:       str | None = None
    chktbl:      str | None = None
    beginmode:   str | None = None
    ctvalue:     str | None = None
    seqnovalue:  str | None = None
    rbavalue:    str | None = None 

_GGSCI_BANNER_PREFIXES = (
    "Oracle GoldenGate Command Interpreter",
    "Version ",
    "Oracle Linux",
    "Operating system character set",
    "Copyright (C)",
)
 
def _parse_ggsci_output(raw: str) -> list[str]:
    """Strip the first 8 header lines and clean GGSCI prompt prefixes."""
    result: list[str] = []
    for line in raw.splitlines(keepends=True):
        if "GGSCI" in line:
            line = line.split(">", 1)[-1]

        stripped = line.strip()
        if not stripped:
            continue
        if any(stripped.startswith(p) for p in _GGSCI_BANNER_PREFIXES):
            continue

        result.append(line)
    return result

@app.post("/api/v2/replicat/ops/view/log", tags=["MigDB Replicat Operations"],
    summary="Perform operations on a MigDB replicat",
    description="Executes replicat operations such as start, stop, kill, stats, checkpoint, integrated/non-integrated mode changes, and begin position alterations for a named replicat.",)
def view_replicat_log(body: ViewReplicatLogRequest):
    repops  = body.repops
    repname = body.repname
    rep_err_print: list[str] = []
    prm_file = ""
 
    os.makedirs(agent_log, exist_ok=True)
 
    if repops == "rpt":
        for name in glob.glob(os.path.join(gg_home, "dirrpt", "*.rpt")):
            base = name.split("/")[-1]
            if re.match(base, repname + ".rpt", re.IGNORECASE):
                with open(os.path.join(gg_home, "dirrpt", base)) as f:
                    rep_err_print.extend(f.readlines())
        return JSONResponse(content=[rep_err_print, prm_file])
 
    if repops == "edit":
        prm_path = os.path.join(gg_home, "dirprm", repname + ".prm")
        try:
            with open(prm_path) as f:
                prm_file = f.read()
        except OSError as e:
            raise HTTPException(status_code=404, detail=str(e))
        return JSONResponse(content=[rep_err_print, prm_file])
 
    proc = _spawn_ggsci()
 
    if repops == "chk":
        proc.stdin.write(f"info {repname} showch debug")
 
    elif repops == "stats":
        proc.stdin.write(f"stats replicat {repname}\n")
 
    elif repops == "startdef":
        proc.stdin.write(f"start replicat {repname}\n")
 
    elif repops == "skiptrans":
        proc.stdin.write(f"start replicat {repname} SKIPTRANSACTION\n")
 
    elif repops == "nofilterdup":
        proc.stdin.write(f"start replicat {repname} NOFILTERDUPTRANSACTIONS\n")
 
    elif repops == "atcsn":
        csn = body.repatcsn or ""
        proc.stdin.write(f"start replicat {repname} ATCSN {csn}\n")
 
    elif repops == "aftercsn":
        csn = body.repaftercsn or ""
        proc.stdin.write(f"start replicat {repname} AFTERCSN {csn}\n")
 
    elif repops == "stop":
        proc.stdin.write(f"stop replicat {repname}\n")
 
    elif repops == "forcestop":
        proc.stdin.write(f"send replicat {repname} forcestop\n")
 
    elif repops == "kill":
        proc.stdin.write(f"kill replicat {repname}\n")
 
    elif repops == "del":
        domain = body.domain or ""
        alias  = body.alias  or ""
        proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
        proc.stdin.write(f"delete replicat {repname}\n")
 
    elif repops == "upgir":
        domain = body.domain or ""
        alias  = body.alias  or ""
        proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
        proc.stdin.write(f"alter replicat {repname},integrated\n")
 
    elif repops == "dwnir":
        domain = body.domain or ""
        alias  = body.alias  or ""
        chktbl = body.chktbl or ""
        proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
        proc.stdin.write(f"alter replicat {repname} nonintegrated ,CHECKPOINTTABLE {chktbl}\n")
 
    elif repops == "begin":
        domain    = body.domain    or ""
        alias     = body.alias     or ""
        beginmode = body.beginmode or ""
        proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
        if beginmode == "Now":
            proc.stdin.write(f"alter replicat {repname},begin now\n")
        elif beginmode == "Time":
            ctvalue = body.ctvalue or ""
            proc.stdin.write(f"alter replicat {repname},begin {ctvalue}\n")
        elif beginmode == "LOC":
            seqno = body.seqnovalue or ""
            rba   = body.rbavalue   or ""
            proc.stdin.write(f"alter replicat {repname},extseqno {seqno},extrba {rba}\n")
 
    else:
        proc.kill()
        raise HTTPException(status_code=400, detail=f"Unknown repops value: {repops!r}")
 
    raw_output = _communicate(proc)
 
    chk_path = os.path.join(agent_log, "ChkRep.lst")
    with open(chk_path, "w") as f:
        f.write(raw_output)
    with open(chk_path) as f:
        rep_err_print = _parse_ggsci_output(f.read())
 
    return JSONResponse(content=[rep_err_print, prm_file])

def _save_upload(file: UploadFile, dest: str) -> bytes:
    """Read all bytes from the upload and write to dest, returning the content."""
    contents = file.file.read()
    with open(dest, "wb") as f:
        f.write(contents)
    return contents

@app.post("/api/v2/upload/image", tags=["MigDB Software Management"],
    summary="Upload a MigDB software or patch image",
    description="Validates and uploads a MigDB zip file (patch, fbo installer, or V-prefixed release) against the current OS platform, then extracts it to the processing directory.",)
async def rhp_upload_image(file: UploadFile = File(...)):
    filename = secure_filename(file.filename)
 
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid or missing filename")
 
    path_to_zip = os.path.join(image_uploads, filename)
    soft_file: list[str] = []
 
    os.makedirs(image_uploads,  exist_ok=True)
    os.makedirs(processing_dir, exist_ok=True)
 
    try:
        if filename.startswith("p"):
            parts          = filename.split("_")
            patch_platform = parts[2].replace(".zip", "").split("-")[0]
 
            if patch_platform == OS_PLAT:
                _save_upload(file, path_to_zip)
                soft_file.append(f"{filename} Uploaded Sucessfully\n")
            else:
                soft_file.append("File uploaded is not suitable for this Operating System\n")
 
        elif "fbo" in filename:
            parts       = filename.split("_")
            gg_platform = parts[3]
 
            if gg_platform == OS_PLAT:
                _save_upload(file, path_to_zip)
                soft_file.append(f"{filename} Uploaded Sucessfully\n")
            else:
                soft_file.append("File uploaded is not suitable for this Platform\n")
 
        elif filename.startswith("V"):
            _save_upload(file, path_to_zip)
 
        if os.path.exists(path_to_zip):
            with zipfile.ZipFile(path_to_zip, "r") as zf:
                zf.extractall(processing_dir)
 
            for fn in os.listdir(processing_dir):
                if "fbo" in fn:
                    parts       = fn.split("_")
                    gg_platform = parts[2]
 
                    if gg_platform != OS_PLAT:
                        shutil.rmtree(processing_dir)
                        soft_file.append("File uploaded is not suitable for this Platform\n")
                    break   # only the first fbo entry matters
 
    except OSError as e:
        soft_file.append(str(e))
 
    return JSONResponse(content=[soft_file])

@app.get("/api/v2/software/files", tags=["MigDB Software Management"],
    summary="List available MigDB software and patch files",
    description="Returns all zip files in the image uploads directory, labelled as either 'patch' (p-prefixed) or 'software' (fbo or V-prefixed).")
def list_soft_files():
    soft_files: list[dict] = []
 
    for filename in os.listdir(image_uploads):
        if not filename.endswith(".zip"):
            continue
 
        if filename.startswith("p"):
            soft_files.append({"filename": filename, "filetype": "patch"})
        elif "fbo" in filename:
            soft_files.append({"filename": filename, "filetype": "software"})
        elif filename.startswith("V"):
            soft_files.append({"filename": filename, "filetype": "software"})
 
    return JSONResponse(content=[soft_files])

class RunInsFileRequest(BaseModel):
    filename: str

def _ensure_ora_inst_loc(gg_platform: str) -> tuple[str, str]:
    """
    Return (inv_loc, inv_grp) from the system oraInst.loc if it exists,
    otherwise create one under agent_base.
    Handles Linux/AIX and Solaris separately.
    """
    if gg_platform in ("Linux", "AIX"):
        system_loc = "/etc/oraInst.loc"
    elif gg_platform == "Solaris":
        system_loc = "/var/opt/oracle/oraInst.loc"
    else:
        system_loc = "/etc/oraInst.loc"
 
    inv_loc = inv_grp = ""
 
    if os.path.exists(system_loc):
        with open(system_loc) as f:
            for line in f:
                if line.startswith("inventory_loc="):
                    inv_loc = line.split("=", 1)[-1].strip()
                elif line.startswith("inst_group="):
                    inv_grp = line.split("=", 1)[-1].strip()
        return inv_loc, inv_grp
 
    # Create a local oraInst.loc under agent_base
    inv_loc = os.path.join(agent_base, "oraInventory")
    os.makedirs(inv_loc, exist_ok=True)
    gid = os.getgid()
    inv_grp = grp.getgrgid(gid).gr_name
    agent_inst_loc = os.path.join(agent_base, "oraInst.loc")
    with open(agent_inst_loc, "w") as f:
        f.write(f"inventory_loc={inv_loc}\n")
        f.write(f"inst_group={inv_grp}\n")
    return inv_loc, inv_grp
 
 
def _resolve_ora_version(gg_base_ver: str) -> str:
    """Determine the ORA_Version string from gg_base_ver and the Oracle client version."""
    db_client_ver = oracledb.clientversion()
    main_client_ver = db_client_ver[0]
    if gg_base_ver.startswith("21"):
        return "ora21c"
    if main_client_ver > 11:
        return f"ORA{main_client_ver}c"
    return f"ORA{main_client_ver}g"
 
 
def _patch_oraparam(run_ins_dir: str, gg_base_ver: str, ora_version: str) -> str:
    """
    Back up oraparam.ini, inject the correct DEFAULT_HOME_NAME, and return
    the path to the backup so the caller can restore it afterwards.
    """
    install_dir  = os.path.join(run_ins_dir, "install")
    oraparam_ini = os.path.join(install_dir, "oraparam.ini")
    backup_path  = "oraparam.ini.orig"
    shutil.copy(oraparam_ini, backup_path)
 
    with open(backup_path) as f:
        content = f.read()
 
    home_name = f"OGG_{gg_base_ver}_{ora_version}_Home"
    content = content.replace("DEFAULT_HOME_NAME=OraHome", f"DEFAULT_HOME_NAME={home_name}")
 
    with open(oraparam_ini, "w") as f:
        f.write(content)
 
    return backup_path
 
 
def _write_response_file(run_ins_dir: str, ora_version: str, inv_loc: str, inv_grp: str) -> str:
    """Generate oggcore_oneplace.rsp and return its path."""
    response_dir   = os.path.join(run_ins_dir, "response")
    response_file  = os.path.join(response_dir, "oggcore.rsp")
    oneplace_rsp   = os.path.join(response_dir, "oggcore_oneplace.rsp")
 
    with open(response_file) as f:
        lines = f.readlines()
 
    with open(oneplace_rsp, "w") as f:
        for line in lines:
            if "INSTALL_OPTION" in line:
                f.write(f"INSTALL_OPTION={ora_version}")
            elif line.startswith("SOFTWARE_LOCATION"):
                f.write(f"SOFTWARE_LOCATION={gg_home}")
            elif "DATABASE_LOCATION" in line:
                f.write(f"DATABASE_LOCATION={db_home}")
            elif "INVENTORY_LOCATION" in line:
                f.write(f"INVENTORY_LOCATION={inv_loc}")
            elif "UNIX_GROUP_NAME" in line:
                f.write(f"UNIX_GROUP_NAME={inv_grp}")
            else:
                f.write(line)
 
    return oneplace_rsp
 
 
def _run_installer_with_response_file(run_ins_dir: str, oneplace_rsp: str) -> str:
    """Run OUI runInstaller in silent mode and return its output."""
    run_installer = os.path.join(run_ins_dir, "runInstaller")
    use_system_ptr = (
        os.path.exists("/var/opt/oracle/oraInst.loc")
        or os.path.exists("/etc/oraInst.loc")
    )
    cmd = [run_installer, "-silent", "-showProgress", "-responseFile", oneplace_rsp]
    if not use_system_ptr:
        cmd += ["-invPtrLoc", os.path.join(agent_base, "oraInst.loc")]
 
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0,
    )
    stdout, _ = proc.communicate()
    return stdout
 
 
def _rac_copy_software(run_ins: list, gg_base_ver: str, ora_version: str) -> None:
    """Copy GG software to RAC nodes and attach the home on each."""
    home_name = f"OGG_{gg_base_ver}_{ora_version}_Home"
    run_ins_home = os.path.join(gg_home, "oui", "bin", "runInstaller")
 
    for node in copy_to_nodes:
        if not node:
            continue
        run_ins.append(f"Connecting to {node} in order to setup software...")
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=node)
        scp = SCPClient(ssh_client.get_transport())
 
        ssh_client.exec_command(f"rmdir {gg_home}")
        run_ins.append(f"Copying files to remote node {node} ...")
        scp.put(gg_home, recursive=True, remote_path=gg_home)
        run_ins.append(f"Copy to remote node {node} completed ...")
 
        attach_cmd = (
            f"{run_ins_home} -silent -attachHome "
            f"ORACLE_HOME={gg_home} ORACLE_HOME_NAME={home_name}"
        )
        run_ins.append(f"Starting to attach Goldengate Home on remote node {node} ...")
        _, stdout, _ = ssh_client.exec_command(attach_cmd)
        run_ins.append(stdout.readlines())
        run_ins.append(f"Setting up software on remote node {node} completed ...")
        ssh_client.get_transport().close()
        ssh_client.close()
 
    run_ins.append("Software Setup is completed")
 
copy_to_nodes = os.environ.get("COPY_TO_NODES",    "").split(",")
def _rac_apply_patch(
    run_ins: list,
    patch_number: str,
    patch_version: str,
    patch_platform: str,
) -> None:
    """Apply patch on each RAC node via SSH."""
    opatch_dir    = os.path.join(gg_home, "OPatch", "opatch")
    patch_dir     = os.path.join(processing_dir, patch_number, patch_version, patch_platform, patch_number)
    use_system_ptr = (
        os.path.exists("/var/opt/oracle/oraInst.loc")
        or os.path.exists("/etc/oraInst.loc")
    )
 
    for node in copy_to_nodes:
        if not node:
            continue
        run_ins.append(f"Connecting to {node} in order to patch Goldengate Home...")
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=node)
 
        run_ins.append(f"Patching remote node {node}")
        if use_system_ptr:
            patch_cmd = (
                f"export ORACLE_HOME={gg_home}\n"
                f"{opatch_dir} apply {patch_dir} -silent\n"
                f"{opatch_dir} lsinventory -oh {gg_home}\n"
            )
        else:
            inv_ptr = os.path.join(agent_base, "oraInst.loc")
            patch_cmd = (
                f"export ORACLE_HOME={gg_home}\n"
                f"{opatch_dir} apply {patch_dir} -silent -invPtrLoc {inv_ptr}\n"
                f"{opatch_dir} lsinventory -oh {gg_home}\n"
            )
 
        _, stdout, _ = ssh_client.exec_command(patch_cmd)
        run_ins.append(stdout.readlines())
        run_ins.append(f"Patching on remote node {node} completed ...")

def _handle_fbo(filename: str, path_to_zip: str, run_ins: list) -> None:
    """Extract and install an fbo-style GG software archive."""
    parts       = filename.split("_")
    gg_base_ver = parts[0]
    gg_platform = parts[3]
    gg_bit      = parts[4]
    gg_vendor   = parts[5]
 
    if os.path.exists(processing_dir):
        shutil.rmtree(processing_dir)
 
    run_ins.append(f"{filename} Processing ...")
    extract_to = os.path.join(processing_dir, gg_base_ver, gg_platform, gg_bit)
    os.makedirs(extract_to, exist_ok=True)
 
    with zipfile.ZipFile(path_to_zip) as zf:
        zf.extractall(extract_to)
    run_ins.append(f"{filename} Processed Sucessfully")
 
    fbo_subdir = (
        f"fbo_ggs_{gg_platform}_{gg_bit}_Oracle_shiphome"
        if gg_vendor == "Oracle"
        else f"fbo_ggs_{gg_platform}_{gg_bit}_shiphome"
    )
    run_ins_dir = os.path.join(extract_to, fbo_subdir, "Disk1")
    run_ins.append(f"Starting runInstaller on node {h_name} to install Goldengate")
 
    _finish_install(run_ins_dir, gg_base_ver, gg_platform, run_ins)
 
def _handle_v_file(filename: str, path_to_zip: str, run_ins: list) -> None:
    """Extract and install a V-prefixed (Oracle eDelivery) GG archive."""
    if os.path.exists(processing_dir):
        shutil.rmtree(processing_dir)
 
    run_ins.append(f"{filename} Processing ...")
    with zipfile.ZipFile(path_to_zip) as zf:
        zf.extractall(processing_dir)
 
    fbo_dir     = ""
    gg_base_ver = ""
    for fn in os.listdir(processing_dir):
        if "fbo" in fn:
            fbo_dir = fn
        elif "WinUnix" in fn and fn.endswith(".pdf"):
            parts = fn.split("_")
            gg_base_ver = parts[4].replace(".pdf", "").replace(".", "")
        elif fn.endswith(".pdf"):
            m = re.search(r"_(\d+)\.(\d+)", fn)
            if m:
                gg_base_ver = f"{m.group(1)}_{m.group(2)}"
 
    parts       = fbo_dir.split("_")
    gg_platform = parts[2]
    run_ins_dir = os.path.join(processing_dir, fbo_dir, "Disk1")
    run_ins.append(f"Starting runInstaller on node {h_name} to install Goldengate")
 
    _finish_install(run_ins_dir, gg_base_ver, gg_platform, run_ins) 
 
def _finish_install(run_ins_dir: str, gg_base_ver: str, gg_platform: str, run_ins: list) -> None:
    """Shared tail of the install flow: oraInst.loc, response file, runInstaller, RAC copy."""
    chmod_dir(run_ins_dir)
 
    inv_loc = inv_grp = ""
    if gg_platform in ("Linux", "AIX", "Solaris"):
        inv_loc, inv_grp = _ensure_ora_inst_loc(gg_platform)
 
    ora_version  = _resolve_ora_version(gg_base_ver)
    backup_path  = _patch_oraparam(run_ins_dir, gg_base_ver, ora_version)
    run_ins.append(f"Goldengate Home is set to - OGG_{gg_base_ver}_{ora_version}_Home")
 
    oneplace_rsp = _write_response_file(run_ins_dir, ora_version, inv_loc, inv_grp)
    install_out  = _run_installer_with_response_file(run_ins_dir, oneplace_rsp)
    run_ins.append(install_out)
 
    # Restore original oraparam.ini
    oraparam_ini = os.path.join(run_ins_dir, "install", "oraparam.ini")
    shutil.copy(backup_path, oraparam_ini)
 
    if rac_check == "Y":
        _rac_copy_software(run_ins, gg_base_ver, ora_version)
 
def _handle_opatch_update(filename: str, path_to_zip: str, run_ins: list) -> None:
    """Unzip OPatch update (patch 6880880) directly into GG_HOME."""
    res = subprocess.run(
        ["unzip", "-o", path_to_zip, "-d", gg_home],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0,
        check=True,
    )
    run_ins.append(res.stdout)
    run_ins.append(f"{filename} Processed Sucessfully\n\n")
 
    os.environ["ORACLE_HOME"] = gg_home
    opatch_dir = os.path.join(gg_home, "OPatch", "opatch")
    proc = subprocess.Popen(
        [opatch_dir, "version"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0,
    )
    opatch_ver, _ = proc.communicate()
    run_ins.append(opatch_ver)
 
def _handle_patch(filename: str, path_to_zip: str, run_ins: list) -> None:
    """Extract and apply a standard OPatch patch."""
    parts          = filename.split("_")
    patch_number   = parts[0].lstrip("p")
    patch_version  = parts[1]
    patch_platform = parts[2].replace(".zip", "")
    opatch_dir     = os.path.join(gg_home, "OPatch", "opatch")
 
    if patch_number == "6880880":
        _handle_opatch_update(filename, path_to_zip, run_ins)
        return
 
    extract_to = os.path.join(processing_dir, patch_number, patch_version, patch_platform)
    os.makedirs(extract_to, exist_ok=True)
 
    with zipfile.ZipFile(path_to_zip) as zf:
        zf.extractall(extract_to)
    run_ins.append(f"{filename} Processed Sucessfully")
 
    patch_dir = os.path.join(extract_to, patch_number)
    chmod_dir(patch_dir)
    run_ins.append(f"Patching local node {h_name}")
 
    os.environ["ORACLE_HOME"] = gg_home
    use_system_ptr = (
        os.path.exists("/var/opt/oracle/oraInst.loc")
        or os.path.exists("/etc/oraInst.loc")
    )
    cmd = [opatch_dir, "apply", patch_dir, "-silent"]
    if not use_system_ptr:
        cmd += ["-invPtrLoc", os.path.join(gg_home, "oraInst.loc")]
 
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0,
    )
    install_out, _ = proc.communicate()
    run_ins.append(install_out)
 
    lsinv = subprocess.getoutput(f"{opatch_dir} lsinventory -oh {gg_home}")
    run_ins.append(lsinv)
 
    if rac_check == "Y":
        _rac_apply_patch(run_ins, patch_number, patch_version, patch_platform)
 
@app.post("/api/v2/install/run", tags=["MigDB Software Management"],
    summary="Install or patch MigDB from an uploaded file",
    description="Processes a MigDB fbo installer, V-prefixed release zip, or OPatch patch file and runs the appropriate installation or patching steps.",)
def view_run_ins_file(body: RunInsFileRequest):
    filename = body.filename.lstrip('"[').rstrip(']"')
    path_to_zip = os.path.join(image_uploads, filename)
    run_ins: list = []
 
    os.makedirs(gg_home, exist_ok=True)
 
    try:
        if "fbo" in filename or filename.startswith("V"):
            if "fbo" in filename:
                _handle_fbo(filename, path_to_zip, run_ins)
            else:
                _handle_v_file(filename, path_to_zip, run_ins)
 
        elif filename.startswith("p"):
            _handle_patch(filename, path_to_zip, run_ins)
 
        else:
            raise HTTPException(status_code=400, detail=f"Unrecognised filename format: {filename!r}")
 
    except subprocess.CalledProcessError as e:
        run_ins.append(str(e))
    except OSError as e:
        run_ins.append(str(e))
 
    return JSONResponse(content=[run_ins])

h_name = os.environ.get("HOSTNAME", "localhost")

_EXCLUDED_SUBDIRS = frozenset({
    "dirdat", "dirprm", "dircrd", "dirrpt",
    "dirpcs", "dirchk", "dirdmp", "dirtmp", "BR",
})

def _get_logger() -> logging.Logger:
    """Return a configured logger writing to createGoldImg.log."""
    os.makedirs(agent_log, exist_ok=True)
    log_path   = os.path.join(agent_log, "createGoldImg.log")
    log_format = "[%(asctime)s] %(levelname)s - %(message)s"
    logging.basicConfig(filename=log_path, level=logging.DEBUG, format=log_format)
    return logging.getLogger(__name__)
 
 
def _build_gold_image(gold_img_path: str, logger: logging.Logger) -> None:
    """Walk gg_home, skipping excluded subdirs and log files, and write a zip."""
    abs_gghome = os.path.abspath(gg_home)
    os.makedirs(os.path.dirname(gold_img_path), exist_ok=True)
 
    with zipfile.ZipFile(gold_img_path, "w", compression=zipfile.ZIP_LZMA) as zf:
        for dirpath, subdirs, files in os.walk(gg_home):
            # Prune excluded subdirectories in-place
            subdirs[:] = [
                d for d in subdirs
                if not any(excl in d for excl in _EXCLUDED_SUBDIRS)
            ]
            for filename in files:
                if "gglog-" in filename or filename.endswith(".log"):
                    continue
                abs_path = os.path.abspath(os.path.join(dirpath, filename))
                arc_name = abs_path[len(abs_gghome) + 1:]
                logger.info(filename)
                zf.write(abs_path, arc_name)
 
 
def _get_gg_versions() -> tuple[str, str]:    
    raw = subprocess.getoutput(f"{ggsci_bin} -v")
    lines = raw.splitlines()
    if len(lines) < 4:
        raise ValueError(f"Unexpected ggsci -v output:\n{raw}")
 
    gg_ver    = lines[2].split()[1]
    db_parts  = lines[3].split()
    oracle_idx = db_parts.index("Oracle")
    gg_db_ver = "Oracle " + db_parts[oracle_idx + 1]
    return gg_ver, gg_db_ver
 
@app.get("/api/v2/goldimage", tags=["MigDB Software Management"],
    summary="Create a MigDB gold image zip",
    description="Zips the MigDB home directory (excluding runtime dirs) into a gold image file and returns it as a downloadable zip with GG version headers.")
def create_gold_image():
    logger = _get_logger()
    logger.info("Creating Gold Image from Goldengate Home - %s", gg_home)
 
    gold_img_path = os.path.join(processing_dir, f"GoldImage_{h_name}.zip")
 
    try:
        _build_gold_image(gold_img_path, logger)
    except OSError as e:
        logger.error("Failed to create Gold Image: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to create Gold Image: {e}")
 
    logger.info("Gold Image from Goldengate Home - %s Completed", gg_home)
    logger.info("Validating Gold Image created from Goldengate Home - %s", gg_home)
    logger.info("Uploading Gold Image to central repository")
 
    try:
        gg_ver, gg_db_ver = _get_gg_versions()
    except (ValueError, IndexError) as e:
        logger.error("Failed to parse ggsci version output: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to parse ggsci version: {e}")
 
    return FileResponse(
        path=gold_img_path,
        media_type="application/zip",
        filename=os.path.basename(gold_img_path),
        headers={
            "GGVer":   gg_ver,
            "GGDBVer": gg_db_ver,
        },
    )

def _ggsci(command: str) -> str:
    """Run a single ggsci command via echo pipe and return its output."""
    return subprocess.getoutput(f"echo -e '{command}'|{ggsci_bin}")
 
 
def _write(filename: str, content: str) -> None:
    """Write content to a file in agent_log."""
    os.makedirs(agent_log, exist_ok=True)
    with open(os.path.join(agent_log, filename), "w") as f:
        f.write(content)

def _parse_pmp_trails(raw: str) -> dict[str, str]:
    """
    Parse 'info extract *' output into {pump_name: trail_path}.
    Pumps writing to Redo Logs are excluded (pmp_name reset to '').
    """
    pmp_trail_set: dict[str, str] = {}
    pmp_name = ""
 
    for line in raw.splitlines():
        if re.search(r"extract", line, re.IGNORECASE):
            parts = line.split()
            if len(parts) > 1:
                pmp_name = parts[1]
        elif re.search(r"\bredo\s+log\b", line, re.IGNORECASE):
            pmp_name = ""
        elif re.search(r"\bfile\b", line, re.IGNORECASE) and pmp_name:
            trail_name = line.split("File", 1)[-1].strip()
            parts      = trail_name.split("/")
            prefix     = parts[-1][:2]
            trail_dir  = "/".join(parts[:-1])
            trail      = f"{trail_dir}/{prefix}"
            pmp_trail_set[pmp_name] = trail
 
    return pmp_trail_set

def _parse_ext_trails(raw: str) -> dict[str, str]:
    """
    Parse 'info exttrail' output into {extract_name: trail_path}.
    """
    ext_trail_set_tmp: dict[str, str] = {}
    trail_name = ""
 
    for line in raw.splitlines():
        if re.search(r"Extract Trail", line, re.IGNORECASE):
            trail_name = line.split(":", 1)[-1].strip()
        elif "Extract" in line:
            ext_name = line.split(":", 1)[-1].strip()
            ext_trail_set_tmp[ext_name] = trail_name
 
    return ext_trail_set_tmp

def _parse_rep_trails(raw: str) -> dict[str, str]:
    """
    Parse 'info replicat * , showch' output into {replicat_name: trail_path}.
    """
    rep_trail_set: dict[str, str] = {}
    rep_name = ""
 
    for line in raw.splitlines():
        if re.search(r"REPLICAT", line, re.IGNORECASE):
            parts = line.split()
            if len(parts) > 1:
                rep_name = parts[1]
        elif re.search(r"Extract Trail", line, re.IGNORECASE) and rep_name:
            rep_trail_set[rep_name] = line.split(":", 1)[-1].strip()
 
    return rep_trail_set

def _build_trail_links(
    ext_trail_set: dict[str, str],
    pmp_trail_set: dict[str, str],
    pmp_rmt_trail_set: dict[str, str],
    rep_trail_set: dict[str, str],
) -> list[dict]:
    """
    Inner-join trail sets to produce edge records for the diagram.
    Returns a list of {start, category, end, id} dicts.
    """
    ext_df     = pd.DataFrame(list(ext_trail_set.items()),     columns=["id", "category"])
    pmp_df     = pd.DataFrame(list(pmp_trail_set.items()),     columns=["id", "category"])
    pmp_rmt_df = pd.DataFrame(list(pmp_rmt_trail_set.items()), columns=["id", "category"])
    rep_df     = pd.DataFrame(list(rep_trail_set.items()),     columns=["id", "category"])
 
    # Extract -> local trail -> Pump
    tc1 = pd.merge(ext_df, pmp_df, on=["category"], how="inner")
    tc1["id"] = np.arange(tc1.shape[0])
    tc1.columns = ["start", "category", "end", "id"]
 
    # Extract -> local trail -> Replicat (direct)
    tc2 = pd.merge(ext_df, rep_df, on=["category"], how="inner")
    tc2["id"] = np.arange(tc2.shape[0])
 
    # Pump -> remote trail -> Replicat
    tc3 = pd.merge(pmp_rmt_df, rep_df, on=["category"], how="inner")
    tc3["id"] = np.arange(tc3.shape[0])
 
    combined = np.concatenate((tc3, tc2, tc1), axis=0)
    df = pd.DataFrame(data=combined, columns=["start", "category", "end", "id"])
    return df.to_dict("records")

@app.get("/api/v2/diagram/info", tags=["MigDB Monitoring"],
    summary="Get MigDB process topology for diagram rendering",
    description="Queries extract, pump, and replicat trail info via ggsci and returns process nodes and trail links for building a replication flow diagram.")
def gg_info_diagram():
    os.makedirs(agent_log, exist_ok=True)
 
    try:
        info_ext_raw = _ggsci("info exttrail")
        info_pmp_raw = _ggsci("info extract *")
        info_rep_raw = _ggsci("info replicat * , showch")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ggsci execution failed: {e}")
 
    _write("infoext.out", info_ext_raw)
    _write("infopmp.out", info_pmp_raw)
    _write("inforep.out", info_rep_raw)
 
    pmp_trail_set     = _parse_pmp_trails(info_pmp_raw)
    ext_trail_set_tmp = _parse_ext_trails(info_ext_raw)
    rep_trail_set     = _parse_rep_trails(info_rep_raw)
 
    ext_trail_set: dict[str, str]     = {}
    pmp_rmt_trail_set: dict[str, str] = {}
 
    for name, trail in ext_trail_set_tmp.items():
        if name in pmp_trail_set:
            pmp_rmt_trail_set[name] = trail
        else:
            ext_trail_set[name] = trail
 
    process_set = {
        "uid":     "Extracts",
        "nodeext": ext_trail_set,
        "pid":     "Pump",
        "nodepmp": pmp_trail_set,
        "id":      "Replicats",
        "noderep": rep_trail_set,
    }
 
    trail_links = _build_trail_links(
        ext_trail_set,
        pmp_trail_set,
        pmp_rmt_trail_set,
        rep_trail_set,
    )
 
    return JSONResponse(content=[process_set, trail_links])


@app.get("/api/v2/monitor/all", tags=["MigDB Monitoring"],
    summary="Get status summary of all MigDB processes",
    description="Returns a high-level status snapshot of all running MigDB processes.")
def gg_monitor_all():
    val = infoall()
    return JSONResponse(content=[val[0]])
 
 
@app.get("/api/v2/info/all", tags=["MigDB Monitoring"],
    summary="Get full process info and active trail path",
    description="Returns complete process status data for all MigDB processes along with the currently active trail path.")
def gg_info_all():
    val = infoall()
    return JSONResponse(content=[val[0], trailPath])

class InfoExtRequest(BaseModel):
    extname: str

@app.post("/api/v2/extract/info", tags=["MigDB Initial Load Extract Info"],
    summary="Get status of one or more extracts",
    description="Runs info extract with tasks and returns the name and status of each matching extract process.")
def gg_info_ext(body: InfoExtRequest):
    os.makedirs(agent_log, exist_ok=True)

    extname = body.extname.lstrip('["').rstrip('"]').strip()
 
    proc = subprocess.run(
        [ggsci_bin],
        input=f"info extract {extname}, allprocesses\n",
        capture_output=True,
        text=True,
        timeout=sshTimeOut,
    )
    raw = proc.stdout

    with open(os.path.join(agent_log, "infoext.out"), "w") as f:
        f.write(raw)
 
    ext_data: list[dict] = []
    for line in raw.splitlines():
        if re.match(r"EXTRACT", line, re.IGNORECASE):
            parts = line.split()
            if len(parts) >= 2:
                ext_data.append({"extname": parts[1], "extstat": parts[-1]})

    return JSONResponse(content=[ext_data])

class InfoRepRequest(BaseModel):
    repname: str

@app.post("/api/v2/replicat/info", tags=["MigDB Replicat Operations"],
    summary="Get status of a replicat",
    description="Runs info replicat via ggsci and returns the name and current status of the matching replicat process.")
def gg_info_rep(body: InfoRepRequest):
    os.makedirs(agent_log, exist_ok=True)
 
    raw = subprocess.getoutput(
        f"echo -e 'info replicat {body.repname}'|{ggsci_bin}"
    )
 
    with open(os.path.join(agent_log, "inforep.out"), "w") as f:
        f.write(raw)
 
    rep_data: list[dict] = []
    for line in raw.splitlines():
        if re.match(r"REPLICAT", line, re.IGNORECASE):
            parts = line.split()
            if len(parts) >= 2:
                rep_data.append({"repname": parts[1], "repstat": parts[-1]})
 
    return JSONResponse(content=[rep_data])

_KEEP_KEYWORDS = frozenset({
    "ERROR", "Created", "Opened", "Credential", "subdirectories", "master",
})

_SKYLIFT_PORT   = "/home/skylift/skylift_port"
_SKYLIFT_DOMAIN = "skyliftai"
 
def _filter_lines(raw: str) -> list[str]:    
    result: list[str] = []
    for line in raw.splitlines(keepends=True):
        if any(kw in line for kw in _KEEP_KEYWORDS):
            result.append(line.split(">", 1)[-1])
    return result

@app.get("/api/v2/vaultAdd", tags=["MigDB SecureVault Management"],
    summary="Initialise MigDB SecureVault and start manager",
    description="Creates subdirs, adds a secure vault and domain, then optionally copies the manager param file and starts the manager if the skylift port file exists.")
def gg_add_cred_store():
    os.makedirs(agent_log, exist_ok=True)
    cred_store_out: list[str] = []
    proc = _spawn_ggsci()
    proc.stdin.write("create subdirs\n")
    proc.stdin.write("add credentialstore\n")
    proc.stdin.write(f"ADD CREDENTIALDOMAIN {_SKYLIFT_DOMAIN}\n")
    cred_store_out.append(_communicate(proc))
 
    if os.path.exists(_SKYLIFT_PORT):
        mgr_prm = os.path.join(gg_home, "dirprm", "mgr.prm")
        shutil.copy(_SKYLIFT_PORT, mgr_prm)
 
        proc = _spawn_ggsci()
        proc.stdin.write("start mgr\n")
        cred_store_out.append(_communicate(proc))
 
    log_path = os.path.join(agent_log, "CredStore_Out.lst")
    with open(log_path, "w") as f:
        for block in cred_store_out:
            f.write(block)
 
    with open(log_path) as f:
        cred_err_print = _filter_lines(f.read())
 
    return JSONResponse(content=[cred_err_print])

class MasterKeyActionRequest(BaseModel):
    menuAction: str

def _run_ggsci(*commands) -> str:
    proc = subprocess.Popen(
        [ggsci_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0,
    )
    stdin_payload = "\n".join(commands) + "\n"
    stdout, _ = proc.communicate(input=stdin_payload)
    proc.kill()         
    proc.stdin.close()   
    return stdout

def _purge_run_ggsci(*commands) -> str:
    proc = subprocess.Popen(
        [ggsci_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0,
    )
    stdin_payload = "\n".join(commands) + "\n"
    stdout, _ = proc.communicate(input=stdin_payload)
    proc.kill()
    proc.stdin.close()
    lines = []
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("Oracle GoldenGate"):
            continue
        if stripped.startswith("Version "):
            continue
        if stripped.startswith("Copyright"):
            continue
        if stripped.startswith("Operating system"):
            continue
        if stripped.startswith("GGSCI ("):
            continue
        if stripped.startswith("Oracle Linux"):
            continue
        lines.append(stripped)

    return lines


@app.get("/api/v2/masterkey/all", tags=["MigDB Encryption Master Key Management"],
    summary="List all Encryption Master key info from the MigDB wallet",
    description="Opens the MigDB wallet and returns master key version, creation date, and status for each key entry.")
def get_master_key() -> list[dict]:
    output = _run_ggsci("open wallet", "info masterkey")
    _write_log("infomasterkey.out", output)
 
    master_key: dict = {}
    key_name: str = ""
 
    for line in output.splitlines():
        if "name" in line.lower():
            key_name = "ENCRYPTION_MASTERKEY"
        elif re.match(r"^\d+.*$", line):
            parts = line.split()
            if len(parts) >= 3:
                master_key.setdefault(key_name, []).append(
                    {"Version": parts[0], "Created": parts[1], "Status": parts[2]}
                )
 
    return [master_key]

@app.post("/api/v2/masterkey/recreate", tags=["MigDB Encryption Master Key Management"],
    summary="Delete Existing Encryption Wallet and create a new MigDB wallet and master key",
    description="Recreates the dirwlt directory, creates a new wallet, and adds a master key. Returns filtered output with wallet and error lines.")
def create_master_key(body: MasterKeyActionRequest) -> list[list[str]]:
    _write_log("menuaction.log", f"menuAction received: {body.menuAction}\n")
    dirwlt = os.path.join(gg_home, "dirwlt")
    try:
        if os.path.exists(dirwlt):
            shutil.rmtree(dirwlt)
        os.makedirs(dirwlt, exist_ok=True)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to prepare wallet directory: {exc}",
        )
 
    output = _run_ggsci("create wallet", "open wallet", "add masterkey")
    _write_log("createmasterkey.out", output)
 
    result_lines: list[str] = []
    for line in output.splitlines():
        line = (
            line
            .replace("OGG-", "CDC-")
            .replace("OGG_DEFAULT_MASTERKEY", "ENCRYPTION_MASTERKEY")
            .replace("Oracle", "")
        )
        if "ERROR" in line:
            result_lines.append(line.split(">", 1)[-1])
        elif re.search(r"wallet", line, re.IGNORECASE):
            result_lines.append(line.split(">", 1)[-1])
 
    return [result_lines]

def _parse_masterkey_output(raw: str, version: Optional[str]) -> list:
    """
    Parse ggsci / deploy output into a list of dicts or plain strings.
    Applies OGG→CDC branding replacements before parsing.
    """
    result = []
    key_name: str = "ENCRYPTION_MASTERKEY"
 
    for line in raw.splitlines():
        line = (
            line
            .replace("OGG-", "CDC-")
            .replace("OGG_DEFAULT_MASTERKEY", "ENCRYPTION_MASTERKEY")
            .replace("Oracle", "")
        )
 
        if "name" in line.lower() and ":" in line:
            # Extract the key name that follows the colon
            key_name = line.split(":", 1)[1].strip()
 
        elif version and line.startswith(str(version)):
            parts = line.split()
            if len(parts) >= 3:
                result.append(
                    {
                        "KeyName": key_name,
                        "Version": parts[0],
                        "Created": " ".join(parts[1:-1]),  # handles spaced timestamps
                        "Status": parts[-1],
                    }
                )
 
        elif "ERROR" in line:
            result.append(line.split(">", 1)[-1].strip())
 
        elif "Wallet" in line:
            result.append(line.split(">", 1)[-1].strip())
 
    return result


class MasterKeyInfoRequest(BaseModel):
    version: str

class MasterKeyDeleteRequest(BaseModel):
    version: str

class MasterKeyDeployRequest(BaseModel):
    dep_url: str


@app.get("/api/v2/masterkey/info/{version}", tags=["MigDB Encryption Master Key Management"],
    summary="Get master key info",
    description="Retrieves master key information for a specific version from the MigDB wallet.")
def master_key_info(version: str) -> list:
    ggsci_out = _run_ggsci(
        "open wallet",
        f"info masterkey version {version}",
    )
    _write_log("ActionMasterkey.out", ggsci_out)
    parsed = _parse_masterkey_output(ggsci_out, version)
    return [parsed]


@app.post("/api/v2/masterkey/renew", tags=["MigDB Encryption Master Key Management"],
    summary="Renew master key",
    description="Renews the master key in the MigDB wallet.")
def master_key_renew() -> list:
    ggsci_out = _run_ggsci("open wallet", "renew masterkey")
    _write_log("ActionMasterkey.out", ggsci_out)
    parsed = _parse_masterkey_output(ggsci_out, version=None)
    return [parsed]


@app.delete("/api/v2/masterkey/{version}", tags=["MigDB Encryption Master Key Management"],
    summary="Delete master key version",
    description="Deletes a specific master key version from the MigDB wallet.")
def master_key_delete(version: str) -> list:
    ggsci_out = _run_ggsci(
        "open wallet",
        f"delete masterkey version {version}",
    )
    _write_log("ActionMasterkey.out", ggsci_out)
    parsed = _parse_masterkey_output(ggsci_out, version)
    return [parsed]


@app.delete("/api/v2/masterkey/wallet/purge", tags=["MigDB Encryption Master Key Management"],
    summary="Purge wallet",
    description="Purges the MigDB wallet entirely.")
def master_key_purge() -> list:
    ggsci_out = _run_ggsci("purge wallet")
    _write_log("ActionMasterkey.out", ggsci_out)
    parsed = _parse_masterkey_output(ggsci_out, version=None)
    return [parsed]


@app.post("/api/v2/masterkey/deploy", tags=["MigDB Encryption Master Key Management"],
    summary="Deploy wallet",
    description="Deploys the MigDB wallet (cwallet.sso) to a remote endpoint.")
def master_key_deploy(body: MasterKeyDeployRequest) -> list:
    wallet_file = os.path.join(gg_home, "dirwlt", "cwallet.sso")
    if not os.path.exists(wallet_file):
        raise HTTPException(
            status_code=404,
            detail=f"Wallet file not found: {wallet_file}",
        )
    deploy_url = body.dep_url.rstrip("/") + "/api/v2/masterkey/uploadwallet"
    try:
        with open(wallet_file, "rb") as payload:
            response = requests.post(
                deploy_url,
                files={"file": payload},
                verify=ssl_verify,
                timeout=30,
            )
        response.raise_for_status()
        deploy_result = response.json()
        combined_output = deploy_result[0] if deploy_result else ""
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Deploy request failed: {exc}",
        )
    _write_log("ActionMasterkey.out", combined_output)
    parsed = _parse_masterkey_output(combined_output, version=None)
    return [parsed]

def _write_log(filename: str, content: str) -> None:
    """Write content to a log file, creating the log directory if needed."""
    os.makedirs(agent_log, exist_ok=True)
    path = os.path.join(agent_log, filename)
    try:
        with open(path, "w") as fh:
            fh.write(content)
    except Exception:
        logger.exception(f"Failed writing {path}")

@app.get("/api/v2/vault/check", tags=["MigDB SecureVault Management"],
    summary="Check if secure vault exists",
    description="Verifies whether the MigDB secure vault is available. "
                "Returns 'Y' if the secure vault exists, or 'N' if it is unavailable or not configured.")
def check_cred_store() -> list[str]:
    if not os.path.exists(ggsci_bin):
        raise HTTPException(status_code=500, detail=f"ggsci not found: {ggsci_bin}")
 
    output = _run_ggsci("info credentialstore\n")
    _write_log("checkcreddom.out", output)
 
    cred_exists = "N" if "Unable" in output else "Y"
    return [cred_exists]

@app.get("/api/v2/vault/info/all", tags=["MigDB SecureVault Management"],
    summary="Retrieve secure vault details",
    description="Fetches all secure vault domains, aliases, and user mappings from the MigDB secure vault. "
                "Returns a list containing domain details, other domains, domain set, alias set, and final alias hierarchy.")
def get_cred_store() -> list:
    empty_response: list = [[], [], [], [], []]
 
    if not os.path.exists(ggsci_bin):
        logger.error(f"GGSCI not found: {ggsci_bin}")
        return empty_response
 
    info_text = _run_ggsci("info credentialstore\n")
    _write_log("creddomains.out", info_text)
 
    domains: list[str] = []
    copy = False
    for raw in info_text.splitlines():
        s = raw.strip()
        if s == "Other domains:":
            copy = True
            continue
        if copy and re.match(r"^To\b", s):
            copy = False
            continue
        if copy and s:
            domains.extend([t for t in re.split(r"[,\s]+", s) if t])
 
    seen: set = set()
    domains = [d for d in domains if not (d in seen or seen.add(d))]
 
    _write_log("othdom.out", ",".join(domains) + "," if domains else "")
 
    Dom_Det: list[dict] = []
    Dom_Set: list[str] = []
    Alias_Set: list[dict] = []
    Oth_Dom: list[dict] = []
 
    if domains:
        Oth_Dom = [{"value": d, "label": d} for d in domains]
 
        cmds = "\n".join(f"info credentialstore domain {d}" for d in domains) + "\n"
        details_text = _run_ggsci(cmds)
        _write_log("othdomdet.out", details_text)
 
        current_dom: str | None = None
        last_alias: str | None = None
 
        for line in details_text.splitlines():
            ls = line.strip()
 
            m = re.match(r"^Domain:\s*(.+)$", ls, flags=re.I)
            if m:
                current_dom = m.group(1).strip()
                Dom_Set.append(current_dom)
                last_alias = None
                continue
 
            m = re.match(r"^Alias\b\s*:?\s*(.+)$", ls, flags=re.I)
            if m:
                last_alias = m.group(1).strip()
                if current_dom:
                    Alias_Set.append({"dom": current_dom, "alias": last_alias})
                continue
 
            m = re.match(r"^Userid\b\s*:?\s*(.+)$", ls, flags=re.I)
            if m:
                uname = m.group(1).strip()
                Dom_Det.append({"alias": last_alias or "", "uname": uname})
                continue
 
    grouped: dict[str, list[str]] = {}
    for item in Alias_Set:
        grouped.setdefault(item["dom"], []).append(item["alias"])
 
    Final_Alias = [
        {
            "label": dom,
            "value": dom,
            "children": [{"label": a, "value": a} for a in aliases],
        }
        for dom, aliases in grouped.items()
    ]
 
    return [Dom_Det, Oth_Dom, Dom_Set, Alias_Set, Final_Alias]

class DBLoginRequest(BaseModel):
    domain: str
    alias: str

    @model_validator(mode="after")
    def check_not_empty(self) -> "DBLoginRequest":
        if not self.domain or not self.domain.strip():
            raise ValueError("'domain' must not be empty or whitespace")
        if not self.alias or not self.alias.strip():
            raise ValueError("'alias' must not be empty or whitespace")
        return self

def _parse_login_output(raw: str) -> list[str]:
    result: list[str] = []
 
    for line in raw.splitlines():
        if "ERROR" in line.upper():
            msg = line.split(">", 1)[-1].strip()
            if "credential store" in msg.lower():
                msg = msg.replace("credential store", "Secure Vault")
            result.append(msg)
 
        elif "database" in line:
            text = line.split(">", 1)[-1]
            text = text.split(".", 1)[0].strip()
            result.append(text)
 
        elif "@" in line:
            # Format: "... as <user>@<instance>) ..."
            after_as = line.split("as", 1)[-1]
            before_paren = after_as.split(")", 1)[0]
            parts = before_paren.split("@")
            if len(parts) == 2:
                user = parts[0].strip()
                instance = parts[1].strip()
                result.append(user)
                result.append(instance)
 
    return result
 
@app.post("/api/v2/vault/testdblogin", tags=["MigDB SecureVault Management"],
    summary="Test database login via secure vault",
    description="Validates a database login using a stored credential alias and domain from the MigDB secure vault. "
                "Runs the GGSCI dblogin command and returns parsed login results or errors.")
def test_db_login(body: DBLoginRequest) -> list[list[str]]:
    if not os.path.exists(ggsci_bin):
        raise HTTPException(status_code=500, detail=f"ggsci not found: {ggsci_bin}")
 
    command = f"dblogin useridalias {body.alias} domain {body.domain}\n"
    output = _run_ggsci(command)
 
    _write_log("TestDBLogin.lst", output)
 
    parsed = _parse_login_output(output)
    return [parsed]

class AddUserAliasRequest(BaseModel):
    domain: str
    alias: str
    user: str
    passwd: str

def _clean_gg_log(lines: list[str]) -> list[str]:
    return [
        line for line in lines
        if not line.strip().lower().startswith("operating system")
    ]

def _parse_user(user: str) -> tuple[str, str]:
    if "@" in user:
        parts = user.split("@", 1)
        return parts[0].strip(), parts[1].strip()
    return user.strip(), ""
 
 
def _save_to_db(alias: str, uname: str, passwd: str, servicename: str) -> None:
    encrypted_passwd = cipher.encrypt(passwd)
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO CONN VALUES (:dbname, :user, :passwd, :servicename)",
            {
                "dbname": alias,
                "user": uname,
                "passwd": encrypted_passwd,
                "servicename": servicename,
            },
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

@app.post("/api/v2/vault/adduseralias", tags=["MigDB SecureVault Management"],
    summary="Add a new user alias to the secure vault",
    description="Adds a new user alias with password and domain to the MigDB secure vault and persists it to the migdb sqlite database.")
def add_user_alias(body: AddUserAliasRequest) -> list[str]:
    if not os.path.exists(ggsci_bin):
        raise HTTPException(status_code=500, detail=f"ggsci not found: {ggsci_bin}")
 
    ggsci_command = (
        f"alter credentialstore add user {body.user} "
        f"password {body.passwd} "
        f"alias {body.alias} "
        f"domain {body.domain}\n"
    )
    raw_output = _run_ggsci(ggsci_command)
 
    cleaned_lines = _clean_gg_log(raw_output.splitlines(keepends=True))
    add_usr = "".join(cleaned_lines)
 
    uname, servicename = _parse_user(body.user)
 
    try:
        _save_to_db(body.alias, uname, body.passwd, servicename)
    except sqlite3.Error as exc:
        logger.error(f"SQLite error while saving credentials: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Credentials saved to ggsci but DB persistence failed: {exc}",
        )

    if "Credential store altered" in add_usr:
        return [f"User alias '{body.alias}' added successfully to MigDB SecureVault."]
    else:
        return [f"Unexpected response from CDC engine: {add_usr.strip()}"]
 
    return [add_usr]

class EditUserAliasRequest(BaseModel):
    domain: str
    alias: str
    user: str
    passwd: str

def _parse_user(user: str) -> tuple[str, str]:
    if "@" in user:
        parts = user.split("@", 1)
        return parts[0].strip(), parts[1].strip()
    return user.strip(), ""
 
 
def _update_db(alias: str, uname: str, passwd: str, servicename: str) -> None:
    encrypted_passwd = cipher.encrypt(passwd)
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO CONN (dbname, user, passwd, servicename)
               VALUES (:dbname, :user, :passwd, :servicename)""",
            {
                "dbname": alias,
                "user": uname,
                "passwd": encrypted_passwd,
                "servicename": servicename,
            },
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
 
@app.put("/api/v2/vault/edituseralias", tags=["MigDB SecureVault Management"],
    summary="Edit an existing user alias in the secure vault",
    description="Replaces the user, password, and domain for an existing alias in the MigDB secure vault and updates the database.")
def edit_user_alias(body: EditUserAliasRequest) -> list[str]:
    if not os.path.exists(ggsci_bin):
        raise HTTPException(status_code=500, detail=f"ggsci not found: {ggsci_bin}")
 
    ggsci_command = (
        f"alter credentialstore replace user {body.user} "
        f"password {body.passwd} "
        f"alias {body.alias} "
        f"domain {body.domain}\n"
    )
    raw_output = _run_ggsci(ggsci_command)
 
    cleaned_lines = _clean_gg_log(raw_output.splitlines(keepends=True))
    edit_usr = "".join(cleaned_lines)
 
    uname, servicename = _parse_user(body.user)
 
    try:
        _update_db(body.alias, uname, body.passwd, servicename)
    except sqlite3.Error as exc:
        logger.error(f"SQLite error while updating credentials: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Credentials updated in ggsci but DB persistence failed: {exc}",
        )

    if "Credential store altered" in edit_usr:
        return [f"User alias '{body.alias}' updated successfully in MigDB SecureVault."]
    else:
        return [f"Unexpected response from CDC engine: {edit_usr.strip()}"]
 
    return [edit_usr]
 
class DelUserAliasRequest(BaseModel):
    domain: str
    alias: str
    user: str

def _delete_from_db(alias: str) -> None:
    """
    Delete the connection record matching the given alias from SQLite.
    Raises sqlite3.Error on failure (caller handles logging and HTTP response).
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM CONN WHERE dbname = :dbname",
            {"dbname": alias},
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

@app.delete("/api/v2/vault/deluseralias", tags=["MigDB SecureVault Management"],
    summary="Delete a user alias from the secure vault",
    description="Removes a user alias and its domain from the MigDB secure vault and deletes the corresponding database record.")
def delete_user_alias(body: DelUserAliasRequest) -> list[str]:
    if not os.path.exists(ggsci_bin):
        raise HTTPException(status_code=500, detail=f"ggsci not found: {ggsci_bin}")
 
    ggsci_command = (
        f"alter credentialstore delete user {body.user} "
        f"alias {body.alias} "
        f"domain {body.domain}\n"
    )
    raw_output = _run_ggsci(ggsci_command)
 
    cleaned_lines = _clean_gg_log(raw_output.splitlines(keepends=True))
    del_usr = "".join(cleaned_lines)
 
    try:
        _delete_from_db(body.alias)
    except sqlite3.Error as exc:
        logger.error(f"SQLite error while deleting credentials: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Alias deleted from ggsci but DB removal failed: {exc}",
        )

    if "Credential store altered" in del_usr:
        return [f"User alias '{body.alias}' deleted successfully from MigDB SecureVault."]
    else:
        return [f"Unexpected response from CDC engine: {del_usr.strip()}"]
 
    return [del_usr]

REQUIRED_COLUMNS = {"UserName", "Password", "ServiceName", "DBName"}

def _process_row(
    cursor: sqlite3.Cursor,
    uname: str,
    passwd: str,
    servicename: str,
    dbname: str,
    domain: str,
) -> dict:
    """
    Run ggsci credentialstore add for one row and upsert into SQLite.
    Returns a result dict with alias, userid, and output/error_message.
    """
    userid = f"{uname}@{servicename}"
    ggsci_input = (
        f"alter credentialstore add user {userid} , "
        f"password {passwd} , "
        f"alias {dbname} , "
        f"domain {domain}\n"
    )
    output = _run_ggsci(ggsci_input)
 
    # Encrypt and persist — done after ggsci so plain passwd is available above
    encrypted_passwd = cipher.encrypt(passwd)
    cursor.execute(
        "INSERT OR REPLACE INTO CONN (dbname, user, passwd, servicename) "
        "VALUES (:dbname, :user, :passwd, :servicename)",
        {
            "dbname": dbname,
            "user": uname,
            "passwd": encrypted_passwd,
            "servicename": servicename,
        },
    )
 
    error_match = re.search(r"Error:.*", output)
    status_message = error_match.group(0) if error_match else "Processed"
 
    return {
        "alias": dbname,
        "userid": userid,
        "output": status_message,
    }

@app.post("/api/v2/vault/bulkupload", tags=["MigDB SecureVault Management"],
    summary="Bulk upload user aliases from Excel",
    description="Accepts an Excel file and domain, processes each row to add user aliases to the MigDB secure vault and persists them to the database.")
async def bulk_upload_excel(
    file: UploadFile = File(...),
    domain: str = Form(...),
) -> JSONResponse:
    if not os.path.exists(ggsci_bin):
        raise HTTPException(status_code=500, detail=f"ggsci not found: {ggsci_bin}")
 
    if not file.filename:
        raise HTTPException(status_code=400, detail="Empty filename")
 
    os.makedirs(processing_dir, exist_ok=True)
    file_path = os.path.join(processing_dir, file.filename)
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {exc}")
 
    try:
        df = pd.read_excel(file_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse Excel file: {exc}")
 
    if df.empty:
        raise HTTPException(status_code=400, detail="Excel file is empty")
 
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required column(s): {', '.join(sorted(missing_cols))}",
        )
 
    users_response: list[dict] = []
 
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
 
        for _, row in df.iterrows():
            uname = row.get("UserName")
            passwd = row.get("Password")
            servicename = row.get("ServiceName")
            dbname = row.get("DBName")
 
            if not all([uname, passwd, servicename, dbname]):
                users_response.append({
                    "userid": None,
                    "status": "Skipped",
                    "reason": "Missing required fields",
                })
                continue
 
            try:
                result = _process_row(
                    cursor,
                    str(uname),
                    str(passwd),
                    str(servicename),
                    str(dbname),
                    domain,
                )
                conn.commit()       
                users_response.append(result)
            except sqlite3.Error as exc:
                logger.error(f"DB error for user {uname}: {exc}")
                conn.rollback()
                users_response.append({
                    "userid": f"{uname}@{servicename}",
                    "status": "Failed",
                    "reason": f"DB error: {exc}",
                })
            except Exception as exc:
                logger.exception(f"Unexpected error for user {uname}: {exc}")
                users_response.append({
                    "userid": f"{uname}@{servicename}",
                    "status": "Failed",
                    "reason": str(exc),
                })
 
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        cursor.close()
        conn.close()
 
    return JSONResponse(
        status_code=200,
        content={
            "message": "Bulk upload completed",
            "total_processed": len(users_response),
            "details": users_response,
        },
    )

_REP_PAT = re.compile(
    r"Oracle\s+GoldenGate|ggsci|Command Interpreter for Oracle:",
    re.IGNORECASE,
)
_SKIP_PAT = re.compile(r"skylift", re.IGNORECASE)
_OGG_PAT = re.compile(r"\bOGG-", re.IGNORECASE)

class ErrLogRequest(BaseModel):
    lineNum: int
 
 
class WriteTmpPrmRequest(BaseModel):
    currentExtParamList: str
 
 
class WriteMgrPrmRequest(BaseModel):
    currentMgrParams: str
 
 
class SavePrmRequest(BaseModel):
    procName: str
    currentParams: str

@app.post("/api/v2/logs/errlog", tags=["MigDB Logs"],
    summary="Fetch error log entries",
    description="Reads ggserr.log in reverse, skips a given number of lines, and returns the next 1024 parsed log entries with branding substitutions applied.")
def get_err_log(body: ErrLogRequest) -> list:
    """
    Reads ggserr.log backwards, skips the first lineNum lines,
    then reads the next 1024 lines, applies branding substitutions,
    and returns parsed tokens alongside the new chunk offset.
    """
    line_num = body.lineNum
    chunk_size = line_num + 1024
    log_path = os.path.join(gg_home, "ggserr.log")
 
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail=f"Log file not found: {log_path}")
 
    all_data: list[dict] = []
 
    with FileReadBackwards(log_path, encoding="utf-8") as infile:
        # Skip the first lineNum lines
        for _ in zip(range(line_num), infile):
            pass
 
        # Read the next chunk (lineNum → chunkSize)
        for index, line in enumerate(infile, start=line_num):
            if index == line_num:
                # First line after skip — begin collecting from next line
                continue
 
            if index == chunk_size:
                # Reached end of chunk — stop
                break
 
            if _SKIP_PAT.search(line):
                continue
 
            line = _REP_PAT.sub("", line)
            line = _OGG_PAT.sub("CDC-", line)
 
            tokens = line.split(sep=None, maxsplit=3)
            all_data.append({"AllVal": tokens})
 
    return [all_data, chunk_size]
 
@app.post("/api/v2/params/tmp", tags=["MigDB Parameter Management"],
    summary="Write temporary parameter file",
    description="Writes the provided extract parameter list to a temporary file and returns its contents.")
def write_tmp_prm(body: WriteTmpPrmRequest) -> list[str]:
    _write_log("tmpPrm", body.currentExtParamList)
    with open(os.path.join(agent_log, "tmpPrm"), "r") as fh:
        prm_file = fh.read()
    return [prm_file]

@app.post("/api/v2/params/manager", tags=["MigDB Parameter Management"],
    summary="Save manager parameter file",
    description="Writes the provided manager parameters to mgr.prm in the MigDB dirprm directory.")
def write_mgr_prm(body: WriteMgrPrmRequest) -> list[str]:
    mgr_prm_path = os.path.join(gg_home, "dirprm", "mgr.prm")
    try:
        os.makedirs(os.path.dirname(mgr_prm_path), exist_ok=True)
        with open(mgr_prm_path, "w") as fh:
            fh.write(body.currentMgrParams)
        msg = "Saved Manager Parameterfile"
    except OSError as exc:
        logger.error(f"Failed to save mgr.prm: {exc}")
        msg = f"There is a problem in saving Parameterfile due to : {exc}"
    return [msg]

@app.post("/api/v2/params/save", tags=["MigDB Parameter Management"],
    summary="Save process parameter file",
    description="Writes the provided parameters to a named process .prm file in the MigDB dirprm directory.")
def save_prm(body: SavePrmRequest) -> list[str]:
    prm_path = os.path.join(gg_home, "dirprm", f"{body.procName}.prm")
    try:
        os.makedirs(os.path.dirname(prm_path), exist_ok=True)
        with open(prm_path, "w") as fh:
            fh.write(body.currentParams)
        msg = f"Saved {body.procName} Parameterfile"
    except OSError as exc:
        logger.error(f"Failed to save {body.procName}.prm: {exc}")
        msg = f"There is a problem in saving Parameterfile due to : {exc}"
    return [msg]

@app.get("/api/v2/params/manager", tags=["MigDB Parameter Management"],
    summary="Read manager parameter file",
    description="Reads and returns the contents of mgr.prm from the MigDB dirprm directory.")
def read_mgr_prm() -> list[str]:
    mgr_prm_path = os.path.join(gg_home, "dirprm", "mgr.prm")
    try:
        with open(mgr_prm_path, "r") as fh:
            mgr_prm_file = fh.read()
    except OSError:
        mgr_prm_file = "Please setup the parameterfile here"
    return [mgr_prm_file]

class AddInitialLoadExtRequest(BaseModel):
    jobName: str
    extname: str
    currentExtParamList: str
    startExtChk: bool

def _parse_ext_output(raw: str) -> list[str]:
    """
    Parse ggsci output and return only ERROR and 'added.' lines,
    with the ggsci prompt prefix (everything up to '>') stripped.
    """
    result: list[str] = []
    for line in raw.splitlines():
        if "ERROR" in line:
            result.append(line.split(">", 1)[-1].strip())
        elif "added." in line:
            result.append(line.split(">", 1)[-1].strip())
    return result

@app.post("/api/v2/extract/addinitialload", tags=["MigDB Heterogeneous Initial Load"],
    summary="Add an initial load extract process",
    description="Creates the trail directory and parameter file, registers the extract process in MigDB, and optionally starts it.")
def add_initial_load_ext(body: AddInitialLoadExtRequest) -> list[list[str]]:
    if not os.path.exists(ggsci_bin):
        raise HTTPException(status_code=500, detail=f"ggsci not found: {ggsci_bin}")
 
    job_trail_dir = os.path.join(trail_path, body.jobName)
    try:
        os.makedirs(job_trail_dir, exist_ok=True)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create trail directory '{job_trail_dir}': {exc}",
        )
 
    ext_prm_path = os.path.join(gg_home, "dirprm", f"{body.extname}.prm")
    try:
        os.makedirs(os.path.dirname(ext_prm_path), exist_ok=True)
        with open(ext_prm_path, "w") as fh:
            fh.write(body.currentExtParamList)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write parameter file '{ext_prm_path}': {exc}",
        )
 
    commands = [f"add extract {body.extname},SOURCEISTABLE"]
    if not body.startExtChk:
        commands.append(f"start extract {body.extname}")
 
    raw_output = _run_ggsci(*commands)
 
    _write_log("AddInitialExtErr.lst", raw_output)
    parsed = _parse_ext_output(raw_output)
 
    return [parsed]

class AddCSVILProcRequest(BaseModel):
    srcdep: str
    srcdomain: str
    srcalias: str
    tgtdep: str
    rsAlias: str
    tabSplit: str
    schemaList: list
    jobName: str
    cdbCheck: str       
    pdbName: str
    currentSCN: str
    parallel: int
    currentAWSBucket: str
    aws_access_key_id: str
    aws_secret_access_key: str
    currentBDA: str

def _get_flashback_scn_and_table_list(
    srcalias: str,
    cdb_check: str,
    pdb_name: str,
    job_name: str,
) -> tuple[str, list[str]]:
    """
    Opens a DB connection via selectConn, optionally switches to the PDB
    container, fetches the current flashback SCN, and returns the table
    list file path along with any status/error messages.
 
    Returns:
        (table_list_file, messages) — messages is a list of status strings.
    """
    messages: list[str] = []
    table_list_file: str = ""
    con = None
 
    try:
        con = selectConn(srcalias)[0]
        cursor = con.cursor()
 
        if cdb_check == "YES" and pdb_name:
            cursor.execute(f"ALTER SESSION SET CONTAINER={pdb_name}")
            table_list_file = os.path.join(
                agent_home, job_name, f"{job_name}_{pdb_name}_tables"
            )
        else:
            table_list_file = os.path.join(agent_home, job_name, f"{job_name}_tables")
 
        cursor.execute(
            "SELECT dbms_flashback.get_system_change_number FROM dual"
        )
        db_row = cursor.fetchone()
        scn = db_row[0] if db_row else "unknown"
        messages.append(f"Creating initialload at SCN - {scn}")
 
    except Exception as exc:
        logger.exception("Failed to fetch flashback SCN")
        messages.append(str(exc))
 
    finally:
        if con:
            cursor.close()
            con.close()
 
    return table_list_file, messages
 
 
def _register_job_and_get_target_url(
    job_name: str,
    srcdep: str,
    tgtdep: str,
    current_bda: str,
) -> tuple[str, list[str]]:
    """
    Looks up the target deployment URL from SQLite and inserts the job
    record into the ILCSV table.
 
    Returns:
        (tgt_dep_url, error_messages)
    """
    tgt_dep_url: str = ""
    errors: list[str] = []
    conn = None
 
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
 
        cursor.execute(
            "SELECT dep_url FROM ONEPCONN WHERE dep = :tgtdep",
            {"tgtdep": tgtdep},
        )
        db_row = cursor.fetchone()
        if db_row:
            tgt_dep_url = db_row[0]
        else:
            logger.warning(f"No dep_url found for tgtdep='{tgtdep}'")
 
        cursor.execute(
            "INSERT INTO ILCSV VALUES (:jobname, :srcdep, :tgtdep, :tgtdeptype)",
            {
                "jobname": job_name,
                "srcdep": srcdep,
                "tgtdep": tgtdep,
                "tgtdeptype": current_bda,
            },
        )
        conn.commit()
 
    except sqlite3.OperationalError as exc:
        logger.error(f"SQLite error registering job '{job_name}': {exc}")
        errors.append(str(exc))
 
    finally:
        if conn:
            cursor.close()
            conn.close()
 
    return tgt_dep_url, errors

@app.post("/api/v2/initialload/csv", tags=["MigDB Heterogeneous Initial Load"],
    summary="Start a CSV-based initial load job",
    description="Fetches the flashback SCN, registers the job in the database, resolves the target deployment URL, and launches a background thread to process tables via CSV.")
def add_csv_il_proc(body: AddCSVILProcRequest) -> list[str]:    
    # ── Step 1: fetch flashback SCN and determine table list file ────────────
    table_list_file, scn_messages = _get_flashback_scn_and_table_list(
        srcalias=body.srcalias,
        cdb_check=body.cdbCheck,
        pdb_name=body.pdbName,
        job_name=body.jobName,
    )
 
    # ── Step 2: register job in SQLite and resolve target deployment URL ─────
    tgt_dep_url, db_errors = _register_job_and_get_target_url(
        job_name=body.jobName,
        srcdep=body.srcdep,
        tgtdep=body.tgtdep,
        current_bda=body.currentBDA,
    )
 
    all_messages = scn_messages + db_errors
 
    # ── Step 3: launch background table iteration thread ────────────────────
    # Thread is only started when the DB registration block completed
    # (even partially), matching original finally-block behaviour.
    if not db_errors:
        il_thread = threading.Thread(
            target=table_itter_rows,
            args=(
                table_list_file,
                body.srcalias,
                body.rsAlias,
                body.cdbCheck,
                body.pdbName,
                body.currentAWSBucket,
                body.jobName,
                body.aws_access_key_id,
                body.aws_secret_access_key,
                body.parallel,
                tgt_dep_url,
            ),
            daemon=True,   # thread won't block server shutdown
        )
        il_thread.start()
        logger.info(f"Initial load thread started for job '{body.jobName}'")
    else:
        logger.warning(
            f"Skipping table iteration thread for job '{body.jobName}' due to DB errors."
        )
 
    return all_messages

class CSVILProcMonRequest(BaseModel):
    jobName: str
    tabList: list
    tgtdepurl: str

def _load_summary(job_name: str) -> pd.DataFrame:
    """
    Load the job summary CSV into a DataFrame.
    Raises HTTPException 404 if the file is missing.
    """
    summary_path = os.path.join(agent_home, job_name, f"{job_name}_Summary")
    if not os.path.exists(summary_path):
        raise HTTPException(
            status_code=404,
            detail=f"Summary file not found: {summary_path}",
        )
    try:
        return pd.read_csv(summary_path)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read summary file: {exc}",
        )
 
 
def _apply_ext_stats(df: pd.DataFrame, job_name: str) -> pd.DataFrame:
    """
    Read all *_stats files for the job, accumulate extract rows processed
    and elapsed time into the DataFrame, then delete each stats file.
 
    Stats file format (single line): "<processed_rows>-<elapsed_time>"
    File name format: "<TabName>=+!<suffix>_stats"
    """
    stats_pattern = os.path.join(agent_home, job_name, "*_stats")
 
    for stats_file in glob.glob(stats_pattern):
        try:
            with open(stats_file) as fh:
                content = fh.read().strip()
            os.remove(stats_file)
        except OSError as exc:
            logger.warning(f"Could not read/remove stats file '{stats_file}': {exc}")
            continue
 
        parts = content.split("-", 1)
        if len(parts) != 2:
            logger.warning(f"Unexpected stats format in '{stats_file}': {content!r}")
            continue
 
        raw_rows, ext_elapsed = parts
        processed_rows = int(raw_rows) if raw_rows.strip() else 0
 
        # Extract table name: basename up to the '=+!' separator
        base_name = os.path.basename(stats_file)
        tab_name = base_name.split("=+!")[0]
 
        mask = df["TabName"] == tab_name
        if mask.any():
            df.loc[mask, "EXT_ROWS_PROCESSED"] = (
                df.loc[mask, "EXT_ROWS_PROCESSED"] + processed_rows
            )
            df.loc[mask, "EXT_ELAPSED"] = ext_elapsed
        else:
            logger.warning(f"TabName '{tab_name}' not found in summary DataFrame")
 
    return df
 
 
def _fetch_rep_stats(
    tgt_dep_url: str,
    job_name: str,
    tab_list: list,
) -> dict:
    """
    POST to the remote deployment monitor endpoint and return the
    replication stats dict from the first element of the JSON response.
    Returns an empty dict on any failure.
    """
    url = tgt_dep_url.rstrip("/") + "/api/v2/initialload/csv/monitor"
    payload = {"jobName": job_name, "tabList": tab_list}
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            verify=ssl_verify,
            timeout=ssh_timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data[0] if data and len(data) > 0 else {}
    except requests.RequestException as exc:
        logger.error(f"Failed to fetch rep stats from '{url}': {exc}")
        return {}
 
 
def _apply_rep_stats(df: pd.DataFrame, rep_stats: dict) -> pd.DataFrame:
    """
    Apply replication stats (rows processed + elapsed) from the remote
    endpoint into the summary DataFrame.
    """
    for tab_name, values in rep_stats.items():
        mask = df["TabName"] == tab_name
        if not mask.any():
            logger.warning(f"TabName '{tab_name}' from rep stats not in summary")
            continue
        try:
            df.loc[mask, "REP_ROWS_PROCESSED"] = (
                df.loc[mask, "REP_ROWS_PROCESSED"] + int(values["REP_ROWS_PROCESSED"])
            )
            df.loc[mask, "REP_ELAPSED"] = values["REP_ELAPSED"]
        except (KeyError, ValueError) as exc:
            logger.warning(f"Skipping rep stats for '{tab_name}': {exc}")
    return df
 
 
def _save_summary(df: pd.DataFrame, job_name: str) -> None:
    """Persist the updated DataFrame back to the summary CSV."""
    summary_path = os.path.join(agent_home, job_name, f"{job_name}_Summary")
    try:
        df.to_csv(summary_path, index=False, header=True)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save summary file: {exc}",
        )
    
@app.post("/api/v2/initialload/csv/monitor", tags=["MigDB Heterogeneous Initial Load"],
    summary="Monitor a CSV initial load job",
    description="Loads the job summary, applies extract and replicat statistics, updates the summary file, and returns the current progress of all tables in the job.")
def csv_il_proc_mon(body: CSVILProcMonRequest) -> list[list[dict]]:
    df = _load_summary(body.jobName) 
    df = _apply_ext_stats(df, body.jobName) 
    rep_stats = _fetch_rep_stats(body.tgtdepurl, body.jobName, body.tabList) 
    if rep_stats:
        df = _apply_rep_stats(df, rep_stats) 
    _save_summary(df, body.jobName) 
    return [df.to_dict("records")]

class TabSplitItem(BaseModel):
    TABLE_NAME: str
 
 
class AddAutoILProcRequest(BaseModel):
    srcdep: str
    srcdomain: str
    srcalias: str
    tgtdep: str
    tgtdomain: str
    tgtalias: str
    chktbl: Optional[str] = None
    tabSplit: list[TabSplitItem]
    schemaList: list[str]
    jobName: str
    cdbCheck: str
    pdbName: str
    currentSCN: str
    deferStart: bool
 
 
def _build_status(defer_start: bool) -> str:
    if defer_start is False:
        return "RUNNING"
    elif defer_start is True:
        return "STOPPED"
    return "ABENDED"
 
 
def _post(url: str, payload: dict, headers: dict) -> requests.Response | None:
    try:
        resp = requests.post(url, json=payload, headers=headers, verify=ssl_verify, timeout=ssh_timeout)
        resp.raise_for_status()
        return resp
    except requests.exceptions.ConnectionError:
        return None
    except requests.RequestException as exc:
        logger.error(f"Request to {url} failed: {exc}")
        return None
 
 
def _insert_ilext(cursor, job_name, srcdep, srcdomain, srcalias, ext_name, status, trail_name, conn):
    cursor.execute(
        "INSERT INTO ILEXT VALUES (:jobname,:srcdep,:domain,:alias,:extname,:status,:srctrail)",
        {"jobname": job_name, "srcdep": srcdep, "domain": srcdomain, "alias": srcalias,
         "extname": ext_name, "status": status, "srctrail": trail_name},
    )
    conn.commit()
 
 
def _insert_ilrep(cursor, job_name, tgtdep, tgtdomain, tgtalias, rep_name, status, trail_name, conn):
    cursor.execute(
        "INSERT INTO ILREP VALUES (:jobname,:tgtdep,:domain,:alias,:repname,:status,:tgttrail)",
        {"jobname": job_name, "tgtdep": tgtdep, "domain": tgtdomain, "alias": tgtalias,
         "repname": rep_name, "status": status, "tgttrail": trail_name},
    )
    conn.commit()
 
 
def _dispatch_ext_rep(src_api_url, tgt_api_url, src_payload, tgt_payload, headers,
                      cursor, conn, job_name, srcdep, srcdomain, srcalias,
                      tgtdep, tgtdomain, tgtalias, ext_name, rep_name, trail_name, status,
                      result_array, dbtype, tgt_header):

    src_req = _post(src_api_url, src_payload, headers)

    if(dbtype=='mongodb'):
        headers = tgt_header
    tgt_req = _post(tgt_api_url, tgt_payload, headers)
 
    if src_req is None or tgt_req is None:
        result_array.append("Remote Deployment Not reachable")
        return
 
    src_data = src_req.json()
    if src_data and len(src_data[0]) > 0:
        result_array.append(src_data[0][0])
        _insert_ilext(cursor, job_name, srcdep, srcdomain, srcalias, ext_name, status, trail_name, conn)
 
    tgt_data = tgt_req.json()

    if isinstance(tgt_data, dict):
        # MongoDB replicat response shape: {'status', 'message', 'details', ...}
        if tgt_data.get('status') == 'success':
            result_array.append(tgt_data.get('message', ''))
            _insert_ilrep(cursor, job_name, tgtdep, tgtdomain, tgtalias, rep_name, status, trail_name, conn)
        else:
            result_array.append(tgt_data.get('message', 'Unknown error creating replicat'))
    elif tgt_data and len(tgt_data) > 0 and len(tgt_data[0]) > 0:
        result_array.append(tgt_data[0][0])
        _insert_ilrep(cursor, job_name, tgtdep, tgtdomain, tgtalias, rep_name, status, trail_name, conn)

def _get_tgt_auth_headers(local_base_url: str, tgtdep: str, dbtype: str, base_headers: dict) -> dict:
    """Return headers augmented with a Bearer token when the target is MongoDB."""
    headers = dict(base_headers)
    if dbtype == "mongodb":
        token_resp = requests.post(
            local_base_url.rstrip("/") + "/api/v2/onep/deptoken",
            json={"dep": tgtdep},
            headers=headers,
            timeout=sshTimeOut,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        headers["Authorization"] = f"Bearer {token_data['access_token']}"
    return headers

@app.post("/api/v2/initialload/auto", tags=["MigDB Heterogeneous Initial Load"],
    summary="Create automatic initial load processes",
    description="Builds and dispatches extract and replicat processes for an automatic initial load job across source and target deployments.")
def add_auto_il_proc(body: AddAutoILProcRequest) -> list:
    headers = get_internal_headers() 
    status = _build_status(body.deferStart)
    result_array: list[str] = []
    conn = None
 
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
 
        ilext_df = pd.read_sql_query(
            "SELECT DISTINCT b.dep_priv_url url_src, b.dbtype db_type FROM onepconn b WHERE b.dep=?",
            conn, params=[body.srcdep],
        )
        src_api_url = ""
        url_src = ""
        for _, row in ilext_df.iterrows():
            url_src = row["url_src"]
            src_api_url = row["url_src"] + "/api/v2/extract/addinitialload"
            
 
        ilrep_df = pd.read_sql_query(
            "SELECT DISTINCT b.dep_url url_tgt, b.dbtype db_type, user, passwd FROM onepconn b WHERE b.dep=?",
            conn, params=[body.tgtdep],
        )
        url_tgt = ""
        dbtype = ""
        for _, row in ilrep_df.iterrows():
            url_tgt = row["url_tgt"]
            dbtype = row["db_type"]
 
        tgt_api_url = url_tgt + "/api/v2/replicat/addinitialload"
        tgt_mgr_url = url_tgt + "/api/v2/onep/rmthostmgr"

        tgt_db_login = f"useridalias {body.tgtalias} domain {body.tgtdomain}"      
        tgt_headers = headers 

        if(dbtype=='mongodb'):
            tgt_api_url = url_tgt + "/api/v2/addMongoReplicat"
            tgt_mgr_url = url_tgt + "/api/v2/ggRmtHostMgr"

            tgt_headers = _get_tgt_auth_headers(url_src, body.tgtdep, dbtype, headers)

            tgt_db_login = ""
            response = requests.get(tgt_mgr_url, headers=tgt_headers, timeout=sshTimeOut)
        else:
            response = requests.get(tgt_mgr_url, timeout=sshTimeOut)    
        

        src_env =  f"SETENV (TNS_ADMIN = {db_home}/network/admin)"
        rmtport, rmthost = response.json()
        src_db_login = f"useridalias {body.srcalias} domain {body.srcdomain}"
        report_rate = "REPORTCOUNT EVERY 1 MINUTES,RATE"
        batch_sql = "BATCHSQL BATCHESPERQUEUE 100, OPSPERBATCH 40000"
        sql_pred = f",SQLPREDICATE 'AS OF SCN {body.currentSCN}';"
 
        df_name = ""
        df_iltables = pd.DataFrame()
        for df_name in glob.glob(os.path.join(agent_home, body.jobName, "*tables")):
            df_iltables = pd.read_csv(df_name, index_col=False)

        tab_exclude = ""
 
        for i, item in enumerate(body.tabSplit):
            name = item.TABLE_NAME
            ext_name = f"E{body.jobName}{i}"
            rep_name = f"R{body.jobName}{i}"
            trail_name = os.path.join(trail_path, body.jobName, f"Z{i}")
            ext_param = f"EXTRACT {ext_name}\n{src_env}\n{src_db_login}\n"
            rep_param = f"REPLICAT {rep_name}\n{tgt_db_login}\n"

            src_pdb = f"SOURCECATALOG {body.pdbName}\n" if body.cdbCheck == "YES" else ""
            map_src_prefix = f"{body.pdbName}." if body.cdbCheck == "YES" else ""

            if body.srcdep == body.tgtdep:
                ext_prm = f"{ext_param}extfile {trail_name}\n{report_rate}\n{src_pdb}TABLE {name}{sql_pred}"
            else:
                ext_prm = (f"{ext_param}\nRMTHOST {rmthost},MGRPORT {rmtport}, "
                        f"TCPBUFSIZE 8388608, TCPFLUSHBYTES 8388608 \nrmtfile {trail_name}\n"
                        f"{report_rate}\n{src_pdb}TABLE {name}{sql_pred}")

                if(dbtype=='mongodb'):
                    ext_prm = (f"{ext_param}\nRMTHOST {rmthost},PORT {rmtport}, "
                        f"TCPBUFSIZE 8388608, TCPFLUSHBYTES 8388608 \nrmtfile {trail_name}\n"
                        f"{report_rate}\nTABLE {name}{sql_pred}")
                
            rep_prm = f"{rep_param}{report_rate}\n{batch_sql}\nMAP {map_src_prefix}{name},TARGET {name};"

            if(dbtype=='mongodb'):
                rep_prm = f"MAP {name},TARGET {name};"
 
            src_payload = {"jobName": body.jobName, "extname": ext_name,
                           "currentExtParamList": ext_prm, "startExtChk": False}
            tgt_payload = {"jobName": body.jobName, "repname": rep_name, "tgtdomain": body.tgtdomain,
                           "tgtalias": body.tgtalias, "repmode": "classic",
                           "currentRepParamList": rep_prm, "trail": trail_name,
                           "chktbl": body.chktbl or "", "startRepChk": False, "tgtdep": body.tgtdep}

            if(dbtype=='mongodb'):
                tgt_payload = {
                   "repname": rep_name,
                   "domain": body.tgtdomain,
                   "alias": body.tgtalias,
                   "trail": trail_name,
                   "startRepChk": False,
                   "currentParamList": rep_prm,
                   "jobName": body.jobName,
                   "tgtdep": body.tgtdep,
                   "tgtdomain": body.tgtdomain,
                   "tgtalias": body.tgtalias,
                   "initialLoad": True,
                }
 
            _dispatch_ext_rep(
                src_api_url, tgt_api_url, src_payload, tgt_payload, headers,
                cursor, conn, body.jobName, body.srcdep, body.srcdomain, body.srcalias,
                body.tgtdep, body.tgtdomain, body.tgtalias,
                ext_name, rep_name, trail_name, status, result_array, dbtype, tgt_headers,
            )
 
            tab_exclude += f"TABLEEXCLUDE {name}\n"
            if not df_iltables.empty:
                mask = df_iltables["OWNER"] + "." + df_iltables["TABLE_NAME"] == name
                df_iltables.loc[mask, "PROC"] = ext_name
 
        ext_name_aa = f"E{body.jobName}AA"
        rep_name_aa = f"R{body.jobName}AA"
        trail_name_aa = os.path.join(trail_path, body.jobName, "ZZ")
        ext_param_aa = f"EXTRACT {ext_name_aa}\n{src_env}\n{src_db_login}\n"
        rep_param_aa = f"REPLICAT {rep_name_aa}\n{tgt_db_login}\n"
 
        ext_table_maps = ""
        rep_table_maps = ""
        map_src_prefix = f"{body.pdbName}." if body.cdbCheck == "YES" else ""
        src_pdb = f"SOURCECATALOG {body.pdbName}\n" if body.cdbCheck == "YES" else ""

        for schema in body.schemaList:
            ext_table_maps += f"TABLE {schema}.*{sql_pred}\n"
            if dbtype == 'mongodb':
                rep_table_maps += f"MAP {schema}.*,TARGET {schema}.*;\n"
            else:
                rep_table_maps += f"MAP {map_src_prefix}{schema}.*,TARGET {schema}.*;\n"

        ext_middle = f"{tab_exclude}\n{ext_table_maps}" if body.tabSplit else ext_table_maps
 
        if body.srcdep == body.tgtdep:
            ext_prm_aa = f"{ext_param_aa}extfile {trail_name_aa}\n{report_rate}\n{src_pdb}{ext_middle}"
        else:
            ext_prm_aa = (f"{ext_param_aa}\nRMTHOST {rmthost},MGRPORT {rmtport}, "
                  f"TCPBUFSIZE 8388608, TCPFLUSHBYTES 8388608 \nrmtfile {trail_name_aa}\n"
                  f"{report_rate}\n{src_pdb}{ext_middle}")

            if(dbtype=='mongodb'):
                ext_prm_aa = (f"{ext_param_aa}\nRMTHOST {rmthost},PORT {rmtport}, "
                    f"TCPBUFSIZE 8388608, TCPFLUSHBYTES 8388608 \nrmtfile {trail_name_aa}\n"
                    f"{report_rate}\n{ext_middle}")


        rep_prm_aa = f"{rep_param_aa}{report_rate}\n{batch_sql}\n{rep_table_maps}"

        if(dbtype=='mongodb'):
            rep_prm_aa = f"{rep_table_maps}"
 
        mgr_prm_load = {
            "prmFile": "mgr.prm",
            "prmContent": f"\nPURGEOLDEXTRACTS {os.path.join(trail_name_aa, body.jobName)}/*,USECHECKPOINTS",
        }
        #_post(url_tgt + "/updatemgrfiles", mgr_prm_load, headers)
        
        if(dbtype != 'mongodb'):
             _post(url_tgt + "/api/v2/gg/mgr/ops", {"mgrOps": "mgrrefresh"}, headers)
 
        if not df_iltables.empty:
            if "PROC" in df_iltables.columns and "'PROC'" in df_iltables.columns:
                df_iltables.drop(columns=["PROC"], inplace=True)
            df_iltables.rename(columns={"'PROC'": "PROC"}, inplace=True)

            proc_col = df_iltables["PROC"].astype(str).str.strip().str.lower()
            unassigned = df_iltables["PROC"].isna() | (proc_col == "") | (proc_col == "proc")
            df_iltables.loc[unassigned, "PROC"] = ext_name_aa

            logger.info(f"Writing updated PROC column to: {df_name}")
            df_iltables.to_csv(df_name, index=False)

        src_payload_aa = {"jobName": body.jobName, "extname": ext_name_aa,
                          "currentExtParamList": ext_prm_aa, "startExtChk": False}
        tgt_payload_aa = {"jobName": body.jobName, "repname": rep_name_aa, "tgtdomain": body.tgtdomain,
                          "tgtalias": body.tgtalias, "repmode": "classic",
                          "currentRepParamList": rep_prm_aa, "trail": trail_name_aa,
                          "chktbl": body.chktbl or "", "startRepChk": False, "tgtdep": body.tgtdep}

        if(dbtype=='mongodb'):
            tgt_payload_aa = {
                "repname": rep_name_aa,
                "domain": body.tgtdomain,
                "alias": body.tgtalias,
                "trail": trail_name_aa,
                "startRepChk": False,
                "currentParamList": rep_prm_aa,
                "jobName": body.jobName,
                "tgtdep": body.tgtdep,
                "tgtdomain": body.tgtdomain,
                "tgtalias": body.tgtalias,
                "initialLoad": True,
            }
 
        _dispatch_ext_rep(
            src_api_url, tgt_api_url, src_payload_aa, tgt_payload_aa, headers,
            cursor, conn, body.jobName, body.srcdep, body.srcdomain, body.srcalias,
            body.tgtdep, body.tgtdomain, body.tgtalias,
            ext_name_aa, rep_name_aa, trail_name_aa, status, result_array, dbtype, tgt_headers,
        )
 
        os.makedirs(agent_log, exist_ok=True)
        log_path = os.path.join(agent_log, "AddAutoProc.lst")
        with open(log_path, "w") as fh:
            for line in result_array:
                fh.write(line)
 
    except sqlite3.DatabaseError as exc:
        logger.error(f"Database error: {exc}")
        result_array.append(str(exc))
 
    finally:
        if conn:
            cursor.close()
            conn.close()
 
    return [result_array]
 
class AddILEXTRequest(BaseModel):
    jobName: str
    srcdep:  str
    extname: str
    trail:   str
 
 
class DelILEXTRequest(BaseModel):
    jobName: str
    srcdep:  str
    extname: str
 
 
class AddInitialLoadRepRequest(BaseModel):
    jobName:             str
    repname:             str
    tgtdomain:           str
    tgtalias:            str
    repmode:             str
    currentRepParamList: str
    startRepChk:         bool
    trail:               str | None = None
    chktbl:              str | None = None
 
 
class AddILREPRequest(BaseModel):
    jobName: str
    tgtdep:  str
    repname: str
    trail:   str
 
 
class DelILREPRequest(BaseModel):
    jobName: str
    tgtdep:  str
    repname: str
 
 
class ProcessActionRequest(BaseModel):
    processName: list[dict]
    ops:         str
 
 
class ILTablesRequest(BaseModel):
    JobName: str 
 
def _filter_rep_output(raw: str) -> list[str]:
    """Keep lines containing 'ERROR' or 'added.', stripping GGSCI prompts."""
    result: list[str] = []
    for line in raw.splitlines(keepends=True)[8:]:
        if "ERROR" in line or "added." in line:
            result.append(line.split(">", 1)[-1])
    return result
 
@app.post("/api/v2/il/ext/add", tags=["MigDB Heterogeneous Initial Load"],
    summary="Add an initial load extract record",
    description="Inserts a new extract record into the ILEXT table with job name, source deployment, extract name, and trail path.")
def add_ilext(body: AddILEXTRequest):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO ILEXT VALUES (:jobname, :srcdep, :extname, :srctrail)",
            {"jobname": body.jobName, "srcdep": body.srcdep,
             "extname": body.extname, "srctrail": body.trail},
        )
        conn.commit()
        msg = "Successfully Inserted"
    except sqlite3.DatabaseError as e:
        msg = str(e)
    finally:
        conn.close()
    return JSONResponse(content=[msg])
 
 
@app.delete("/api/v2/il/ext/delete", tags=["MigDB Heterogeneous Initial Load"],
    summary="Delete an initial load extract record",
    description="Removes an extract record from the ILEXT table matching the given job name, source deployment, and extract name.")
def del_ilext(body: DelILEXTRequest):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "DELETE FROM ILEXT WHERE extname=:extname AND srcdep=:srcdep AND jobname=:jobname",
            {"srcdep": body.srcdep, "extname": body.extname, "jobname": body.jobName},
        )
        conn.commit()
        msg = "Successfully Deleted"
    except sqlite3.DatabaseError as e:
        msg = str(e)
    finally:
        conn.close()
    return JSONResponse(content=[msg])

@app.post("/api/v2/il/rep/add-initial", tags=["MigDB Heterogeneous Initial Load"],
    summary="Add an initial load replicat process",
    description="Writes the replicat parameter file, registers the replicat in MigDB with the specified mode (classic, parallel, integrated, coordinated, or SPECIALRUN), and optionally starts it.")
def add_initial_load_rep(body: AddInitialLoadRepRequest):
    os.makedirs(agent_log, exist_ok=True)
 
    # Write param file
    prm_path = os.path.join(gg_home, "dirprm", body.repname + ".prm")
    with open(prm_path, "w") as f:
        f.write(body.currentRepParamList)
 
    proc   = _spawn_ggsci()
    mode   = body.repmode
    name   = body.repname
    trail  = body.trail  or ""
    chktbl = body.chktbl or ""
 
    if mode == "parallel":
        proc.stdin.write(
            f"add replicat {name},{mode},exttrail {trail},checkpointtable {chktbl}\n"
        )
    elif mode == "integrated":
        proc.stdin.write(f"add replicat {name},{mode},exttrail {trail}\n")
    elif mode in ("", "classic"):
        proc.stdin.write(
            f"add replicat {name},exttrail {trail},checkpointtable {chktbl}\n"
        )
    elif mode == "coordinated":
        proc.stdin.write(
            f"add replicat {name},{mode},exttrail {trail},checkpointtable {chktbl}\n"
        )
    elif mode == "SPECIALRUN":
        proc.stdin.write(f"add replicat {name},{mode}\n")
 
    if body.startRepChk is False:
        proc.stdin.write(f"start replicat {name}\n")
 
    raw = _communicate(proc)
 
    # Persist and filter output
    log_path = os.path.join(agent_log, "AddInitialRepErr.lst")
    with open(log_path, "w") as f:
        f.write(raw)
    with open(log_path) as f:
        rep_err_print = _filter_rep_output(f.read())
 
    return JSONResponse(content=[rep_err_print])

@app.post("/api/v2/il/rep/add", tags=["MigDB Heterogeneous Initial Load"],
    summary="Add an initial load replicat record",
    description="Inserts a new replicat record into the ILREP table with job name, target deployment, replicat name, and trail path.")
def add_ilrep(body: AddILREPRequest):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO ILREP VALUES (:jobname, :tgtdep, :repname, :tgttrail)",
            {"jobname": body.jobName, "tgtdep": body.tgtdep,
             "repname": body.repname, "tgttrail": body.trail},
        )
        conn.commit()
        msg = "Successfully Inserted"
    except sqlite3.DatabaseError as e:
        msg = str(e)
    finally:
        conn.close()
    return JSONResponse(content=[msg])
 
 
@app.delete("/api/v2/il/rep/delete", tags=["MigDB Heterogeneous Initial Load"],
    summary="Delete an initial load replicat record",
    description="Removes a replicat record from the ILREP table matching the given job name, target deployment, and replicat name.")
def del_ilrep(body: DelILREPRequest):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "DELETE FROM ILREP WHERE jobname=:jobname AND repname=:repname AND tgtdep=:tgtdep",
            {"jobname": body.jobName, "tgtdep": body.tgtdep, "repname": body.repname},
        )
        conn.commit()
        msg = "Successfully Deleted"
    except sqlite3.DatabaseError as e:
        msg = str(e)
    finally:
        conn.close()
    return JSONResponse(content=[msg])

@app.get("/api/v2/il/dataset", tags=["MigDB Heterogeneous Initial Load"],
    summary="Retrieve initial load dataset list",
    description="Returns a distinct list of job names from joined ILEXT and ILREP records, along with any CSV-based initial load jobs.")
def gg_il_dataset():
    sql = """
        SELECT DISTINCT a.jobname AS jobname
        FROM   ILEXT a
        JOIN   ILREP b ON a.jobname = b.jobname AND a.trail = b.trail
        UNION
        SELECT jobname FROM ILCSV
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        result = pd.read_sql_query(sql, conn).to_dict("records")
    except sqlite3.Error as e:
        result = str(e)
    finally:
        conn.close()
    return JSONResponse(content=[result])

_PROCESS_KEYS = frozenset({"ExtName", "PmpName", "RepName"})
 
 
@app.post("/api/v2/process/action", tags=["MigDB Process Management"],
    summary="Start or stop MigDB processes",
    description="Executes start or stop commands on the given list of extract, pump, or replicat process names via GGSCI.")
def gg_process_action(body: ProcessActionRequest):
    os.makedirs(agent_log, exist_ok=True)
 
    if not body.ops.startswith(("start", "stop")):
        raise HTTPException(status_code=400, detail=f"Unknown ops value: {body.ops!r}")
 
    verb = "start" if body.ops.startswith("start") else "stop"
 
    proc = _spawn_ggsci(bufsize=100)
    for name_dict in body.processName:
        for key, process in name_dict.items():
            if key in _PROCESS_KEYS:
                proc.stdin.write(f"{verb} {process}\n")
 
    raw = _communicate(proc)
 
    log_path = os.path.join(agent_log, "ggProcessAction.trc")
    with open(log_path, "w") as f:
        f.write(raw)
    with open(log_path) as f:
        action_err_print = _parse_ggsci_output(f.read())
 
    return JSONResponse(content=[action_err_print])

@app.post("/api/v2/il/tables", tags=["MigDB Heterogeneous Initial Load"],
    summary="Load initial load table statistics",
    description="Reads the job's table metadata CSV, initializes per-table statistics for extract and replicat row counts, elapsed time, and rates, and saves a summary file if one does not already exist.")
def gg_il_tables(body: ILTablesRequest):
    job_name    = body.JobName
    il_stats:   dict = {}
    tgtdeptype  = ""
    tgtdepurl   = ""
    df          = None
 
    try:
        for file_path in glob.glob(os.path.join(agent_home,job_name,"*tables")):
            df = pd.read_csv(file_path)
            df = df.fillna(0)
            for _, row in df.iterrows():
                tab_name = f"{row['OWNER']}.{row['TABLE_NAME']}"
                il_stats[tab_name] = {
                    "TargetRows":        row["NUM_ROWS"],
                    "Process":           row["PROC"],
                    "EXT_ROWS_PROCESSED": 0,
                    "EXT_ELAPSED":        0,
                    "EXT_RATE":           0,
                    "REP_ROWS_PROCESSED": 0,
                    "REP_ELAPSED":        0,
                    "REP_RATE":           0,
                }
    except Exception as e:
        tgtdeptype = str(e)
    finally:
        if df is not None:
            df.index.name = "TabName"
            summary_path = os.path.join(agent_home, job_name, job_name + "_Summary")
            if not os.path.exists(summary_path):
                df.to_csv(summary_path)
 
    return JSONResponse(content=[il_stats, tgtdeptype, tgtdepurl])

def parse_ggsci_output(output: str) -> list[str]:
    result = []
    for line in output.splitlines()[8:]:
        if 'GGSCI' in line:
            result.append(line.split('>', 1)[-1])
        else:
            result.append(line)
    return result

def run_ggsci(commands: list[str]) -> str:
    proc = subprocess.Popen(
        [ggsci_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0
    )
    output, _ = proc.communicate(input='\n'.join(commands) + '\n')
    proc.kill()
    proc.stdin.close()
    return output

class GGILActionRequest(BaseModel):
    jobName: str
    ilops: str

@app.post("/api/v2/gg-il-action", tags=["MigDB Heterogeneous Initial Load"],
    summary="Trigger initial load action across deployments",
    description="Dispatches start, stop, or purge actions to both source extract and target replicat deployments for a given initial load job and returns the combined operation output.")
def gg_il_action(body: GGILActionRequest):
    il_op_data = []
    conn = sqlite3.connect(DB_PATH)

    headers = get_internal_headers() 

    try:
        # Extract side
        ilext_fetch = pd.read_sql_query(
            """SELECT DISTINCT a.*, b.dep_priv_url url_src
               FROM ILEXT a, onepconn b
               WHERE a.srcdep = b.dep AND a.jobname = :jobName""",
            conn, params=[body.jobName]
        )

        ext_name = []
        dep_url_src = None
        src_domain = None
        src_alias = None
        for _, row in ilext_fetch.iterrows():
            dep_url_src = row['url_src']
            ext_name.append(row['extname'])
            src_domain = row['domain']
            src_alias = row['alias']

        if dep_url_src:
            try:
                r = requests.post(
                    dep_url_src + '/api/v2/ggiljobact',
                    json={"jobName": body.jobName, "extName": ext_name, "ilops": "ext" + body.ilops, "domain":  src_domain,
                        "alias":   src_alias,},
                    headers=headers,
                    verify=ssl_verify,
                    timeout=sshTimeOut
                )
                if r.status_code != 200:
                    logger.error(f"ggiljobact call failed ({r.status_code}): {r.text}")
                else:
                    il_op_data.extend(r.json()[0])
            except requests.exceptions.ConnectionError:
                pass

        # Replicat side
        ilrep_fetch = pd.read_sql_query(
            """SELECT DISTINCT a.*, b.dep_priv_url url_tgt, b.dep_url tgt_url
               FROM ILREP a, onepconn b
               WHERE a.tgtdep = b.dep AND jobname = :jobName""",
            conn, params=[body.jobName]
        )

        rep_det = []
        dep_url_tgt = None
        tgt_domain = None
        tgt_alias = None
        for _, row in ilrep_fetch.iterrows():
            dep_url_tgt = row['tgt_url']
            tgt_domain = row['domain']
            tgt_alias = row['alias']
            rep_det.append({
                'repname': row['repname'],
                'status':  row['status'],
                'trail':   row['trail'],
            })

        if dep_url_tgt:
            try:
                r = requests.post(
                    dep_url_tgt + '/api/v2/gg/il/jobact',
                    json={
                        "jobName": body.jobName,
                        "repDet":  rep_det,
                        "ilops":   "rep" + body.ilops,
                        "domain":  tgt_domain,
                        "alias":   tgt_alias,
                    },
                    headers={"Content-Type": "application/json"},
                    verify=ssl_verify,
                    timeout=sshTimeOut
                )
                if r.status_code != 200:
                    logger.error(f"gg/inforep call failed ({r.status_code}): {r.text}")               
                else:
                    il_op_data.extend(r.json()[0])
            except requests.exceptions.ConnectionError:
                pass

    finally:
        conn.close()

    return [il_op_data]


class GGILProcessesRequest(BaseModel):
    JobName: str

@app.post("/api/v2/gg-il-processes", tags=["MigDB Heterogeneous Initial Load"],
    summary="Get initial load process details",
    description="Fetches extract and replicat process info, trail links, and per-table row statistics for a given initial load job across source and target deployments.")
def gg_il_processes(body: GGILProcessesRequest):
    job_name = body.JobName
    trail_common = []
    il_exception = ''
    il_ext_data = []
    il_rep_data = []
    il_ext_proc_stats = {}
    process_node = {}
    src_link_node = []
    tgt_link_node = []
    headers = get_internal_headers() 

    conn = sqlite3.connect(DB_PATH)

    try:
        # Load table list from CSV
        tab_list = []
        for dfname in glob.glob(os.path.join(agent_home, job_name, job_name + '*tables')):
            tab_list = pd.read_csv(dfname, index_col=False).fillna(0).to_dict(orient='records')

        # Extract side
        ilext_fetch = pd.read_sql_query(
            """SELECT DISTINCT a.*, b.dep_priv_url url_src, b.dep_url src_dep_url
               FROM ILEXT a, onepconn b
               WHERE a.srcdep = b.dep AND a.jobname = :jobName""",
            conn, params=[job_name]
        )

        dep_url_src = None
        for _, row in ilext_fetch.iterrows():
            dep_name = row['srcdep']
            dep_url_src = row['url_src']
            src_url = row['src_dep_url']
            process_node.setdefault(dep_name, []).append({
                'procname': row['extname'], 'dep_url': src_url, 'type': 'Ext'
            })
            src_link_node.append({'extname': row['extname'], 'trail': row['trail'], 'dep_src': dep_name})

        if dep_url_src:
            for name in tab_list:
                il_ext_proc_stats[name['OWNER'] + '.' + name['TABLE_NAME']] = {
                    'TargetRows': name['NUM_ROWS'],
                    'Process':    name['PROC'],
                    'TotalEXT':   0,
                }
            try:
                r = requests.post(
                    dep_url_src + '/api/v2/extract/info',
                    json={'extname': 'E' + job_name + '*'},
                    headers=headers, verify=ssl_verify, timeout=sshTimeOut
                )
                if r.json()[0]:
                    il_ext_data = r.json()[0]
                    for name in il_ext_data:
                        try:
                            r2 = requests.post(
                                dep_url_src + '/api/v2/ggextprocstats',
                                json={
                                    'procName':       name['extname'],
                                    'procStats':      name['extstat'],
                                    'jobName':        job_name,
                                    'ILExtProcStats': il_ext_proc_stats,
                                },
                                headers=headers, verify=ssl_verify, timeout=sshTimeOut
                            )
                            if r2.json():
                                il_ext_proc_stats.update(r2.json())
                        except requests.exceptions.ConnectionError:
                            il_exception = 'error'
            except requests.exceptions.ConnectionError:
                il_exception = 'error'

        # Replicat side
        ilrmt_fetch = pd.read_sql_query(
            """SELECT DISTINCT b.dep_url AS url_tgt, a.tgtdep AS tgtdep, b.dbtype AS dbtype
               FROM ILREP a, onepconn b
               WHERE a.tgtdep = b.dep AND a.jobname = :jobName""",
            conn, params={"jobName": job_name}
        )

        tgt_url = None
        tgtdep_name = None
        tgt_dbtype = None
        for _, row in ilrmt_fetch.iterrows():
            tgt_url = row['url_tgt']
            tgtdep_name = row['tgtdep']
            tgt_dbtype = row['dbtype']

        tgt_headers = headers
        if tgt_dbtype == 'mongodb':
            tgt_headers = _get_tgt_auth_headers(dep_url_src, tgtdep_name, tgt_dbtype, headers)

        if tgt_url:
            try:
                r = requests.post(
                    tgt_url + '/api/v2/ggilrep',
                    json={'jobName': job_name},
                    headers=tgt_headers, verify=ssl_verify, timeout=sshTimeOut
                )
                if r.json()[0]:
                    for name in r.json()[0]:
                        dep_name = name['depName']
                        process_node.setdefault(dep_name, []).append({
                            'procname': name['repname'], 'dep_url': name['dep_url'], 'type': 'Rep'
                        })
                        tgt_link_node.append({
                            'repname': name['repname'],
                            'trail':   name['trail'],
                            'dep_tgt': dep_name,
                        })
            except requests.exceptions.ConnectionError:
                il_exception = 'error'

            inforep_url = '/api/v2/gg/inforep'
            procstats_url = '/api/v2/gg/rep/procstats'
            if tgt_dbtype == 'mongodb':
                inforep_url = '/api/v2/gginforep'
                procstats_url = '/api/v2/ggrepprocstats'

            try:
                r = requests.post(
                    tgt_url + inforep_url,
                    json={'repname': 'R' + job_name + '*'},
                    headers=tgt_headers, verify=ssl_verify, timeout=sshTimeOut
                )
                if r.status_code != 200:
                    logger.error(f"gg/inforep call failed ({r.status_code}): {r.text}")               
                else:
                    il_rep_data = r.json()[0]
                    for name in il_rep_data:
                        try:
                            r2 = requests.post(
                                tgt_url + procstats_url,
                                json={
                                    'procName':       name['repname'],
                                    'jobName':        job_name,
                                    'procStats':      name['repstat'],
                                    'ILExtProcStats': il_ext_proc_stats,
                                },
                                headers=tgt_headers, verify=ssl_verify, timeout=sshTimeOut
                            )
                            if r2.status_code != 200:
                                logger.error(f"gg/inforep call failed ({r2.status_code}): {r2.text}")               
                            else:
                                il_ext_proc_stats.update(r2.json())
                        except requests.exceptions.ConnectionError:
                            il_exception = 'error'
            except requests.exceptions.ConnectionError:
                il_exception = 'error'

    finally:
        conn.close()

    # Trail merge
    src_df = pd.DataFrame(src_link_node)
    tgt_df = pd.DataFrame(tgt_link_node)
    if not src_df.empty and not tgt_df.empty:
        trail_common = pd.merge(src_df, tgt_df, on=['trail'], how='inner').to_dict('records')

    return [trail_common, il_ext_data, il_ext_proc_stats, process_node, il_rep_data, il_exception]


class ILJobActRequest(BaseModel):
    jobName:  str
    ilops:    str
    extName:  list[str] = [] 
    repDet:   list[dict] = []    
    domain:   str = ""            
    alias:    str = ""           
 
def _positional_binds(n: int) -> str:
    """Return '?,?,?' style placeholders for n values (sqlite3 qmark style)."""
    return ",".join("?" * n)
 
 
def _safe_post(url: str, payload: dict, headers: dict):
    try:
        r = requests.post(url, json=payload, headers=headers, verify=ssl_verify, timeout=ssh_timeout)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError as exc:
        logger.error(f"Connection error to {url}: {exc}")
        return None
    except Exception as exc:
        logger.error(f"Request failed to {url}: {exc}")
        return None
     
@app.post("/api/v2/ggiljobact", tags=["MigDB Heterogeneous Initial Load"],
    summary="Execute extract or replicat job actions",
    description="Performs start, stop, or purge operations on extract or replicat processes for an initial load job and updates the job status in the database.")
def gg_il_job_act(body: ILJobActRequest):
    os.makedirs(agent_log, exist_ok=True)
 
    il_ops_err_print: list[str] = []
    conn = sqlite3.connect(DB_PATH)
 
    try:
        if body.ilops.startswith("ext"):
            ext_names = body.extName or []
            if not ext_names:
                raise HTTPException(status_code=400, detail="extName is required for ext* ops")
 
            proc = _spawn_ggsci()
 
            if body.ilops == "extstop":
                for name in ext_names:
                    proc.stdin.write(f"kill {name}\n")
                raw = _communicate(proc)
                conn.execute(
                    f"UPDATE ILEXT SET status='STOPPED' WHERE extname IN ({_positional_binds(len(ext_names))})",
                    ext_names,
                )
 
            elif body.ilops == "extstart":
                for name in ext_names:
                    proc.stdin.write(f"start extract {name}\n")
                raw = _communicate(proc)
                conn.execute(
                    f"UPDATE ILEXT SET status='RUNNING' WHERE extname IN ({_positional_binds(len(ext_names))})",
                    ext_names,
                )
 
            elif body.ilops == "extpurge":
                for name in ext_names:
                    proc.stdin.write(f"delete {name}\n")
                raw = _communicate(proc)
                conn.execute(
                    f"DELETE FROM ILEXT WHERE extname IN ({_positional_binds(len(ext_names))})",
                    ext_names,
                )
 
            else:
                _communicate(proc)   # clean up
                raise HTTPException(status_code=400, detail=f"Unknown ilops: {body.ilops!r}")
 
            conn.commit()
 
            log_path = os.path.join(agent_log, "ILExtOps.lst")
            with open(log_path, "w") as f:
                f.write(raw)
            with open(log_path) as f:
                il_ops_err_print = _parse_ggsci_output(f.read())
 
        elif body.ilops.startswith("rep"):
            rep_det = body.repDet or []
            if not rep_det:
                raise HTTPException(status_code=400, detail="repDet is required for rep* ops")
 
            proc     = _spawn_ggsci()
            rep_names: list[str] = []
 
            if body.ilops == "repstop":
                for pattern in rep_det:
                    proc.stdin.write(f"kill {pattern['repname']}\n")
                    proc.stdin.write(f"alter replicat {pattern['repname']} , extseqno 0 , extrba 0\n")
                    rep_names.append(pattern["repname"])
                    for fname in glob.glob(pattern["trail"] + "*", recursive=True):
                        os.remove(fname)
                raw = _communicate(proc)
                conn.execute(
                    f"UPDATE ILREP SET status='STOPPED' WHERE repname IN ({_positional_binds(len(rep_names))})",
                    rep_names,
                )
                conn.commit()
                # Remove non-table files for this job
                for entry in os.scandir(os.path.join(agent_home, body.jobName)):
                    if "_tables" not in entry.name:
                        os.remove(entry.path)
 
            elif body.ilops == "repstart":
                for pattern in rep_det:
                    proc.stdin.write(f"start {pattern['repname']} , NOFILTERDUPTRANSACTIONS\n")
                    rep_names.append(pattern["repname"])
                raw = _communicate(proc)
                conn.execute(
                    f"UPDATE ILREP SET status='RUNNING' WHERE repname IN ({_positional_binds(len(rep_names))})",
                    rep_names,
                )
                conn.commit()
 
            elif body.ilops == "reppurge":
                domain = body.domain or ""
                alias  = body.alias  or ""
                proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
                for pattern in rep_det:
                    if pattern.get("status") == "STOPPED":
                        proc.stdin.write(f"delete replicat {pattern['repname']}\n")
                        rep_names.append(pattern["repname"])
                raw = _communicate(proc)
                if rep_names:
                    conn.execute(
                        f"DELETE FROM ILREP WHERE repname IN ({_positional_binds(len(rep_names))})",
                        rep_names,
                    )
                    conn.commit()
 
            else:
                _communicate(proc)
                raise HTTPException(status_code=400, detail=f"Unknown ilops: {body.ilops!r}")
 
            log_path = os.path.join(agent_log, "ILRepOps.lst")
            with open(log_path, "w") as f:
                f.write(raw)
            with open(log_path) as f:
                il_ops_err_print = _parse_ggsci_output(f.read())
 
        else:
            raise HTTPException(status_code=400, detail=f"Unknown ilops prefix: {body.ilops!r}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        conn.close()
 
    return JSONResponse(content=[il_ops_err_print])

class ILRepRequest(BaseModel):
    jobName: str
 
 
class ExtProcStatsRequest(BaseModel):
    jobName:        str
    procName:       str
    procStats:      str
    ILExtProcStats: dict
 
 
class RepProcStatsRequest(BaseModel):
    jobName:        str
    procName:       str
    procStats:      str
    ILExtProcStats: dict 
 
def _is_stopped_or_abended(proc_stats: str) -> bool:
    """
    The original used `elif procStats == 'STOPPED' or 'ABENDED'` which is
    always True because `bool('ABENDED')` is always True.
    This helper preserves the intent of checking for either value.
    """
    return proc_stats in ("STOPPED", "ABENDED")
 
 
def _ensure_job_dir(job_name: str, proc_name: str) -> None:
    """Create job directory and sentinel 'running' file if not present, then start stats thread."""
    job_dir = os.path.join(agent_home, job_name)
    os.makedirs(job_dir, exist_ok=True)
    sentinel = os.path.join(job_dir, proc_name + "running")
    if not os.path.exists(sentinel):
        open(sentinel, "w").close()
        threading.Thread(target=ILGetStats, args=(proc_name, job_name), daemon=True).start()
 
 
def _cleanup_proc_files(job_name: str, proc_name: str) -> None:
    """Remove sentinel and rate-list files when a process stops."""
    for suffix in ("running", "Rate.lst"):
        path = os.path.join(agent_home, job_name, proc_name + suffix)
        if os.path.exists(path):
            os.remove(path)

@app.post("/api/v2/ggilrep", tags=["MigDB Heterogeneous Initial Load"],
    summary="Get initial load replicat details",
    description="Returns replicat process details including target deployment, domain, alias, and trail path for a given initial load job.")
def gg_il_rep(body: ILRepRequest):
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            """SELECT DISTINCT a.*, b.dep_priv_url url_tgt
               FROM   ILREP a
               JOIN   onepconn b ON a.tgtdep = b.dep
               WHERE  a.jobname = ?""",
            conn, params=[body.jobName],
        )
    finally:
        conn.close()
 
    rep_det = [
        {
            "depName":   row["tgtdep"],
            "dep_url":   row["url_tgt"],
            "tgtdomain": row.get("domain", ""),
            "tgtalias":  row.get("alias", ""),
            "repname":   row["repname"],
            "trail":     row["trail"],
        }
        for _, row in df.iterrows()
    ]
    return JSONResponse(content=[rep_det])

def normalize_table_name(raw_name: str) -> str:
    """
    Normalize any GoldenGate-reported table identifier to OWNER.TABLE form,
    regardless of whether a container/PDB prefix is present.
    Handles:
      ORCLPDB.NAVAN.DEPARTMENTS -> NAVAN.DEPARTMENTS
      NAVAN.DEPARTMENTS         -> NAVAN.DEPARTMENTS
      navan.departments         -> NAVAN.DEPARTMENTS
    """
    parts = raw_name.strip().rstrip(':').split('.')
    if len(parts) >= 2:
        return f"{parts[-2]}.{parts[-1]}".upper()
    return raw_name.strip().rstrip(':').upper()

@app.post("/api/v2/ggextprocstats", tags=["MigDB Heterogeneous Initial Load"],
    summary="Get extract process statistics",
    description="Reads extract rate and report files to update per-table row counts, rates, elapsed time, and discard stats based on whether the process is running, stopped, or abended.")
def gg_ext_proc_stats(body: ExtProcStatsRequest):
    job_name       = body.jobName
    proc_name      = body.procName
    proc_stats     = body.procStats
    il_ext_stats   = dict(body.ILExtProcStats)   # copy so we can mutate safely
 
    if proc_stats == "RUNNING":
        _ensure_job_dir(job_name, proc_name)
 
        rate_path = os.path.join(agent_home, job_name, proc_name + "Rate.lst")
        try:
            with open(rate_path) as f:
                copy      = False
                rate_copy = False
                tab_name  = ""
                ext_rate  = "0"
                total_ext = 0
 
                for line in f:
                    if line.startswith("Extracting"):
                        #raw_name = line.split()[2]
                        #tab_name = '.'.join(raw_name.split('.')[-2:]).upper()
                        tab_name = normalize_table_name(line.split()[2])
                        #tab_name = line.split()[2]
 
                    elif "Total statistics" in line:
                        rate_copy = True
 
                    elif "Total operations/second" in line:
                        rate_copy = False
 
                    elif rate_copy:
                        if "inserts/second" in line:
                            ext_rate = line.split()[2]
 
                    elif "Latest statistics" in line:
                        copy = True
 
                    elif "End of statistics" in line:
                        copy = False
 
                    elif copy:
                        if "Total inserts/second" in line:
                            total_ext = round(float(line.split()[2]))
                        elif "Total discards/second" in line:
                            total_ext_dsc = line.split()[2]
                            if tab_name in il_ext_stats:
                                il_ext_stats[tab_name].update({
                                    "TotalEXT":    total_ext,
                                    "TotalEXTDSC": total_ext_dsc,
                                    "ExtRate":     ext_rate,
                                })
        except FileNotFoundError:
            pass
 
    elif proc_stats == 'STOPPED' or proc_stats == 'ABENDED':
        _cleanup_proc_files(job_name, proc_name)
 
        rpt_path = os.path.join(gg_home, "dirrpt", proc_name + ".rpt")
        try:
            with open(rpt_path) as f:
                tab_name   = ""
                elap_time  = ""
                total_ext  = "0"
 
                for line in f:
                    if "Report at" in line:
                        parts      = line.split()
                        end_time   = parts[2] + ":" + parts[3]
                        start_time = parts[6] + ":" + parts[7].rstrip(")")
                        elap_time  = str(
                            (datetime.strptime(end_time,   DATETIME_FMT)
                           - datetime.strptime(start_time, DATETIME_FMT)).total_seconds()
                        )
 
                    elif line.startswith("From table"):
                        #raw_name = line.split()[2].rstrip(":")
                        #tab_name = '.'.join(raw_name.split('.')[-2:]).upper()
                        tab_name = normalize_table_name(line.split()[2])
                        #tab_name = line.split()[2].rstrip(":")
 
                    elif "inserts" in line:
                        total_ext = line.split()[2]
 
                    elif "discards" in line:
                        total_ext_dsc = line.split()[2]
                        if tab_name in il_ext_stats:
                            il_ext_stats[tab_name].update({
                                "TotalEXT":    total_ext,
                                "TotalEXTDSC": total_ext_dsc,
                                "ExtElapse":   elap_time,
                                "ExtRate":     "Completed",
                            })
        except FileNotFoundError:
            pass
 
    return JSONResponse(content=il_ext_stats)

@app.post("/api/v2/ggrepprocstats", tags=["MigDB Heterogeneous Initial Load"],
    summary="Get replicat process statistics",
    description="Reads replicat rate and end-time files to update per-table replication counts, rates, elapsed time, ETA, and completion status based on whether the process is running, stopped, or abended.")
def gg_rep_proc_stats(body: RepProcStatsRequest):
    job_name     = body.jobName
    proc_name    = body.procName
    proc_stats   = body.procStats
    il_ext_stats = dict(body.ILExtProcStats)
 
    if proc_stats == "RUNNING":
        _ensure_job_dir(job_name, proc_name)
 
        rate_path = os.path.join(agent_home, job_name, proc_name + "Rate.lst")
        try:
            with open(rate_path) as f:
                copy       = False
                rate_copy  = False
                tab_name   = ""
                start_time = ""
                rep_rate   = 0.0
                total_rep  = 0
 
                for line in f:
                    if line.startswith("Replicating"):
                        tab_name = line.split()[2]
 
                    elif "Total statistics" in line:
                        rate_copy = True
 
                    elif "Total operations" in line:
                        rate_copy = False
 
                    elif rate_copy:
                        if "inserts" in line:
                            rep_rate = float(line.split()[2])
 
                    elif "Latest statistics" in line:
                        parts      = line.split()
                        start_time = parts[4] + ":" + parts[5].rstrip(")")
                        copy       = True
 
                    elif "End of statistics" in line:
                        copy = False
 
                    elif copy:
                        if "Total inserts" in line:
                            total_rep = round(float(line.split()[2]))
 
                        elif "Total discards" in line:
                            total_rep_dsc = line.split()[2]
                            status  = ""
                            rep_eta = 0
 
                            ext_entry = il_ext_stats.get(tab_name, {})
                            if ext_entry:
                                if (int(ext_entry.get("TotalEXT", -1)) == total_rep
                                        and ext_entry.get("ExtRate") == "Completed"):
                                    # Extract finished — record or read end-time file
                                    end_file = os.path.join(agent_home, job_name, tab_name + "endtime")
                                    if not os.path.exists(end_file):
                                        end_time = datetime.now().strftime(DATETIME_FMT)
                                        elap_time = (
                                            datetime.strptime(end_time,   DATETIME_FMT)
                                          - datetime.strptime(start_time, DATETIME_FMT)
                                        ).total_seconds()
                                        with open(end_file, "w") as ef:
                                            ef.write(f"{end_time} {start_time} {total_rep} {total_rep_dsc}")
                                    else:
                                        with open(end_file) as ef:
                                            parts     = ef.read().split()
                                            end_time  = parts[0]
                                            elap_time = (
                                                datetime.strptime(end_time,   DATETIME_FMT)
                                              - datetime.strptime(start_time, DATETIME_FMT)
                                            ).total_seconds()
                                    status = "Completed"
                                else:
                                    # Still in progress
                                    end_time  = datetime.now().strftime(DATETIME_FMT)
                                    elap_time = (
                                        datetime.strptime(end_time,   DATETIME_FMT)
                                      - datetime.strptime(start_time, DATETIME_FMT)
                                    ).total_seconds()
                                    if elap_time > 0:
                                        rep_rate = round(total_rep / elap_time, 2)
                                    status  = "InProgress"
                                    target  = int(ext_entry.get("TargetRows", 0))
                                    rep_eta = int((target - total_rep) / rep_rate) if rep_rate else 0
 
                            if tab_name in il_ext_stats:
                                il_ext_stats[tab_name].update({
                                    "TotalREP":    total_rep,
                                    "TotalREPDSC": total_rep_dsc,
                                    "RepRate":     rep_rate,
                                    "RepElapse":   elap_time,
                                    "RepETA":      round(rep_eta),
                                    "Status":      status,
                                })
        except FileNotFoundError:
            pass
 
    elif _is_stopped_or_abended(proc_stats):
        _cleanup_proc_files(job_name, proc_name)
 
        try:
            for end_file in glob.glob(os.path.join(agent_home, job_name, "*endtime")):
                with open(end_file) as f:
                    parts         = f.read().split()
                    end_time      = parts[0]
                    start_time    = parts[1]
                    total_rep     = parts[2]
                    total_rep_dsc = parts[3]
                    elap_time     = (
                        datetime.strptime(end_time,   DATETIME_FMT)
                      - datetime.strptime(start_time, DATETIME_FMT)
                    ).total_seconds()
                    tab_name = os.path.basename(end_file).removesuffix("endtime")
                    status   = "Completed" if proc_stats == "STOPPED" else "Abended"
 
                    if tab_name in il_ext_stats:
                        il_ext_stats[tab_name].update({
                            "TotalREP":    total_rep,
                            "TotalREPDSC": total_rep_dsc,
                            "RepElapse":   elap_time,
                            "Status":      status,
                        })
        except FileNotFoundError:
            pass
 
    return JSONResponse(content=il_ext_stats)

class AddIERequest(BaseModel):
    regExtChk:          bool
    regVal:             str = 'now'
    lmDictSCN:          str | int
    currentShareOpt:    str
    CaptureName:        str
    extname:            str
    domain:             str
    alias:              str
    mode:               str
    beginmode:          str
    trailtype:          str
    trailsubdir:        str
    trailsubdirslash:   str
    trail:              str
    trailsize:          int | str = '500mb'
    currentExtParamList: str
    startExtChk:        bool = False
    CDBCheck:           str
    PDBName:            str
    pdbSelList:         list[str]
    isPDBLogin:         bool
 
 
class InfoChkptTblRequest(BaseModel):
    domain: str
    alias:  str
 
 
class AddChkptTblRequest(BaseModel):
    domain:   str
    alias:    str
    chkpttbl: str
    operation: str
 
def _dblogin(alias: str, domain: str) -> tuple[str, bool]:
    """
    Attempt a dblogin and return (output, success).
    success=False if output contains ERROR.
    """
    proc = _spawn_ggsci()
    proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
    out = _communicate(proc)
    return out, "ERROR" not in out
 
def _filter_ext_output(raw: str) -> list[str]:
    """Keep error and 'added.' lines, replacing OGG- with CDC- prefixes."""
    result: list[str] = []
    for line in raw.splitlines(keepends=True):
        line = line.replace("OGG-", "CDC-")
        if re.search(r"error", line, re.I) or "added." in line:
            result.append(line.split(">", 1)[-1])
    return result
 
 
def _filter_chkpt_output(raw: str) -> list[str]:
    """Keep ERROR, OCI, and 'created' lines from checkpoint output."""
    result: list[str] = []
    for line in raw.splitlines(keepends=True):
        if "ERROR" in line:
            result.append(line.split(">", 1)[-1])
        elif "OCI" in line:
            result.append(line)
        elif "created" in line:
            parts = line.split()
            if "created" in parts[1:] and "table" in parts:
                result.append(parts[parts.index("table") + 1])
    return result
 
 
def _db_insert_chkpt(alias: str, chkpttbl: str) -> None:
    """Upsert a checkpoint table record into the CHKPT table."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO CHKPT VALUES (:dbname, :tabname)",
            {"dbname": alias, "tabname": chkpttbl},
        )
        conn.commit()
    except sqlite3.DatabaseError:
        pass
    finally:
        conn.close()

@app.post("/api/v2/extract/add-integrated", tags=["MigDB Extract Management"],
    summary="Add an integrated extract process",
    description="Registers the extract with the database, creates the extract and trail in MigDB, writes the parameter file, and optionally starts the extract process.")
def gg_add_ie(body: AddIERequest):
    os.makedirs(agent_log, exist_ok=True)
    add_ext_out: list[str] = []
 
    login_out, login_ok = _dblogin(body.alias, body.domain)
    add_ext_out.append(login_out)
 
    if not login_ok:
        return JSONResponse(content=[_filter_ext_output("".join(add_ext_out))])
 
    proc = _spawn_ggsci()
    proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")

    if body.regExtChk:
        if body.CDBCheck == "YES":
            pdb_list = ",".join(body.pdbSelList)
            add_ext_out.append(pdb_list)
            if body.regVal == "now":
                if body.isPDBLogin:
                    proc.stdin.write(
                        f"register extract {body.extname} database\n"
                    )
                else:
                    proc.stdin.write(
                        f"register extract {body.extname} database CONTAINER({pdb_list})\n"
                    )
            elif body.regVal == "existscn":
                if body.isPDBLogin:
                    proc.stdin.write(
                        f"register extract {body.extname} database"
                        f" SCN {body.lmDictSCN}\n"
                    )
                else:
                    proc.stdin.write(
                        f"register extract {body.extname} database CONTAINER({pdb_list})"
                        f" SCN {body.lmDictSCN}\n"
                    )
        else:
            if body.regVal == "now":
                proc.stdin.write(f"register extract {body.extname} database\n")
            elif body.regVal == "existscn":
                share = body.currentShareOpt
                share_target = body.CaptureName if share == "EXTRACT" else share
                proc.stdin.write(
                    f"register extract {body.extname} database"
                    f" SCN {body.lmDictSCN} SHARE {share_target}\n"
                )
    reg_out = _communicate(proc)
 
    if re.search(r"error", reg_out, re.I):
        add_ext_out.append(reg_out)
        return JSONResponse(content=[_filter_ext_output("".join(add_ext_out))])
 
    trail_full = f"{body.trailsubdir}{body.trailsubdirslash}{body.trail}"
    proc = _spawn_ggsci()
    proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")
    proc.stdin.write(
        f"add extract {body.extname} integrated tranlog , begin {body.beginmode}\n"
    )
    proc.stdin.write(
        f"add exttrail {trail_full} extract {body.extname} megabytes {body.trailsize}\n"
    )
    add_ext_err = _communicate(proc)
    add_ext_out.append(add_ext_err)
 
    if re.search(r"error", add_ext_err, re.I):
        return JSONResponse(content=[_filter_ext_output("".join(add_ext_out))])
 
    prm_path = os.path.join(gg_home, "dirprm", body.extname + ".prm")
    with open(prm_path, "w") as f:
        f.write(body.currentExtParamList)
 
    if not body.startExtChk:
        time.sleep(3)
        proc = _spawn_ggsci()
        proc.stdin.write(f"start extract {body.extname}")
        start_ext_err = _communicate(proc)
        add_ext_out.append(start_ext_err)
    else:
        add_ext_out.append(add_ext_err)
 
    log_path = os.path.join(agent_log, "AddExtErr.lst")
    with open(log_path, "w") as f:
        f.writelines(add_ext_out)
    with open(log_path) as f:
        ext_err_print = _filter_ext_output(f.read())
 
    return JSONResponse(content=[ext_err_print])

@app.post("/api/v2/chkpt/info", tags=["MigDB Checkpoint Management"],
    summary="Get checkpoint table info",
    description="Looks up the checkpoint table name for the given alias from the database and returns its status from MigDB via GGSCI.")
def gg_info_chkpt_tbl(body: InfoChkptTblRequest):
    os.makedirs(agent_log, exist_ok=True)
    info_chkpt_out: list[str] = []
 
    if not os.path.exists(ggsci_bin):
        return JSONResponse(content=[[]])
 
    login_out, login_ok = _dblogin(body.alias, body.domain)
    if not login_ok:
        info_chkpt_out.append(login_out)
    else:
        # Look up checkpoint table name from DB
        conn = sqlite3.connect(DB_PATH)
        try:
            rows = conn.execute(
                "SELECT tabname FROM CHKPT WHERE dbname = ?", (body.alias,)
            ).fetchall()
        finally:
            conn.close()
 
        if rows:
            for row in rows:
                tabname = row[0]
                proc = _spawn_ggsci()
                proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")
                proc.stdin.write(f"info checkpointtable {tabname}\n")
                info_chkpt_out.append(_communicate(proc))
        else:
            info_chkpt_out.append("ERROR : No Checkpoint Table found")
 
    # Persist and filter
    log_path = os.path.join(agent_log, "InfoChkptTbl.lst")
    with open(log_path, "w") as f:
        f.writelines(info_chkpt_out)
    with open(log_path) as f:
        info_chkpt_err_print = _filter_chkpt_output(f.read())
 
    return JSONResponse(content=[info_chkpt_err_print])

def _db_insert_chkpt(alias: str, chkpttbl: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                'INSERT INTO CHKPT VALUES(:dbname, :tabname)',
                {'dbname': alias, 'tabname': chkpttbl}
            )
            conn.commit()
    except sqlite3.DatabaseError:
        pass


def _db_delete_chkpt(alias: str, chkpttbl: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                'DELETE FROM CHKPT WHERE tabname = ? AND dbname = ?',
                (chkpttbl, alias)
            )
            conn.commit()
    except sqlite3.DatabaseError:
        pass

@app.post("/api/v2/chkpt/add", tags=["MigDB Checkpoint Management"],
    summary="Add a checkpoint table",
    description="Creates a new checkpoint table in MigDB for the given alias and domain, "
                "and persists the table name to the database on success or if it already exists.")
def gg_add_chkpt_tbl(body: AddChkptTblRequest):
    domain   = body.domain
    alias    = body.alias
    ckptOps  = body.operation
    chkpttbl = body.chkpttbl

    os.makedirs(agent_log, exist_ok=True)
    add_chkpt_out: list[str] = []

    ckptOps_norm = ckptOps.strip().lower()

    login_out, login_ok = _dblogin(alias, domain)

    if not login_ok:
        add_chkpt_out.append(login_out)
    else:
        proc = _spawn_ggsci()
        proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")

        if ckptOps_norm == "add":
            proc.stdin.write(f"add checkpointtable {chkpttbl}\n")
        elif ckptOps_norm == "view":
            proc.stdin.write(f"info checkpointtable {chkpttbl}\n")
        elif ckptOps_norm == "delete":
            proc.stdin.write(f"delete checkpointtable {chkpttbl}\nyes\n")
        elif ckptOps_norm == "upgrade":
            proc.stdin.write(f"upgrade checkpointtable {chkpttbl}\n")
        elif ckptOps_norm == "clean":
            proc.stdin.write(f"cleanup checkpointtable {chkpttbl}\n")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {ckptOps}")

        add_chkpt_out.append(_communicate(proc))

    # ── Write raw output to log ───────────────────────────────────────────────
    log_path = os.path.join(agent_log, "AddChkptTbl.lst")
    with open(log_path, "w") as f:
        f.writelines(add_chkpt_out)

    # ── Parse log and build response ──────────────────────────────────────────
    add_chkpt_err_print: list[str] = []

    with open(log_path) as f:
        for raw_line in f:
            line = raw_line
            if re.search(r"\bERROR\b", line, re.I) or "OCI" in line:
                cleaned = line.split(">", 1)[-1].strip()
                add_chkpt_err_print.append(cleaned)
                if ckptOps_norm == "add" and "already" in line.lower():
                    _db_insert_chkpt(alias, chkpttbl)

            elif ckptOps_norm == "add" and "created" in line.lower():
                _db_insert_chkpt(alias, chkpttbl)
                add_chkpt_err_print.append(line.split(">", 1)[-1].strip())

            elif ckptOps_norm == "delete" and (
                "deleted" in line.lower() or "dropped" in line.lower()
            ):
                _db_delete_chkpt(alias, chkpttbl)
                add_chkpt_err_print.append(line.split(">", 1)[-1].strip())

            elif ckptOps_norm == "upgrade" and "upgrade" in line.lower():
                add_chkpt_err_print.append(line.split(">", 1)[-1].strip())

            elif ckptOps_norm == "clean" and any(
                kw in line.lower() for kw in ["cleaned", "cleanup", "rows"]
            ):
                add_chkpt_err_print.append(line.split(">", 1)[-1].strip())

            elif ckptOps_norm == "view" and any(
                kw in line.lower() for kw in ["checkpoint", "table", "owner", "rows", "info", "name"]
            ):
                add_chkpt_err_print.append(line.split(">", 1)[-1].strip())

    if not add_chkpt_err_print:
        with open(log_path) as f:
            add_chkpt_err_print = [line.strip() for line in f if line.strip()]

    return JSONResponse(content=[add_chkpt_err_print]) 

class AddCERequest(BaseModel):
    extname:             str
    domain:              str
    alias:               str
    mode:                str
    threads:             int | str
    beginmode:           str
    trailtype:           str
    trailsubdir:         str
    trailsubdirslash:    str
    trail:               str
    trailsize:           int | str
    currentExtParamList: str
    startExtChk:         bool
    regExtChk:           bool
 
class GetExtParamRequest(BaseModel):
    currentextname: str
 
class AddPumpPTRequest(BaseModel):
    extname:             str
    mode:                str
    srcTrail:            str
    beginmode:           str
    trail:               str
    trailsize:           int | str
    currentPmpParamList: str
    startPmpChk:         bool
 
class DelExtRequest(BaseModel):
    extname: str
    domain:  str
    alias:   str
 
class GetRMTTrailRequest(BaseModel):
    extName: str
 
class DelRMTRequest(BaseModel):
    pmpName: str
 
def _filter_keywords(raw: str, keywords: set[str]) -> list[str]:
    """Keep lines containing any of the given keywords, stripping GGSCI prompts."""
    result: list[str] = []
    for line in raw.splitlines(keepends=True):
        if any(kw in line for kw in keywords):
            result.append(line.split(">", 1)[-1])
    return result
 
 
def _write_and_parse(log_filename: str, raw_lines: list[str], parser) -> list[str]:
    """Write raw_lines to agent_log/log_filename, then apply parser to the file content."""
    os.makedirs(agent_log, exist_ok=True)
    log_path = os.path.join(agent_log, log_filename)
    with open(log_path, "w") as f:
        f.writelines(raw_lines)
    with open(log_path) as f:
        return parser(f.read())
    
@app.post("/api/v2/extract/add-classic", tags=["MigDB Extract Management"],
    summary="Add a classic extract process",
    description="Verifies database login, creates the extract and trail in MigDB, writes the parameter file, and optionally starts the classic extract process.")
def gg_add_ce(body: AddCERequest):
    add_ce_out: list[str] = []
 
    # Step 1: verify DB login
    login_out, login_ok = _dblogin(body.alias, body.domain)
    add_ce_out.append(login_out)
 
    if not login_ok:
        return JSONResponse(
            content=[_write_and_parse("AddCEErr.lst", add_ce_out, _parse_ggsci_output)]
        )
 
    # Step 2: add extract, exttrail, and optionally register
    trail_full = f"{body.trailsubdir}{body.trailsubdirslash}{body.trail}"
    proc = _spawn_ggsci()
    proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")
    proc.stdin.write(
        f"add extract {body.extname} {body.mode} threads {body.threads} {body.beginmode}\n"
    )
    proc.stdin.write(
        f"add exttrail {trail_full} extract {body.extname} megabytes {body.trailsize}\n"
    )
    if body.regExtChk:
        proc.stdin.write(f"register extract {body.extname} LOGRETENTION\n")
    add_ce_err = _communicate(proc)
    add_ce_out.append(add_ce_err)
 
    # Step 3: write param file
    prm_path = os.path.join(gg_home, "dirprm", body.extname + ".prm")
    with open(prm_path, "w") as f:
        f.write(body.currentExtParamList)
 
    # Step 4: start extract if requested
    if body.startExtChk is False:
        proc = _spawn_ggsci()
        proc.stdin.write(f"start extract {body.extname}")
        start_ce_err = _communicate(proc)
        add_ce_out.append(add_ce_err)
        add_ce_out.append(start_ce_err)
    else:
        add_ce_out.append(add_ce_err)
 
    return JSONResponse(
        content=[_write_and_parse("AddCEErr.lst", add_ce_out, _parse_ggsci_output)]
    )

@app.get("/api/v2/exttrail/list", tags=["MigDB Extract Management"],
    summary="List all extract trails",
    description="Retrieves all extract trail names and their associated extract process names from MigDB and returns them as a labeled list.")
def gg_get_ext_trail():
    raw = subprocess.getoutput(f"echo -e 'info exttrail'|{ggsci_bin}")
    os.makedirs(agent_log, exist_ok=True)
 
    log_path = os.path.join(agent_log, "infoext.out")
    with open(log_path, "w") as f:
        f.write(raw)
 
    ext_trail_data: list[dict] = []
    trail_name = ""
    with open(log_path) as f:
        for line in f:
            if "Extract Trail" in line:
                trail_name = line.split(":", 1)[-1].strip()
            elif "Extract" in line:
                ext_name = line.split(":", 1)[-1].strip()
                ext_trail_data.append({"label": ext_name, "value": trail_name})
 
    return JSONResponse(content=[ext_trail_data])

@app.post("/api/v2/extract/param", tags=["MigDB Extract Management"],
    summary="Get extract parameter file contents",
    description="Resolves the trail path for the given extract name and reads the matching parameter file, returning table and source catalog entries along with the trail path.")
def gg_get_ext_param(body: GetExtParamRequest):
    ext_name = body.currentextname
 
    # Resolve trail via ggsci
    raw_trail = subprocess.getoutput(
        f"echo -e 'info {ext_name} , showch'|{ggsci_bin}|grep -i 'Extract Trail:'"
    )
    ext_trail = raw_trail.split(":", 1)[-1].strip() if ":" in raw_trail else ""
 
    # Read matching param file
    ext_prm_data: list[str] = []
    for name in glob.glob(os.path.join(gg_home, "dirprm", "*.prm")):
        base = os.path.basename(name)
        if re.match(base, ext_name + ".prm", re.IGNORECASE):
            copy = False
            with open(os.path.join(gg_home, "dirprm", base)) as f:
                for line in f:
                    if re.match(r"sourcecatalog", line, re.IGNORECASE):
                        copy = True
                    if re.match(r"table", line, re.IGNORECASE):
                        copy = True
                    if copy:
                        ext_prm_data.append(line)
            break   # stop after first match
 
    return JSONResponse(content=[ext_prm_data, ext_trail])

@app.post("/api/v2/pump/add", tags=["MigDB Pump Management"],
    summary="Add a pump process",
    description="Creates a pump extract and remote trail in MigDB, writes the parameter file, and optionally starts the pump process.")
def gg_add_pump_pt(body: AddPumpPTRequest):
    add_pmp_out: list[str] = []
 
    proc = _spawn_ggsci()
    proc.stdin.write(f"add extract {body.extname} , {body.mode} {body.srcTrail}\n")
    proc.stdin.write(
        f"add rmttrail {body.trail} extract {body.extname} megabytes {body.trailsize}\n"
    )
    add_pmp_err = _communicate(proc)
 
    # Write param file
    with open(os.path.join(gg_home, "dirprm", body.extname + ".prm"), "w") as f:
        f.write(body.currentPmpParamList)
 
    if body.startPmpChk is False:
        proc = _spawn_ggsci()
        proc.stdin.write(f"start extract {body.extname}\n")
        start_pmp_err = _communicate(proc)
        add_pmp_out.extend([add_pmp_err, start_pmp_err])
    else:
        add_pmp_out.append(add_pmp_err)
 
    def _filter_pmp(raw: str) -> list[str]:
        return _filter_keywords(raw, {"ERROR", "EXTRACT", "added"})
 
    return JSONResponse(
        content=[_write_and_parse("AddPmpErr.lst", add_pmp_out, _filter_pmp)]
    )

@app.delete("/api/v2/extract/delete", tags=["MigDB Extract Management"],
    summary="Delete an extract process",
    description="Verifies database login and deletes the specified extract process from MigDB.")
def gg_del_ext(body: DelExtRequest):
    del_ext_out: list[str] = []
 
    login_out, login_ok = _dblogin(body.alias, body.domain)
    del_ext_out.append(login_out)
 
    if not login_ok:
        def _filter_del(raw: str) -> list[str]:
            return _filter_keywords(raw, {"ERROR", "EXTRACT", "Deleted"})
        return JSONResponse(
            content=[_write_and_parse("DelExtErr.lst", del_ext_out, _filter_del)]
        )
 
    proc = _spawn_ggsci()
    proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")
    proc.stdin.write(f"delete {body.extname}\n")
    del_ext_out.append(_communicate(proc))
 
    def _filter_del(raw: str) -> list[str]:
        return _filter_keywords(raw, {"ERROR", "EXTRACT", "Deleted"})
 
    return JSONResponse(
        content=[_write_and_parse("DelExtErr.lst", del_ext_out, _filter_del)]
    )

@app.post("/api/v2/pump/rmttrail", tags=["MigDB Pump Management"],
    summary="Get remote trail path for a pump",
    description="Reads the parameter file for the given pump extract name and returns the configured remote or extract trail path.")
def gg_get_rmt_trail(body: GetRMTTrailRequest):
    rmt_trail = ""
    for name in glob.glob(os.path.join(gg_home, "dirprm", "*.prm")):
        base = os.path.basename(name)
        if re.match(base, body.extName + ".prm", re.IGNORECASE):
            with open(os.path.join(gg_home, "dirprm", base)) as f:
                for line in f:
                    if re.match(r"rmttrail", line, re.IGNORECASE):
                        rmt_trail = line.split()[1]
                    elif re.match(r"exttrail", line, re.IGNORECASE):
                        rmt_trail = line.split()[1]
            break   # stop after first match
 
    return JSONResponse(content=[rmt_trail])

@app.delete("/api/v2/pump/rmttrail/delete", tags=["MigDB Pump Management"],
    summary="Delete a remote trail from a pump",
    description="Finds the remote trail attached to the given pump name and deletes it from MigDB, returning the operation result.")
def gg_del_rmt(body: DelRMTRequest):
    os.makedirs(agent_log, exist_ok=True)
    raw_info = subprocess.getoutput(f"echo -e 'info rmttrail'|{ggsci_bin}")
    log_path = os.path.join(agent_log, "informt.out")
    with open(log_path, "w") as f:
        f.write(raw_info)
 
    del_rmt = ""
    trail_name = ""
    with open(log_path) as f:
        for line in f:
            if "Extract Trail" in line:
                trail_name = line.split(":", 1)[-1].strip()
            elif "Extract" in line:
                ext_name = line.split(":", 1)[-1].strip()
                if ext_name.upper() == body.pmpName.upper():
                    del_rmt = subprocess.getoutput(
                        f"echo -e 'delete rmttrail {trail_name} , extract {body.pmpName}'|{ggsci_bin}"
                    )
                    break  # only the first matching pump matters
 
    if not del_rmt:
        del_rmt = f"No Remote trails attached to pump {body.pmpName}"
 
    def _filter_rmt(raw: str) -> list[str]:
        return _filter_keywords(raw, {"ERROR", "match", "trail", "Deleted"})
 
    return JSONResponse(
        content=[_write_and_parse("DelRMTErr.lst", [del_rmt], _filter_rmt)]
    )

class ExtOpsRequest(BaseModel):
    extops:      str
    extname:     str
    extatcsn:    str | None = None
    extaftercsn: str | None = None
    domain:      str | None = None
    alias:       str | None = None
    beginmode:   str | None = None
    ctvalue:     str | None = None
    scnvalue:    str | None = None
    seqnovalue:  str | None = None
    rbavalue:    str | None = None
    trailname:   list[str] | str | None = None
    trailtype:   str | None = None
    trailsize:   int | str | None = None
 
 
class RepOpsRequest(BaseModel):
    repops:      str
    repname:     str
    domain:      str | None = None
    alias:       str | None = None
    chktbl:      str | None = None
    beginmode:   str | None = None
    ctvalue:     str | None = None
    seqnovalue:  str | None = None
    rbavalue:    str | None = None
    repatcsn:    str | None = None
    repaftercsn: str | None = None
 
 
class MgrOpsRequest(BaseModel):
    mgrOps: str

def proc_stats(filepath: str) -> dict:
    RepProcStats={}
    with open(filepath) as repErrFile:
         table_pattern = re.compile(r"^\s*(Replicating|Extracting)\s+from\s+(\S+)\s+to\s+\S+:\s*$", re.IGNORECASE)
         TabName = None
         for line in repErrFile:
             table_match = table_pattern.search(line)
             if table_match:
                TabName = table_match.group(2)
                RepProcStats.setdefault(TabName, {})
             if TabName is None:
                continue  
             low = line.lower()
             if 'total inserts' in low:
                RepProcStats[TabName].update({'Inserts' :  low.rsplit(None, 1)[-1] })
             elif 'total updates' in low:
                RepProcStats[TabName].update({'Updates' :  low.rsplit(None, 1)[-1] })
             elif 'total deletes' in low:
                RepProcStats[TabName].update({'Deletes' :  low.rsplit(None, 1)[-1] })
             elif 'total upserts' in low:
                RepProcStats[TabName].update({'Upserts' :  low.rsplit(None, 1)[-1] })
             elif 'total discards' in low:
                RepProcStats[TabName].update({'Discards' : low.rsplit(None, 1)[-1]})
             elif 'total operations' in low:
                RepProcStats[TabName].update({'Operations' : low.rsplit(None, 1)[-1] })

             elif 'total cdr conflicts' in low:
                RepProcStats[TabName].update({'CDRConflicts':       low.rsplit(None, 1)[-1]})
             elif 'cdr resolutions succeeded' in low:
                RepProcStats[TabName].update({'CDRResolutions':     low.rsplit(None, 1)[-1]})
             elif 'cdr updaterowexists conflicts' in low:
                RepProcStats[TabName].update({'CDRUpdateRowExists': low.rsplit(None, 1)[-1]})
             elif 'cdr updaterowmissing conflicts' in low:
                RepProcStats[TabName].update({'CDRUpdateRowMissing':low.rsplit(None, 1)[-1]})       
             elif 'cdr insertrowexists conflicts' in low:
                RepProcStats[TabName].update({'CDRInsertRowExists': low.rsplit(None, 1)[-1]})
             elif 'cdr rownotfound conflicts' in low:
                RepProcStats[TabName].update({'CDRRowNotFound':     low.rsplit(None, 1)[-1]})
             elif 'cdr deleterowexists conflicts' in low:
                RepProcStats[TabName].update({'CDRDeleteRowExists': low.rsplit(None, 1)[-1]})
             elif 'cdr deleterowmissing conflicts' in low:
                RepProcStats[TabName].update({'CDRDeleteRowMissing':low.rsplit(None, 1)[-1]})

    return RepProcStats
 
def _wait_for_status(
    proc: subprocess.Popen,
    extname: str,
    target: str,
    poll_cmd: str,
    sleep_sec: int = 60,
) -> None:
    while True:
        output = proc.stdout.readline()
        if target in output:
            break
        time.sleep(sleep_sec)
        proc.stdin.write(poll_cmd)
        proc.stdin.flush()

def _handle_upgie(extname: str, alias: str, domain: str) -> list[str]:
    ext_err: list[str] = []
    proc = _spawn_ggsci(bufsize=1)
    proc.stdin.write(f"info {extname}")
    info = _communicate(proc)
    if "Integrated" in info:
        ext_err.append("Extract is Already in Integrated Mode !! STOP !!")
        return ext_err
    if "Oracle Redo Logs" not in info or "RUNNING" not in info:
        return ext_err
    login_out, login_ok = _dblogin(alias, domain)
    if not login_ok:
        ext_err.append(login_out)
        return ext_err
    proc = _spawn_ggsci(bufsize=1)
    proc.stdin.write(f"send extract {extname} tranlogoptions PREPAREFORUPGRADETOIE\n")
    proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
    proc.stdin.write(f"stop extract {extname}\n")
    time.sleep(60)
    proc.stdin.write(f"info extract {extname}\n")
    proc.stdin.flush()
    _wait_for_status(proc, extname, "STOPPED", f"info extract {extname}\n")
    proc.stdin.write(f"register extract {extname} database\n")
    reg_err = proc.stdout.readline()
    ext_err.append(reg_err)
    if "ERROR" in reg_err and "already registered" not in reg_err:
        proc.kill()
        proc.stdin.close()
        return ext_err
    proc.stdin.write(f"start extract {extname}\n")
    time.sleep(60)
    proc.stdin.write(f"info extract {extname} upgrade\n")
    proc.stdin.flush()
    _wait_for_status(proc, extname, "capture.", f"info extract {extname} upgrade\n")
    proc.stdin.write(f"start extract {extname}\n")
    _communicate(proc)
    return ext_err
 
 
def _handle_dwnie(extname: str, alias: str, domain: str) -> list[str]:
    ext_err: list[str] = []
    proc = _spawn_ggsci(bufsize=1)
    proc.stdin.write(f"info {extname}")
    info = _communicate(proc)
    if "Oracle Redo Logs" in info:
        ext_err.append("Extract is Already in Classic Mode !! STOP !!")
        return ext_err
    if "Integrated" not in info or "RUNNING" not in info:
        return ext_err
    login_out, login_ok = _dblogin(alias, domain)
    if not login_ok:
        ext_err.append(login_out)
        return ext_err
    proc = _spawn_ggsci(bufsize=1)
    proc.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
    proc.stdin.write(f"stop extract {extname}\n")
    time.sleep(60)
    proc.stdin.write(f"info extract {extname}\n")
    proc.stdin.flush()
    _wait_for_status(proc, extname, "STOPPED", f"info extract {extname}\n")
    proc.stdin.write(f"info {extname} downgrade\n")
    info_ie_err = proc.stdout.readline()
    ext_err.append(info_ie_err)
    if "ready to be downgraded" not in info_ie_err:
        proc.kill()
        proc.stdin.close()
        return ext_err
    proc.stdin.write(f"alter extract {extname} downgrade integrated tranlog\n")
    proc.stdin.write(f"info extract {extname}\n")
    proc.stdin.flush()
    _wait_for_status(proc, extname, "Oracle Redo Logs", f"info extract {extname}\n")
    proc.stdin.write(f"unregister extract {extname} database\n")
    proc.stdin.write(f"start extract {extname}\n")
    _communicate(proc)
    return ext_err

@app.get("/api/v2/mgr/report", tags=["MigDB Manager"],
    summary="View manager report file",
    description="Reads and returns the cleaned contents of the MGR.rpt report file from the MigDB dirrpt directory.")
def gg_view_mgr_rpt():
    rpt_path = os.path.join(gg_home, "dirrpt", "MGR.rpt")
    try:
        with open(rpt_path) as f:
            lines = list(clean_gg_log(f.read().splitlines()))
    except OSError as e:
        raise HTTPException(status_code=404, detail=str(e))
 
    df = pd.DataFrame(lines, columns=["line"])
    return JSONResponse(content=[df.values.tolist()])

@app.post("/api/v2/extract/ops", tags=["MigDB Extract Management"],
    summary="Execute extract operations",
    description="Performs a wide range of extract operations including start, stop, kill, delete, stats, checkpoint, trail management, and parameter file editing via GGSCI.")
def gg_ext_ops(body: ExtOpsRequest):
    os.makedirs(agent_log, exist_ok=True)
    extops  = body.extops
    extname = body.extname
    prmfile = ""
    ext_err_print: list[str] = []
    ext_proc_stats: dict = {}
 
    # -- RPT: read report file directly
    if extops == "extrpt":
        for name in glob.glob(os.path.join(gg_home, "dirrpt", "*.rpt")):
            base = os.path.basename(name)
            if re.match(base, extname + ".rpt", re.IGNORECASE):
                with open(os.path.join(gg_home, "dirrpt", base)) as f:
                    ext_err_print = list(clean_gg_log(f))
        return JSONResponse(content=[ext_err_print, prmfile, ext_proc_stats])
 
    # -- EDIT: read param file directly
    if extops == "extedit":
        prm_path = os.path.join(gg_home, "dirprm", extname + ".prm")
        try:
            with open(prm_path) as f:
                prmfile = f.read()
        except OSError as e:
            raise HTTPException(status_code=404, detail=str(e))
        return JSONResponse(content=[ext_err_print, prmfile, ext_proc_stats])
 
    # -- UPGIE / DWNIE: multi-step interactive flows
    if extops == "upgie":
        ext_err_print = _handle_upgie(extname, body.alias or "", body.domain or "")
        return JSONResponse(content=[ext_err_print, prmfile, ext_proc_stats])
 
    if extops == "dwnie":
        ext_err_print = _handle_dwnie(extname, body.alias or "", body.domain or "")
        return JSONResponse(content=[ext_err_print, prmfile, ext_proc_stats])
 
    # -- All other ops: single ggsci session
    proc = _spawn_ggsci()
 
    if extops == "extchk":
        proc.stdin.write(f"info {extname} showch debug")
 
    elif extops == "extstats":
        proc.stdin.write(f"stats extract {extname},TOTAL\n")
 
    elif extops == "extstartdef":
        proc.stdin.write(f"start extract {extname}\n")
 
    elif extops == "extstartatcsn":
        proc.stdin.write(f"start {extname} atcsn {body.extatcsn}\n")
 
    elif extops == "extstartaftercsn":
        proc.stdin.write(f"start {extname} aftercsn {body.extaftercsn}\n")
 
    elif extops == "extstop":
        proc.stdin.write(f"stop extract {extname}\n")
 
    elif extops == "extforcestop":
        proc.stdin.write(f"send extract {extname} forcestop\n")
 
    elif extops == "extkill":
        proc.stdin.write(f"kill extract {extname}\n")
 
    elif extops == "extstatus":
        proc.stdin.write(f"send extract {extname} status\n")
 
    elif extops == "extdel":
        proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")
        proc.stdin.write(f"delete extract {extname}\n")
 
    elif extops == "pmpdel":
        proc.stdin.write(f"delete extract {extname}\n")
 
    elif extops == "extetroll":
        proc.stdin.write(f"alter extract {extname} etrollover\n")
 
    elif extops == "extbegin":
        beginmode = body.beginmode or ""
        if beginmode == "Now":
            proc.stdin.write(f"alter extract {extname},begin now\n")
        elif beginmode == "Time":
            ctvalue = (body.ctvalue or "").replace("T", " ")
            proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")
            proc.stdin.write(f"alter extract {extname},begin {ctvalue}\n")
        elif beginmode == "SCN":
            proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")
            proc.stdin.write(f"alter extract {extname},scn {body.scnvalue}\n")
        elif beginmode == "pmpextseqno":
            proc.stdin.write(
                f"alter extract {extname},extseqno {body.seqnovalue},extrba {body.rbavalue}\n"
            )
 
    elif extops == "exttraildel":
        for trail in (body.trailname or []):
            proc.stdin.write(f"delete exttrail {trail}, Extract {extname}\n")
 
    elif extops == "exttrailadd":
        trail = body.trailname[0] if isinstance(body.trailname, list) else body.trailname
        proc.stdin.write(
            f"add {body.trailtype} {trail}, Extract {extname},megabytes {body.trailsize}\n"
        )
 
    elif extops == "cachemgr":
        proc.stdin.write(f"send extract {extname} cachemgr cachestats\n")
 
    elif extops == "extunreg":
        proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")
        proc.stdin.write(f"unregister extract {extname} database\n")
 
    else:
        proc.kill()
        raise HTTPException(status_code=400, detail=f"Unknown extops value: {extops!r}")
 
    raw = _communicate(proc)
 
    if extops == "extstats":
        stats_path = os.path.join(agent_log, "extStats")
        with open(stats_path, "w") as f:
            f.write(raw)
        ext_proc_stats = proc_stats(stats_path)
    else:
        chk_path = os.path.join(agent_log, "ChkExt.lst")
        with open(chk_path, "w") as f:
            f.write(raw)
        with open(chk_path) as f:
            for line in clean_gg_log(f):
                ext_err_print.append(line)

    return JSONResponse(content=[ext_err_print, prmfile, ext_proc_stats])

@app.post("/api/v2/replicat/ops", tags=["MigDB Replicat Management"],
    summary="Execute replicat operations",
    description="Performs a wide range of replicat operations including start, stop, kill, delete, stats, checkpoint, integrated mode changes, and parameter file editing via GGSCI.")
def gg_rep_ops(body: RepOpsRequest):
    os.makedirs(agent_log, exist_ok=True)
    repops  = body.repops
    repname = body.repname
    rep_err_print: list[str] = []
    rep_proc_stats: dict = {}
    prm_file = ""
 
    # -- RPT: read report file directly
    if repops == "reprpt":
        for name in glob.glob(os.path.join(gg_home, "dirrpt", "*.rpt")):
            base = os.path.basename(name)
            if re.match(base, repname + ".rpt", re.IGNORECASE):
                with open(os.path.join(gg_home, "dirrpt", base)) as f:
                    rep_err_print = list(clean_gg_log(f))
        return JSONResponse(content=[rep_err_print, prm_file, rep_proc_stats])
 
    # -- EDIT: read param file directly
    if repops == "repedit":
        prm_path = os.path.join(gg_home, "dirprm", repname + ".prm")
        try:
            with open(prm_path) as f:
                prm_file = f.read()
        except OSError as e:
            raise HTTPException(status_code=404, detail=str(e))
        return JSONResponse(content=[rep_err_print, prm_file, rep_proc_stats])
 
    # -- All other ops: single ggsci session
    proc = _spawn_ggsci()
 
    if repops == "repchk":
        proc.stdin.write(f"info {repname} showch\n")
 
    elif repops == "repstatus":
        proc.stdin.write(f"send {repname} status\n")
 
    elif repops == "repdetail":
        proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")
        proc.stdin.write(f"info {repname} detail\n")
 
    elif repops == "repstats":
        proc.stdin.write(f"stats replicat {repname},TOTAL\n")

    elif repops == "cdrstats":
        proc.stdin.write(f"stats replicat {repname},TOTAL, REPORTCDR\n")
 
    elif repops == "repstartdef":
        proc.stdin.write(f"start replicat {repname}\n")
 
    elif repops == "repskiptrans":
        proc.stdin.write(f"start replicat {repname} SKIPTRANSACTION\n")
 
    elif repops == "repnofilterdup":
        proc.stdin.write(f"start replicat {repname} NOFILTERDUPTRANSACTIONS\n")
 
    elif repops == "repatcsn":
        proc.stdin.write(f"start replicat {repname} ATCSN {body.repatcsn}\n")
 
    elif repops == "repaftercsn":
        proc.stdin.write(f"start replicat {repname}, AFTERCSN {body.repaftercsn}\n")
 
    elif repops == "repstop":
        proc.stdin.write(f"stop replicat {repname}\n")
 
    elif repops == "repforcestop":
        proc.stdin.write(f"send replicat {repname} forcestop\n")
 
    elif repops == "repkill":
        proc.stdin.write(f"kill replicat {repname}\n")
 
    elif repops == "cachemgr":
        proc.stdin.write(f"send replicat {repname} cachemgr cachestats\n")
 
    elif repops == "repdel":
        proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")
        proc.stdin.write(f"delete replicat {repname}\n")
 
    elif repops == "upgir":
        proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")
        proc.stdin.write(f"alter replicat {repname},integrated\n")
 
    elif repops == "dwnir":
        proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")
        proc.stdin.write(f"alter replicat {repname} nonintegrated ,CHECKPOINTTABLE {body.chktbl}\n")
 
    elif repops == "repbegin":
        beginmode = body.beginmode or ""
        proc.stdin.write(f"dblogin useridalias {body.alias} domain {body.domain}\n")
        if beginmode == "Now":
            proc.stdin.write(f"alter replicat {repname},begin now\n")
        elif beginmode == "Time":
            proc.stdin.write(f"alter replicat {repname},begin {body.ctvalue}\n")
        elif beginmode == "LOC":
            proc.stdin.write(
                f"alter replicat {repname},extseqno {body.seqnovalue},extrba {body.rbavalue}\n"
            )
 
    else:
        proc.kill()
        raise HTTPException(status_code=400, detail=f"Unknown repops value: {repops!r}")
 
    raw = _communicate(proc)

 
    if repops == "repstats":
        stats_path = os.path.join(agent_log, "repStats")
        with open(stats_path, "w") as f:
            f.write(raw)
        rep_proc_stats = proc_stats(stats_path)
    elif repops == "cdrstats":
        stats_path = os.path.join(agent_log, "cdrstats")
        with open(stats_path, "w") as f:
            f.write(raw)
        rep_proc_stats = proc_stats(stats_path)
    else:
        chk_path = os.path.join(agent_log, "ChkRep.lst")
        with open(chk_path, "w") as f:
            f.write(raw)
        with open(chk_path) as f:
            rep_err_print = list(clean_gg_log(f))
 
    return JSONResponse(content=[rep_err_print, prm_file, rep_proc_stats])

_MGR_COMMANDS: dict[str, str] = {
    "mgrstart":       "start manager",
    "mgrstop":        "stop manager!",
    "mgrrefresh":     "refresh manager",
    "mgrkill":        "kill manager",
    "mgrchildstatus": "send manager childstatus debug",
    "mgrportinfo":    "send manager GETPORTINFO detail",
    "mgrpurgeold":    "send manager GETPURGEOLDEXTRACTS detail",
}
 
@app.post("/api/v2/mgr/ops", tags=["MigDB Manager"],
    summary="Execute manager operations",
    description="Runs a manager operation command via GGSCI such as start, stop, refresh, or status and returns the parsed output.")
def gg_mgr_ops(body: MgrOpsRequest):
    os.makedirs(agent_log, exist_ok=True)
    mgr_op = body.mgrOps
 
    cmd = _MGR_COMMANDS.get(mgr_op)
    if not cmd:
        raise HTTPException(status_code=400, detail=f"Unknown mgrOps value: {mgr_op!r}")
 
    proc = _spawn_ggsci()
    proc.stdin.write(cmd)
    raw = _communicate(proc)

    mgr_ops_print = []
    log_path = os.path.join(agent_log, "MgrOps.lst")
    with open(log_path, "w") as f:
        f.write(raw)
    with open(log_path) as f:
        for line in clean_gg_log(f):
            mgr_ops_print.append(line)

    return JSONResponse(content=[mgr_ops_print])

split_qualify_size: str = os.environ.get("SPLIT_QUALIFY_SIZE", "1024")

def _parse_lines(raw: str, keywords: list[str]) -> list[str]:
    result = []
    for line in raw.splitlines():
        line_lower = line.lower()
        if any(kw.lower() in line_lower for kw in keywords):
            result.append(line.split(">", 1)[-1].strip())
    return result

class ExtShowTransRequest(BaseModel):
    extname: str
 
 
class ExtSkipTransRequest(BaseModel):
    extname: str
    xid: str
 
 
class AddReplicatRequest(BaseModel):
    repname: str
    domain: str
    alias: str
    repmode: str
    beginmode: str
    csnVal: Optional[str] = None
    trail: str
    chkpttbl: str
    currentParamList: str
    startRepChk: bool
    @field_validator("csnVal", mode="before")
    @classmethod
    def coerce_csn_to_str(cls, v):
        if v is None:
            return v
        return str(v)
 
 
class CdbCheckRequest(BaseModel):
    dbname: str
 
 
class LmDictDetRequest(BaseModel):
    dbname: str
 
 
class TableListRequest(BaseModel):
    dbname: str
    schemaList: list[str]
    cdbCheck: str
    pdbName: str
    gatherMeta: bool
    LoadName: Optional[str] = None

@app.post("/api/v2/extract/showtrans", tags=["MigDB Extract Management"],
    summary="Show active extract transactions",
    description="Sends a SHOWTRANS command to the specified extract process and returns a parsed tabular list of active transactions including XID, SCN, status, and timing details.")
def ext_show_trans(body: ExtShowTransRequest) -> list:
    output = _run_ggsci(f"SEND EXTRACT {body.extname} SHOWTRANS TABULAR")
    _write_log("ExtShowTrans.lst", output)
 
    ext_show_trans_print = []
    copy = False
    result = []
 
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("-"):
            continue
        if "ERROR" in line:
            result = [line.split(">", 1)[-1].strip()]
            return [result]
        if line.startswith("XID"):
            copy = True
            continue
        if line.startswith("GGSCI"):
            copy = False
            continue
        if copy:
            ext_show_trans_print.append(line.split())
 
    if ext_show_trans_print:
        df = pd.DataFrame(
            ext_show_trans_print,
            columns=["XID", "Items", "Extract", "Redo Thread", "Start Time", "SCN", "Redo Seq", "Redo RBA", "Status"],
        )
        result = df.to_dict("records")
 
    return [result]

@app.post("/api/v2/extract/skiptrans", tags=["MigDB Extract Management"],
    summary="Skip an extract transaction",
    description="Forces the specified extract process to skip a given transaction ID and returns the operation result.")
def ext_skip_trans(body: ExtSkipTransRequest) -> list[list[str]]:
    xid = body.xid.lstrip('["').rstrip('"]')
    output = _run_ggsci(f"SEND EXTRACT {body.extname} SKIPTRANS {xid} FORCE")
    _write_log("ExtSkipTrans.lst", output)
    parsed = _parse_lines(output, ["ERROR", "skipped", "not found"])
    return [parsed]

@app.post("/api/v2/replicat/add", tags=["MigDB Replicat Management"],
    summary="Add a replicat process",
    description="Verifies database login, creates the replicat with the specified mode and trail, writes the parameter file, and optionally starts the replicat with the given begin mode.")
def add_replicat(body: AddReplicatRequest) -> list[list[str]]:
    if body.beginmode in ("ATCSN", "AFTERCSN") and not body.csnVal:
        raise HTTPException(status_code=422, detail="csnVal is required for ATCSN or AFTERCSN beginmode")
 
    login_output = _run_ggsci(f"dblogin useridalias {body.alias} domain {body.domain}")
 
    if "error" in login_output.lower():
        _write_log("AddRepErr.lst", login_output)
        return [_parse_lines(login_output, ["ERROR", "added.", "starting"])]
 
    commands = [f"dblogin useridalias {body.alias} domain {body.domain}",
        f"add replicat {body.repname} {body.repmode} exttrail {body.trail} , checkpointtable {body.chkpttbl}"]

    add_output = _run_ggsci(*commands)
 
    if "error" in add_output.lower():
        _write_log("AddRepErr.lst", add_output)
        return [_parse_lines(add_output, ["ERROR", "added.", "starting"])]
 
    rep_prm_path = os.path.join(gg_home, "dirprm", f"{body.repname}.prm")
    os.makedirs(os.path.dirname(rep_prm_path), exist_ok=True)
    with open(rep_prm_path, "w") as fh:
        fh.write(body.currentParamList)
 
    combined_output = add_output
 
    if not body.startRepChk:
        if body.beginmode == "DEFAULT":
            start_cmd = f"start replicat {body.repname}"
        elif body.beginmode == "ATCSN":
            start_cmd = f"start replicat {body.repname} , atcsn {body.csnVal}"
        elif body.beginmode == "AFTERCSN":
            start_cmd = f"start replicat {body.repname} , aftercsn {body.csnVal}"
        else:
            start_cmd = f"start replicat {body.repname}"
 
        start_output = _run_ggsci(start_cmd)
        combined_output += start_output

    _write_log("AddRepErr.lst", combined_output)
    parsed = _parse_lines(combined_output, ["ERROR", "added.", "starting"])
    return [parsed]

@app.post("/api/v2/db/cdbcheck", tags=["MigDB Database"],
    summary="Check CDB status and fetch database details",
    description="Connects to the database, checks if it is a CDB, fetches PDB names, schema list, and full database details including version, host, edition, and current SCN.")
def cdb_check(body: CdbCheckRequest) -> list:
    val = selectConn(body.dbname)
    con = val[3]
    db_main_ver = val[1]
    cdb_check_val = "NO"
    pdb_name_fetch = ""
    schema_data_fetch = ""
    db_details_fetch = ""
    isPDBLogin = False
    cdb_version_val = "EE"
 
    try:
        if "ORA-" in str(db_main_ver):
            pdb_name_fetch = db_main_ver
        else:
            if int(db_main_ver) > 11:
                cdb_df = pd.read_sql_query("SELECT CDB FROM v$database", con)
                cdb_check_val = cdb_df.to_dict("records")[0]["cdb"]
                cdb_version_val = get_oracle_edition_abbr(con)
 
                if cdb_check_val == "YES":
                    pdb_login_sql = """ SELECT SYS_CONTEXT('USERENV', 'CON_NAME') AS container_name,
                                    SYS_CONTEXT('USERENV', 'CON_ID')   AS container_id FROM DUAL"""
                    pdb_login_details_fetch = pd.read_sql_query(pdb_login_sql, con).to_dict("records")
                    if pdb_login_details_fetch:
                        container_id = int(pdb_login_details_fetch[0].get('container_id', 0))
                        isPDBLogin   = container_id >= 3

                        schema_data_fetch = pd.read_sql_query(
                            """SELECT username FROM all_users
                            WHERE username NOT IN ('SYS','SYSTEM','PUBLIC','ORACLE_OCM','DBSNMP','APPQOSSYS',
                            'ANONYMOUS','DBSFWUSER','SI_INFORMTN_SCHEMA','CTXSYS','AUDSYS','OJVMSYS',
                            'REMOTE_SCHEDULER_AGENT','GSMADMIN_INTERNAL','ORDPLUGINS','MDSYS','OLAPSYS',
                            'LBACSYS','OUTLN','XDB','WMSYS','DVF','ORDDATA','DVSYS','ORDSYS','SYSDG',
                            'SYSRAC','SYSKM','SYSBACKUP','MDDATA','GGSYS','GSMCATUSER','XS$NULL','MIGDB',
                            'PDBADMIN','DIP','SYS$UMF')""", con
                        ).to_dict("records")

                    pdb_df = pd.read_sql_query(
                        "SELECT NAME FROM v$pdbs WHERE NAME NOT IN ('CDB$ROOT','PDB$SEED')", con
                    )
                    pdb_name_fetch = pdb_df.to_dict("records")
                    db_details_sql = """SELECT db.DBid, db.name DBNAME, p.name PDBNAME, db.platform_name,
                                               i.HOST_NAME HOST, i.VERSION,
                                               DECODE(regexp_substr(v.banner,'[^ ]+',1,4),'Edition','Standard',
                                                      regexp_substr(v.banner,'[^ ]+',1,4)) DB_Edition,
                                               i.instance_number instance, db.database_role, db.current_scn, db.cdb
                                        FROM v$database db, v$instance i, v$version v, v$pdbs p
                                        WHERE banner LIKE 'Oracle%'"""
                else:
                    db_details_sql = """SELECT db.DBid, db.name DBNAME, db.platform_name, i.HOST_NAME HOST, i.VERSION,
                                               DECODE(regexp_substr(v.banner,'[^ ]+',1,4),'Edition','Standard',
                                                      regexp_substr(v.banner,'[^ ]+',1,4)) DB_Edition,
                                               i.instance_number instance, db.database_role, db.current_scn
                                        FROM v$database db, v$instance i, v$version v
                                        WHERE banner LIKE 'Oracle%'"""
                    schema_data_fetch = pd.read_sql_query(
                        """SELECT username FROM all_users
                           WHERE username NOT IN ('SYS','SYSTEM','PUBLIC','ORACLE_OCM','DBSNMP','APPQOSSYS',
                           'ANONYMOUS','DBSFWUSER','SI_INFORMTN_SCHEMA','CTXSYS','AUDSYS','OJVMSYS',
                           'REMOTE_SCHEDULER_AGENT','GSMADMIN_INTERNAL','ORDPLUGINS','MDSYS','OLAPSYS',
                           'LBACSYS','OUTLN','XDB','WMSYS','DVF','ORDDATA','DVSYS','ORDSYS','SYSDG',
                           'SYSRAC','SYSKM','SYSBACKUP','MDDATA','GGSYS','GSMCATUSER','XS$NULL','MIGDB',
                           'PDBADMIN','DIP','SYS$UMF')""", con
                    ).to_dict("records")
            else:
                db_details_sql = """SELECT db.DBid, db.name DBNAME, db.platform_name, i.HOST_NAME HOST, i.VERSION,
                                           DECODE(regexp_substr(v.banner,'[^ ]+',1,4),'Edition','Standard',
                                                  regexp_substr(v.banner,'[^ ]+',1,4)) DB_Edition,
                                           i.instance_number instance, db.database_role, db.current_scn
                                    FROM v$database db, v$instance i, v$version v
                                    WHERE banner LIKE 'Oracle%'"""
                schema_data_fetch = pd.read_sql_query(
                    """SELECT username FROM all_users
                       WHERE username NOT IN ('SYS','SYSTEM','PUBLIC','ORACLE_OCM','DBSNMP','APPQOSSYS',
                       'ANONYMOUS','DBSFWUSER','SI_INFORMTN_SCHEMA','CTXSYS','AUDSYS','OJVMSYS',
                       'REMOTE_SCHEDULER_AGENT','GSMADMIN_INTERNAL','ORDPLUGINS','MDSYS','OLAPSYS',
                       'LBACSYS','OUTLN','XDB','WMSYS','DVF','ORDDATA','DVSYS','ORDSYS','SYSDG',
                       'SYSRAC','SYSKM','SYSBACKUP','MDDATA','GGSYS','GSMCATUSER','XS$NULL','MIGDB',
                       'PDBADMIN','DIP','SYS$UMF')""", con
                ).to_dict("records")
 
            db_details_fetch = pd.read_sql_query(db_details_sql, con).to_dict("records")

 
    except oracledb.DatabaseError as exc:
        db_details_fetch = str(exc)
        logger.info(str(exc))
    finally:
        if con:
            con.close()
    return [cdb_check_val, pdb_name_fetch, schema_data_fetch, db_details_fetch, trail_path, isPDBLogin, cdb_version_val]

@app.post("/api/v2/db/lmdictdet", tags=["MigDB Database"],
    summary="Fetch LogMiner dictionary details",
    description="Retrieves active capture client names and archived log entries where dictionary begins, used for LogMiner-based extract configuration.")
def lm_dict_det(body: LmDictDetRequest) -> list:
    val = selectConn(body.dbname)
    con = val[3]
    db_main_ver = val[1]
 
    if int(db_main_ver) > 11:
        capture_sql = "SELECT CLIENT_NAME FROM cdb_capture"
    else:
        capture_sql = "SELECT CLIENT_NAME FROM dba_capture"
 
    capture_fetch = pd.read_sql_query(capture_sql, con).to_dict("records")
 
    dict_det_fetch = pd.read_sql_query(
        """SELECT first_change# FIRST_CHANGE, FIRST_TIME
           FROM v$archived_log
           WHERE dictionary_begin = 'YES'
             AND standby_dest = 'NO'
             AND name IS NOT NULL
             AND status = 'A'""", con
    ).astype(str).to_dict("records")
 
    return [capture_fetch, dict_det_fetch]

@app.post("/api/v2/db/tablelist", tags=["MigDB Database"],
    summary="Fetch table list for schemas",
    description="Queries all tables for the given schema list, saves table metadata to CSV, calculates average space, and optionally gathers column-level Oracle metadata for each table.")
def table_list(body: TableListRequest) -> list:
    val = selectConn(body.dbname)
    con = val[0]
    cursor = con.cursor()
    table_name_list = []
    auto_qualify_split = []
    load_name = body.LoadName or ""
 
    try:
        bind_names = ",".join(f":{i}" for i in range(len(body.schemaList)))
        schemas = list(body.schemaList)
 
        if body.cdbCheck == "YES" and body.pdbName:
            cursor.execute(f"ALTER SESSION SET CONTAINER={body.pdbName}")
 
        cursor.execute("SELECT value FROM v$parameter WHERE name='db_block_size'")
        blk_size_fetch = cursor.fetchone()
 
        if load_name:
            folder_path = os.path.join(agent_home, load_name)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
            os.makedirs(folder_path, exist_ok=True)
 
        if body.cdbCheck == "YES" and body.pdbName:
            table_sql = f"""SELECT owner, table_name, num_rows, blocks, avg_space, last_analyzed, 'proc' proc
                            FROM all_tables WHERE owner IN ({bind_names})"""
        else:
            table_sql = f"""SELECT owner, table_name, num_rows, blocks, avg_space, last_analyzed, 'proc'
                            FROM all_tables WHERE owner IN ({bind_names})"""

        cursor.execute(table_sql, schemas)
        table_fetch = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
 
        if table_fetch:
            df = pd.DataFrame(table_fetch)
            if body.cdbCheck == "YES" and body.pdbName:
                df.to_csv(
                    os.path.join(agent_home, load_name, f"{load_name}_{body.pdbName}_tables"),
                    header=col_names,
                )
            else:
                df.to_csv(
                    os.path.join(agent_home, load_name, f"{load_name}_tables"),
                    header=col_names,
                )
 
        for row in table_fetch:
            avg_space = (
                round(((int(row[3]) * int(blk_size_fetch[0])) - (int(row[3]) * int(row[4]))) / 1024 / 1024)
                if row[3]
                else 0
            )
            last_analyzed = row[5].date().isoformat() if row[5] is not None else "Not Analyzed"
 
            table_name_list.append({
                "owner": row[0],
                "table_name": row[1],
                "num_rows": row[2],
                "avg_space": avg_space,
                "last_analyzed": last_analyzed,
            })
 
            if avg_space > int(split_qualify_size):
                auto_qualify_split.append({"table_name": f"{row[0]}.{row[1]}"})
 
            if body.gatherMeta:
                meta_df = pd.read_sql_query(
                    """SELECT O.NAME TABLE_NAME, T.OBJ#, C.NAME COLUMN_NAME, C.TYPE# DTYPE,
                              C.CHARSETFORM, C.LENGTH, C.SCALE, C.PRECISION#, C.INTCOL#, TS.NAME TSNAME
                       FROM SYS.OBJ$ O, SYS.TAB$ T, SYS.COL$ C, ALL_USERS U, SYS.TS$ TS
                       WHERE O.OBJ# = T.OBJ# AND C.OBJ# = T.OBJ# AND U.USER_ID = O.OWNER#
                         AND TS.TS# = T.TS# AND U.USERNAME = :owner AND O.NAME = :table_name
                       ORDER BY O.NAME, C.INTCOL#""",
                    con,
                    params=[str(row[0]), str(row[1])],
                )
                if load_name:
                    meta_df.to_csv(
                        os.path.join(agent_home, load_name, f"OracleMetaData_{row[0]}_{row[1]}"),
                        index=False,
                    )
 
    except oracledb.DatabaseError as exc:
        logger.info(str(exc))
        table_name_list.append(str(exc))
    finally:
        if con:
            cursor.close()
            con.close()

    return [table_name_list, gg_home, auto_qualify_split]


class CDRTableListRequest(BaseModel):
    dbname:     str
    schemaList: list[str]
    cdbCheck:   str = "NO"
    pdbName:    str | None = None

@app.post(
    "/api/v2/db/cdrtablelist",
    tags=["MigDB AutoCDR"],
    summary="Fetch table list for ACDR compatibility",
    description="Queries all tables for the given schema list, checks for Auto CDR compatibility"
)
def cdr_table_list(body: CDRTableListRequest) -> list:
    val = selectConn(body.dbname)
    con = val[0]

    cursor = con.cursor()
    table_name_list = []

    try:
        # Switch container if CDB mode
        if body.cdbCheck == "YES" and body.pdbName:
            cursor.execute(f"ALTER SESSION SET CONTAINER = {body.pdbName}")

        # Build bind variables for schema list
        bind_names = ", ".join(f":{i}" for i in range(len(body.schemaList)))
        schemas    = list(body.schemaList)

        table_sql = f"""
            SELECT
                c.owner || '.' || c.table_name  AS table_name,
                c.constraint_type,
                cc.column_name,
                cc.position,
                tc.nullable,
                c.status,
                c.validated,
                CASE
                    WHEN c.constraint_type = 'P'
                        THEN 'Compatible'
                    WHEN c.constraint_type = 'U'
                     AND tc.nullable       = 'N'
                     AND NOT EXISTS (
                             SELECT 1
                             FROM   all_constraints pk
                             WHERE  pk.owner           = c.owner
                             AND    pk.table_name      = c.table_name
                             AND    pk.constraint_type = 'P'
                         )
                        THEN 'Compatible'
                    ELSE 'Not Compatible'
                END AS acdr_status
            FROM   all_constraints  c
            JOIN   all_cons_columns cc
                   ON  c.constraint_name = cc.constraint_name
                   AND c.owner           = cc.owner
            JOIN   all_tab_columns  tc
                   ON  tc.owner       = c.owner
                   AND tc.table_name  = c.table_name
                   AND tc.column_name = cc.column_name
            WHERE  c.owner           IN ({bind_names})
            AND    c.constraint_type IN ('P', 'U')
            ORDER BY c.owner, c.table_name, c.constraint_type, cc.position
        """

        cursor.execute(table_sql, schemas)
        table_fetch = cursor.fetchall()
        col_names   = [desc[0] for desc in cursor.description]

        # Build response as list of dicts
        for row in table_fetch:
            row_dict = dict(zip(col_names, row))
            table_name_list.append(row_dict)

        if not table_name_list:
            raise HTTPException(
                status_code=404,
                detail=f"No tables found for schemas: {body.schemaList}"
            )

        return table_name_list

    except oracledb.DatabaseError as e:
        error, = e.args
        raise HTTPException(
            status_code=500,
            detail={
                "oracle_error_code":    error.code,
                "oracle_error_message": error.message,
                "context":              "table_list query failed"
            }
        )
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error in table_list: {str(e)}"
        )

    finally:
        cursor.close()

class CDRActionRequest(BaseModel):
    domain      : str
    alias       : str
    dbname      : str
    schemaList  : List[str]       = []
    tabNameList : List[str]       = []
    buttonValue : str             = 'info'
    cdbCheck    : Optional[str]   = 'NO'
    pdbName     : Optional[str]   = ''

@app.post(
    "/api/v2/cdr/action",
    tags=["CDR Management"],
    summary="Enable, view or disable Auto CDR for selected tables",
    description=(
        "Streams per-table CDR results as SSE. "
        "buttonValue: 'add' = enable, 'info' = view, 'del' = disable."
    )
)
async def cdr_action(body: CDRActionRequest):

    def generate():

        try:
            val = selectConn(body.dbname)
            con = val[0]
        except Exception as e:
            yield f"data: {json.dumps({'tableName': '', 'status': 'Error', 'message': f'DB Connection failed: {str(e)}'})}\n\n"
            yield "data: __DONE__\n\n"
            return

        try:
            if body.cdbCheck == 'YES' and body.pdbName:
                cur = con.cursor()
                cur.execute(f"ALTER SESSION SET CONTAINER = {body.pdbName}")
                cur.close()
        except Exception as e:
            yield f"data: {json.dumps({'tableName': '', 'status': 'Error', 'message': f'Container switch failed: {str(e)}'})}\n\n"
            yield "data: __DONE__\n\n"
            return

        seen = set()  

        for tabname in body.tabNameList:
            tabname = tabname.strip()
            if not tabname:
                continue

            if tabname in seen:
                continue
            seen.add(tabname)

            if '.' in tabname:
                schema_name, table_name = tabname.split('.', 1)
            else:
                yield f"data: {json.dumps({'tableName': tabname, 'status': 'Error', 'message': 'Table name must be in SCHEMA.TABLE format'})}\n\n"
                continue

            schema_name = schema_name.strip().upper()
            table_name  = table_name.strip().upper()

            cursor = con.cursor()
            
            if body.buttonValue == 'add':
                # ── Enable CDR ────────────────────────────────────────────────
                try:
                    cursor.execute("""
                        BEGIN
                            DBMS_GOLDENGATE_ADM.ADD_AUTO_CDR(
                                schema_name            => :schema_name,
                                table_name             => :table_name,
                                resolution_granularity => 'ROW',
                                tombstone_deletes      => TRUE,
                                fetchcols              => TRUE,
                                record_conflicts       => TRUE,
                                use_custom_handlers    => 0
                            );
                        END;
                    """, {
                        'schema_name': schema_name,
                        'table_name' : table_name
                    })
                    con.commit()
                    result = {
                        'tableName'  : f"{schema_name}.{table_name}",
                        'status'     : 'Enabled',
                        'cdrType'    : 'AUTO',
                        'resolution' : 'ROW',
                        'message'    : 'CDR enabled successfully'
                    }

                except oracledb.DatabaseError as e:
                    error_obj   = e.args[0]
                    ora_code    = getattr(error_obj, 'code',    0)
                    ora_message = getattr(error_obj, 'message', str(e)).strip()

                    # ORA-26960: CDR already enabled → treat as success
                    if ora_code == 26960:
                        try: con.rollback()
                        except: pass
                        result = {
                            'tableName'  : f"{schema_name}.{table_name}",
                            'status'     : 'Already Enabled',
                            'cdrType'    : 'AUTO',
                            'resolution' : 'ROW',
                            'message'    : 'CDR was already configured for this table'
                        }
                    else:
                        try: con.rollback()
                        except: pass
                        result = {
                            'tableName'  : f"{schema_name}.{table_name}",
                            'status'     : 'Error',
                            'cdrType'    : '',
                            'resolution' : '',
                            'message'    : f'ORA-{ora_code}: {ora_message}'
                        }

            elif body.buttonValue == 'del':
                # ── Disable CDR ───────────────────────────────────────────────
                try:
                    cursor.execute("""
                        BEGIN
                            DBMS_GOLDENGATE_ADM.REMOVE_AUTO_CDR(
                                schema_name => :schema_name,
                                table_name  => :table_name
                            );
                        END;
                    """, {
                        'schema_name': schema_name,
                        'table_name' : table_name
                    })
                    con.commit()
                    result = {
                        'tableName'  : f"{schema_name}.{table_name}",
                        'status'     : 'Disabled',
                        'cdrType'    : '',
                        'resolution' : '',
                        'message'    : 'CDR disabled successfully'
                    }

                except oracledb.DatabaseError as e:
                    error_obj   = e.args[0]
                    ora_code    = getattr(error_obj, 'code',    0)
                    ora_message = getattr(error_obj, 'message', str(e)).strip()

                    # ORA-26961: CDR not configured → treat as info
                    if ora_code == 26961:
                        try: con.rollback()
                        except: pass
                        result = {
                            'tableName'  : f"{schema_name}.{table_name}",
                            'status'     : 'Not Configured',
                            'cdrType'    : '',
                            'resolution' : '',
                            'message'    : 'CDR was not configured on this table'
                        }
                    else:
                        try: con.rollback()
                        except: pass
                        result = {
                            'tableName'  : f"{schema_name}.{table_name}",
                            'status'     : 'Error',
                            'cdrType'    : '',
                            'resolution' : '',
                            'message'    : f'ORA-{ora_code}: {ora_message}'
                        }

            elif body.buttonValue == 'info':
                try:
                    cursor.execute("""
                        SELECT
                            t.TABLE_OWNER,
                            t.TABLE_NAME,
                            t.TOMBSTONE_TABLE,
                            t.ROW_RESOLUTION_COLUMN
                        FROM ALL_GG_AUTO_CDR_TABLES t
                        WHERE t.TABLE_OWNER = :schema_name
                        AND   t.TABLE_NAME  = :table_name
                    """, {
                        'schema_name': schema_name,
                        'table_name' : table_name
                    })
                    row = cursor.fetchone()

                    if row:

                        cursor.execute("""
                            SELECT COLUMN_NAME
                            FROM   ALL_TAB_COLUMNS
                            WHERE  TABLE_NAME = 'ALL_GG_AUTO_CDR_COLUMNS'
                            AND    OWNER      = 'SYS'
                            ORDER BY COLUMN_ID
                        """)
                        available_cols = [r[0] for r in cursor.fetchall()]

                        select_cols = "TABLE_OWNER, TABLE_NAME, COLUMN_NAME"

                        # Optional columns — add only if they exist
                        if 'COLUMN_GROUP_NAME'   in available_cols: select_cols += ", COLUMN_GROUP_NAME"
                        if 'RESOLUTION_COLUMN'   in available_cols: select_cols += ", RESOLUTION_COLUMN"
                        if 'DELTA_RESOLUTION'    in available_cols: select_cols += ", DELTA_RESOLUTION"
                        if 'RESOLUTION_TYPE'     in available_cols: select_cols += ", RESOLUTION_TYPE"

                        # Also get column-level detail from ALL_GG_AUTO_CDR_COLUMNS
                        cursor.execute(f"""
                            SELECT {select_cols}
                            FROM ALL_GG_AUTO_CDR_COLUMNS c
                            WHERE c.TABLE_OWNER = :schema_name
                            AND   c.TABLE_NAME  = :table_name
                            AND   ROWNUM        <= 10
                        """, {
                            'schema_name': schema_name,
                            'table_name' : table_name
                        })
                        col_rows   = cursor.fetchall()

                        col_detail = 'N/A'
                        if col_rows:
                            col_names = []
                            for c in col_rows:
                                col_entry = c[2]
                                if 'COLUMN_GROUP_NAME' in available_cols and len(c) > 3:
                                    grp = c[available_cols.index('COLUMN_GROUP_NAME') - 
                                            (len(available_cols) - len(c))]
                                    if grp:
                                        col_entry += f"(grp:{grp})"
                                col_names.append(col_entry)
                            col_detail = ', '.join(col_names)

                        result = {
                            'tableName'  : f"{schema_name}.{table_name}",
                            'status'     : 'Active',
                            'cdrType'    : 'AUTO CDR',
                            'resolution' : row[3] or 'ROW',   # ROW_RESOLUTION_COLUMN
                            'message'    : (
                                f'Auto CDR active. '
                                f'Tombstone table: {row[2] or "N/A"}. '
                                f'Resolution col: {row[3] or "N/A"}. '
                                f'Columns: {col_detail}'
                            )
                        }
                    else:
                        result = {
                            'tableName'  : f"{schema_name}.{table_name}",
                            'status'     : 'Not Configured',
                            'cdrType'    : '',
                            'resolution' : '',
                            'message'    : 'Auto CDR not configured for this table'
                        }

                except oracledb.DatabaseError as e:
                    error_obj   = e.args[0]
                    ora_code    = getattr(error_obj, 'code',    'UNKNOWN')
                    ora_message = getattr(error_obj, 'message', str(e)).strip()
                    result = {
                        'tableName'  : f"{schema_name}.{table_name}",
                        'status'     : 'Error',
                        'cdrType'    : '',
                        'resolution' : '',
                        'message'    : f'ORA-{ora_code}: {ora_message}'
                    }

            elif body.buttonValue == 'alter':
                # ── Alter CDR settings ────────────────────────────────────────
                try:
                    cursor.execute("""
                        BEGIN
                            DBMS_GOLDENGATE_ADM.ALTER_AUTO_CDR(
                                schema_name        => :schema_name,
                                table_name         => :table_name,
                                tombstone_deletes  => TRUE,
                                fetchcols          => TRUE,
                                record_conflicts   => TRUE,
                                use_custom_handlers => 0
                            );
                        END;
                    """, {
                        'schema_name': schema_name,
                        'table_name' : table_name
                    })
                    con.commit()
                    result = {
                        'tableName'  : f"{schema_name}.{table_name}",
                        'status'     : 'Altered',
                        'cdrType'    : 'AUTO',
                        'resolution' : 'ROW',
                        'message'    : 'CDR settings updated successfully'
                    }

                except oracledb.DatabaseError as e:
                    error_obj   = e.args[0]
                    ora_code    = getattr(error_obj, 'code',    0)
                    ora_message = getattr(error_obj, 'message', str(e)).strip()
                    try: con.rollback()
                    except: pass
                    result = {
                        'tableName'  : f"{schema_name}.{table_name}",
                        'status'     : 'Error',
                        'cdrType'    : '',
                        'resolution' : '',
                        'message'    : f'ORA-{ora_code}: {ora_message}'
                    }

            else:
                result = {
                    'tableName'  : f"{schema_name}.{table_name}",
                    'status'     : 'Error',
                    'cdrType'    : '',
                    'resolution' : '',
                    'message'    : f'Unknown action: {body.buttonValue}'
                }


            cursor.close()

            yield f"data: {json.dumps(result)}\n\n"

        try:
            con.close()
        except Exception:
            pass

        yield "data: __DONE__\n\n"

    return StreamingResponse(
        generate(),
        media_type='text/plain',
        headers={
            'Cache-Control'         : 'no-cache',
            'X-Accel-Buffering'     : 'no',
            'Connection'            : 'keep-alive',
            'X-Content-Type-Options': 'nosniff',
        }
    )


class CDRExceptionsRequest(BaseModel):
    dbname:   str
    tables:   List[str]
    cdbCheck: Optional[str] = "NO"
    pdbName:  Optional[str] = ""

@app.post("/api/v2/cdr/exceptions",
    tags=["CDR, exceptions, dba_apply_error_messages, conflicts"],
    summary="Returns full exception detail for CDR conflict rows filtered by the selected table names.",
    description=(
        "Accepts a list of fully-qualified table names (SCHEMA.TABLE),"
        "strips the schema prefix, and queries dba_apply_error_messages"
        "to return all exception records for those tables."
    ))
def get_cdr_exceptions(body: CDRExceptionsRequest):
    conn = None
    try:
        val = selectConn(body.dbname)
        conn = val[0]
        cursor = conn.cursor()
        table_names = []
        for t in body.tables:
            parts = t.split('.')
            table_names.append(parts[-1].upper())   # use last segment
 
        if not table_names:
            return JSONResponse(content=[[]])

        CHUNK = 999

        bind_dict   = {}
        in_clauses  = []

        for chunk_start in range(0, len(table_names), CHUNK):
            chunk = table_names[chunk_start : chunk_start + CHUNK]
            placeholders = ', '.join(
                [':t' + str(chunk_start + i) for i in range(len(chunk))]
            )
            in_clauses.append(f"UPPER(m.OBJECT_NAME) IN ({placeholders})")
            for i, name in enumerate(chunk):
                bind_dict['t' + str(chunk_start + i)] = name
 
        where_clause = '\n               OR '.join(in_clauses)
 
        sql = f"""
            SELECT * FROM dba_apply_error_messages m
            WHERE {where_clause}
        """
 
        cursor.execute(sql, bind_dict)
        columns = [col[0] for col in cursor.description]
        rows    = []
 
        for row in cursor.fetchall():
            row_dict = {}
            for col, val in zip(columns, row):
                # cx_Oracle LOB → string
                if hasattr(val, 'read'):
                    val = val.read()

                if isinstance(val, bytes):
                    val = val.hex().upper()
                row_dict[col] = str(val) if val is not None else ''

            seq = row_dict.get('SEQ', row_dict.get('SEQ#', ''))
            rba = row_dict.get('RBA', '')
            row_dict['SEQ_RBA'] = f"{seq}/{rba}" if seq or rba else ''

            rows.append(row_dict)
  
        summary = {}
        for r in rows:
            tbl = r.get('OBJECT_NAME', 'UNKNOWN')
            if tbl not in summary:
                summary[tbl] = {
                    'table':           tbl,
                    'total_errors':    0,
                    'total_partial':   0,
                    'total_lost':      0,
                    'total_conflicts': 0,
                    'conflict_types':  {}
                }
            summary[tbl]['total_errors'] += 1
 
            state = r.get('APPLIED_STATE', '').strip().upper()
            if state == 'PARTIAL':
                summary[tbl]['total_partial'] += 1
            elif state == 'LOST':
                summary[tbl]['total_lost'] += 1
 
            ctype = r.get('CONFLICT_TYPE', '').strip()
            if ctype:
                summary[tbl]['total_conflicts'] += 1
                summary[tbl]['conflict_types'][ctype] = \
                    summary[tbl]['conflict_types'].get(ctype, 0) + 1
 
        return JSONResponse(content=[rows])
 
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )
    finally:
        if conn:
            conn.close()
 
class TombstoneRequest(BaseModel):
    dbname: str
    schemaList: List[str]
    tabNameList: List[str]      # list of SCHEMA.TABLE
    cdbCheck: str
    pdbName: Optional[str] = ""


@app.post("/api/v2/cdr/tombstone", tags=["MigDB AutoCDR"],
    summary="Get tombstone table details for CDR-enabled tables",
    description=(
        "Accepts a list of fully-qualified table names (SCHEMA.TABLE) and, for each table, "
        "looks up its Auto CDR registration in ALL_GG_AUTO_CDR_TABLES, resolves the associated "
        "tombstone table, verifies it physically exists, and returns its CDR metadata, "
        "column definitions, and up to 200 of the most recent tombstone rows."))
def get_tombstone_details(req: TombstoneRequest):
    conn   = None
    cursor = None
    try:
        val   = selectConn(req.dbname)
        conn = val[0]
        cursor = conn.cursor()

        if not req.tabNameList:
            raise HTTPException(
                status_code=400,
                detail="tabNameList is empty. Please provide at least one SCHEMA.TABLE."
            )

        cursor.execute("""
            SELECT column_name
            FROM   all_tab_columns
            WHERE  table_name = 'ALL_GG_AUTO_CDR_TABLES'
            ORDER BY column_id
        """)
        available_cols = [row[0].upper() for row in cursor.fetchall()]

        if not available_cols:
            raise HTTPException(
                status_code=404,
                detail=(
                    "View ALL_GG_AUTO_CDR_TABLES not found. "
                    "MigDB Auto CDR may not be installed."
                )
            )

        base_cols     = ["TABLE_OWNER", "TABLE_NAME", "TOMBSTONE_TABLE"]
        optional_cols = [
            "RESOLUTION_GRANULARITY",
            "FETCHCOLS",
            "RECORD_CONFLICTS",
            "USE_CUSTOM_HANDLERS",
            "ROW_RESOLUTION_COLUMN",
            "EXISTING_DATA_TIMESTAMP"
        ]
        select_cols = base_cols + [
            c for c in optional_cols if c in available_cols
        ]

        all_results = []

        for full_table in req.tabNameList:
            parts = full_table.strip().upper().split(".")
            if len(parts) != 2:
                all_results.append({
                    "base_table"      : full_table,
                    "exists"          : False,
                    "tombstone_table" : None,
                    "cdr_meta"        : [],
                    "columns"         : [],
                    "rows"            : [],
                    "total_fetched"   : 0,
                    "message"         : "Invalid format. Expected SCHEMA.TABLE, got: " + full_table
                })
                continue

            schema_name, table_name = parts

            try:
                cdr_query = """
                    SELECT {cols}
                    FROM   all_gg_auto_cdr_tables
                    WHERE  table_owner= :schema
                      AND  table_name = :tbl
                """.format(cols=", ".join(select_cols))

                cursor.execute(cdr_query, schema=schema_name, tbl=table_name)
                cdr_rows = cursor.fetchall()

            except Exception as e:
                all_results.append({
                    "base_table"      : full_table,
                    "exists"          : False,
                    "tombstone_table" : None,
                    "cdr_meta"        : [],
                    "columns"         : [],
                    "rows"            : [],
                    "total_fetched"   : 0,
                    "message"         : "Error querying ALL_GG_AUTO_CDR_TABLES: " + str(e)
                })
                continue

            if not cdr_rows:
                all_results.append({
                    "base_table"      : schema_name + "." + table_name,
                    "exists"          : False,
                    "tombstone_table" : None,
                    "cdr_meta"        : [],
                    "columns"         : [],
                    "rows"            : [],
                    "total_fetched"   : 0,
                    "message"         : (
                        "No CDR entry in ALL_GG_AUTO_CDR_TABLES for "
                        + schema_name + "." + table_name
                        + ". CDR may not be enabled."
                    )
                })
                continue

            cdr_meta = []
            for row in cdr_rows:
                row_dict = {}
                for i, col in enumerate(select_cols):
                    val = row[i]
                    if val is None:
                        row_dict[col] = ""
                    elif hasattr(val, 'isoformat'):
                        row_dict[col] = val.isoformat()
                    else:
                        row_dict[col] = str(val)
                cdr_meta.append(row_dict)

            tombstone_table_name = cdr_rows[0][2]   # TOMBSTONE_TABLE column

            if not tombstone_table_name:
                all_results.append({
                    "base_table"      : schema_name + "." + table_name,
                    "exists"          : True,
                    "tombstone_table" : None,
                    "cdr_meta"        : cdr_meta,
                    "columns"         : [],
                    "rows"            : [],
                    "total_fetched"   : 0,
                    "message"         : (
                        "CDR registered but TOMBSTONE_TABLE is NULL for "
                        + schema_name + "." + table_name
                    )
                })
                continue

            tombstone_table_name = tombstone_table_name.upper()

            cursor.execute("""
                SELECT COUNT(*)
                FROM   dba_tables
                WHERE  owner      = :schema
                  AND  table_name = :ts_tbl
            """, schema=schema_name, ts_tbl=tombstone_table_name)

            ts_exists = cursor.fetchone()[0]

            if ts_exists == 0:
                all_results.append({
                    "base_table"      : schema_name + "." + table_name,
                    "exists"          : True,
                    "tombstone_table" : schema_name + "." + tombstone_table_name,
                    "cdr_meta"        : cdr_meta,
                    "columns"         : [],
                    "rows"            : [],
                    "total_fetched"   : 0,
                    "message"         : (
                        "ALL_GG_AUTO_CDR_TABLES references "
                        + schema_name + "." + tombstone_table_name
                        + " but the table does not exist physically."
                    )
                })
                continue

            cursor.execute("""
                SELECT column_name,
                       data_type,
                       data_length,
                       nullable,
                       column_id
                FROM   dba_tab_columns
                WHERE  owner      = :schema
                  AND  table_name = :ts_tbl
                ORDER BY column_id
            """, schema=schema_name, ts_tbl=tombstone_table_name)

            ts_col_rows = cursor.fetchall()
            ts_columns  = [r[0] for r in ts_col_rows]
            ts_col_meta = [
                {
                    "COLUMN_NAME" : r[0],
                    "DATA_TYPE"   : r[1],
                    "DATA_LENGTH" : r[2],
                    "NULLABLE"    : r[3],
                    "COLUMN_ID"   : r[4]
                }
                for r in ts_col_rows
            ]

            if not ts_columns:
                all_results.append({
                    "base_table"      : schema_name + "." + table_name,
                    "exists"          : True,
                    "tombstone_table" : schema_name + "." + tombstone_table_name,
                    "cdr_meta"        : cdr_meta,
                    "column_meta"     : [],
                    "columns"         : [],
                    "rows"            : [],
                    "total_fetched"   : 0,
                    "message"         : "Tombstone table exists but has no columns."
                })
                continue

            full_ts_table = '"{schema}"."{tbl}"'.format(
                schema=schema_name,
                tbl=tombstone_table_name
            )

            try:
                cursor.execute("""
                    SELECT *
                    FROM   {tbl}
                    ORDER BY 1 DESC
                    FETCH FIRST 200 ROWS ONLY
                """.format(tbl=full_ts_table))

                raw_rows = cursor.fetchall()

            except Exception as e:
                all_results.append({
                    "base_table"      : schema_name + "." + table_name,
                    "exists"          : True,
                    "tombstone_table" : schema_name + "." + tombstone_table_name,
                    "cdr_meta"        : cdr_meta,
                    "column_meta"     : ts_col_meta,
                    "columns"         : ts_columns,
                    "rows"            : [],
                    "total_fetched"   : 0,
                    "message"         : "Error selecting from tombstone table: " + str(e)
                })
                continue

            result_rows = []
            for row in raw_rows:
                row_dict = {}
                for i, col in enumerate(ts_columns):
                    val = row[i]
                    if val is None:
                        row_dict[col] = ""
                    elif hasattr(val, 'isoformat'):
                        row_dict[col] = val.isoformat()
                    elif hasattr(val, 'read'):
                        try:
                            row_dict[col] = val.read()
                        except Exception:
                            row_dict[col] = "[CLOB/BLOB]"
                    else:
                        row_dict[col] = str(val)
                result_rows.append(row_dict)

            all_results.append({
                "base_table"      : schema_name + "." + table_name,
                "exists"          : True,
                "tombstone_table" : schema_name + "." + tombstone_table_name,
                "cdr_meta"        : cdr_meta,
                "column_meta"     : ts_col_meta,
                "columns"         : ts_columns,
                "rows"            : result_rows,
                "total_fetched"   : len(result_rows),
                "message"         : "OK"
            })

        return [all_results]

    except HTTPException:
        raise

    except Exception as e:
        error_msg  = str(e)
        error_code = 0
        try:
            error_obj  = e.args[0]
            error_code = getattr(error_obj, 'code',    0)
            error_msg  = getattr(error_obj, 'message', str(e))
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail={
                "oracle_error_code"    : error_code,
                "oracle_error_message" : error_msg
            }
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



SCHEMA_EXCLUSION = (
    "'SYS','SYSTEM','PUBLIC','ORACLE_OCM','DBSNMP','APPQOSSYS','ANONYMOUS','DBSFWUSER',"
    "'SI_INFORMTN_SCHEMA','CTXSYS','AUDSYS','OJVMSYS','REMOTE_SCHEDULER_AGENT',"
    "'GSMADMIN_INTERNAL','ORDPLUGINS','MDSYS','OLAPSYS','LBACSYS','OUTLN','XDB',"
    "'WMSYS','DVF','ORDDATA','DVSYS','ORDSYS','SYSDG','SYSRAC','SYSKM','SYSBACKUP',"
    "'MDDATA','GGSYS','GSMCATUSER','XS$NULL','PDBADMIN','DIP','SYS$UMF'"
)
SCHEMA_LIST_SQL = f"SELECT username FROM all_users WHERE username NOT IN ({SCHEMA_EXCLUSION})"

class MetaDataFileRequest(BaseModel):
    jobName: str
    tabName: str
 
 
class ApplyMetadataRequest(BaseModel):
    dbname: str
    dep_url: str
 
 
class SuppLogRequest(BaseModel):
    dbname: str
 
 
class SuppLogSchemaRequest(BaseModel):
    dbname: str
    pdbName: str
    cdbCheck: str
 
 
class XidDetRequest(BaseModel):
    jobName: str
    alias: str
    cdbCheck: str
    pdbList: str
 
 
class ExpDirsRequest(BaseModel):
    alias: str
    cdbCheck: str
    pdbList: str
 
 
class MakeJobDirRequest(BaseModel):
    jobName: str
    expModeVal: str
    expdpExtOptionsVal: str
    expQueryVal: str
    exp_schema: str
    imp_parallel: str
    tabExistAction: str
    tabExclude: str
    remapSchema: str
    reMapSchemaNameListDisp: list[str]
    remapTgtSchemaNames: str
    remapTableSpaces: str
    reMapTablespaceListDisp: list[str]
    remapTgtTableSpaceNames: str

@app.post("/api/v2/metadata/file", tags=["MigDB Metadata"],
    summary="Download metadata file for a table",
    description="Returns the Oracle metadata file for the given table name and job as a downloadable file response.")
def metadata_file(body: MetaDataFileRequest) -> FileResponse:
    parts = body.tabName.split(".", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=422, detail="tabName must be in 'OWNER.TABLE_NAME' format")
 
    tab_owner, table_name = parts
    file_path = os.path.join(
        agent_home, body.jobName, f"OracleMetaData_{tab_owner}_{table_name}"
    )
 
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Metadata file not found: {file_path}")
 
    return FileResponse(file_path, filename=os.path.basename(file_path))

@app.post("/api/v2/metadata/apply", tags=["MigDB Metadata"],
    summary="Apply metadata to target database",
    description="Fetches the metadata SQL file from the source deployment and executes each statement on the target database, returning the creation status for each table.")
def apply_metadata(body: ApplyMetadataRequest) -> list:
    val = selectConn(body.dbname)
    con = val[0]
    cursor = con.cursor()
    table_create = []
 
    try:
        url = body.dep_url.rstrip("/") + "/api/v2/metadata/file"
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            return [{"TabName": "Source Dep not Reachable", "msg": str(exc)}]
 
        os.makedirs(agent_log, exist_ok=True)
        metadata_path = os.path.join(agent_log, "metadata.sql")
        with open(metadata_path, "wb") as fh:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    fh.write(chunk)
 
        with open(metadata_path, "r") as infile:
            for line in infile:
                try:
                    cursor.execute(line)
                    table_create.append({"TabName": line.split()[2], "msg": "Successfully Created"})
                except oracledb.DatabaseError as exc:
                    table_create.append({"TabName": line.split()[2], "msg": str(exc)})
 
    finally:
        if con:
            cursor.close()
            con.close()
 
    return [table_create]

@app.post("/api/v2/db/supplog", tags=["MigDB Database"],
    summary="Prechecks for MigDB",
    description="Prechecks for MigDB . Retrieves supplemental logging settings, force logging, log mode, and MigDB replication parameter status from the database.")
def supp_log(body: SuppLogRequest) -> list:
    val = selectConn(body.dbname)
    con = val[3]
    db_ver = val[1]
    db_min_ver = val[2]
    cdb_check = "NO"
    result = ""
 
    if "ORA-" in str(db_ver):
        return [db_ver, cdb_check]
 
    try:
        supp_log_sql = """SELECT LOG_MODE, SUPPLEMENTAL_LOG_DATA_MIN, SUPPLEMENTAL_LOG_DATA_PK,
                                 SUPPLEMENTAL_LOG_DATA_UI, SUPPLEMENTAL_LOG_DATA_FK,
                                 SUPPLEMENTAL_LOG_DATA_ALL, DB_UNIQUE_NAME, FORCE_LOGGING
                          FROM v$database"""
 
        if int(db_ver) == 11 and int(db_min_ver) == 4:
            db_param_sql = "SELECT value FROM v$parameter WHERE name='enable_goldengate_replication'"
 
        elif int(db_ver) > 11:
            cdb_df = pd.read_sql_query("SELECT CDB FROM v$database", con)
            cdb_check = cdb_df.to_dict("records")[0]["cdb"]
            db_param_sql = "SELECT value FROM v$parameter WHERE name='enable_goldengate_replication'"
 
        else:
            db_param_sql = "SELECT 'TRUE' value FROM dual"
 
        supp_data = pd.read_sql_query(supp_log_sql, con)
        db_param = pd.read_sql_query(db_param_sql, con)
        result = pd.concat([supp_data, db_param], axis=1).to_dict("records")
 
    except oracledb.DatabaseError as exc:
        result = str(exc)
        logger.info(str(exc))
    finally:
        if con:
            con.close()
 
    return [result, cdb_check]

@app.post("/api/v2/db/supplogschema", tags=["MigDB Database"],
    summary="Get schema supplemental logging details",
    description="Fetches schema-level supplemental logging information from the database, optionally switching to the specified PDB container first.")
def supp_log_schema(body: SuppLogSchemaRequest) -> list:
    val = selectConn(body.dbname)
    con = val[0]
    db_ver = val[1]
    schema_data_fetch = ""
 
    if "ORA-" in str(db_ver):
        return [db_ver]
 
    try:
        if body.cdbCheck == "YES" and body.pdbName:
            cursor = con.cursor()
            cursor.execute(f"ALTER SESSION SET CONTAINER={body.pdbName}")
 
        schema_data_fetch = pd.read_sql_query(SCHEMA_LIST_SQL, con).to_dict("records")
 
    except oracledb.DatabaseError as exc:
        schema_data_fetch = str(exc)
    finally:
        if con:
            con.close()
 
    return [schema_data_fetch]

@app.post("/api/v2/db/xiddet", tags=["MigDB Database"],
    summary="Get transaction XID details",
    description="Fetches active transaction XID details, current system timestamp, and the first SCN time for the capture process associated with the given job.")
def xid_det(body: XidDetRequest) -> list:
    val = selectConn(body.alias)
    con = val[0]
    xid_det_list = []
    curr_time = ""
    first_scn_time = ""
 
    try:
        cursor = con.cursor()
        cursor.outputtypehandler = output_type_handler
 
        cursor.execute(
            "SELECT TO_CHAR(scn_to_timestamp(first_scn),'mm/dd/yyyy hh24:mi:ss') "
            "FROM dba_capture WHERE capture_name LIKE '%%%s%%'" % body.jobName
        )
        first_scn = cursor.fetchone()
 
        if body.cdbCheck == "YES" and body.pdbList:
            cursor.execute(f"ALTER SESSION SET CONTAINER={body.pdbList}")
 
        cursor.execute(
            "SELECT INST_ID, XIDUSN, XIDSLOT, XIDSQN, MIN(START_TIME) start_time "
            "FROM gv$transaction GROUP BY INST_ID, XIDUSN, XIDSLOT, XIDSQN"
        )
        xid_row = cursor.fetchone()
 
        cursor.execute("SELECT TO_CHAR(SYSTIMESTAMP,'mm/dd/yyyy hh24:mi:ss') FROM dual")
        time_row = cursor.fetchone()
 
        if first_scn:
            first_scn_time = first_scn[0]
        if xid_row:
            xid_det_list.append({
                "inst_id": xid_row[0],
                "XIDUSN": xid_row[1],
                "XIDSLOT": xid_row[2],
                "XIDSQN": xid_row[3],
                "start_time": xid_row[4],
            })
        if time_row:
            curr_time = time_row[0]
 
    except oracledb.DatabaseError as exc:
        logger.info(str(exc))
    finally:
        if con:
            cursor.close()
            con.close()
 
    return [xid_det_list, curr_time, first_scn_time]

def _get_mount_info(path: str) -> dict:
    """
    Walks up from `path` to find the actual mount point backing it, and
    returns its filesystem type and source device/export.

    This is the real, OS-level way to tell "is this EFS" — Oracle's
    dba_directories/all_directories only stores the path string, it has
    no idea what's actually mounted there. EFS always shows up as an
    NFSv4 mount (fstype 'nfs4') with a source like
    'fs-0c7a75ff63da4c499.efs.eu-west-1.amazonaws.com:/' — local disk
    (EBS, root volume, etc.) shows fstype like 'xfs' or 'ext4', and a
    source like '/dev/nvme1n1p1'.
    """
    try:
        result = subprocess.run(
            ["findmnt", "-T", path, "-no", "FSTYPE,SOURCE,TARGET"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return {"fstype": None, "source": None, "mount_point": None}

        parts = result.stdout.strip().split(None, 2)
        return {
            "fstype": parts[0] if len(parts) > 0 else None,
            "source": parts[1] if len(parts) > 1 else None,
            "mount_point": parts[2] if len(parts) > 2 else None,
        }

    except Exception as exc:
        logger.warning(f"_get_mount_info failed for {path}: {exc}")
        return {"fstype": None, "source": None, "mount_point": None}


def _is_efs_mount(mount_info: dict) -> bool:
    """
    True only if the underlying mount is genuinely EFS:
      - filesystem type is nfs4 (EFS is always NFSv4), AND
      - the source string matches EFS's naming pattern
        (contains 'efs' or an 'fs-xxxxxxxx' filesystem ID), which rules
        out other NFS servers that aren't EFS.
    """
    if not mount_info or mount_info.get("fstype") != "nfs4":
        return False
    source = (mount_info.get("source") or "").lower()
    return "efs" in source or bool(re.search(r"fs-[0-9a-f]{8,}", source))

@app.post("/api/v2/db/expdirs", tags=["MigDB Database"],
    summary="Get database export directories",
    description="Retrieves all available Oracle directory names from the database, optionally switching to the specified PDB container first.")
def exp_dirs(body: ExpDirsRequest) -> list:
    val = selectConn(body.alias)
    con = val[0]
    dir_name_fetch = []
    efs_dir_names = []
 
    try:
        cursor = con.cursor()
        if body.cdbCheck == "YES" and body.pdbList:
            cursor.execute(f"ALTER SESSION SET CONTAINER={body.pdbList}")
 
        cursor.execute("SELECT directory_name, directory_path  FROM all_directories")
        rows = cursor.fetchall()

        dir_name_fetch = [row[0] for row in rows] if rows else []

        for directory_name, directory_path in rows:
            is_efs = False
            if directory_path:
                if is_efs_path(directory_path):
                    is_efs = True
                elif os.path.isdir(directory_path):
                    mount_info = _get_mount_info(directory_path)
                    is_efs = _is_efs_mount(mount_info)
            if is_efs:
                efs_dir_names.append(directory_name)

        #dir_name_fetch = [row[0] for row in rows] if rows else []
 
    except oracledb.DatabaseError as exc:
        dir_name_fetch = str(exc)
    finally:
        if con:
            cursor.close()
            con.close()
 
    return [dir_name_fetch, efs_dir_names]

@app.post("/api/v2/job/makedir", tags=["MigDB Job Management"],
    summary="Create job directory and config files",
    description="Creates the job working directory and writes configuration files for export mode, schema mapping, tablespace remapping, parallel settings, and table exclusion lists.")
def make_job_dir(body: MakeJobDirRequest) -> dict:
    job_dir = os.path.join(agent_home, body.jobName)
    os.makedirs(job_dir, exist_ok=True)
 
    def _write(filename: str, content: str) -> None:
        with open(os.path.join(job_dir, filename), "w") as fh:
            fh.write(content)
 
    if body.expModeVal == "TABLE":
        _write(f"{body.jobName}_expdpExtOptionsVal", body.expdpExtOptionsVal)
        _write(f"{body.jobName}_IncTables", body.tabExclude)
    elif body.expModeVal == "SCHEMA":
        _write(f"{body.jobName}_expdpExtOptionsVal", "NONE")
 
    _write(f"{body.jobName}_Schemas", body.exp_schema)
    _write(f"{body.jobName}_impParallel", body.imp_parallel)
    _write(f"{body.jobName}_expMode", body.expModeVal)
    _write(f"{body.jobName}_tabExistAction", body.tabExistAction)
 
    if body.remapSchema == "yes":
        src_remap = ",".join(body.reMapSchemaNameListDisp)
        _write(f"{body.jobName}_SRC_Remap_Schemas", src_remap)
        _write(f"{body.jobName}_TGT_Remap_Schemas", body.remapTgtSchemaNames)
 
    if body.remapTableSpaces == "yes":
        src_ts = ",".join(body.reMapTablespaceListDisp)
        _write(f"{body.jobName}_SRC_Remap_Tablespaces", src_ts)
        _write(f"{body.jobName}_TGT_Remap_Tablespaces", body.remapTgtTableSpaceNames)
 
    return {"message": f"Job directory created for '{body.jobName}'", "path": job_dir}
 
class ExpDPRequest(BaseModel):
    srcDep: str
    tgtDep: str
    srcdbName: str
    jobName: str
    schemas: list[str]
    tables: list[str]
    SRCExpModeVal: str
    srcDirName: str
    expParallel: str
    contentOpt: str
    compOpt: str
    compAlgo: str
    tgtdbName: str
    tgtDirName: str
    impParallel: str
    cdbCheck: str
    pdbName: str
    tabExclude: str
    remapSchema: str
    reMapSchemaNameListDisp: list[str]
    remapTgtSchemaNames: str
    remapTableSpaces: str
    reMapTablespaceListDisp: list[str]
    remapTgtTableSpaceNames: str
    tabExistAction: str
    selectExludeObjVal: list[str]
    expdpExtOptionsVal: str
    expQueryVal: str
 
 
class ImpDPRequest(BaseModel):
    jobName: str

def _read_job_file(job_name: str, suffix: str) -> str:
    path = os.path.join(agent_home, job_name, f"{job_name}_{suffix}")
    with open(path) as fh:
        return fh.read()
 
def _build_expdp_cmd(
    exp_schema: str,
    tab_exclude: str,
    exp_mode: str,
    has_exclude_expr: bool,
    has_query: bool,
    use_encryption: bool = False,
    use_compression: bool = False,
    use_parallel: bool = False,
    db_main_ver: int = 19 
) -> str:
    open_mode = "SCHEMA" if exp_mode == "SCHEMA" else "TABLE"
    lines = [
        "DECLARE hdnl number; BEGIN",
        f"hdnl := SYS.DBMS_DATAPUMP.OPEN('EXPORT','{open_mode}',NULL,:jobName);",
        "SYS.DBMS_DATAPUMP.ADD_FILE(handle => hdnl, filename => :dumpfile, directory => :dirName, filetype => sys.dbms_datapump.ku$_file_type_dump_file, reusefile => 1);",
        "SYS.DBMS_DATAPUMP.ADD_FILE(handle => hdnl, filename => :logFile, directory => :dirName, filetype => sys.dbms_datapump.ku$_file_type_log_file);",
        f"SYS.DBMS_DATAPUMP.METADATA_FILTER(hdnl,'SCHEMA_EXPR','IN ({exp_schema})');",
    ]
 
    if exp_mode == "SCHEMA" and tab_exclude:
        lines.append(f"SYS.DBMS_DATAPUMP.METADATA_FILTER(hdnl,'NAME_EXPR','NOT IN({tab_exclude})', object_type => 'TABLE');")
    elif exp_mode == "TABLE" and tab_exclude:
        lines.append(f"SYS.DBMS_DATAPUMP.METADATA_FILTER(hdnl,'NAME_EXPR','IN ({tab_exclude})');")
 
    if has_exclude_expr:
        lines.append("SYS.DBMS_DATAPUMP.METADATA_FILTER(hdnl, 'EXCLUDE_PATH_EXPR', :exclude_expr);")

    lines.append("SYS.DBMS_DATAPUMP.DATA_FILTER(hdnl, 'INCLUDE_ROWS', :content_mode);")

    if use_encryption:
        lines += [
            "SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl,'ENCRYPTION_PASSWORD',:exp_encrypt_passwd);",
            "SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl,'ENCRYPTION_ALGORITHM',:exp_encrypt_algo);",
        ] 
 
    if has_query:
        lines.append("SYS.DBMS_DATAPUMP.DATA_FILTER(hdnl,'SUBQUERY',:expQueryVal);")

    if use_compression and int(db_main_ver)>11:
        lines += [
            "SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl,'COMPRESSION',:compOpt);",
            "SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl,'COMPRESSION_ALGORITHM',:compAlgo);",
        ]
    elif use_compression and int(db_main_ver)==11:
        lines += ["SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl,'COMPRESSION',:compOpt);",]

    if use_parallel:
        lines.append("SYS.DBMS_DATAPUMP.SET_PARALLEL(hdnl,:parallel);",) 

    lines += [
        "SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl,'FLASHBACK_SCN',:flashback_scn);",
        "SYS.DBMS_DATAPUMP.START_JOB(hdnl); END;",
    ]
    
    return "\n".join(lines)
 
 
def _build_impdp_cmd(
    imp_schema: str,
    tab_inc: str,
    imp_mode: str,
    remap_schema_clause: str,
    remap_tablespace_clause: str,
    has_query: bool,
    use_encryption: bool = False,
    use_parallel: bool = False,
) -> str:
    open_mode = "SCHEMA" if imp_mode == "SCHEMA" else "TABLE"

    lines = [
        "DECLARE hdnl number; BEGIN",
        f"hdnl := SYS.DBMS_DATAPUMP.OPEN('IMPORT','{open_mode}',NULL,:jobName);",
        "SYS.DBMS_DATAPUMP.ADD_FILE(handle => hdnl, filename => :dumpfile, directory => :dirName, filetype => sys.dbms_datapump.ku$_file_type_dump_file, reusefile => 1);",
        "SYS.DBMS_DATAPUMP.ADD_FILE(handle => hdnl, filename => :logFile, directory => :dirName, filetype => sys.dbms_datapump.ku$_file_type_log_file);",
        f"SYS.DBMS_DATAPUMP.METADATA_FILTER(hdnl,'SCHEMA_EXPR','IN ({imp_schema})');",
    ]

    if use_encryption:
        lines.append("SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl,'ENCRYPTION_PASSWORD',:exp_encrypt_passwd);")
 
    if imp_mode == "TABLE" and tab_inc:
        lines.append(f"SYS.DBMS_DATAPUMP.METADATA_FILTER(hdnl,'NAME_EXPR','IN ({tab_inc})');")
 
    if has_query:
        lines.append("SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl,'DATA_OPTIONS',SYS.DBMS_DATAPUMP.KU$_DATAOPT_DISABL_APPEND_HINT);")
 
    lines.append("SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl,'TABLE_EXISTS_ACTION',:exists_action);")
 
    if remap_schema_clause:
        lines.append(remap_schema_clause)
    if remap_tablespace_clause:
        lines.append(remap_tablespace_clause)
 
    if use_parallel:
        lines.append("SYS.DBMS_DATAPUMP.SET_PARALLEL(hdnl,:parallel);")

    lines.append("SYS.DBMS_DATAPUMP.START_JOB(hdnl); END;")


    return "\n".join(lines)
 
 
def _build_remap_clause(src_list: list[str], tgt_list: list[str], remap_type: str) -> str:
    clause = ""
    for i, (src, tgt) in enumerate(zip(src_list, tgt_list)):
        clause += f"SYS.DBMS_DATAPUMP.METADATA_REMAP(hdnl,'{remap_type}','{src}','{tgt}');\n"
    return clause.rstrip("\n")


def resolve_dep_url(dep_url: str, dep_priv_url: str | None) -> str:
    """
    Prefer the private URL for intra-VPC/self calls to avoid EC2 hairpin NAT
    limitations (public IP -> self doesn't loop back through the IGW).
    Falls back to the public dep_url if no private URL is configured.
    """
    return dep_priv_url if dep_priv_url else dep_url

@app.post("/api/v2/datapump/export", tags=["MigDB Homogeneous DataPump"],
    summary="Start a DataPump export job",
    description="Creates job directories on source and target deployments, captures the flashback SCN, builds and executes the expdp command, and returns the initial export job status.")

def exp_dp(body: ExpDPRequest) -> list:
    exp_schema = ",".join(f"''{name}''" for name in body.schemas)
    exp_dumpfile = f"{body.jobName}%U.dmp"
    exp_logfile = f"{body.jobName}_Export.log"
    expdp_mon_fetch = []
 
    conn = sqlite3.connect(DB_PATH)
    sq_cursor = conn.cursor()
    try:
        sq_cursor.execute("SELECT dep_url,dep_priv_url FROM onepconn WHERE dep=:srcdep", {"srcdep": body.srcDep})
        src_row = sq_cursor.fetchone()
        sq_cursor.execute("SELECT dep_url,dep_priv_url FROM onepconn WHERE dep=:tgtdep", {"tgtdep": body.tgtDep})
        tgt_row = sq_cursor.fetchone()
    finally:
        sq_cursor.close()
        conn.close()
 
    if not src_row or not tgt_row:
        raise HTTPException(status_code=404, detail="Source or target deployment URL not found")

    src_url = resolve_dep_url(src_row[0], src_row[1])
    tgt_url = resolve_dep_url(tgt_row[0], tgt_row[1])
 
    headers = get_internal_headers() 

    payload = {
        "jobName": body.jobName, "expModeVal": body.SRCExpModeVal,
        "expdpExtOptionsVal": body.expdpExtOptionsVal, "expQueryVal": body.expQueryVal,
        "exp_schema": exp_schema, "imp_parallel": body.impParallel,
        "tabExistAction": body.tabExistAction, "tabExclude": body.tabExclude,
        "remapSchema": body.remapSchema, "reMapSchemaNameListDisp": body.reMapSchemaNameListDisp,
        "remapTgtSchemaNames": body.remapTgtSchemaNames, "remapTableSpaces": body.remapTableSpaces,
        "reMapTablespaceListDisp": body.reMapTablespaceListDisp,
        "remapTgtTableSpaceNames": body.remapTgtTableSpaceNames,
    }

    urls_to_call = list(dict.fromkeys([src_url + "/api/v2/job/makedir",tgt_url  + "/api/v2/job/makedir"]))
 
    for url in urls_to_call:
        try:
            resp = requests.post(url, json=payload, headers=headers, verify=ssl_verify, timeout=ssh_timeout)
            resp.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            logger.error(f"makejobdir failed for {url}: {exc}")
 
    con = None
    try:
        val = selectConn(body.srcdbName)
        con = val[0]
        db_main_ver = val[1]
        cursor = con.cursor()
        exp_job_owner = val[4]
        edition = get_oracle_edition_abbr(con)
 
        ins_payload = {
            "srcdep": body.srcDep, "tgtdep": body.tgtDep,
            "srcdbName": body.srcdbName, "tgtdbName": body.tgtdbName,
            "jobName": body.jobName, "jobOwner": exp_job_owner,
            "srcdumpDir": body.srcDirName, "tgtdumpDir": body.tgtDirName,
            "dumpFile": exp_dumpfile, "cdbCheck": body.cdbCheck,
            "pdbName": body.pdbName, "reMapSchema": body.remapSchema,
            "remapTablespace": body.remapTableSpaces, "src_edition" : edition ,
        }
        urls_to_call = list(dict.fromkeys([src_url + "/api/v2/onep/expimpinsert", tgt_url  + "/api/v2/onep/expimpinsert"]))

        for url in urls_to_call:
            try:
                resp = requests.post(url, json=ins_payload, headers=headers, verify=ssl_verify, timeout=ssh_timeout)
                resp.raise_for_status()
            except requests.exceptions.ConnectionError as exc:
                logger.error(f"expimpinsert failed for {url}: {exc}")
 
        if body.cdbCheck == "YES" and body.pdbName:
            cursor.execute(f"ALTER SESSION SET CONTAINER={body.pdbName}")
 
        cursor.execute("SELECT dbms_flashback.get_system_change_number FROM dual")
        db_row = cursor.fetchone()
        flashback_scn = db_row[0] if db_row else 0
 
        _write_job_file(body.jobName, "flashbackscn", str(flashback_scn))
 
        job_name_ts = f"{body.jobName}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        has_exclude = bool(body.selectExludeObjVal)
        exclude_expr = (
            "IN (" + ",".join(f"'{i}'" for i in body.selectExludeObjVal) + ")"
            if has_exclude else ""
        )
        has_query = body.expdpExtOptionsVal == "QUERY"

        use_encryption = True
        use_compression = True
        use_parallel = True
        if edition == 'SE2':
              use_encryption = False
              use_compression = False
              use_parallel = False

        if body.compOpt=="NONE":
            use_compression = False

        _write_job_file(body.jobName, "UseEncryption", "YES" if use_encryption else "NO")
 
        cmd = _build_expdp_cmd(
            exp_schema=exp_schema,
            tab_exclude=body.tabExclude,
            exp_mode=body.SRCExpModeVal,
            has_exclude_expr=has_exclude,
            has_query=has_query,
            use_encryption=use_encryption,
            use_compression=use_compression,
            use_parallel=use_parallel,
            db_main_ver=db_main_ver
        )

        bind_params = {
            "jobName": job_name_ts, "dirName": body.srcDirName,
            "dumpfile": exp_dumpfile, "logFile": exp_logfile,
            "flashback_scn": flashback_scn,
            "content_mode": body.contentOpt,
        }
 
        """bind_params = {
            "jobName": job_name_ts, "dirName": body.srcDirName,
            "dumpfile": exp_dumpfile, "logFile": exp_logfile,
            "flashback_scn": flashback_scn, "compOpt": body.compOpt,
            "compAlgo": body.compAlgo, "parallel": body.expParallel,
            "content_mode": body.contentOpt,
        }"""

        if use_encryption:
            bind_params["exp_encrypt_passwd"] = exp_encrypt_passwd
            bind_params["exp_encrypt_algo"]   = exp_encrypt_algo

        if use_compression and int(db_main_ver)>11:
            bind_params["compOpt"]   = body.compOpt
            bind_params["compAlgo"] = body.compAlgo 
        elif use_compression and int(db_main_ver)==11:
            bind_params["compOpt"]   = body.compOpt

        if use_parallel:
            bind_params["parallel"]   = body.expParallel

        if has_exclude:
            bind_params["exclude_expr"] = exclude_expr
        if has_query:
            bind_params["expQueryVal"] = body.expQueryVal
 
        cursor.execute(cmd, bind_params)
 
        start_time = datetime.now(timezone.utc).strftime("%Y-%m-%d:%H:%M:%S")
        _write_job_file(body.jobName, "Stats", start_time)
        time.sleep(5)
 
        expdp_mon_fetch.append({
            "STATE": "INPROGRESS", "DEGREE": body.expParallel,
            "DONE": -1, "TIME_REMAINING": "UNKNOWN", "ELA_TIME": 0,
        })
 
    except oracledb.DatabaseError as exc:
        logger.error(str(exc))
        expdp_mon_fetch.append({
            "STATE": "ERROR", "DEGREE": body.expParallel,
            "DONE": -1, "TIME_REMAINING": "UNKNOWN", "ELA_TIME": 0,
        })
    finally:
        if con:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                con.close()
            except Exception:
                pass
        exp_df = pd.DataFrame(expdp_mon_fetch)
        exp_df.to_csv(os.path.join(agent_home, body.jobName, f"{body.jobName}_ExportStarted"))
 
    return [expdp_mon_fetch]

def _dump_files_exist(cursor, directory_name: str, dump_file_pattern: str, max_pieces: int = 99) -> bool:
    """
    Check via DBMS_LOB.FILEEXISTS whether at least one file matching
    dump_file_pattern exists in directory_name. Handles the Data Pump
    '%U' wildcard by checking numbered pieces 01..max_pieces, same way
    Data Pump itself would generate them.
    Returns True if at least one matching file is found.
    """
    if "%U" in dump_file_pattern:
        # Data Pump %U = 2-digit zero-padded increment (01, 02, ... 99, then 3-digit if needed)
        check_block = """
        DECLARE
            l_bfile     BFILE;
            l_found     NUMBER := 0;
        BEGIN
            FOR i IN 1..:max_pieces LOOP
                BEGIN
                    l_bfile := BFILENAME(:dir_name, :base_prefix || LPAD(i, 2, '0') || :suffix);
                    IF DBMS_LOB.FILEEXISTS(l_bfile) = 1 THEN
                        l_found := 1;
                        EXIT;
                    END IF;
                EXCEPTION WHEN OTHERS THEN NULL;
                END;
            END LOOP;
            :result := l_found;
        END;
        """
        prefix, suffix = dump_file_pattern.split("%U", 1)
        result_var = cursor.var(int)
        cursor.execute(
            check_block,
            {
                "max_pieces": max_pieces,
                "dir_name": directory_name,
                "base_prefix": prefix,
                "suffix": suffix,
                "result": result_var,
            },
        )
        found = result_var.getvalue() == 1
    else:
        # Literal filename, no wildcard — single direct check
        check_block = """
        DECLARE
            l_bfile BFILE;
            l_found NUMBER := 0;
        BEGIN
            BEGIN
                l_bfile := BFILENAME(:dir_name, :file_name);
                IF DBMS_LOB.FILEEXISTS(l_bfile) = 1 THEN
                    l_found := 1;
                END IF;
            EXCEPTION WHEN OTHERS THEN NULL;
            END;
            :result := l_found;
        END;
        """
        result_var = cursor.var(int)
        cursor.execute(
            check_block,
            {
                "dir_name": directory_name,
                "file_name": dump_file_pattern,
                "result": result_var,
            },
        )
        found = result_var.getvalue() == 1

    logger.info(
        f"Dump file check for pattern '{dump_file_pattern}' in "
        f"directory '{directory_name}': {'FOUND' if found else 'NOT FOUND'}"
    )
    return found

@app.post("/api/v2/datapump/import", tags=["MigDB Homogeneous DataPump"],
    summary="Start a DataPump import job",
    description="Reads job configuration files, builds the impdp command with schema and tablespace remapping, executes the import on the target database, and returns the job start status.")
def imp_dp(body: ImpDPRequest) -> dict:
    imp_logfile = f"{body.jobName}_Import.log"
 
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT jobOwner, tgtdbName, tgtdumpDir, dumpFile, reMapSchema, remapTablespace ,src_edition "
        "FROM expimp WHERE jobName=:jobName",
        {"jobName": body.jobName},
    )
    db_row = cursor.fetchone()
    cursor.close()
    conn.close()
 
    if not db_row:
        raise HTTPException(status_code=404, detail=f"No expimp record found for job '{body.jobName}'")
 
    job_owner, tgt_db_name, tgt_dir_name, dump_file, remap_schema, remap_tablespace ,src_edition = db_row
    job_owner = job_owner.upper()
 
    imp_mode = _read_job_file(body.jobName, "expMode")
    tab_inc = _read_job_file(body.jobName, "IncTables") if imp_mode == "TABLE" else ""
    imp_schema = _read_job_file(body.jobName, "Schemas")
    imp_parallel = _read_job_file(body.jobName, "impParallel")
    tab_exists_action = _read_job_file(body.jobName, "tabExistAction")
    expdp_ext_options = _read_job_file(body.jobName, "expdpExtOptionsVal")

    if not imp_schema or not imp_schema.strip():
        raise HTTPException(
            status_code=400,
            detail=f"Job '{body.jobName}' has no schema list configured "
                    f"(missing/empty {body.jobName}_Schemas file). Cannot start import."
        )

    is_shared_directory = _read_job_file(body.jobName, "IsSharedDirectory") == "YES"

    remap_schema_clause = ""
    remap_tablespace_clause = ""
 
    if remap_schema == "yes":
        src_schemas = _read_job_file(body.jobName, "SRC_Remap_Schemas").split(",")
        tgt_schemas = _read_job_file(body.jobName, "TGT_Remap_Schemas").split(",")
        remap_schema_clause = _build_remap_clause(src_schemas, tgt_schemas, "REMAP_SCHEMA")
 
    if remap_tablespace == "yes":
        src_ts = _read_job_file(body.jobName, "SRC_Remap_Tablespaces").split(",")
        tgt_ts = _read_job_file(body.jobName, "TGT_Remap_Tablespaces").split(",")
        remap_tablespace_clause = _build_remap_clause(src_ts, tgt_ts, "REMAP_TABLESPACE")
 
    import_flag_path = os.path.join(agent_home, body.jobName, f"{body.jobName}_Import")
    if os.path.exists(import_flag_path):
        return {"message": "Import already started", "jobName": body.jobName}

    con = None

    try:
        val = selectConn(tgt_db_name)
        con = val[0]
        cursor = con.cursor()

        if _dump_files_exist(cursor, tgt_dir_name, dump_file):
            logger.info(
                f"Dump file(s) matching '{dump_file}' already exist in directory "
                f"'{tgt_dir_name}' for job '{body.jobName}' — skipping impdp build/execute."
            )
        #    return {
        #        "message": f"Dump file(s) matching '{dump_file}' already exist in "
        #                   f"directory '{tgt_dir_name}'. Import skipped.",
        #        "jobName": body.jobName
        #    }
 
        dp_job_name = f"{body.jobName}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        has_query = expdp_ext_options == "QUERY"
        tgt_edition = get_oracle_edition_abbr(con)

        #use_encryption = True
        use_encryption = _read_job_file(body.jobName, "UseEncryption") == "YES"
        use_parallel = True

        if src_edition != 'EE' :
            use_encryption = False 
            use_parallel = False
        elif src_edition == 'EE' and tgt_edition != 'EE':
            use_parallel = False

        cmd = _build_impdp_cmd(
                            imp_schema=imp_schema,
                            tab_inc=tab_inc,
                            imp_mode=imp_mode,
                            remap_schema_clause=remap_schema_clause,
                            remap_tablespace_clause=remap_tablespace_clause,
                            has_query=has_query,
                            use_encryption=use_encryption,
                            use_parallel=use_parallel,
                            )
       
        bind_params = {
                        "jobName": body.jobName, "dirName": tgt_dir_name,
                        "dumpfile": dump_file, "logFile": imp_logfile,
                        "exists_action": tab_exists_action,
                        }

        if use_encryption:
            bind_params["exp_encrypt_passwd"] = exp_encrypt_passwd

        if use_parallel:
            bind_params["parallel"]   = imp_parallel
        
        logger.info(f"impdp cmd={cmd!r} bind_params={bind_params!r}")

        cursor.execute(cmd, bind_params)

        start_time = datetime.now(timezone.utc).strftime("%Y-%m-%d:%H:%M:%S")
        _write_job_file(body.jobName, "Import", start_time)
        _write_job_file(body.jobName, "DPJobName", dp_job_name)

    except oracledb.DatabaseError as exc:
            logger.error(str(exc))

            try:
                error_obj, = exc.args
                code = getattr(error_obj, "code", "?")
                message = getattr(error_obj, "message", str(exc))
                offset = getattr(error_obj, "offset", "?")
                logger.error(f"impdp failed — ORA-{code} at offset {offset}: {message}")
            except Exception:
                logger.error(f"impdp failed (raw): {exc}")

            logger.error(f"Full PL/SQL block:\n{cmd}")
            logger.error(f"Bind params: {bind_params}")

            log_path = os.path.join(agent_home, body.jobName, f"{body.jobName}_ImportOnDemand.log")
            with open(log_path, "w") as fh:
                fh.write(str(exc))
            raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if con:
            cursor.close()
            con.close()
 
    return {"message": "Import started", "jobName": body.jobName}

@app.get("/api/v2/datapump/jobs", tags=["MigDB Homogeneous DataPump"],
    summary="List all DataPump jobs",
    description="Returns a list of all DataPump job names recorded in the expimp table.")
def expimp_job() -> list[list[str]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT jobName FROM expimp")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [[row[0] for row in rows] if rows else []]

class ExpdpMonRequest(BaseModel):
    jobName: str
 
 
class TransferToRDSStatsRequest(BaseModel):
    jobName: str
    dumpFile: list[str] = []
 
 
class ImportStatsRequest(BaseModel):
    jobName: str
    tgtdbName: str
 
def _read_job_file(job_name: str, suffix: str) -> str:
    path = os.path.join(agent_home, job_name, f"{job_name}_{suffix}")
    try:
        with open(path) as fh:
            return fh.read()
    except OSError:
        return ""
 
 
def _write_job_file(job_name: str, suffix: str, content: str) -> None:
    os.makedirs(os.path.join(agent_home, job_name), exist_ok=True)
    with open(os.path.join(agent_home, job_name, f"{job_name}_{suffix}"), "w") as fh:
        fh.write(content)
 
 
def _parse_job_completion_line(line: str) -> dict:
    parts = line.split()
    result = {"STATE": "COMPLETED", "WORKERS": 5, "DONE": 100, "TIME_REMAINING": 0, "Elapsed": parts[-1]}
    for i, token in enumerate(parts):
        if token == "at":
            try:
                mon = parts[i + 2]
                day = parts[i + 3]
                time_val = parts[i + 4]
                year = parts[i + 5]
                ela = f"{year}-{mon}-{day} {time_val}"
                end_time = datetime.strptime(ela, "%Y-%b-%d %H:%M:%S").strftime("%Y-%b-%d %H:%M:%S")
                result["endTime"] = end_time
            except (IndexError, ValueError):
                pass
            break
    return result
 
 
def _read_dbms_output_lines(cursor, con, chunk_size: int = 100) -> list[str]:
    collected = []
    chararr = con.gettype("SYS.DBMS_OUTPUT.CHARARR")
    lines_obj = chararr.newobject()
    lines_obj.extend([""] * chunk_size)
    num_lines = cursor.var(int)
 
    while True:
        num_lines.setvalue(0, chunk_size)
        cursor.callproc("dbms_output.get_lines", [lines_obj, num_lines])
        n = int(num_lines.getvalue() or 0)
        if n == 0:
            break
        collected.extend(line for line in lines_obj.aslist()[:n] if line)
 
    return collected

@app.post("/api/v2/datapump/exportmon", tags=["MigDB Homogeneous DataPump"],
    summary="Monitor DataPump export job",
    description="Polls the source database for export job progress, reads export logs, tracks dump file transfer status to target, monitors import progress, and returns full pipeline status.")
def expdp_mon(body: ExpdpMonRequest) -> list:
    job_name = body.jobName
    exp_log_file = f"{job_name}_Export.log"
 
    expdp_mon_fetch = []
    xfr_percent = []
    xfr_to_rds_percent = []
    ready_to_transfer = ""
    ready_to_import = ""
    dump_file = ""
    tab_stats = ""
    impdp_mon_fetch = ""
    flashback_scn = ""
    src_dep_url = ""
    tgt_dep_url = ""
 
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT jobOwner, srcdbName, tgtdbName, srcdumpDir, tgtdumpDir, cdbCheck, pdbName, "
        "reMapSchema, srcdep, tgtdep FROM expimp WHERE jobName=:jobName",
        {"jobName": job_name},
    )
    db_row = cursor.fetchone()
 
    if not db_row:
        logger.info(f"[{job_name}] no expimp record found in sqlite; returning empty status")
        cursor.close()
        conn.close()
        return [expdp_mon_fetch, xfr_percent, dump_file, ready_to_import,
                impdp_mon_fetch, tab_stats, flashback_scn, src_dep_url, tgt_dep_url,
                ready_to_transfer, xfr_to_rds_percent]
 
    job_owner, src_db_name, tgt_db_name, src_dir_name, tgt_dir_name, \
        cdb_check, pdb_name, remap_schema, srcdep, tgtdep = db_row
 
    job_owner = job_owner.upper()
    logger.info(f"[{job_name}] expimp record loaded: jobOwner={job_owner} srcdbName={src_db_name} "
                f"tgtdbName={tgt_db_name} srcDir={src_dir_name} tgtDir={tgt_dir_name} "
                f"cdbCheck={cdb_check} pdbName={pdb_name} remapSchema={remap_schema} "
                f"srcdep={srcdep} tgtdep={tgtdep}")

 
    cursor.execute("SELECT dep_priv_url FROM onepconn WHERE dep=:srcdep", {"srcdep": srcdep})
    src_row = cursor.fetchone()
    src_dep_url = src_row[0] if src_row else ""
    logger.info(f"[{job_name}] resolved src_dep_url={src_dep_url!r}")
 
    cursor.execute("SELECT dep_priv_url FROM onepconn WHERE dep=:tgtdep", {"tgtdep": tgtdep})
    tgt_row = cursor.fetchone()
    tgt_dep_url = tgt_row[0] if tgt_row else ""
    logger.info(f"[{job_name}] resolved tgt_dep_url={tgt_dep_url!r}")
 
    cursor.close()
    conn.close()
 
    val = selectConn(src_db_name)
    con = val[0]
    src_cursor = con.cursor()
    logger.info(f"[{job_name}] connected to source db {src_db_name}")
 
    if "ORA-" in str(val[1]):
        logger.error(f"[{job_name}] source connection error: {val[1]}")
        return [f"{src_db_name} - {val[1]}", xfr_percent, dump_file, ready_to_import,
                impdp_mon_fetch, tab_stats, flashback_scn, src_dep_url, tgt_dep_url,
                ready_to_transfer, xfr_to_rds_percent]
 
    headers = get_internal_headers() 
 
    try:
        flashback_scn = _read_job_file(job_name, "flashbackscn")
        logger.info(f"[{job_name}] flashback_scn={flashback_scn}")
 
        if cdb_check == "YES" and pdb_name:
            logger.info(f"[{job_name}] switching container to PDB {pdb_name}")
            src_cursor.execute(f"ALTER SESSION SET CONTAINER={pdb_name}")

        logger.info(f"[{job_name}] querying dba_datapump_jobs / longops for live progress") 
        src_cursor.execute(
            """SELECT * FROM (
                   SELECT DISTINCT ddj.state, ddj.degree,
                          ROUND((p.sofar/p.totalwork)*100,2) done,
                          p.time_remaining
                   FROM dba_datapump_jobs ddj
                   LEFT JOIN dba_datapump_sessions x ON (x.job_name = ddj.job_name)
                   LEFT JOIN v$session y ON (y.saddr = x.saddr)
                   LEFT JOIN v$sql z ON (y.sql_id = z.sql_id)
                   LEFT JOIN v$session_longops p ON (p.sql_id = y.sql_id)
                   WHERE y.module='Data Pump Worker'
                     AND x.job_name = :jobName
                     AND ddj.job_name = :jobName
                   ORDER BY p.time_remaining DESC)
               WHERE rownum=1 AND time_remaining IS NOT NULL""",
            {"jobName": job_name},
        )
        expdp_mon = src_cursor.fetchall()
        logger.info(f"[{job_name}] live longops query returned {len(expdp_mon)} row(s): {expdp_mon}")
 
        if expdp_mon:
            start_time = _read_job_file(job_name, "Stats")
            end_time = datetime.now(timezone.utc).strftime("%Y-%m-%d:%H:%M:%S")
            fmt = "%Y-%m-%d:%H:%M:%S"
            elap = (datetime.strptime(end_time, fmt) - datetime.strptime(start_time, fmt)).total_seconds()
            expdp_mon_fetch.append({
                "STATE": expdp_mon[0][0], "DEGREE": expdp_mon[0][1],
                "DONE": expdp_mon[0][2], "TIME_REMAINING": expdp_mon[0][3], "ELA_TIME": elap,
            })
            logger.info(f"[{job_name}] in-progress state captured: {expdp_mon_fetch[-1]}")
 
        else:
            end_time_flag = os.path.join(agent_home, job_name, f"{job_name}_Export_EndTime.log")
            logger.info(f"[{job_name}] no live longops row; checking end-time flag {end_time_flag} "
                        f"(exists={os.path.exists(end_time_flag)})")

 
            if not os.path.exists(end_time_flag):
                expdp_mon_fetch.append({"STATE": "IN PROGRESS", "WORKERS": 5, "DONE": -1,
                                        "TIME_REMAINING": 0, "Elapsed": 0})
                logger.info(f"[{job_name}] marking as IN PROGRESS; reading export log via UTL_FILE")
 
                read_log_sql = f"""DECLARE
                    fp UTL_FILE.FILE_TYPE;
                    z VARCHAR2(4000);
                    BEGIN
                    fp := UTL_FILE.FOPEN(:dirName, '{exp_log_file}', 'r');
                    LOOP
                    UTL_FILE.GET_LINE(fp, z);
                    dbms_output.put_line(z);
                    END LOOP;
                    EXCEPTION WHEN NO_DATA_FOUND THEN UTL_FILE.FCLOSE(fp);
                    END;"""
 
                src_cursor.callproc("dbms_output.enable", [None])
                src_cursor.execute(read_log_sql, {"dirName": src_dir_name})
 
                chunk_size = 100
                lines_var = src_cursor.arrayvar(str, chunk_size)
                num_lines = src_cursor.var(int)
                num_lines.setvalue(0, chunk_size)
               
                total_lines_written=0
 
                export_log_path = os.path.join(agent_home, job_name, f"{job_name}_Export.log")
                with open(export_log_path, "w") as log_fh:
                    while num_lines.getvalue() == chunk_size:
                        src_cursor.callproc("dbms_output.get_lines", [lines_var, num_lines])
                        count = num_lines.getvalue()
                        for i in range(count):
                            line = lines_var.getvalue()[i]
                            if not line:
                                continue
                            log_fh.write(line + "\n")
                            if line.startswith("Job"):
                                completion = _parse_job_completion_line(line)
                                expdp_mon_fetch.append(completion)
                                logger.info(f"[{job_name}] parsed job completion line: {completion}")
                                if "endTime" in completion and not os.path.exists(end_time_flag):
                                    _write_job_file(job_name, "Export_EndTime.log".replace(f"{job_name}_", ""),
                                                    completion["endTime"] + "\n")
                                    logger.info(f"[{job_name}] wrote end-time flag: {completion['endTime']}")
                logger.info(f"[{job_name}] finished streaming export log, {total_lines_written} line(s) written to {export_log_path}")
 
            else:
                export_log_path = os.path.join(agent_home, job_name, f"{job_name}_Export.log")
                logger.info(f"[{job_name}] end-time flag already exists; reading cached export log {export_log_path}")

                if os.path.exists(export_log_path):
                    with open(export_log_path) as fh:
                        for line in fh:
                            if line.startswith("Job"):
                                completion = _parse_job_completion_line(line)
                                expdp_mon_fetch.append(completion)
                                logger.info(f"[{job_name}] parsed cached job completion line: {completion}")
        logger.info(f"expdp_mon_fetch {expdp_mon_fetch}") 
        if expdp_mon_fetch and expdp_mon_fetch[0].get("STATE") == "COMPLETED":
            logger.info(f"[{job_name}] export STATE=COMPLETED; scanning export log for dump file names")
            dump_file = []
            export_log_path = os.path.join(agent_home, job_name, f"{job_name}_Export.log")
            if os.path.exists(export_log_path):
                with open(export_log_path) as fh:
                    for line in fh:
                        if ".dmp" in line.lower():
                            candidate = line.replace("\\", "/").split("/")[-1].strip()
                            if candidate:
                                dump_file.append(candidate)
            logger.info(f"[{job_name}] dump_file list discovered: {dump_file}")
 
            for file_name in dump_file:
                speed_path = os.path.join(agent_home, job_name, f"{file_name}_speed")
                if os.path.exists(speed_path):
                    with open(speed_path) as fh:
                        xfr_stats = fh.read().split("$")
                    if xfr_stats[0]:
                        xfr_percent.append({
                            "fileName": file_name, "Percent": xfr_stats[0],
                            "elapTime": xfr_stats[1] if len(xfr_stats) > 1 else "",
                            "XFRSpeed": xfr_stats[2] if len(xfr_stats) > 2 else "",
                            "TotalBytes": xfr_stats[3] if len(xfr_stats) > 3 else "",
                            "XFRBytes": xfr_stats[4] if len(xfr_stats) > 4 else "",
                            "XFReta": xfr_stats[5] if len(xfr_stats) > 5 else "",
                        })
                else:
                    logger.info(f"[{job_name}] no speed file yet for {file_name} at {speed_path}")
            logger.info(f"[{job_name}] xfr_percent {xfr_percent}")

            fully_transferred = [x["fileName"] for x in xfr_percent if int(float(x["Percent"])) == 100]
            logger.info(f"fully_transferred {fully_transferred}")
 
            if dump_file and len(fully_transferred) == len(dump_file):
                ready_to_transfer = "YES"
                logger.info(f"ready_to_transfer {ready_to_transfer}")
                tgt_xfr_url = f"{tgt_dep_url}/api/v2/datapump/transferrdsstats"
                logger.info(f"[{job_name}] posting to {tgt_xfr_url} for EFS transfer stats")
                result = _safe_post(tgt_xfr_url, {"jobName": job_name, "dumpFile": dump_file}, headers)
                logger.info(f"[{job_name}] transferrdsstats result: {result}")
                if result:
                    xfr_to_rds_percent = result
                    ready_to_import_list = [x["fileName"] for x in result if int(float(x.get("Percent", 0))) == 100]
                    logger.info(f"ready_to_import_list {ready_to_import_list}")
                    logger.info(f"length of dumpfile {len(dump_file)}")
 
                    if len(ready_to_import_list) == len(dump_file):
                        ready_to_import = "YES"
                        logger.info(f"ready_to_import {ready_to_import}")
                        tgt_imp_stat_url = f"{tgt_dep_url}/api/v2/datapump/importstats"
                        logger.info(f"[{job_name}] posting to {tgt_imp_stat_url} for import stats")
                        imp_result = _safe_post(tgt_imp_stat_url, {"tgtdbName": tgt_db_name, "jobName": job_name}, headers)
                        logger.info(f"[{job_name}] importstats result: {imp_result}")
                        if imp_result:
                            impdp_mon_fetch = imp_result
                        if isinstance(impdp_mon_fetch, dict) and impdp_mon_fetch.get("STATE") == "COMPLETED":
                            logger.info(f"[{job_name}] import STATE=COMPLETED; fetching table stats")
                            tab_stats_exp = _safe_post(
                                f"{src_dep_url}/api/v2/datapump/tablestatsexp", {"jobName": job_name}, headers
                            ) or {}
                            logger.info(f"[{job_name}] tablestatsexp result: {tab_stats_exp}")
                            tab_stats = _safe_post(
                                f"{tgt_dep_url}/api/v2/datapump/tablestatsimp",
                                {"jobName": job_name, "tabStatsExp": tab_stats_exp, "reMapSchema": remap_schema},
                                headers,
                            ) or ""
                            logger.info(f"[{job_name}] tablestatsimp result: {tab_stats}")
    except (oracledb.DatabaseError, AttributeError, Exception) as exc:
        _write_job_file(job_name, "ExportOnDemand.log", str(exc))
        logger.error(f"[{job_name}] exportmon failed: {exc}")
    finally:
        if con:
            src_cursor.close()
            con.close()
            logger.info(f"[{job_name}] source connection closed")
 
    return [expdp_mon_fetch, xfr_percent, dump_file, ready_to_import,
            impdp_mon_fetch, tab_stats, flashback_scn, src_dep_url, tgt_dep_url,
            ready_to_transfer, xfr_to_rds_percent]

@app.post("/api/v2/datapump/transferrdsstats", tags=["MigDB Homogeneous DataPump"],
    summary="Get RDS transfer statistics",
    description="Reads per-dump-file transfer speed files from the job directory and returns transfer progress including percent complete, speed, bytes transferred, and ETA.")
def transfer_to_rds_stats(body: TransferToRDSStatsRequest) -> list:

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT srcdbName, srcdumpDir, tgtdbName, tgtdumpDir FROM expimp WHERE jobName=:jobName",
        {"jobName": body.jobName},
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        src_db_name, src_dir_name, tgt_db_name, tgt_dump_dir = row
        src_dir_path = get_directory_path(src_db_name, src_dir_name)
        tgt_dir_path = get_directory_path(tgt_db_name, tgt_dump_dir)

        def _normalize(path):
            return os.path.normpath(path.strip()).rstrip("/").lower() if path else ""

        if src_dir_path and tgt_dir_path and _normalize(src_dir_path) == _normalize(tgt_dir_path):
            return [
                {
                    "fileName": f,
                    "Percent": "100",
                    "elapTime": "0",
                    "XFRSpeed": "INSTANT",
                    "TotalBytes": "0",
                    "XFRBytes": "0",
                    "XFReta": "0",
                }
                for f in body.dumpFile
            ]

    job_dir = Path(agent_home) / body.jobName
    xfr_to_rds_percent = []
 
    for p in sorted(job_dir.glob("*_speed")):
        try:
            raw = p.read_text(encoding="utf-8").strip()
            if not raw:
                continue
            parts = raw.split("$")
            parts += [""] * (7 - len(parts))
            fname = p.name[:-6] if p.name.endswith("_speed") else p.name
            xfr_to_rds_percent.append({
                "fileName": fname,
                "Percent": parts[0],
                "elapTime": parts[1],
                "XFRSpeed": parts[2],
                "TotalBytes": parts[3],
                "XFRBytes": parts[4],
                "XFReta": parts[5],
                "XFRTgtBytes": parts[6],
            })
        except Exception as exc:
            logger.warning(f"Could not read {p}: {exc}")
 
    return xfr_to_rds_percent

@app.post("/api/v2/datapump/importstats", tags=["MigDB Homogeneous DataPump"],
    summary="Get DataPump import job statistics",
    description="Queries the target database for active import job status, reads the import log file via DBMS_OUTPUT, and returns the current import state including completion status and elapsed time.")
def import_stats(body: ImportStatsRequest) -> dict:
    job_name = body.jobName
    imp_log_file = f"{job_name}_Import.log"
    impdp_mon_fetch: dict | str = ""
 
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT tgtdumpDir, reMapSchema FROM expimp WHERE jobName=:jobName",
        {"jobName": job_name},
    )
    db_row = cursor.fetchone()
    cursor.close()
    conn.close()
 
    if not db_row:
        raise HTTPException(status_code=404, detail=f"No expimp record for job '{job_name}'")
 
    tgt_dir_name, remap_schema = db_row
    tgt_con = None
 
    try:
        tgt_val = selectConn(body.tgtdbName)
        tgt_con = tgt_val[0]
        alchemy_con = tgt_val[3]
        tgt_cursor = tgt_con.cursor()
 
        impdp_df = pd.read_sql_query(
            "SELECT dp.state, dp.workers, -1 DONE, 0 TIME_REMAINING "
            "FROM gv$datapump_job dp WHERE dp.job_name=:jobName",
            alchemy_con,
            params={"jobName": job_name},
        )
        records = impdp_df.to_dict("records")
 
        if records:
            impdp_mon_fetch = {"STATE": "IN PROGRESS", "WORKERS": 5, "DONE": -1,
                               "TIME_REMAINING": 0, "Elapsed": 0}
 
        else:
            end_time_flag = os.path.join(agent_home, job_name, f"{job_name}_Import_EndTime.log")
 
            if not os.path.exists(end_time_flag):
                impdp_mon_fetch = {"STATE": "IN PROGRESS", "WORKERS": 5, "DONE": -1,
                                   "TIME_REMAINING": 0, "Elapsed": 0}
 
                read_log_sql = f"""DECLARE
                    l_bfile      BFILE;
                    l_last       PLS_INTEGER := 1;
                    l_current    PLS_INTEGER;
                    l_raw_line   RAW(32767);
                    l_line_text  VARCHAR2(32767);
                    l_line_count PLS_INTEGER := 0;
                    BEGIN
                    l_bfile := BFILENAME(:dirName, '{imp_log_file}');
                    DBMS_LOB.FILEOPEN(l_bfile, DBMS_LOB.FILE_READONLY);
                    LOOP
                        l_current := DBMS_LOB.INSTR(l_bfile, HEXTORAW('0A'), l_last, 1);
                        EXIT WHEN NVL(l_current, 0) = 0;
                        IF l_current > l_last THEN
                            l_raw_line  := DBMS_LOB.SUBSTR(l_bfile, l_current - l_last, l_last);
                            l_line_text := UTL_RAW.CAST_TO_VARCHAR2(l_raw_line);
                            DBMS_OUTPUT.PUT_LINE(l_line_text);
                        ELSE
                            DBMS_OUTPUT.PUT_LINE('');
                        END IF;
                        l_last := l_current + 1;
                        l_line_count := l_line_count + 1;
                        EXIT WHEN l_line_count > 100000;
                    END LOOP;
                    IF DBMS_LOB.FILEISOPEN(l_bfile) = 1 THEN DBMS_LOB.FILECLOSE(l_bfile); END IF;
                    EXCEPTION WHEN OTHERS THEN
                        IF DBMS_LOB.FILEISOPEN(l_bfile) = 1 THEN DBMS_LOB.FILECLOSE(l_bfile); END IF;
                        DBMS_OUTPUT.PUT_LINE('Error: ' || SQLERRM);
                    END;"""
 
                tgt_cursor.callproc("dbms_output.enable", [None])
                tgt_cursor.execute(read_log_sql, {"dirName": tgt_dir_name})
 
                output_lines = _read_dbms_output_lines(tgt_cursor, tgt_con)
 
                imp_log_path = os.path.join(agent_home, job_name, f"{job_name}_Import.log")
                with open(imp_log_path, "w") as fh:
                    for line in output_lines:
                        fh.write(line + "\n")
                        if line.startswith("Job"):
                            completion = _parse_job_completion_line(line)
                            impdp_mon_fetch = {
                                "STATE": "COMPLETED", "WORKERS": 5, "DONE": 100,
                                "TIME_REMAINING": 0, "Elapsed": completion.get("Elapsed", ""),
                            }
                            if "endTime" in completion and not os.path.exists(end_time_flag):
                                with open(end_time_flag, "w") as ef:
                                    ef.write(completion["endTime"])
 
            else:
                imp_log_path = os.path.join(agent_home, job_name, f"{job_name}_Import.log")
                if os.path.exists(imp_log_path):
                    with open(imp_log_path) as fh:
                        for line in fh:
                            if line.startswith("Job"):
                                parts = line.split()
                                impdp_mon_fetch = {"STATE": "COMPLETED", "WORKERS": 5,
                                                   "DONE": 100, "TIME_REMAINING": 0,
                                                   "Elapsed": parts[-1]}
 
    except (oracledb.DatabaseError, Exception) as exc:
        _write_job_file(job_name, "ImportOnDemand.log", str(exc))
        logger.info(str(exc))
        impdp_mon_fetch = {"STATE": "ERROR", "msg": str(exc)}
    finally:
        if tgt_con:
            tgt_cursor.close()
            tgt_con.close()
 
    return impdp_mon_fetch

class JobNameRequest(BaseModel):
    jobName: str
 
 
class TableStatsImpRequest(BaseModel):
    jobName: str
    tabStatsExp: dict
    reMapSchema: str
 
 
class UpdateS3ConfigRequest(BaseModel):
    jobName: str
    bucketName: str
    aws_access_key_id: str
    aws_secret_access_key: str

def _job_path(job_name: str, suffix: str) -> str:
    return os.path.join(agent_home, job_name, f"{job_name}_{suffix}")
 
 
def _read_job_file(job_name: str, suffix: str) -> str:
    try:
        with open(_job_path(job_name, suffix)) as fh:
            return fh.read()
    except OSError:
        return ""
 
 
def _fetch_expimp_row(job_name: str, columns: str) -> Optional[tuple]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT {columns} FROM expimp WHERE jobName=:jobName", {"jobName": job_name})
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row
 
 
def _read_speed_file(job_name: str, file_name: str) -> Optional[dict]:
    speed_path = _job_path(job_name, f"{file_name}_speed".replace(f"{job_name}_", ""))
    speed_path = os.path.join(agent_home, job_name, f"{file_name}_speed")
    if not os.path.exists(speed_path):
        return None
    try:
        parts = open(speed_path).read().strip().split("$")
        parts += [""] * (7 - len(parts))
        return {
            "fileName": file_name, "Percent": parts[0], "elapTime": parts[1],
            "XFRSpeed": parts[2], "TotalBytes": parts[3], "XFRBytes": parts[4], "XFReta": parts[5],
        }
    except OSError:
        return None
 
 
def _parse_export_log_dumpfiles(job_name: str) -> list[str]:
    log_path = _job_path(job_name, "Export.log")
    dump_files = []
    if not os.path.exists(log_path):
        return dump_files
    with open(log_path) as fh:
        for line in fh:
            stripped = line.strip()
            if ".dmp" in stripped.lower():
                candidate = stripped.replace("\\", "/").split("/")[-1].strip()
                if candidate:
                    dump_files.append(candidate)
    return dump_files
 
 
def _read_dbms_output(cursor, con, chunk_size: int = 100) -> list[str]:
    collected = []
    chararr = con.gettype("SYS.DBMS_OUTPUT.CHARARR")
    lines_obj = chararr.newobject()
    lines_obj.extend([""] * chunk_size)
    num_lines = cursor.var(int)
    while True:
        num_lines.setvalue(0, chunk_size)
        cursor.callproc("dbms_output.get_lines", [lines_obj, num_lines])
        n = int(num_lines.getvalue() or 0)
        if n == 0:
            break
        collected.extend(line for line in lines_obj.aslist()[:n] if line)
    return collected

@app.post("/api/v2/datapump/tablestatsexp", tags=["MigDB Homogeneous DataPump"],
    summary="Get export table statistics",
    description="Reads the export log file and returns per-table exported row counts for the given job.")
def table_stats_exp(body: JobNameRequest) -> dict:
    tab_stats: dict = {}
    log_path = _job_path(body.jobName, "Export.log")
    if not os.path.exists(log_path):
        return tab_stats
    with open(log_path) as fh:
        for line in fh:
            if line.startswith("."):
                parts = line.split()
                try:
                    idx = parts.index("exported")
                    tab_name = parts[idx + 1]
                    tab_rows = parts[idx + 4]
                    tab_stats[tab_name] = {"ExportRows": tab_rows}
                except (ValueError, IndexError):
                    continue
    return tab_stats

@app.post("/api/v2/datapump/tablestatsimp", tags=["MigDB Homogeneous DataPump"],
    summary="Get import table statistics",
    description="Merges export and import row counts per table from log files, applies schema remapping if configured, and saves the result to a CSV summary file.")
def table_stats_imp(body: TableStatsImpRequest) -> dict:
    tab_stats = dict(body.tabStatsExp)
    log_path = _job_path(body.jobName, "Import.log")
    src_remap, tgt_remap = [], []
    if body.reMapSchema == "yes":
        src_remap = _read_job_file(body.jobName, "SRC_Remap_Schemas").split(",")
        tgt_remap = _read_job_file(body.jobName, "TGT_Remap_Schemas").split(",")

    matched = 0
    skipped_parse = 0
    skipped_no_key = 0

    if os.path.exists(log_path):
        with open(log_path) as fh:
            for raw_line in fh:
                # FIX: strip leading/trailing whitespace before checking the
                # prefix — log lines are often indented, which previously
                # caused startswith(".") to fail silently and skip every row.
                line = raw_line.strip()
                if not line.startswith("."):
                    continue

                parts = line.split()
                try:
                    idx = parts.index("imported")
                    tab_name = parts[idx + 1]
                    tab_rows = parts[idx + 4]
                except (ValueError, IndexError):
                    # FIX: count and log unparseable lines instead of
                    # silently dropping them, so parsing gaps are visible.
                    skipped_parse += 1
                    logger.debug(f"[{body.jobName}] tablestatsimp: could not parse line: {line!r}")
                    continue

                if body.reMapSchema == "yes":
                    tab_owner = tab_name.split(".")[0].strip('"')
                    tgt_tab = tab_name.split(".")[1] if "." in tab_name else tab_name
                    for i, (src, tgt) in enumerate(zip(src_remap, tgt_remap)):
                        if tgt.strip() == tab_owner:
                            tab_name = f'"{src.strip()}".{tgt_tab}'
                            break

                if tab_name in tab_stats:
                    tab_stats[tab_name]["ImportRows"] = tab_rows
                    matched += 1
                else:
                    # FIX: count and log rows that parsed fine but didn't
                    # match any key already present in tab_stats (e.g. from
                    # a remap mismatch or quoting/casing difference), so
                    # these don't disappear without a trace either.
                    skipped_no_key += 1
                    logger.debug(f"[{body.jobName}] tablestatsimp: parsed {tab_name}={tab_rows} "
                                 f"rows but no matching key in tab_stats")

        logger.info(f"[{body.jobName}] tablestatsimp: matched={matched} "
                    f"skipped_parse={skipped_parse} skipped_no_key={skipped_no_key}")
    else:
        logger.warning(f"[{body.jobName}] tablestatsimp: log file not found at {log_path}")

    stats_csv = _job_path(body.jobName, "Table_Stats.csv")
    if not os.path.exists(stats_csv):
        pd.DataFrame.from_dict(tab_stats).to_csv(stats_csv, index=False, header=True)

    return tab_stats

@app.post("/api/v2/datapump/expdpstatus", tags=["MigDB Homogeneous DataPump"],
    summary="Get detailed DataPump export status",
    description="Queries the source database for active DataPump session details including progress percentage, time remaining, and current table being processed.")
def expdp_status(body: JobNameRequest) -> list:
    row = _fetch_expimp_row(body.jobName, "jobOwner, srcdbName, cdbCheck, pdbName")
    if not row:
        raise HTTPException(status_code=404, detail=f"No expimp record for job '{body.jobName}'")
 
    job_owner = row[0].upper()
    src_db_name, cdb_check, pdb_name = row[1], row[2], row[3]
 
    con_src = selectConn(src_db_name)[0]
    expdp_status_result = {}
 
    try:
        if cdb_check == "YES" and pdb_name:
            with con_src.cursor() as cur:
                cur.execute(f"ALTER SESSION SET CONTAINER={pdb_name}")
 
        sql = r"""SELECT ds.owner_name, ds.job_name,
                         s.inst_id, s.sid, s.serial# AS serial, s.module, s.action,
                         l.opname, l.sofar, l.totalwork, l.message,
                         ROUND(l.sofar / NULLIF(l.totalwork, 0) * 100, 2) AS pct_done,
                         l.time_remaining, l.units,
                         REGEXP_SUBSTR(l.message,'Rowid Range Scan:\s*([[:alnum:]_$#]+\.[[:alnum:]_$#]+)',1,1,NULL,1) AS current_table
                  FROM   dba_datapump_sessions ds
                  JOIN   gv$session s ON s.saddr = ds.saddr AND s.inst_id = ds.inst_id
                  LEFT JOIN gv$session_longops l
                         ON l.sid = s.sid AND l.serial# = s.serial# AND l.inst_id = s.inst_id
                  WHERE  UPPER(ds.owner_name) = :jobowner
                    AND  UPPER(ds.job_name) LIKE UPPER(:jobname) || '%'
                    AND  s.module LIKE 'Data Pump%%'
                    AND  (l.totalwork IS NULL OR l.totalwork = 0 OR l.sofar < l.totalwork)
                  ORDER BY s.inst_id, s.sid"""
 
        df = fetch_query_params(sql, con_src, cast_str=True, params={"jobowner": job_owner, "jobname": body.jobName})
        expdp_status_result = df.to_dict(orient="records")
 
    except Exception as exc:
        logger.info(str(exc))
    finally:
        if con_src:
            con_src.close()
 
    return [expdp_status_result]

@app.post("/api/v2/datapump/readexportlog", tags=["MigDB Homogeneous DataPump"],
    summary="Read export log from database",
    description="Reads the DataPump export log file from the source Oracle directory via UTL_FILE and returns the log lines.")
def read_export_log(body: JobNameRequest) -> list[list[str]]:
    row = _fetch_expimp_row(body.jobName, "jobOwner, srcdbName, srcdumpDir, cdbCheck, pdbName")
    if not row:
        return [[]]
 
    job_owner, src_db_name, src_dir_name, cdb_check, pdb_name = row
    exp_log_file = f"{body.jobName}_Export.log"
    export_log: list[str] = []
    con = None
 
    try:
        val = selectConn(src_db_name)
        con = val[0]
        cursor = con.cursor()
 
        if cdb_check == "YES" and pdb_name:
            cursor.execute(f"ALTER SESSION SET CONTAINER={pdb_name}")
 
        read_log_sql = f"""DECLARE
            fp UTL_FILE.FILE_TYPE;
            z  VARCHAR2(4000);
            BEGIN
            fp := UTL_FILE.FOPEN(:dirName, '{exp_log_file}', 'r');
            LOOP UTL_FILE.GET_LINE(fp, z); dbms_output.put_line(z); END LOOP;
            EXCEPTION WHEN NO_DATA_FOUND THEN UTL_FILE.FCLOSE(fp);
            END;"""
 
        cursor.callproc("dbms_output.enable", [None])
        cursor.execute(read_log_sql, {"dirName": src_dir_name})
 
        chunk_size = 100
        lines_var = cursor.arrayvar(str, chunk_size)
        num_lines = cursor.var(int)
        num_lines.setvalue(0, chunk_size)
 
        on_demand_path = _job_path(body.jobName, "ExportOnDemand.log")
        os.makedirs(os.path.dirname(on_demand_path), exist_ok=True)
        with open(on_demand_path, "w") as fh:
            while num_lines.getvalue() == chunk_size:
                cursor.callproc("dbms_output.get_lines", [lines_var, num_lines])
                for i in range(num_lines.getvalue()):
                    line = lines_var.getvalue()[i]
                    if line:
                        fh.write(line + "\n")
                        export_log.append(line)
 
    except (oracledb.DatabaseError, AttributeError) as exc:
        _write_job_file(body.jobName, "ExportOnDemand.log", str(exc))
        logger.info(str(exc))
    finally:
        if con:
            cursor.close()
            con.close()
 
    return [export_log]

@app.post("/api/v2/datapump/s3transferlog", tags=["MigDB Homogeneous DataPump"],
    summary="Get S3 transfer log statistics",
    description="Reads per-dump-file speed logs from the job directory and returns S3 transfer progress including percent complete, speed, bytes, and ETA.")
def s3_transfer_log(body: JobNameRequest) -> list[list[dict]]:
    if not re.match(r"^[\w\-]+$", body.jobName):
        raise HTTPException(status_code=400, detail="Invalid jobName format")
 
    log_path = _job_path(body.jobName, "Export.log")
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail=f"Export log not found for job: {body.jobName}")
 
    dump_files: list[str] = []
    try:
        with open(log_path) as fh:
            for line in fh:
                stripped = line.strip()
                if stripped.lower().endswith(".dmp"):
                    candidate = stripped.replace("\\", "/").split("/")[-1].strip()
                    if candidate:
                        dump_files.append(candidate)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read export log: {exc}")
 
    xfr_percent: list[dict] = []
    for file_name in dump_files:
        speed_path = os.path.join(agent_home, body.jobName, f"{file_name}_speed")
        if not os.path.exists(speed_path):
            xfr_percent.append({
                "fileName": file_name, "Percent": "0", "elapTime": "0",
                "XFRSpeed": "N/A", "TotalBytes": "0", "XFRBytes": "0", "XFReta": "0",
            })
            continue
        try:
            parts = open(speed_path).read().strip().split("$")
        except OSError as exc:
            logger.error(f"{file_name}: failed to read speed log — {exc}")
            continue
        if len(parts) < 6 or not parts[0]:
            logger.warning(f"{file_name}: speed log incomplete")
            continue
        xfr_percent.append({
            "fileName": file_name, "Percent": parts[0], "elapTime": parts[1],
            "XFRSpeed": parts[2], "TotalBytes": parts[3], "XFRBytes": parts[4], "XFReta": parts[5],
        })
 
    return [xfr_percent]

@app.post("/api/v2/datapump/transferlogtords", tags=["MigDB Homogeneous DataPump"],
    summary="Get transfer-to-RDS log statistics",
    description="Reads all speed log files from the job directory and returns transfer progress details including bytes transferred, speed, ETA, and target bytes for each dump file.")
def transfer_log_to_rds(body: JobNameRequest) -> list[list[dict]]:
    job_dir = os.path.join(agent_home, body.jobName)
    xfr_percent: list[dict] = []
 
    for spath in glob.glob(os.path.join(job_dir, "*_speed")):
        base = os.path.basename(spath)
        file_name = base[:-len("_speed")] if base.endswith("_speed") else base
        try:
            raw = open(spath).read().strip()
        except FileNotFoundError:
            continue
        if not raw:
            continue
        parts = raw.split("$")
        while len(parts) < 7:
            parts.append("")
        entry = {
            "fileName": file_name, "Percent": parts[0], "elapTime": parts[1],
            "XFRSpeed": parts[2], "TotalBytes": parts[3], "XFRBytes": parts[4],
            "XFReta": parts[5], "XFRTgtBytes": parts[6],
        }
        if len(parts) >= 8:
            entry["XFRUnit"] = parts[7]
        xfr_percent.append(entry)
 
    return [xfr_percent]

@app.post("/api/v2/datapump/readimportlog", tags=["MigDB Homogeneous DataPump"],
    summary="Read import log from database",
    description="Reads the DataPump import log file from the target Oracle directory via DBMS_LOB and returns the log lines.")
def read_import_log(body: JobNameRequest) -> list[list[str]]:
    row = _fetch_expimp_row(body.jobName, "jobOwner, tgtdbName, tgtdumpDir")
    if not row:
        return [[]]
 
    job_owner, tgt_db_name, tgt_dir_name = row
    imp_log_file = f"{body.jobName}_Import.log"
    on_demand_path = _job_path(body.jobName, "ImportOnDemand.log")
    import_log: list[str] = []
    tgt_con = None
 
    try:
        val = selectConn(tgt_db_name)
        tgt_con = val[0]
        tgt_cursor = tgt_con.cursor()
 
        read_log_sql = f"""DECLARE
            l_bfile      BFILE;
            l_last       PLS_INTEGER := 1;
            l_current    PLS_INTEGER;
            l_raw_line   RAW(32767);
            l_line_text  VARCHAR2(32767);
            l_line_count PLS_INTEGER := 0;
            BEGIN
            l_bfile := BFILENAME(:dirName, :imp_logFile);
            DBMS_LOB.FILEOPEN(l_bfile, DBMS_LOB.FILE_READONLY);
            LOOP
                l_current := DBMS_LOB.INSTR(l_bfile, HEXTORAW('0A'), l_last, 1);
                EXIT WHEN NVL(l_current, 0) = 0;
                IF l_current > l_last THEN
                    l_raw_line  := DBMS_LOB.SUBSTR(l_bfile, l_current - l_last, l_last);
                    l_line_text := UTL_RAW.CAST_TO_VARCHAR2(l_raw_line);
                    DBMS_OUTPUT.PUT_LINE(l_line_text);
                ELSE
                    DBMS_OUTPUT.PUT_LINE('');
                END IF;
                l_last := l_current + 1;
                l_line_count := l_line_count + 1;
                EXIT WHEN l_line_count > 100000;
            END LOOP;
            IF DBMS_LOB.FILEISOPEN(l_bfile) = 1 THEN DBMS_LOB.FILECLOSE(l_bfile); END IF;
            EXCEPTION WHEN OTHERS THEN
                IF DBMS_LOB.FILEISOPEN(l_bfile) = 1 THEN DBMS_LOB.FILECLOSE(l_bfile); END IF;
                DBMS_OUTPUT.PUT_LINE('Error: ' || SQLERRM);
            END;"""
 
        tgt_cursor.callproc("dbms_output.enable", [None])
        tgt_cursor.execute(read_log_sql, {"dirName": tgt_dir_name, "imp_logFile": imp_log_file})
        output_lines = _read_dbms_output(tgt_cursor, tgt_con)
 
        os.makedirs(os.path.dirname(on_demand_path), exist_ok=True)
        with open(on_demand_path, "w") as fh:
            for line in output_lines:
                import_log.append(line)
                fh.write(line + "\n")
 
    except oracledb.DatabaseError as exc:
        logger.info(str(exc))
        _write_job_file(body.jobName, "ImportOnDemand.log", str(exc))
    finally:
        if tgt_con:
            tgt_cursor.close()
            tgt_con.close()
 
    return [import_log]

@app.post("/api/v2/datapump/downloads3log", tags=["MigDB Homogeneous DataPump"],
    summary="Get S3 download log from RDS",
    description="Reads the RDS download task log from the target database using rdsadmin file utilities and returns the log content.")
def download_s3_log(body: JobNameRequest) -> list:
    row = _fetch_expimp_row(body.jobName, "jobOwner, tgtdbName, tgtdumpDir")
    if not row:
        return [[]]
 
    job_owner, tgt_db_name, tgt_dir_name = row
    dbtask_fetch: list = []
    tgt_con = None
 
    try:
        val = selectConn(tgt_db_name)
        tgt_con = val[0]
        tgt_cursor = tgt_con.cursor()
 
        task_id = _read_job_file(body.jobName, "Download")
        download_log_path = _job_path(body.jobName, "DownloadLog")
        if os.path.exists(download_log_path):
            dbtask_fetch.append({"TEXT": open(download_log_path).read()})
 
        dbtask_id_log = f"dbtask-{task_id}.log"
        df = pd.read_sql_query(
            "SELECT text FROM table(rdsadmin.rds_file_util.read_text_file('BDUMP', :dbtask))",
            tgt_con,
            params=[dbtask_id_log],
        )
        dbtask_fetch = df.to_dict("records")
 
    except oracledb.DatabaseError as exc:
        dbtask_fetch.append(str(exc))
    except pd.io.sql.DatabaseError as exc:
        dbtask_fetch.append({"TEXT": str(exc)})
    finally:
        if tgt_con:
            tgt_cursor.close()
            tgt_con.close()
 
    return [dbtask_fetch]

@app.post("/api/v2/datapump/updates3config", tags=["MigDB Homogeneous DataPump"],
    summary="Update S3 configuration for a job",
    description="Updates the S3 bucket name and AWS credentials for the given DataPump job in the database.")
def update_s3_config(body: UpdateS3ConfigRequest) -> list[list[str]]:
    msg: list[str] = []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE expimp SET bucketName=:bucketName, aws_access_key_id=:aws_access_key_id, "
            "aws_secret_access_key=:aws_secret_access_key WHERE jobName=:jobName",
            {
                "bucketName": body.bucketName,
                "aws_access_key_id": body.aws_access_key_id,
                "aws_secret_access_key": body.aws_secret_access_key,
                "jobName": body.jobName,
            },
        )
        conn.commit()
        msg.append("Updated Successfully")
    except sqlite3.DatabaseError as exc:
        msg.append(str(exc))
    finally:
        cursor.close()
        conn.close()
    return [msg]

import uuid

def _verify_shared_storage(src_db_name: str, src_dir_name: str,
                            tgt_db_name: str, tgt_dir_name: str,
                            cdb_check: str = "NO", pdb_name: str = "") -> bool:
    """
    Empirically verify that the source and target Oracle directory objects
    point at the same underlying physical storage (e.g. a shared EFS mount).

    Writes a unique marker file from the source DB session, then tries to
    read it back from the target DB session. Only returns True if the
    target can see the file AND its content matches exactly what the
    source wrote.
    """
    marker_name = f"_shared_check_{uuid.uuid4().hex[:12]}.tmp"
    marker_value = uuid.uuid4().hex

    src_con = None
    tgt_con = None

    try:
        src_con = selectConn(src_db_name)[0]
        src_cur = src_con.cursor()
        if cdb_check == "YES" and pdb_name:
            src_cur.execute(f"ALTER SESSION SET CONTAINER={pdb_name}")

        write_sql = """DECLARE
            fh UTL_FILE.FILE_TYPE;
            BEGIN
            fh := UTL_FILE.FOPEN(:dirName, :fileName, 'w');
            UTL_FILE.PUT_LINE(fh, :val);
            UTL_FILE.FCLOSE(fh);
            END;"""
        src_cur.execute(write_sql, dirName=src_dir_name, fileName=marker_name, val=marker_value)
        src_con.commit()
        src_cur.close()

        tgt_con = selectConn(tgt_db_name)[0]
        tgt_cur = tgt_con.cursor()

        bfile_var = tgt_cur.var(oracledb.DB_TYPE_BFILE)
        tgt_cur.execute(
            "BEGIN :bfile := BFILENAME(:dir, :fname); END;",
            bfile=bfile_var, dir=tgt_dir_name, fname=marker_name,
        )
        tgt_bfile = bfile_var.getvalue()

        if not tgt_bfile.fileexists():
            logger.info(
                f"_verify_shared_storage: marker '{marker_name}' written to "
                f"{src_db_name}/{src_dir_name} is NOT visible from "
                f"{tgt_db_name}/{tgt_dir_name} — NOT shared storage."
            )
            return False

        tgt_bfile.open()
        read_back = tgt_bfile.read(1, len(marker_value)).decode("utf-8", errors="replace")
        tgt_bfile.close()
        tgt_cur.close()

        is_shared = read_back == marker_value
        logger.info(
            f"_verify_shared_storage: {src_db_name}/{src_dir_name} <-> "
            f"{tgt_db_name}/{tgt_dir_name} shared={is_shared} "
            f"(wrote={marker_value!r} read={read_back!r})"
        )
        return is_shared

    except Exception as exc:
        logger.warning(
            f"_verify_shared_storage failed for {src_db_name}/{src_dir_name} vs "
            f"{tgt_db_name}/{tgt_dir_name}: {exc} — treating as NOT shared (safe default)."
        )
        return False

    finally:
        try:
            if src_con:
                cur = src_con.cursor()
                if cdb_check == "YES" and pdb_name:
                    cur.execute(f"ALTER SESSION SET CONTAINER={pdb_name}")
                cur.execute(
                    "BEGIN UTL_FILE.FREMOVE(:dirName, :fileName); END;",
                    dirName=src_dir_name, fileName=marker_name,
                )
                src_con.commit()
                cur.close()
        except Exception:
            pass
        if src_con:
            try: src_con.close()
            except Exception: pass
        if tgt_con:
            try: tgt_con.close()
            except Exception: pass

@app.post("/api/v2/datapump/xfrdumpfiles", tags=["MigDB Homogeneous DataPump"],
    summary="Transfer dump files to target",
    description="Reads dump file names from the export log and spawns background threads to transfer each file from the source to the target database dump directory.")
def xfr_dump_files(body: JobNameRequest) -> dict:
    if not re.match(r"^[\w\-]+$", body.jobName):
        raise HTTPException(status_code=400, detail="Invalid jobName format")
 
    log_path = _job_path(body.jobName, "Export.log")
    dump_files: list[str] = []
 
    try:
        with open(log_path) as fh:
            for line in fh:
                stripped = line.strip()
                if stripped.lower().endswith(".dmp"):
                    candidate = line.replace("\\", "/").split("/")[-1].strip()
                    if candidate:
                        dump_files.append(candidate)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Export log not found: {log_path}")
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied reading log: {log_path}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read export log: {exc}")
 
    if not dump_files:
        raise HTTPException(status_code=404, detail="No .dmp files found in export log")
 
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT jobOwner, srcdbName, srcdumpDir, cdbCheck, pdbName, tgtdbName, tgtdumpDir "
        "FROM expimp WHERE jobName=:jobName",
        {"jobName": body.jobName},
    )
    db_row = cursor.fetchone()
    cursor.close()
    conn.close()
 
    if not db_row:
        raise HTTPException(status_code=404, detail=f"No job record found for jobName: {body.jobName}")
 
    src_db_name = db_row["srcdbName"]
    dir_name = db_row["srcdumpDir"]
    cdb_check = db_row["cdbCheck"]
    pdb_name = db_row["pdbName"]
    tgt_db_name = db_row["tgtdbName"]
    tgt_dump_dir = db_row["tgtdumpDir"]

    src_dir_path = get_directory_path(src_db_name, dir_name)
    tgt_dir_path  = get_directory_path(tgt_db_name, tgt_dump_dir)

    def _normalize(path: str) -> str:
        return os.path.normpath(path.strip()).rstrip("/").lower() if path else ""

    target_is_efs = bool(tgt_dir_path) and is_efs_path(tgt_dir_path)

    is_shared_directory = False
    if target_is_efs:
        is_shared_directory = _verify_shared_storage(
            src_db_name, dir_name, tgt_db_name, tgt_dump_dir, cdb_check, pdb_name
        )
        if not is_shared_directory:
            logger.info(
                f"Job {body.jobName}: target is EFS but live verification failed "
                f"— not the same shared storage. Falling back to normal transfer."
            )
    else:
        logger.info(f"Job {body.jobName}: target directory is not EFS — running normal file transfer.")

    _write_job_file(body.jobName, "IsSharedDirectory", "YES" if is_shared_directory else "NO")

    use_local_efs = is_efs_path(tgt_dir_path) and os.path.isdir(local_efs_dir) if tgt_dir_path else False

    #use_local_efs = is_efs_path(tgt_dir_path) and os.path.isdir(local_efs_dir)

    if is_shared_directory:
        logger.info(
            f"Job {body.jobName}: source dir '{src_dir_path}' and target dir "
            f"'{tgt_dir_path}' are the SAME shared location — skipping "
            f"transfer entirely for all dump files."
        )

    started, skipped = [], []

    if is_shared_directory:
        if src_dir_path:
            try:
                os.chmod(src_dir_path, 0o777)
            except OSError as exc:
                logger.warning(f"Could not chmod source directory {src_dir_path}: {exc}")

    for file_name in dump_files:
        size_log = os.path.join(agent_home, body.jobName, f"{file_name}_Size.log")

        if is_shared_directory:

            src_dump_file_path = os.path.join(src_dir_path, file_name) if src_dir_path else None
            if src_dump_file_path and os.path.exists(src_dump_file_path):
                try:
                    os.chmod(src_dump_file_path, 0o777)
                except OSError as exc:
                    logger.warning(f"Could not chmod source file {src_dump_file_path}: {exc}")

            if not os.path.exists(size_log):
                dump_file_path = os.path.join(tgt_dir_path, file_name)
                try:
                    file_size = os.path.getsize(dump_file_path) if os.path.exists(dump_file_path) else 0
                except OSError as exc:
                    logger.warning(f"Could not stat {dump_file_path}: {exc}")
                    file_size = 0
 
                with open(size_log, "w") as fh:
                    fh.write(str(file_size))

                speed_path = os.path.join(agent_home, body.jobName, f"{file_name}_speed")
                with open(speed_path, "w") as sp:
                    sp.write(f"100$0$INSTANT${file_size}${file_size}$0")

                _write_job_file(body.jobName, f"{file_name}_TransferStatus", "SKIPPED_SHARED_DIR")
                logger.info(f"{file_name}: marked complete without transfer (shared directory).")
            skipped.append(file_name)
            continue

        if not os.path.exists(size_log):
            skipped.append(file_name)
            if use_local_efs:
                t = threading.Thread(
                                     target=transfer_dumpFile_efs,
                                     args=(src_db_name, body.jobName, dir_name, file_name,cdb_check, pdb_name, local_efs_dir),
                                     name=f"xfr-efs-{body.jobName}-{file_name}", daemon=True)
            else:
                t = threading.Thread(
                                    target=transfer_dumpFile,
                                    args=(src_db_name, body.jobName, dir_name, file_name, cdb_check, pdb_name, tgt_db_name, tgt_dump_dir),
                                    name=f"xfr-{body.jobName}-{file_name}",
                                    daemon=True)
            t.start()
            started.append(file_name)
            time.sleep(1)
 
    return {"started": started, "skipped": skipped,
            "message": f"{len(started)} transfer(s) initiated, {len(skipped)} already done"}

@app.post("/api/v2/datapump/xfrdumpfilestoec2", tags=["MigDB Homogeneous DataPump"],
    summary="Transfer dump files to EC2",
    description="Reads dump file names from the export log and spawns background SCP threads to upload each file to the remote EC2 instance for the given job.")
def xfr_dump_files_to_ec2(body: JobNameRequest) -> dict:
    dump_files: list[str] = []
    log_path = _job_path(body.jobName, "Export.log")
 
    try:
        with open(log_path) as fh:
            for line in fh:
                if ".dmp" in line.lower():
                    dump_files.append(line.strip())
    except OSError as exc:
        raise HTTPException(status_code=404, detail=f"Export log not found: {exc}")
 
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT dep_url FROM onepconn WHERE dep_type='rd'")
    dep_row = cursor.fetchone()
    cursor.close()
    conn.close()
 
    if not dep_row:
        raise HTTPException(status_code=404, detail="No RD deployment URL found")
 
    dep_url = dep_row[0]
    rmt_dir = f"/home/ec2-user/{body.jobName}"
    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", dep_url)
    if not match:
        raise HTTPException(status_code=400, detail="Could not parse host IP from dep_url")
 
    host = match.group(1)
    rmt_key_path = config.get("AGENT_CONFIG", "RMT_KEY_PATH")
    started = []
 
    for file_name in dump_files:
        dump_file_name = file_name.split("/")[-1]
        rmt_size_log = os.path.join(agent_home, body.jobName, f"{dump_file_name}_RMT_Size.log")
        if not os.path.exists(rmt_size_log):
            t = threading.Thread(
                target=upload_one_file,
                args=(host, rmt_key_path, file_name, body.jobName),
                name=f"scp-{dump_file_name}",
                daemon=True,
            )
            t.start()
            started.append(dump_file_name)
            time.sleep(1)
 
    return {"started": started, "message": f"{len(started)} upload(s) initiated"}



class DownloadRequest(BaseModel):
    jobName: str

@app.post("/api/v2/download-from-s3", tags=["MigDB Homogeneous DataPump"],
    summary="Download dump files from S3",
    description="Looks up job details from the database and spawns a background thread to download dump files from the S3 bucket to the target database dump directory.")
def download_from_s3(data: DownloadRequest):
    jobName = data.jobName
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT jobOwner, bucketName, tgtdbName, tgtdumpDir FROM expimp WHERE jobName=:jobName',
        {"jobName": jobName}
    )
    db_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not db_row:
        raise HTTPException(status_code=404, detail=f"Job '{jobName}' not found")

    jobOwner = db_row[0].upper()
    bucketName = db_row[1]
    tgtdbName = db_row[2]
    dirName = db_row[3]

    download_path = os.path.join(agent_home, jobName, jobName + '_Download')
    if not os.path.exists(download_path):
        thread = threading.Thread(
            target=download_dumpFile,
            args=(jobName, tgtdbName, bucketName, dirName)
        )
        thread.start()

    return {"message": f"Download started for job '{jobName}'"}

class TshootImpDPRequest(BaseModel):
    jobName: str

@app.post("/api/v2/tshoot-imp-dp", tags=["MigDB Homogeneous DataPump"],
    summary="Troubleshoot DataPump import job",
    description="Queries the target database for resumable job status, long operations, lock details, session waits, and DataPump worker SQL to help diagnose import issues.")
def tshoot_imp_dp(data: TshootImpDPRequest):
    jobName = data.jobName

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT tgtdbName FROM expimp WHERE jobName=:jobName', {"jobName": jobName})
    db_row = cursor.fetchone()
    cursor.close()
    conn.close()

    impdp_longOps_fetch = ''
    resumable_job_fetch = ''
    session_waits_fetch = ''
    impdp_locks_fetch = ''
    dp_worker_sql_fetch = ''

    if not db_row:
        raise HTTPException(status_code=404, detail=f"Job '{jobName}' not found")

    tgtdbName = db_row[0]
    tgtcon = None
    try:
        val = selectConn(tgtdbName)
        tgtcon = val[0]

        resumable_job = """
            SELECT session_id, status, start_time, suspend_time, resume_time, error_msg, SQL_TEXT
            FROM dba_resumable
        """
        resumable_job_fetch = fetch_query(resumable_job, tgtcon, cast_str=True)

        impdp_longOps = """
            SELECT dp.job_name, dp.state, dp.WORKERS, sl.OPNAME, sl.MESSAGE,
                   ROUND(sl.SOFAR/sl.TOTALWORK*100, 2) DONE, sl.TIME_REMAINING
            FROM gv$session_longops sl, gv$datapump_job dp
            WHERE sl.opname = dp.job_name
              AND sofar != totalwork
              AND dp.job_name = :jobName
        """
        impdp_longOps_fetch = fetch_query_params(impdp_longOps, tgtcon, cast_str=True, params={"jobName": jobName})
        impdp_longOps_fetch = impdp_longOps_fetch.to_dict('records')

        impdp_locks = """
            SELECT dw.waiting_session, dw.holding_session, b.serial# serial, w.event,
                   w.program wprogram, b.program bprogram, w.module wmod, b.module bmod, LOCK_ID1
            FROM sys.dba_waiters dw, gv$session w, gv$session b
            WHERE dw.waiting_session = w.sid
              AND dw.holding_session = b.sid
              AND (w.module LIKE 'Data Pump%'
                OR w.program LIKE '%EXPDP%'
                OR w.program LIKE '%IMPDP%')
            ORDER BY dw.holding_session
        """
        impdp_locks_fetch = fetch_query(impdp_locks, tgtcon, cast_str=True)

        session_waits = """
            SELECT sw.SID, s.program PROG, sw.SEQ# SEQ, sw.EVENT, sw.WAIT_TIME,
                   sw.SECONDS_IN_WAIT, sw.STATE, sw.P1TEXT, sw.P1,
                   sw.P2TEXT, sw.P2, sw.P3TEXT, sw.P3
            FROM GV$SESSION_WAIT sw, GV$SESSION s
            WHERE sw.wait_class <> 'Idle'
              AND sw.sid = s.sid
              AND (s.module LIKE 'Data Pump%'
                OR s.program LIKE '%EXPDP%'
                OR s.program LIKE '%IMPDP%')
        """
        session_waits_fetch = fetch_query(session_waits, tgtcon, cast_str=True)

        dp_worker_sql = """
            SELECT sysdate "date", s.program, s.sid, s.status, s.username,
                   d.job_name, p.spid, s.serial#, p.pid
            FROM gv$session s, gv$process p, dba_datapump_sessions d
            WHERE p.addr = s.paddr
              AND s.saddr = d.saddr
        """
        dp_worker_sql_fetch = fetch_query(dp_worker_sql, tgtcon, cast_str=True)

    except oracledb.DatabaseError as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if tgtcon:
            tgtcon.close()

    return [resumable_job_fetch, impdp_locks_fetch, session_waits_fetch, impdp_longOps_fetch, dp_worker_sql_fetch]

class TableSpaceImpDPRequest(BaseModel):
    jobName: str
    schemas: List[str]
    srcdbName: str
    tgtdbName: str
    cdbCheck: str
    pdbName: str

@app.post("/api/v2/tablespace-imp-dp", tags=["MigDB Homogeneous DataPump"],
    summary="Get tablespace details for import",
    description="Queries the source database for distinct tablespace names used by the given schemas, optionally switching to the specified PDB container first.")
def tablespace_imp_dp(data: TableSpaceImpDPRequest):
    jobName = data.jobName
    schemas = data.schemas
    srcdbName = data.srcdbName
    tgtdbName = data.tgtdbName
    cdbCheck = data.cdbCheck
    pdbName = data.pdbName

    tablespace_det_fetch = ''
    srccon = None
    try:
        val = selectConn(srcdbName)
        srccon = val[0]
        srccursor = srccon.cursor()

        if cdbCheck == 'YES' and len(pdbName) > 0:
            srccursor.execute('ALTER SESSION SET CONTAINER=' + str(pdbName))

        bindNames = [":" + str(i + 1) for i in range(len(schemas))]
        tablespace_det = """
            SELECT DISTINCT tablespace_name
            FROM dba_segments
            WHERE OWNER IN (%s)
        """ % ",".join(bindNames)

        tablespace_det_fetch = pd.read_sql_query(tablespace_det, srccon, params=[*schemas])
        tablespace_det_fetch = tablespace_det_fetch.to_dict('records')

    except oracledb.DatabaseError as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if srccursor:
           srccursor.close()
        if srccon:
            srccon.close()

    return [tablespace_det_fetch]

class GgSuppSchemaRequest(BaseModel):
    domain: str
    alias: str
    opts: Optional[str] = None
    SchemaName: str

class GgSuppTrandataRequest(BaseModel):
    domain: str
    alias: str
    buttonValue : str
    opts: Optional[str] = None
    tabNameList: List[str]

# ── shared helpers ────────────────────────────────────────────────────────────

def _supp_login_check(alias: str, domain: str) -> Optional[str]:
    """Returns error string if login fails, else None."""
    ssh = subprocess.Popen(
        [ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0
    )
    out, _ = ssh.communicate(f"dblogin useridalias {alias} domain {domain}\n")
    ssh.kill()
    return out if "ERROR" in out else None

def _supp_run_ggsci(alias: str, domain: str, commands: list[str]) -> str:
    ssh = subprocess.Popen(
        [ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0
    )
    cmds = f"dblogin useridalias {alias} domain {domain}\n" + "\n".join(commands) + "\n"
    out, _ = ssh.communicate(cmds)
    return out

async def _supp_run_ggsci_stream(alias: str, domain: str, commands: list[str]):
    cmds = f"dblogin useridalias {alias} domain {domain}\n" + "\n".join(commands) + "\nexit\n"
    proc = await asyncio.create_subprocess_exec(
        ggsci_bin,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    proc.stdin.write(cmds.encode())
    await proc.stdin.drain()
    proc.stdin.close()

    while True:
        raw = await proc.stdout.readline()
        if not raw:
            break
        line = raw.decode(errors="replace").rstrip()
        if line:
            yield line
        await asyncio.sleep(0)

    await proc.wait()

def _supp_parse_and_write(raw_output: str, tranlevel: str, SchemaName: Optional[str] = None):
    """Write log, parse errors and key column results."""
    err_file_path = os.path.join(agent_log, 'AddSuppErr.lst')
    with open(err_file_path, 'w') as f:
        f.write(raw_output)

    ErrPrint = []
    suppResults = []
    pattern = re.compile(
        r"key columns on table\s+([A-Z0-9_]+\.[A-Z0-9_]+):\s*([A-Z0-9_,\s]+)", re.I
    )
    with open(err_file_path, 'r') as f:
        for line in f:
            line = line.replace("Oracle Goldengate", "MigDB").replace("OGG-", "CDC-")
            if 'ERROR' in line:
                ErrPrint.append(line.split('>', 1)[-1])
            if tranlevel == 'schematrandata' and SchemaName and SchemaName in line:
                ErrPrint.append(line)
                logger.info(line)
                stripped = line.strip()
                if not stripped:
                    continue
                m = pattern.search(stripped)
                if m:
                    table = m.group(1)
                    keys = [k.strip() for k in m.group(2).split(",")]
                    suppResults.append({"level": "Success", "table": table, "keys": keys})
    return [ErrPrint, suppResults]


# ── Schema-level (schematrandata) ─────────────────────────────────────────────

def _supp_run_ggsci_schema_tables(alias: str, domain: str, schema_name: str, action: str, opts: str = '') -> str:
    """Run add/info/delete trandata SCHEMA.* to get per-table results."""
    ssh = subprocess.Popen(
        [ggsci_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=0
    )
    if action == 'add':
        cmd = (
            f'dblogin useridalias {alias} domain {domain}\n'
            f'add schematrandata {schema_name} {opts}\n'
        )
    elif action == 'info':
        cmd = (
            f'dblogin useridalias {alias} domain {domain}\n'
            f'info schematrandata {schema_name}\n'
        )
    elif action == 'del':
        cmd = (
            f'dblogin useridalias {alias} domain {domain}\n'
            f'delete schematrandata {schema_name} {opts}\n'
        )
    else:
        cmd = ''
    out, _ = ssh.communicate(input=cmd, timeout=120)
    return out

def _parse_schema_tables_output(out: str, schema_name: str):
    result = {
        'tableName'      : schema_name,
        'status'         : 'Unknown',
        'schedulingCols' : 'NO',
        'allCols'        : 'NO',
        'error'          : ''
    }
    warnings = []               # per-table issues (non-fatal to schema status)
    found_any = False
    status_locked = False       # True once a definitive schema-level message is seen

    for raw_line in out.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        low = line.lower()

        # --- Per-table / row-level errors: collect, DON'T overwrite schema status ---
        if re.search(r'\berror\s+ogg-\d+', low):
            warnings.append(line)
            found_any = True
            continue

        if low.startswith('error:') or re.search(r'\berror:\s', line, re.IGNORECASE):
            warnings.append(line)
            found_any = True
            if not status_locked:
                result['status'] = 'Error'
            continue

        if re.search(r'OGG-0197[67]\b', line) or re.search(r'OGG-0198[01]\b', line):
            if 'scheduling' in low:
                result['schedulingCols'] = 'YES'
            elif 'all columns' in low:
                result['allCols'] = 'YES'
            if not status_locked:
                result['status'] = 'Enabled'
            found_any = True
            continue

        if re.search(r'OGG-0197[89]\b', line) or re.search(r'OGG-0198[23]\b', line):
            if 'scheduling' in low:
                result['schedulingCols'] = 'NO'
            elif 'all columns' in low:
                result['allCols'] = 'NO'
            if not status_locked:
                result['status'] = 'Disabled'
            found_any = True
            continue

        # --- Definitive schema-level messages: these LOCK the status ---
        if 'schematrandata has been added on schema' in low:
            result['status'] = 'Enabled'
            status_locked = True
            found_any = True
            continue

        if 'schematrandata has been removed on schema' in low or \
           'schematrandata has been deleted on schema' in low:
            result['status'] = 'Disabled'
            status_locked = True
            found_any = True
            continue

        if 'supplemental logging is disabled on schema' in low:
            result['status'] = 'Disabled'
            status_locked = True
            found_any = True
            continue

        if 'supplemental logging' in low and 'is enabled on schema' in low:
            result['status'] = 'Enabled'
            status_locked = True
            found_any = True
            continue

    if not found_any:
        result['status'] = 'Unknown'
        result['error']  = 'No table details found in output'
    elif warnings:
        # Surface per-table issues as warnings without failing the whole op
        result['error'] = '; '.join(warnings)

    return [result]

@app.post("/api/v2/supp/schema", tags=["MigDB Supplemental Logging"],
    summary="Add schema-level supplemental logging",
    description="Streams per-table results for 'add trandata SCHEMA.*' as SSE.")
def supp_schema_add(data: GgSuppSchemaRequest):
    def generate():
        if err := _supp_login_check(data.alias, data.domain):
            yield f"data: {json.dumps({'tableName': data.SchemaName, 'status': 'Error', 'keys': '', 'error': str(err)})}\n\n"
            yield "data: __DONE__\n\n"
            return
        try:
            out  = _supp_run_ggsci_schema_tables(data.alias, data.domain, data.SchemaName, 'add', data.opts or '')
            rows = _parse_schema_tables_output(out, data.SchemaName)
            for row in rows:
                yield f"data: {json.dumps(row)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'tableName': data.SchemaName, 'status': 'Error', 'keys': '', 'error': str(e)})}\n\n"
        yield "data: __DONE__\n\n"

    return StreamingResponse(generate(), media_type='text/plain',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no',
                 'Connection': 'keep-alive', 'X-Content-Type-Options': 'nosniff'})


@app.get("/api/v2/supp/schema/{schema_name}", tags=["MigDB Supplemental Logging"],
    summary="View schema-level supplemental logging",
    description="Streams per-table results for 'info trandata SCHEMA.*' as SSE.")
def supp_schema_info(schema_name: str, alias: str, domain: str):
    def generate():
        if err := _supp_login_check(alias, domain):
            yield f"data: {json.dumps({'tableName': schema_name, 'status': 'Error', 'keys': '', 'error': str(err)})}\n\n"
            yield "data: __DONE__\n\n"
            return
        try:
            out  = _supp_run_ggsci_schema_tables(alias, domain, schema_name, 'info')
            rows = _parse_schema_tables_output(out, schema_name)
            for row in rows:
                yield f"data: {json.dumps(row)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'tableName': schema_name, 'status': 'Error', 'keys': '', 'error': str(e)})}\n\n"
        yield "data: __DONE__\n\n"

    return StreamingResponse(generate(), media_type='text/plain',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no',
                 'Connection': 'keep-alive', 'X-Content-Type-Options': 'nosniff'})


@app.delete("/api/v2/supp/schema/{schema_name}", tags=["MigDB Supplemental Logging"],
    summary="Delete schema-level supplemental logging",
    description="Streams per-table results for 'delete trandata SCHEMA.*' as SSE.")
def supp_schema_delete(schema_name: str, alias: str, domain: str, opts: Optional[str] = None):
    def generate():
        if err := _supp_login_check(alias, domain):
            yield f"data: {json.dumps({'tableName': schema_name, 'status': 'Error', 'keys': '', 'error': str(err)})}\n\n"
            yield "data: __DONE__\n\n"
            return
        try:
            out  = _supp_run_ggsci_schema_tables(alias, domain, schema_name, 'del', opts or '')
            rows = _parse_schema_tables_output(out, schema_name)
            for row in rows:
                yield f"data: {json.dumps(row)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'tableName': schema_name, 'status': 'Error', 'keys': '', 'error': str(e)})}\n\n"
        yield "data: __DONE__\n\n"

    return StreamingResponse(generate(), media_type='text/plain',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no',
                 'Connection': 'keep-alive', 'X-Content-Type-Options': 'nosniff'})


# ── Table-level (trandata) ────────────────────────────────────────────────────

@app.post("/api/v2/supp/trandata", tags=["MigDB Supplemental Logging"])
async def gg_add_supp(data: GgSuppTrandataRequest):

    def generate():
        for tabname in data.tabNameList:
            tabname = tabname.strip()
            if not tabname:
                continue

            ssh = subprocess.Popen(
                [ggsci_bin],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=0
            )

            try:
                if data.buttonValue == 'add':
                    cmd = (
                        f'dblogin useridalias {data.alias} domain {data.domain}\n'
                        f'add trandata {tabname} {data.opts or ""}\n'
                    )
                elif data.buttonValue == 'info':
                    cmd = (
                        f'dblogin useridalias {data.alias} domain {data.domain}\n'
                        f'info trandata {tabname}\n'
                    )
                elif data.buttonValue == 'del':
                    cmd = (
                        f'dblogin useridalias {data.alias} domain {data.domain}\n'
                        f'delete trandata {tabname} {data.opts or ""}\n'
                    )
                else:
                    cmd = ''

                output, _ = ssh.communicate(input=cmd, timeout=60)
                result = _parse_single_table_output(output, tabname)

            except subprocess.TimeoutExpired:
                ssh.kill()
                ssh.wait()
                result = {
                    'tableName': tabname,
                    'status'   : 'Error',
                    'keys'     : '',
                    'error'    : 'GGSCI timed out'
                }
            except Exception as e:
                try:
                    ssh.kill()
                except Exception:
                    pass
                result = {
                    'tableName': tabname,
                    'status'   : 'Error',
                    'keys'     : '',
                    'error'    : str(e)
                }

            yield f"data: {json.dumps(result)}\n\n"

        yield "data: __DONE__\n\n"

    return StreamingResponse(
        generate(),
        media_type='text/plain',
        headers={
            'Cache-Control'         : 'no-cache',
            'X-Accel-Buffering'     : 'no',
            'Connection'            : 'keep-alive',
            'X-Content-Type-Options': 'nosniff',
        }
    )


def _parse_single_table_output(output, tabname):
    lines     = output.splitlines()
    status    = None
    keys      = ''
    error_msg = ''

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if re.match(r'^GGSCI\s*\(', line, re.IGNORECASE):
            continue
        if 'Oracle GoldenGate Command Interpreter' in line:
            continue
        if 'Oracle Goldengate support native capture' in line:
            continue
        if 'Successfully logged into database' in line:
            continue
        if re.match(r'^Version\s+\d+', line, re.IGNORECASE):
            continue
        if re.match(r'^Copyright', line, re.IGNORECASE):
            continue
        if re.match(r'^Operating system', line, re.IGNORECASE):
            continue
        if re.match(r'^Oracle Linux', line, re.IGNORECASE):
            continue
        if re.match(r'^OGGCORE_', line, re.IGNORECASE):
            continue

        if 'OGG-15131' in line:
            status = 'Already Enabled'
            continue

        if 'OGG-15132' in line:
            status = 'Enabled'
            continue

        if 'OGG-15135' in line:
            continue

        if 'OGG-15142' in line:
            status = 'Disabled'
            continue

        if 'OGG-15137' in line:
            if not status:  # don't override OGG-15142 if already set
                status = 'Already Disabled'
            continue

        if 'OGG-15435' in line:
            if not status:
                status = 'Disabled'
            continue

        if 'OGG-26035' in line:
            if not status:
                m = re.search(r'is\s+(ENABLED|DISABLED)', line, re.IGNORECASE)
                if m:
                    val = m.group(1).upper()
                    status = 'Enabled' if val == 'ENABLED' else 'Disabled'
            continue

        if re.search(r'logging of supplemental redo log data is already enabled for table', line, re.IGNORECASE):
            status = 'Already Enabled'
            continue
        if re.search(r'logging of supplemental redo log data is enabled for table', line, re.IGNORECASE):
            status = 'Enabled'
            continue
        if re.search(r'logging of supplemental redo log data is already disabled for table', line, re.IGNORECASE):
            status = 'Already Disabled'
            continue
        if re.search(r'logging of supplemental redo log data is disabled for table', line, re.IGNORECASE):
            status = 'Disabled'
            continue

        if 'OGG-10471' in line:
            m = re.search(r'key columns on table\s+[\w.]+\s*:\s*(.+?)\.?\s*$', line, re.IGNORECASE)
            if m:
                keys = m.group(1).strip().rstrip('.')
            continue
        if re.search(r'columns supplementally logged for table', line, re.IGNORECASE):
            m = re.search(r'columns supplementally logged for table\s+[\w.]+\s*:\s*(.+?)\.?\s*$', line, re.IGNORECASE)
            if m:
                keys = m.group(1).strip().rstrip('.')
            continue

        if re.search(r'\b(ERROR|WARNING)\s+OGG-\d+', line, re.IGNORECASE):
            error_msg = line
            status    = 'Error'
            continue

    if status == 'Error':
        return {
            'tableName': tabname,
            'status'   : 'Error',
            'keys'     : '',
            'error'    : error_msg
        }

    return {
        'tableName': tabname,
        'status'   : status or 'Unknown',
        'keys'     : keys,
        'error'    : ''
    }

class GgHeartBeatBaseRequest(BaseModel):
    domain: str
    alias: str

class GgHeartBeatMutateRequest(GgHeartBeatBaseRequest):
    HBTblFrequency: int
    HBTblRetention: int
    HBTblPurgeFrequency: int

class AddHeartBeatRequest(BaseModel):
    domain:             str
    alias:              str
    hbTblOps:           str
    targetOnly:         Optional[str] = ""
    partitioned:         Optional[bool] = False 
    HBTblFrequency:     Optional[int] = None
    HBTblRetention:     Optional[int] = None
    HBTblPurgeFrequency: Optional[int] = None


def _update_globals_and_login(alias: str, domain: str) -> tuple[list, any]:
    """Shared helper: update GLOBALS file, verify login, return (AddHB_Out, ssh)."""
    # --- Fetch user from DB ---
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user FROM CONN WHERE dbname=:dbname', {"dbname": alias})
    db_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not db_row:
        raise HTTPException(status_code=404, detail=f"No user found for alias '{alias}'")
    user = db_row[0]

    # --- Update GLOBALS file ---
    globals_path = os.path.join(gg_home, 'GLOBALS')
    with open(globals_path, 'r') as f:
        global_lines = f.readlines()
    with open(globals_path, 'w') as f:
        for line in global_lines:
            f.write(f"GGSCHEMA {user}\n" if 'GGSCHEMA' in line else line)

    # --- Login check ---
    ssh = subprocess.Popen(
        [ggsci_bin],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0
    )
    ssh.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
    LoginErr, _ = ssh.communicate()

    AddHB_Out = []
    if "ERROR" in LoginErr:
        AddHB_Out.append(LoginErr)
        ssh.kill()
        ssh.stdin.close()
        return AddHB_Out, None  # None signals login failure

    # --- Open fresh session for actual command ---
    ssh = subprocess.Popen(
        [ggsci_bin],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0
    )
    ssh.stdin.write(f"dblogin useridalias {alias} domain {domain}\n")
    return AddHB_Out, ssh


def _run_and_parse(ssh, command: str, AddHB_Out: list) -> list:
    """Write command, communicate, parse output, return ErrPrint."""
    if ssh:
        ssh.stdin.write(command)
        AddHBErr, _ = ssh.communicate()
        if 'ERROR' in AddHBErr:
            AddHB_Out.append(AddHBErr)
            ssh.kill()
            ssh.stdin.close()
        else:
            AddHB_Out.append(AddHBErr)

    err_file_path = os.path.join(agent_log, 'AddHBErr.lst')
    with open(err_file_path, 'w') as f:
        for line in AddHB_Out:
            f.write(line)

    ErrPrint = []
    with open(err_file_path, 'r') as f:
        for line in f:
            if 'ERROR' in line:
                ErrPrint.append(line.split('>', 1)[-1])
            elif 'ORA-' in line:
                ErrPrint.append(line.split('>', 1)[-1])
                ErrPrint.append('Solution : Please grant create procedure and create view to MigDB Admin user')
            elif 'INFO' in line:
                ErrPrint.append(line)

    return [ErrPrint]

@app.post("/api/v2/heartbeat/manage", tags=["MigDB Heartbeat Management"],
    summary="Manage heartbeat table",
    description="Add, edit, or delete a heartbeat table in MigDB for the given alias and domain.")
def gg_add_heartbeat(body: AddHeartBeatRequest):
    domain     = body.domain
    alias      = body.alias
    hbTblOps   = body.hbTblOps
    targetOnly = body.targetOnly

    if hbTblOps in ("addTable", "edTable"):
        if not body.HBTblFrequency or not body.HBTblRetention or not body.HBTblPurgeFrequency:
            raise HTTPException(
                status_code=400,
                detail="HBTblFrequency, HBTblRetention, and HBTblPurgeFrequency "
                       "are required for addTable and edTable operations."
            )

    user = None
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT user FROM CONN WHERE dbname = :dbname',
                {'dbname': alias}
            )
            db_row = cursor.fetchone()
            if db_row:
                user = db_row[0]
    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    if not user:
        raise HTTPException(status_code=404, detail=f"No user found for alias '{alias}'")

    globals_path = os.path.join(gg_home, 'GLOBALS')
    try:
        with open(globals_path, 'r') as f:
            global_lines = f.readlines()

        with open(globals_path, 'w') as f:
            for line in global_lines:
                if 'GGSCHEMA' in line.upper():
                    f.write(f'GGSCHEMA {user}\n')
                else:
                    f.write(line)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to update GLOBALS file: {e}")

    os.makedirs(agent_log, exist_ok=True)
    add_hb_out: list[str] = []

    dblogin_cmd = f"dblogin useridalias {alias} domain {domain}\n"

    login_proc = _spawn_ggsci()
    login_proc.stdin.write(dblogin_cmd)
    login_out = _communicate(login_proc)

    if 'ERROR' in login_out:
        add_hb_out.append(login_out)
    else:
        proc = _spawn_ggsci()
        proc.stdin.write(dblogin_cmd)

        if hbTblOps == "addTable":
            cmd = "add heartbeattable"
            if targetOnly == "targetonly":
                cmd += ", targetonly"
            if body.partitioned:               
                cmd += ", partitioned"
            proc.stdin.write(cmd + "\n")

        elif hbTblOps == "edTable":
            proc.stdin.write(
                f"alter heartbeattable"
                f" frequency {body.HBTblFrequency},"
                f" retention_time {body.HBTblRetention},"
                f" purge_frequency {body.HBTblPurgeFrequency}\n"
            )

        elif hbTblOps == "delTable":
            proc.stdin.write("delete heartbeattable\n")

        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {hbTblOps}")

        add_hb_out.append(_communicate(proc))

    log_path = os.path.join(agent_log, "AddHBErr.lst")
    with open(log_path, "w") as f:
        f.writelines(add_hb_out)

    err_print: list[str] = []

    with open(log_path, "r") as f:
        for raw_line in f:
            stripped = raw_line.strip()

            if not stripped:
                continue

            if 'GGSCI' in stripped and '>' in stripped:
                msg = stripped.split('>', 1)[-1].strip()
                if not msg:
                    continue
                stripped = msg

            stripped = re.sub(r'\bOGG-', 'CDC-', stripped, flags=re.IGNORECASE)
            # stripped = replace_gg_branding(stripped)

            if 'ORA-' in stripped:
                err_print.append(stripped + '\n')
                err_print.append(
                    'Solution: Please grant CREATE PROCEDURE and '
                    'CREATE VIEW to MigDB Admin user\n'
                )

            elif re.search(r'\bERROR\b', stripped, re.IGNORECASE):
                err_print.append(stripped + '\n')

            elif re.search(r'\bWARNING\b', stripped, re.IGNORECASE):
                err_print.append(stripped + '\n')

            elif re.search(r'\bINFO\b', stripped, re.IGNORECASE):
                err_print.append(stripped + '\n')

            elif re.search(r'\bfailed\b', stripped, re.IGNORECASE):
                err_print.append(stripped + '\n')

    return JSONResponse(content=[err_print])

@app.get("/api/v2/list-prm-files", tags=["MigDB Parameter Management"],
    summary="List parameter files",
    description="Returns all .prm files from the MigDB dirprm directory along with the GLOBALS file, creating it with default wallet settings if it does not already exist.")
def list_prm_files():
    globals_filename = 'GLOBALS'
    globals_path = os.path.join(gg_home, globals_filename)
    param_directory = os.path.join(gg_home, 'dirprm')

    # --- Collect .prm files ---
    prmfiles = [
        filename
        for filename in os.listdir(param_directory)
        if filename.endswith(".prm") and os.path.isfile(os.path.join(param_directory, filename))
    ]

    # --- Handle GLOBALS file ---
    if not os.path.exists(globals_path):
        wallet_content = (
            f"GGSCHEMA GGADMIN\n"
            f"WALLETLOCATION {os.path.join(gg_home, 'dirwlt')}\n"
            f"ALLOWOUTPUTDIR {trailPath}"
        )
        with open(globals_path, 'w') as f:
            f.write(wallet_content)

    prmfiles.append(globals_filename)

    return [prmfiles]

@app.get("/api/v2/list-rpt-files", tags=["MigDB Parameter Management"],
    summary="List report files",
    description="Returns all .rpt report files found in the MigDB dirrpt directory.")
def list_rpt_files():
    report_directory = os.path.join(gg_home, 'dirrpt')

    rptfiles = [
        filename
        for filename in os.listdir(report_directory)
        if filename.endswith(".rpt") and os.path.isfile(os.path.join(report_directory, filename))
    ]

    return [rptfiles]

@app.get("/api/v2/list-dsc-files", tags=["MigDB Parameter Management"],
    summary="List discard files",
    description="Returns all .dsc discard files from the MigDB dirrpt directory and resolves additional discard file paths declared in .prm parameter files.")
def list_dsc_files():
    report_directory = os.path.join(gg_home, 'dirrpt')
    prm_directory = os.path.join(gg_home, 'dirprm')

    # --- Collect .dsc files from dirrpt ---
    dscfiles = [
        filename
        for filename in os.listdir(report_directory)
        if filename.endswith(".dsc") and os.path.isfile(os.path.join(report_directory, filename))
    ]

    # --- Extract DISCARDFILE paths from .prm files ---
    dscnames = []
    for filename in os.listdir(prm_directory):
        if filename.endswith(".prm"):
            prm_path = os.path.join(prm_directory, filename)
            with open(prm_path) as infile:
                for line in infile:
                    if 'DISCARDFILE' in line:
                        parts = line.split()
                        dscnames.append(parts[1].rstrip(','))

    # --- Resolve discard file paths ---
    for name in dscnames:
        if name.startswith('.') or name[0].isalnum():
            dscfiles.append(os.path.join(gg_home, name))
        else:
            dscfiles.append(name)

    return [dscfiles]

class PrmFileRequest(BaseModel):
    prmFile: str

@app.post("/api/v2/view-prm-files", tags=["MigDB Parameter Management"],
    summary="View a parameter file",
    description="Reads and returns the contents of a specified .prm parameter file or the GLOBALS file from the MigDB installation directory.")
def view_prm_files(body: PrmFileRequest):
    prm_file = body.prmFile.lstrip('["').rstrip('"]')
    
    if prm_file == 'GLOBALS':
        file_path = os.path.join(gg_home, 'GLOBALS')
    else:
        file_path = os.path.join(gg_home, 'dirprm', prm_file)
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File '{prm_file}' not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied reading '{prm_file}'")
    
    return [content]


class RptFileRequest(BaseModel):
    rptFile: str

@app.post("/api/v2/view-rpt-files", tags=["MigDB Parameter Management"],
    summary="View a report file",
    description="Reads and returns the cleaned contents of a specified .rpt report file from the MigDB dirrpt directory.")
def view_rpt_files(body: RptFileRequest):
    rpt_file = body.rptFile.lstrip('["').rstrip('"]')
    file_path = os.path.join(gg_home, 'dirrpt', rpt_file)

    try:
        with open(file_path, 'r') as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File '{rpt_file}' not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied reading '{rpt_file}'")

    content = "\n".join(line for line in clean_gg_log(lines))
    return [content]

class DscFileRequest(BaseModel):
    dscFile: str

@app.post("/api/v2/view-dsc-files", tags=["MigDB Parameter Management"],
    summary="View a discard file",
    description="Reads and returns the cleaned contents of a specified .dsc discard file from the MigDB dirrpt directory.")
def view_dsc_files(body: DscFileRequest):
    dsc_file = body.dscFile.lstrip('["').rstrip('"]')
    file_path = os.path.join(gg_home, 'dirrpt', dsc_file)

    try:
        with open(file_path, 'r') as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File '{dsc_file}' not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied reading '{dsc_file}'")

    content = "\n".join(line for line in clean_gg_log(lines))
    return [content]


class SavePrmFileRequest(BaseModel):
    prmFile: str
    prmContent: str

@app.post("/api/v2/save-prm-files", tags=["MigDB Parameter Management"],
    summary="Save a parameter file",
    description="Writes updated content to the specified .prm or GLOBALS file, creating a timestamped backup of the existing file before saving.")
def save_prm_files(body: SavePrmFileRequest):
    prm_file = body.prmFile.lstrip('["').rstrip('"]')

    if prm_file == 'GLOBALS':
        file_path = os.path.join(gg_home, prm_file)
    else:
        file_path = os.path.join(gg_home, 'dirprm', prm_file)

    try:
        if prm_file != 'GLOBALS':
            backup_path = file_path + "." + datetime.now().strftime("%Y-%m-%d_%H%M%S")
            shutil.copy(file_path, backup_path)

        with open(file_path, 'w') as f:
            f.write(body.prmContent)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File '{prm_file}' not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied writing '{prm_file}'")

    return ['Parameter File Saved']


@app.get("/api/v2/get-version", tags=["MigDB CDC Info"],
    summary="Get CDC version",
    description="Retrieve the installed CDC version string and returns both the full version and a condensed numeric version identifier.")
def get_version():
    getVer = subprocess.getoutput(ggsci_bin + " -v")

    try:
        gg_ver = None
        gg_version = None

        for line in getVer.splitlines():
            if 'Version' in line:
                gg_ver = line.split('Version', 1)[-1].strip()
                gg_ver1 = gg_ver.split('.')
                gg_version = gg_ver1[0] + gg_ver1[1]
                break
        if gg_ver is None:
            raise HTTPException(status_code=500, detail="Version string not found in ggsci output")

    except IndexError:
        raise HTTPException(status_code=500, detail="Failed to parse version string")

    return [gg_ver, gg_version]

class MemUsageRequest(BaseModel):
    processName: str
    read_bytes: int
    write_bytes: int
    read_count: int
    write_count: int

@app.post("/api/v2/mem-usage-by-process", tags=["MigDB System Monitoring"],
    summary="Get memory, CPU and IO stats for a process",
    description="Reads the PID file for the given MigDB process and returns detailed memory, CPU, thread-level CPU, and IO statistics using psutil.")
def mem_usage_by_process(body: MemUsageRequest):
    extpidfiles = []
    mem_process_det = {}
    cpu_process_det = {}
    cpu_thread_det = []
    io_process_det = {}

    pid_dir = os.path.join(gg_home, 'dirpcs', body.processName)
    extpidfiles = glob.glob(pid_dir + '.pc*')

    process_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    for file in extpidfiles:
        process = os.path.basename(file).split('.')[0]

        with open(file) as infile:
            for line in infile:
                line = line.strip()
                if len(line) <= 2:
                    continue

                parts = line.split()
                if 'PID' not in parts:
                    continue

                pid = parts[parts.index('PID') + 1]

                try:
                    p = psutil.Process(int(pid))
                    mem_full = p.memory_full_info()
                    mem_info = p.memory_info()

                    mem_process_det = {
                        'group':   process,
                        'rss':     bytes2human(mem_full[0]),
                        'vms':     bytes2human(mem_full[1]),
                        'swap':    bytes2human(mem_full[9]),
                        'lib':     bytes2human(mem_info[5]),
                        'uss':     bytes2human(mem_full[7]),
                        'mem':     round(p.memory_percent(), 2),
                        'rssper':  p.memory_percent(memtype="rss"),
                        'vmsper':  p.memory_percent(memtype="vms"),
                        'ussper':  p.memory_percent(memtype="uss"),
                        'inctime': process_time,
                    }

                    cpu_percent = p.cpu_percent(interval=0.1)
                    cpu_times = p.cpu_times()
                    cpu_time = sum(cpu_times)

                    cpu_process_det = {
                        'process': process,
                        'pid':     pid,
                        'user':    cpu_times[0],
                        'kernel':  cpu_times[1],
                        'iowait':  cpu_times[4],
                        'inctime': process_time,
                    }

                    for t in p.threads():
                        thread_cpu_total = t.system_time + t.user_time
                        cpu = round(cpu_percent * (thread_cpu_total / cpu_time), 1)
                        cpu_sys = round(cpu_percent * round(t.system_time / cpu_time))
                        cpu_user = round(cpu_percent * round(t.user_time / cpu_time))
                        cpu_thread_det.append({
                            'group':   process,
                            'pid':     pid,
                            'thread':  t[0],
                            'cpu':     cpu,
                            'cpusys':  cpu_sys,
                            'cpuuser': cpu_user,
                            'inctime': process_time,
                        })

                    io = p.io_counters()
                    io_process_det = {
                        'group':             process,
                        'diskio':            io[2] + io[3],
                        'read_count':        io[0],
                        'write_count':       io[1],
                        'read_bytes':        io[2],
                        'write_bytes':       io[3],
                        'delta_read_count':  (io[0] - body.read_count)  if body.read_count  > 0 else 0,
                        'delta_write_count': (io[1] - body.write_count) if body.write_count > 0 else 0,
                        'delta_read_bytes':  (io[2] - body.read_bytes)  if body.read_bytes  > 0 else 0,
                        'delta_write_bytes': (io[3] - body.write_bytes) if body.write_bytes > 0 else 0,
                        'inctime':           process_time,
                    }

                except psutil.NoSuchProcess:
                    pass

    return [mem_process_det, cpu_process_det, cpu_thread_det, io_process_det]

@app.get("/api/v2/mem-usage", tags=["MigDB System Monitoring"],
    summary="Get overall system and process stats",
    description="Scans all MigDB process PID files and returns per-process memory, CPU, and IO metrics along with overall system memory utilization, swap, load average, and CPU times.")
def mem_usage():
    mem_det = []
    cpu_det = []
    io_det = []

    pid_dir = os.path.join(gg_home, 'dirpcs')
    extpidfiles = glob.glob(pid_dir + '/*.pc*')

    i = 0
    total_process_mem = 0
    process_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    for file in extpidfiles:
        process = os.path.basename(file).split('.')[0]

        with open(file) as infile:
            for line in infile:
                line = line.strip()
                if len(line) <= 2:
                    continue

                parts = line.split()
                if 'PID' not in parts:
                    continue

                pid = parts[parts.index('PID') + 1]

                try:
                    p = psutil.Process(int(pid))
                    mem_full = p.memory_full_info()

                    mem_det.append({
                        'id':      i,
                        'group':   process,
                        'rss':     round(mem_full[0] / (1024 * 1024)),
                        'uss':     round(mem_full[7] / (1024 * 1024)),
                        'mem':     round(p.memory_percent(), 3),
                        'inctime': process_time,
                    })

                    total_process_mem += p.memory_percent()

                    cpu_det.append({
                        'id':      i,
                        'group':   process,
                        'cpu':     p.cpu_percent(interval=0.2),
                        'inctime': process_time,
                    })

                    io = p.io_counters()
                    io_det.append({
                        'id':        i,
                        'group':     process,
                        'diskbytes': io[2] + io[3],
                        'diskcount': io[0] + io[1],
                        'inctime':   process_time,
                    })

                    i += 1

                except psutil.NoSuchProcess:
                    pass

    cpu_times = psutil.cpu_times_percent(interval=0.2)
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    loadavg = psutil.getloadavg()

    mem_util = {
        'total':        round(mem[0]  / (1024 ** 3)),
        'available':    round(mem[1]  / (1024 ** 3)),
        'used':         round(mem[3]  / (1024 ** 3)),
        'free':         round(mem[4]  / (1024 ** 3)),
        'percent':      mem[2],
        'swap_tot':     round(swap[0] / (1024 ** 3)),
        'swap_used':    round(swap[1] / (1024 ** 3)),
        'swap_free':    round(swap[2] / (1024 ** 3)),
        'swap_percent': round(swap[3] / (1024 ** 3)),
        'cpuUser':      cpu_times[0],
        'cpuSystem':    cpu_times[2],
        'loadavg':      loadavg,
    }

    return [mem_det, mem_util, cpu_det, io_det, round(total_process_mem, 1)]

class DbConnRequest(BaseModel):
    dbButton: str
    dbname: str | None = None
    username: str | None = None
    passwd: str | None = None
    servicename: str | None = None

@app.post("/api/v2/db/conn", tags=["MigDB Database"],
    summary="Add a database connection",
    description="Inserts a new database connection record with encrypted credentials into the CONN table.")
def db_conn_add(body: DbConnRequest):
    msg = ''
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO CONN VALUES(:dbname,:user,:passwd,:servicename)',
            {
                "dbname":      body.dbname,
                "user":        body.username,
                "passwd":      cipher.encrypt(body.passwd),
                "servicename": body.servicename,
            }
        )
        msg = 'Database Details Added'

        conn.commit()

    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            cursor.close()
            conn.close()

    return [msg]

@app.put("/api/v2/db/conn", tags=["MigDB Database"],
    summary="Update a database connection",
    description="Updates an existing database connection record with new credentials in the CONN table.")
def db_conn_edit(body: DbConnRequest):
    msg = ''
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            'INSERT OR REPLACE INTO CONN VALUES(:dbname,:user,:passwd,:servicename)',
            {
                "dbname":      body.dbname,
                "user":        body.username,
                "passwd":      cipher.encrypt(body.passwd),
                "servicename": body.servicename,
            }
        )
        msg = 'Database Details Updated'
        conn.commit()

    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            cursor.close()
            conn.close()

    return [msg]

@app.delete("/api/v2/db/conn", tags=["MigDB Database"],
    summary="Delete a database connection",
    description="Removes a database connection record from the CONN table by database name.")
def db_conn_delete(body: DbConnRequest):
    msg = ''
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            'DELETE FROM CONN WHERE dbname=:dbname',
            {"dbname": body.dbname}
        )
        msg = 'Database Details Deleted'
        conn.commit()

    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            cursor.close()
            conn.close()

    return [msg]

class SelectDBDetRequest(BaseModel):
    dbname: str

@app.post("/api/v2/select-db-det", tags=["MigDB Database"],
    summary="Get database connection details",
    description="Fetches the username and service name for a given database name from the CONN table.")
def select_db_det(body: SelectDBDetRequest):
    msg = []
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT user, servicename FROM CONN WHERE dbname=:dbname',
            {"dbname": body.dbname}
        )
        db_row = cursor.fetchone()
        if db_row:
            msg.append({'user': db_row[0], 'servicename': db_row[1]})

    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            cursor.close()
            conn.close()

    return [msg]


@app.get("/api/v2/db-det", tags=["MigDB Database"],
    summary="List all database connections",
    description="Returns all database names registered in the CONN table.")
def db_det():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query('SELECT dbname FROM CONN', conn)
    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

    return [df.to_dict('records')]

@app.get("/api/v2/rep-type", tags=["MigDB Replicat Management"],
    summary="Get replicat types and PIDs",
    description="Runs GGSCI info replicat and returns each replicat's name, type (classic, integrated, or parallel), and process ID.")
def rep_type():
    info_rep = subprocess.getoutput("echo -e 'info replicat *'|" + ggsci_bin)

    rep_data = []
    rep_name = None
    rep_type = None

    for line in info_rep.splitlines():
        if re.search('REPLICAT', line, re.IGNORECASE):
            rep_name = line.split()[1]
        elif re.search('INTEGRATED', line, re.IGNORECASE):
            rep_type = 'INTEGRATED'
        elif re.search('Parallel', line, re.IGNORECASE):
            rep_type = 'PARALLEL'

        if re.search('Process', line, re.IGNORECASE):
            pid = line.split()[2]

            if rep_type == 'PARALLEL':
                rep_data.append({'RepName': rep_name, 'RepType': rep_type, 'PID': pid})
                rep_type = None
            elif rep_type is None:
                rep_data.append({'RepName': rep_name, 'RepType': 'CLASSIC', 'PID': pid})

    return [rep_data]

class CRTshootRequest(BaseModel):
    repName: str

@app.post("/api/v2/cr-tshoot", tags=["MigDB Replicat Management"],
    summary="Troubleshoot a replicat process",
    description="Looks up the replicat alias, connects to the database, and returns session details, ASH history, SQL full text, database info, and pstack thread output for diagnosis.")
def cr_tshoot(body: CRTshootRequest):
    rep_name = body.repName
    alias = None

    # Find alias from .prm file
    for prm_path in glob.glob(os.path.join(gg_home, 'dirprm', '*.prm')):
        name = os.path.basename(prm_path)
        if re.match(name, rep_name + '.prm', re.IGNORECASE):
            with open(prm_path, mode='r') as infile:
                for line in infile:
                    if re.match('useridalias', line, re.IGNORECASE):
                        alias = line.split()[1]

    if not alias:
        raise HTTPException(status_code=404, detail=f"No useridalias found for replicat '{rep_name}'")

    # Fetch DB credentials
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT user, passwd, servicename FROM CONN WHERE dbname=:dbname',
        {"dbname": alias}
    )
    db_row = cursor.fetchone()
    conn.close()

    if not db_row:
        raise HTTPException(status_code=404, detail=f"No DB credentials found for alias '{alias}'")

    user, passwd, servicename = db_row[0], cipher.decrypt(db_row[1]), db_row[2]

    # Connect to Oracle
    try:
        con = oracledb.connect(user=user, password=passwd, dsn=servicename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Oracle connection failed: {str(e)}")

    # DB details
    db_det_sql = """
        SELECT db.DBid, db.name DBNAME, db.platform_name, i.HOST_NAME HOST, i.VERSION,
               DECODE(regexp_substr(v.banner, '[^ ]+', 1, 4), 'Edition', 'Standard',
                      regexp_substr(v.banner, '[^ ]+', 1, 4)) DB_Edition,
               i.instance_number instance, db.database_role, db.current_scn
        FROM v$database db, v$instance i, v$version v
        WHERE banner LIKE 'Oracle%'
    """
    db_det_fetch = pd.read_sql_query(db_det_sql, con).to_dict('records')

    # PID list from .pcr file
    pidlist = []
    for file in glob.glob(os.path.join(gg_home, 'dirpcs', rep_name + '.pcr')):
        process = os.path.basename(file).split('.')[0]
        with open(file) as infile:
            for line in infile:
                line = line.strip()
                if len(line) > 2:
                    pid_match = re.search(r'\bPID\s+(\d+)\b', line)
                    if pid_match:
                        pidlist.append({'NAME': process, 'PROCESS': pid_match.group(1)})

    if not pidlist:
        raise HTTPException(status_code=404, detail=f"No PID files found for replicat '{rep_name}'")

    df = pd.DataFrame(pidlist, columns=['NAME', 'PROCESS'])
    pids = [p['PROCESS'] for p in pidlist]
    bind_names = [":" + str(i + 1) for i in range(len(pids))]

    # Session details
    session_sql = """
        SELECT s.sid sid, s.serial# serial, p.spid spid, s.sql_id sql_id,
               s.event event, s.last_call_et call, s.process process
        FROM gv$session s, gv$process p
        WHERE s.paddr = p.addr AND s.process IN (%s)
    """ % ",".join(bind_names)
    session_det_fetch = pd.read_sql_query(session_sql, con, params=[*pids])
    session_det_fetch = pd.merge(session_det_fetch, df).to_dict('records')

    if not session_det_fetch:
        raise HTTPException(status_code=404, detail="No session details found")

    first_session = session_det_fetch[0]

    # ASH details
    ash_sql = """
        SELECT INST_ID, NVL(event, 'ON CPU') event, COUNT(DISTINCT sample_time) AS TOTAL_COUNT
        FROM gv$active_session_history
        WHERE sample_time > sysdate - 30/24/60
          AND SESSION_ID = :1 AND SESSION_SERIAL# = :2
        GROUP BY inst_id, event
    """
    ash_det_fetch = pd.read_sql_query(
        ash_sql, con, params=[first_session['SID'], first_session['SERIAL']]
    ).astype(str).to_dict('records')

    # SQL full text
    sql_det_sql = "SELECT SQL_FULLTEXT FROM gv$sql WHERE sql_id = :1"
    sql_det_fetch = pd.read_sql_query(
        sql_det_sql, con, params=[first_session['SQL_ID']]
    ).astype(str).to_dict('records')

    con.close()

    # pstack
    pstack = {}
    pstack_output = subprocess.getoutput("pstack " + min(pids))
    thread_id = None
    for line in pstack_output.splitlines():
        if line.startswith('Thread '):
            thread_id = line.split()[1]
        elif thread_id is not None:
            pstack.setdefault(thread_id, []).append(line)


    return [db_det_fetch, session_det_fetch, pstack, ash_det_fetch, sql_det_fetch]

class PRTshootRequest(BaseModel):
    repName: str

@app.post("/api/v2/pr-tshoot", tags=["MigDB Replicat Management"],
    summary="Troubleshoot a parallel replicat process",
    description="Reads the replicat PRM file to find the alias, connects to the database, and returns session details, depinfo scheduler and transaction data, wait graph, pstack threads, and database info.")
def pr_tshoot(body: PRTshootRequest):
    rep_name = body.repName
    alias = None

    # Find alias from .prm file
    for prm_path in glob.glob(os.path.join(gg_home, 'dirprm', '*.prm')):
        name = os.path.basename(prm_path)
        if re.match(name, rep_name + '.prm', re.IGNORECASE):
            with open(prm_path, mode='r') as infile:
                for line in infile:
                    if re.match('useridalias', line, re.IGNORECASE):
                        alias = line.split()[1]

    if not alias:
        raise HTTPException(status_code=404, detail=f"No useridalias found for replicat '{rep_name}'")

    # Fetch DB credentials
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT user, passwd, servicename FROM CONN WHERE dbname=:dbname',
        {"dbname": alias}
    )
    db_row = cursor.fetchone()
    conn.close()

    if not db_row:
        raise HTTPException(status_code=404, detail=f"No DB credentials found for alias '{alias}'")

    user, passwd, servicename = db_row[0], cipher.decrypt(db_row[1]), db_row[2]

    # Connect to Oracle
    try:
        con = oracledb.connect(user=user, password=passwd, dsn=servicename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Oracle connection failed: {str(e)}")

    # DB details
    db_det_sql = """
        SELECT db.DBid, db.name DBNAME, db.platform_name, i.HOST_NAME HOST, i.VERSION,
               DECODE(regexp_substr(v.banner, '[^ ]+', 1, 4), 'Edition', 'Standard',
                      regexp_substr(v.banner, '[^ ]+', 1, 4)) DB_Edition,
               i.instance_number instance, db.database_role, db.current_scn
        FROM v$database db, v$instance i, v$version v
        WHERE banner LIKE 'Oracle%'
    """
    db_det_fetch = pd.read_sql_query(db_det_sql, con)

    # PID list from .pcr files
    pidlist = []
    for file in glob.glob(os.path.join(gg_home, 'dirpcs', rep_name + '*.pcr')):
        process = os.path.basename(file).split('.')[0]
        with open(file) as infile:
            for line in infile:
                line = line.strip()
                if len(line) > 2:
                    pid_match = re.search(r'PID\s+(\d+)', line)
                    if pid_match:
                        pidlist.append({'NAME': process, 'PROCESS': pid_match.group(1)})

    if not pidlist:
        raise HTTPException(status_code=404, detail=f"No PID files found for replicat '{rep_name}'")

    df = pd.DataFrame(pidlist, columns=['NAME', 'PROCESS'])
    pids = [p['PROCESS'] for p in pidlist]
    bind_names = [":" + str(i + 1) for i in range(len(pids))]

    # Session details
    session_sql = """
        SELECT s.sid sid, s.serial# serial, p.spid spid, s.sql_id sql_id,
               s.event event, s.last_call_et call, s.process process
        FROM gv$session s, gv$process p
        WHERE s.paddr = p.addr AND s.process IN (%s)
    """ % ",".join(bind_names)
    session_det_fetch = fetch_query_params(session_sql, con, cast_str=True, params=[*pids])
    session_det_fetch = pd.merge(session_det_fetch, df)

    # depinfo parsing
    dep_info = subprocess.getoutput("echo -e 'send '" + rep_name + ",depinfo |" + ggsci_bin)
    scheduler_list = []
    running_txn_list = []
    wait_info = []
    in_wait_section = False

    for line in dep_info.splitlines():
        if 'Scheduler' in line:
            scheduler_list.append(line.strip().rstrip(':').split()[1])
        elif 'Group' in line:
            parts = line.strip().split(':')
            txn = parts[1].split(',')
            running_txn_list.append({'Group': parts[0], 'Txn': txn})
        elif 'Waiting' in line:
            in_wait_section = True
        elif in_wait_section:
            wait_info.append(line.strip())

    # Wait graph
    txn_list = []
    wait_txn_list = []
    wait_graph = []
    for i, name in enumerate(wait_info):
        parts = name.split()
        if len(parts) > 1:
            txn_list.append(parts[3])
            wait_txn_list.append(parts[10])
            wait_graph.append({'id': i, 'start': parts[3], 'end': parts[10], 'category': '0'})

    txn_data = list(dict.fromkeys(txn_list))
    wait_txn_data = list(dict.fromkeys(wait_txn_list))

    node_data = (
        [{'id': name, 'category': 'Txn'}     for name in txn_data] +
        [{'id': name, 'category': 'WaitTxn'} for name in wait_txn_data]
    )

    con.close()

    # pstack
    pstack = {}
    thread_id = None
    for line in subprocess.getoutput("pstack " + min(pids)).splitlines():
        if line.startswith('Thread '):
            thread_id = line.split()[1]
        elif thread_id:
            pstack.setdefault(thread_id, []).append(line)

    return [
        db_det_fetch.to_dict('records'),
        session_det_fetch.to_dict('records'),
        scheduler_list,
        running_txn_list,
        node_data,
        wait_graph,
        pstack,
    ]

class ReqArchLogRequest(BaseModel):
    dbname: str
    req_scn: int

@app.post("/api/v2/req-arch-log", tags=["MigDB Database"],
    summary="Get archived log details for an SCN",
    description="Queries the source database for archived log files whose SCN range covers the requested SCN and returns the matching log details.")
def req_arch_log(body: ReqArchLogRequest):
    con = selectConn(body.dbname)[0]

    try:
        archive_log_sql = """
            SELECT NAME, THREAD#, SEQUENCE#, FIRST_TIME, NEXT_TIME,
                   FIRST_CHANGE#, NEXT_CHANGE#, DELETED
            FROM v$archived_log
            WHERE :req_scn BETWEEN FIRST_CHANGE# AND NEXT_CHANGE#
        """
        archive_log_fetch = pd.read_sql_query(
            archive_log_sql, con, params=[body.req_scn]
        ).astype(str).to_dict('records')

    except oracledb.DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if con:
            con.close()

    return [archive_log_fetch]

class IETshootRequest(BaseModel):
    dbname: str

@app.post("/api/v2/ie-tshoot", tags=["MigDB Extract Management"],
    summary="Troubleshoot an integrated extract process",
    description="Connects to the source database and returns extract capture status, parameters, LogMiner memory, streams pool stats, long running transactions, reader/builder/preparer/merger events and ASH data based on the database version.")
def ie_tshoot(body: IETshootRequest):
        val = selectConn(body.dbname)
        con = val[0]
        db_main_ver = val[1]
        db_minor_ver = val[2]
        if 'ORA-' in db_main_ver:
            return {"error": db_main_ver}
        try:
                db_det = '''SELECT db.DBid,db.name, db.platform_name  ,i.HOST_NAME HOST, i.VERSION,
                           DECODE(regexp_substr(v.banner, '[^ ]+', 1, 4),'Edition','Standard',regexp_substr(v.banner, '[^ ]+', 1, 4)) DB_Edition,
                           i.instance_number instance,db.database_role,db.current_scn, db.min_required_capture_change# min_required_capture_change
                    from v$database db,v$instance i, v$version v
                    where banner like 'Oracle%' '''
                db_det_fetch = pd.read_sql_query(db_det, con)
                db_det = db_det_fetch.to_dict('records')
                if int(db_main_ver) == 11:
                    ext_stat = '''select  SYSDATE Current_time,c.client_name extract_name,c.capture_name,
                         c.capture_user,
                         c.capture_type,
                         decode(cp.value,'N','NO', 'YES') Real_time_mine,
                         c.version,
                         c.required_checkpoint_scn,
                         (case
                          when g.sid=g.server_sid and g.serial#=g.server_serial# then 'V2'
                          else 'V1'
                          end) protocol,
                          c.logminer_id,
                          o.created registered,
                          o.last_ddl_time,
                          c.status,
                          g.STATE State,
                         (SYSDATE- g.capture_message_create_time)*86400 capture_lag,
                         g.bytes_of_redo_mined/1024/1024 mined_MB,
                         g.bytes_sent/1024/1024 sent_MB,
                         g.startup_time,
                         g.inst_id,
                         c.source_database
                         from dba_capture c, dba_objects o,
                              gv$goldengate_capture g,
                              dba_capture_parameters cp
                         where
                              c.capture_name=g.capture_name
                              and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                              and c.status='ENABLED' and c.purpose='GoldenGate Capture'
                              and c.capture_name = o.object_name
                              and c.capture_name=g.capture_name
                         union all
                         select  SYSDATE Current_time,c.client_name extract_name,c.capture_name,
                         c.capture_user,
                         c.capture_type,
                         decode(cp.value, 'N','NO', 'YES') Real_time_mine,
                         c.version,
                         c.required_checkpoint_scn,
                         'Unavailable',
                         c.logminer_id,
                         o.created registered,
                         o.last_ddl_time,
                         c.status,
                         'Unavailable',
                         NULL,
                         NULL,
                         NULL,
                         NULL,
                         NULL,
                         c.source_database
                         from dba_capture c, dba_objects o,
                              dba_capture_parameters cp
                         where
                         c.status in ('DISABLED','ABORTED') and c.purpose='GoldenGate Capture'
                         and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                         and c.capture_name = o.object_name
                         order by extract_name'''
                    ext_params = '''select cp.capture_name,substr(cp.capture_name,9,8)  extract_name,
                                   max(case when parameter='PARALLELISM' then value end) parallelism
                                  ,max(case when parameter='MAX_SGA_SIZE' then value end) max_sga_size
                                  ,max(case when parameter='EXCLUDETAG' then value end) excludetag
                                  ,max(case when parameter='EXCLUDEUSER' then value end) excludeuser
                                  ,max(case when parameter='GETAPPLOPS' then value end) getapplops
                                  ,max(case when parameter='GETREPLICATES' then value end) getreplicates
                                  ,max(case when parameter='_CHECKPOINT_FREQUENCY' then value end) checkpoint_frequency
                            from dba_capture_parameters cp, dba_capture c where c.capture_name=cp.capture_name
                                 and c.purpose='GoldenGate Capture'
                            group by cp.capture_name'''
                elif int(db_main_ver) == 12 and int(db_minor_ver) == 1:
                    ext_stat = '''select  SYSDATE Current_time,  c.client_name extract_name,c.capture_name,
                                 c.capture_user,
                                 c.capture_type,
                                 decode(cp.value,'N','NO', 'YES') Real_time_mine,
                                 c.version,
                                 c.required_checkpoint_scn,
                                 (case
                                  when g.sid=g.server_sid and g.serial#=g.server_serial# then 'V2'
                                  else 'V1'
                                  end) protocol,
                                 c.logminer_id,
                                 o.created registered,
                                 o.last_ddl_time,
                                 c.status,
                                 g.STATE  State,
                                 (SYSDATE- g.capture_message_create_time)*86400 capture_lag,
                                 g.bytes_of_redo_mined/1024/1024 mined_MB,
                                 g.bytes_sent/1024/1024 sent_MB,
                                 g.startup_time,
                                 g.con_id,
                                 g.inst_id,
                                 c.source_database
                         from cdb_capture c, cdb_objects o,
                              gv$goldengate_capture g,
                              cdb_capture_parameters cp
                         where
                              c.capture_name=g.capture_name
                              and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                              and c.status='ENABLED'  and c.purpose='GoldenGate Capture'
                              and c.capture_name=o.object_name
                              and c.capture_name=g.capture_name
                         union all
                         select  SYSDATE Current_time, c.client_name extract_name,c.capture_name,
                                 c.capture_user,
                                 c.capture_type,
                                 decode(cp.value, 'N','NO', 'YES') Real_time_mine,
                                 c.version,
                                 c.required_checkpoint_scn,
                                 'Unavailable',
                                 c.logminer_id,
                                 o.created registered,
                                 o.last_ddl_time,
                                 c.status,
                                 'Unavailable',
                                 NULL,
                                 NULL,
                                 NULL,
                                 NULL,
                                 NULL,
                                 NULL,
                                 c.source_database
                         from cdb_capture c, cdb_objects o,
                              cdb_capture_parameters cp
                         where
                              c.status in ('DISABLED', 'ABORTED') and c.purpose='GoldenGate Capture'
                              and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                              and c.capture_name=o.object_name
                              order by extract_name'''
                    ext_params = '''select cp.capture_name,substr(cp.capture_name,9,8)  extract_name,
                                   max(case when parameter='PARALLELISM' then value end) parallelism
                                  ,max(case when parameter='MAX_SGA_SIZE' then value end) max_sga_size
                                  ,max(case when parameter='EXCLUDETAG' then value end) excludetag
                                  ,max(case when parameter='EXCLUDEUSER' then value end) excludeuser
                                  ,max(case when parameter='GETAPPLOPS' then value end) getapplops
                                  ,max(case when parameter='GETREPLICATES' then value end) getreplicates
                                  ,max(case when parameter='_CHECKPOINT_FREQUENCY' then value end) checkpoint_frequency
                            from cdb_capture_parameters cp, cdb_capture c where c.capture_name=cp.capture_name
                                 and c.purpose='GoldenGate Capture'
                            group by cp.capture_name'''
                elif int(db_main_ver) == 12 and int(db_minor_ver) == 2:
                    ext_stat = '''select  SYSDATE Current_time,  c.client_name extract_name,c.capture_name,
                                  c.capture_user,
                                  c.capture_type,
                                  decode(cp.value,'N','NO', 'YES') Real_time_mine,
                                  c.version,
                                  c.required_checkpoint_scn,
                                  (case
                                   when g.sid=g.server_sid and g.serial#=g.server_serial# then 'V2'
                                   else 'V1'
                                   end) protocol,
                                  c.logminer_id,
                                  o.created registered,
                                  o.last_ddl_time,
                                  c.status,
                                  g.STATE State,
                                  (SYSDATE- g.capture_message_create_time)*86400 capture_lag,
                                  g.bytes_of_redo_mined/1024/1024 mined_MB,
                                  g.bytes_sent/1024/1024 sent_MB,
                                  g.startup_time,
                                  g.con_id,
                                  g.inst_id,
                                  c.source_database
                          from cdb_capture c, cdb_objects o,
                               gv$goldengate_capture g,
                               cdb_capture_parameters cp
                          where
                               c.capture_name=g.capture_name
                               and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                               and c.status='ENABLED'  and c.purpose='GoldenGate Capture'
                               and c.capture_name=o.object_name
                               and c.capture_name=g.capture_name
                          union all
                          select  SYSDATE Current_time, c.client_name extract_name,c.capture_name,
                                  c.capture_user,
                                  c.capture_type,
                                  decode(cp.value, 'N','NO', 'YES') Real_time_mine,
                                  c.version,
                                  c.required_checkpoint_scn,
                                  'Unavailable',
                                  c.logminer_id,
                                  o.created registered,
                                  o.last_ddl_time,
                                  c.status,
                                  'Unavailable',
                                  NULL,
                                  NULL,
                                  NULL,
                                  NULL,
                                  NULL,
                                  NULL,
                                  c.source_database
                          from cdb_capture c, cdb_objects o,
                               cdb_capture_parameters cp
                          where
                               c.status in ('DISABLED', 'ABORTED') and c.purpose='GoldenGate Capture'
                               and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                               and c.capture_name=o.object_name
                               order by extract_name'''
                    ext_params = '''select cp.capture_name,substr(cp.capture_name,9,8)  extract_name,
                                   max(case when parameter='PARALLELISM' then value end) parallelism
                                  ,max(case when parameter='MAX_SGA_SIZE' then value end) max_sga_size
                                  ,max(case when parameter='EXCLUDETAG' then value end) excludetag
                                  ,max(case when parameter='EXCLUDEUSER' then value end) excludeuser
                                  ,max(case when parameter='GETAPPLOPS' then value end) getapplops
                                  ,max(case when parameter='GETREPLICATES' then value end) getreplicates
                                  ,max(case when parameter='_CHECKPOINT_FREQUENCY' then value end) checkpoint_frequency
                            from cdb_capture_parameters cp, cdb_capture c where c.capture_name=cp.capture_name
                                 and c.purpose='GoldenGate Capture'
                           group by cp.capture_name'''
                elif int(db_main_ver) > 12:
                    ext_stat = '''select  SYSDATE Current_time,  c.client_name extract_name,c.capture_name,
                                  c.capture_user,
                                  c.capture_type,
                                  decode(cp.value,'N','NO', 'YES') Real_time_mine,
                                  c.version,
                                  c.required_checkpoint_scn,
                                  (case
                                   when g.sid=g.server_sid and g.serial#=g.server_serial# then 'V2'
                                   else 'V1'
                                   end) protocol,
                                  c.logminer_id,
                                  o.created registered,
                                  o.last_ddl_time,
                                  c.status,
                                  g.STATE State,
                                  (SYSDATE- g.capture_message_create_time)*86400 capture_lag,
                                  g.bytes_of_redo_mined/1024/1024 mined_MB,
                                  g.bytes_sent/1024/1024 sent_MB,
                                  g.startup_time,
                                  g.con_id,
                                  g.inst_id,
                                  c.source_database
                          from cdb_capture c, cdb_objects o,
                               gv$goldengate_capture g,
                               cdb_capture_parameters cp
                          where
                               c.capture_name=g.capture_name
                               and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                               and c.status='ENABLED'  and c.purpose='GoldenGate Capture'
                               and c.capture_name=o.object_name
                               and c.capture_name=g.capture_name
                          union all
                          select  SYSDATE Current_time, c.client_name extract_name,c.capture_name,
                                  c.capture_user,
                                  c.capture_type,
                                  decode(cp.value, 'N','NO', 'YES') Real_time_mine,
                                  c.version,
                                  c.required_checkpoint_scn,
                                  'Unavailable',
                                  c.logminer_id,
                                  o.created registered,
                                  o.last_ddl_time,
                                  c.status,
                                  'Unavailable',
                                  NULL,
                                  NULL,
                                  NULL,
                                  NULL,
                                  NULL,
                                  NULL,
                                  c.source_database
                          from cdb_capture c, cdb_objects o,
                               cdb_capture_parameters cp
                          where
                               c.status in ('DISABLED', 'ABORTED') and c.purpose='GoldenGate Capture'
                               and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                               and c.capture_name=o.object_name
                               order by extract_name'''
                    ext_params = '''select cp.capture_name,substr(cp.capture_name,9,8)  extract_name,
                                   max(case when parameter='PARALLELISM' then value end) parallelism
                                  ,max(case when parameter='MAX_SGA_SIZE' then value end) max_sga_size
                                  ,max(case when parameter='EXCLUDETAG' then value end) excludetag
                                  ,max(case when parameter='EXCLUDEUSER' then value end) excludeuser
                                  ,max(case when parameter='GETAPPLOPS' then value end) getapplops
                                  ,max(case when parameter='GETREPLICATES' then value end) getreplicates
                                  ,max(case when parameter='_CHECKPOINT_FREQUENCY' then value end) checkpoint_frequency
                            from cdb_capture_parameters cp, cdb_capture c where c.capture_name=cp.capture_name
                                 and c.purpose='GoldenGate Capture'
                           group by cp.capture_name'''
                ext_mem = '''select session_name, available_txn, delivered_txn,
                             available_txn-delivered_txn as difference,
                             builder_work_size, prepared_work_size,
                             used_memory_size , max_memory_size,
                             (used_memory_size/max_memory_size)*100 as used_mem_pct
                             FROM gv$logmnr_session order by session_name'''
                streams_pool = '''select inst_id, TOTAL_MEMORY_ALLOCATED/(1024*1024) as used_MB,  CURRENT_SIZE/(1024*1024) as  max_MB,
                          decode(current_size, 0,to_number(null),
                          (total_memory_allocated/current_size)*100) as pct_Streams_pool from gv$streams_pool_statistics'''
                streams_pool_stats = '''select capture_name,sga_used/(1024*1024) as used, sga_allocated/(1024*1024) as alloced
                                , (sga_used/sga_allocated)*100 as pct,total_messages_captured as msgs_captured,
                                total_messages_enqueued as msgs_enqueued from gv$goldengate_capture order by capture_name'''
                logmnr_mem = '''select session_name, l.USED_MEMORY_SIZE/(1024*1024) as used_MB, l.MAX_MEMORY_SIZE/(1024*1024) as max_MB,
                        (l.USED_MEMORY_SIZE/l.MAX_MEMORY_SIZE)*100 as pct_logminer_mem_used,s.current_size/(1024*1024) streams_size,decode(s.current_size, 0,
                        to_number(null),(l.used_memory_size/s.current_size)*100) pct_streams_pool
                        from gv$logmnr_session l, gv$streams_pool_statistics s
                        where l.inst_id=s.inst_id order by session_name'''

                long_running = '''select t.inst_id, sid||','||serial# sid,xidusn||'.'||xidslot||'.'||xidsqn xid,
                          (sysdate -  start_date ) * 1440 runlength ,t.start_scn,terminal,
                          program from gv$transaction t, gv$session s
                          where t.addr=s.taddr and (sysdate - start_date) * 1440 > 20 order by runlength desc'''
                reader_event = '''SELECT c.capture_name || ' - reader' as logminer_reader_name,
                                 lp.sid,lp.SERIAL# SERIAL,lp.SPID,sess_capture.p2text,sess_capture.p2,sess_capture.p3text,sess_capture.p3,LATCHWAIT, LATCHSPIN,
                                 sess_capture.event EVENT
                          FROM (SELECT SID,
                                SERIAL#,
                                EVENT,
                                p2,p2text,p3,p3text
                                FROM  gv$session
                                GROUP BY sid, serial#, event , p2,p2text,p3,p3text) sess_capture,
                          v$logmnr_process lp, v$goldengate_capture c
                          WHERE lp.SID = sess_capture.sid
                                AND lp.serial# = sess_capture.SERIAL#
                                AND lp.role = 'reader' and lp.session_id = c.logminer_id
                          ORDER BY logminer_reader_name'''
                reader_ash = '''SELECT c.inst_id, c.capture_name || ' - reader'|| lp.spid as logminer_reader_name
                              , ash_capture.event_count
                              , ash_total.total_count
                              , round(ash_capture.event_count*100/NULLIF(ash_total.total_count,0),2) as Percentage
                              , 'YES' busy
                              , nvl(ash_capture.event,'on CPU or wait on CPU') event
                        FROM (SELECT INST_ID, SESSION_ID, SESSION_SERIAL#, EVENT, COUNT(sample_time) AS EVENT_COUNT
                              FROM  gv$active_session_history
                              WHERE sample_time > sysdate - 30/24/60
                              GROUP BY inst_id, session_id, session_serial#, event) ash_capture
                          , (SELECT INST_ID, COUNT(DISTINCT sample_time) AS TOTAL_COUNT
                             FROM  gv$active_session_history
                             WHERE sample_time > sysdate - 30/24/60
                             group by inst_id) ash_total
                           , gv$logmnr_process lp
                           , gv$goldengate_capture c
                        WHERE lp.SID        = ash_capture.SESSION_ID
                        AND   lp.serial#    = ash_capture.SESSION_SERIAL#
                        AND   lp.role       = 'reader'
                        AND   lp.session_id = c.logminer_id
                        AND   c.inst_id = ash_capture.inst_id
                        AND   c.inst_id = ash_total.inst_id
                        AND   c.inst_id = lp.inst_id
                        ORDER BY c.inst_id, logminer_reader_name, Percentage'''

                builder_event = '''SELECT c.capture_name || ' - builder' as logminer_builder_name,
                                  lp.sid,lp.SERIAL# SERIAL,lp.SPID , LATCHWAIT, LATCHSPIN,
                                  sess_capture.event EVENT
                          FROM (SELECT SID,
                                SERIAL#,
                                EVENT
                                FROM  gv$session
                                GROUP BY sid, serial#, event) sess_capture,
                          v$logmnr_process lp, v$goldengate_capture c
                          WHERE lp.SID = sess_capture.sid
                                AND lp.serial# = sess_capture.SERIAL#
                                AND lp.role = 'builder' and lp.session_id = c.logminer_id
                          ORDER BY logminer_builder_name'''

                builder_ash = '''SELECT c.inst_id, c.capture_name || ' - builder'|| lp.spid as logminer_builder_name
                              , ash_capture.event_count
                              , ash_total.total_count
                              , round(ash_capture.event_count*100/NULLIF(ash_total.total_count,0),2) as Percentage
                              , 'YES' busy
                              , nvl(ash_capture.event,'on CPU or wait on CPU') event
                        FROM (SELECT INST_ID, SESSION_ID, SESSION_SERIAL#, EVENT, COUNT(sample_time) AS EVENT_COUNT
                              FROM  gv$active_session_history
                              WHERE sample_time > sysdate - 30/24/60
                              GROUP BY inst_id, session_id, session_serial#, event) ash_capture
                          , (SELECT INST_ID, COUNT(DISTINCT sample_time) AS TOTAL_COUNT
                             FROM  gv$active_session_history
                             WHERE sample_time > sysdate - 30/24/60
                             group by inst_id) ash_total
                           , gv$logmnr_process lp
                           , gv$goldengate_capture c
                        WHERE lp.SID        = ash_capture.SESSION_ID
                        AND   lp.serial#    = ash_capture.SESSION_SERIAL#
                        AND   lp.role       = 'builder'
                        AND   lp.session_id = c.logminer_id
                        AND   c.inst_id = ash_capture.inst_id
                        AND   c.inst_id = ash_total.inst_id
                        AND   c.inst_id = lp.inst_id
                        ORDER BY c.inst_id, logminer_builder_name, Percentage'''

                preparer_event = '''SELECT c.capture_name || ' - preparer' as logminer_preparer_name,
                                 lp.sid,lp.SERIAL# SERIAL,lp.SPID , LATCHWAIT, LATCHSPIN,
                                 sess_capture.event EVENT
                          FROM (SELECT SID,
                                SERIAL#,
                                EVENT
                                FROM  gv$session
                                GROUP BY sid, serial#, event) sess_capture,
                          v$logmnr_process lp, v$goldengate_capture c
                          WHERE lp.SID = sess_capture.sid
                                AND lp.serial# = sess_capture.SERIAL#
                                AND lp.role = 'preparer' and lp.session_id = c.logminer_id
                          ORDER BY logminer_preparer_name'''


                preparer_ash = '''SELECT c.inst_id, c.capture_name || ' - preparer'|| lp.spid as logminer_preparer_name
                              , ash_capture.event_count
                              , ash_total.total_count
                              , round(ash_capture.event_count*100/NULLIF(ash_total.total_count,0),2) as Percentage
                              , 'YES' busy
                              , nvl(ash_capture.event,'on CPU or wait on CPU') event
                        FROM (SELECT INST_ID, SESSION_ID, SESSION_SERIAL#, EVENT, COUNT(sample_time) AS EVENT_COUNT
                              FROM  gv$active_session_history
                              WHERE sample_time > sysdate - 30/24/60
                              GROUP BY inst_id, session_id, session_serial#, event) ash_capture
                          , (SELECT INST_ID, COUNT(DISTINCT sample_time) AS TOTAL_COUNT
                             FROM  gv$active_session_history
                             WHERE sample_time > sysdate - 30/24/60
                             group by inst_id) ash_total
                           , gv$logmnr_process lp
                           , gv$goldengate_capture c
                        WHERE lp.SID        = ash_capture.SESSION_ID
                        AND   lp.serial#    = ash_capture.SESSION_SERIAL#
                        AND   lp.role       = 'preparer'
                        AND   lp.session_id = c.logminer_id
                        AND   c.inst_id = ash_capture.inst_id
                        AND   c.inst_id = ash_total.inst_id
                        AND   c.inst_id = lp.inst_id
                        ORDER BY c.inst_id, logminer_preparer_name, Percentage'''

                merger_event = '''SELECT c.capture_name || ' - merger' as logminer_merger_name,
                                  lp.sid,lp.SERIAL# SERIAL,lp.SPID , LATCHWAIT, LATCHSPIN,
                                  sess_capture.event EVENT
                          FROM (SELECT SID,
                                SERIAL#,
                                EVENT
                                FROM  gv$session
                                GROUP BY sid, serial#, event) sess_capture,
                          v$logmnr_process lp, v$goldengate_capture c
                          WHERE lp.SID = sess_capture.sid
                                AND lp.serial# = sess_capture.SERIAL#
                                AND lp.role = 'merger' and lp.session_id = c.logminer_id
                          ORDER BY logminer_merger_name'''

                merger_ash = '''SELECT c.inst_id, c.capture_name || ' - merger' as logminer_merger_name
                              , ash_capture.event_count
                              , ash_total.total_count
                              , round(ash_capture.event_count*100/NULLIF(ash_total.total_count,0),2) as Percentage
                              , 'YES' busy
                              , nvl(ash_capture.event,'on CPU or wait on CPU') event
                        FROM (SELECT INST_ID, SESSION_ID, SESSION_SERIAL#, EVENT, COUNT(sample_time) AS EVENT_COUNT
                              FROM  gv$active_session_history
                              WHERE sample_time > sysdate - 30/24/60
                              GROUP BY inst_id, session_id, session_serial#, event) ash_capture
                          , (SELECT INST_ID, COUNT(DISTINCT sample_time) AS TOTAL_COUNT
                             FROM  gv$active_session_history
                             WHERE sample_time > sysdate - 30/24/60
                             group by inst_id) ash_total
                           , gv$logmnr_process lp
                           , gv$goldengate_capture c
                        WHERE lp.SID        = ash_capture.SESSION_ID
                        AND   lp.serial#    = ash_capture.SESSION_SERIAL#
                        AND   lp.role       = 'merger'
                        AND   lp.session_id = c.logminer_id
                        AND   c.inst_id = ash_capture.inst_id
                        AND   c.inst_id = ash_total.inst_id
                        AND   c.inst_id = lp.inst_id
                        ORDER BY c.inst_id, logminer_merger_name, Percentage'''

                logmnr_stats = '''select c.capture_name, name, value
                          from gv$goldengate_capture c, gv$logmnr_stats l
                          where c.logminer_id = l.session_id
                          and c.inst_id = l.inst_id
                          and name in ('bytes paged out', 'pageout time (seconds)' , 'bytes of redo mined', 'bytes checkpointed' , 'checkpoint time (seconds)', 'resume from low memory' , 'distinct txns in queue')
                          order by capture_name,name'''
                ext_stat_fetch = fetch_query(ext_stat,con,cast_str=True)
                ext_params_fetch = fetch_query(ext_params,con,cast_str=True)
                ext_mem_fetch = fetch_query(ext_mem,con,cast_str=True)
                streams_pool_fetch = fetch_query(streams_pool,con,cast_str=True)
                streams_pool_stats_fetch = fetch_query(streams_pool_stats,con,cast_str=True)
                logmnr_mem_fetch = fetch_query(logmnr_mem,con,cast_str=True)
                long_running_fetch = fetch_query(long_running,con,cast_str=True)
                reader_event_fetch = fetch_query(reader_event,con,cast_str=True)
                builder_event_fetch = fetch_query(builder_event,con,cast_str=True)
                preparer_event_fetch = fetch_query(preparer_event,con,cast_str=True)
                logmnr_stats_fetch = fetch_query(logmnr_stats,con,cast_str=True)
                merger_event_fetch = fetch_query(merger_event,con,cast_str=True)
                reader_ash_fetch = fetch_query(reader_ash,con,cast_str=True)
                merger_ash_fetch = fetch_query(merger_ash,con,cast_str=True)
                preparer_ash_fetch = fetch_query(preparer_ash , con , cast_str=True)
                builder_ash_fetch = fetch_query(builder_ash , con , cast_str=True)


        except Exception as e:
                con.close()
                logger.error(str(e))
                return {"error": str(e)}
        finally:
                if con:
                    con.close()
        return {
                "ext_stat": ext_stat_fetch,
                "ext_params": ext_params_fetch,
                "ext_mem": ext_mem_fetch,
                "streams_pool" : streams_pool_fetch,
                "streams_pool_stats" : streams_pool_stats_fetch,
                "logmnr_mem" : logmnr_mem_fetch,
                "long_running" : long_running_fetch,
                "reader_event" : reader_event_fetch ,
                "builder_event" : builder_event_fetch,
                "preparer_event" : preparer_event_fetch,
                "db_main_ver" : db_main_ver,
                "db_minor_ver" : db_minor_ver, 
                "db_det" : db_det, 
                "logmnr_stats" : logmnr_stats_fetch, 
                "merger_event" : merger_event_fetch, 
                "reader_ash" : reader_ash_fetch,
                "merger_ash" : merger_ash_fetch,
                "preparer_ash" : preparer_ash_fetch,
                "builder_ash" : builder_ash_fetch
              }

class IRTshootRequest(BaseModel):
    dbname: str

def fetch_query(query: str, con, cast_str: bool = True):
    try:
        df = pd.read_sql_query(query, con)
        if cast_str:
            df = df.fillna('-').astype(str)
        else:
            df = df.where(pd.notnull(df), None)
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"fetch_query failed for query={query!r}: {e}")
        return [] 
 
SQL_DB_DET = """
    SELECT db.DBid, db.name, db.platform_name, i.HOST_NAME HOST, i.VERSION,
           DECODE(regexp_substr(v.banner,'[^ ]+',1,4),'Edition','Standard',
                  regexp_substr(v.banner,'[^ ]+',1,4)) DB_Edition,
           i.instance_number instance, db.database_role
    FROM v$database db, v$instance i, v$version v
    WHERE banner LIKE 'Oracle%'
"""
 
SQL_REP_PARAMS_11 = """
    SELECT apply_name, substr(apply_name,5,8) replicat_name,
           max(CASE WHEN parameter='PARALLELISM'               THEN value END) parallelism,
           max(CASE WHEN parameter='MAX_PARALLELISM'           THEN value END) max_parallelism,
           max(CASE WHEN parameter='COMMIT_SERIALIZATION'      THEN value END) commit_serialization,
           max(CASE WHEN parameter='EAGER_SIZE'                THEN value END) eager_size,
           max(CASE WHEN parameter='_DML_REORDER'              THEN value END) batchsql,
           max(CASE WHEN parameter='_BATCHTRANSOPS'            THEN value END) batchtransops,
           max(CASE WHEN parameter='BATCHSQL_MODE'             THEN value END) batchsql_mode,
           max(CASE WHEN parameter='MAX_SGA_SIZE'              THEN value END) max_sga_size,
           max(CASE WHEN parameter='OPTIMIZE_PROGRESS_TABLE'   THEN value END) optimize_progress_table
    FROM dba_apply_parameters ap, dba_goldengate_inbound ib
    WHERE ib.server_name = ap.apply_name
    GROUP BY apply_name
"""
 
SQL_REP_PARAMS_12 = SQL_REP_PARAMS_11.replace(
    "dba_apply_parameters ap, dba_goldengate_inbound ib",
    "cdb_apply_parameters ap, cdb_goldengate_inbound ib",
)
 
SQL_REP_INBOUND_11 = """
    SELECT server_name, processed_low_position, applied_low_position,
           applied_high_position, oldest_position, applied_low_scn,
           applied_time, applied_message_create_time, logbsn
    FROM dba_gg_inbound_progress
    ORDER BY server_name
"""
 
SQL_REP_INBOUND_12 = """
    SELECT con_id, server_name, processed_low_position, applied_low_position,
           applied_high_position, oldest_position, applied_low_scn,
           applied_time, applied_message_create_time, logbsn
    FROM cdb_gg_inbound_progress
    ORDER BY server_name
"""
 
SQL_REP_SUMMARY_11 = """
    SELECT sysdate Current_time, ib.replicat_name, ib.server_name, ib.apply_user,
           ib.status, o.created registered, o.last_ddl_time, a.apply_tag,
           r.state ReceiverState, g.state, g.active_server_count,
           g.unassigned_complete_txns, g.lwm_message_create_time lwm,
           NVL(Round((g.hwm_message_create_time-g.lwm_message_create_time)*24*3600,2),0) SourceTSrange,
           g.lwm_time apply_time,
           NVL(Round((g.hwm_time-g.lwm_time)*24*3600,2),0) ApplyTSrange,
           g.startup_time, g.inst_id
    FROM dba_goldengate_inbound ib, dba_objects o, dba_apply a,
         gv$gg_apply_coordinator g, gv$gg_apply_receiver r
    WHERE ib.server_name = g.apply_name AND ib.status = 'ATTACHED'
      AND ib.server_name = o.object_name AND ib.server_name = g.apply_name
      AND ib.server_name = r.apply_name  AND ib.server_name = a.apply_name
    UNION ALL
    SELECT sysdate Current_time, ib.replicat_name, ib.server_name, ib.apply_user,
           ib.status, o.created registered, o.last_ddl_time, a.apply_tag,
           'Unavailable', null, null, null,
           pg.applied_message_create_time, null SourceTSrange,
           pg.applied_time, null ApplyTSrange, null, null
    FROM dba_goldengate_inbound ib, dba_objects o, dba_gg_inbound_progress pg, dba_apply a
    WHERE ib.status != 'ATTACHED' AND ib.server_name = o.object_name
      AND ib.server_name = a.apply_name AND ib.server_name = pg.server_name(+)
    ORDER BY replicat_name
"""
 
SQL_REP_SUMMARY_12 = """
    SELECT sysdate Current_time, o.con_id, ib.replicat_name, ib.server_name,
           ib.apply_user, ib.status, o.created registered, o.last_ddl_time,
           a.apply_tag, r.state ReceiverState, g.state, g.active_server_count,
           g.unassigned_complete_txns, g.lwm_message_create_time lwm,
           NVL(Round((g.hwm_message_create_time-g.lwm_message_create_time)*24*3600,2),0) SourceTSrange,
           g.lwm_time apply_time,
           NVL(Round((g.hwm_time-g.lwm_time)*24*3600,2),0) ApplyTSrange,
           g.startup_time, g.inst_id
    FROM cdb_goldengate_inbound ib, cdb_objects o, cdb_apply a,
         gv$gg_apply_coordinator g, gv$gg_apply_receiver r
    WHERE ib.server_name = g.apply_name AND ib.status = 'ATTACHED'
      AND ib.server_name = o.object_name AND ib.server_name = g.apply_name
      AND ib.server_name = r.apply_name  AND ib.server_name = a.apply_name
    UNION ALL
    SELECT sysdate Current_time, o.con_id, ib.replicat_name, ib.server_name,
           ib.apply_user, ib.status, o.created registered, o.last_ddl_time,
           a.apply_tag, 'Unavailable' ReceiverState, null State,
           null server_count, null unassigned_complete_txns,
           pg.applied_message_create_time, null SourceTSrange,
           pg.applied_time, null ApplyTSrange, null startup_time, null inst_id
    FROM cdb_goldengate_inbound ib, cdb_objects o, cdb_apply a, cdb_gg_inbound_progress pg
    WHERE ib.status != 'ATTACHED' AND ib.server_name = a.apply_name
      AND ib.server_name = o.object_name AND ib.server_name = pg.server_name(+)
    ORDER BY replicat_name
"""
 
SQL_APPLY_READER_11 = """
    SELECT ap.APPLY_NAME, s.sid, s.serial# serial,
           SUBSTR(s.PROGRAM,INSTR(S.PROGRAM,'(')+1,4) PROCESS_NAME,
           r.ELAPSED_DEQUEUE_TIME, r.ELAPSED_SCHEDULE_TIME, r.STATE,
           r.oldest_transaction_id
    FROM gV$GG_APPLY_READER r, gV$SESSION s, DBA_APPLY ap
    WHERE r.SID = s.SID AND r.SERIAL# = s.SERIAL#
      AND r.inst_id = s.inst_id AND r.APPLY_NAME = ap.APPLY_NAME
    ORDER BY ap.apply_name
"""
 
SQL_APPLY_READER_12 = SQL_APPLY_READER_11.replace("DBA_APPLY ap", "CDB_APPLY ap")
 
SQL_APPLY_COORDINATOR_11 = """
    SELECT ap.APPLY_NAME, s.sid, s.serial# serial,
           SUBSTR(s.PROGRAM,INSTR(S.PROGRAM,'(')+1,4) PROCESS,
           c.STARTUP_TIME, c.ELAPSED_SCHEDULE_TIME, c.STATE,
           c.TOTAL_RECEIVED RECEIVED, c.TOTAL_ASSIGNED ASSIGNED,
           c.unassigned_complete_txns unassigned, c.TOTAL_APPLIED APPLIED,
           c.TOTAL_ERRORS ERRORS, c.total_ignored, c.total_rollbacks
    FROM gV$GG_APPLY_COORDINATOR c, gV$SESSION s, dba_APPLY ap
    WHERE c.SID = s.SID AND c.SERIAL# = s.SERIAL#
      AND c.APPLY_NAME = ap.APPLY_NAME
    ORDER BY ap.apply_name
"""
 
SQL_APPLY_COORDINATOR_12 = SQL_APPLY_COORDINATOR_11.replace(
    "dba_APPLY ap", "cdb_APPLY ap"
)
 
SQL_APPLY_SERVER_ASH = """
    SELECT a.inst_id,
           a.apply_name || ' - ' || a.server_id apply_name,
           ash.event_count, ash_total.total_count,
           ash.event_count*100/NULLIF(ash_total.total_count,0) Percentage,
           'YES' busy,
           NVL(ash.event,'on CPU or wait on CPU') event
    FROM (SELECT inst_id, SESSION_ID, SESSION_SERIAL#, EVENT,
                 COUNT(sample_time) EVENT_COUNT
          FROM gv$active_session_history
          WHERE sample_time > sysdate - 30/24/60
          GROUP BY inst_id, session_id, session_serial#, event) ash,
         (SELECT inst_id, COUNT(DISTINCT sample_time) TOTAL_COUNT
          FROM gv$active_session_history
          WHERE sample_time > sysdate - 30/24/60
          GROUP BY inst_id) ash_total,
         gv$gg_apply_server a
    WHERE a.sid = ash.SESSION_ID AND a.serial# = ash.SESSION_SERIAL#
      AND a.inst_id = ash.inst_id AND a.inst_id = ash_total.inst_id
    ORDER BY a.inst_id, apply_name, to_number(Percentage)
"""
 
SQL_APPLY_RECEIVER = """
    SELECT inst_id, apply_name, sid, serial# serial, startup_time,
           total_messages_received, total_available_messages, state,
           last_received_msg_position, acknowledgement_position
    FROM gv$gg_apply_receiver
    ORDER BY inst_id, apply_name
"""
 
SQL_APPLY_RECEIVER_ASH = """
    SELECT a.inst_id, a.apply_name, ash.event_count, ash_total.total_count,
           ash.event_count*100/NULLIF(ash_total.total_count,0) Percentage,
           DECODE(ash.event,'Streams AQ: enqueue blocked on low memory','NO',
                  'Streams AQ: enqueue blocked due to flow control','NO',
                  'REPL Capture/Apply: flow control','NO',
                  'REPL Capture/Apply: memory','NO','YES') busy,
           nvl(ash.event,'on CPU or wait on CPU') event
    FROM (SELECT inst_id, SESSION_ID, SESSION_SERIAL#, EVENT,
                 COUNT(sample_time) EVENT_COUNT
          FROM gv$active_session_history
          WHERE sample_time > sysdate - 2
          GROUP BY inst_id, session_id, session_serial#, event) ash,
         (SELECT inst_id, COUNT(DISTINCT sample_time) TOTAL_COUNT
          FROM gv$active_session_history
          WHERE sample_time > sysdate - 2
          GROUP BY inst_id) ash_total,
         gv$gg_apply_receiver a
    WHERE a.sid = ash.SESSION_ID AND a.serial# = ash.SESSION_SERIAL#
      AND a.source_database_name = 'replicat'
      AND a.inst_id = ash.inst_id AND a.inst_id = ash_total.inst_id
    ORDER BY a.inst_id, a.apply_name, to_number(Percentage)
"""
 
SQL_APPLY_READER_ASH = """
    SELECT a.inst_id, a.apply_name, ash.event_count, ash_total.total_count,
           ash.event_count*100/NULLIF(ash_total.total_count,0) Percentage,
           DECODE(ash.event,'rdbms ipc message','NO','YES') busy,
           NVL(ash.event,'on CPU or wait on CPU') event
    FROM (SELECT inst_id, SESSION_ID, SESSION_SERIAL#, EVENT,
                 COUNT(sample_time) EVENT_COUNT
          FROM gv$active_session_history
          WHERE sample_time > sysdate - 1
          GROUP BY inst_id, session_id, session_serial#, event) ash,
         (SELECT inst_id, COUNT(DISTINCT sample_time) TOTAL_COUNT
          FROM gv$active_session_history
          WHERE sample_time > sysdate - 1
          GROUP BY inst_id) ash_total,
         gv$gg_apply_reader a
    WHERE a.sid = ash.SESSION_ID AND a.serial# = ash.SESSION_SERIAL#
      AND a.inst_id = ash.inst_id AND a.inst_id = ash_total.inst_id
    ORDER BY a.inst_id, apply_name, to_number(Percentage)
"""
 
SQL_APPLY_READER_INFO = """
    SELECT APPLY_NAME,
           ((DEQUEUE_TIME - DEQUEUED_MESSAGE_CREATE_TIME)*86400) LATENCY,
           TO_CHAR(DEQUEUED_MESSAGE_CREATE_TIME,'HH24:MI:SS MM/DD') DEQUEUED_MESSAGE_CREATE_TIME,
           TO_CHAR(DEQUEUE_TIME,'HH24:MI:SS MM/DD') LAST_DEQUEUE,
           DEQUEUED_POSITION
    FROM gV$GG_APPLY_READER
    ORDER BY apply_name
"""
 
SQL_APPLY_READER_LCR_DEP = """
    SELECT r.apply_name, r.total_messages_dequeued, r.total_lcrs_with_dep,
           r.total_lcrs_with_WMdep, c.total_assigned, c.total_wait_deps,
           c.total_wait_commits,
           100*(r.total_lcrs_with_dep)/nullif((r.total_messages_dequeued-c.total_assigned),0) WaitDep_perc_msgs,
           100*(r.total_lcrs_with_WMdep)/nullif((c.total_received),0) WM_WaitDep_perc_msgs
    FROM gv$gg_apply_reader r, gv$gg_apply_coordinator c
    WHERE r.apply_name = c.apply_name AND r.inst_id = c.inst_id
    ORDER BY r.apply_name
"""
 
SQL_APPLY_COORDINATOR_INFO = """
    SELECT apply_name, total_applied, total_wait_deps, total_wait_commits,
           (100*total_wait_deps/NULLIF(total_applied,0))    WAITDEP,
           (100*total_wait_commits/NULLIF(total_applied,0)) COMMITDEP
    FROM gv$gg_apply_coordinator
    ORDER BY apply_name
"""
 
SQL_APPLY_SERVER_AGG_STATS = """
    SELECT a.inst_id, a.apply_name, a.server_id,
           substr(s.PROGRAM,INSTR(S.PROGRAM,'(')+1,4) PROCESS_NAME,
           a.sid, a.serial# serial, a.STATE,
           a.xidusn||'.'||a.xidslt||'.'||a.xidsqn CURRENT_TXN,
           a.TOTAL_ASSIGNED ASSIGNED, a.TOTAL_MESSAGES_APPLIED msg_APPLIED,
           a.MESSAGE_SEQUENCE, a.lcr_retry_iteration, a.txn_retry_iteration,
           a.total_lcrs_retried, a.total_txns_retried, a.total_txns_recorded,
           a.elapsed_apply_time, a.apply_time, s.logon_time
    FROM gV$GG_APPLY_SERVER a, gV$SESSION s
    WHERE a.SID = s.SID AND a.SERIAL# = s.SERIAL# AND a.inst_id = s.inst_id
    ORDER BY a.apply_name, a.server_id
"""
 
SQL_APPLY_SERVER_INFO = """
    SELECT a.inst_id, a.apply_name, a.server_id, a.state,
           a.total_messages_applied, q.sql_id, q.sql_fulltext sqltext,
           q.executions, q.rows_processed,
           q.rows_processed/decode(q.executions,0,1,executions) rows_per_exec,
           q.optimizer_mode, optimizer_cost
    FROM gv$GG_apply_server a, gv$sql q, gv$session s
    WHERE a.sid = s.sid AND a.serial# = s.serial#
      AND a.inst_id = s.inst_id AND s.sql_hash_value = q.hash_value
      AND s.sql_address = q.address AND s.sql_id = q.sql_id
      AND s.inst_id = q.inst_id AND a.inst_id = q.inst_id
    ORDER BY a.apply_name, a.server_id
"""
 
SQL_APPLY_SERVER_TXN = """
    SELECT a.inst_id, a.APPLY_NAME,
           SUBSTR(s.PROGRAM,INSTR(S.PROGRAM,'(')+1,4) PROCESS_NAME,
           server_id, a.state, a.sid, a.serial# serial,
           a.TOTAL_ASSIGNED ASSIGNED, a.TOTAL_MESSAGES_APPLIED msg_APPLIED,
           xidusn||'.'||xidslt||'.'||xidsqn CURRENT_TXN,
           commit_position,
           dep_xidusn||'.'||dep_xidslt||'.'||dep_xidsqn DEPENDENT_TXN,
           dep_commit_position, message_sequence, apply_time
    FROM gV$GG_APPLY_SERVER a, gV$SESSION s
    WHERE a.SID = s.SID AND a.SERIAL# = s.SERIAL# AND a.inst_id = s.inst_id
    ORDER BY a.apply_name, a.state
"""
 
SQL_APPLY_FTS_INFO = """
    SELECT DISTINCT sp1.object_owner||'.'||sp1.object_name table_name
    FROM gv$sqlarea sa, gv$sql_plan sp1
    WHERE sa.sql_id = sp1.sql_id AND sa.inst_id = sp1.inst_id
      AND sp1.depth < 2
      AND (sp1.object_owner, sp1.object_name, sp1.inst_id) IN
          (SELECT destination_table_owner, destination_table_name, inst_id
           FROM gv$goldengate_table_stats)
      AND sa.parsing_schema_name IN (SELECT username FROM DBA_GOLDENGATE_PRIVILEGES)
      AND (sa.action LIKE 'OGG%' OR sa.module LIKE 'OGG%' OR sa.module LIKE 'GoldenGate%')
      AND sa.command_type IN (3, 6, 7)
      AND 0 = (SELECT count(*) FROM gv$sql_plan sp2
               WHERE sp2.object_owner IN ('SYS','SYSTEM')
                 AND sp2.sql_id = sa.sql_id AND sp2.inst_id = sa.inst_id)
      AND 0 = (SELECT count(*) FROM gv$sql_plan sp2
               WHERE sp2.options IN ('UNIQUE SCAN')
                 AND sp2.sql_id = sa.sql_id AND sp2.inst_id = sa.inst_id)
"""
 
SQL_APPLY_FLOW = """
    SELECT TO_CHAR(sysdate,'YYYY-MM-DD HH24:MI:SS') mtime,
           rcv.inst_id, rcv.APPLY_NAME, rcv.STATE receiver_state,
           r.STATE reader_state,
           ROUND(r.SGA_USED/1024/1024,2) SGA_USED,
           ROUND(r.SGA_ALLOCATED/1024/1024,2) SGA_ALLOCATED,
           rcv.TOTAL_available_messages, rcv.TOTAL_MESSAGES_RECEIVED,
           r.TOTAL_MESSAGES_DEQUEUED, c.UNASSIGNED_COMPLETE_TXNS,
           (SELECT count(*) FROM gv$goldengate_transaction t
            WHERE t.component_name = c.apply_name AND t.inst_id = c.inst_id) open_txn,
           c.active_server_count,
           (SELECT count(1) FROM gv$gg_apply_server s
            WHERE s.state = 'EXECUTE TRANSACTION'
              AND s.apply_name = c.apply_name AND s.inst_id = c.inst_id) active_executing_count
    FROM gv$gg_apply_reader r, gv$gg_apply_receiver rcv, gv$gg_apply_coordinator c
    WHERE c.apply_name = rcv.apply_name AND c.apply_name = r.apply_name
      AND c.inst_id = rcv.inst_id AND c.inst_id = r.inst_id
    ORDER BY r.SGA_USED DESC
"""
 
SQL_APPLY_SERVER_WAITS = """
    SELECT a.inst_id, a.apply_name, a.server_id, w.event, w.seconds_in_wait secs
    FROM gv$GG_apply_server a, gv$session_wait w
    WHERE a.sid = w.sid AND a.inst_id = w.inst_id
    ORDER BY a.apply_name, a.server_id
"""
 
SQL_STREAMS_POOL = """
    SELECT inst_id,
           TOTAL_MEMORY_ALLOCATED/(1024*1024) used_MB,
           CURRENT_SIZE/(1024*1024) max_MB,
           decode(current_size,0,to_number(null),
                  (total_memory_allocated/current_size)*100) pct_Streams_pool
    FROM gv$streams_pool_statistics
"""
 
SQL_STREAMS_POOL_USAGE = """
    SELECT apr.inst_id, 'Replicat' process_type, apr.apply_name process_name,
           CASE ap.value WHEN 'INFINITE' THEN 'not set'
                         ELSE to_char(ap.value*1024*1024) END max_sga_size,
           to_char(round(apr.sga_used/(1024*1024),2)) sga_used,
           to_char(round(apr.sga_allocated/(1024*1024),2)) sga_allocated,
           CASE ap.value WHEN 'INFINITE' THEN 'no MAX_SGA_SIZE set'
                         ELSE to_char(round(100*apr.sga_allocated/ap.value/(1024*1024),2))
                         END PCT_ALLOCMEM_OF_MAX_SGA_SIZE,
           CASE WHEN p1.value=0 THEN CASE WHEN p2.value=0
                THEN CASE WHEN p3.value=0
                     THEN to_char((SELECT 0.1*bytes FROM v$sgainfo WHERE name='Shared Pool Size'))
                     ELSE to_char((SELECT 0.1*bytes FROM v$sgainfo WHERE name='Maximum SGA Size'))
                     END ELSE to_char(p2.value) END
                ELSE to_char(p1.value) END streams_pool_size,
           CASE WHEN p1.value=0 THEN CASE WHEN p2.value=0
                THEN CASE WHEN p3.value=0 THEN '__sga_target'
                     ELSE 'memory_target' END
                ELSE 'sga_target' END
                ELSE 'streams_pool_size' END sp_derrived
    FROM gv$gg_apply_reader apr, dba_apply_parameters ap,
         gv$parameter p1, gv$parameter p2, gv$parameter p3
    WHERE apr.apply_name = ap.apply_name
      AND apr.inst_id = p1.inst_id AND apr.inst_id = p2.inst_id
      AND apr.inst_id = p3.inst_id
      AND p1.name = 'streams_pool_size' AND p2.name = 'sga_target'
      AND p3.name = 'memory_target'   AND ap.parameter = 'MAX_SGA_SIZE'
    ORDER BY apr.inst_id, process_type, process_name
"""
 
SQL_REP_OPEN_TRANS = """
    SELECT component_name, count(*) "Open Transactions",
           sum(cumulative_message_count) "Total LCRs"
    FROM gv$Goldengate_transaction
    WHERE component_type = 'APPLY'
    GROUP BY component_name
    ORDER BY 3
"""
 
SQL_REP_OPEN_TRANS_10000 = """
    SELECT component_name, count(*) "Open Transactions",
           sum(cumulative_message_count) "Total LCRs"
    FROM gv$Goldengate_transaction
    WHERE component_type = 'APPLY' AND cumulative_message_count > 10000
    GROUP BY component_name
    ORDER BY 1
"""
 
 
@app.post("/api/v2/db/irtshoot", tags=["MigDB Replicat Management"],
    summary="Troubleshoot an integrated replicat process",
    description="Connects to the target database and returns replicat summary, parameters, open transactions, inbound server stats, apply process details including receiver, reader, coordinator, server ASH, flow, and streams pool data based on database version.")
def ir_tshoot(body: IRTshootRequest):
    val         = selectConn(body.dbname)
    con         = val[0]
    db_main_ver = val[1]
 
    if "ORA-" in str(db_main_ver):
        return JSONResponse(content={"error": db_main_ver})
 
    try:
        db_det = fetch_query(SQL_DB_DET, con, cast_str=True)
        ver    = int(db_main_ver)
 
        if ver == 11:
            rep_params        = SQL_REP_PARAMS_11
            rep_inbound       = SQL_REP_INBOUND_11
            rep_summary       = SQL_REP_SUMMARY_11
            apply_reader      = SQL_APPLY_READER_11
            apply_coordinator = SQL_APPLY_COORDINATOR_11
        else:
            rep_params        = SQL_REP_PARAMS_12
            rep_inbound       = SQL_REP_INBOUND_12
            rep_summary       = SQL_REP_SUMMARY_12
            apply_reader      = SQL_APPLY_READER_12
            apply_coordinator = SQL_APPLY_COORDINATOR_12
 
        return JSONResponse(content={
            "rep_summary":            fetch_query(rep_summary,                    con, cast_str=True),
            "rep_params":             fetch_query(rep_params,                     con, cast_str=True),
            "rep_open_trans":         fetch_query(SQL_REP_OPEN_TRANS,             con, cast_str=True),
            "rep_open_trans_10000":   fetch_query(SQL_REP_OPEN_TRANS_10000,       con, cast_str=True),
            "db_det":                 db_det,
            "rep_inbound":            fetch_query(rep_inbound,                    con, cast_str=True),
            "apply_receiver":         fetch_query(SQL_APPLY_RECEIVER,             con, cast_str=True),
            "apply_receiver_ash":     fetch_query(SQL_APPLY_RECEIVER_ASH,         con, cast_str=True),
            "apply_reader":           fetch_query(apply_reader,                   con, cast_str=True),
            "apply_reader_ash":       fetch_query(SQL_APPLY_READER_ASH,           con, cast_str=True),
            "apply_reader_info":      fetch_query(SQL_APPLY_READER_INFO,          con, cast_str=True),
            "apply_coordinator_info": fetch_query(SQL_APPLY_COORDINATOR_INFO,     con, cast_str=True),
            "apply_coordinator":      fetch_query(apply_coordinator,              con, cast_str=True),
            "apply_server_info":      fetch_query(SQL_APPLY_SERVER_INFO,          con, cast_str=True),
            "apply_server_txn":       fetch_query(SQL_APPLY_SERVER_TXN,           con, cast_str=True),
            "apply_fts_info":         fetch_query(SQL_APPLY_FTS_INFO,             con, cast_str=True),
            "apply_server_ash":       fetch_query(SQL_APPLY_SERVER_ASH,           con, cast_str=True),
            "apply_flow":             fetch_query(SQL_APPLY_FLOW,                 con, cast_str=True),
            "apply_server_agg":       fetch_query(SQL_APPLY_SERVER_AGG_STATS,     con, cast_str=True),
            "apply_server_waits":     fetch_query(SQL_APPLY_SERVER_WAITS,         con, cast_str=True),
            "apply_reader_lcr_dep":   fetch_query(SQL_APPLY_READER_LCR_DEP,       con, cast_str=True),
            "streams_pool":           fetch_query(SQL_STREAMS_POOL,               con, cast_str=True),
            "streams_pool_stats":     fetch_query(SQL_STREAMS_POOL_USAGE,         con, cast_str=True),
        })
 
    except Exception as e:
        logger.error(str(e))
        return JSONResponse(content={"error": str(e)})
 
    finally:
        try:
            con.close()
        except Exception:
            pass

class OnepConnRequest(BaseModel):
    dep_type: str
    onepOps: str
    user: Optional[str] = None
    passwd: Optional[str] = None
    role: Optional[str] = None
    dep_url: Optional[str] = None
    dep: Optional[str] = None
 
 
class OnepDepUrlRequest(BaseModel):
    dep: str
 
 
class OnepLoginRequest(BaseModel):
    user: str
    passwd: str
    onepsuid: str
 
 
class ExpimpInsertRequest(BaseModel):
    srcdep: str
    tgtdep: str
    srcdbName: str
    tgtdbName: str
    jobName: str
    jobOwner: str
    srcdumpDir: str
    tgtdumpDir: str
    dumpFile: str
    cdbCheck: str
    pdbName: str
    reMapSchema: str
    remapTablespace: str
    src_edition: str
 
 
@app.post("/api/v2/onep/conn", tags=["MigDB Connection"],
    summary="Add a MigDB deployment connection",
    description="Adds a local or remote deployment connection to the ONEPCONN table with encrypted credentials, validating remote deployments via login before storing.")
def onep_conn(body: OnepConnRequest) -> list[list[str]]:
    err_print: list[str] = []
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        oneplace_dep = config.get("AGENT_CONFIG", "AGENT_DEPLOYMENT")
 
        if body.dep_type == "ld":
            if body.onepOps == "add":
                encrypted = cipher.encrypt(body.passwd)
                cursor.execute(
                    "INSERT INTO ONEPCONN VALUES (:dep,:user,:passwd,:role,:dep_type,:dep_url)",
                    {"dep": oneplace_dep, "user": body.user, "passwd": encrypted,
                     "role": body.role, "dep_type": body.dep_type, "dep_url": body.dep_url},
                )
            elif body.onepOps == "edit":
                encrypted = cipher.encrypt(body.passwd)
                dep_url = body.dep_url
                dep = body.dep
                cursor.execute(
                    "UPDATE ONEPCONN SET passwd=:passwd, dep_url=:dep_url WHERE user=:user AND dep=:dep",
                    {"user": body.user, "passwd": encrypted, "dep_url": dep_url, "dep": dep},
                )
            elif body.onepOps == "del":
                cursor.execute("DELETE FROM ONEPCONN WHERE user=:user", {"user": body.user})
            conn.commit()
            err_print.append(f"OneP User {body.user} Added")
 
        elif body.dep_type == "rd":
            encrypted = cipher.encrypt(body.passwd)
            #login_url = body.dep_url.rstrip("/") + "/api/v2/onep/login"
            payload = {"user": body.user, "passwd": encrypted, "onepsuid": "oneplaceusid1980"}
            headers = { "Content-Type": "application/json" }

            base_url = body.dep_url.rstrip("/")
            primary_url = base_url + "/api/v2/onep/login"
            fallback_url = base_url + "/api/v2/onepLogin"

            try:
                r = requests.post(primary_url, json=payload, headers=headers,
                                  verify=ssl_verify, timeout=ssh_timeout)
                if not r.ok:
                    r = requests.post(fallback_url, json=payload, headers=headers,
                              verify=ssl_verify, timeout=ssh_timeout)
                r.raise_for_status()
                resp = r.json()
                sign_in = resp[1]
                oneplace_role = resp[2]
                oneplace_dep = resp[4]
                dep_url = resp[3]
                dbtype = resp[5]
                if sign_in == "Y" and oneplace_role == "admin":
                    cursor.execute(
                       """INSERT INTO ONEPCONN (dep, user, passwd, role, dep_type, dep_url, dbtype)
                           VALUES (:dep, :user, :passwd, :role, :dep_type, :dep_url, :dbtype)""",
                        {"dep": oneplace_dep, "user": body.user, "passwd": encrypted,
                         "role": oneplace_role, "dep_type": body.dep_type,
                         "dep_url": dep_url, "dbtype": dbtype},
                    )
                    conn.commit()
                    err_print.append(f"OneP User {body.user} Added")
                else:
                    err_print.append("Invalid Deployment Credentials")
            except requests.exceptions.ConnectionError:
                err_print.append("Invalid Deployment")
 
    except sqlite3.DatabaseError as exc:
        err_print.append(f"There is a problem with OneP Database {exc}")
    finally:
        if conn:
            conn.close()
 
    return [err_print]
 
 
@app.get("/api/v2/onep/dep", tags=["MigDB Connection"],
    summary="List Oracle admin deployments",
    description="Returns all distinct deployment names and URLs from ONEPCONN where the role is admin and the database type is Oracle.")
def onep_dep() -> list:
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            "SELECT DISTINCT dep, dep_url FROM ONEPCONN WHERE role='admin' AND dbtype!='comparepad'",
            conn,
        )
        return [df.to_dict("records")]
    except sqlite3.DatabaseError as exc:
        logger.info(f"There is a problem with Light Database {exc}")
        return [[]]
    finally:
        if conn:
            conn.close()
 
 
@app.post("/api/v2/onep/depurl", tags=["MigDB Connection"],
    summary="Get deployment URL and type",
    description="Fetches the deployment URL and database type for a given deployment name from the ONEPCONN table.")
def onep_dep_url(body: OnepDepUrlRequest) -> list:
    dep_url = ""
    dep_type = ""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT dep_url, dbtype FROM ONEPCONN WHERE dep=:dep",
            {"dep": body.dep},
        )
        row = cursor.fetchone()
        if row:
            dep_url, dep_type = row[0], row[1]
    except sqlite3.DatabaseError as exc:
        logger.info(str(exc))
    finally:
        if conn:
            conn.close()
    return [dep_url, trail_path, dep_type]
 
 
@app.get("/api/v2/onep/rmthostmgr", tags=["MigDB Connection"],
    summary="Get remote host manager port",
    description="Validates admin credentials against the ONEPCONN table and returns the MigDB manager port and agent host for the remote deployment.")
def gg_rmt_host_mgr():
    rmt_port = ""
    val = infoall()
    for item in val[0]:
        if "mgrport" in item:
            rmt_port = item["mgrport"]
    return [rmt_port, agent_host]

class OnepDepTokenRequest(BaseModel):
    dep: str

@app.post(
    "/api/v2/onep/deptoken",
    tags=["Deployment"],
    summary="Get a fresh access token for a remote deployment",
    description=(
        "Looks up the saved credentials for the given remote (dep_type='rd') "
        "deployment, decrypts the password, logs into that deployment's own "
        "/api/v2/onepLogin, and returns the resulting AccessToken for the "
        "browser to store."
    ),
)
async def onep_dep_token(body: OnepDepTokenRequest):
    conn = sqlite3.connect('conn.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT dep_url, user, passwd, dbtype FROM ONEPCONN WHERE dep=:dep AND dep_type="rd"',
        {'dep': body.dep}
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"No remote deployment found for '{body.dep}'")

    dep_url, user, encrypted_passwd, dbtype = row

    try:
        passwd = cipher.decrypt(encrypted_passwd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not decrypt stored credentials: {e}")

    login_url = dep_url.rstrip("/") + "/api/v2/onepLogin"
    payload = {"user": user, "passwd": encrypted_passwd, "onepsuid": "oneplaceusid1980"}
    headers = { "Content-Type": "application/json" }

    try:
        r = requests.post(login_url, json=payload, headers=headers,
                           verify=ssl_verify, timeout=sshTimeOut)
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail=f"Could not reach deployment at {dep_url}")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail=f"Timed out reaching deployment at {dep_url}")

    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code,
                             detail=f"Login to {dep_url} returned HTTP {r.status_code}")

    try:
        resp = r.json()
    except ValueError:
        raise HTTPException(status_code=502, detail=f"Invalid response from {dep_url}")

    sign_in = resp[1]
    if sign_in != 'Y':
        raise HTTPException(status_code=401, detail="Invalid deployment credentials")

    return {
        "dep_url": dep_url,
        "dep_name": resp[4],
        "dbtype": dbtype,
        "onepsuid": "oneplaceusid1980",
        "role": resp[2],
        "access_token": resp[6],
    } 
 
@app.post("/api/v2/onep/login", tags=["Auth"],
    summary="Authenticate a MigDB user",
    description="Validates the provided credentials against the ONEPCONN table and returns the sign-in status, role, deployment URL, deployment name, and database type.",
    operation_id="onep_login")
def onep_login(body: OnepLoginRequest) -> list:
    err_print: list[str] = []
    sign_in = "N"
    dep_name = ""
    role = ""
    dep_url = ""
    dep_type = ""
    AccessToken = ""
    conn = None
 
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT dep, user, passwd, role, dep_url, dbtype FROM ONEPCONN "
            "WHERE user=:user AND dep_type='ld'",
            {"user": body.user},
        )
        row = cursor.fetchone()
 
        if row:
            stored_user = row[1]
            stored_passwd = cipher.decrypt(row[2])
            incoming_passwd = (
                cipher.decrypt(body.passwd)
                if body.onepsuid == "oneplaceusid1980"
                else body.passwd
            )
            if stored_user == body.user and stored_passwd == incoming_passwd:
                sign_in = "Y"
                dep_name = row[0]
                dep_url = row[4]
                role = row[3]
                dep_type = row[5]
                AccessToken = create_access_token(
                    data={"sub": row[1], "role": row[3]}
                )
            else:
                err_print.append("Invalid Login Credentials")
        else:
            err_print.append("Invalid Login Credentials")
 
    except sqlite3.DatabaseError as exc:
        err_print.append(str(exc))
    finally:
        if conn:
            conn.close()
 
    return [err_print, sign_in, role, dep_url, dep_name, dep_type, AccessToken]
 
 
@app.post("/api/v2/onep/expimpinsert", tags=["MigDB Connection"],
    summary="Insert an export/import job record",
    description="Inserts a new export/import job record into the expimp table with source and target deployment, database, directory, and remapping details.")
def expimp_insert(body: ExpimpInsertRequest) -> dict:
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO expimp (srcdep, tgtdep, srcdbName, tgtdbName, jobName, jobOwner,
               srcdumpDir, tgtdumpDir, dumpFile, cdbCheck, pdbName, reMapSchema, remapTablespace,src_edition)
               VALUES (:srcdep, :tgtdep, :srcdbName, :tgtdbName, :jobName, :jobOwner,
                       :srcdumpDir, :tgtdumpDir, :dumpFile, :cdbCheck, :pdbName,
                       :reMapSchema, :remapTablespace ,:src_edition)""",
            body.model_dump(),
        )
        conn.commit()
        return {"message": "Record inserted successfully", "jobName": body.jobName}
    except Exception as exc:
        logger.error(str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if conn:
            cursor.close()
            conn.close()
 
# DB Assessment Code Start
ASSESSMENT_BASE_DIR = os.path.join(agent_home, "assessments")
styles = getSampleStyleSheet()
 
 
class ConnectionRequest(BaseModel):
    host: str
    port: str = "1521"
    service_name: str
    username: str
    password: str
 
 
class AssessmentRequest(BaseModel):
    dbName: str
 
 
class MonitorRequest(BaseModel):
    AssessmentID: str
 
 
class StorageType(Enum):
    GP3 = "gp3"
    IO1 = "io1"
    IO2 = "io2"
 
 
@app.get("/api/v2/health", tags=["MigDB System"],
    summary="Health check",
    description="Returns the current service health status and timestamp.")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Oracle to RDS Migration Assessment",
    }
 
cell_style = ParagraphStyle(  
    "TableCell",
    parent=styles["Normal"],
    fontSize=9,
    leading=11,
    wordWrap="CJK",
)

def make_cell(value):  
    text = str(value) if value is not None else ""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(text, cell_style)

def safe_table(data, col_widths):  
    wrapped = [[make_cell(cell) for cell in row] for row in data]
    return Table(wrapped, colWidths=col_widths) 
 
def render_anything(elements, data, title=None):
    if title:
        elements.append(Paragraph(f"<b>{title}</b>", styles["Heading2"]))
        elements.append(Spacer(1, 8))
 
    if isinstance(data, dict):
        table_data = [["Key", "Value"]]
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                elements.append(Paragraph(f"<b>{k}</b>", styles["Normal"]))
                render_anything(elements, v)
            else:
                table_data.append([str(k), str(v)])
        if len(table_data) > 1:
            elements.append(Table(table_data, hAlign="LEFT"))
            elements.append(Spacer(1, 10))
 
    elif isinstance(data, list):
        if not data:
            elements.append(Paragraph("No data available", styles["Normal"]))
            elements.append(Spacer(1, 6))
            return
        if all(isinstance(item, dict) for item in data):
            headers = list(data[0].keys())
            table_data = [headers]
            for item in data:
                table_data.append([str(item.get(h, "")) for h in headers])
            col_width = 450 // len(headers)
            elements.append(Table(table_data, hAlign="LEFT"))
            elements.append(Spacer(1, 10))
        else:
            for item in data:
                elements.append(Paragraph(f"- {item}", styles["Normal"]))
            elements.append(Spacer(1, 10))
    else:
        elements.append(Paragraph(str(data), styles["Normal"]))
        elements.append(Spacer(1, 6))
 
 
def generate_assessment_pdf(assessment_id, dbName, db_info, features, schemas, blockers, recommendation, run_time=None):
    assessment_dir = os.path.join(ASSESSMENT_BASE_DIR, assessment_id)
    os.makedirs(assessment_dir, exist_ok=True)
    pdf_path = os.path.join(assessment_dir, "assessment_report.pdf")
    elements = []
 
    def heading(text):
        elements.append(Paragraph(f"<b>{text}</b>", styles["Heading2"]))
        elements.append(Spacer(1, 10))
 
    def normal(text):
        elements.append(Paragraph(text, styles["Normal"]))
        elements.append(Spacer(1, 6))
 
    if run_time is None:
        run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
 
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    heading("Oracle to AWS RDS Migration Assessment")
    normal(f"Assessment ID: {assessment_id}")
    normal(f"Database Name: {dbName}")
    normal(f"Assessment Run Time: {run_time}")
    render_anything(elements, db_info, "Database Overview")
    render_anything(elements, features, "Feature Analysis")
    render_anything(elements, schemas, "Schema Details")
    render_anything(elements, blockers, "Migration Blockers")
    render_anything(elements, recommendation, "RDS Recommendation")
    doc.build(elements)
    return pdf_path
 
@app.post("/api/v2/assessment/run", tags=["MigDB Assessment"],
    summary="Run a database assessment (streaming)",
    description="Streams live progress as SSE while running each assessment step: database info, feature compatibility, schema analysis, blocker detection, and RDS recommendations.")
async def run_assessment(body: AssessmentRequest):
    dbName = body.dbName

    def generate():
        assessment_id = dbName + "_" + datetime.now().strftime("%Y%m%d%H%M%S")

        def emit(step, status, message="", extra=None):
            payload = {"step": step, "status": status, "message": message}
            if extra:
                payload.update(extra)
            return f"data: {json.dumps(payload)}\n\n"

        conn = None
        try:
            yield emit("init", "running", f"Creating assessment job for '{dbName}'...")

            conn = sqlite3.connect(DB_PATH)
            sq_cursor = conn.cursor()
            sq_cursor.execute(
                "INSERT INTO DBASSESSMENT(jobid, dbname, runtime) VALUES(:assessment_id, :dbName, datetime('now'))",
                {"assessment_id": assessment_id, "dbName": dbName},
            )
            conn.commit()
            yield emit("init", "done", f"Assessment job '{assessment_id}' created.")

            steps = [
                ("db_info",        "Fetching database info...",              get_database_info),
                ("features",       "Checking feature compatibility...",       check_feature_compatibility),
                ("schemas",        "Analyzing schemas...",                    analyze_schemas),
                ("blockers",       "Checking migration blockers...",          check_blockers),
                ("datatypes",      "Scanning datatype usage by tablespace...", datatype_used_by_tablespace),
                ("special_types",  "Scanning special datatypes...",           get_special_datatypes),
                ("lobs",           "Scanning LOB column sizes...",            get_lobs_columns_size),
                ("user_types",     "Scanning user-defined columns...",        get_user_defined_columns),
                ("invisible_cols", "Scanning invisible/virtual columns...",   get_invisible_table_columns),
                ("tde_cols",       "Scanning TDE-encrypted columns...",       get_tables_with_column_level_tde_encryption),
                ("basicfile_lobs", "Scanning Tables with BASICFILE LOB...",   get_tables_with_basicfile_lob),
                ("recommendation", "Computing RDS instance recommendation...", get_rds_recommendation),
            ]

            for step_id, label, fn in steps:
                yield emit(step_id, "running", label)
                try:
                    fn(dbName)
                    yield emit(step_id, "done", f"{label} done.")
                except HTTPException as he:
                    # DB connection failure or similar — surface it and stop
                    yield emit(step_id, "error", str(he.detail))
                    yield emit("assessment", "error", "Assessment aborted due to a connection error.")
                    yield "data: __DONE__\n\n"
                    return
                except Exception as e:
                    logger.error(f"Assessment step '{step_id}' failed: {e}", exc_info=True)
                    yield emit(step_id, "error", str(e))
                    # non-fatal steps can continue; keep going

            yield emit("assessment", "success", "Assessment completed successfully.",
                        extra={"assessment_id": assessment_id})
            yield "data: __DONE__\n\n"

        except Exception as e:
            logger.error(f"run_assessment failed for '{dbName}': {e}", exc_info=True)
            yield emit("assessment", "error", str(e))
            yield "data: __DONE__\n\n"
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Content-Type-Options": "nosniff",
        },
    )
 
@app.post("/api/v2/assessment/monitor", tags=["MigDB Assessment"],
    summary="Monitor an assessment (streaming)",
    description="Streams live progress while re-fetching database info, feature compatibility, "
                 "schema analysis, blockers, and RDS recommendations for a given assessment ID.")
async def monitor_assessment(body: MonitorRequest):
    def generate():
        def emit(step, status, message="", extra=None):
            payload = {"step": step, "status": status, "message": message}
            if extra:
                payload.update(extra)
            return f"data: {json.dumps(payload)}\n\n"

        try:
            yield emit("lookup", "running", "Looking up assessment record...")

            sqconn = sqlite3.connect(DB_PATH)
            sqcursor = sqconn.cursor()
            sqcursor.execute(
                "SELECT dbname FROM DBASSESSMENT WHERE jobid=:jobid",
                {"jobid": body.AssessmentID},
            )
            db_row = sqcursor.fetchone()
            sqcursor.close()
            sqconn.close()

            if not db_row:
                yield emit("lookup", "error", "Assessment not found")
                yield "data: __DONE__\n\n"
                return

            dbName = db_row[0]
            yield emit("lookup", "done", f"Found assessment for database '{dbName}'.")

            results = {}
            steps = [
                ("db_info",        "Fetching database info...",               get_database_info),
                ("features",       "Checking feature compatibility...",        check_feature_compatibility),
                ("schemas",        "Analyzing schemas...",                     analyze_schemas),
                ("blockers",       "Checking migration blockers...",           check_blockers),
                ("datatypes",      "Scanning datatype usage by tablespace...", datatype_used_by_tablespace),
                ("special_types",  "Scanning special datatypes...",            get_special_datatypes),
                ("lobs",           "Scanning LOB column sizes...",             get_lobs_columns_size),
                ("user_types",     "Scanning user-defined columns...",         get_user_defined_columns),
                ("invisible_cols", "Scanning invisible/virtual columns...",    get_invisible_table_columns),
                ("tde_cols",       "Scanning TDE-encrypted columns...",        get_tables_with_column_level_tde_encryption),
                ("basicfile_lobs", "Scanning Tables with BASICFILE LOB...",    get_tables_with_basicfile_lob),
                ("recommendation", "Computing RDS instance recommendation...", get_rds_recommendation),
            ]

            for step_id, label, fn in steps:
                yield emit(step_id, "running", label)
                try:
                    results[step_id] = fn(dbName)
                    yield emit(step_id, "done", f"{label} done.")
                except HTTPException as he:
                    yield emit(step_id, "error", str(he.detail))
                    yield emit("assessment", "error", "Monitoring aborted due to a connection error.")
                    yield "data: __DONE__\n\n"
                    return
                except Exception as e:
                    logger.error(f"monitor_assessment step '{step_id}' failed: {e}", exc_info=True)
                    yield emit(step_id, "error", str(e))
                    results[step_id] = None

            # same array shape your old function returned
            final_payload = [
                results.get("db_info"),
                results.get("features"),
                results.get("schemas"),
                results.get("blockers"),
                results.get("recommendation"),
                results.get("datatypes"),
                results.get("special_types"),
                results.get("lobs"),
                results.get("user_types"),
                results.get("invisible_cols"),
                results.get("tde_cols"),
                results.get("basicfile_lobs")
            ]

            yield emit("assessment", "success", "Assessment data refreshed.", extra={"data": final_payload})
            yield "data: __DONE__\n\n"

        except Exception as e:
            logger.error(f"monitor_assessment failed: {e}", exc_info=True)
            yield emit("assessment", "error", str(e))
            yield "data: __DONE__\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Content-Type-Options": "nosniff",
        },
    ) 
 
@app.post("/api/v2/assessment/pdf", tags=["MigDB Assessment"],
    summary="Download assessment PDF report",
    description="Returns the generated PDF assessment report for the given assessment ID as a downloadable file.")
def monitor_assessment_pdf(body: MonitorRequest):
    assessment_dir = os.path.join(ASSESSMENT_BASE_DIR, body.AssessmentID)
    pdf_path = os.path.join(assessment_dir, "assessment_report.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Assessment PDF not found")
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"assessment_{body.AssessmentID}.pdf",
    )
 
 
@app.get("/api/v2/assessments", tags=["MigDB Assessment"],
    summary="List all assessments",
    description="Returns all assessment job IDs stored in the DBASSESSMENT table.")
def list_assessments():
    sqconn = sqlite3.connect(DB_PATH)
    sqcursor = sqconn.cursor()
    sqcursor.execute("SELECT jobid FROM DBASSESSMENT")
    db_rows = sqcursor.fetchall()
    sqcursor.close()
    sqconn.close()
    assessments = [row for row in db_rows] if db_rows else []
    return {"assessments": assessments}
 
assessment_cache: dict[str, dict] = {}
 
@app.get("/api/v2/assessment/{assessment_id}", tags=["MigDB Assessment"],
    summary="Get assessment results",
    description="Returns the cached assessment results for the given assessment ID.")
def get_assessment(assessment_id: str):
    if assessment_id not in assessment_cache:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {"assessment_id": assessment_id, "results": assessment_cache[assessment_id]}
 
 
@app.delete("/api/v2/assessment/{assessment_id}", tags=["MigDB Assessment"],
    summary="Delete an assessment",
    description="Removes the assessment results for the given assessment ID from the cache.")
def delete_assessment(assessment_id: str):
    if assessment_id not in assessment_cache:
        raise HTTPException(status_code=404, detail="Assessment not found")
    del assessment_cache[assessment_id]
    return {"message": "Assessment deleted successfully"}
 
 
@app.get("/api/v2/assessment/{assessment_id}/export/json", include_in_schema=False, tags=["MigDB Assessment"],
    summary="Export assessment as JSON",
    description="Exports the assessment results for the given assessment ID as a downloadable JSON file.")
def export_json(assessment_id: str):
    if assessment_id not in assessment_cache:
        raise HTTPException(status_code=404, detail="Assessment not found")
    results = assessment_cache[assessment_id]
    json_str = json.dumps(results, indent=2, default=str)
    buffer = io.BytesIO(json_str.encode())
    return FileResponse(
        buffer,
        media_type="application/json",
        filename=f"assessment_{assessment_id}.json",
    )
 
 
@app.get("/api/v2/assessment/{assessment_id}/export/excel", include_in_schema=False, tags=["MigDB Assessment"],
    summary="Export assessment as Excel",
    description="Exports the assessment results including summary, features, schemas, blockers, and recommendations as a downloadable Excel file.")
def export_excel(assessment_id: str):
    if assessment_id not in assessment_cache:
        raise HTTPException(status_code=404, detail="Assessment not found")
    results = assessment_cache[assessment_id]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_data = {
            "Metric": ["Database Size (GB)", "Total Schemas", "Total Tables", "Recommended Instance", "Estimated Cost"],
            "Value": [
                results["database_info"]["size_gb"],
                results["database_info"]["schema_count"],
                results["database_info"]["table_count"],
                results["recommendations"]["instance_type"],
                f"${results['recommendations']['estimated_monthly_cost']}",
            ],
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
        pd.DataFrame(results["features"]).to_excel(writer, sheet_name="Features", index=False)
        pd.DataFrame(results["schemas"]).to_excel(writer, sheet_name="Schemas", index=False)
        if results["blockers"]:
            pd.DataFrame(results["blockers"]).to_excel(writer, sheet_name="Blockers", index=False)
        rec_data = pd.DataFrame([results["recommendations"]]).T
        rec_data.columns = ["Value"]
        rec_data.to_excel(writer, sheet_name="Recommendations")
    output.seek(0)
    return FileResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"assessment_{assessment_id}.xlsx",
    )
 
 
@app.get("/api/v2/assessment/{assessment_id}/metrics", include_in_schema=False, tags=["MigDB Assessment"],
    summary="Get assessment metrics",
    description="Returns database info, summary, and estimated monthly cost metrics for the given assessment ID.")
def get_metrics(assessment_id: str):
    if assessment_id not in assessment_cache:
        raise HTTPException(status_code=404, detail="Assessment not found")
    results = assessment_cache[assessment_id]
    return {
        "assessment_id": assessment_id,
        "metrics": {
            "database_info": results["database_info"],
            "summary": results["summary"],
            "estimated_cost": results["recommendations"]["estimated_monthly_cost"],
        },
    }
 
 
@app.get("/api/v2/assessment/{assessment_id}/features", include_in_schema=False, tags=["MigDB Assessment"],
    summary="Get feature compatibility analysis",
    description="Returns a categorized breakdown of feature compatibility results including compatible, requires modification, not used, and error counts for the given assessment ID.",
    operation_id="get_feature_compatibility")
def get_feature_compatibility(assessment_id: str):
    if assessment_id not in assessment_cache:
        raise HTTPException(status_code=404, detail="Assessment not found")
    features = assessment_cache[assessment_id]["features"]
    compatible = [f for f in features if f["status"] == "Compatible"]
    modified = [f for f in features if f["status"] == "Modified"]
    not_used = [f for f in features if f["status"] == "Not Used"]
    errors = [f for f in features if f["status"] == "Error"]
    return {
        "assessment_id": assessment_id,
        "feature_analysis": {
            "total": len(features),
            "compatible": {"count": len(compatible), "features": compatible},
            "requires_modification": {"count": len(modified), "features": modified},
            "not_used": {"count": len(not_used), "features": not_used},
            "errors": {"count": len(errors), "features": errors},
        },
    }
 
 
def get_database_info(dbName):
    con = None
    cursor = None
    try:
        val = selectConn(dbName)
        con = val[0]
        cursor = con.cursor()
        cursor.execute("SELECT * FROM v$version WHERE banner LIKE 'Oracle%'")
        version_info = cursor.fetchone()[0]
 
        cursor.execute("""
            SELECT d.cdb, c.con_id, c.name as pdb_name
            FROM v$database d
            CROSS JOIN v$containers c
            WHERE c.con_id = SYS_CONTEXT('USERENV', 'CON_ID')
        """)
        tablespace_info = {"is_cdb": False, "total_db_size_gb": 0, "tablespaces": [], "pdbs": []}
 
        db_info = cursor.fetchone()
        is_cdb = db_info[0] == "YES" if db_info else False
        tablespace_info["is_cdb"] = is_cdb
 
        if is_cdb:
            logger.info(f"{dbName} is a Container Database (CDB)")
            cursor.execute("""
                SELECT con_id, name, open_mode
                FROM v$pdbs
                WHERE name NOT IN ('PDB$SEED')
                ORDER BY con_id
            """)
            pdbs = cursor.fetchall()
            for pdb_id, pdb_name, open_mode in pdbs:
                logger.info(f"Processing PDB: {pdb_name} (CON_ID: {pdb_id}, Status: {open_mode})")
                pdb_info = {"pdb_name": pdb_name, "pdb_id": pdb_id, "open_mode": open_mode, "tablespaces": [], "total_size_gb": 0}
                placeholders = ",".join(f":ts{i}" for i in range(len(SYSTEM_TABLESPACES)))
                bind_vars = {"pdb_id": pdb_id, **{f"ts{i}": ts for i, ts in enumerate(SYSTEM_TABLESPACES)}}
                cursor.execute(f"""
                    SELECT tablespace_name, ROUND(SUM(bytes)/1024/1024/1024, 2) as size_gb
                    FROM cdb_data_files
                    WHERE con_id = :pdb_id
                    AND tablespace_name NOT IN ({placeholders})
                    GROUP BY tablespace_name
                """, bind_vars)
                pdb_tablespaces = cursor.fetchall()
                for ts_name, ts_size in pdb_tablespaces:
                    ts_size_float = float(ts_size) if ts_size else 0.0
                    pdb_info["tablespaces"].append({"tablespace": ts_name, "size_gb": ts_size_float})
                pdb_info["total_size_gb"] = round(sum(ts["size_gb"] for ts in pdb_info["tablespaces"]), 2)
                tablespace_info["pdbs"].append(pdb_info)
                logger.info(f"PDB {pdb_name}: {len(pdb_info['tablespaces'])} tablespaces, {pdb_info['total_size_gb']} GB")
            tablespace_info["total_db_size_gb"] = round(sum(pdb["total_size_gb"] for pdb in tablespace_info["pdbs"]), 2)
            for pdb in tablespace_info["pdbs"]:
                for ts in pdb["tablespaces"]:
                    tablespace_info["tablespaces"].append({"pdb_name": pdb["pdb_name"], "tablespace": ts["tablespace"], "size_gb": ts["size_gb"]})
        else:
            logger.info(f"{dbName} is a non-Container Database")
            placeholders = ",".join(f":ts{i}" for i in range(len(SYSTEM_TABLESPACES)))
            bind_vars = {f"ts{i}": ts for i, ts in enumerate(SYSTEM_TABLESPACES)}
            cursor.execute(f"""
                SELECT tablespace_name, ROUND(SUM(bytes)/1024/1024/1024, 2) as size_gb
                FROM dba_data_files
                WHERE tablespace_name NOT IN ({placeholders})
                GROUP BY tablespace_name
            """, bind_vars)
            tablespaces = cursor.fetchall()
            for ts_name, ts_size in tablespaces:
                ts_size_float = float(ts_size) if ts_size else 0.0
                tablespace_info["tablespaces"].append({"tablespace": ts_name, "size_gb": ts_size_float})
            tablespace_info["total_db_size_gb"] = round(sum(ts["size_gb"] for ts in tablespace_info["tablespaces"]), 2)

        schemas_placeholders = ",".join(f":s{i}" for i in range(len(SYSTEM_SCHEMAS)))
        bind_vars = {f"s{i}": schema for i, schema in enumerate(SYSTEM_SCHEMAS)}
        cursor.execute(f"""
            SELECT COUNT(DISTINCT username) FROM dba_users
            WHERE username NOT IN ({schemas_placeholders})
        """, bind_vars)
        schema_count = cursor.fetchone()[0]
 
        code_objects = []
        if is_cdb:
            schemas_placeholders = ",".join(f":s{i}" for i in range(len(SYSTEM_SCHEMAS)))
            bind_vars = {f"s{i}": schema for i, schema in enumerate(SYSTEM_SCHEMAS)}
            cursor.execute(f"""
                SELECT con.pdb_name AS pdb_name, obj.owner, obj.object_type, COUNT(*) AS object_count
                FROM cdb_objects obj
                JOIN cdb_pdbs con ON obj.con_id = con.con_id
                WHERE obj.owner NOT IN ({schemas_placeholders})
                GROUP BY con.pdb_name, obj.owner, obj.object_type
            """, bind_vars)
            for pdb_name, owner, obj_type, count in cursor.fetchall():
                code_objects.append({"pdb": pdb_name, "owner": owner, "object_type": obj_type, "count": count})
        else:
            schemas_placeholders = ",".join(f":s{i}" for i in range(len(SYSTEM_SCHEMAS)))
            bind_vars = {f"s{i}": schema for i, schema in enumerate(SYSTEM_SCHEMAS)}
            cursor.execute(f"""
                SELECT owner, object_type, COUNT(*)
                FROM dba_objects
                WHERE object_type IN ('PROCEDURE', 'FUNCTION', 'PACKAGE')
                AND owner NOT IN ({schemas_placeholders})
                GROUP BY owner, object_type
            """, bind_vars)
            for owner, obj_type, count in cursor.fetchall():
                code_objects.append({"pdb": "NON-CDB", "owner": owner, "object_type": obj_type, "count": count})
 
        cursor.execute("SELECT value FROM nls_database_parameters WHERE parameter = 'NLS_CHARACTERSET'")
        charset = cursor.fetchone()[0]
 
        return {
            "version": version_info,
            "size_gb": tablespace_info["total_db_size_gb"],
            "tablespaces": tablespace_info,
            "character_set": charset,
            "schema_count": schema_count,
            "objects": code_objects,
        }
    except Exception as e:
        logger.error(f"get_database_info failed for {dbName}: {e}", exc_info=True)
        return {
            "version": "Error",
            "size_gb": "Error",
            "tablespaces": {"is_cdb": False, "total_db_size_gb": 0, "tablespaces": [], "pdbs": []},
            "character_set": "Error",
            "schema_count": "Error",
            "objects": [],
        }
        '''return {
            "version": "Error",
            "size_gb": "Error",
            "character_set": "Error",
            "schema_count": "Error",
            "table_count": "Error",
            "index_count": "Error",
            "procedures": "Error",
            "functions": "Error",
            "packages": "Error",
        }'''
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
 
 
def check_feature_compatibility(dbName):
    con = None
    cursor = None
    try:
        val = selectConn(dbName)
        con = val[0]
        cursor = con.cursor()
        features = []
        feature_checks = {
            "Partitioning": "SELECT COUNT(*) FROM dba_part_tables WHERE owner NOT LIKE '%SYS%'",
            "Compression": "SELECT COUNT(*) FROM dba_tables WHERE compression = 'ENABLED' AND owner NOT LIKE '%SYS%'",
            "Encryption": "SELECT COUNT(*) FROM dba_encrypted_columns WHERE owner NOT LIKE '%SYS%'",
            "Materialized Views": "SELECT COUNT(*) FROM dba_mviews WHERE owner NOT LIKE '%SYS%'",
            "Database Links": "SELECT COUNT(*) FROM dba_db_links WHERE owner NOT LIKE '%SYS%'",
            "Scheduler Jobs": "SELECT COUNT(*) FROM dba_scheduler_jobs WHERE owner NOT LIKE '%SYS%'",
            "Advanced Queuing": "SELECT COUNT(*) FROM dba_queues WHERE owner NOT LIKE '%SYS%'",
        }
        for feature_name, query in feature_checks.items():
            try:
                cursor.execute(query)
                count = cursor.fetchone()[0]
                if feature_name in ["Partitioning", "Compression", "Materialized Views", "Encryption"]:
                    status = "Compatible" if count > 0 else "Not Used"
                    action = "Supported in RDS Enterprise Edition"
                elif feature_name == "Database Links":
                    status = "Modified" if count > 0 else "Not Used"
                    action = "Review and recreate in RDS"
                elif feature_name == "Scheduler Jobs":
                    status = "Modified" if count > 0 else "Not Used"
                    action = "Use DBMS_SCHEDULER or AWS EventBridge"
                else:
                    status = "Compatible" if count > 0 else "Not Used"
                    action = "Verify licensing in RDS"
                features.append({"feature": feature_name, "count": count, "status": status, "action": action})
            except oracledb.Error as e:
                features.append({"feature": feature_name, "count": 0, "status": "Error", "action": "Unable to check"})
                logger.error(str(e))
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
    return features
 
 
def analyze_schemas(dbName):
    con = None
    cursor = None
    try:
        val = selectConn(dbName)
        con = val[0]
        cursor = con.cursor()
        schemas_placeholders = ",".join(f":s{i}" for i in range(len(SYSTEM_SCHEMAS)))
        bind_vars = {f"s{i}": schema for i, schema in enumerate(SYSTEM_SCHEMAS)}
        cursor.execute(f"""
            SELECT t.owner,
                   COUNT(DISTINCT t.table_name) AS table_count,
                   SUM(t.num_rows) AS total_rows,
                   ROUND(SUM(s.bytes)/1024/1024/1024, 2) AS size_gb
            FROM dba_tables t
            LEFT JOIN dba_segments s ON t.owner = s.owner AND t.table_name = s.segment_name
            WHERE t.owner NOT IN ({schemas_placeholders})
            GROUP BY t.owner
            ORDER BY SUM(s.bytes) DESC NULLS LAST
        """, bind_vars)
        schemas = []
        for row in cursor:
            schemas.append({
                "schema": row[0],
                "tables": row[1],
                "total_rows": row[2] if row[2] else 0,
                "size_gb": float(row[3]) if row[3] else 0,
            })
        return schemas
    except oracledb.Error as e:
        logger.error(str(e))
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
 
def check_blockers(dbName):
    con = None
    cursor = None
    try:
        val = selectConn(dbName)
        con = val[0]
        cursor = con.cursor()
        blockers = []
        try:
            cursor.execute("SELECT COUNT(*) FROM v$active_instances")
            if cursor.fetchone()[0] > 1:
                blockers.append({
                    "blocker": "Oracle RAC Detected",
                    "severity": "High",
                    "recommendation": "Use RDS Multi-AZ and Read Replicas",
                })
        except:
            pass
 
        try:
            schemas_placeholders = ",".join(f":s{i}" for i in range(len(SYSTEM_SCHEMAS)))
            bind_vars = {f"s{i}": schema for i, schema in enumerate(SYSTEM_SCHEMAS)}
            cursor.execute(f"SELECT COUNT(*) FROM dba_tab_columns WHERE data_type = 'BFILE' AND owner NOT IN ({schemas_placeholders})", bind_vars)
            bfile_count = cursor.fetchone()[0]
            if bfile_count > 0:
                blockers.append({
                    "blocker": f"BFILE columns ({bfile_count})",
                    "severity": "Medium",
                    "recommendation": "Convert to BLOB and use S3",
                })
 
            cursor.execute("""
                SELECT count(*)
                FROM v$parameter
                WHERE isdefault = 'FALSE'
                AND name NOT IN ('db_name','db_block_size','compatible')
                ORDER BY name
            """)
            parameter_count = cursor.fetchone()[0]
            if parameter_count > 0:
                blockers.append({
                    "blocker": f"Non Default Database parameter count - {parameter_count}",
                    "severity": "Medium",
                    "recommendation": "Review the need for the non default parameters and apply in RDS",
                })
 
            cursor.execute("""
                SELECT parameter, value FROM v$option
                WHERE parameter IN ('Oracle Database Vault', 'Oracle Label Security')
            """)
            rows = cursor.fetchall()
            for parameter, value in rows:
                if value == "TRUE":
                    if parameter == "Oracle Database Vault":
                        blockers.append({
                            "feature": "Oracle Database Vault",
                            "blocker": "Oracle Database Vault is enabled and NOT supported on AWS RDS.",
                            "severity": "High",
                            "recommendation": (
                                "Database Vault is not supported on RDS. "
                                "Review and remove Database Vault realms, command rules, "
                                "and factors before migration. "
                                "Consider using RDS IAM policies and parameter groups "
                                "as alternative access controls."
                            ),
                        })
                    elif parameter == "Oracle Label Security":
                        blockers.append({
                            "feature": "Oracle Label Security",
                            "blocker": "Oracle Label Security is enabled and NOT supported on AWS RDS.",
                            "severity": "High",
                            "recommendation": (
                                "Oracle Label Security (OLS) is not supported on RDS. "
                                "Review all OLS policies and labeled tables. "
                                "Consider implementing row-level security using "
                                "Oracle VPD (Virtual Private Database) as an alternative, "
                                "which IS supported on RDS."
                            ),
                        })
 
            cursor.execute("SELECT flashback_on, log_mode, db_unique_name FROM v$database")
            row = cursor.fetchone()
            flashback_on, log_mode, db_unique_name = row
            if flashback_on == "YES":
                blockers.append({
                    "feature": "Flashback Database",
                    "blocker": f"Flashback Database is ENABLED on '{db_unique_name}'. This feature is NOT supported on AWS RDS.",
                    "severity": "High",
                    "recommendation": (
                        "Flashback Database is not supported on RDS. "
                        "Use the following RDS alternatives instead:\n"
                        "  1. RDS Automated Backups + Point-In-Time Recovery (PITR)\n"
                        "  2. RDS Manual Snapshots for specific restore points\n"
                        "  3. AWS Backup for centralized backup management\n"
                        "  See: https://aws.amazon.com/blogs/database/"
                        "alternatives-to-the-oracle-flashback-database-feature-in-amazon-rds-for-oracle/"
                    ),
                })

            schemas_placeholders = ",".join(f":s{i}" for i in range(len(SYSTEM_SCHEMAS)))
            bind_vars = {f"s{i}": schema for i, schema in enumerate(SYSTEM_SCHEMAS)}
            cursor.execute(f"""
                SELECT owner, name, type, line, TRIM(text) AS text
                FROM dba_source s
                JOIN dba_users u ON u.username = s.owner
                WHERE (
                    UPPER(s.text) LIKE '%FTP%' OR UPPER(s.text) LIKE '%SFTP%'
                    OR UPPER(s.text) LIKE '%UTL_TCP%'
                    OR UPPER(s.text) LIKE '%UTL_FILE%'
                    OR UPPER(s.text) LIKE '%DBMS_FILE_TRANSFER%'
                    OR UPPER(s.text) LIKE '%PUT_LINE%'
                    OR UPPER(s.text) LIKE '%PORT 21%'
                    OR UPPER(s.text) LIKE '%PORT 22%'
                    OR UPPER(s.text) LIKE '%PORT, 21%'
                    OR UPPER(s.text) LIKE '%PORT, 22%'
                )
                AND owner NOT IN ({schemas_placeholders})
                ORDER BY s.owner, s.name, s.line
            """, bind_vars)
            rows = cursor.fetchall()
            if rows:
                objects = list({(r[0], r[1], r[2]) for r in rows})
                details = [f"  - [{obj_type}] {owner}.{name}" for owner, name, obj_type in sorted(objects)]
                #samples = [f"    Line {line}: {sanitize_sample(text)}" for _, _, _, line, text in rows[:5]]
                samples = [f"    Line {line}: {text}" for _, _, _, line, text in rows[:5]]
                blockers.append({
                    "feature": "FTP/SFTP Usage in Stored Code",
                    "blocker": (
                        f"FTP/SFTP related keywords detected in "
                        f"{len(objects)} stored object(s). "
                        f"These may use UTL_TCP or DBMS_FILE_TRANSFER "
                        f"for file transfers not supported on RDS."
                    ),
                    "severity": "High",
                    "recommendation": (
                        "Review and refactor the following objects:\n"
                        + "\n".join(details)
                        + "\n\n  Replace with:\n"
                        "  1. AWS Transfer Family for SFTP/FTP endpoints\n"
                        "  2. UTL_HTTP + S3 pre-signed URLs for file uploads\n"
                        "  3. AWS Lambda triggered by S3 events for file processing"
                    ),
                })
 
            cursor.execute("""
                SELECT a.host, a.lower_port, a.upper_port, a.acl, p.principal, p.privilege, p.is_grant
                FROM dba_network_acls a
                JOIN dba_network_acl_privileges p ON a.acl = p.acl
                WHERE (
                    a.lower_port IN (20, 21, 22) OR a.upper_port IN (20, 21, 22)
                    OR (a.lower_port <= 20 AND a.upper_port >= 22)
                )
                ORDER BY a.host, a.lower_port
            """)
            rows = cursor.fetchall()
            if rows:
                details = [
                    f"  - Host: {host:<30} Ports: {lower}-{upper:<6} Principal: {principal} Privilege: {privilege}"
                    for host, lower, upper, acl, principal, privilege, is_grant in rows
                ]
                blockers.append({
                    "feature": "FTP/SFTP ACL Network Access",
                    "blocker": (
                        f"{len(rows)} ACL rule(s) found allowing FTP (port 20/21) "
                        f"or SFTP (port 22) network access. "
                        f"RDS does not support outbound FTP/SFTP connections."
                    ),
                    "severity": "High",
                    "recommendation": (
                        "Remove FTP/SFTP ACL rules. Use AWS Transfer Family\n"
                        "or S3 pre-signed URLs for file transfer needs.\n"
                        "ACL rules found:\n" + "\n".join(details)
                    ),
                })
        except:
            pass
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
    return blockers

def datatype_used_by_tablespace(dbName):
    con = None
    cursor = None
    try:
        val = selectConn(dbName)
        con = val[0]
        cursor = con.cursor()
        datatypes = []
        
        try:
            
            cursor.execute("""
                WITH assessment_schemas AS (
                    SELECT username
                    FROM dba_users
                    WHERE oracle_maintained = 'N'
                    AND username NOT IN ('SQLTXPLAIN', 'PERFSTAT')
                )
                SELECT NVL(t.tablespace_name, 'PARTITIONED/DEFAULT') AS tablespace_name,
                    c.data_type,
                    COUNT(DISTINCT c.owner || '.' || c.table_name) AS num_tables,
                    COUNT(*) AS num_columns
                FROM dba_tab_columns c
                JOIN dba_tables t
                ON t.owner = c.owner
                AND t.table_name = c.table_name
                JOIN assessment_schemas a
                ON a.username = c.owner
                WHERE c.table_name NOT LIKE 'BIN$%'
                GROUP BY NVL(t.tablespace_name, 'PARTITIONED/DEFAULT'),
                        c.data_type
                ORDER BY tablespace_name,
                        num_columns DESC,
                        c.data_type
            """)
            datatypes = cursor.fetchall()            
        except:
            pass
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
    return datatypes

def get_special_datatypes(dbName):
    con = None
    cursor = None
    try:
        val = selectConn(dbName)
        con = val[0]
        cursor = con.cursor()
        special_datatypes_list = []
        
        try:
            
            cursor.execute("""
                WITH assessment_schemas AS (
                    SELECT username
                    FROM dba_users
                    WHERE oracle_maintained = 'N'
                    AND username NOT IN ('SQLTXPLAIN', 'PERFSTAT')
                )
                SELECT NVL(t.tablespace_name, 'PARTITIONED/DEFAULT') AS tablespace_name,
                    c.owner,
                    c.table_name,
                    c.column_name,
                    CASE
                        WHEN c.data_type_owner IS NOT NULL
                        THEN c.data_type_owner || '.' || c.data_type
                        ELSE c.data_type
                    END AS data_type,
                    c.data_length
                FROM dba_tab_columns c
                JOIN dba_tables t
                ON t.owner = c.owner
                AND t.table_name = c.table_name
                JOIN assessment_schemas a
                ON a.username = c.owner
                WHERE (
                        c.data_type IN (
                            'BLOB',
                            'CLOB',
                            'NCLOB',
                            'BFILE',
                            'LONG',
                            'LONG RAW',
                            'XMLTYPE',
                            'ANYDATA',
                            'URITYPE'
                        )
                        OR (c.data_type_owner = 'MDSYS'
                            AND c.data_type = 'SDO_GEOMETRY')
                    )
                AND c.table_name NOT LIKE 'BIN$%'
                ORDER BY tablespace_name,
                        c.owner,
                        c.table_name,
                        c.column_id

            """)
            special_datatypes_list = cursor.fetchall()            
        except:
            pass
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
    return special_datatypes_list

def get_lobs_columns_size(dbName):
    con = None
    cursor = None
    try:
        val = selectConn(dbName)
        con = val[0]
        cursor = con.cursor()
        lobs_columns_size_list = []
        
        try:
            
            cursor.execute("""
                WITH assessment_schemas AS (
                    SELECT username
                    FROM dba_users
                    WHERE oracle_maintained = 'N'
                    AND username NOT IN ('SQLTXPLAIN', 'PERFSTAT')
                ),
                lob_segment_size AS (
                    SELECT owner,
                        segment_name,
                        SUM(bytes) AS bytes
                    FROM dba_segments
                    WHERE segment_type LIKE 'LOB%'
                    GROUP BY owner,
                            segment_name
                )
                SELECT NVL(t.tablespace_name, 'PARTITIONED/DEFAULT') AS tablespace_name,
                    l.owner,
                    l.table_name,
                    l.column_name,
                    l.segment_name AS lob_segment,
                    l.tablespace_name AS lob_tablespace,
                    l.securefile,
                    l.in_row,
                    ROUND(NVL(s.bytes, 0) / POWER(1024, 3), 2) AS lob_size_gb
                FROM dba_lobs l
                JOIN dba_tables t
                ON t.owner = l.owner
                AND t.table_name = l.table_name
                JOIN assessment_schemas a
                ON a.username = l.owner
                LEFT JOIN lob_segment_size s
                ON s.owner = l.owner
                AND s.segment_name = l.segment_name
                WHERE l.table_name NOT LIKE 'BIN$%'
                ORDER BY lob_size_gb DESC,
                        l.owner,
                        l.table_name,
                        l.column_name
            """)
            lobs_columns_size_list = cursor.fetchall()            
        except:
            pass
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
    return lobs_columns_size_list

def get_user_defined_columns(dbName):
    con = None
    cursor = None
    try:
        val = selectConn(dbName)
        con = val[0]
        cursor = con.cursor()
        user_defined_columns_list = []
        
        try:
            
            cursor.execute("""
                WITH assessment_schemas AS (
                    SELECT username
                    FROM dba_users
                    WHERE oracle_maintained = 'N'
                    AND username NOT IN ('SQLTXPLAIN', 'PERFSTAT')
                ),
                application_type_owners AS (
                    SELECT username
                    FROM dba_users
                    WHERE oracle_maintained = 'N'
                )
                SELECT NVL(t.tablespace_name, 'PARTITIONED/DEFAULT') AS tablespace_name,
                    c.owner,
                    c.table_name,
                    c.column_name,
                    c.data_type_owner,
                    c.data_type
                FROM dba_tab_columns c
                JOIN dba_tables t
                ON t.owner = c.owner
                AND t.table_name = c.table_name
                JOIN assessment_schemas a
                ON a.username = c.owner
                JOIN application_type_owners ato
                ON ato.username = c.data_type_owner
                WHERE c.data_type_owner IS NOT NULL
                AND c.table_name NOT LIKE 'BIN$%'
                ORDER BY tablespace_name,
                        c.owner,
                        c.table_name,
                        c.column_id
            """)
            user_defined_columns_list = cursor.fetchall()            
        except:
            pass
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
    return user_defined_columns_list

def get_invisible_table_columns(dbName):
    con = None
    cursor = None
    try:
        val = selectConn(dbName)
        con = val[0]
        cursor = con.cursor()
        invisible_table_columns_list = []
        
        try:
            
            cursor.execute("""
                WITH assessment_schemas AS (
                    SELECT username
                    FROM dba_users
                    WHERE oracle_maintained = 'N'
                    AND username NOT IN ('SQLTXPLAIN', 'PERFSTAT')
                )
                SELECT NVL(t.tablespace_name, 'PARTITIONED/DEFAULT') AS tablespace_name,
                    c.owner,
                    c.table_name,
                    c.column_name,
                    CASE
                        WHEN c.data_type_owner IS NOT NULL
                        THEN c.data_type_owner || '.' || c.data_type
                        ELSE c.data_type
                    END AS data_type,
                    c.virtual_column,
                    c.hidden_column
                FROM dba_tab_cols c
                JOIN dba_tables t
                ON t.owner = c.owner
                AND t.table_name = c.table_name
                JOIN assessment_schemas a
                ON a.username = c.owner
                WHERE (c.virtual_column = 'YES'
                    OR c.hidden_column = 'YES')
                AND c.user_generated = 'YES'
                AND c.table_name NOT LIKE 'BIN$%'
                ORDER BY tablespace_name,
                        c.owner,
                        c.table_name,
                        c.internal_column_id
            """)
            invisible_table_columns_list = cursor.fetchall()            
        except:
            pass
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
    return invisible_table_columns_list

def get_tables_with_column_level_tde_encryption(dbName):
    con = None
    cursor = None
    try:
        val = selectConn(dbName)
        con = val[0]
        cursor = con.cursor()
        tables = []
        
        try:
            
            cursor.execute("""
                WITH assessment_schemas AS (
                    SELECT username
                    FROM dba_users
                    WHERE oracle_maintained = 'N'
                    AND username NOT IN ('SQLTXPLAIN', 'PERFSTAT')
                )
                SELECT NVL(t.tablespace_name, 'PARTITIONED/DEFAULT') AS tablespace_name,
                    e.owner,
                    e.table_name,
                    e.column_name,
                    e.encryption_alg,
                    e.salt,
                    e.integrity_alg
                FROM dba_encrypted_columns e
                JOIN dba_tables t
                ON t.owner = e.owner
                AND t.table_name = e.table_name
                JOIN assessment_schemas a
                ON a.username = e.owner
                WHERE e.table_name NOT LIKE 'BIN$%'
                ORDER BY tablespace_name,
                        e.owner,
                        e.table_name,
                        e.column_name
            """)
            tables = cursor.fetchall()            
        except:
            pass
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
    return tables

def get_tables_with_basicfile_lob(dbName):
    con = None
    cursor = None
    try:
        val = selectConn(dbName)
        con = val[0]
        cursor = con.cursor()
        basicfile_lobs = []
        
        try:
            schemas_placeholders = ",".join(f":s{i}" for i in range(len(SYSTEM_SCHEMAS)))
            bind_vars = {f"s{i}": schema for i, schema in enumerate(SYSTEM_SCHEMAS)}
            cursor.execute(f"""
                SELECT owner,table_name, column_name, segment_name, tablespace_name, securefile 
                FROM All_lobs WHERE SECUREFILE = 'NO' and owner not in ({schemas_placeholders})
            """, bind_vars)
            basicfile_lobs = cursor.fetchall()            
        except:
            pass
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
    return basicfile_lobs

def _parse_gib(value):
    if pd.isna(value):
        return 0.0
    return float(str(value).replace("GiB", "").strip())
 
 
def _parse_int(value):
    if pd.isna(value):
        return 0
    return int(str(value).split()[0])
 
 
def _parse_price(value):
    if pd.isna(value):
        return 0.0
    return float(str(value).replace("$", "").replace(",", "").strip())
 
 
def _load_rds_instances() -> dict:
    excel_path = os.path.join(agent_base, "AWS_RDS_Oracle.xlsx")
    df = pd.read_excel(excel_path)
    df.columns = df.columns.str.strip()
 
    required_columns = ["Instances", "vCPU", "Memory", "Network Performance", "Price Per Hour", "Instance Type"]
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing columns in Excel: {missing_cols}")
 
    instances = {}
    for _, row in df.iterrows():
        instance_name = row["Instances"]
        instances[instance_name] = {
            "instance_class": instance_name,
            "vcpus": _parse_int(row["vCPU"]),
            "memory_gb": _parse_gib(row["Memory"]),
            "network_performance": row["Network Performance"],
            "price_per_hour": _parse_price(row["Price Per Hour"]),
            "instance_type": row["Instance Type"],
            "max_iops": 12000,
        }
    return instances
 
 
RDS_INSTANCES: dict = _load_rds_instances()
 
 
def _to_float(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)
 
 
def _calculate_cpu_utilization_from_awr(sizing_data: list) -> dict | None:
    if not sizing_data:
        return None
 
    latest = sizing_data[0]
    num_cpus = _to_float(latest.get("cpunumber") or 2)
 
    valid_snapshots = [
        s for s in sizing_data
        if (
            _to_float(s.get("total_cpu_time_seconds", 0)) > 0
            and _to_float(s.get("elapsed_seconds", 0)) > 0
        )
    ]
 
    if not valid_snapshots:
        logger.warning("No valid DB CPU + Background CPU time data, using host CPU metrics")
        cpu_utilizations = []
        for snapshot in sizing_data:
            host_cpu_avg = _to_float(snapshot.get("hostcpupctavg_hourly") or 0)
            effective_cores_avg = num_cpus * (host_cpu_avg / 100.0)
            cpu_utilizations.append({"cpu_percent": host_cpu_avg, "effective_cores": effective_cores_avg})
 
        peak_cpu_percent = max(_to_float(s.get("hostcpupctmax_hourly", 0)) for s in sizing_data)
        avg_cpu_percent = statistics.mean(_to_float(s.get("hostcpupctavg_hourly", 0)) for s in sizing_data)
        peak_effective_cores = max(u["effective_cores"] for u in cpu_utilizations)
        avg_effective_cores = statistics.mean(u["effective_cores"] for u in cpu_utilizations)
        db_cpu_avg_percent = 0.0
        background_cpu_avg_percent = 0.0
        data_source = "dba_hist_sysmetric_summary"
    else:
        cpu_utilizations = []
        for snapshot in valid_snapshots:
            cpu_utilizations.append({
                "cpu_percent": _to_float(snapshot.get("calculated_cpu_percent") or 0),
                "effective_cores": _to_float(snapshot.get("effective_cores") or 0),
                "db_cpu_percent": _to_float(snapshot.get("db_cpu_percent") or 0),
                "background_cpu_percent": _to_float(snapshot.get("background_cpu_percent") or 0),
            })
 
        peak_cpu_percent = max(u["cpu_percent"] for u in cpu_utilizations)
        avg_cpu_percent = statistics.mean(u["cpu_percent"] for u in cpu_utilizations)
        peak_effective_cores = max(u["effective_cores"] for u in cpu_utilizations)
        avg_effective_cores = statistics.mean(u["effective_cores"] for u in cpu_utilizations)
        db_cpu_avg_percent = statistics.mean(u["db_cpu_percent"] for u in cpu_utilizations)
        background_cpu_avg_percent = statistics.mean(u["background_cpu_percent"] for u in cpu_utilizations)
        data_source = "dba_hist_sys_time_model (DB CPU + background cpu time)"
 
    recommended_cores = max(peak_effective_cores * 1.2, avg_effective_cores * 1.2, 1.0)
 
    valid_vcpu_counts = [2, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192]
    recommended_vcpus = next((v for v in valid_vcpu_counts if v >= recommended_cores), 2)
 
    can_use_burstable = avg_cpu_percent < 30 and peak_cpu_percent < 90
 
    return {
        "num_cpus": int(num_cpus),
        "peak_cpu_percent": round(peak_cpu_percent, 2),
        "avg_cpu_percent": round(avg_cpu_percent, 2),
        "db_cpu_avg_percent": round(db_cpu_avg_percent, 2),
        "background_cpu_avg_percent": round(background_cpu_avg_percent, 2),
        "peak_effective_cores": round(peak_effective_cores, 2),
        "avg_effective_cores": round(avg_effective_cores, 2),
        "recommended_cores_from_peak": round(peak_effective_cores * 1.2, 2),
        "recommended_cores_from_avg": round(avg_effective_cores * 1.2, 2),
        "recommended_cores_with_buffer": round(recommended_cores, 2),
        "recommended_vcpus": recommended_vcpus,
        "can_use_burstable": can_use_burstable,
        "calculation_method": "AWS AWR Miner: (DB CPU + Background CPU) / NUM_CPUS / Elapsed Time * 1.2 buffer",
        "data_source": data_source,
    }
 
 
def get_rds_recommendation_from_sizing(sizing_data: list) -> dict:
    if not sizing_data:
        return {"status": "error", "message": "No sizing data available"}
 
    try:
        latest = sizing_data[0]
 
        cpu_analysis = _calculate_cpu_utilization_from_awr(sizing_data)
        if not cpu_analysis:
            return {"status": "error", "message": "Unable to calculate CPU metrics"}
 
        required_vcpus = cpu_analysis["recommended_vcpus"]
 
        peak_read_iops = max(_to_float(s.get("rdiopsmax_hourly") or 0) for s in sizing_data)
        avg_read_iops = statistics.mean(_to_float(s.get("rdiopsavg_hourly") or 0) for s in sizing_data)
        peak_write_iops = max(_to_float(s.get("wtiopsmax_hourly") or 0) for s in sizing_data)
        avg_write_iops = statistics.mean(_to_float(s.get("wtiopsavg_hourly") or 0) for s in sizing_data)
        total_iops = peak_read_iops + peak_write_iops
        avg_total_iops = avg_read_iops + avg_write_iops
 
        sga_mb = _to_float(latest.get("sgamb") or 1024)
        pga_mb = _to_float(latest.get("pgamb") or 256)
        db_size_mb = _to_float(latest.get("tbsizeusedmb") or 1024)
        sga_gb = sga_mb / 1024.0
        pga_gb = pga_mb / 1024.0
        db_size_gb = db_size_mb / 1024.0
 
        required_memory_gb = max((sga_gb + pga_gb) * 1.2, 8.0)
 
        if total_iops <= 3000:
            storage_type = "gp3"
            provisioned_iops = 3000
        elif total_iops <= 16000:
            storage_type = "gp3"
            provisioned_iops = int(total_iops * 1.2)
        else:
            storage_type = "io2"
            provisioned_iops = int(total_iops * 1.2)
 
        storage_size_gb = max(int(db_size_gb * 1.5), 100)
 
        recommendations = []
        for instance_class, instance in RDS_INSTANCES.items():
            is_burstable = instance_class.startswith("db.t3")
            if not cpu_analysis["can_use_burstable"] and is_burstable:
                continue
            if instance["memory_gb"] < required_memory_gb or instance["vcpus"] < required_vcpus:
                continue
 
            instance_cost = instance["price_per_hour"] * 730.0
            storage_cost = storage_size_gb * 0.115
            if storage_type == "gp3" and provisioned_iops > 3000:
                storage_cost += (provisioned_iops - 3000) * 0.005
            elif storage_type == "io2":
                storage_cost = storage_size_gb * 0.125 + provisioned_iops * 0.065
            monthly_cost = instance_cost + storage_cost
 
            memory_ratio = instance["memory_gb"] / required_memory_gb
            vcpu_ratio = float(instance["vcpus"]) / float(required_vcpus)
 
            if memory_ratio > 2.5 or vcpu_ratio > 2.5:
                continue
 
            score = (
                max(0, (memory_ratio - 1.0) * 10)
                + max(0, (vcpu_ratio - 1.0) * 10)
                + (-5.0 if is_burstable and cpu_analysis["can_use_burstable"] else 0.0)
            )
 
            recommendations.append({
                "instance_class": instance["instance_class"],
                "vcpus": instance["vcpus"],
                "memory_gb": instance["memory_gb"],
                "network_performance": instance["network_performance"],
                "max_iops": instance["max_iops"],
                "estimated_monthly_cost": round(monthly_cost, 2),
                "is_burstable": is_burstable,
                "memory_ratio": round(memory_ratio, 2),
                "vcpu_ratio": round(vcpu_ratio, 2),
                "score": score,
            })
 
        if not recommendations:
            return {
                "status": "error",
                "message": f"No suitable instance found for requirements: {required_vcpus} vCPUs, {required_memory_gb:.2f}GB memory, {int(total_iops)} IOPS",
            }
 
        recommendations.sort(key=lambda x: (x["score"], x["estimated_monthly_cost"]))
        top_recommendations = recommendations[:3]
        for i, rec in enumerate(top_recommendations):
            rec["rank"] = i + 1
            del rec["score"]
            del rec["memory_ratio"]
            del rec["vcpu_ratio"]
 
        return {
            "status": "success",
            "source_metrics": {
                "database_name": latest.get("database_name", ""),
                "host_name": latest.get("host_name", ""),
                "num_cpus": cpu_analysis["num_cpus"],
                "memory_gb": round(sga_gb + pga_gb, 2),
                "sga_gb": round(sga_gb, 2),
                "pga_gb": round(pga_gb, 2),
                "db_size_gb": round(db_size_gb, 2),
                "peak_cpu_percent": cpu_analysis["peak_cpu_percent"],
                "avg_cpu_percent": cpu_analysis["avg_cpu_percent"],
                "peak_read_iops": int(peak_read_iops),
                "avg_read_iops": int(avg_read_iops),
                "peak_write_iops": int(peak_write_iops),
                "avg_write_iops": int(avg_write_iops),
                "peak_total_iops": int(total_iops),
                "avg_total_iops": int(avg_total_iops),
            },
            "cpu_analysis": {
                "methodology": "AWS AWR Miner",
                "data_source": cpu_analysis["data_source"],
                "num_cpus": cpu_analysis["num_cpus"],
                "total_cpu_percent": cpu_analysis["avg_cpu_percent"],
                "db_cpu_percent": cpu_analysis["db_cpu_avg_percent"],
                "background_cpu_percent": cpu_analysis["background_cpu_avg_percent"],
                "peak_cpu_percent": cpu_analysis["peak_cpu_percent"],
                "peak_effective_cores": cpu_analysis["peak_effective_cores"],
                "avg_effective_cores": cpu_analysis["avg_effective_cores"],
                "recommended_cores_with_buffer": cpu_analysis["recommended_cores_with_buffer"],
                "can_use_burstable": cpu_analysis["can_use_burstable"],
                "formula": "Total_CPU = DB_CPU + Background_CPU, CPU% = Total_CPU / NUM_CPUS / Elapsed_Time × 100, Effective_Cores = Total_CPU / Elapsed_Time, Recommended = Effective_Cores × 1.2",
            },
            "requirements": {
                "required_memory_gb": round(required_memory_gb, 2),
                "required_vcpus": int(required_vcpus),
                "required_iops": int(total_iops),
                "cpu_reasoning": (
                    f"AWS methodology: {cpu_analysis['peak_effective_cores']} effective cores "
                    f"× 1.2 buffer = {cpu_analysis['recommended_cores_with_buffer']} cores → {required_vcpus} vCPUs"
                ),
            },
            "storage": {
                "type": str(storage_type),
                "size_gb": int(storage_size_gb),
                "provisioned_iops": int(provisioned_iops) if provisioned_iops > 3000 else None,
                "reasoning": f"Database size {db_size_gb:.2f}GB × 1.5 growth = {storage_size_gb}GB",
            },
            "recommendations": top_recommendations,
        }
 
    except Exception as e:
        logger.error(f"Error in RDS recommendation: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}
 
 
def check_awrrepo(dbName: str) -> list:
    sizing_info = []
    con = None
    cursor = None
 
    try:
        val = selectConn(dbName)
        con = val[0]
        cursor = con.cursor()
 
        cursor.execute("""
            WITH view_sysstat AS (
                SELECT ss.dbid, ss.snap_id, ss.instance_number,
                    SUM(CASE WHEN metric_name = 'Physical Read Total IO Requests Per Sec' THEN maxval END) rdiopsmax,
                    SUM(CASE WHEN metric_name = 'Physical Read Total IO Requests Per Sec' THEN average END) rdiopsavg,
                    SUM(CASE WHEN metric_name = 'Physical Write Total IO Requests Per Sec' THEN maxval END) wtiopsmax,
                    SUM(CASE WHEN metric_name = 'Physical Write Total IO Requests Per Sec' THEN average END) wtiopsavg,
                    SUM(CASE WHEN metric_name = 'Physical Read Total Bytes Per Sec' THEN maxval END) rdbtpsmax,
                    SUM(CASE WHEN metric_name = 'Physical Read Total Bytes Per Sec' THEN average END) rdbtpsavg,
                    SUM(CASE WHEN metric_name = 'Physical Write Total Bytes Per Sec' THEN maxval END) wtbtpsmax,
                    SUM(CASE WHEN metric_name = 'Physical Write Total Bytes Per Sec' THEN average END) wtbtpsavg,
                    SUM(CASE WHEN metric_name = 'Redo Generated Per Sec' THEN maxval END) redobtpsmax,
                    SUM(CASE WHEN metric_name = 'Redo Generated Per Sec' THEN average END) redobtpsavg,
                    SUM(CASE WHEN metric_name = 'Host CPU Utilization (%)' THEN maxval END) hostcpumax,
                    SUM(CASE WHEN metric_name = 'Host CPU Utilization (%)' THEN average END) hostcpuavg
                FROM dba_hist_sysmetric_summary ss
                WHERE ss.metric_name IN (
                    'Physical Read Total IO Requests Per Sec',
                    'Physical Write Total IO Requests Per Sec',
                    'Physical Read Total Bytes Per Sec',
                    'Physical Write Total Bytes Per Sec',
                    'Redo Generated Per Sec',
                    'Host CPU Utilization (%)'
                )
                GROUP BY ss.dbid, ss.snap_id, ss.instance_number
            ),
            view_osstat AS (
                SELECT os.dbid, os.snap_id, os.instance_number,
                    MAX(CASE WHEN stat_name = 'NUM_CPU_SOCKETS' THEN value END) cpusocket,
                    MAX(CASE WHEN stat_name = 'NUM_CPU_CORES' THEN value END) cpucore,
                    MAX(CASE WHEN stat_name = 'NUM_CPUS' THEN value END) cpunumber,
                    MAX(CASE WHEN stat_name = 'PHYSICAL_MEMORY_BYTES' THEN ROUND(value/1024/1024,0) END) rammb
                FROM dba_hist_osstat os
                WHERE os.stat_name IN (
                    'NUM_CPUS',
                    'NUM_CPU_CORES',
                    'NUM_CPU_SOCKETS',
                    'PHYSICAL_MEMORY_BYTES'
                )
                GROUP BY os.dbid, os.snap_id, os.instance_number
            ),
            view_sga AS (
                SELECT snap_id, dbid, instance_number, SUM(bytes) value
                FROM dba_hist_sgastat
                GROUP BY snap_id, dbid, instance_number
            ),
            view_pga AS (
                SELECT snap_id, dbid, instance_number, value
                FROM dba_hist_pgastat
                WHERE name = 'total PGA allocated'
            ),
            view_dbsize AS (
                SELECT ROUND(SUM(bytes)/1024/1024) tbsizeusedmb
                FROM dba_segments
            ),
            view_cpu_time_raw AS (
                SELECT
                    tm.dbid,
                    tm.snap_id,
                    tm.instance_number,
                    tm.stat_name,
                    tm.value,
                    tm.value - LAG(tm.value) OVER (
                        PARTITION BY tm.dbid, tm.instance_number, tm.stat_name
                        ORDER BY tm.snap_id
                    ) as value_delta
                FROM dba_hist_sys_time_model tm
                WHERE tm.stat_name IN ('DB CPU', 'background cpu time', 'DB time')
            ),
            view_cpu_time AS (
                SELECT
                    dbid,
                    snap_id,
                    instance_number,
                    MAX(CASE WHEN stat_name = 'DB CPU' THEN value_delta / 1000000 END) as db_cpu_time_seconds,
                    MAX(CASE WHEN stat_name = 'background cpu time' THEN value_delta / 1000000 END) as background_cpu_time_seconds,
                    MAX(CASE WHEN stat_name = 'DB time' THEN value_delta / 1000000 END) as db_time_seconds
                FROM view_cpu_time_raw
                WHERE value_delta IS NOT NULL
                GROUP BY dbid, snap_id, instance_number
            ),
            view_elapsed_time AS (
                SELECT
                    snap_id,
                    dbid,
                    instance_number,
                    begin_interval_time,
                    end_interval_time,
                    ROUND(
                        EXTRACT(DAY FROM (end_interval_time - begin_interval_time)) * 86400 +
                        EXTRACT(HOUR FROM (end_interval_time - begin_interval_time)) * 3600 +
                        EXTRACT(MINUTE FROM (end_interval_time - begin_interval_time)) * 60 +
                        EXTRACT(SECOND FROM (end_interval_time - begin_interval_time)),
                        2
                    ) as elapsed_seconds
                FROM dba_hist_snapshot
            )
            SELECT
                d.name database_name,
                i.host_name,
                vs.instance_number,
                TO_CHAR(vs.end_interval_time, 'DD-MON-YYYY HH24:MI:SS') snaptime,
                NVL(ROUND(vss2.rdiopsmax, 0), 0) rdiopsmax_hourly,
                NVL(ROUND(vss2.rdiopsavg, 0), 0) rdiopsavg_hourly,
                NVL(ROUND(vss2.wtiopsmax, 0), 0) wtiopsmax_hourly,
                NVL(ROUND(vss2.wtiopsavg, 0), 0) wtiopsavg_hourly,
                NVL(ROUND(vss2.rdbtpsmax, 0), 0) rdbtpsmax_hourly,
                NVL(ROUND(vss2.rdbtpsavg, 0), 0) rdbtpsavg_hourly,
                NVL(ROUND(vss2.wtbtpsmax, 0), 0) wtbtpsmax_hourly,
                NVL(ROUND(vss2.wtbtpsavg, 0), 0) wtbtpsavg_hourly,
                NVL(ROUND(vss2.hostcpumax, 0), 0) hostcpupctmax_hourly,
                NVL(ROUND(vss2.hostcpuavg, 0), 0) hostcpupctavg_hourly,
                NVL(ROUND(vss2.redobtpsmax, 0), 0) redobtpsmax_hourly,
                NVL(ROUND(vss2.redobtpsavg, 0), 0) redobtpsavg_hourly,
                NVL(vos2.cpusocket, 0) cpusocket,
                NVL(vos2.cpucore, 0) cpucore,
                NVL(vos2.cpunumber, 0) cpunumber,
                NVL(vos2.rammb, 0) rammb,
                NVL(ROUND(vsga.value/1024/1024, 0), 0) sgamb,
                NVL(ROUND(vpga.value/1024/1024, 0), 0) pgamb,
                NVL(dbsize.tbsizeusedmb, 0) tbsizeusedmb,
                NVL(ROUND(vct.db_cpu_time_seconds, 2), 0) db_cpu_time_seconds,
                NVL(ROUND(vct.background_cpu_time_seconds, 2), 0) background_cpu_time_seconds,
                NVL(ROUND(vct.db_time_seconds, 2), 0) db_time_seconds,
                NVL(ROUND(vet.elapsed_seconds, 2), 0) elapsed_seconds,
                NVL(ROUND(NVL(vct.db_cpu_time_seconds, 0) + NVL(vct.background_cpu_time_seconds, 0), 2), 0) total_cpu_time_seconds,
                CASE
                    WHEN vet.elapsed_seconds > 0 AND vos2.cpunumber > 0
                    THEN ROUND(((NVL(vct.db_cpu_time_seconds, 0) + NVL(vct.background_cpu_time_seconds, 0)) / vos2.cpunumber / vet.elapsed_seconds) * 100, 2)
                    ELSE 0
                END as calculated_cpu_percent,
                CASE
                    WHEN vet.elapsed_seconds > 0
                    THEN ROUND((NVL(vct.db_cpu_time_seconds, 0) + NVL(vct.background_cpu_time_seconds, 0)) / vet.elapsed_seconds, 2)
                    ELSE 0
                END as effective_cores,
                CASE
                    WHEN vet.elapsed_seconds > 0 AND vos2.cpunumber > 0
                    THEN ROUND((NVL(vct.db_cpu_time_seconds, 0) / vos2.cpunumber / vet.elapsed_seconds) * 100, 2)
                    ELSE 0
                END as db_cpu_percent,
                CASE
                    WHEN vet.elapsed_seconds > 0 AND vos2.cpunumber > 0
                    THEN ROUND((NVL(vct.background_cpu_time_seconds, 0) / vos2.cpunumber / vet.elapsed_seconds) * 100, 2)
                    ELSE 0
                END as background_cpu_percent,
                CASE
                    WHEN vet.elapsed_seconds > 0 AND vos2.cpunumber > 0
                    THEN ROUND((NVL(vct.db_time_seconds, 0) / vos2.cpunumber / vet.elapsed_seconds) * 100, 2)
                    ELSE 0
                END as db_time_percent
            FROM dba_hist_snapshot vs
            CROSS JOIN v$database d
            CROSS JOIN view_dbsize dbsize
            LEFT JOIN view_sysstat vss2
                ON vs.dbid = vss2.dbid AND vs.snap_id = vss2.snap_id AND vs.instance_number = vss2.instance_number
            LEFT JOIN view_osstat vos2
                ON vs.dbid = vos2.dbid AND vs.snap_id = vos2.snap_id AND vs.instance_number = vos2.instance_number
            LEFT JOIN view_sga vsga
                ON vs.dbid = vsga.dbid AND vs.snap_id = vsga.snap_id AND vs.instance_number = vsga.instance_number
            LEFT JOIN view_pga vpga
                ON vs.dbid = vpga.dbid AND vs.snap_id = vpga.snap_id AND vs.instance_number = vpga.instance_number
            LEFT JOIN view_cpu_time vct
                ON vs.dbid = vct.dbid AND vs.snap_id = vct.snap_id AND vs.instance_number = vct.instance_number
            LEFT JOIN view_elapsed_time vet
                ON vs.dbid = vet.dbid AND vs.snap_id = vet.snap_id AND vs.instance_number = vet.instance_number
            LEFT JOIN gv$instance i
                ON i.instance_number = vs.instance_number
            WHERE vs.dbid = d.dbid
            ORDER BY vs.snap_id DESC
        """)
 
        columns = [col[0].lower() for col in cursor.description]
        rows = cursor.fetchall()
 
        for row in rows:
            record = dict(zip(columns, row))
            for key, value in record.items():
                if value is None:
                    record[key] = "" if key in ("database_name", "host_name", "snaptime") else 0
            sizing_info.append(record)
 
        logger.info(f"Fetched {len(sizing_info)} AWR snapshots for {dbName}")
 
    except Exception as e:
        logger.error(f"Error in check_awrrepo: {str(e)}")
 
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
 
    return sizing_info
  
def get_rds_recommendation(dbName: str) -> dict:
    try:
        sizing_data = check_awrrepo(dbName)
        if not sizing_data:
            return {
                "status": "error",
                "message": "No AWR data available. Ensure AWR is enabled and snapshots exist.",
            }
        return get_rds_recommendation_from_sizing(sizing_data)
    except Exception as e:
        logger.error(f"Error getting RDS recommendation: {str(e)}")
        return {"status": "error", "message": str(e)}
 
# DB Assessment Code END

def selectConn(dbname):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user,passwd,servicename FROM CONN WHERE dbname=:dbname', {"dbname": dbname})
    db_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not db_row:
        raise HTTPException(
            status_code=404,
            detail=f"No connection details found for database '{dbname}'"
        )

    user = db_row[0]
    passwd = cipher.decrypt(db_row[1])
    servicename = db_row[2]
    
    try:
        if ':' in servicename and '/' in servicename:
            hostTmp = servicename.split('/')[0]
            port = hostTmp.split(':')[1]
            host = hostTmp.split(':')[0]
            servicename = servicename.split('/')[1]
            params = oracledb.ConnectParams(host=host,port=port,service_name=servicename,sdu=65535)
            dsn = params.get_connect_string()
        else:
            dsn = servicename
        raw_con = oracledb.connect(user=user, password=passwd, dsn=dsn)
        engine = create_engine(f"oracle+oracledb://{user}:{passwd}@{dsn}")
        con = engine.connect()

        db_det = '''SELECT version from v$instance'''
        db_det_fetch = pd.read_sql(db_det, con)
        db_ver = db_det_fetch.iloc[0]['version'].split('.')
        db_main_ver = db_ver[0]
        db_minor_ver = db_ver[3]

    except Exception as e:
        logger.info(str(e))
        raise HTTPException(
            status_code=502,
            detail=f"Database connection failed for '{dbname}': {str(e)}"
        )

    return [raw_con, db_main_ver, db_minor_ver,con,user]

# Compare pad code start


class AddAgentRequest(BaseModel):
    agent_name: str
    port: str
    dbname: str

@app.post("/api/v2/add-agent", status_code=201, tags=["MigDB ComparePad Agent Management"],
    summary="Add a new agent",
    description="Registers a new agent with its name, port, and database alias in the agents table.")
def add_agent(body: AddAgentRequest):
    agent_name = body.agent_name.strip().lower().replace(" ", "_")
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO agents (agent_name, port, db_alias) VALUES (?, ?, ?)",
            (agent_name, body.port, body.dbname)
        )
        conn.commit()

    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Agent already exists or duplicate entry")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            cursor.close()
            conn.close()

    return {"status": "success", "message": "Agent added successfully"}

@app.get("/api/v2/get-agents", tags=["MigDB ComparePad Agent Management"],
    summary="List all agents",
    description="Returns all registered agents with their name, port, and database alias from the agents table.")
def get_agents():
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT agent_name, port, db_alias FROM agents")
        rows = cursor.fetchall()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            cursor.close()
            conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No Agents Found")

    return {
        "status": "success",
        "data": [
            {"agent_name": row[0], "port": row[1], "db_alias": row[2]}
            for row in rows
        ]
    }


class GetAgentUserNamePasswordRequest(BaseModel):
    db_alias: str

@app.post("/api/v2/get-agent-credentials", tags=["MigDB ComparePad Agent Management"],
    summary="Get agent database credentials",
    description="Fetches and decrypts the database credentials for a given agent database alias from the CONN table.")
def get_agent_credentials(body: GetAgentUserNamePasswordRequest):
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT dbname, user, passwd, servicename FROM CONN WHERE dbname = ?",
            (body.db_alias,)
        )
        row = cursor.fetchone()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            cursor.close()
            conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="No DB Found")

    return {
        "status": "success",
        "data": {
            "dbname":      row[0],
            "username":    row[1],
            "password":    cipher.decrypt(row[2]) if row[2] else None,
            "servicename": row[3],
        }
    }

class GetDBNameUsePortRequest(BaseModel):
    port: str

@app.post("/api/v2/get-db-name-by-port", tags=["MigDB ComparePad Agent Management"],
    summary="Get database alias by port",
    description="Looks up and returns the database alias associated with the given agent port from the agents table.")
def get_db_name_by_port(body: GetDBNameUsePortRequest):
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT db_alias FROM agents WHERE port = ?", (body.port,))
        row = cursor.fetchone()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            cursor.close()
            conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="No DB Alias Found")

    return {"status": "success", "data": {"db_alias": row[0]}}

@app.get("/api/v2/get-db-names", tags=["MigDB Database"],
    summary="List all database names",
    description="Returns all database names and service names registered in the CONN table.")
def get_db_names():
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT dbname, servicename FROM CONN")
        rows = cursor.fetchall()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            cursor.close()
            conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No DB Names Found")

    return {
        "status": "success",
        "data": [{"dbname": row[0], "servicename": row[1]} for row in rows]
    }


@app.get("/api/v2/get-comparepad-connection", tags=["MigDB ComparePad Agent Management"],
    summary="Get and verify ComparePad connection",
    description="Fetches the ComparePad credentials and URL from the database, verifies the connection is reachable, and returns the connection status and URL.",
    operation_id="get_comparepad_conn")
def get_comparepad_connection():
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user, passwd, dep_url FROM ONEPCONN WHERE dbtype = ?",
            ("comparepad",)
        )
        db_row = cursor.fetchone()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    finally:
        if conn:
            cursor.close()
            conn.close()

    if not db_row:
        raise HTTPException(status_code=404, detail="ComparePad configuration not found in database.")

    user, encrypted_passwd, compare_pad_url = db_row
    decrypted_passwd = cipher.decrypt(encrypted_passwd)

    try:
        response = requests.get(compare_pad_url, timeout=5)
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Connection failed. Status code: {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Unable to connect to ComparePad URL: {str(e)}")

    return {
        "status": "success",
        "message": "Connection successful.",
        "url": compare_pad_url
    }

# Compare pad code END


def selectConnPool(dbname, parallel):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user,passwd,servicename FROM CONN WHERE dbname=:dbname', {"dbname": dbname})
    db_row = cursor.fetchone()
    cursor.close()
    conn.close()
    con = ''
    db_main_ver = ''
    db_minor_ver = ''
    user = ''
    if db_row:
        user = db_row[0]
        passwd = db_row[1]
        passwd = cipher.decrypt(passwd)
        servicename = db_row[2]
        try:
            pool = oracledb.SessionPool(user, passwd, servicename, min=parallel, max=parallel, increment=0,
                                         threaded=True, getmode=oracledb.SPOOL_ATTRVAL_WAIT)
        except oracledb.DatabaseError as e:
            logger.info(str(e))
    return [pool]


def large_csv_upload_to_s3(jobName, dbName, rsAlias, cdbCheck, pdbName, bucketName, chunk_id, aws_access_key_id,
                           aws_secret_access_key, table_owner, table_name, start_rowid, end_rowid, tgt_dep_url,
                           startTime, parallel):
    try:
        con = selectConn(dbName)[0]
        cursor = con.cursor()
        if cdbCheck == 'YES' and len(pdbName) > 0:
            cursor.execute('''alter session set container=''' + pdbName)
            statFileName = os.path.join(agent_home, jobName,
                                        pdbName + '.' + table_owner + '.' + table_name + '=+!' + str(
                                            chunk_id) + '_stats')
        else:
            statFileName = os.path.join(agent_home, jobName,
                                        table_owner + '.' + table_name + '=+!' + str(chunk_id) + '_stats')
        chunk_proc = '''select * from ''' + table_owner + '.' + table_name + ''' where rowid between :start_rowid  and :end_rowid'''
        param = {"start_rowid": start_rowid, "end_rowid": end_rowid}
        df = pd.read_sql_query(chunk_proc, con, params=[param["start_rowid"], param["end_rowid"]])
        loadSize = str(len(df.index))
        if df.empty == False:
            csv_buffer = BytesIO()
            with gzip.GzipFile(mode='w', fileobj=csv_buffer) as zipped_file:
                df.to_csv(TextIOWrapper(zipped_file, 'utf8'), index=False, header=False)
            fileName = table_owner + '.' + table_name + str(chunk_id) + '.csv'
            s3 = boto3.resource('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
            s3_object = s3.Object(bucketName, fileName).put(Body=csv_buffer.getvalue())
            endTime = datetime.now(timezone.utc)
            endTime = endTime.strftime('%Y-%m-%d:%H:%M:%S')
            dep_url = tgt_dep_url + '/addlargecsvilproc'
            payload = {"jobName": jobName, "cdbCheck": cdbCheck, "pdbName": pdbName, "chunk_id": chunk_id,
                       "table_owner": table_owner, "table_name": table_name, "rsAlias": rsAlias, "fileName": fileName,
                       "currentAWSBucket": bucketName, "aws_access_key_id": aws_access_key_id,
                       "aws_secret_access_key": aws_secret_access_key, "loadSize": loadSize, "startTime": startTime}
            headers = get_internal_headers() 
            r = requests.post(dep_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
        else:
            endTime = datetime.now(timezone.utc)
            endTime = endTime.strftime('%Y-%m-%d:%H:%M:%S')
    except Exception as e:
        pass
    finally:
        if con:
            datetimeFormat = '%Y-%m-%d:%H:%M:%S'
            elapTime = datetime.strptime(str(endTime), datetimeFormat) - datetime.strptime(startTime, datetimeFormat)
            elapTime = elapTime.total_seconds()
            with open(statFileName, 'w') as infile:
                infile.write(loadSize + '-' + str(elapTime))
            cursor.callproc('DBMS_PARALLEL_EXECUTE.set_chunk_status', [jobName, chunk_id, 2]);
            cursor.close()
            con.close()


def small_csv_upload_to_s3(jobName, dbName, rsAlias, cdbCheck, pdbName, bucketName, aws_access_key_id,
                           aws_secret_access_key, table_name, tgt_dep_url):
    try:
        con = selectConn(dbName)[0]
        cursor = con.cursor()
        if cdbCheck == 'YES' and len(pdbName) > 0:
            cursor.execute('''alter session set container=''' + pdbName)
            statFileName = os.path.join(agent_home, jobName, pdbName + '.' + table_name + '=+!' + '_stats')
        else:
            statFileName = os.path.join(agent_home, jobName, table_name + '=+!' + '_stats')
        chunk_proc = '''select * from {}'''.format(table_name)
        startTime = datetime.now(timezone.utc)
        startTime = startTime.strftime('%Y-%m-%d:%H:%M:%S')
        df = pd.read_sql_query(chunk_proc, con)
        loadSize = str(len(df.index))
        if df.empty == False:
            csv_buffer = BytesIO()
            with gzip.GzipFile(mode='w', fileobj=csv_buffer) as zipped_file:
                df.to_csv(TextIOWrapper(zipped_file, 'utf8'), index=False, header=False)
            fileName = table_name + '.csv'
            s3 = boto3.resource('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
            s3_object = s3.Object(bucketName, fileName).put(Body=csv_buffer.getvalue())
            endTime = datetime.now(timezone.utc)
            endTime = endTime.strftime('%Y-%m-%d:%H:%M:%S')
            dep_url = tgt_dep_url + '/addsmallcsvilproc'
            payload = {"jobName": jobName, "cdbCheck": cdbCheck, "pdbName": pdbName, "table_name": table_name,
                       "rsAlias": rsAlias, "fileName": fileName, "currentAWSBucket": bucketName,
                       "aws_access_key_id": aws_access_key_id, "aws_secret_access_key": aws_secret_access_key,
                       "loadSize": loadSize, "startTime": startTime}
            headers = get_internal_headers() 
            r = requests.post(dep_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
        else:
            endTime = datetime.now(timezone.utc)
            endTime = endTime.strftime('%Y-%m-%d:%H:%M:%S')
    except Exception as e:
        pass
    finally:
        if con:
            datetimeFormat = '%Y-%m-%d:%H:%M:%S'
            elapTime = datetime.strptime(str(endTime), datetimeFormat) - datetime.strptime(startTime, datetimeFormat)
            elapTime = elapTime.total_seconds()
            with open(statFileName, 'w') as infile:
                infile.write(loadSize + '-' + str(elapTime))
            cursor.close()
            con.close()


def table_itter_rows(table_list_file, srcalias, rsAlias, cdbCheck, pdbName, currentAWSBucket, jobName,
                     aws_access_key_id, aws_secret_access_key, parallel, tgt_dep_url):
    try:
        con = selectConn(srcalias)[0]
        cursor = con.cursor()
        if cdbCheck == 'YES' and len(pdbName) > 0:
            cursor.execute('''alter session set container=''' + pdbName)
        if os.path.exists(table_list_file):
            df = pd.read_csv(table_list_file)
            df_sorted = df.sort_values(by=["NUM_ROWS"], ascending=False)
            tabList = []
            for i, tablename in df_sorted.iterrows():
                if int(tablename['NUM_ROWS']) > 750000:
                    create_task_cmd = """BEGIN
                                          DBMS_PARALLEL_EXECUTE.create_task (task_name => :task_name);
                                          END;"""
                    cursor.execute(create_task_cmd, task_name=jobName)
                    cursor.execute('''SELECT status FROM   user_parallel_execute_tasks where task_name=:task_name''',
                                   {"task_name": jobName})
                    status = cursor.fetchone()
                    if status:
                        if status[0] == 'CREATED':
                            create_chunks = """BEGIN
                                           DBMS_PARALLEL_EXECUTE.create_chunks_by_rowid(task_name  => :task_name,
                                                       table_owner =>  :table_owner,
                                                       table_name => :table_name,
                                                       by_row  => TRUE,
                                                       chunk_size => '500000');
                                           END;"""
                            cursor.execute(create_chunks, task_name=jobName, table_owner=tablename['OWNER'],
                                           table_name=tablename['TABLE_NAME'])
                            cursor.execute(
                                '''SELECT status FROM   user_parallel_execute_tasks where task_name=:task_name''',
                                {"task_name": jobName})
                            db_row = cursor.fetchone()
                            if db_row:
                                startTime = datetime.now(timezone.utc)
                                startTime = startTime.strftime('%Y-%m-%d:%H:%M:%S')
                                status = db_row[0]
                                if status == 'CHUNKED':
                                    chunkList = []
                                    while True:
                                        cursor.execute(
                                            """SELECT chunk_id,start_rowid,end_rowid  FROM   user_parallel_execute_chunks where task_name=:task_name and status='UNASSIGNED'""",
                                            {"task_name": jobName})
                                        db_row = cursor.fetchmany(int(parallel))
                                        chunkList = []
                                        if db_row:
                                            for chunk in db_row:
                                                ilp = mp.Process(target=large_csv_upload_to_s3, args=(
                                                jobName, srcalias, rsAlias, cdbCheck, pdbName, currentAWSBucket,
                                                chunk[0], aws_access_key_id, aws_secret_access_key, tablename['OWNER'],
                                                tablename['TABLE_NAME'], chunk[1], chunk[2], tgt_dep_url, startTime,
                                                parallel))
                                                chunkList.append(ilp)
                                                ilp.start()
                                            for ilp in chunkList:
                                                ilp.join()
                                        else:
                                            break
                                    while True:
                                        cursor.execute(
                                            """SELECT chunk_id,start_rowid,end_rowid  FROM   user_parallel_execute_chunks where task_name=:task_name and status !='PROCESSED'""",
                                            {"task_name": jobName})
                                        db_row = cursor.fetchmany(int(parallel))
                                        if db_row:
                                            time.sleep(5)
                                        else:
                                            cursor.callproc('DBMS_PARALLEL_EXECUTE.DROP_TASK', [jobName]);
                                            break
                else:
                    tabList.append(tablename['OWNER'] + '.' + tablename['TABLE_NAME'])
            args = ()
            for tab in tabList:
                args += ((jobName, srcalias, rsAlias, cdbCheck, pdbName, currentAWSBucket, aws_access_key_id,
                          aws_secret_access_key, tab, tgt_dep_url,),)
            p = mp.Pool(int(parallel))
            p.starmap(small_csv_upload_to_s3, args)
    except Exception as e:
        pass
    finally:
        if con:
            cursor.close()
            con.close()


def infoall():
    processTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with  open(os.path.join(agent_log, 'infoall'), mode='r') as infile:
        GG_Data = []
        copy = False
        for line in infile:
            if re.match('EXTRACT', line, re.IGNORECASE):
                copy = True
            elif re.match('REPLICAT', line, re.IGNORECASE):
                copy = False
                break
            if copy:
                if re.match('EXTRACT', line, re.IGNORECASE):
                    line = line.split()
                    ExtName = line[1]
                    ExtStat = line[-1]
                elif 'Lag' in line:
                    line = line.split()
                    if 'unknown'  not in line[2]:
                        extlagH, extlagM, extlagS = line[2].split(':')
                        ExtLag = int(extlagH) * 3600 + int(extlagM) * 60 + int(extlagS)
                    else:
                        ExtLag = 'unknown'
                    extchkH, extchkM, extchkS = line[4].split(':')
                    ExtChkLag = int(extchkH) * 3600 + int(extchkM) * 60 + int(extchkS)
                elif 'Redo' in line:
                    GG_Data.append({'extname': ExtName, 'extstat': ExtStat, 'extlag': ExtLag, 'extchklag': ExtChkLag,
                                    'extIncTime': processTime})
                elif 'File' in line:
                    GG_Data.append({'pmpname': ExtName, 'pmpstat': ExtStat, 'pmplag': ExtLag, 'pmpchklag': ExtChkLag,
                                    'pmpIncTime': processTime})
    with  open(os.path.join(agent_log, 'infoall'), mode='r') as infile:
        copy = False
        for line in infile:
            if re.match('REPLICAT', line, re.IGNORECASE):
                copy = True
            elif 'Manager' in line:
                copy = False
                break
            if copy:
                if re.match('REPLICAT', line, re.IGNORECASE):
                    line = line.split()
                    RepName = line[1]
                    RepStat = line[-1]
                elif 'Lag' in line:
                    line = line.split()
                    if 'unknown'  not in line[2]:
                        replagH, replagM, replagS = line[2].split(':')
                        RepLag = int(replagH) * 3600 + int(replagM) * 60 + int(replagS)
                    else:
                        RepLag = 'unknown'
                    repchkH, repchkM, repchkS = line[4].split(':')
                    RepChkLag = int(repchkH) * 3600 + int(repchkM) * 60 + int(repchkS)
                elif 'File' in line:
                    GG_Data.append({'repname': RepName, 'repstat': RepStat, 'replag': RepLag, 'repchklag': RepChkLag,
                                    'repIncTime': processTime})
    with  open(os.path.join(agent_log, 'infoall'), mode='r') as infile:
        for line in infile:
            if 'Manager' in line:
                mgr = line.split()
                if not re.match('DOWN!', mgr[2], re.IGNORECASE):
                    tcpstr = mgr[mgr.index('port') + 1]
                    rmt = tcpstr.split(':')[1].rstrip(',')
                    rmtport = rmt.split('.')[-1]
                    rmthost = rmt.rstrip(rmtport + '.')
                else:
                    rmthost = socket.gethostname()
                    try:
                        with open(os.path.join(gg_home, 'dirprm', 'mgr.prm')) as infile:
                            for line in infile:
                                if 'port' in line or 'PORT' in line:
                                    rmtport = line.split()[1]
                    except FileNotFoundError as e:
                        rmtport = 'Not configured'
                GG_Data.append({'mgrstat': mgr[2], 'mgrhost': rmthost, 'mgrport': rmtport})
    return [GG_Data]

def fetch_query_params(query, con, cast_str=True,params=None):
    df = pd.read_sql_query(query, con,params=params)
    if cast_str:
        df = df.fillna('-').astype(str)
    else:
        df = df.fillna(value=None)

    return df


def extract_file(zf, info, extract_dir):
    zf.extract(info.filename, path=extract_dir)
    out_path = os.path.join(extract_dir, info.filename)
    perm = info.external_attr >> 16
    os.chmod(out_path, perm)

def bytes2human(n):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n

def get_oracle_edition_abbr(conn):
    """
    Reads the banner from v$version using an existing connection,
    and returns the edition abbreviation (e.g. 'EE', 'SE2').
    """
    edition_map = {
        'Enterprise Edition': 'EE',
        'Standard Edition': 'SE',
        'Standard Edition 2': 'SE2',
        'Personal Edition': 'PE',
        'Express Edition': 'XE',
    }
    query = "SELECT banner FROM v$version WHERE banner LIKE 'Oracle Database%'"

    if isinstance(conn, SAConnection):
        # SQLAlchemy connection
        result = conn.execute(text(query))
        banner = result.scalar()
    else:
        # Raw DB-API connection (oracledb / cx_Oracle)
        cursor = conn.cursor()
        cursor.execute(query)
        banner = cursor.fetchone()[0]
        cursor.close()

    match = re.search(r'(Enterprise|Standard|Personal|Express)\s+Edition(\s+\d+)?', banner)
    if not match:
        return None

    edition_full = match.group(0)
    return edition_map.get(edition_full, edition_full)

mcp = FastApiMCP(app)
mcp.mount()

# Static files — mount LAST so API routes take priority
app.mount("/", StaticFiles(directory=resource_path("web"), html=True), name="web")
#app.mount("/", StaticFiles(directory="./migdb/web", html=True), name="static")

