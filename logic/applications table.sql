-- Create applications table
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    position_title VARCHAR(255) NOT NULL,
    job_url TEXT,
    location VARCHAR(255),
    salary VARCHAR(100),
    description TEXT,
    requirements TEXT,
    status VARCHAR(50) DEFAULT 'Applied' NOT NULL,
    date_applied TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deadline DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- Create index on status for faster queries
CREATE INDEX idx_applications_status ON applications(status);

-- Create index on date_applied for sorting
CREATE INDEX idx_applications_date_applied ON applications(date_applied DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_applications_updated_at 
    BEFORE UPDATE ON applications 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
-- Sample data (optional)
INSERT INTO applications (company_name, position_title, location, salary, status) 
VALUES 
    ('Google', 'Software Engineer', 'London, UK', '£60,000 - £80,000', 'Applied'),
    ('Microsoft', 'Backend Developer', 'Remote', '£55,000 - £75,000', 'Pending Interview'),
    ('Amazon', 'Full Stack Developer', 'Manchester, UK', '£50,000 - £70,000', 'Interview Scheduled');
"""