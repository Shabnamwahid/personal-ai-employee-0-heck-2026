import os
import sys
import json
import base64
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class EmailMCPServer:
    """MCP Server for sending emails."""
    
    def __init__(self, port: int = 8809):
        self.port = port
        self.vault_root = Path(os.getenv('VAULT_ROOT', '.'))
        self.credentials_path = Path(__file__).parent / 'credentials.json'
        self.token_path = Path(__file__).parent / 'token.json'
        self.service = None
        self.shutdown = False
    
    def authenticate(self):
        """Authenticate with Gmail API."""
        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    print("Error: credentials.json not found")
                    return False
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=8080)
            
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("Gmail API authenticated")
        return True
    
    def send_email(self, to: str, subject: str, body: str, attachment_path: str = None) -> dict:
        """Send an email via Gmail API."""
        try:
            from email.message import EmailMessage
            import mimetypes
            
            message = EmailMessage()
            message['To'] = to
            message['From'] = 'me'
            message['Subject'] = subject
            message.set_content(body)
            
            if attachment_path:
                filepath = self.vault_root / attachment_path
                if filepath.exists():
                    mime_type, _ = mimetypes.guess_type(str(filepath))
                    mime_type = mime_type or 'application/octet-stream'
                    
                    with open(filepath, 'rb') as f:
                        file_data = f.read()
                    
                    message.add_attachment(
                        file_data,
                        maintype=mime_type.split('/')[0],
                        subtype=mime_type.split('/')[1],
                        filename=filepath.name
                    )
            
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': encoded_message}
            ).execute()
            
            self.log_sent_email(to, subject, sent_message['id'])
            
            return {
                'success': True,
                'message_id': sent_message['id'],
                'thread_id': sent_message.get('threadId')
            }
            
        except Exception as error:
            return {
                'success': False,
                'error': str(error)
            }
    
    def log_sent_email(self, to: str, subject: str, message_id: str):
        """Log sent email to vault."""
        logs_folder = self.vault_root / 'Logs'
        logs_folder.mkdir(exist_ok=True)
        
        log_file = logs_folder / f"email_log_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'to': to,
            'subject': subject,
            'message_id': message_id,
            'status': 'sent'
        }
        
        logs = []
        if log_file.exists():
            logs = json.loads(log_file.read_text())
        logs.append(log_entry)
        
        log_file.write_text(json.dumps(logs, indent=2))


class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for MCP requests."""
    
    server_instance: EmailMCPServer = None
    
    def do_POST(self):
        """Handle MCP tool calls."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            request = json.loads(post_data.decode())
            tool_name = request.get('tool')
            params = request.get('params', {})
            
            if tool_name == 'send_email':
                result = self.server_instance.send_email(
                    to=params.get('to'),
                    subject=params.get('subject'),
                    body=params.get('body'),
                    attachment_path=params.get('attachment')
                )
            elif tool_name == 'test_connection':
                result = {'success': self.server_instance.service is not None}
            elif tool_name == 'shutdown':
                print("Shutting down server...")
                result = {'success': True}
                self.server_instance.shutdown = True
            else:
                result = {'success': False, 'error': f'Unknown tool: {tool_name}'}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().isoformat()}] {args[0]}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Email MCP Server')
    parser.add_argument('--port', type=int, default=8809, help='Server port')
    parser.add_argument('--auth', action='store_true', help='Authenticate only')
    args = parser.parse_args()
    
    server = EmailMCPServer(args.port)
    
    if args.auth:
        if server.authenticate():
            print("Authentication successful!")
        return
    
    if not server.authenticate():
        print("Authentication failed")
        sys.exit(1)
    
    MCPRequestHandler.server_instance = server
    
    httpd = HTTPServer(('localhost', args.port), MCPRequestHandler)
    print(f"Email MCP Server running on http://localhost:{args.port}")
    
    while not server.shutdown:
        httpd.handle_request()
    
    httpd.server_close()
    print("Server stopped")


if __name__ == '__main__':
    main()
