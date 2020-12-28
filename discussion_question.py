from discord import Message

class DiscussionQuestion:
    author: str
    content: str
    date: str
    verified: bool
    verify_msg_id: int

    def __init__(self, msg: Message) -> None:
        self.author = msg.author.id
        self.content = msg.content.replace(".submit ", "")
        self.date = msg.created_at.strftime("%d %b %Y @ %I:%M%p UTC")
        self.verified = False
        self.verify_msg_id = 0
    
    def add_verify_id(self, msg_id: int):
        self.verify_msg_id = msg_id
    
    def verify(self):
        self.verified = True