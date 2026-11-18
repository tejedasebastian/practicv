import { Buffer } from "node:buffer";

import { expect, test } from "@playwright/test";

const profile = {
  id: "11111111-1111-1111-1111-111111111111",
  full_name: "Fase Dos Demo",
  email: "fase2@example.com",
  phone: null,
  university: null,
  career: "Ingeniería de Software",
  cycle: 8,
  location: "Lima",
  target_roles: ["Data Analyst"],
  preferred_modality: null,
  salary_expectation: null,
  availability: null,
  locale: "es",
  created_at: "2026-11-17T00:00:00Z",
  updated_at: "2026-11-17T00:00:00Z",
};

const cv = {
  cv_id: "22222222-2222-2222-2222-222222222222",
  filename: "cv.pdf",
  mime_type: "application/pdf",
  raw_text: "correo fase2@example.com telefono +51 987 654 321",
  sections: { experiencia: "Practicante de datos", habilidades: "Python PowerBI SQL" },
  skills: [
    {
      skill_id: "33333333-3333-3333-3333-333333333333",
      canonical_name: "Power BI",
      category: "bi",
      level: 1,
      evidence: "PowerBI",
      confidence: 0.9,
      confirmed: false,
    },
    {
      skill_id: "44444444-4444-4444-4444-444444444444",
      canonical_name: "Python",
      category: "programming",
      level: 1,
      evidence: "Python",
      confidence: 0.9,
      confirmed: false,
    },
  ],
  contact: { email: "fase2@example.com", phone: "+51 987 654 321" },
  warnings: ["No se detectó una sección de logros."],
  redacted_text: "correo [EMAIL] telefono [PHONE]",
};

test("profile, CV, skills and AI consent flow", async ({ page }) => {
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();

    if (method === "POST" && url.pathname === "/api/v1/profiles") {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(profile),
      });
      return;
    }
    if (method === "POST" && url.pathname.endsWith("/cv")) {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(cv),
      });
      return;
    }
    if (method === "PATCH" && url.pathname.endsWith("/cv/skills")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          skills: cv.skills.map((skill) => ({ ...skill, level: 3, confirmed: true })),
        }),
      });
      return;
    }
    if (method === "POST" && url.pathname.endsWith("/cv/analyze-ai")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          provider: "stub",
          redacted_text: "correo [EMAIL] telefono [PHONE]",
          pii_removed: true,
          suggestions: ["Agrega logros medibles."],
        }),
      });
      return;
    }
    await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });

  await page.goto("/perfil");
  await expect(page.getByRole("heading", { name: "Tu perfil" })).toBeVisible();

  await page.getByTestId("profile-name").fill("Fase Dos Demo");
  await page.getByTestId("profile-email").fill("fase2@example.com");
  await page.getByTestId("profile-career").fill("Ingeniería de Software");
  await page.getByTestId("profile-save").click();
  await expect(page.getByText("Perfil guardado")).toBeVisible();

  await page.getByTestId("cv-file").setInputFiles({
    name: "cv.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("pdf-demo"),
  });
  await page.getByTestId("cv-upload").click();
  await expect(page.getByText("CV procesado")).toBeVisible();
  await expect(page.getByText("Power BI")).toBeVisible();

  await page.getByTestId("skill-level-0").selectOption("3");
  await page.getByLabel("Confirmada").first().check();
  await page.getByTestId("skills-save").click();
  await expect(page.getByText("Habilidades guardadas")).toBeVisible();

  await page.getByTestId("ai-consent").check();
  await page.getByTestId("ai-analyze").click();
  await expect(page.getByTestId("ai-result")).toContainText("[EMAIL]");
  await expect(page.getByText("Agrega logros medibles.")).toBeVisible();

  await page.screenshot({ path: "docs/assets/profile-cv.png", fullPage: true });
});
