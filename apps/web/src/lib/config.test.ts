import { describe, expect, it } from "vitest";

import { runtimeConfig } from "./config";

describe("runtimeConfig", () => {
  it("keeps local quality mode separate from OpenAI API usage", () => {
    expect(runtimeConfig.qualityLocalLlm).toBe("openai/gpt-oss-20b");
    expect(runtimeConfig.qualityModeExecution).toBe("self-hosted local inference");
    expect(Object.values(runtimeConfig).join(" ")).not.toContain("OPENAI_API_KEY");
  });

  it("matches the MVP upload contract defaults", () => {
    expect(runtimeConfig.maxDurationMinutes).toBe(20);
    expect(runtimeConfig.maxUploadBytes).toBe(2_147_483_648);
    expect(runtimeConfig.supportedFormats).toEqual(["mp4", "mov", "m4v"]);
  });
});
