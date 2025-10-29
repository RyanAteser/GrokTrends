-- Table for paid subscribers
CREATE TABLE IF NOT EXISTS paid_members (
                                            id SERIAL PRIMARY KEY,
                                            email VARCHAR(255) UNIQUE NOT NULL,
                                            stripe_customer_id VARCHAR(255),
                                            stripe_subscription_id VARCHAR(255) UNIQUE,
                                            status VARCHAR(50) DEFAULT 'active', -- active, cancelled, past_due
                                            founding_member BOOLEAN DEFAULT false,
                                            monthly_price_cents INTEGER DEFAULT 2000, -- locked in price in cents
                                            created_at TIMESTAMPTZ DEFAULT NOW(),
                                            updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_paid_members_email ON paid_members(email);
CREATE INDEX IF NOT EXISTS idx_paid_members_status ON paid_members(status);
CREATE INDEX IF NOT EXISTS idx_paid_members_stripe_sub ON paid_members(stripe_subscription_id);

-- Add a trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_paid_members_updated_at BEFORE UPDATE
    ON paid_members FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();