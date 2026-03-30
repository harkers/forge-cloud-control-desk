# Forge Cloud Control Desk

A lightweight internal operations platform that uses Compute Engine API as the execution layer and Google Workspace/Enterprise APIs as the workflow, evidence, and reporting layer.

## Overview
Forge Cloud Control Desk provides a unified interface for managing Google Cloud VM resources and integrating with Google Workspace APIs for email, Drive, Sheets, and Service Health.
## Architecture

### Layers
- **Execution Layer**: Compute Engine REST API (compute.googleapis.com)
- **Workflow Layer**: Google Workspace APIs (Gmail, Drive, Sheets)
- **Reporting Layer**: Google Service Health API

### API Endpoints
- Compute Engine: compute.googleapis.com
- Gmail API: gmail.googleapis.com
- Drive API: drive.googleapis.com
- Sheets API: sheets.googleapis.com
- Service Health API: servicehealth.googleapis.com
## GitHub Repository
https://github.com/harkers/forge-cloud-control-desk

## License
Apache 2.0
