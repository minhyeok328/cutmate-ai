import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

async function readJson(relativePath) {
  const text = await readFile(path.join(root, relativePath), "utf8");
  return JSON.parse(text);
}

const config = await readJson("src-tauri/tauri.conf.json");
const capability = await readJson("src-tauri/capabilities/default.json");
const packageJson = await readJson("package.json");

assertEqual(config.productName, "CutMate AI", "desktop product name");
assertEqual(config.build.frontendDist, "../apps/web/out", "static frontend output path");
assertEqual(config.build.devUrl, "http://localhost:3000", "desktop dev URL");
assertEqual(config.build.beforeDevCommand, "pnpm --filter @cutmate/web dev", "desktop frontend dev command");
assertEqual(config.build.beforeBuildCommand, "pnpm --filter @cutmate/web build", "desktop frontend build command");
assertIncludes(config.bundle.targets, "dmg", "macOS DMG target");
assertIncludes(config.bundle.externalBin, "binaries/cutmate-api", "API sidecar bundle path");
assertIncludes(config.bundle.icon, "icons/icon.icns", "macOS icon path");
assertIncludes(config.bundle.icon, "icons/icon.ico", "Windows icon path");
assertEqual(config.bundle.macOS.minimumSystemVersion, "12.0", "minimum macOS version");
assertCspAllows(config.app.security.csp);
assertEqual(packageJson.scripts["desktop:dev"], "tauri dev", "desktop dev script");
assertEqual(packageJson.scripts["desktop:build"], "tauri build --bundles dmg", "desktop build script");

assertIncludes(capability.windows, "main", "main window capability");
const spawnPermission = capability.permissions.find(
  (permission) =>
    typeof permission === "object" && permission.identifier === "shell:allow-spawn"
);

if (!spawnPermission) {
  throw new Error("Missing shell:allow-spawn permission for the API sidecar");
}

const allowedSidecar = spawnPermission.allow?.find(
  (entry) => entry.name === "binaries/cutmate-api" && entry.sidecar === true
);

if (!allowedSidecar) {
  throw new Error("Missing sidecar allow entry for binaries/cutmate-api");
}

function assertEqual(actual, expected, label) {
  if (actual !== expected) {
    throw new Error(`Invalid ${label}: expected ${expected}, received ${actual}`);
  }
}

function assertIncludes(values, expected, label) {
  if (!Array.isArray(values) || !values.includes(expected)) {
    throw new Error(`Invalid ${label}: expected ${expected}`);
  }
}

function assertCspAllows(csp) {
  if (typeof csp !== "object" || csp === null) {
    throw new Error("Desktop CSP must be enabled and configured");
  }

  assertCspSource(csp["default-src"], "'self'", "default source");
  assertCspSource(csp["connect-src"], "ipc:", "Tauri IPC connection");
  assertCspSource(csp["connect-src"], "http://localhost:8000", "local API connection");
  assertCspSource(csp["connect-src"], "http://127.0.0.1:8000", "desktop API sidecar connection");
  assertCspSource(csp["object-src"], "'none'", "blocked plugin/object content");
}

function assertCspSource(value, expected, label) {
  const values = Array.isArray(value) ? value : String(value ?? "").split(/\s+/);
  if (!values.includes(expected)) {
    throw new Error(`Invalid desktop CSP ${label}: expected ${expected}`);
  }
}
