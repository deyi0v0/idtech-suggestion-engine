-- Mapping hardware to software
-- This script must run AFTER software and hardware have been inserted.
INSERT INTO hardware_software_map (hardware_id, software_id)
SELECT h.id, s.id
FROM (VALUES
    -- RKI
    ('Kiosk III', 'RKI'),
    ('Kiosk V', 'RKI'),
    ('SmartPIN L80', 'RKI'),
    ('SecureMag', 'RKI'),
    ('SecureKey M130', 'RKI'),
    ('SecureHead', 'RKI'),
    ('Augusta', 'RKI'),
    ('AP3880P', 'RKI'),
    ('AP6800', 'RKI'),
    ('Kiosk IV', 'RKI'),
    ('MiniSmart II', 'RKI'),
    ('SmartPIN L120', 'RKI'),
    ('SREDKey 2', 'RKI'),
    ('VP3300C EXT', 'RKI'),
    ('VP3300', 'RKI'),
    ('VP3300 OEM', 'RKI'),
    ('VP3350', 'RKI'),
    ('VP3600', 'RKI'),
    ('VP5300M', 'RKI'),
    ('VP5300 Antenna', 'RKI'),
    ('VP5300', 'RKI'),
    ('VP6300', 'RKI'),
    ('VP6800', 'RKI'),
    ('VP6825', 'RKI'),
    ('VP8300', 'RKI'),
    ('VP7200', 'RKI'),

    -- RDM
    ('Kiosk V', 'RDM'),
    ('AP6800', 'RDM'),
    ('VP3350', 'RDM'),
    ('VP3600', 'RDM'),
    ('VP5300', 'RDM'),
    ('VP6300', 'RDM'),
    ('VP6800', 'RDM'),
    ('VP6825', 'RDM'),
    ('VP7200', 'RDM'),

    -- PAE
    ('Kiosk V', 'PAE'),
    ('VP3350', 'PAE'),
    ('VP5300', 'PAE'),
    ('VP6800', 'PAE'),
    ('VP6825', 'PAE'),
    ('VP7200', 'PAE')
) as m(model_name, software_name)
JOIN hardware h ON h.model_name = m.model_name
JOIN software s ON s.name = m.software_name
ON CONFLICT DO NOTHING;