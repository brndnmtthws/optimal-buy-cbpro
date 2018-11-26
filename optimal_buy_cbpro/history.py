#!/usr/bin/env python3
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    currency = Column(String)
    price = Column(Float)
    size = Column(Float)
    cbpro_order_id = Column(String)
    created_at = Column(DateTime)


class Withdrawal(Base):
    __tablename__ = 'withdrawals'

    id = Column(Integer, primary_key=True)
    currency = Column(String)
    amount = Column(Float)
    crypto_address = Column(String)
    cbpro_withdrawal_id = Column(String)


class Deposit(Base):
    __tablename__ = 'deposits'

    id = Column(Integer, primary_key=True)
    currency = Column(String)
    amount = Column(Float)
    payment_method_id = Column(String)
    payout_at = Column(DateTime)
    cbpro_deposit_id = Column(String)


def get_session(engine):
    engine = create_engine(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session
