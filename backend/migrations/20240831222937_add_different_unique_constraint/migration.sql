/*
  Warnings:

  - A unique constraint covering the columns `[filename]` on the table `Session` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "Session_filename_key" ON "Session"("filename");
