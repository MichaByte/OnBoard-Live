-- CreateTable
CREATE TABLE "Stream" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "key" TEXT NOT NULL,
    "active" BOOLEAN NOT NULL DEFAULT false,
    "focused" BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT "Stream_key_fkey" FOREIGN KEY ("key") REFERENCES "User" ("slackId") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "User" (
    "slackId" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "Stream_key_key" ON "Stream"("key");

-- CreateIndex
CREATE UNIQUE INDEX "User_slackId_key" ON "User"("slackId");
