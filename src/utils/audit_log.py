import os
import datetime
import json
from cryptography.fernet import Fernet
from pathlib import Path

class AuditLogger:
    def __init__(self, log_file="audit.log", key_file="audit.key"):
        self.app_data_dir = Path(os.getenv('APPDATA') or Path.home()) / "PDFToolsDesktop"
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_path = self.app_data_dir / log_file
        self.key_path = self.app_data_dir / key_file
        
        self._load_or_generate_key()
        self.cipher = Fernet(self.key)

    def _load_or_generate_key(self):
        if self.key_path.exists():
            with open(self.key_path, "rb") as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(self.key_path, "wb") as f:
                f.write(self.key)

    def log_event(self, action, details):
        """
        Logs an event to the encrypted audit log.
        """
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        
        json_data = json.dumps(entry)
        encrypted_data = self.cipher.encrypt(json_data.encode())
        
        with open(self.log_path, "ab") as f:
            f.write(encrypted_data + b"\n")

    def read_logs(self):
        """
        Reads and decrypts all logs.
        """
        logs = []
        if not self.log_path.exists():
            return logs
            
        with open(self.log_path, "rb") as f:
            for line in f:
                try:
                    decrypted_data = self.cipher.decrypt(line.strip())
                    logs.append(json.loads(decrypted_data.decode()))
                except Exception as e:
                    print(f"Error decrypting log entry: {e}")
        return logs

# Singleton instance
audit_logger = AuditLogger()
