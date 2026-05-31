import { beforeEach, describe, expect, it, vi } from "vitest";

import { isTauriRuntime, startDesktopApiSidecar } from "./desktop-runtime";

const shellMock = vi.hoisted(() => {
  const spawn = vi.fn<() => Promise<void>>();

  return {
    sidecar: vi.fn(() => ({ spawn })),
    spawn
  };
});

vi.mock("@tauri-apps/plugin-shell", () => ({
  Command: {
    sidecar: shellMock.sidecar
  }
}));

describe("desktop runtime", () => {
  beforeEach(() => {
    shellMock.sidecar.mockClear();
    shellMock.spawn.mockReset();
    shellMock.spawn.mockResolvedValue(undefined);
  });

  it("does not start a sidecar in a normal browser", async () => {
    expect(isTauriRuntime({})).toBe(false);
    await expect(startDesktopApiSidecar({})).resolves.toEqual({
      started: false,
      reason: "not-tauri"
    });
  });

  it("detects a Tauri runtime marker", () => {
    expect(isTauriRuntime({ __TAURI_INTERNALS__: {} })).toBe(true);
  });

  it("reuses an in-flight Tauri sidecar startup", async () => {
    let resolveSpawn: (() => void) | undefined;
    shellMock.spawn.mockReturnValueOnce(
      new Promise<void>((resolve) => {
        resolveSpawn = resolve;
      })
    );

    const runtimeWindow = { __TAURI_INTERNALS__: {} };
    const firstStart = startDesktopApiSidecar(runtimeWindow);
    const secondStart = startDesktopApiSidecar(runtimeWindow);

    await vi.waitFor(() => expect(shellMock.sidecar).toHaveBeenCalled());

    resolveSpawn?.();
    await expect(firstStart).resolves.toEqual({ started: true });
    await expect(secondStart).resolves.toEqual({ started: true });
    expect(shellMock.sidecar).toHaveBeenCalledTimes(1);
  });
});
