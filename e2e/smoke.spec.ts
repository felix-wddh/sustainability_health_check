import { test, expect } from '@playwright/test';

test('end-to-end dummy flow and CSV', async ({ page }) => {
  await page.goto('/');
  // Step 1: Dummy Data
  await page.getByRole('button', { name: 'Use Dummy Data' }).click();
  await expect(page.getByRole('button', { name: /Completeness/i })).toBeEnabled();

  // Move to Step 2
  await page.getByRole('button', { name: /Completeness/ }).click();
  await page.getByRole('button', { name: /Apply Mapping/ }).click();

  // Step 3
  await page.getByRole('button', { name: /KPI Computation/ }).click();
  await page.getByRole('button', { name: /Compute KPIs/ }).click();

  // Step 4
  await page.getByRole('button', { name: /Expert Review/ }).click();
  await page.getByRole('button', { name: /Lock Baseline/ }).click();

  // Step 5
  await page.getByRole('button', { name: /One-Click PPT Export/ }).click();
  await expect(page.getByRole('button', { name: 'Download CSV' })).toBeEnabled();
});

