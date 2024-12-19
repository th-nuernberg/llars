from datetime import datetime
from typing import Dict, Set, Optional
from db.tables import UserPrompt, User
from flask_sqlalchemy import SQLAlchemy
import logging
import json

class PeRooms:
    def __init__(self, db: SQLAlchemy):
        self.db = db
        # rooms[room_id] = {
        #   'prompt_id': int,
        #   'name': str,
        #   'content': dict,
        #   'users': { sid: username },
        #   'cursors': { sid: { 'block_id': str, 'position': int, 'username': str, 'sid': str } },
        #   'created_at': datetime,
        #   'last_updated': datetime,
        #   'owner_id': user_id
        # }
        self.rooms: Dict[str, Dict] = {}
        self.user_rooms: Dict[str, str] = {}  # Maps user_id (sid) to room_id
        self.usernames: Dict[str, str] = {}  # Maps sid to username

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

        prompt = UserPrompt.query.get(prompt_id)
        if not prompt:
            return None

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
            'users': {},
            'cursors': {},  # NEU: Initialisiere Cursor-Dictionary
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

        username = self.usernames.get(user_id, "Unknown User")  # Falls kein Username vorhanden
        self.rooms[room_id]['users'][user_id] = username
        self.user_rooms[user_id] = room_id
        self.rooms[room_id]['last_updated'] = datetime.utcnow()

        # User bekommt beim Joinen noch keinen Cursor gesetzt, könnte man optional tun.
        # self.rooms[room_id]['cursors'][user_id] = {'block_id': None, 'position': 0}

        logging.info(f"User {user_id} joined room {room_id} as {username}, room info: {self.rooms[room_id]}")
        return self.rooms[room_id], room_id

    def leave_room(self, user_id: str) -> tuple[bool, str, dict]:
        """
        Remove a user from their current room.
        Returns tuple of (success, room_id, remaining_users).
        """
        if user_id not in self.user_rooms:
            return False, '', {}

        room_id = self.user_rooms[user_id]
        # Benutzer entfernen
        if user_id in self.rooms[room_id]['users']:
            del self.rooms[room_id]['users'][user_id]
        # Auch den Cursor entfernen
        if user_id in self.rooms[room_id]['cursors']:
            del self.rooms[room_id]['cursors'][user_id]

        remaining_users = self.rooms[room_id]['users']
        del self.user_rooms[user_id]

        # Raum schließen, wenn keine User mehr
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

        # Alle User entfernen
        for user_id in list(self.rooms[room_id]['users'].keys()):
            if user_id in self.user_rooms:
                del self.user_rooms[user_id]

        # Raum löschen
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
        if 'blocks' not in content:
            content['blocks'] = {}
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

    def update_cursor_position(self, room_id: str, user_id: str, block_id: str, position: int) -> bool:
        """
        Update the cursor position for a given user in a room.
        Now includes username and sid in cursor data.
        """
        if room_id not in self.rooms:
            return False

        # Ensure user is in this room
        if user_id not in self.rooms[room_id]['users']:
            return False

        username = self.usernames.get(user_id, "Unknown User")

        self.rooms[room_id]['cursors'][user_id] = {
            'block_id': block_id,
            'position': position,
            'username': username,
            'sid': user_id  # Include the socket ID
        }
        self.rooms[room_id]['last_updated'] = datetime.utcnow()
        return True
