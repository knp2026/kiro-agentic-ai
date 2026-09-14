
-- Create the Customer table
CREATE TABLE Customer (
    CustomerID SERIAL PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    PhoneNumber VARCHAR(20) UNIQUE NOT NULL,
    DateOfBirth DATE NOT NULL,
    AuthenticationToken TEXT,
    VerifiedStatus BOOLEAN NOT NULL DEFAULT FALSE
);

-- Create the Account table
CREATE TABLE Account (
    AccountID SERIAL PRIMARY KEY,
    CustomerID INTEGER REFERENCES Customer(CustomerID),
    AccountType VARCHAR(50) NOT NULL,
    AccountNumber VARCHAR(50) UNIQUE NOT NULL
);

-- Create the Contract table
CREATE TABLE Contract (
    ContractID SERIAL PRIMARY KEY,
    AccountID INTEGER REFERENCES Account(AccountID),
    ContractType VARCHAR(50) NOT NULL,
    ContractData JSONB NOT NULL
);