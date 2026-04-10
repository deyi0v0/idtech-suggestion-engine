-- Mapping hardware to use cases
-- This script must run AFTER use cases and hardware have been inserted.
INSERT INTO hardware_use_case_map (hardware_id, use_case_id)
SELECT h.id, uc.id
FROM (VALUES
    -- ATM Card Readers
    ('Kiosk III', 'ATM Card Readers'),
    ('Kiosk V', 'ATM Card Readers'),
    ('SmartPIN L120', 'ATM Card Readers'),
    ('VP5300', 'ATM Card Readers'),
    ('VP5300 Antenna', 'ATM Card Readers'),
    ('VP5300M', 'ATM Card Readers'),
    ('Zeus', 'ATM Card Readers'),

    -- EV Charging Station Payment Solutions
    ('AP6800', 'EV Charging Station Payment Solutions'),
    ('Kiosk IV', 'EV Charging Station Payment Solutions'),
    ('SmartPIN L80', 'EV Charging Station Payment Solutions'),
    ('VP3300C EXT', 'EV Charging Station Payment Solutions'),
    ('VP5300', 'EV Charging Station Payment Solutions'),
    ('VP5300M', 'EV Charging Station Payment Solutions'),
    ('VP6300', 'EV Charging Station Payment Solutions'),
    ('VP6800', 'EV Charging Station Payment Solutions'),
    ('VP6825', 'EV Charging Station Payment Solutions'),

    -- Loyalty Program Contactless Readers
    ('Kiosk IV', 'Loyalty Program Contactless Readers'),
    ('Kiosk V', 'Loyalty Program Contactless Readers'),
    ('PiP', 'Loyalty Program Contactless Readers'),
    ('VP3300', 'Loyalty Program Contactless Readers'),
    ('VP7200', 'Loyalty Program Contactless Readers'),

    -- Parking Payment Systems
    ('AP6800', 'Parking Payment Systems'),
    ('Kiosk IV', 'Parking Payment Systems'),
    ('SmartPIN L120', 'Parking Payment Systems'),
    ('VP5300', 'Parking Payment Systems'),
    ('VP5300 Antenna', 'Parking Payment Systems'),
    ('VP5300M', 'Parking Payment Systems'),
    ('VP6300', 'Parking Payment Systems'),
    ('VP6800', 'Parking Payment Systems'),
    ('VP6825', 'Parking Payment Systems'),
    ('VP7200', 'Parking Payment Systems'),
    ('Zeus', 'Parking Payment Systems'),

    -- Secure Banking Solutions
    ('Kiosk V', 'Secure Banking Solutions'),

    -- Transit Payment Solutions
    ('AP6800', 'Transit Payment Solutions'),
    ('Kiosk IV', 'Transit Payment Solutions'),
    ('SmartPIN L120', 'Transit Payment Solutions'),
    ('SmartPIN L80', 'Transit Payment Solutions'),
    ('VP3300C EXT', 'Transit Payment Solutions'),
    ('VP5300', 'Transit Payment Solutions'),
    ('VP5300 Antenna', 'Transit Payment Solutions'),
    ('VP5300M', 'Transit Payment Solutions'),
    ('VP6300', 'Transit Payment Solutions'),
    ('VP6800', 'Transit Payment Solutions'),
    ('VP6825', 'Transit Payment Solutions'),
    ('Zeus', 'Transit Payment Solutions'),

    -- Vending Payment Systems
    ('AP6800', 'Vending Payment Systems'),
    ('Kiosk V', 'Vending Payment Systems'),
    ('VP3300 OEM', 'Vending Payment Systems'),
    ('VP6300', 'Vending Payment Systems'),
    ('VP6800', 'Vending Payment Systems'),
    ('VP6825', 'Vending Payment Systems')
) as m(model_name, use_case_name)
JOIN hardware h ON h.model_name = m.model_name
JOIN use_cases uc ON uc.name = m.use_case_name
ON CONFLICT DO NOTHING;