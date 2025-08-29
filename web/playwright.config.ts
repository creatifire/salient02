import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  retries: 0,
  outputDir: '../.playwright-results',
  use: {
    baseURL: process.env.WEB_ORIGIN || 'http://localhost:4321',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'PUBLIC_ENABLE_STANDALONE_CHAT=true pnpm dev',
    url: process.env.WEB_ORIGIN || 'http://localhost:4321',
    reuseExistingServer: true,
    timeout: 60_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});


