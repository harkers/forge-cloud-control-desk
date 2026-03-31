# MCP Server for Forge Compute Control Desk

## Overview

This MCP server exposes VM management capabilities via the Model Context Protocol.

## Tools Available

| Tool | Description |
|------|-------------|
| `list_vms` | List all VM instances in the project and zone |
| `start_vm` | Start a VM instance |
| `stop_vm` | Stop a VM instance |
| `restart_vm` | Restart (reset) a VM instance |
| `get_vm` | Get detailed information about a VM instance |
| `list_evidence` | List evidence files in the local evidence folder |
| `generate_report` | Generate a weekly governance report |

## Configuration

The server uses the same configuration as the forge-cloud-control-desk project:
- `GCP_PROJECT_ID`
- `GCP_ZONE`
- `GCP_SERVICE_ACCOUNT_JSON`
- `SHEETS_SPREADSHEET_ID`
- `DRIVE_EVIDENCE_FOLDER_ID`

## Running the Server

```bash
cd /home/stu/.openclaw/workspace/projects/forge-cloud-control-desk
export $(xargs < .env)
python3 -m src.mcp.server
```

The server will start and listen for MCP connections.

## Usage Example

```bash
# List all VMs
mcp call list_vms

# Start a VM
mcp call start_vm '{"instance_name": "forge-test-vm"}'

# Get VM details
mcp call get_vm '{"instance_name": "forge-test-vm"}'

# Generate report
mcp call generate_report
```

## Integration with OpenClaw

To integrate with OpenClaw, add the MCP server configuration to your OpenClaw config:

```json
{
  "mcp": {
    "servers": {
      "forge-ccd": {
        "command": "python3",
        "args": ["/home/stu/.openclaw/workspace/projects/forge-cloud-control-desk/src/mcp/server.py"],
        "env": {
          "GCP_PROJECT_ID": "orderededge-groupware",
          "GCP_ZONE": "europe-west2-b"
        }
      }
    }
  }
}
```
