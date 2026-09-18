import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import type { VacancyListItem } from "../types";
import VacancyCard from "./VacancyCard.vue";
import VacancyDetails from "./VacancyDetails.vue";

const row: VacancyListItem = {
  vacancy: {
    id: 7,
    source: "hh",
    external_id: "vacancy-7",
    company: "Acme",
    title: "Senior Python Developer",
    url: "https://example.com/vacancy-7",
    description: "<p>Build reliable Python services.</p>",
    location: "Москва",
    remote: true,
    salary_from: "300000",
    salary_to: "400000",
    salary_currency: "RUR",
    published_at: "2026-09-17T10:00:00Z",
    filtered_reason: null,
  },
  analysis: {
    vacancy_id: 7,
    technical_score: 91,
    seniority_score: 85,
    domain_score: 76,
    location_score: 100,
    salary_score: 90,
    final_score: 88,
    recommended: true,
    strengths: ["Strong Python match"],
    gaps: ["No explicit Kafka experience"],
    missing_keywords: ["Kafka"],
    explanation: "The role closely matches the candidate profile.",
    analyzed_at: "2026-09-17T11:00:00Z",
  },
  application: null,
};

afterEach(() => {
  document.body.innerHTML = "";
  document.body.style.overflow = "";
});

describe("VacancyDetails", () => {
  it("shows the complete analysis", () => {
    const wrapper = mount(VacancyDetails, {
      props: { row },
      global: { stubs: { Teleport: true } },
    });

    expect(wrapper.text()).toContain("Senior Python Developer");
    expect(wrapper.text()).toContain("Технологии");
    expect(wrapper.text()).toContain("Strong Python match");
    expect(wrapper.text()).toContain("No explicit Kafka experience");
    expect(wrapper.text()).toContain("Build reliable Python services.");
    expect(wrapper.text()).not.toContain("<p>");
  });

  it("closes with Escape", async () => {
    const wrapper = mount(VacancyDetails, {
      props: { row },
      global: { stubs: { Teleport: true } },
    });

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted("close")).toHaveLength(1);
  });
});

describe("VacancyCard", () => {
  it("opens vacancy details", async () => {
    const wrapper = mount(VacancyCard, { props: { row } });

    await wrapper.get("button.card-button").trigger("click");

    expect(wrapper.emitted("open")).toHaveLength(1);
  });
});
