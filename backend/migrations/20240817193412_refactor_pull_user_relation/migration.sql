/*
  Warnings:

  - You are about to drop the column `userId` on the `PullRequest` table. All the data in the column will be lost.

*/
-- CreateTable
CREATE TABLE "_PullRequestToPossibleUser" (
    "A" INTEGER NOT NULL,
    "B" TEXT NOT NULL,
    CONSTRAINT "_PullRequestToPossibleUser_A_fkey" FOREIGN KEY ("A") REFERENCES "PullRequest" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "_PullRequestToPossibleUser_B_fkey" FOREIGN KEY ("B") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_PullRequest" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "github_id" INTEGER NOT NULL,
    "known_user_id" TEXT,
    "token" TEXT NOT NULL,
    "secondary_token" TEXT NOT NULL,
    CONSTRAINT "PullRequest_known_user_id_fkey" FOREIGN KEY ("known_user_id") REFERENCES "User" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);
INSERT INTO "new_PullRequest" ("github_id", "id", "secondary_token", "token") SELECT "github_id", "id", "secondary_token", "token" FROM "PullRequest";
DROP TABLE "PullRequest";
ALTER TABLE "new_PullRequest" RENAME TO "PullRequest";
CREATE UNIQUE INDEX "PullRequest_github_id_key" ON "PullRequest"("github_id");
CREATE UNIQUE INDEX "PullRequest_token_key" ON "PullRequest"("token");
CREATE UNIQUE INDEX "PullRequest_secondary_token_key" ON "PullRequest"("secondary_token");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;

-- CreateIndex
CREATE UNIQUE INDEX "_PullRequestToPossibleUser_AB_unique" ON "_PullRequestToPossibleUser"("A", "B");

-- CreateIndex
CREATE INDEX "_PullRequestToPossibleUser_B_index" ON "_PullRequestToPossibleUser"("B");
