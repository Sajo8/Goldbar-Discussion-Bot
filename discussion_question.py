from discord import Message

class DiscussionQuestion:
    author: str
    content: str
    date: str

    def __init__(self, msg: Message) -> None:
        self.author = msg.author.id
        self.content = msg.content
        self.date = msg.created_at.strftime("%d %b %Y")