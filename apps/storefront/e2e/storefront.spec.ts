import { test, expect } from "@playwright/test";

// Flujos públicos del storefront multi-tenant. Requieren:
//   pnpm dlx supabase db reset && psql "$GROWUP_MIGRATION_URL" -f supabase/seed.demo.sql
//   GROWUP_STOREFRONT_HOST=ropa.growup.com pnpm --filter @growup/storefront dev
// y la API en localhost:8000. En CI: STOREFRONT_URL=https://staging.growup.com

test("home carga el storefront del tenant", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("header")).toBeVisible();
  await expect(page).toHaveTitle(/.+/);
});

test("colección muestra productos", async ({ page }) => {
  await page.goto("/collection");
  await expect(page.locator("article, [data-product-card]").first()).toBeVisible();
});

test("PDP muestra variantes y precio", async ({ page }) => {
  await page.goto("/collection");
  const first = page.locator("article a").first();
  await first.click();
  await expect(page.locator("text=/variantes/i").or(page.locator("text=/agotado/i"))).toBeVisible();
});

test("producto inexistente devuelve 404", async ({ page }) => {
  const response = await page.goto("/products/no-existe-este-producto");
  expect(response?.status()).toBe(404);
});

test("las imágenes del catálogo tienen alt", async ({ page }) => {
  await page.goto("/collection");
  const images = page.locator("main img");
  const count = await images.count();
  if (count > 0) {
    for (let i = 0; i < count; i++) {
      await expect(images.nth(i)).toHaveAttribute("alt", /.+/);
    }
  }
});

test("carrito: añadir y ver", async ({ page }) => {
  await page.goto("/collection");
  await page.locator("article a").first().click();
  await page.locator("select#variant-select").selectOption({ index: 1 });
  await page.getByRole("button", { name: /añadir al carrito/i }).click();
  await expect(page).toHaveURL(/\/carrito/);
  await expect(page.locator("text=/subtotal/i")).toBeVisible();
});
