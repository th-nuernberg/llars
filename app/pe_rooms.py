from datetime import datetime
from typing import Dict, Set, Optional
from db.tables import UserPrompt, User
from flask_sqlalchemy import SQLAlchemy
import logging
import json

class PeRooms:
    def __init__(self, db: SQLAlchemy):
        self.db = db
        self.rooms: Dict[str, Dict] = {}  # Stores active rooms
        self.user_rooms: Dict[str, str] = {}  # Maps user_id to room_id

    def _generate_room_id(self, prompt_id: int) -> str:
        """Generate a room ID based on the prompt ID."""
        return f"room_{prompt_id}"

    def create_room(self, prompt_id: int) -> Optional[Dict]:
        """
        Create a new room for collaborative prompt editing.
        Loads the prompt data from the database.
        """
        room_id = self._generate_room_id(prompt_id)

        if room_id in self.rooms:
            return self.rooms[room_id]

        # Load prompt from database
        prompt = UserPrompt.query.get(prompt_id)
        if not prompt:
            return None

        # Sicherstellen, dass prompt.content ein Dictionary ist
        content = prompt.content
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except:
                content = {}

        self.rooms[room_id] = {
            'prompt_id': prompt_id,
            'name': prompt.name,
            'content': content,
            'users': set(),
            'created_at': datetime.utcnow(),
            'last_updated': datetime.utcnow(),
            'owner_id': prompt.user_id
        }

        return self.rooms[room_id]

    def join_room(self, prompt_id: int, user_id: str) -> tuple[Optional[Dict], str]:
        """
        Add a user to a room. Creates the room if it doesn't exist.
        Returns tuple of (room_data, room_id) or (None, '') if failed.
        """
        room_id = self._generate_room_id(prompt_id)

        # Create room if it doesn't exist
        if room_id not in self.rooms:
            room_data = self.create_room(prompt_id)
            if not room_data:
                return None, ''

        # Add user to room
        self.rooms[room_id]['users'].add(user_id)
        self.user_rooms[user_id] = room_id
        self.rooms[room_id]['last_updated'] = datetime.utcnow()
        logging.info(f"User {user_id} joined room {room_id}, room info: {self.rooms[room_id]}")
        return self.rooms[room_id], room_id

    def leave_room(self, user_id: str) -> tuple[bool, str, set]:
        """
        Remove a user from their current room.
        Returns tuple of (success, room_id, remaining_users).
        """
        if user_id not in self.user_rooms:
            return False, '', set()

        room_id = self.user_rooms[user_id]

        # Remove user from room
        self.rooms[room_id]['users'].remove(user_id)
        remaining_users = self.rooms[room_id]['users']
        del self.user_rooms[user_id]

        # Close room if empty
        if not remaining_users:
            self.close_room(room_id)

        return True, room_id, remaining_users

    def close_room(self, room_id: str) -> bool:
        """
        Close a room and clean up resources.
        Returns True if room was successfully closed.
        """
        if room_id not in self.rooms:
            return False

        # Remove all users from the room
        for user_id in list(self.rooms[room_id]['users']):
            if user_id in self.user_rooms:
                del self.user_rooms[user_id]

        # Delete the room
        del self.rooms[room_id]
        return True

    def get_room_data(self, room_id: str) -> Optional[Dict]:
        """Get room data if room exists."""
        return self.rooms.get(room_id)

    def get_user_room(self, user_id: str) -> Optional[Dict]:
        """Get room data for user's current room."""
        room_id = self.user_rooms.get(user_id)
        if room_id:
            return self.rooms.get(room_id)
        return None

    def update_room_content(self, room_id: str, content: Dict) -> bool:
        """
        Update the content of a room and mark last_updated.
        """
        if room_id not in self.rooms:
            return False

        self.rooms[room_id]['content'] = content
        self.rooms[room_id]['last_updated'] = datetime.utcnow()
        return True

    def save_room_to_db(self, room_id: str) -> bool:
        """
        Save the current room content to the database.
        """
        if room_id not in self.rooms:
            return False

        room = self.rooms[room_id]
        prompt = UserPrompt.query.get(room['prompt_id'])

        if not prompt:
            return False

        try:
            prompt.content = json.dumps(room['content'])
            prompt.updated_at = datetime.utcnow()
            self.db.session.commit()
            return True
        except Exception as e:
            self.db.session.rollback()
            print(f"Error saving to database: {e}")
            return False


    def update_room_content(self, room_id: str, content: Dict) -> bool:
        if room_id not in self.rooms:
            return False
        if 'blocks' not in content:
            content['blocks'] = {}
        self.rooms[room_id]['content'] = content
        self.rooms[room_id]['last_updated'] = datetime.utcnow()
        return True