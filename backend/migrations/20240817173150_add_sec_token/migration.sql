/*
  Warnings:

  - The required column `secondary_token` was added to the `PullRequest` table with a prisma-level default value. This is not possible if the table is not empty. Please add this column as optional, then populate it before making it required.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_PullRequest" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "github_id" INTEGER NOT NULL,
    "userId" TEXT,
    "token" TEXT NOT NULL,
    "secondary_token" TEXT NOT NULL,
    CONSTRAINT "PullRequest_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);
INSERT INTO "new_PullRequest" ("github_id", "id", "token", "userId") SELECT "github_id", "id", "token", "userId" FROM "PullRequest";
DROP TABLE "PullRequest";
ALTER TABLE "new_PullRequest" RENAME TO "PullRequest";
CREATE UNIQUE INDEX "PullRequest_github_id_key" ON "PullRequest"("github_id");
CREATE UNIQUE INDEX "PullRequest_token_key" ON "PullRequest"("token");
CREATE UNIQUE INDEX "PullRequest_secondary_token_key" ON "PullRequest"("secondary_token");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
