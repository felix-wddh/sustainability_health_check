import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'e2e',
  webServer: {
    command: 'npm run preview -- --port 5174',
    port: 5174,
    reuseExistingServer: !process.env.CI
  },
  use: { baseURL: 'http://localhost:5174' }
});

