from sqlalchemy import Column, Integer, String
from Database import Base

class Accounts(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    contact = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return f"<Account {self.email}>"