from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass



class Customer(Base):
    __tablename__ = "customers"