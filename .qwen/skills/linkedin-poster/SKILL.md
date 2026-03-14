---
name: linkedin-poster
description: |
  Automatically post to LinkedIn for lead generation and business promotion.
  Uses Playwright to automate LinkedIn posting with content from Obsidian vault.
  Includes scheduling, hashtag management, and engagement tracking.
---

# LinkedIn Poster

Automate LinkedIn posts to promote your business and generate leads.

## Prerequisites

1. **Install Dependencies**:
   ```bash
   pip install playwright python-dotenv
   playwright install
   ```

2. **LinkedIn Account**: Business or personal profile

## Configuration

```env
VAULT_ROOT=C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault
CONTENT_FOLDER=Plans/LinkedIn_Content
POST_SCHEDULE=0 9 * * *
HASHTAGS=#AI #Automation #Business #Technology
```

## Usage

### Create Content

Create content files in `Plans/LinkedIn_Content/`:

```markdown
---
type: linkedin_post
scheduled: 2026-01-08T09:00:00Z
status: draft
---

## Post Content

Excited to announce our new AI automation service!

#AI #Automation #Business
```

### Post to LinkedIn

```bash
# Test post
python scripts/linkedin_poster.py --test --content Plans/LinkedIn_Content/post.md

# Actual post
python scripts/linkedin_poster.py --post --content Plans/LinkedIn_Content/post.md
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Login failed | Clear session and re-login |
| Post not appearing | Check content length (max 3000 chars) |

## Security Notes

- LinkedIn session contains auth tokens
- Never commit session files
- Rate limit: max 3 posts per day
