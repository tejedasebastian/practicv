import { expect, test } from "@playwright/test";

const candidate = {
  url: "https://example.com/ofertas/datos-gmail",
  title: "Practicante de Datos desde Gmail",
  source: "html",
};

test("gmail connection, search, preview and import", async ({ page, context }) => {
  await page.addInitScript(() => window.localStorage.setItem("practicv.locale", "es"));

  await context.route("**/api/v1/email/google/status", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        configured: true,
        connected: true,
        email: "demo@example.com",
        detail: "Google account connected.",
      }),
    });
  });
  await context.route("**/api/v1/email/google/messages**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        messages: [
          {
            id: "m1",
            subject: "Alertas de la semana",
            sender: "alertas@example.com",
            date: "Mon, 23 Nov 2026 10:00:00 +0000",
            snippet: "Oferta de datos",
          },
        ],
        warnings: [],
      }),
    });
  });
  await context.route("**/api/v1/email/google/preview", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        subject: "Alertas de la semana",
        candidates: [candidate],
        warnings: [],
      }),
    });
  });
  await context.route("**/api/v1/email/google/import", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        created: 1,
        duplicates: 0,
        errors: [],
        warnings: [],
        total_rows: 1,
        preview: [
          {
            title: candidate.title,
            company: "Gmail Corp",
            salary_amount: 1500,
            source_url: candidate.url,
            duplicate: false,
          },
        ],
        offer_ids: ["offer-gmail"],
      }),
    });
  });
  await context.route("**/api/v1/offers/sources/status", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ mcp: "unavailable", detail: null, filters: null }),
    });
  });
  await context.route("**/api/v1/offers/sources/practilizate/status", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ enabled: false, detail: "" }),
    });
  });
  await context.route("**/api/v1/offers", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });

  await page.goto("/ofertas");
  await page.getByTestId("offers-tab-email").click();
  await expect(page.getByTestId("gmail-panel")).toContainText("Gmail conectado");

  await page.getByTestId("gmail-search").click();
  await expect(page.getByTestId("gmail-message-m1")).toContainText("Alertas de la semana");
  await page.getByTestId("gmail-message-m1").click();

  await expect(page.getByTestId("email-candidate-0")).toContainText(candidate.title);
  await page.getByTestId("email-import").click();
  await expect(page.getByTestId("offers-status")).toContainText("Oferta creada");
  await expect(page.getByTestId("import-summary")).toContainText("Gmail Corp");
});
