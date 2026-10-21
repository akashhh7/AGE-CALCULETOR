const fs = require('fs');
const path = require('path');

const filePath = path.join(process.cwd(), 'website/static/changelog.js');

try {
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const startIndex = fileContent.search(/(const|let|var)\s+releases\s*=\s*\[/);
    if (startIndex === -1) {
        console.error("could not find 'releases' array inside the changelogjs");
        process.exit(1);
    }

    const dataSection = fileContent.substring(startIndex);
    const arrayMatch = dataSection.match(/\[\s*\{[\s\S]*?\}\s*\]/);

    if (!arrayMatch) {
        console.error("could not extract valid array block structure from releases data.");
        process.exit(1);
    }

    const releases = eval(arrayMatch[0]);
    if (!releases || releases.length === 0) {
        console.error("The releases data structure appears to be empty.");
        process.exit(1);
    }

    const latest = releases[0];
    const formatType = (type) => type.charAt(0).toUpperCase() + type.slice(1);

    let markdown = `# ${latest.version} - ${latest.name}\n\n`;
    if (latest.summary) {
        markdown += `${latest.summary}\n\n`;
    }

    markdown += `### Changes\n`;
    latest.changes.forEach(change => {
        markdown += `* **[${formatType(change.type)}]** ${change.text}\n`;
    });

    if (releases.length > 1) {
        markdown += `\n---\n\n<details>\n<summary>Older releases</summary>\n\n`;

        for (let i = 1; i < releases.length; i++) {
            const old = releases[i];
            markdown += `### ${old.version} - ${old.name}\n`;
            old.changes.forEach(change => {
                markdown += `* **[${formatType(change.type)}]** ${change.text}\n`;
            });
            markdown += `\n`;
        }

        markdown += `</details>\n`;
    }

    fs.writeFileSync('RELEASE_NOTES.md', markdown);
    console.log("Successfully generated RELEASE_NOTES.md");

} catch (error) {
    console.error("Error generating release notes:", error);
    process.exit(1);
}
