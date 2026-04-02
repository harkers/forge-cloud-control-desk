"""
GCCD Status Dashboard - Flask Web Application

Provides real-time visibility into:
- Service Health status
- VM inventory and state
- Recent operations
- Quick actions

Run: python3 -m src.dashboard.app
Access: http://localhost:5001
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, jsonify
from integrations.service_health import check_service_health, ServiceHealthClient
from integrations.compute_vm import ComputeVMClient

# Configuration
DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', 5001))
EVIDENCE_DIR = Path(__file__).parent.parent.parent / 'data' / 'evidence'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('DASHBOARD_SECRET_KEY', 'gccd-dev-key-change-in-prod')


def get_vm_summary():
    """Get VM inventory summary."""
    try:
        client = ComputeVMClient()
        vms = client.list_vms()
        
        running = sum(1 for vm in vms if vm.get('status') == 'RUNNING')
        stopped = sum(1 for vm in vms if vm.get('status') == 'TERMINATED')
        
        return {
            'total': len(vms),
            'running': running,
            'stopped': stopped,
            'vms': vms[:10],  # Limit to 10 for dashboard
            'status': 'ok'
        }
    except Exception as e:
        return {
            'total': 0,
            'running': 0,
            'stopped': 0,
            'vms': [],
            'status': 'error',
            'error': str(e)
        }


def get_recent_evidence(limit=5):
    """Get recent evidence files."""
    try:
        evidence_files = []
        
        # Scan evidence directories
        for category in ['vm_operations', 'service_health', 'reports']:
            cat_dir = EVIDENCE_DIR / category
            if not cat_dir.exists():
                continue
            
            files = sorted(cat_dir.glob('*.md'), reverse=True)[:limit]
            for f in files:
                evidence_files.append({
                    'name': f.name,
                    'path': str(f.relative_to(EVIDENCE_DIR)),
                    'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    'category': category
                })
        
        # Sort by modification time
        evidence_files.sort(key=lambda x: x['modified'], reverse=True)
        return evidence_files[:limit]
        
    except Exception as e:
        return []


def get_health_status():
    """Get current service health status."""
    try:
        result = check_service_health()
        return {
            'status': result.get('status', 'UNKNOWN'),
            'active_incidents': result.get('active_incidents', 0),
            'region': result.get('region', 'europe-west2'),
            'last_check': datetime.now().isoformat(),
            'status_code': 'operational' if result.get('active_incidents', 0) == 0 else 'degraded'
        }
    except Exception as e:
        return {
            'status': 'UNKNOWN',
            'active_incidents': 0,
            'region': 'europe-west2',
            'last_check': datetime.now().isoformat(),
            'status_code': 'unknown',
            'error': str(e)
        }


@app.route('/')
def dashboard():
    """Main dashboard view."""
    health = get_health_status()
    vms = get_vm_summary()
    recent = get_recent_evidence()
    
    return render_template('dashboard.html', 
                         health=health, 
                         vms=vms, 
                         recent=recent,
                         now=datetime.now())


@app.route('/api/health')
def api_health():
    """API endpoint for health status."""
    return jsonify(get_health_status())


@app.route('/api/vms')
def api_vms():
    """API endpoint for VM inventory."""
    return jsonify(get_vm_summary())


@app.route('/api/evidence')
def api_evidence():
    """API endpoint for recent evidence."""
    limit = int(request.args.get('limit', 5))
    return jsonify(get_recent_evidence(limit))


@app.route('/health-check')
def health_check_page():
    """Dedicated health check page."""
    health = get_health_status()
    return render_template('health.html', health=health, now=datetime.now())


if __name__ == '__main__':
    print(f"🚀 GCCD Status Dashboard")
    print(f"   Starting on port {DASHBOARD_PORT}...")
    print(f"   Access: http://localhost:{DASHBOARD_PORT}")
    print(f"   API: http://localhost:{DASHBOARD_PORT}/api/health")
    print("")
    
    app.run(host='0.0.0.0', port=DASHBOARD_PORT, debug=True)
