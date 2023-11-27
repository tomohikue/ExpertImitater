import { test, expect } from '@playwright/test';

test('Mobile Safari', async ({ page }) => {
  // ブラウザが起動した時に表示されるページ
  await page.goto('http://127.0.0.1:8000/');

  await page.pause();
});