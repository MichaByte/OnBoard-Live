/*
  Warnings:

  - You are about to drop the column `active` on the `Stream` table. All the data in the column will be lost.
  - You are about to drop the column `focused` on the `Stream` table. All the data in the column will be lost.
  - The primary key for the `User` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - You are about to drop the column `slackId` on the `User` table. All the data in the column will be lost.
  - Added the required column `user_id` to the `Stream` table without a default value. This is not possible if the table is not empty.
  - The required column `id` was added to the `User` table with a prisma-level default value. This is not possible if the table is not empty. Please add this column as optional, then populate it before making it required.
  - Added the required column `slack_id` to the `User` table without a default value. This is not possible if the table is not empty.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Stream" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_live" BOOLEAN NOT NULL DEFAULT false,
    "is_focused" BOOLEAN NOT NULL DEFAULT false,
    "key" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    CONSTRAINT "Stream_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Stream" ("id", "key") SELECT "id", "key" FROM "Stream";
DROP TABLE "Stream";
ALTER TABLE "new_Stream" RENAME TO "Stream";
CREATE UNIQUE INDEX "Stream_key_key" ON "Stream"("key");
CREATE UNIQUE INDEX "Stream_user_id_key" ON "Stream"("user_id");
CREATE TABLE "new_User" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "slack_id" TEXT NOT NULL,
    "name" TEXT NOT NULL
);
INSERT INTO "new_User" ("name") SELECT "name" FROM "User";
DROP TABLE "User";
ALTER TABLE "new_User" RENAME TO "User";
CREATE UNIQUE INDEX "User_slack_id_key" ON "User"("slack_id");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
