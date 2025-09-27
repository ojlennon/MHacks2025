CREATE TABLE lisence_plates(
    plate_number VARCHAR(10) PRIMARY KEY,
    owner_name VARCHAR(100) NOT NULL,
    DOB DATE NOT NULL,
    hasWarrant BOOLEAN DEFAULT FALSE,
    warrant_reason TEXT,
    registration_date DATE DEFAULT CURRENT_DATE,
    isStolen BOOLEAN DEFAULT FALSE
)