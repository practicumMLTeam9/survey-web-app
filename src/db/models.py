from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, BOOLEAN
from datetime import datetime

from .session import Base


class Poll(Base):
    __tablename__ = 'polls'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_user_id = Column(String)


class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    poll_id = Column(Integer, ForeignKey('polls.id'))
    text = Column(Text)
    type = Column(String)
    is_required = Column(BOOLEAN, default=True)
    position = Column(Integer)


class QuestionOption(Base):
    __tablename__ = 'question_options'

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id'))
    text = Column(Text)
    position = Column(Integer)


class Submission(Base):
    __tablename__ = 'submissions'

    id = Column(Integer, primary_key=True)
    poll_id = Column(Integer, ForeignKey('polls.id'))
    respondent_token = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Answer(Base):
    __tablename__ = 'answers'

    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey('submissions.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    option_id = Column(Integer, ForeignKey('question_options.id'))
    text_value = Column(Text)
