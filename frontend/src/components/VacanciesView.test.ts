import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import VacanciesView from "./VacanciesView.vue";

afterEach(() => {
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
});

describe("VacanciesView", () => {
  it("restores filters from the URL", async () => {
    window.history.replaceState(
      {},
      "",
      "/?query=Python&vacancy_state=recommended&remote=true",
    );
    const fetchMock = vi.fn(async (_input: string | URL | Request) => Response.json([]));
    vi.stubGlobal("fetch", fetchMock);

    const wrapper = mount(VacanciesView);
    await flushPromises();

    expect(wrapper.get<HTMLInputElement>('input[type="search"]').element.value).toBe("Python");
    expect(wrapper.get<HTMLSelectElement>("select").element.value).toBe("recommended");
    expect(wrapper.get<HTMLInputElement>('.filters input[type="checkbox"]').element.checked).toBe(true);
    expect(String(fetchMock.mock.calls[0]?.[0])).toContain("query=Python");
    expect(String(fetchMock.mock.calls[0]?.[0])).toContain("vacancy_state=recommended");
    expect(String(fetchMock.mock.calls[0]?.[0])).toContain("remote=true");
  });
});
