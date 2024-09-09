/*
  Warnings:

  - You are about to drop the column `github_user_id` on the `User` table. All the data in the column will be lost.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_User" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "slack_id" TEXT NOT NULL,
    "name" TEXT NOT NULL
);
INSERT INTO "new_User" ("created_at", "id", "name", "slack_id") SELECT "created_at", "id", "name", "slack_id" FROM "User";
DROP TABLE "User";
ALTER TABLE "new_User" RENAME TO "User";
CREATE UNIQUE INDEX "User_slack_id_key" ON "User"("slack_id");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
