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
    anonymous: bool

    # this has to be done in order to make sure Pickle actually saves it
    def __init__(self):
        self.discussion_questions = []
        self.notifiees = []
        self.anonymous = True

    def __str__(self) -> str:
        if len(self.discussion_questions) > 0:  # ensure we have some questions
            for i in range(0, len(self.discussion_questions)):  # loop through every question
                question = random.choice(
                    self.discussion_questions
                )  # get random question then remove it from the list
                if question.verified:  # make sure it's verified
                    self.discussion_questions.remove(question)

                    if self.anonymous:
                        author_string = f"Submitted by Anonymous on {question.date}"
                    else:
                        author_string = f"Submitted by <@{question.author}> on {question.date}"

                    response = f"""
                    Discussion question of the week:

                    {question.content}

                    {author_string}

                    <@{globals.KINJO_ID}>
                    """
                    for n in self.notifiees:
                        response += f"<@{n}> "

                    return dedent(response)  # return the question and quit

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

    def add_notifiee(self, n: int) -> None:
        if n not in self.notifiees:
            self.notifiees.append(n)

    def remove_notifiee(self, n: int) -> None:
        if n in self.notifiees:
            self.notifiees.remove(n)
