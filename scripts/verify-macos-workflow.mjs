import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const workflow = await readFile(path.join(root, ".github/workflows/build-macos.yml"), "utf8");
const guide = await readFile(path.join(root, "docs/desktop-build.md"), "utf8");

assertIncludes(workflow, "workflow_dispatch:", "manual workflow trigger");
assertExcludes(workflow, "\n  push:", "push trigger");
assertExcludes(workflow, "\n  pull_request:", "pull request trigger");
assertExcludes(workflow, "\n  schedule:", "schedule trigger");
assertIncludes(workflow, "runs-on: macos-latest", "macOS runner");
assertIncludes(workflow, "permissions:\n  contents: read", "read-only workflow permission");
assertIncludes(workflow, "retention-days: 3", "short artifact retention");
assertIncludes(
  workflow,
  "uv run pyinstaller --onefile --name cutmate-api --collect-submodules app",
  "PyInstaller sidecar build"
);
assertIncludes(workflow, "src-tauri/binaries/cutmate-api-${TARGET_TRIPLE}", "target-specific sidecar path");
assertIncludes(workflow, "pnpm build", "pre-DMG app build verification");
assertIncludes(workflow, "pnpm desktop:build", "root desktop build script");
assertIncludes(workflow, "src-tauri/target/release/bundle/dmg/*.dmg", "DMG artifact path");

assertIncludes(guide, "# CutMate AI macOS 빌드 가이드", "Korean guide title");
assertIncludes(guide, "서명되지 않은 DMG", "unsigned DMG explanation");
assertIncludes(guide, "GitHub Actions", "GitHub Actions instructions");
assertIncludes(guide, "Apple Developer Program", "future signing path");

function assertIncludes(text, expected, label) {
  if (!text.includes(expected)) {
    throw new Error(`Missing ${label}: ${expected}`);
  }
}

function assertExcludes(text, unwanted, label) {
  if (text.includes(unwanted)) {
    throw new Error(`Unexpected ${label}: ${unwanted}`);
  }
}
