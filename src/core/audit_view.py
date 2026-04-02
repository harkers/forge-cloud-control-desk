"""GCCD Enhanced Audit Views

Provides:
- Searchable operation log
- Cost analysis by VM
- Failed operation tracking
- SLA compliance metrics
- Operation history dashboard

Usage:
    from audit_view import AuditView
    
    audit = AuditView()
    audit.show_recent_operations(days=7)
    audit.show_cost_analysis()
    audit.show_failed_operations()
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class OperationRecord:
    """Represents a single GCCD operation."""
    operation_id: str
    timestamp: datetime
    operation_type: str  # create, delete, start, stop, etc.
    vm_name: str
    status: str  # success, failed, pending
    user: str
    reason: str
    duration_seconds: Optional[float]
    error_message: Optional[str]
    evidence_path: Optional[Path]


class AuditView:
    """Enhanced audit views for GCCD operations."""
    
    def __init__(self, evidence_dir: Path = None):
        if evidence_dir is None:
            evidence_dir = Path(__file__).parent.parent.parent / "data" / "evidence"
        self.evidence_dir = evidence_dir
        self.operations_cache: List[OperationRecord] = []
        
    def load_operations(self, days: int = 30) -> List[OperationRecord]:
        """Load all operations from evidence files."""
        operations = []
        cutoff = datetime.now() - timedelta(days=days)
        
        # Scan for operation evidence files
        categories = ["vm_operations", "inspections", "service_health"]
        
        for category in categories:
            cat_dir = self.evidence_dir / category
            if not cat_dir.exists():
                continue
                
            for filepath in cat_dir.glob("*.md"):
                try:
                    op = self._parse_evidence_file(filepath, category)
                    if op and op.timestamp > cutoff:
                        operations.append(op)
                except Exception:
                    continue
        
        # Sort by timestamp
        operations.sort(key=lambda x: x.timestamp, reverse=True)
        self.operations_cache = operations
        return operations
    
    def _parse_evidence_file(self, filepath: Path, category: str) -> Optional[OperationRecord]:
        """Parse an evidence markdown file into OperationRecord."""
        content = filepath.read_text()
        
        # Extract timestamp from filename or content
        timestamp = self._extract_timestamp(filepath.name)
        
        # Extract operation type from content
        op_type = self._extract_operation_type(content, filepath.name)
        
        # Extract VM name
        vm_name = self._extract_vm_name(content, filepath.name)
        
        # Extract status
        status = self._extract_status(content)
        
        # Extract user (from file metadata or content)
        user = "gccd-system"  # Default, could extract from git/user
        
        # Extract reason
        reason = self._extract_reason(content)
        
        # Generate operation ID
        op_id = f"{op_type}-{vm_name}-{timestamp.strftime('%Y%m%d%H%M%S')}"
        
        return OperationRecord(
            operation_id=op_id,
            timestamp=timestamp,
            operation_type=op_type,
            vm_name=vm_name,
            status=status,
            user=user,
            reason=reason,
            duration_seconds=None,
            error_message=None,
            evidence_path=filepath
        )
    
    def _extract_timestamp(self, filename: str) -> datetime:
        """Extract timestamp from filename."""
        # Pattern: name_YYYY-MM-DDTHH-MM-SS.md
        match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})', filename)
        if match:
            return datetime.strptime(match.group(1), "%Y-%m-%dT%H-%M-%S")
        return datetime.now()
    
    def _extract_operation_type(self, content: str, filename: str) -> str:
        """Extract operation type from content or filename."""
        # Check content first
        if "create" in content.lower():
            return "create"
        elif "delete" in content.lower():
            return "delete"
        elif "start" in content.lower():
            return "start"
        elif "stop" in content.lower():
            return "stop"
        elif "restart" in content.lower():
            return "restart"
        elif "inspect" in content.lower():
            return "inspect"
        elif "health" in content.lower():
            return "health_check"
        
        # Fallback to filename
        if "create" in filename.lower():
            return "create"
        elif "delete" in filename.lower():
            return "delete"
        elif "inspect" in filename.lower():
            return "inspect"
        
        return "unknown"
    
    def _extract_vm_name(self, content: str, filename: str) -> str:
        """Extract VM name from content or filename."""
        # Pattern in content: **Instance Name:** vm-name
        match = re.search(r'\*\*Instance Name:\*\*\s*(\S+)', content)
        if match:
            return match.group(1)
        
        # Pattern in filename: vmname_timestamp.md
        parts = filename.split('_')
        if len(parts) >= 2 and parts[0] not in ["notification", "health"]:
            return parts[0]
        
        return "unknown"
    
    def _extract_status(self, content: str) -> str:
        """Extract operation status from content."""
        if "✅" in content or "success" in content.lower():
            return "success"
        elif "❌" in content or "failed" in content.lower():
            return "failed"
        elif "error" in content.lower():
            return "failed"
        return "completed"  # Assume completed if no error marker
    
    def _extract_reason(self, content: str) -> str:
        """Extract reason from content."""
        # Pattern: **Reason:** reason text
        match = re.search(r'\*\*Reason:\*\*\s*(.+)', content)
        if match:
            return match.group(1).strip()
        return "Not specified"
    
    def show_recent_operations(self, days: int = 7, limit: int = 50) -> str:
        """Display recent operations as formatted text."""
        operations = self.load_operations(days=days)[:limit]
        
        lines = [
            f"Recent Operations (last {days} days)",
            "=" * 80,
            ""
        ]
        
        for op in operations:
            icon = "✅" if op.status == "success" else "❌" if op.status == "failed" else "⏳"
            lines.append(
                f"{icon} {op.timestamp.strftime('%Y-%m-%d %H:%M')} | "
                f"{op.operation_type:10} | {op.vm_name:20} | {op.status:10}"
            )
            if op.reason and op.reason != "Not specified":
                lines.append(f"   Reason: {op.reason}")
        
        lines.append("")
        lines.append(f"Total: {len(operations)} operations")
        
        return "\n".join(lines)
    
    def show_cost_analysis(self) -> str:
        """Display cost analysis by VM."""
        operations = self.load_operations(days=30)
        
        # Group by VM
        vm_stats = defaultdict(lambda: {
            "create_count": 0,
            "delete_count": 0,
            "start_count": 0,
            "stop_count": 0,
            "running_hours": 0,
            "last_seen": None
        })
        
        for op in operations:
            vm = vm_stats[op.vm_name]
            if op.operation_type == "create":
                vm["create_count"] += 1
            elif op.operation_type == "delete":
                vm["delete_count"] += 1
            elif op.operation_type == "start":
                vm["start_count"] += 1
            elif op.operation_type == "stop":
                vm["stop_count"] += 1
            
            if vm["last_seen"] is None or op.timestamp > vm["last_seen"]:
                vm["last_seen"] = op.timestamp
        
        lines = [
            "VM Cost Analysis (last 30 days)",
            "=" * 80,
            ""
        ]
        
        lines.append(f"{'VM Name':<25} {'Creates':<8} {'Starts':<8} {'Stops':<8} {'Status':<10}")
        lines.append("-" * 80)
        
        for vm_name, stats in sorted(vm_stats.items()):
            status = "Active" if stats["delete_count"] == 0 else "Deleted"
            lines.append(
                f"{vm_name:<25} {stats['create_count']:<8} {stats['start_count']:<8} "
                f"{stats['stop_count']:<8} {status:<10}"
            )
        
        return "\n".join(lines)
    
    def show_failed_operations(self, days: int = 7) -> str:
        """Display failed operations."""
        operations = self.load_operations(days=days)
        failed = [op for op in operations if op.status == "failed"]
        
        lines = [
            f"Failed Operations (last {days} days)",
            "=" * 80,
            ""
        ]
        
        if not failed:
            lines.append("No failed operations in the specified period ✅")
            return "\n".join(lines)
        
        for op in failed:
            lines.append(f"❌ {op.timestamp.strftime('%Y-%m-%d %H:%M')}")
            lines.append(f"   Operation: {op.operation_type}")
            lines.append(f"   VM: {op.vm_name}")
            lines.append(f"   Evidence: {op.evidence_path}")
            if op.error_message:
                lines.append(f"   Error: {op.error_message}")
            lines.append("")
        
        lines.append(f"Total failures: {len(failed)}")
        
        return "\n".join(lines)
    
    def get_sla_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Calculate SLA compliance metrics."""
        operations = self.load_operations(days=days)
        
        if not operations:
            return {"error": "No operations found"}
        
        total = len(operations)
        successful = len([op for op in operations if op.status == "success"])
        failed = len([op for op in operations if op.status == "failed"])
        
        # Success rate
        success_rate = (successful / total * 100) if total > 0 else 0
        
        # Operations by type
        by_type = defaultdict(int)
        for op in operations:
            by_type[op.operation_type] += 1
        
        return {
            "period_days": days,
            "total_operations": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round(success_rate, 2),
            "operations_by_type": dict(by_type)
        }
    
    def search_operations(self, query: str, days: int = 30) -> List[OperationRecord]:
        """Search operations by VM name, type, or reason."""
        operations = self.load_operations(days=days)
        query = query.lower()
        
        results = [
            op for op in operations
            if query in op.vm_name.lower()
            or query in op.operation_type.lower()
            or query in op.reason.lower()
        ]
        
        return results


# CLI interface
def main():
    """CLI for audit views."""
    import sys
    
    audit = AuditView()
    
    if len(sys.argv) < 2:
        print("Usage: python3 -m src.core.audit_view <command> [args]")
        print("")
        print("Commands:")
        print("  recent [days]     - Show recent operations")
        print("  costs             - Show cost analysis")
        print("  failed [days]     - Show failed operations")
        print("  sla [days]        - Show SLA metrics")
        print("  search <query>    - Search operations")
        return
    
    command = sys.argv[1]
    
    if command == "recent":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        print(audit.show_recent_operations(days=days))
    
    elif command == "costs":
        print(audit.show_cost_analysis())
    
    elif command == "failed":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        print(audit.show_failed_operations(days=days))
    
    elif command == "sla":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        import json
        print(json.dumps(audit.get_sla_metrics(days=days), indent=2))
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: audit_view search <query>")
            return
        query = sys.argv[2]
        results = audit.search_operations(query)
        print(f"Found {len(results)} results for '{query}':")
        for op in results:
            print(f"  {op.timestamp.strftime('%Y-%m-%d')} | {op.operation_type} | {op.vm_name}")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
