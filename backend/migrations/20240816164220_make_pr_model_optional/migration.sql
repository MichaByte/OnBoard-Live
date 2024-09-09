-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_PullRequest" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "userId" TEXT,
    "token" TEXT NOT NULL,
    CONSTRAINT "PullRequest_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);
INSERT INTO "new_PullRequest" ("id", "token", "userId") SELECT "id", "token", "userId" FROM "PullRequest";
DROP TABLE "PullRequest";
ALTER TABLE "new_PullRequest" RENAME TO "PullRequest";
CREATE UNIQUE INDEX "PullRequest_token_key" ON "PullRequest"("token");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
