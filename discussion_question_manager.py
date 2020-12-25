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
    manager.add_question_from_msg(message)
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
            # get random question then remove it from the list
            question = random.choice(self.discussion_questions)
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
        
        # list is empty, no questions
        else:
            response = f"""
            No discussion question this week! :(

            <@{globals.KINJO_ID}>
            """
            return dedent(response)
    
    def add_question(self, q: DiscussionQuestion) -> None:
        self.discussion_questions.append(q)
    
    def add_question_from_msg(self, m: Message) -> None:
        self.add_question(DiscussionQuestion(m))

    
    def change_notifiee(self, n: int) -> None:
        if n in self.notifiees:
            self.notifiees.remove(n) # remove them if they're already added
        else:
            self.notifiees.append(n) # add them if they're not already added