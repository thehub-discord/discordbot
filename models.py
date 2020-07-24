"""
Created by Epic at 7/23/20
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, BigInteger, String, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger(), unique=True, primary_key=True)
    github_username = Column(String(), unique=True)
    commits = relationship("Commit")


class Commit(Base):
    __tablename__ = "commits"
    commit_id = Column(String, unique=True, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
