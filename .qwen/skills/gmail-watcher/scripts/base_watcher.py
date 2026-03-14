from abc import ABC, abstractmethod
from pathlib import Path
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseWatcher(ABC):
    """Base class for all watcher scripts."""
    
    def __init__(self, vault_root: str):
        self.vault_root = Path(vault_root)
        self.state_file = self.vault_root / '.watcher_state.json'
        self.logger = logging.getLogger(self.__class__.__name__)
        self.needs_action_folder = self.vault_root / 'Needs_Action'
    
    @abstractmethod
    def check_for_updates(self) -> list:
        """Return list of new items to process."""
        pass
    
    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create .md file in Needs_Action folder."""
        pass
    
    def load_state(self) -> dict:
        """Load processed item IDs."""
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text(encoding='utf-8'))
            return data.get(self.__class__.__name__, {})
        return {}
    
    def save_state(self, state: dict):
        """Save processed item IDs."""
        all_state = {}
        if self.state_file.exists():
            all_state = json.loads(self.state_file.read_text(encoding='utf-8'))
        all_state[self.__class__.__name__] = state
        self.state_file.write_text(json.dumps(all_state, indent=2), encoding='utf-8')
    
    def generate_filename(self, prefix: str, identifier: str) -> str:
        """Generate unique filename."""
        timestamp = datetime.now().strftime('%Y-%m-%d')
        safe_id = ''.join(c for c in identifier if c.isalnum() or c in ' _-')[:50]
        return f"{prefix}_{safe_id}_{timestamp}.md"
    
    def run(self):
        """Main watcher loop."""
        self.logger.info(f"Starting {self.__class__.__name__}...")
        self.logger.info(f"Vault root: {self.vault_root}")
        
        try:
            new_items = self.check_for_updates()
            self.logger.info(f"Found {len(new_items)} new items")
            
            for item in new_items:
                filepath = self.create_action_file(item)
                self.logger.info(f"Created: {filepath.relative_to(self.vault_root)}")
            
            self.logger.info("Watcher cycle complete")
            
        except Exception as e:
            self.logger.error(f"Error in watcher: {e}", exc_info=True)
