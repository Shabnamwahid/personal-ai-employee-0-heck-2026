import os
import sys
from pathlib import Path

class TaskScheduler:
    """Cross-platform task scheduler."""
    
    def __init__(self, vault_root: str, scripts_path: str):
        self.vault_root = Path(vault_root)
        self.scripts_path = Path(scripts_path)
        self.python = sys.executable
    
    def create_pm2_config(self):
        """Create PM2 ecosystem config."""
        config = f'''module.exports = {{
  apps: [
    {{
      name: 'gmail-watcher',
      script: '{self.scripts_path}/gmail_watcher.py',
      interpreter: '{self.python}',
      interpreter_args: '--vault {self.vault_root}',
      cron_restart: '*/5 * * * *'
    }},
    {{
      name: 'whatsapp-watcher',
      script: '{self.scripts_path}/whatsapp_watcher.py',
      interpreter: '{self.python}',
      interpreter_args: '--vault {self.vault_root}',
      cron_restart: '*/10 * * * *'
    }},
    {{
      name: 'orchestrator',
      script: '{self.scripts_path}/orchestrator.py',
      interpreter: '{self.python}',
      interpreter_args: '--vault {self.vault_root}',
      cron_restart: '*/2 * * * *'
    }}
  ]
}};
'''
        config_path = self.scripts_path / 'ecosystem.config.js'
        config_path.write_text(config, encoding='utf-8')
        print(f"PM2 config created: {config_path}")
        print("\nRun: pm2 start ecosystem.config.js")
        print("Then: pm2 save && pm2 startup")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Task Scheduler')
    parser.add_argument('--pm2', action='store_true', help='Create PM2 config')
    parser.add_argument('--install', action='store_true', help='Install scheduled tasks')
    parser.add_argument('--vault', type=str, help='Vault root path')
    parser.add_argument('--scripts', type=str, help='Scripts path')
    args = parser.parse_args()
    
    vault_root = args.vault or os.getenv('VAULT_ROOT')
    scripts_path = args.scripts or os.getenv('SCRIPTS_PATH')
    
    if not vault_root or not scripts_path:
        print("Error: --vault and --scripts required")
        sys.exit(1)
    
    scheduler = TaskScheduler(vault_root, scripts_path)
    
    if args.pm2:
        scheduler.create_pm2_config()
    elif args.install:
        print("Use PM2 for cross-platform process management:")
        print("  npm install -g pm2")
        print("  python task_scheduler.py --pm2")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
