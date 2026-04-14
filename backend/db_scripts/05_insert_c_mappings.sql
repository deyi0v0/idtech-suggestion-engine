-- Mapping hardware to categories
-- This script must run AFTER categories and hardware have been inserted.
INSERT INTO hardware_category_map (hardware_id, category_id)
SELECT h.id, c.id
FROM (VALUES
    -- Countertop Solution
    ('Augusta', 'Countertop Solution'),
    ('EconoScan III', 'Countertop Solution'),
    ('PiP', 'Countertop Solution'),
    ('SREDKey 2', 'Countertop Solution'),
    ('ValueScan III', 'Countertop Solution'),
    ('VP3350', 'Countertop Solution'),
    ('VP8300', 'Countertop Solution'),

    -- EMV Common Kernel
    ('AP6800', 'EMV Common Kernel'),
    ('Kiosk V', 'EMV Common Kernel'),
    ('MiniSmart II', 'EMV Common Kernel'),
    ('VP3300', 'EMV Common Kernel'),
    ('VP3350', 'EMV Common Kernel'),
    ('VP5300', 'EMV Common Kernel'),
    ('VP5300M', 'EMV Common Kernel'),
    ('VP6300', 'EMV Common Kernel'),
    ('VP6800', 'EMV Common Kernel'),
    ('VP6825', 'EMV Common Kernel'),
    ('VP7200', 'EMV Common Kernel'),
    ('VP8300', 'EMV Common Kernel'),

    -- Legacy Products
    ('Gaming Reader', 'Legacy Products'),
    ('Kiosk III', 'Legacy Products'),
    ('MiniMag Duo', 'Legacy Products'),
    ('MiniMag II', 'Legacy Products'),
    ('Omni', 'Legacy Products'),
    ('SecureKey M130', 'Legacy Products'),
    ('SecureMag', 'Legacy Products'),
    ('Spectrum Air', 'Legacy Products'),
    ('Spectrum III Hybrid', 'Legacy Products'),
    ('VP6300', 'Legacy Products'),

    -- Mobile Payment Devices
    ('AP3880P', 'Mobile Payment Devices'),
    ('VP3300', 'Mobile Payment Devices'),
    ('VP3350', 'Mobile Payment Devices'),
    ('VP3600', 'Mobile Payment Devices'),

    -- OEM Payment Products
    ('2D Scan FX200', 'OEM Payment Products'),
    ('MiniSmart II', 'OEM Payment Products'),
    ('MSR Assemblies', 'OEM Payment Products'),
    ('PiP OEM', 'OEM Payment Products'),
    ('SecureHead', 'OEM Payment Products'),
    ('VP3300 OEM', 'OEM Payment Products'),
    ('VP3300C EXT', 'OEM Payment Products'),

    -- Unattended Payment Solutions
    ('AP6800', 'Unattended Payment Solutions'),
    ('Kiosk IV', 'Unattended Payment Solutions'),
    ('Kiosk V', 'Unattended Payment Solutions'),
    ('SmartPIN L120', 'Unattended Payment Solutions'),
    ('SmartPIN L80', 'Unattended Payment Solutions'),
    ('VP5300', 'Unattended Payment Solutions'),
    ('VP5300 Antenna', 'Unattended Payment Solutions'),
    ('VP5300M', 'Unattended Payment Solutions'),
    ('VP6300', 'Unattended Payment Solutions'),
    ('VP6800', 'Unattended Payment Solutions'),
    ('VP6825', 'Unattended Payment Solutions'),
    ('VP7200', 'Unattended Payment Solutions'),
    ('Zeus', 'Unattended Payment Solutions')
) as m(model_name, category_name)
JOIN hardware h ON h.model_name = m.model_name
JOIN categories c ON c.name = m.category_name
ON CONFLICT DO NOTHING;
