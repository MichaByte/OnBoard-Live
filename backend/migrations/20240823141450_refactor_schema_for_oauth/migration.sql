/*
  Warnings:

  - You are about to drop the column `known_user_id` on the `PullRequest` table. All the data in the column will be lost.
  - You are about to drop the column `secondary_token` on the `PullRequest` table. All the data in the column will be lost.
  - You are about to drop the column `token` on the `PullRequest` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "User" ADD COLUMN "github_user_id" TEXT;

-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_PullRequest" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "github_id" INTEGER NOT NULL,
    "user_id" TEXT,
    CONSTRAINT "PullRequest_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);
INSERT INTO "new_PullRequest" ("github_id", "id") SELECT "github_id", "id" FROM "PullRequest";
DROP TABLE "PullRequest";
ALTER TABLE "new_PullRequest" RENAME TO "PullRequest";
CREATE UNIQUE INDEX "PullRequest_github_id_key" ON "PullRequest"("github_id");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
