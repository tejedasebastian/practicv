import { expect, test } from "@playwright/test";

const job = {
  "@context": "https://schema.org",
  "@type": "JobPosting",
  title: "Practicante de Datos Bookmarklet",
  description: "<p>Buscamos practicante con SQL y Power BI.</p>",
  hiringOrganization: { "@type": "Organization", name: "Bookmarklet Corp" },
  jobLocation: {
    "@type": "Place",
    address: { "@type": "PostalAddress", addressLocality: "Lima" },
  },
  employmentType: "Hibrido",
  datePosted: "2026-11-01",
  validThrough: "2026-12-20",
  baseSalary: {
    "@type": "MonetaryAmount",
    currency: "PEN",
    value: { "@type": "QuantitativeValue", value: 1500 },
  },
};

const preview = {
  title: "Practicante de Datos Bookmarklet",
  company: "Bookmarklet Corp",
  source_url: "https://example.com/ofertas/datos",
  location: "Lima",
  modality: "Hibrido",
  salary_text: null,
  salary_amount: 1500,
  salary_currency: "PEN",
  description: "Buscamos practicante con SQL y Power BI.",
  requirements_text: "Buscamos practicante con SQL y Power BI.",
  published_at: "2026-11-01T00:00:00Z",
  deadline_at: "2026-12-20T00:00:00Z",
  confidence: 0.9,
  warnings: [],
};

const fixtureHtml = `<!doctype html>
<html>
  <head>
    <title>Oferta de prueba</title>
    <script type="application/ld+json">${JSON.stringify(job)}</script>
  </head>
  <body><h1>Practicante de Datos Bookmarklet</h1><p>Texto visible de la oferta.</p></body>
</html>`;

test("bookmarklet captures a JobPosting and confirms it", async ({ page, context }) => {
  await page.addInitScript(() => window.localStorage.setItem("practicv.locale", "es"));

  await context.route("https://jobs.example.com/offer", async (route) => {
    await route.fulfill({ status: 200, contentType: "text/html", body: fixtureHtml });
  });

  let previewBody: Record<string, unknown> | null = null;
  let createBody: Record<string, unknown> | null = null;

  await context.route("**/api/v1/offers/bookmarklet/preview", async (route) => {
    previewBody = route.request().postDataJSON() as Record<string, unknown>;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(preview),
    });
  });
  await context.route("**/api/v1/offers/bookmarklet", async (route) => {
    createBody = route.request().postDataJSON() as Record<string, unknown>;
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        offer: {
          id: "offer-bookmarklet",
          source_type: "bookmarklet",
          title: preview.title,
          company: preview.company,
        },
        duplicate: false,
      }),
    });
  });

  await page.goto("/bookmarklet");
  const link = page.getByTestId("bookmarklet-link");
  await expect(link).toHaveAttribute("href", /^javascript:/);
  const href = await link.getAttribute("href");
  expect(href).toBeTruthy();

  await page.goto("https://jobs.example.com/offer");
  const popupPromise = page.waitForEvent("popup");
  await page.evaluate((source) => {
    (0, eval)(source);
  }, href!.replace(/^javascript:/, ""));
  const popup = await popupPromise;

  await expect(popup).toHaveURL(/\/captura#/);
  await expect(popup.getByTestId("capture-title")).toHaveValue(
    "Practicante de Datos Bookmarklet",
  );
  await expect(popup.getByTestId("capture-company")).toHaveValue("Bookmarklet Corp");
  await expect(popup.getByTestId("capture-warnings")).toHaveCount(0);

  await popup.getByTestId("capture-save").click();
  await expect(popup.getByTestId("capture-status")).toContainText("Oferta guardada");

  expect(previewBody?.url).toBe("https://jobs.example.com/offer");
  expect((previewBody?.jsonld as string[]).join(" ")).toContain("JobPosting");
  expect(createBody?.title).toBe("Practicante de Datos Bookmarklet");
  expect(createBody?.company).toBe("Bookmarklet Corp");
  expect(createBody?.source_url).toBe("https://example.com/ofertas/datos");
});
