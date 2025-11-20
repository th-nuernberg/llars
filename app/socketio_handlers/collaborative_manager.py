"""
Collaborative Manager for SocketIO
Handles collaborative editing sessions, user presence, and cursor positions.
"""

from datetime import datetime


class CollaborativeManager:
    """Manages collaborative editing features for prompt engineering"""

    def __init__(self):
        self.active_prompts = {}  # Speichert aktive Prompts und deren Collaborators
        self.user_rooms = {}  # Speichert, in welchen Räumen sich ein User befindet
        self.cursor_positions = {}  # Speichert Cursor-Positionen

    def join_prompt(self, prompt_id, user_id, username):
        """Add a user to a collaborative prompt session"""
        room_id = f"prompt_{prompt_id}"
        if room_id not in self.active_prompts:
            self.active_prompts[room_id] = {
                'collaborators': {},
                'content': {}
            }

        self.active_prompts[room_id]['collaborators'][user_id] = {
            'username': username,
            'joined_at': datetime.now().isoformat()
        }

        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        self.user_rooms[user_id].add(room_id)

        return list(self.active_prompts[room_id]['collaborators'].values())

    def leave_prompt(self, prompt_id, user_id):
        """Remove a user from a collaborative prompt session"""
        room_id = f"prompt_{prompt_id}"
        if room_id in self.active_prompts:
            if user_id in self.active_prompts[room_id]['collaborators']:
                del self.active_prompts[room_id]['collaborators'][user_id]

            if user_id in self.user_rooms:
                self.user_rooms[user_id].remove(room_id)

            # Lösche Cursor-Position
            if user_id in self.cursor_positions:
                del self.cursor_positions[user_id]

            return list(self.active_prompts[room_id]['collaborators'].values())
        return []

    def update_cursor(self, prompt_id, user_id, block_id, position):
        """Update cursor position for a user in a prompt"""
        self.cursor_positions[user_id] = {
            'prompt_id': prompt_id,
            'block_id': block_id,
            'position': position,
            'timestamp': datetime.now().isoformat()
        }
        return self.cursor_positions[user_id]

    def get_collaborators(self, prompt_id):
        """Get all collaborators for a prompt"""
        room_id = f"prompt_{prompt_id}"
        if room_id in self.active_prompts:
            return list(self.active_prompts[room_id]['collaborators'].values())
        return []
