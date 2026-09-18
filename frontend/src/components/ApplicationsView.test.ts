import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import ApplicationsView from "./ApplicationsView.vue";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ApplicationsView", () => {
  it("saves an application note", async () => {
    const fetchMock = vi.fn(async (input: string | URL | Request, options?: RequestInit) => {
      const path = String(input);
      if (path.startsWith("/applications?") && !options?.method) {
        return Response.json([{
          id: 4,
          vacancy_id: 7,
          status: "shortlisted",
          notes: null,
          created_at: "2026-09-17T10:00:00Z",
          updated_at: "2026-09-17T10:00:00Z",
        }]);
      }
      if (path.startsWith("/vacancies?")) {
        return Response.json([{
          vacancy: {
            id: 7,
            source: "hh",
            external_id: "vacancy-7",
            company: "Acme",
            title: "Senior Python Developer",
            url: "https://example.com/vacancy-7",
            description: "Python services",
            location: null,
            remote: true,
            salary_from: null,
            salary_to: null,
            salary_currency: null,
            published_at: null,
            filtered_reason: null,
          },
          analysis: null,
          application: null,
        }]);
      }
      if (path === "/applications/4" && options?.method === "PATCH") {
        return Response.json({
          id: 4,
          vacancy_id: 7,
          status: "shortlisted",
          notes: "Написать рекрутеру",
          created_at: "2026-09-17T10:00:00Z",
          updated_at: "2026-09-17T11:00:00Z",
        });
      }
      return Response.json({ detail: "Unexpected request" }, { status: 500 });
    });
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(ApplicationsView);
    await flushPromises();
    await wrapper.get("textarea").setValue("Написать рекрутеру");
    await wrapper.get("button.card-button").trigger("click");
    await flushPromises();

    const patchCall = fetchMock.mock.calls.find(([, options]) => options?.method === "PATCH");
    expect(patchCall?.[0]).toBe("/applications/4");
    expect(patchCall?.[1]?.body).toBe(JSON.stringify({ notes: "Написать рекрутеру" }));
    expect(wrapper.get("button.card-button").attributes("disabled")).toBeDefined();
  });
});
