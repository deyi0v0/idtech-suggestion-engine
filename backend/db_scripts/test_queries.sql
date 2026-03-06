-- Check if all records were imported correctly
SELECT 
    (SELECT COUNT(*) FROM hardware) as hardware_count,
    (SELECT COUNT(*) FROM categories) as category_count,
    (SELECT COUNT(*) FROM use_cases) as use_case_count,
    (SELECT COUNT(*) FROM hardware_category_map) as category_mappings,
    (SELECT COUNT(*) FROM hardware_use_case_map) as use_case_mappings;

-- This tests the hardware_category_map join
SELECT h.model_name, h.interface
FROM hardware h
JOIN hardware_category_map hcm ON h.id = hcm.hardware_id
JOIN categories c ON hcm.category_id = c.id
WHERE c.name = 'Unattended Payment Solutions'
ORDER BY h.model_name;

-- Find a device ('VP6800') and list all its categories and use cases
SELECT 
    h.model_name,
    string_agg(DISTINCT c.name, ', ') as categories,
    string_agg(DISTINCT uc.name, ', ') as use_cases
FROM hardware h
LEFT JOIN hardware_category_map hcm ON h.id = hcm.hardware_id
LEFT JOIN categories c ON hcm.category_id = c.id
LEFT JOIN hardware_use_case_map hucm ON h.id = hucm.hardware_id
LEFT JOIN use_cases uc ON hucm.use_case_id = uc.id
WHERE h.model_name = 'VP6800'
GROUP BY h.model_name;

-- Find all devices that have "PCI 6.X" mentioned in their extra_specs
SELECT model_name, extra_specs->>'certifications' as certs
FROM hardware
WHERE extra_specs::text ILIKE '%PCI 6.X%';

-- Find Hardware by Use Case
SELECT h.model_name
FROM hardware h
JOIN hardware_use_case_map hucm ON h.id = hucm.hardware_id
JOIN use_cases uc ON hucm.use_case_id = uc.id
WHERE uc.name = 'EV Charging Station Payment Solutions';

-- Find all devices mapped to multiple use cases
SELECT h.model_name, COUNT(hucm.use_case_id) as use_case_count
FROM hardware h
JOIN hardware_use_case_map hucm ON h.id = hucm.hardware_id
GROUP BY h.model_name
HAVING COUNT(hucm.use_case_id) > 1
ORDER BY use_case_count DESC;

-- Find devices with no use cases
SELECT h.model_name
FROM hardware h
LEFT JOIN hardware_use_case_map hucm ON h.id = hucm.hardware_id
WHERE hucm.use_case_id IS NULL;

-- Find use cases with no hardware
SELECT uc.name
FROM use_cases uc
LEFT JOIN hardware_use_case_map hucm ON uc.id = hucm.use_case_id
WHERE hucm.hardware_id IS NULL;

-- Find devices with no categories
SELECT h.model_name
FROM hardware h
LEFT JOIN hardware_category_map hcm ON h.id = hcm.hardware_id
WHERE hcm.category_id IS NULL;

-- Find categories with no hardware
SELECT c.name
FROM categories c
LEFT JOIN hardware_category_map hcm ON c.id = hcm.category_id
WHERE hcm.hardware_id IS NULL;

-- Find devices with multiple specific use cases
SELECT h.model_name
FROM hardware h
JOIN hardware_use_case_map hucm ON h.id = hucm.hardware_id
JOIN use_cases uc ON hucm.use_case_id = uc.id
WHERE uc.name IN ('EV Charging Station Payment Solutions', 'Loyalty Program Contactless Readers')
GROUP BY h.model_name
HAVING COUNT(DISTINCT uc.name) = 2;