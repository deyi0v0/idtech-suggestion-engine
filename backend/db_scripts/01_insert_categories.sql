INSERT INTO categories (name) VALUES
    ('Countertop Solution'),
    ('EMV Common Kernel'),
    ('Legacy Products'),
    ('Mobile Payment Devices'),
    ('OEM Payment Products'),
    ('Unattended Payment Solutions')
ON CONFLICT (name) DO NOTHING;