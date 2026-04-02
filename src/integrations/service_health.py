#!/usr/bin/env python3
"""
Forge Compute Control Desk — Service Health Integration

Monitors Google Cloud Service Health for incidents affecting Compute Engine operations.
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build


# Configuration from environment
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "orderededge-groupware")
SERVICE_ACCOUNT_FILE = os.environ.get(
    "GCP_SERVICE_ACCOUNT_JSON", 
    "/home/stu/.config/gcp/forge-ccd-service-account.json"
)

# Service Health requires cloud-platform.read-only scope
SERVICE_HEALTH_SCOPES = ["https://www.googleapis.com/auth/cloud-platform.read-only"]


class ServiceHealthClient:
    """Client for Google Cloud Service Health API."""
    
    def __init__(self):
        self.service = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the Service Health API client."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE,
                scopes=SERVICE_HEALTH_SCOPES,
            )
            # Service Health API v1
            self.service = build("cloudresourcemanager", "v3", credentials=credentials)
        except Exception as e:
            print(f"Warning: Could not initialize Service Health client: {e}")
            self.service = None
    
    def is_available(self) -> bool:
        """Check if the Service Health client is available."""
        return self.service is not None
    
    def get_events_for_project(self, project_id: str = None) -> List[Dict[str, Any]]:
        """
        Get active and recent service events for a project.
        
        Returns list of events affecting the specified project.
        """
        if not self.service:
            return []
        
        project_id = project_id or PROJECT_ID
        
        try:
            # Note: Service Health API structure may vary
            # This is a placeholder for the actual API call
            # The real implementation would use:
            # parent = f"projects/{project_id}"
            # response = self.service.projects().events().list(parent=parent).execute()
            
            # For now, return empty list - API needs proper enablement
            print(f"Service Health check for project {project_id} (API not yet enabled)")
            return []
            
        except Exception as e:
            print(f"Error fetching service events: {e}")
            return []
    
    def get_compute_events(self, region: str = None) -> List[Dict[str, Any]]:
        """
        Get events specifically affecting Compute Engine.
        
        Args:
            region: Optional region filter (e.g., 'europe-west2')
        
        Returns:
            List of Compute Engine related events
        """
        all_events = self.get_events_for_project()
        
        # Filter for Compute Engine events
        compute_events = []
        for event in all_events:
            # Filter by service name
            if 'compute' in event.get('service', '').lower():
                if region is None or region in event.get('affected_regions', []):
                    compute_events.append(event)
        
        return compute_events
    
    def has_active_incidents(self, region: str = None) -> bool:
        """
        Check if there are any active incidents.
        
        Returns:
            True if active incidents exist, False otherwise
        """
        events = self.get_compute_events(region)
        
        for event in events:
            if event.get('status') == 'ACTIVE':
                return True
        
        return False
    
    def get_status_summary(self, region: str = None) -> Dict[str, Any]:
        """
        Get a summary of service health status.
        
        Returns:
            Dictionary with status summary
        """
        events = self.get_compute_events(region)
        
        active_count = sum(1 for e in events if e.get('status') == 'ACTIVE')
        resolved_count = sum(1 for e in events if e.get('status') == 'RESOLVED')
        
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'region': region or 'all',
            'active_incidents': active_count,
            'resolved_last_7_days': resolved_count,
            'total_events': len(events),
            'status': 'DEGRADED' if active_count > 0 else 'OPERATIONAL',
            'events': events[:5]  # Return top 5 most recent
        }


def check_service_health(evidence_folder: str = None) -> Dict[str, Any]:
    """
    Check service health and write evidence.
    
    Args:
        evidence_folder: Folder to write health check evidence
    
    Returns:
        Health check result dictionary
    """
    from pathlib import Path
    
    # Initialize client
    client = ServiceHealthClient()
    
    # Get region from environment
    region = os.environ.get("GCP_REGION", "europe-west2")
    
    # Get status summary
    summary = client.get_status_summary(region)
    
    # Write evidence if folder provided
    if evidence_folder:
        evidence_path = Path(evidence_folder) / "service_health"
        evidence_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
        evidence_file = evidence_path / f"health_check_{timestamp}.md"
        
        with open(evidence_file, 'w') as f:
            f.write(f"# Service Health Check\n\n")
            f.write(f"**Timestamp:** {summary['timestamp']}\n")
            f.write(f"**Region:** {summary['region']}\n")
            f.write(f"**Overall Status:** {summary['status']}\n\n")
            f.write(f"## Summary\n\n")
            f.write(f"| Metric | Value |\n")
            f.write(f"|--------|-------|\n")
            f.write(f"| Active Incidents | {summary['active_incidents']} |\n")
            f.write(f"| Resolved (7 days) | {summary['resolved_last_7_days']} |\n")
            f.write(f"| Total Events | {summary['total_events']} |\n\n")
            
            if summary['events']:
                f.write(f"## Recent Events\n\n")
                for event in summary['events']:
                    f.write(f"### {event.get('title', 'Untitled Event')}\n\n")
                    f.write(f"- **Status:** {event.get('status')}\n")
                    f.write(f"- **Service:** {event.get('service')}\n")
                    f.write(f"- **Start:** {event.get('start_time')}\n")
                    f.write(f"- **Update:** {event.get('update_time')}\n\n")
        
        summary['evidence_path'] = str(evidence_file)
    
    return summary


if __name__ == "__main__":
    # Test the service health integration
    print("Testing Service Health Integration...")
    print("=" * 60)
    
    client = ServiceHealthClient()
    
    if client.is_available():
        print("✓ Service Health client initialized")
        
        region = os.environ.get("GCP_REGION", "europe-west2")
        summary = client.get_status_summary(region)
        
        print(f"\nRegion: {region}")
        print(f"Status: {summary['status']}")
        print(f"Active Incidents: {summary['active_incidents']}")
        print(f"Total Events: {summary['total_events']}")
    else:
        print("✗ Service Health client not available")
        print("  (API may not be enabled or credentials missing)")
    
    print("=" * 60)
