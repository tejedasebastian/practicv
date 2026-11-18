import { expect, test } from "@playwright/test";

test.use({ video: { mode: "on", size: { width: 1280, height: 720 } } });

const profileId = "profile-1";
const offerId = "offer-1";

const offer = {
  id: offerId,
  source_type: "manual",
  external_id: null,
  source_url: "https://example.com/offer-1",
  captured_at: "2026-11-17T00:00:00Z",
  title: "Practicante de Datos",
  company: "Demo Data Corp",
  location: "Lima",
  modality: "Híbrido",
  salary_text: "S/ 1,500",
  salary_amount: 1500,
  salary_currency: "PEN",
  description: "Oferta de datos para la demo.",
  requirements_text: "SQL, Power BI",
  published_at: null,
  deadline_at: "2026-12-31T00:00:00Z",
  parse_confidence: 0.95,
  dedupe_hash: "demo-offer",
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
  explanation_json: [],
  overridden: false,
  override_reason: null,
  created_at: "2026-11-17T00:00:00Z",
};

const application = {
  id: "application-1",
  profile_id: profileId,
  offer_id: offerId,
  status: "applied",
  applied_at: "2026-11-17T00:00:00Z",
  next_action_at: "2026-12-15T00:00:00Z",
  next_action_note: "Preparar entrevista.",
  notes: "Demo.",
  cv_document_id: null,
  created_at: "2026-11-17T00:00:00Z",
  updated_at: "2026-11-17T00:00:00Z",
};

const profile = {
  id: profileId,
  full_name: "Estudiante Demo",
  email: "demo@practicv.local",
  phone: null,
  university: "UNMSM",
  career: "Ingeniería de Software",
  cycle: 8,
  location: "Lima",
  target_roles: ["Data Analyst"],
  preferred_modality: "Híbrido",
  salary_expectation: 1200,
  availability: "Lunes a viernes",
  locale: "es",
  created_at: "2026-11-17T00:00:00Z",
  updated_at: "2026-11-17T00:00:00Z",
};

test("demo walkthrough", async ({ page }) => {
  await page.addInitScript((id) => {
    window.localStorage.setItem("practicv.profileId", id);
    window.localStorage.setItem("practicv.locale", "es");
  }, profileId);

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();

    if (method === "GET" && url.pathname === "/api/v1/offers") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([offer]) });
      return;
    }
    if (method === "GET" && url.pathname === "/api/v1/offers/sources/status") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ mcp: "available", detail: null, filters: null }),
      });
      return;
    }
    if (method === "GET" && url.pathname === `/api/v1/offers/${offerId}`) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(offer) });
      return;
    }
    if (method === "POST" && url.pathname === "/api/v1/matches") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(match) });
      return;
    }
    if (method === "GET" && url.pathname === `/api/v1/profiles/${profileId}`) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(profile) });
      return;
    }
    if (method === "GET" && url.pathname === "/api/v1/applications") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{ application, offer, match }]),
      });
      return;
    }
    await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });

  await page.goto("/");
  await expect(page.getByTestId("app-title")).toHaveText("PractiCV");
  await page.waitForTimeout(2000);

  await page.goto("/perfil");
  await expect(page.getByRole("heading", { name: "Tu perfil" })).toBeVisible();
  await page.waitForTimeout(2000);

  await page.goto("/ofertas");
  await expect(page.getByTestId("offers-title")).toBeVisible();
  await page.waitForTimeout(2500);

  await page.goto(`/ofertas/${offerId}`);
  await page.getByTestId("match-calculate").click();
  await expect(page.getByTestId("match-score")).toContainText("85");
  await page.waitForTimeout(2500);

  await page.goto("/postulaciones");
  await expect(page.getByTestId("applications-title")).toBeVisible();
  await page.waitForTimeout(3000);
});
