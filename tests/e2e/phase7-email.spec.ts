import { expect, test } from "@playwright/test";

const candidate = {
  url: "https://example.com/ofertas/datos-email",
  title: "Practicante de Datos desde Correo",
  source: "html",
};

test("email alert preview and import", async ({ page, context }) => {
  await page.addInitScript(() => window.localStorage.setItem("practicv.locale", "es"));

  await context.route("**/api/v1/offers/sources/status", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ mcp: "unavailable", detail: null, filters: null }),
    });
  });
  await context.route("**/api/v1/offers/import/email/preview", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        subject: "Ofertas de la semana",
        candidates: [candidate],
        warnings: [],
      }),
    });
  });
  await context.route("**/api/v1/offers/import/email", async (route) => {
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
            company: "Correo Corp",
            salary_amount: 1400,
            source_url: candidate.url,
            duplicate: false,
          },
        ],
        offer_ids: ["offer-email"],
      }),
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
  await page.getByTestId("offer-email").setInputFiles({
    name: "alerta.eml",
    mimeType: "message/rfc822",
    buffer: Buffer.from("Subject: Ofertas de la semana\n\nNuevas ofertas."),
  });
  await page.getByTestId("email-preview").click();

  await expect(page.getByText("Ofertas de la semana")).toBeVisible();
  await expect(page.getByTestId("email-candidate-0")).toContainText(candidate.title);
  await page.getByTestId("email-import").click();

  await expect(page.getByTestId("offers-status")).toContainText("Oferta creada");
  await expect(page.getByTestId("import-summary")).toContainText("Correo Corp");
});
