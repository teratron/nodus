const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const MAGIC_DIR = path.join(__dirname, '..');
const CHECKSUMS_FILE = '.checksums';
const CHECKSUMS_PATH = path.join(MAGIC_DIR, CHECKSUMS_FILE);

/**
 * Calculates SHA256 hash of a file.
 */
function getFileHash(filePath) {
    const fileBuffer = fs.readFileSync(filePath);
    const hashSum = crypto.createHash('sha256');
    hashSum.update(fileBuffer);
    return hashSum.digest('hex');
}

/**
 * Recursively gets all files in a directory.
 */
function getAllFiles(dirPath, arrayOfFiles) {
    const files = fs.readdirSync(dirPath);

    arrayOfFiles = arrayOfFiles || [];

    files.forEach((file) => {
        const fullPath = path.join(dirPath, file);
        if (fs.statSync(fullPath).isDirectory()) {
            if (file === 'history') return;
            arrayOfFiles = getAllFiles(fullPath, arrayOfFiles);
        } else {
            arrayOfFiles.push(fullPath);
        }
    });

    return arrayOfFiles;
}

function run() {
    console.log('Generating checksums for .magic/ content...');

    const allFiles = getAllFiles(MAGIC_DIR);
    const checksums = {};

    // For reproducibility, we sort the files
    allFiles.sort().forEach((fullPath) => {
        const relativePath = path.relative(MAGIC_DIR, fullPath).replace(/\\/g, '/');

        // Skip the checksums file itself to avoid recursive hash changes
        if (relativePath === CHECKSUMS_FILE) {
            // Keep the existing hash if it exists, or use a placeholder
            // In this version, we'll just preserve the old value if present to maintain structure
            try {
                const current = JSON.parse(fs.readFileSync(CHECKSUMS_PATH, 'utf8'));
                checksums[CHECKSUMS_FILE] = current[CHECKSUMS_FILE] || 'meta-checksum-placeholder';
            } catch (e) {
                checksums[CHECKSUMS_FILE] = 'meta-checksum-placeholder';
            }
            return;
        }

        checksums[relativePath] = getFileHash(fullPath);
    });

    // Write to .checksums
    const output = JSON.stringify(checksums, null, 2);
    fs.writeFileSync(CHECKSUMS_PATH, output + '\n');

    console.log(`Successfully updated ${CHECKSUMS_PATH}`);
    console.log(`Files processed: ${Object.keys(checksums).length}`);
}

run();
