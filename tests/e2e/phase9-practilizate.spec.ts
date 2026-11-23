import { expect, test } from "@playwright/test";

test("practilizate adapter imports its CSV", async ({ page, context }) => {
  await page.addInitScript(() => window.localStorage.setItem("practicv.locale", "es"));

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
      body: JSON.stringify({ enabled: true, detail: "Practilizate adapter is enabled." }),
    });
  });
  await context.route("**/api/v1/offers/import/practilizate", async (route) => {
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
            title: "Practicante Practilizate",
            company: "Practilizate Corp",
            salary_amount: 1300,
            source_url: "https://example.com/practilizate/1",
            duplicate: false,
          },
        ],
        offer_ids: ["offer-practilizate"],
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
  await page.getByTestId("offers-tab-practilizate").click();
  await expect(page.getByTestId("practilizate-status")).toContainText("Adaptador habilitado");

  await page.getByTestId("practilizate-file").setInputFiles({
    name: "dashboard_dataset.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      "title,company,url\nPracticante Practilizate,Practilizate Corp,https://example.com/practilizate/1\n",
    ),
  });
  await page.getByTestId("practilizate-import").click();

  await expect(page.getByTestId("offers-status")).toContainText("Oferta creada");
  await expect(page.getByTestId("import-summary")).toContainText("Practilizate Corp");
});
