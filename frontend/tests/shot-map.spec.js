
import { test, expect } from '@playwright/test'

test('Shot Map filters and Reset button work', async ({ page }) => {
  // Open the website
  await page.goto('http://localhost:5173/')

  // Enter the demo workspace
await page.getByRole('button', {
  name: /Explore the demo workspace/
}).click()

// Open the Shot Map
await page.getByText('Shot Map', { exact: true }).first().click()

  // Confirm the Shot Type filter exists
  const shotType = page.getByLabel('Shot Type')
  await expect(shotType).toBeVisible()

  // Record the original shot count
  const count = page.getByRole('heading', {
    name: /Shots in view/
  })
  const originalCount = await count.textContent()

  // Choose a shot type
  const options = await shotType.locator('option').allTextContents()
  expect(options.length).toBeGreaterThan(1)

  await shotType.selectOption({ index: 1 })

  // Confirm the selected filter is active
  await expect(shotType).not.toHaveValue('all')

  // Reset the filters
  await page.getByRole('button', { name: 'Reset' }).click()

  // Confirm everything returns to normal
  await expect(shotType).toHaveValue('all')
  await expect(count).toHaveText(originalCount)
})
