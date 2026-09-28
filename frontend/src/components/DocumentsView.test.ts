import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import DocumentsView from "./DocumentsView.vue";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("DocumentsView", () => {
  it("handles Markdown documents", async () => {
    const coverLetter = Array.from({ length: 10 }, (_, index) => `Строка письма ${index + 1}`);
    const fetchMock = vi.fn(async (
      input: string | URL | Request,
      options?: RequestInit,
    ) => {
      const path = String(input);
      if (path === "/documents/resumes") {
        return Response.json([
          { name: "resume.md", size: 128, modified_at: "2026-09-21T08:00:00Z" },
        ]);
      }
      if (path === "/documents/vacancies") {
        return Response.json([
          { name: "backend.markdown", size: 256, modified_at: "2026-09-21T08:00:00Z" },
        ]);
      }
      if (path.startsWith("/documents/catalog/")) return Response.json([]);
      if (path === "/documents/analyze" && options?.method === "POST") {
        return Response.json([{
          vacancy_file: "backend.markdown",
          final_score: 85,
          technical_score: 90,
          seniority_score: 80,
          domain_score: 70,
          strengths: ["Python"],
          gaps: [],
          missing_keywords: [],
          recommendations: ["Emphasize Python"],
          cover_letter: coverLetter,
          explanation: "Strong match",
        }]);
      }
      return Response.json({ detail: "Unexpected request" }, { status: 500 });
    });
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(DocumentsView);
    await flushPromises();

    expect(wrapper.get<HTMLSelectElement>("#resume-file").element.value).toBe("resume.md");
    expect(wrapper.text()).toContain("backend.markdown");
    expect(wrapper.text()).toContain("PDF или Markdown");

    await wrapper.get("form.document-controls").trigger("submit");
    await flushPromises();

    expect(wrapper.text()).toContain("Сопроводительное письмо");
    expect(wrapper.findAll(".cover-letter p")).toHaveLength(10);
  });
});
