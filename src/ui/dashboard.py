#!/usr/bin/env python3
"""
Forge Compute Control Desk — Phase 5: Dashboard UI

Simple internal dashboard for VM management with:
- Instance list view
- Quick actions (start, stop, restart, inspect)
- Evidence browser
- Settings panel
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime
import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    GCP_PROJECT_ID,
    GCP_ZONE,
    GCP_SERVICE_ACCOUNT_JSON,
    SHEETS_SPREADSHEET_ID,
    DRIVE_EVIDENCE_FOLDER_ID,
    LOG_LEVEL,
)

from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Cache instances for 30 seconds
instances_cache = {"time": 0, "data": []}
CACHE_TTL = 30


def get_compute_service():
    """Get Compute Engine API client."""
    credentials = service_account.Credentials.from_service_account_file(
        GCP_SERVICE_ACCOUNT_JSON,
        scopes=['https://www.googleapis.com/auth/compute']
    )
    return build('compute', 'v1', credentials=credentials)


def list_instances():
    """List all VM instances with caching."""
    import time
    current_time = time.time()
    
    if current_time - instances_cache['time'] < CACHE_TTL and instances_cache['data']:
        return instances_cache['data']
    
    compute = get_compute_service()
    result = compute.instances().list(
        project=GCP_PROJECT_ID,
        zone=GCP_ZONE,
    ).execute()
    
    instances = result.get('items', [])
    instances_cache['time'] = current_time
    instances_cache['data'] = instances
    
    return instances


@app.route('/')
def index():
    """Main dashboard page."""
    instances = list_instances()
    return render_template('index.html', 
                         project_id=GCP_PROJECT_ID,
                         zone=GCP_ZONE,
                         instances=instances)


@app.route('/api/instances')
def api_instances():
    """API endpoint for instance list."""
    instances = list_instances()
    return jsonify({
        'success': True,
        'count': len(instances),
        'instances': [
            {
                'name': inst.get('name'),
                'status': inst.get('status'),
                'machine_type': inst.get('machineType', '').split('/')[-1],
                'zone': inst.get('zone', '').split('/')[-1],
                'id': inst.get('id')
            }
            for inst in instances
        ]
    })


@app.route('/api/instances/<instance_name>/start', methods=['POST'])
def api_start_instance(instance_name):
    """Start a VM instance."""
    try:
        compute = get_compute_service()
        operation = compute.instances().start(
            project=GCP_PROJECT_ID,
            zone=GCP_ZONE,
            instance=instance_name,
        ).execute()
        
        return jsonify({
            'success': True,
            'operation_id': operation.get('name'),
            'message': f'Start operation initiated for {instance_name}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/instances/<instance_name>/stop', methods=['POST'])
def api_stop_instance(instance_name):
    """Stop a VM instance."""
    try:
        compute = get_compute_service()
        operation = compute.instances().stop(
            project=GCP_PROJECT_ID,
            zone=GCP_ZONE,
            instance=instance_name,
        ).execute()
        
        return jsonify({
            'success': True,
            'operation_id': operation.get('name'),
            'message': f'Stop operation initiated for {instance_name}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/instances/<instance_name>/restart', methods=['POST'])
def api_restart_instance(instance_name):
    """Restart a VM instance."""
    try:
        compute = get_compute_service()
        operation = compute.instances().reset(
            project=GCP_PROJECT_ID,
            zone=GCP_ZONE,
            instance=instance_name,
        ).execute()
        
        return jsonify({
            'success': True,
            'operation_id': operation.get('name'),
            'message': f'Restart operation initiated for {instance_name}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/instances/<instance_name>/inspect', methods=['GET'])
def api_inspect_instance(instance_name):
    """Get VM instance details."""
    try:
        compute = get_compute_service()
        instance = compute.instances().get(
            project=GCP_PROJECT_ID,
            zone=GCP_ZONE,
            instance=instance_name,
        ).execute()
        
        return jsonify({
            'success': True,
            'instance': instance
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/evidence')
def api_evidence():
    """List evidence files."""
    evidence_folder = DRIVE_EVIDENCE_FOLDER_ID or '/tmp/forge-ccd-evidence'
    
    evidence_files = []
    for root, dirs, files in os.walk(evidence_folder):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                stat = os.stat(filepath)
                evidence_files.append({
                    'name': file,
                    'path': filepath,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    
    return jsonify({
        'success': True,
        'count': len(evidence_files),
        'evidence_files': evidence_files
    })


@app.route('/api/settings')
def api_settings():
    """Get current settings."""
    return jsonify({
        'success': True,
        'settings': {
            'project_id': GCP_PROJECT_ID,
            'zone': GCP_ZONE,
            'sheets_spreadsheet_id': SHEETS_SPREADSHEET_ID,
            'evidence_folder': DRIVE_EVIDENCE_FOLDER_ID,
            'log_level': LOG_LEVEL
        }
    })


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
