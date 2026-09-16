
-- Patient Entity
CREATE TABLE Patient (
    PatientID UUID PRIMARY KEY,
    FirstName VARCHAR(255) NOT NULL,
    LastName VARCHAR(255) NOT NULL,
    DateOfBirth DATE NOT NULL,
    Gender VARCHAR(50) NOT NULL,
    ContactInformation JSONB NOT NULL,
    EmergencyContact JSONB NOT NULL
);

-- HealthcareProvider Entity
CREATE TABLE HealthcareProvider (
    ProviderID UUID PRIMARY KEY,
    ProviderName VARCHAR(255) NOT NULL,
    ProviderType VARCHAR(255) NOT NULL,
    ContactInformation JSONB NOT NULL
);

-- Partner Entity
CREATE TABLE Partner (
    PartnerID UUID PRIMARY KEY,
    PartnerName VARCHAR(255) NOT NULL,
    PartnerType VARCHAR(255) NOT NULL,
    ContactInformation JSONB NOT NULL
);

-- Consultation Entity
CREATE TABLE Consultation (
    ConsultationID UUID PRIMARY KEY,
    PatientID UUID REFERENCES Patient(PatientID),
    ProviderID UUID REFERENCES HealthcareProvider(ProviderID)
);