
-- Insert sample data into the Customer table
INSERT INTO Customer (FirstName, LastName, Email, PhoneNumber, DateOfBirth)
VALUES ('John', 'Doe', 'johndoe@example.com', '+1234567890', '1980-01-01');

-- Insert sample data into the Account table
INSERT INTO Account (CustomerID, AccountType, AccountNumber)
VALUES (1, 'Checking', '1234567890');

-- Insert sample data into the Contract table
INSERT INTO Contract (AccountID, ContractType, ContractData)
VALUES (1, 'Loan', '{"loan_amount": 100000, "interest_rate": 5.5, "term_years": 30}');