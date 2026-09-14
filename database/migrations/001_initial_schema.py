
from yoyo import step

__depends__ = {}

steps = [
    step("CREATE TABLE Customer (CustomerID SERIAL PRIMARY KEY, FirstName VARCHAR(50) NOT NULL, LastName VARCHAR(50) NOT NULL, Email VARCHAR(100) UNIQUE NOT NULL, PhoneNumber VARCHAR(20) NOT NULL, DateOfBirth DATE NOT NULL, AuthenticationToken TEXT, VerifiedStatus BOOLEAN DEFAULT FALSE)"),
    step("CREATE TABLE Account (AccountID SERIAL PRIMARY KEY, CustomerID INTEGER REFERENCES Customer(CustomerID), AccountType VARCHAR(50) NOT NULL, AccountNumber VARCHAR(50) UNIQUE NOT NULL)"),
    step("CREATE TABLE Contract (ContractID SERIAL PRIMARY KEY, AccountID INTEGER REFERENCES Account(AccountID), ContractType VARCHAR(50) NOT NULL, ContractData TEXT NOT NULL)")
]