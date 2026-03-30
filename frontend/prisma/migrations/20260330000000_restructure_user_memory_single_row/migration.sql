-- Drop old indexes and constraints
DROP INDEX IF EXISTS "UserMemory_userId_idx";
DROP INDEX IF EXISTS "UserMemory_userId_category_key";

-- Drop old columns
ALTER TABLE "UserMemory" DROP COLUMN IF EXISTS "category";
ALTER TABLE "UserMemory" DROP COLUMN IF EXISTS "content";

-- Add new columns
ALTER TABLE "UserMemory" ADD COLUMN "workContext" TEXT;
ALTER TABLE "UserMemory" ADD COLUMN "personalContext" TEXT;
ALTER TABLE "UserMemory" ADD COLUMN "topOfMind" TEXT;
ALTER TABLE "UserMemory" ADD COLUMN "preferences" TEXT;

-- Add unique constraint on userId (one row per user)
ALTER TABLE "UserMemory" ADD CONSTRAINT "UserMemory_userId_key" UNIQUE ("userId");
