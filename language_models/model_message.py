from enum import Enum

class Role(Enum):
    SYSTEM = 1
    USER = 2
    ASSISTANT = 3

class ModelMessage:
    def __init__(self, role: Role, content: str):
        self.role = role
        self.content = content

    def get_content(self):
        return self.content
    
    def get_role(self):
        return self.role.name.lower()

    def is_system_message(self):
        return self.role == Role.SYSTEM

    def is_user_message(self):
        return self.role == Role.USER
    
    def is_assistant_message(self):
        return self.role == Role.ASSISTANT

