const fs = require('fs');
const path = require('path');

const designDir = process.env.MAGIC_DESIGN_DIR || '.design';
const changelogPath = path.join(designDir, 'CHANGELOG.md');
const contextPath = path.join(designDir, 'CONTEXT.md');

if (!fs.existsSync(designDir) || !fs.statSync(designDir).isDirectory()) {
    console.error(`Error: ${designDir} directory not found`);
    process.exit(1);
}

const date = new Date().toISOString().split('T')[0];
let contextContent = `# Project Context\n\n**Generated:** ${date}\n\n## Active Technologies\n\n`;

let techList = '';
if (fs.existsSync('package.json')) techList += '- Node.js\n';
if (fs.existsSync('pyproject.toml')) techList += '- Python (uv/poetry/hatch)\n';
if (fs.existsSync('requirements.txt')) techList += '- Python\n';
if (fs.existsSync('Cargo.toml')) techList += '- Rust\n';
if (fs.existsSync('go.mod')) techList += '- Go\n';
if (fs.existsSync('Makefile')) techList += '- Make\n';

if (!techList) {
    contextContent += '- Unknown (no manifest detected)\n';
} else {
    contextContent += techList;
}

contextContent += '\n## Core Project Structure\n\n```plaintext\n';

function buildTree(dir, prefix, currentDepth, maxDepth, ignores) {
    if (currentDepth > maxDepth) return '';
    let result = '';
    let files;
    try {
        files = fs.readdirSync(dir).filter(f => !ignores.includes(f)).sort();
    } catch (e) {
        return '';
    }

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const isLast = i === files.length - 1;
        const fullPath = path.join(dir, file);

        let stat;
        try { stat = fs.statSync(fullPath); } catch (e) { continue; }

        const branch = isLast ? '└── ' : '├── ';
        const name = stat.isDirectory() ? file + '/' : file;

        result += `${prefix}${branch}${name}\n`;

        if (stat.isDirectory()) {
            const nextPrefix = prefix + (isLast ? '    ' : '│   ');
            result += buildTree(fullPath, nextPrefix, currentDepth + 1, maxDepth, ignores);
        }
    }
    return result;
}

const ignoreList = ['node_modules', 'target', '.git', '.venv', '__pycache__'];
try {
    contextContent += '.\n';
    contextContent += buildTree('.', '', 1, 2, ignoreList);
} catch (err) {
    contextContent += `- Project root\n  - ${designDir}/\n  - .magic/\n`;
}
contextContent += '```\n\n## Recent Changes\n\n';

if (fs.existsSync(changelogPath)) {
    const changelogText = fs.readFileSync(changelogPath, 'utf8');
    const lines = changelogText.trimEnd().split(/\r?\n/);
    const last15 = lines.slice(-15).join('\n');
    contextContent += last15 + '\n';
} else {
    contextContent += 'No recent changelog found.\n';
}

contextContent += '\n';

fs.writeFileSync(contextPath, contextContent);
