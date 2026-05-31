import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

import { WORKSPACE_COPY, workflowSteps } from "./workspace-copy";

const pageSource = readFileSync(new URL("../app/page.tsx", import.meta.url), "utf8");
const globalStyles = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");

describe("workspace Korean copy", () => {
  it("keeps the primary workspace labels in Korean", () => {
    expect(WORKSPACE_COPY.appName).toBe("컷메이트 AI");
    expect(WORKSPACE_COPY.sections.script).toBe("대본 편집");
    expect(WORKSPACE_COPY.actions.runAnalysis).toBe("AI 분석 시작");
    expect(WORKSPACE_COPY.actions.render).toBe("내보내기 생성");
    expect(workflowSteps.map((step) => step.label)).toEqual([
      "업로드",
      "분석",
      "대본",
      "내보내기"
    ]);
  });

  it("keeps the MVP media limits visible to the user", () => {
    expect(WORKSPACE_COPY.upload.help).toContain("2GB");
    expect(WORKSPACE_COPY.upload.help).toContain("20분");
    expect(WORKSPACE_COPY.upload.help).toContain("MP4");
  });

  it("uses script-first editing language instead of generic dashboard language", () => {
    const allCopy = JSON.stringify(WORKSPACE_COPY);
    expect(allCopy).toContain("대본");
    expect(allCopy).toContain("자막");
    expect(allCopy).toContain("컷");
    expect(allCopy).not.toContain("Review Workspace");
    expect(allCopy).not.toContain("Render Queue");
  });

  it("keeps the desktop editor grid from forcing laptop-width overflow", () => {
    const editorGridRule = globalStyles.match(/\.editor-grid\s*\{(?<body>[^}]*)\}/)?.groups?.body;

    expect(editorGridRule).toBeDefined();
    expect(editorGridRule).not.toMatch(/minmax\(\d+px,/);
  });

  it("announces the selected export aspect ratio to assistive tech", () => {
    expect(pageSource).toContain("aria-pressed={exportAspectRatio === option.value}");
  });
});
