import { describe, expect, it } from "vitest";

import { WORKSPACE_COPY, workflowSteps } from "./workspace-copy";

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
});
