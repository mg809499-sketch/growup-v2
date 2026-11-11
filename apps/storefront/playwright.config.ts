import { defineConfig, devices } from "@playwright/test";

const STOREFRONT_URL = process.env.STOREFRONT_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: STOREFRONT_URL,
    trace: "on-first-retry",
    extraHTTPHeaders: {
      "x-storefront-host": process.env.STOREFRONT_HOST ?? "ropa.growup.com",
    },
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  // En CI el storefront corre contra staging; en local, contra `pnpm dev`.
  // No levantamos webServer aquí para no sorprender con puertos ocupados;
  // los comandos están documentados en el README.
});
