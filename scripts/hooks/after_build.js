"use strict";
const fs = require("fs");
const archiver = require("archiver");

module.exports = function (configObj) {
  return new Promise((resolve, reject) => {
    console.log("Running after_build hook.");
    //change the extension of the my-archive.xxx file from .war to .zip as needed
    const output = fs.createWriteStream("Sybase.zip");
    //leave unchanged, compression is the same for WAR or Zip file
    const archive = archiver("zip");

    output.on("close", () => {
      console.log("Files were successfully archived.");
      resolve();
    });

    archive.on("warning", (error) => {
      console.warn(error);
    });

    archive.on("error", (error) => {
      reject(error);
    });

    archive.pipe(output);
    archive.directory("web", false);
    archive.finalize();

    resolve(configObj);
  });
};
