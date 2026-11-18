import { expect, test } from "@playwright/test";

const manualOffer = {
  id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  source_type: "manual",
  external_id: null,
  source_url: "https://example.com/offers/manual-ui",
  captured_at: "2026-11-17T00:00:00Z",
  title: "Practicante Manual UI",
  company: "UI Corp",
  location: "Lima",
  modality: "Híbrido",
  salary_text: "S/ 1,200",
  salary_amount: 1200,
  salary_currency: "PEN",
  description: "Oferta manual",
  requirements_text: "Python, SQL",
  published_at: null,
  deadline_at: null,
  parse_confidence: null,
  dedupe_hash: "hash-manual",
};

const mcpOffers = [
  {
    ...manualOffer,
    id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    source_type: "mcp_practicas_pe",
    source_url: "https://www.practicas.pe/oferta-convocatoria-9001.html",
    title: "Practicante de Datos MCP",
    company: "MCP Corp",
  },
  {
    ...manualOffer,
    id: "cccccccc-cccc-cccc-cccc-cccccccccccc",
    source_type: "mcp_practicas_pe",
    source_url: "https://www.practicas.pe/oferta-convocatoria-9002.html",
    title: "Practicante de BI MCP",
    company: "MCP BI",
  },
];

test("manual offer and MCP search/import flow", async ({ page }) => {
  let offers: typeof manualOffer[] = [];

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();

    if (method === "GET" && url.pathname === "/api/v1/offers/sources/status") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          mcp: "available",
          detail: null,
          filters: { carreras: [{ id: "18", nombre: "Ingeniería de Sistemas" }] },
        }),
      });
      return;
    }
    if (method === "GET" && url.pathname === "/api/v1/offers") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(offers),
      });
      return;
    }
    if (method === "POST" && url.pathname === "/api/v1/offers/manual") {
      offers = [manualOffer, ...offers];
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({ offer: manualOffer, duplicate: false }),
      });
      return;
    }
    if (method === "POST" && url.pathname === "/api/v1/offers/mcp/search") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          results: [
            {
              titulo: "Practicante de Datos MCP",
              empresa: "MCP Corp",
              ubicacion: "Lima",
              subvencion: "S/ 1,300",
              modalidad: "Híbrido",
              url: mcpOffers[0].source_url,
            },
            {
              titulo: "Practicante de BI MCP",
              empresa: "MCP BI",
              ubicacion: "Lima",
              subvencion: "S/ 1,500",
              modalidad: "Presencial",
              url: mcpOffers[1].source_url,
            },
          ],
          total: 2,
          warning: null,
        }),
      });
      return;
    }
    if (method === "POST" && url.pathname === "/api/v1/offers/mcp/import") {
      offers = [...mcpOffers, ...offers];
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          created: 2,
          duplicates: 0,
          errors: [],
          warnings: [],
          total_rows: 2,
          preview: [],
          offer_ids: mcpOffers.map((offer) => offer.id),
        }),
      });
      return;
    }
    await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });

  await page.goto("/ofertas");
  await expect(page.getByTestId("offers-title")).toBeVisible();

  await page.getByTestId("offer-title").fill("Practicante Manual UI");
  await page.getByTestId("offer-company").fill("UI Corp");
  await page.getByTestId("offer-url").fill("https://example.com/offers/manual-ui");
  await page.getByTestId("offer-save").click();

  await expect(page.getByTestId("offers-status")).toContainText("Oferta creada");
  await expect(page.getByTestId("offers-list")).toContainText("Practicante Manual UI");

  await page.getByTestId("offers-tab-mcp").click();
  await page.getByTestId("mcp-query").fill("datos");
  await page.getByTestId("mcp-search").click();

  await expect(page.getByTestId("mcp-result-0")).toContainText("MCP Corp");
  await expect(page.getByTestId("mcp-result-1")).toContainText("MCP BI");

  await page.getByTestId("mcp-import").click();
  await expect(page.getByTestId("import-summary")).toContainText("Creadas: 2");
  await expect(page.getByTestId("offers-list")).toContainText("Practicante de Datos MCP");
});
