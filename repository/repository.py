
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from repository.customer import Customer
from repository.account import Account
from repository.contract import Contract

class Repository:
    def __init__(self, db_url):
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def get_customer_by_id(self, customer_id):
        return self.session.query(Customer).filter(Customer.customer_id == customer_id).first()

    def get_account_by_id(self, account_id):
        return self.session.query(Account).filter(Account.account_id == account_id).first()

    def get_contract_by_id(self, contract_id):
        return self.session.query(Contract).filter(Contract.contract_id == contract_id).first()