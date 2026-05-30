export const runtimeConfig = {
  appName: "CutMate AI",
  apiUrl: process.env.NEXT_PUBLIC_CUTMATE_API_URL ?? "http://localhost:8000",
  maxDurationMinutes: 20,
  maxUploadBytes: 2_147_483_648,
  supportedFormats: ["mp4", "mov", "m4v"] as const,
  modes: ["light", "standard", "quality"] as const,
  defaultLocalLlm: "Qwen/Qwen3-8B",
  qualityLocalLlm: "openai/gpt-oss-20b",
  qualityModeExecution: "self-hosted local inference"
} as const;

export type AnalysisMode = (typeof runtimeConfig.modes)[number];
