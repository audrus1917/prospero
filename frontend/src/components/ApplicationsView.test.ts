import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import ApplicationsView from "./ApplicationsView.vue";

// Restore browser globals after each test so fetch mocks cannot leak.
afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ApplicationsView", () => {
  it("saves an application note", async () => {
    // One mock models all API endpoints used during mount and note submission.
    const fetchMock = vi.fn(async (input: string | URL | Request, options?: RequestInit) => {
      const path = String(input);
      // Initial tracking-record request.
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
      // Parallel vacancy request provides display metadata for the application.
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
      // PATCH response represents the canonical note returned after persistence.
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

    // Wait for mounted network requests before interacting with rendered controls.
    const wrapper = mount(ApplicationsView);
    await flushPromises();
    await wrapper.get("textarea").setValue("Написать рекрутеру");
    await wrapper.get("button.card-button").trigger("click");
    await flushPromises();

    // Verify both the endpoint contract and the exact serialized request payload.
    const patchCall = fetchMock.mock.calls.find(([, options]) => options?.method === "PATCH");
    expect(patchCall?.[0]).toBe("/applications/4");
    expect(patchCall?.[1]?.body).toBe(JSON.stringify({ notes: "Написать рекрутеру" }));
    // The button disables after the saved value and local draft are synchronized.
    expect(wrapper.get("button.card-button").attributes("disabled")).toBeDefined();
  });
});
