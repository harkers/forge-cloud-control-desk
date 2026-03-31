#!/usr/bin/env python3
"""
Forge Compute Control Desk — MCP Server

MCP server exposing VM management capabilities via the Model Context Protocol.
"""

import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.types import (
    CallToolRequest,
    ListToolsRequest,
    Tool,
    TextContent,
)
import json
import asyncio

# Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "orderededge-groupware")
ZONE = os.environ.get("GCP_ZONE", "europe-west2-b")
SERVICE_ACCOUNT_FILE = os.environ.get(
    "GCP_SERVICE_ACCOUNT_JSON", "/home/stu/.config/gcp/forge-ccd-service-account.json"
)
SHEETS_SPREADSHEET_ID = os.environ.get("SHEETS_SPREADSHEET_ID")
DRIVE_EVIDENCE_FOLDER_ID = os.environ.get(
    "DRIVE_EVIDENCE_FOLDER_ID", "/home/stu/.openclaw/workspace/projects/forge-cloud-control-desk/data/evidence"
)

# Compute Engine service
compute = None


def init_compute():
    """Initialize Compute Engine API client."""
    global compute
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/compute"],
    )
    compute = build("compute", "v1", credentials=credentials)


def get_compute():
    """Get or initialize Compute Engine client."""
    if compute is None:
        init_compute()
    return compute


def list_instances() -> List[Dict[str, Any]]:
    """List all VM instances."""
    c = get_compute()
    result = c.instances().list(project=PROJECT_ID, zone=ZONE).execute()
    return result.get("items", [])


def start_instance(instance_name: str) -> Dict[str, Any]:
    """Start a VM instance."""
    c = get_compute()
    operation = c.instances().start(project=PROJECT_ID, zone=ZONE, instance=instance_name).execute()
    return operation


def stop_instance(instance_name: str) -> Dict[str, Any]:
    """Stop a VM instance."""
    c = get_compute()
    operation = c.instances().stop(project=PROJECT_ID, zone=ZONE, instance=instance_name).execute()
    return operation


def restart_instance(instance_name: str) -> Dict[str, Any]:
    """Restart a VM instance (reset)."""
    c = get_compute()
    operation = c.instances().reset(project=PROJECT_ID, zone=ZONE, instance=instance_name).execute()
    return operation


def get_instance(instance_name: str) -> Dict[str, Any]:
    """Get VM instance details."""
    c = get_compute()
    return c.instances().get(project=PROJECT_ID, zone=ZONE, instance=instance_name).execute()


# Define tools
TOOLS = [
    Tool(
        name="list_vms",
        description="List all VM instances in the project and zone",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="start_vm",
        description="Start a VM instance",
        inputSchema={
            "type": "object",
            "properties": {
                "instance_name": {"type": "string", "description": "Name of the VM instance"},
            },
            "required": ["instance_name"],
        },
    ),
    Tool(
        name="stop_vm",
        description="Stop a VM instance",
        inputSchema={
            "type": "object",
            "properties": {
                "instance_name": {"type": "string", "description": "Name of the VM instance"},
            },
            "required": ["instance_name"],
        },
    ),
    Tool(
        name="restart_vm",
        description="Restart (reset) a VM instance",
        inputSchema={
            "type": "object",
            "properties": {
                "instance_name": {"type": "string", "description": "Name of the VM instance"},
            },
            "required": ["instance_name"],
        },
    ),
    Tool(
        name="get_vm",
        description="Get detailed information about a VM instance",
        inputSchema={
            "type": "object",
            "properties": {
                "instance_name": {"type": "string", "description": "Name of the VM instance"},
            },
            "required": ["instance_name"],
        },
    ),
    Tool(
        name="list_evidence",
        description="List evidence files in the local evidence folder",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="generate_report",
        description="Generate a weekly governance report",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
]

# Create MCP server
app = Server("forge-ccd-mcp", version="1.0.0")


@app.list_tools()
async def handle_list_tools(request: ListToolsRequest) -> Dict[str, Any]:
    """Handle list tools request."""
    return {"tools": TOOLS}


@app.call_tool()
async def handle_call_tool(request: CallToolRequest) -> Dict[str, Any]:
    """Handle tool call request."""
    tool_name = request.name
    arguments = request.arguments or {}

    if tool_name == "list_vms":
        instances = list_instances()
        return {
            "content": [
                TextContent(
                    type="text",
                    text=json.dumps(
                        [
                            {
                                "name": i.get("name"),
                                "status": i.get("status"),
                                "machine_type": i.get("machineType", "").split("/")[-1],
                            }
                            for i in instances
                        ],
                        indent=2,
                    ),
                )
            ]
        }

    elif tool_name == "start_vm":
        instance_name = arguments.get("instance_name")
        if not instance_name:
            return {
                "content": [TextContent(type="text", text="Error: instance_name is required")],
                "isError": True,
            }
        operation = start_instance(instance_name)
        return {
            "content": [TextContent(type="text", text=json.dumps(operation, indent=2))],
        }

    elif tool_name == "stop_vm":
        instance_name = arguments.get("instance_name")
        if not instance_name:
            return {
                "content": [TextContent(type="text", text="Error: instance_name is required")],
                "isError": True,
            }
        operation = stop_instance(instance_name)
        return {
            "content": [TextContent(type="text", text=json.dumps(operation, indent=2))],
        }

    elif tool_name == "restart_vm":
        instance_name = arguments.get("instance_name")
        if not instance_name:
            return {
                "content": [TextContent(type="text", text="Error: instance_name is required")],
                "isError": True,
            }
        operation = restart_instance(instance_name)
        return {
            "content": [TextContent(type="text", text=json.dumps(operation, indent=2))],
        }

    elif tool_name == "get_vm":
        instance_name = arguments.get("instance_name")
        if not instance_name:
            return {
                "content": [TextContent(type="text", text="Error: instance_name is required")],
                "isError": True,
            }
        instance = get_instance(instance_name)
        return {
            "content": [TextContent(type="text", text=json.dumps(instance, indent=2, default=str))],
        }

    elif tool_name == "list_evidence":
        evidence_folder = DRIVE_EVIDENCE_FOLDER_ID
        evidence_files = []
        if os.path.exists(evidence_folder):
            for root, dirs, files in os.walk(evidence_folder):
                for file in files:
                    if file.endswith(".md"):
                        filepath = os.path.join(root, file)
                        stat = os.stat(filepath)
                        evidence_files.append(
                            {
                                "name": file,
                                "path": filepath,
                                "size": stat.st_size,
                            }
                        )
        return {
            "content": [TextContent(type="text", text=json.dumps(evidence_files, indent=2))],
        }

    elif tool_name == "generate_report":
        from datetime import datetime

        instances = list_instances()
        status_counts = {}
        for inst in instances:
            status = inst.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1

        report_content = f"""# Weekly Governance Report

**Generated:** {datetime.utcnow().isoformat()}Z
**Project:** {PROJECT_ID}
**Zone:** {ZONE}

## Summary

| Status | Count |
|--------|-------|
"""

        for status, count in sorted(status_counts.items()):
            report_content += f"| {status} | {count} |\n"

        report_content += "\n## Instance Details\n\n"

        for inst in instances:
            name = inst.get("name")
            status = inst.get("status")
            machine_type = inst.get("machineType", "").split("/")[-1]
            zone = inst.get("zone", "").split("/")[-1]
            report_content += f"- **{name}** ({zone}): {status} ({machine_type})\n"

        # Save report
        reports_folder = os.path.join(evidence_folder, "reports")
        os.makedirs(reports_folder, exist_ok=True)
        report_filename = f"governance_report_weekly_{datetime.utcnow().strftime('%Y-%m-%d')}.md"
        report_filepath = os.path.join(reports_folder, report_filename)

        with open(report_filepath, "w") as f:
            f.write(report_content)

        return {
            "content": [
                TextContent(
                    type="text", text=f"Report generated: {report_filepath}\n\n" + report_content
                )
            ]
        }

    return {
        "content": [TextContent(type="text", text=f"Unknown tool: {tool_name}")],
        "isError": True,
    }


async def main():
    """Run the MCP server."""
    print("Starting Forge Compute Control Desk MCP server...")
    print(f"Project: {PROJECT_ID}")
    print(f"Zone: {ZONE}")
    print(f"Evidence folder: {DRIVE_EVIDENCE_FOLDER_ID}")
    print("MCP server ready. Waiting for connections...")
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
