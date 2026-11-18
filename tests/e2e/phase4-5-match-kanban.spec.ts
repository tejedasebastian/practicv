import { expect, test } from "@playwright/test";

const profileId = "profile-1";
const offerId = "offer-1";
const applicationId = "application-1";

const offer = {
  id: offerId,
  source_type: "manual",
  external_id: null,
  source_url: "https://example.com/offer-1",
  captured_at: "2026-11-17T00:00:00Z",
  title: "Practicante de Datos UI",
  company: "UI Data Corp",
  location: "Lima",
  modality: "Híbrido",
  salary_text: "S/ 1,500",
  salary_amount: 1500,
  salary_currency: "PEN",
  description: "Oferta de datos",
  requirements_text: "SQL, Power BI",
  published_at: null,
  deadline_at: null,
  parse_confidence: null,
  dedupe_hash: "hash-offer-1",
};

const match = {
  id: "match-1",
  profile_id: profileId,
  offer_id: offerId,
  overall_score: 85,
  must_have_score: 83,
  confidence: 90,
  decision: "apply_with_gaps",
  gaps_json: [
    {
      skill: "Power BI",
      requirement_type: "must",
      required_level: 2,
      user_level: 1,
      evidence: "Power BI intermedio",
      suggestion: "Sube Power BI de nivel 1 a 2.",
    },
  ],
  explanation_json: [
    {
      skill: "Power BI",
      requirement_type: "must",
      required_level: 2,
      user_level: 1,
      status: "gap",
      evidence: "Power BI intermedio",
      suggestion: "Sube Power BI de nivel 1 a 2.",
    },
  ],
  overridden: false,
  override_reason: null,
  created_at: "2026-11-17T00:00:00Z",
};

const overriddenMatch = {
  ...match,
  decision: "apply",
  overridden: true,
  override_reason: "Revisado manualmente",
};

const application = {
  id: applicationId,
  profile_id: profileId,
  offer_id: offerId,
  status: "saved",
  applied_at: null,
  next_action_at: null,
  next_action_note: "Preparar CV",
  notes: null,
  cv_document_id: null,
  created_at: "2026-11-17T00:00:00Z",
  updated_at: "2026-11-17T00:00:00Z",
};

const applicationWithOffer = { application, offer };

test.beforeEach(async ({ page }) => {
  await page.addInitScript((id) => {
    window.localStorage.setItem("practicv.profileId", id);
  }, profileId);
});

test("match, override and create application", async ({ page }) => {
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();

    if (method === "GET" && url.pathname === `/api/v1/offers/${offerId}`) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(offer) });
      return;
    }
    if (method === "POST" && url.pathname === "/api/v1/matches") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(match) });
      return;
    }
    if (method === "PATCH" && url.pathname === `/api/v1/matches/${match.id}`) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(overriddenMatch) });
      return;
    }
    if (method === "POST" && url.pathname === "/api/v1/applications") {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({ application, duplicate: false }),
      });
      return;
    }
    await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });

  await page.goto(`/ofertas/${offerId}`);
  await expect(page.getByTestId("offer-detail-title")).toHaveText("Practicante de Datos UI");

  await page.getByTestId("match-calculate").click();
  await expect(page.getByTestId("match-score")).toContainText("85");
  await expect(page.getByTestId("match-decision")).toHaveText("Aplicar con brechas");
  await expect(page.getByTestId("match-gap-0")).toContainText("Power BI");

  await page.getByTestId("match-override-decision").selectOption("apply");
  await page.getByTestId("match-override-save").click();
  await expect(page.getByTestId("match-status")).toContainText("Decisión actualizada");
  await expect(page.getByTestId("match-decision")).toHaveText("Aplicar");

  await page.getByTestId("create-application").click();
  await expect(page.getByTestId("match-status")).toContainText("Postulación creada");

  await page.screenshot({ path: "docs/assets/match.png", fullPage: true });
});

test("kanban move and reminder", async ({ page }) => {
  let currentApplication = application;

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();

    if (method === "GET" && url.pathname === "/api/v1/applications") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{ application: currentApplication, offer }]),
      });
      return;
    }
    if (method === "PATCH" && url.pathname === `/api/v1/applications/${applicationId}`) {
      currentApplication = { ...application, status: "interview", applied_at: "2026-11-17T00:00:00Z" };
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(currentApplication),
      });
      return;
    }
    if (method === "POST" && url.pathname === `/api/v1/applications/${applicationId}/reminders`) {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "reminder-1",
          application_id: applicationId,
          due_at: "2026-12-01T09:00:00Z",
          channel: "in_app",
          message: "Seguimiento",
          status: "pending",
        }),
      });
      return;
    }
    await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });

  await page.goto("/postulaciones");
  await expect(page.getByTestId("applications-title")).toHaveText("Postulaciones");
  await expect(page.getByTestId("kanban-column-saved")).toContainText("Practicante de Datos UI");

  await page.getByTestId("application-status-0").selectOption("interview");
  await expect(page.getByTestId("applications-status")).toContainText("Entrevista");
  await expect(page.getByTestId("kanban-column-interview")).toContainText("Practicante de Datos UI");

  await page.getByTestId("application-reminder-date-0").fill("2026-12-01");
  await page.getByTestId("application-reminder-add-0").click();
  await expect(page.getByTestId("applications-status")).toContainText("Recordatorio agregado");

  await expect(page.getByTestId("export-xlsx")).toHaveAttribute("href", /applications\.xlsx/);
  await expect(page.getByTestId("export-csv")).toHaveAttribute("href", /applications\.csv/);
  await expect(page.getByTestId("export-ics")).toHaveAttribute("href", /calendar\.ics/);

  await page.screenshot({ path: "docs/assets/kanban.png", fullPage: true });
});
