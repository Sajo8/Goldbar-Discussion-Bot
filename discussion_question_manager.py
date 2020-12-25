import pickle
from discussion_question import DiscussionQuestion
import random
import globals
from typing import List
from discord import Message
from textwrap import dedent

class DiscussionQuestionManager:
    """
    Class which takes in a list of DiscussionQuestions
    It then formats it into a string, taking care of all possible cases

    __str__ is overrided, so just print it

    Eg:
    manager = DiscussionQuestionManager()
    manager.add_msg(message)
    print(manager)
    """

    discussion_questions: List[DiscussionQuestion]
    notifiees: List[int]

    # this has to be done in order to make sure Pickle actually saves it
    def __init__(self):
        self.discussion_questions = [] 
        self.notifiees = []

    def __str__(self) -> str:
        # ensure we have some questions
        if len(self.discussion_questions) > 0:
            for i in range(0, len(self.discussion_questions)):
                # get random question then remove it from the list
                question = random.choice(self.discussion_questions)
                # make sure it's verified
                if question.verified:
                    self.discussion_questions.remove(question)

                    response = f"""
                    Discussion question of the week:

                    {question.content}

                    Submitted by <@{question.author}> on {question.date}

                    <@{globals.KINJO_ID}>
                    """
                    for n in self.notifiees:
                        response += f"<@{n}> "
                    
                    return dedent(response)

        # there are no (verified) questions
        response = f"""
        No discussion question this week! :(

        <@{globals.KINJO_ID}>
        """
        return dedent(response)
    
    def add_question(self, q: DiscussionQuestion) -> None:
        self.discussion_questions.append(q)
    
    def add_msg(self, m: Message) -> None:
        self.add_question(DiscussionQuestion(m))
    
    def get_from_verify_id(self, msg_id: int):
        for q in self.discussion_questions:
            return q if msg_id == q.verify_msg_id else None
        return None
        

    def change_notifiee(self, n: int) -> None:
        if n in self.notifiees:
            self.notifiees.remove(n) # remove them if they're already added
        else:
            self.notifiees.append(n) # add them if they're not already added