#!/usr/bin/env python3
"""Setup PM2 ecosystem config for AI Employee skills."""

import os
import sys
from pathlib import Path

SKILLS_BASE = Path(r"C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026\.qwen\skills")
VAULT_ROOT = Path(r"C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026\AI_Employee_Vault")

def create_pm2_config():
    """Create PM2 ecosystem.config.js file."""
    
    python_exe = sys.executable.replace('\\', '/')
    vault_path = str(VAULT_ROOT).replace('\\', '/')
    scripts_path = str(SKILLS_BASE).replace('\\', '/')
    
    config = f"""module.exports = {{
  apps: [
    {{
      name: 'gmail-watcher',
      script: '{scripts_path}/gmail-watcher/scripts/gmail_watcher.py',
      interpreter: '{python_exe}',
      interpreter_args: '--vault {vault_path}',
      cron_restart: '*/5 * * * *',
      error_file: '{vault_path}/Logs/pm2_gmail_error.log',
      out_file: '{vault_path}/Logs/pm2_gmail_out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      env: {{
        VAULT_ROOT: '{vault_path}',
        POLL_INTERVAL: '60',
        MAX_RESULTS_PER_POLL: '10'
      }}
    }},
    {{
      name: 'whatsapp-watcher',
      script: '{scripts_path}/whatsapp-watcher/scripts/whatsapp_watcher.py',
      interpreter: '{python_exe}',
      interpreter_args: '--vault {vault_path}',
      cron_restart: '*/10 * * * *',
      error_file: '{vault_path}/Logs/pm2_whatsapp_error.log',
      out_file: '{vault_path}/Logs/pm2_whatsapp_out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      env: {{
        VAULT_ROOT: '{vault_path}',
        POLL_INTERVAL: '120',
        SESSION_PATH: '{scripts_path}/whatsapp-watcher/session'
      }}
    }},
    {{
      name: 'orchestrator',
      script: '{scripts_path}/orchestrator/scripts/orchestrator.py',
      interpreter: '{python_exe}',
      interpreter_args: '--vault {vault_path}',
      cron_restart: '*/2 * * * *',
      error_file: '{vault_path}/Logs/pm2_orchestrator_error.log',
      out_file: '{vault_path}/Logs/pm2_orchestrator_out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      env: {{
        VAULT_ROOT: '{vault_path}',
        POLL_INTERVAL: '30',
        MAX_CLAUDE_ITERATIONS: '10'
      }}
    }},
    {{
      name: 'email-mcp-server',
      script: '{scripts_path}/email-mcp/scripts/email_mcp_server.py',
      interpreter: '{python_exe}',
      args: '--port 8809',
      instance_var: 'INSTANCE_NUM',
      error_file: '{vault_path}/Logs/pm2_email_mcp_error.log',
      out_file: '{vault_path}/Logs/pm2_email_mcp_out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      env: {{
        VAULT_ROOT: '{vault_path}'
      }}
    }}
  ]
}};
"""
    
    config_path = SKILLS_BASE / 'ecosystem.config.js'
    config_path.write_text(config, encoding='utf-8')
    print(f"PM2 ecosystem config created: {config_path}")
    return config_path


def create_env_template():
    """Create .env template file."""
    
    env_content = """# AI Employee Silver Tier Configuration
# Copy this file to .env and fill in your values

# Vault Configuration
VAULT_ROOT=C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault

# Gmail API Configuration (for gmail-watcher and email-mcp)
# Get credentials from: https://console.cloud.google.com/
GMAIL_CLIENT_ID=your_client_id_here
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_REDIRECT_URI=http://localhost:8080

# Watcher Settings
POLL_INTERVAL=60
MAX_RESULTS_PER_POLL=10
LABELS_TO_WATCH=INBOX,IMPORTANT,UNREAD

# WhatsApp Settings
SESSION_PATH=./whatsapp_session
KEYWORD_FILTERS=pricing,invoice,interested,buy,purchase

# Orchestrator Settings
MAX_CLAUDE_ITERATIONS=10

# Approval Settings
APPROVAL_TIMEOUT=86400
AUTO_APPROVE_THRESHOLD=50

# LinkedIn Settings
HASHTAGS=#AI #Automation #Business #Technology
"""
    
    env_path = SKILLS_BASE / '.env.template'
    env_path.write_text(env_content, encoding='utf-8')
    print(f".env template created: {env_path}")
    return env_path


def create_readme():
    """Create Silver Tier README."""
    
    readme = """# Silver Tier Skills - AI Employee

This directory contains all Silver tier skills for the Personal AI Employee hackathon project.

## Skills Overview

| Skill | Description | Status |
|-------|-------------|--------|
| **gmail-watcher** | Monitor Gmail for new emails | ✅ Ready |
| **whatsapp-watcher** | Monitor WhatsApp Web for messages | ✅ Ready |
| **linkedin-poster** | Auto-post to LinkedIn | ✅ Ready |
| **email-mcp** | Send emails via Gmail API | ✅ Ready |
| **orchestrator** | Master coordination process | ✅ Ready |
| **hitl-approval** | Human-in-the-Loop workflow | ✅ Ready |
| **task-scheduler** | Schedule recurring tasks | ✅ Ready |
| **browsing-with-playwright** | Browser automation (Bronze) | ✅ Ready |

## Quick Start

### 1. Install Dependencies

```bash
# Python dependencies
pip install google-auth google-auth-oauthlib google-api-python-client playwright python-dotenv

# Playwright browsers
playwright install

# PM2 for process management
npm install -g pm2
```

### 2. Set Up Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json` to:
   - `gmail-watcher/scripts/credentials.json`
   - `email-mcp/scripts/credentials.json`

### 3. Configure Environment

```bash
# Copy template
cp .env.template .env

# Edit .env with your credentials
# IMPORTANT: Never commit .env to version control
```

### 4. Authenticate Gmail

```bash
# Gmail Watcher
cd gmail-watcher/scripts
python gmail_watcher.py --auth

# Email MCP
cd email-mcp/scripts
python email_mcp_server.py --auth
```

### 5. Start Processes with PM2

```bash
# From skills directory
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs

# Save for startup
pm2 save
pm2 startup
```

## Folder Structure

```
skills/
├── gmail-watcher/
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── base_watcher.py
│   │   ├── gmail_watcher.py
│   │   └── credentials.json (you add this)
│   └── references/
├── whatsapp-watcher/
│   ├── SKILL.md
│   └── scripts/
│       └── whatsapp_watcher.py
├── linkedin-poster/
│   ├── SKILL.md
│   └── scripts/
│       └── linkedin_poster.py
├── email-mcp/
│   ├── SKILL.md
│   └── scripts/
│       └── email_mcp_server.py
├── orchestrator/
│   ├── SKILL.md
│   └── scripts/
│       └── orchestrator.py
├── hitl-approval/
│   ├── SKILL.md
│   └── scripts/
│       └── hitl_approval.py
├── task-scheduler/
│   ├── SKILL.md
│   └── scripts/
│       └── task_scheduler.py
├── browsing-with-playwright/ (Bronze tier)
├── ecosystem.config.js
└── .env.template
```

## PM2 Commands

```bash
# Start all processes
pm2 start ecosystem.config.js

# Start specific process
pm2 start gmail-watcher

# Stop all
pm2 stop all

# Restart all
pm2 restart all

# View status
pm2 status

# View logs
pm2 logs

# View logs for specific process
pm2 logs gmail-watcher

# Delete process
pm2 delete gmail-watcher

# Save process list for startup
pm2 save

# Setup startup
pm2 startup
```

## Testing Individual Skills

### Gmail Watcher

```bash
# Test mode (single poll)
python gmail-watcher/scripts/gmail_watcher.py --test --vault <path_to_vault>

# Run once
python gmail-watcher/scripts/gmail_watcher.py --vault <path_to_vault>
```

### WhatsApp Watcher

```bash
# Test mode (shows browser)
python whatsapp-watcher/scripts/whatsapp_watcher.py --test --vault <path_to_vault> --no-headless
```

### LinkedIn Poster

```bash
# Test login
python linkedin-poster/scripts/linkedin_poster.py --test-login --vault <path_to_vault>

# Test post (no actual posting)
python linkedin-poster/scripts/linkedin_poster.py --test --content Plans/LinkedIn_Content/test.md
```

### Orchestrator

```bash
# Run once
python orchestrator/scripts/orchestrator.py --vault <path_to_vault> --once

# Continuous mode
python orchestrator/scripts/orchestrator.py --vault <path_to_vault>
```

### HITL Approval

```bash
# List pending approvals
python hitl-approval/scripts/hitl_approval.py --list-pending --vault <path_to_vault>

# Approve file
python hitl-approval/scripts/hitl_approval.py --approve filename.md --vault <path_to_vault>
```

## Troubleshooting

### Gmail API Issues

**Problem**: `credentials.json not found`
- **Solution**: Download from Google Cloud Console and place in correct folder

**Problem**: `token.json expired`
- **Solution**: Delete token.json and re-run `--auth`

**Problem**: `Gmail API quota exceeded`
- **Solution**: Increase POLL_INTERVAL to 300+ seconds

### WhatsApp Issues

**Problem**: QR code appears every time
- **Solution**: Check SESSION_PATH permissions, ensure it's writable

**Problem**: No messages detected
- **Solution**: Check KEYWORD_FILTERS configuration

### PM2 Issues

**Problem**: Processes keep restarting
- **Solution**: Check error logs: `pm2 logs <process-name> --err`

**Problem**: Python not found
- **Solution**: Use absolute path to python in ecosystem.config.js

### Orchestrator Issues

**Problem**: Claude not responding
- **Solution**: Verify `claude --version` works in terminal

**Problem**: Files not moving to Done
- **Solution**: Check folder permissions in vault

## Security Notes

1. **Never commit** `.env`, `credentials.json`, or `token.json` to version control
2. Store secrets securely and rotate credentials monthly
3. Use app-specific passwords if 2FA enabled
4. Review approval requests before approving sensitive actions
5. Enable audit logging in Logs folder

## Silver Tier Checklist

- [ ] All dependencies installed
- [ ] Gmail API credentials configured
- [ ] All watchers authenticated
- [ ] PM2 processes running
- [ ] Test email sent successfully
- [ ] Test WhatsApp message detected
- [ ] Orchestrator processing files
- [ ] HITL approval workflow tested
- [ ] Logs being generated

## Next Steps (Gold Tier)

1. Integrate Odoo accounting system
2. Add Facebook/Instagram integration
3. Add Twitter (X) integration
4. Implement weekly CEO Briefing
5. Add Ralph Wiggum loop for autonomous completion
6. Deploy to cloud for 24/7 operation

## Support

- Hackathon Blueprint: `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`
- Wednesday Meetings: Zoom link in blueprint document
- YouTube: https://www.youtube.com/@panaversity
"""
    
    readme_path = SKILLS_BASE / 'SILVER_TIER_README.md'
    readme_path.write_text(readme, encoding='utf-8')
    print(f"Silver Tier README created: {readme_path}")
    return readme_path


def main():
    print("Setting up Silver Tier PM2 configuration...")
    print("=" * 50)
    
    create_pm2_config()
    create_env_template()
    create_readme()
    
    print("\n" + "=" * 50)
    print("Silver Tier setup complete!")
    print("\nNext steps:")
    print("1. Copy .env.template to .env and fill in your credentials")
    print("2. Download Gmail API credentials.json for gmail-watcher and email-mcp")
    print("3. Run: playwright install")
    print("4. Authenticate Gmail: python gmail-watcher/scripts/gmail_watcher.py --auth")
    print("5. Start PM2: pm2 start ecosystem.config.js")
    print("6. Save for startup: pm2 save && pm2 startup")
    print("\nFor detailed instructions, see: SILVER_TIER_README.md")


if __name__ == '__main__':
    main()
