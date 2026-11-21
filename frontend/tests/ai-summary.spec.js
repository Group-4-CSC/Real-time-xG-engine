import { test, expect } from '@playwright/test'

// Run against a local Vite dev server at http://localhost:5173.
// All AI requests are intercepted: no API key or real provider needed.
async function openSummary(page) {
  await page.goto('http://localhost:5173/')
  await page.getByRole('button', { name: /Explore the demo workspace/ }).click()
  await page.getByRole('button', { name: 'Match Summary' }).click()
}

test('AI summary: successful backend response is clearly labeled', async ({ page }, testInfo) => {
  await page.route('**/api/ai/match-summary/', async route => {
    const payload = route.request().postDataJSON()
    expect(route.request().method()).toBe('POST')
    expect(payload.match_id).toBe('M1')
    expect(payload.half).toBe('all')
    expect(payload.teams).toHaveLength(2)
    expect(payload.teams.every(team => team.shots === team.xg_calculated_shots + team.xg_missing_shots)).toBe(true)
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        summary: 'Farmingdale State had four chances. Adelphi also created chances. Both teams registered xG.',
        is_placeholder: false,
      }),
    })
  })
  await openSummary(page)
  await expect(page.getByLabel('AI Match Summary').getByText('AI-generated', { exact: true })).toBeVisible()
  await expect(page.getByLabel('AI Match Summary').getByText(/Farmingdale State had four chances/)).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('ai-summary-success.png'), fullPage: true })
})

test('AI summary: backend 503 shows verified stats fallback and a retry', async ({ page }, testInfo) => {
  let attempts = 0
  await page.route('**/api/ai/match-summary/', async route => {
    attempts += 1
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'AI summary is temporarily unavailable.' }),
    })
  })
  await openSummary(page)
  const card = page.getByLabel('AI Match Summary')
  await expect(card.getByText('Fallback — match stats only', { exact: true })).toBeVisible()
  await expect(card.getByText(/AI analysis is unavailable/)).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('ai-summary-fallback.png'), fullPage: true })
  await card.getByRole('button', { name: 'Retry summary' }).click()
  await expect(card.getByText('Fallback — match stats only', { exact: true })).toBeVisible()
  expect(attempts).toBeGreaterThanOrEqual(2)
})

test('AI summary: malformed backend output is not mislabeled as AI-generated', async ({ page }) => {
  await page.route('**/api/ai/match-summary/', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ summary: '', is_placeholder: false }),
  }))
  await openSummary(page)
  const card = page.getByLabel('AI Match Summary')
  await expect(card.getByText('Fallback — match stats only', { exact: true })).toBeVisible()
  await expect(card.getByText(/invalid output/)).toBeVisible()
})
