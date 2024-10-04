/*
  Warnings:

  - You are about to drop the column `user_id` on the `Session` table. All the data in the column will be lost.
  - Added the required column `pr_id` to the `Session` table without a default value. This is not possible if the table is not empty.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Session" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "pr_id" INTEGER NOT NULL,
    "timestamp" TEXT NOT NULL,
    "filename" TEXT NOT NULL,
    "duration" INTEGER NOT NULL,
    "reviewed" BOOLEAN NOT NULL DEFAULT false,
    "approved" BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT "Session_pr_id_fkey" FOREIGN KEY ("pr_id") REFERENCES "PullRequest" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Session" ("approved", "duration", "filename", "id", "reviewed", "timestamp") SELECT "approved", "duration", "filename", "id", "reviewed", "timestamp" FROM "Session";
DROP TABLE "Session";
ALTER TABLE "new_Session" RENAME TO "Session";
CREATE UNIQUE INDEX "Session_pr_id_key" ON "Session"("pr_id");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
