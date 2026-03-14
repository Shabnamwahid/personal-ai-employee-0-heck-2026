import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

class HITLApproval:
    """Human-in-the-Loop approval manager."""
    
    def __init__(self, vault_root: str):
        self.vault_root = Path(vault_root)
        self.pending = self.vault_root / 'Pending_Approval'
        self.approved = self.vault_root / 'Approved'
        self.rejected = self.vault_root / 'Rejected'
        self.timeout = int(os.getenv('APPROVAL_TIMEOUT', '86400'))
    
    def create_approval_request(self, request_data: dict) -> Path:
        """Create approval request file."""
        filename = f"{request_data['action']}_{request_data.get('recipient', 'unknown')}_{datetime.now().strftime('%Y-%m-%d')}.md"
        filepath = self.pending / filename
        
        expires = datetime.now() + timedelta(seconds=self.timeout)
        
        content = f'''---
type: approval_request
action: {request_data['action']}
amount: {request_data.get('amount', 'N/A')}
recipient: {request_data.get('recipient', 'N/A')}
reason: {request_data.get('reason', 'N/A')}
created: {datetime.now().isoformat()}
expires: {expires.isoformat()}
status: pending
---

## Action Details

**Action:** {request_data['action']}
**Amount:** {request_data.get('amount', 'N/A')}
**To/Recipient:** {request_data.get('recipient', 'N/A')}
**Reason:** {request_data.get('reason', 'N/A')}

## Details

{request_data.get('details', 'No additional details')}

## To Approve
Move this file to Approved/ folder.

## To Reject
Move this file to Rejected/ folder.
'''
        
        filepath.write_text(content, encoding='utf-8')
        return filepath
    
    def list_pending(self) -> list:
        """List all pending approvals."""
        pending = []
        for f in self.pending.glob('*.md'):
            content = f.read_text(encoding='utf-8')
            if 'status: pending' in content:
                pending.append({'file': f.name, 'path': str(f)})
        return pending
    
    def approve(self, filename: str) -> bool:
        """Move file to Approved."""
        src = self.pending / filename
        if src.exists():
            dest = self.approved / filename
            src.rename(dest)
            return True
        return False
    
    def reject(self, filename: str, reason: str = '') -> bool:
        """Move file to Rejected."""
        src = self.pending / filename
        if src.exists():
            dest = self.rejected / filename
            content = src.read_text(encoding='utf-8')
            content += f"\n\n## Rejected\n\nReason: {reason}\nDate: {datetime.now().isoformat()}"
            dest.write_text(content, encoding='utf-8')
            src.unlink()
            return True
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='HITL Approval Manager')
    parser.add_argument('--list-pending', action='store_true', help='List pending approvals')
    parser.add_argument('--approve', type=str, help='Approve file')
    parser.add_argument('--reject', type=str, help='Reject file')
    parser.add_argument('--reason', type=str, help='Rejection reason')
    parser.add_argument('--vault', type=str, help='Vault root path')
    args = parser.parse_args()
    
    vault_root = args.vault or os.getenv('VAULT_ROOT')
    if not vault_root:
        vault_root = input("Enter vault root path: ")
    
    manager = HITLApproval(vault_root)
    
    if args.list_pending:
        pending = manager.list_pending()
        print(f"Pending approvals: {len(pending)}")
        for p in pending:
            print(f"  - {p['file']}")
    
    elif args.approve:
        if manager.approve(args.approve):
            print(f"Approved: {args.approve}")
        else:
            print(f"File not found: {args.approve}")
    
    elif args.reject:
        if manager.reject(args.reject, args.reason or 'No reason provided'):
            print(f"Rejected: {args.reject}")
        else:
            print(f"File not found: {args.reject}")


if __name__ == '__main__':
    main()
