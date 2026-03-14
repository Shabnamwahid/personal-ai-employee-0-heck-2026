module.exports = {
  apps: [
    {
      name: 'gmail-watcher',
      script: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/.qwen/skills/gmail-watcher/scripts/gmail_watcher.py',
      interpreter: 'C:/Users/abRahman/AppData/Local/Programs/Python/Python311/python.exe',
      interpreter_args: '--vault C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault',
      cron_restart: '*/5 * * * *',
      error_file: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault/Logs/pm2_gmail_error.log',
      out_file: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault/Logs/pm2_gmail_out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      env: {
        VAULT_ROOT: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault',
        POLL_INTERVAL: '60',
        MAX_RESULTS_PER_POLL: '10'
      }
    },
    {
      name: 'whatsapp-watcher',
      script: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/.qwen/skills/whatsapp-watcher/scripts/whatsapp_watcher.py',
      interpreter: 'C:/Users/abRahman/AppData/Local/Programs/Python/Python311/python.exe',
      interpreter_args: '--vault C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault',
      cron_restart: '*/10 * * * *',
      error_file: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault/Logs/pm2_whatsapp_error.log',
      out_file: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault/Logs/pm2_whatsapp_out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      env: {
        VAULT_ROOT: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault',
        POLL_INTERVAL: '120',
        SESSION_PATH: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/.qwen/skills/whatsapp-watcher/session'
      }
    },
    {
      name: 'orchestrator',
      script: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/.qwen/skills/orchestrator/scripts/orchestrator.py',
      interpreter: 'C:/Users/abRahman/AppData/Local/Programs/Python/Python311/python.exe',
      interpreter_args: '--vault C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault',
      cron_restart: '*/2 * * * *',
      error_file: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault/Logs/pm2_orchestrator_error.log',
      out_file: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault/Logs/pm2_orchestrator_out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      env: {
        VAULT_ROOT: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault',
        POLL_INTERVAL: '30',
        MAX_CLAUDE_ITERATIONS: '10'
      }
    },
    {
      name: 'email-mcp-server',
      script: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/.qwen/skills/email-mcp/scripts/email_mcp_server.py',
      interpreter: 'C:/Users/abRahman/AppData/Local/Programs/Python/Python311/python.exe',
      args: '--port 8809',
      instance_var: 'INSTANCE_NUM',
      error_file: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault/Logs/pm2_email_mcp_error.log',
      out_file: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault/Logs/pm2_email_mcp_out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      env: {
        VAULT_ROOT: 'C:/Users/abRahman/Desktop/personal-ai-employee-0-heck-2026/AI_Employee_Vault'
      }
    }
  ]
};
