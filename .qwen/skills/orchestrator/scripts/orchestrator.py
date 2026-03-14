import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List
import shutil

class Orchestrator:
    """Main orchestration process for AI Employee."""
    
    def __init__(self, vault_root: str):
        self.vault_root = Path(vault_root)
        self.poll_interval = int(os.getenv('POLL_INTERVAL', '30'))
        
        self.needs_action = self.vault_root / 'Needs_Action'
        self.in_progress = self.vault_root / 'In_Progress' / 'orchestrator'
        self.pending_approval = self.vault_root / 'Pending_Approval'
        self.approved = self.vault_root / 'Approved'
        self.done = self.vault_root / 'Done'
        self.logs = self.vault_root / 'Logs'
        
        for folder in [self.needs_action, self.in_progress, self.pending_approval, 
                       self.approved, self.done, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.vault_root / '.orchestrator_state.json'
        self.running = True
    
    def log(self, message: str):
        """Log message to console and file."""
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        
        log_file = self.logs / f"orchestrator_{datetime.now().strftime('%Y-%m-%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    def get_new_files(self) -> List[Path]:
        """Get new files in Needs_Action folder."""
        cutoff = time.time() - (self.poll_interval * 2)
        return [f for f in self.needs_action.glob('*.md') if f.stat().st_mtime > cutoff]
    
    def claim_file(self, filepath: Path) -> Path:
        """Move file to In_Progress."""
        dest = self.in_progress / filepath.name
        shutil.move(str(filepath), str(dest))
        self.log(f"Claimed: {filepath.name}")
        return dest
    
    def release_file(self, filepath: Path, status: str = 'done'):
        """Move file to final destination."""
        if status == 'pending_approval':
            dest = self.pending_approval / filepath.name
        else:
            dest = self.done / filepath.name
        shutil.move(str(filepath), str(dest))
        self.log(f"Released to {dest.name}: {filepath.name}")
    
    def trigger_claude(self, filepath: Path) -> bool:
        """Trigger Claude Code to process file."""
        try:
            content = filepath.read_text(encoding='utf-8')
            
            prompt = f"""Process this action file:

{content}

Instructions:
1. Analyze the request
2. Determine required actions
3. If multi-step, create Plan.md
4. If approval needed, create file in Pending_Approval/
5. Execute via MCP servers if approved
"""
            
            result = subprocess.run(
                ['claude', '--prompt', prompt],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            response = f"\n\n## AI Processing ({datetime.now().isoformat()})\n\n{result.stdout}"
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(response)
            
            return True
            
        except subprocess.TimeoutExpired:
            self.log(f"Claude timeout for {filepath.name}")
            return False
        except Exception as e:
            self.log(f"Error triggering Claude: {e}")
            return False
    
    def process_approvals(self):
        """Process approved actions."""
        for filepath in self.approved.glob('*.md'):
            self.log(f"Processing approved: {filepath.name}")
            self.release_file(filepath, 'done')
    
    def run_cycle(self):
        """Run one orchestration cycle."""
        new_files = self.get_new_files()
        
        for filepath in new_files:
            try:
                claimed = self.claim_file(filepath)
                success = self.trigger_claude(claimed)
                
                if success:
                    approval_files = list(self.pending_approval.glob('*'))
                    if approval_files:
                        self.release_file(claimed, 'pending_approval')
                    else:
                        self.release_file(claimed, 'done')
                else:
                    self.release_file(claimed, 'done')
                    
            except Exception as e:
                self.log(f"Error processing {filepath.name}: {e}")
        
        self.process_approvals()
    
    def run(self):
        """Main orchestration loop."""
        self.log("Orchestrator started")
        
        while self.running:
            try:
                self.run_cycle()
            except Exception as e:
                self.log(f"Cycle error: {e}")
            
            time.sleep(self.poll_interval)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AI Employee Orchestrator')
    parser.add_argument('--vault', type=str, help='Vault root path')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    args = parser.parse_args()
    
    vault_root = args.vault or os.getenv('VAULT_ROOT')
    if not vault_root:
        vault_root = input("Enter vault root path: ")
    
    orchestrator = Orchestrator(vault_root)
    
    if args.once:
        orchestrator.run_cycle()
    else:
        try:
            orchestrator.run()
        except KeyboardInterrupt:
            orchestrator.running = False
            print("\nOrchestrator stopped")


if __name__ == '__main__':
    main()
