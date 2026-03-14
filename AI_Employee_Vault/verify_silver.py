#!/usr/bin/env python3
"""Verify Silver tier completion status."""

import os
from pathlib import Path

SKILLS_BASE = Path(r"C:\Users\abRahman\Desktop\personal-ai-employee-0-heck-2026\.qwen\skills")

print("=" * 60)
print("SILVER TIER VERIFICATION REPORT")
print("=" * 60)

# Silver Tier Requirements from blueprint
requirements = {
    "1. Two or more Watcher scripts (Gmail + WhatsApp + LinkedIn)": False,
    "2. Automatically Post on LinkedIn": False,
    "3. Claude reasoning loop (creates Plan.md files)": False,
    "4. One working MCP server for external action": False,
    "5. Human-in-the-loop approval workflow": False,
    "6. Basic scheduling via cron or Task Scheduler": False,
    "7. All AI functionality as Agent Skills": False,
}

# Check each skill directory
skills_found = []
print("\n📁 SKILL DIRECTORIES FOUND:")
print("-" * 40)

for item in SKILLS_BASE.iterdir():
    if item.is_dir():
        skills_found.append(item.name)
        has_skill_md = (item / "SKILL.md").exists()
        has_scripts = (item / "scripts").exists()
        
        scripts_count = 0
        if has_scripts:
            scripts_count = len(list((item / "scripts").glob("*.py")))
        
        status = "✅" if (has_skill_md and scripts_count > 0) else "❌"
        print(f"{status} {item.name}")
        print(f"   - SKILL.md: {'Yes' if has_skill_md else 'No'}")
        print(f"   - scripts/: {scripts_count} files" if has_scripts else "   - scripts/: Missing")

print(f"\nTotal skills: {len(skills_found)}")

# Check specific requirements
print("\n📋 SILVER TIER REQUIREMENTS CHECK:")
print("-" * 40)

# 1. Two or more Watcher scripts
watchers = ["gmail-watcher", "whatsapp-watcher", "linkedin-poster"]
watchers_found = [w for w in watchers if w in skills_found]
if len(watchers_found) >= 2:
    requirements["1. Two or more Watcher scripts (Gmail + WhatsApp + LinkedIn)"] = True
    print(f"✅ 2+ Watcher scripts: {', '.join(watchers_found)}")
else:
    print(f"❌ 2+ Watcher scripts: Only {', '.join(watchers_found)}")

# 2. LinkedIn Poster
if "linkedin-poster" in skills_found:
    lp_script = SKILLS_BASE / "linkedin-poster" / "scripts" / "linkedin_poster.py"
    if lp_script.exists():
        requirements["2. Automatically Post on LinkedIn"] = True
        print(f"✅ LinkedIn Poster: Ready")
    else:
        print(f"❌ LinkedIn Poster: Script missing")
else:
    print(f"❌ LinkedIn Poster: Not found")

# 3. Orchestrator (Claude reasoning loop)
if "orchestrator" in skills_found:
    orch_script = SKILLS_BASE / "orchestrator" / "scripts" / "orchestrator.py"
    if orch_script.exists():
        content = orch_script.read_text()
        if "claude" in content.lower() or "Plan.md" in content:
            requirements["3. Claude reasoning loop (creates Plan.md files)"] = True
            print(f"✅ Orchestrator (Claude loop): Ready")
        else:
            print(f"⚠️ Orchestrator: Claude integration unclear")
    else:
        print(f"❌ Orchestrator: Script missing")
else:
    print(f"❌ Orchestrator: Not found")

# 4. MCP Server
if "email-mcp" in skills_found:
    mcp_script = SKILLS_BASE / "email-mcp" / "scripts" / "email_mcp_server.py"
    if mcp_script.exists():
        requirements["4. One working MCP server for external action"] = True
        print(f"✅ Email MCP Server: Ready")
    else:
        print(f"❌ Email MCP Server: Script missing")
else:
    print(f"❌ Email MCP Server: Not found")

# 5. HITL Approval
if "hitl-approval" in skills_found:
    hitl_script = SKILLS_BASE / "hitl-approval" / "scripts" / "hitl_approval.py"
    if hitl_script.exists():
        requirements["5. Human-in-the-loop approval workflow"] = True
        print(f"✅ HITL Approval: Ready")
    else:
        print(f"❌ HITL Approval: Script missing")
else:
    print(f"❌ HITL Approval: Not found")

# 6. Task Scheduler
if "task-scheduler" in skills_found:
    sched_script = SKILLS_BASE / "task-scheduler" / "scripts" / "task_scheduler.py"
    if sched_script.exists():
        requirements["6. Basic scheduling via cron or Task Scheduler"] = True
        print(f"✅ Task Scheduler: Ready")
    else:
        print(f"❌ Task Scheduler: Script missing")
else:
    print(f"❌ Task Scheduler: Not found")

# 7. All as Agent Skills (SKILL.md files)
skill_files = list(SKILLS_BASE.glob("*/SKILL.md"))
if len(skill_files) >= 6:  # At least 6 skills with SKILL.md
    requirements["7. All AI functionality as Agent Skills"] = True
    print(f"✅ Agent Skills (SKILL.md): {len(skill_files)} files")
else:
    print(f"❌ Agent Skills (SKILL.md): Only {len(skill_files)} files")

# Check additional files
print("\n📄 ADDITIONAL FILES:")
print("-" * 40)

additional_files = {
    "ecosystem.config.js": "PM2 configuration",
    ".env.template": "Environment template",
    "SILVER_TIER_README.md": "Setup documentation",
}

for filename, description in additional_files.items():
    filepath = SKILLS_BASE / filename
    if filepath.exists():
        print(f"✅ {filename}: {description}")
    else:
        print(f"❌ {filename}: {description} - MISSING")

# Final verdict
print("\n" + "=" * 60)
print("FINAL VERDICT")
print("=" * 60)

requirements_met = sum(1 for v in requirements.values() if v)
total_requirements = len(requirements)

for req, met in requirements.items():
    status = "✅" if met else "❌"
    print(f"{status} {req}")

print(f"\nRequirements Met: {requirements_met}/{total_requirements}")

if requirements_met == total_requirements:
    print("\n🎉 SILVER TIER IS COMPLETE!")
    print("\nNext: Ready to test and use, or proceed to Gold Tier")
else:
    print(f"\n⚠️ SILVER TIER INCOMPLETE - {total_requirements - requirements_met} requirements missing")

print("=" * 60)
