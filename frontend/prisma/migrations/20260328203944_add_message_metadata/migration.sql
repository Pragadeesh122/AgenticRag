-- AlterTable
ALTER TABLE "ChatMessage" ADD COLUMN     "metadata" JSONB NOT NULL DEFAULT '{}';
