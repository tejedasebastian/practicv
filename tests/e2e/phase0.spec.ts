import { expect, test } from "@playwright/test";

test("PractiCV landing loads and toggles ES/EN", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByTestId("app-title")).toHaveText("PractiCV");
  await expect(page.getByTestId("hero-subtitle")).toContainText("Convierte cualquier oferta");
  await expect(page.getByTestId("phase-label")).toContainText("Fase 0");

  await page.getByTestId("lang-en").click();
  await expect(page.getByTestId("hero-subtitle")).toContainText("Turn any internship");
  await expect(page.getByTestId("phase-label")).toContainText("Phase 0");

  await page.getByTestId("lang-es").click();
  await expect(page.getByTestId("hero-subtitle")).toContainText("Convierte cualquier oferta");
});
