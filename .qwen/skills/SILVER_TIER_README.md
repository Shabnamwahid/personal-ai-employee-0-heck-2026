# Silver Tier Skills - AI Employee

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
