-- Data Cleanup SQL Script for Resume Module Migration
-- This script removes duplicate ATS scores to allow OneToOneField constraint

-- Option 1: Keep only the most recent ATS score for each resume (RECOMMENDED)
-- Uncomment the following lines to use this approach:
/*
DELETE FROM resumes_atsscore
WHERE id NOT IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY resume_id ORDER BY created_at DESC) as rn
        FROM resumes_atsscore
    ) subquery WHERE rn = 1
);
*/

-- Option 2: Keep only the highest scoring ATS score for each resume
-- Uncomment the following lines to use this approach:
/*
DELETE FROM resumes_atsscore
WHERE id NOT IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY resume_id ORDER BY score DESC, created_at DESC) as rn
        FROM resumes_atsscore
    ) subquery WHERE rn = 1
);
*/

-- Option 3: Delete all existing ATS scores (fresh start)
-- Uncomment the following line to use this approach:
/*
DELETE FROM resumes_atsscore;
*/

-- After running ONE of the above options, verify the cleanup:
SELECT resume_id, COUNT(*) as count
FROM resumes_atsscore
GROUP BY resume_id
HAVING COUNT(*) > 1;

-- The above query should return 0 rows if cleanup was successful
