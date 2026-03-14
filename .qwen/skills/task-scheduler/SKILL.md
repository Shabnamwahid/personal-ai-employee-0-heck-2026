---
name: task-scheduler
description: |
  Schedule recurring tasks using cron (Linux/Mac) or Task Scheduler (Windows).
  Triggers orchestrator and watchers at specified intervals.
---

# Task Scheduler

Automate task scheduling for AI Employee processes.

## Platform Support

- **Windows**: Task Scheduler via schtasks
- **Linux/Mac**: cron jobs
- **Cross-platform**: PM2 process manager

## Usage

### Windows (Task Scheduler)

```bash
python scripts/task_scheduler.py --install
```

### PM2 (Recommended)

```bash
# Create PM2 config
python scripts/task_scheduler.py --pm2

# Start all processes
pm2 start ecosystem.config.js

# Save for startup
pm2 save
pm2 startup
```

## Default Schedule

| Task | Frequency |
|------|-----------|
| Gmail Watcher | Every 5 min |
| WhatsApp Watcher | Every 10 min |
| Orchestrator | Every 2 min |
| LinkedIn Poster | Daily 9 AM |
