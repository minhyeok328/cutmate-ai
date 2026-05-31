type SidecarStartResult = {
  started: boolean;
  reason?: "not-tauri" | "unavailable";
};

const SIDECAR_START_PROMISE = "__CUTMATE_API_SIDECAR_START_PROMISE__" as const;

type TauriWindowLike = {
  __TAURI_INTERNALS__?: unknown;
  [SIDECAR_START_PROMISE]?: Promise<SidecarStartResult>;
};

function getRuntimeWindow(): unknown {
  return typeof window === "undefined" ? undefined : window;
}

export function isTauriRuntime(value: unknown = getRuntimeWindow()): value is TauriWindowLike {
  return typeof value === "object" && value !== null && "__TAURI_INTERNALS__" in value;
}

export async function startDesktopApiSidecar(
  runtimeWindow: unknown = getRuntimeWindow()
): Promise<SidecarStartResult> {
  if (!isTauriRuntime(runtimeWindow)) {
    return { started: false, reason: "not-tauri" };
  }

  if (runtimeWindow[SIDECAR_START_PROMISE]) {
    return runtimeWindow[SIDECAR_START_PROMISE];
  }

  const startPromise = spawnApiSidecar();
  runtimeWindow[SIDECAR_START_PROMISE] = startPromise;

  const result = await startPromise;
  if (!result.started) {
    delete runtimeWindow[SIDECAR_START_PROMISE];
  }

  return result;
}

async function spawnApiSidecar(): Promise<SidecarStartResult> {
  try {
    const { Command } = await import("@tauri-apps/plugin-shell");
    const command = Command.sidecar("binaries/cutmate-api");
    await command.spawn();
    return { started: true };
  } catch {
    return { started: false, reason: "unavailable" };
  }
}
