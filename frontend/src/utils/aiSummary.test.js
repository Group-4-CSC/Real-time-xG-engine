import test from 'node:test'
import assert from 'node:assert/strict'
import { fallbackText, interpretAiResponse, loadAiSummary } from './aiSummary.js'
import { getAiMatchSummary } from '../api.js'

const stats = {
  match_id: 'M1',
  half: 'all',
  teams: [
    { name: 'Home', shots: 5, goals: 1, xg: 0.8, xg_calculated_shots: 4, xg_missing_shots: 1 },
    { name: 'Away', shots: 3, goals: 0, xg: null, xg_calculated_shots: 0, xg_missing_shots: 3 },
  ],
}

test('successful AI output is labeled AI-generated', async () => {
  const result = await loadAiSummary(stats, async payload => {
    assert.deepEqual(payload, stats)
    return { summary: 'Home recorded five shots. Away recorded three shots. xG coverage is incomplete.', is_placeholder: false }
  })
  assert.equal(result.mode, 'ai')
  assert.match(result.text, /coverage/)
})

test('explicit backend fallback must not be labeled AI-generated', async () => {
  const result = await loadAiSummary(stats, async () => ({ summary: 'Verified match statistics only.', is_fallback: true }))
  assert.equal(result.mode, 'fallback')
  assert.match(result.message, /provider/)
})

test('provider failure displays deterministic statistics with missing xG disclosed', async () => {
  const result = await loadAiSummary(stats, async () => { throw new Error('503') })
  assert.equal(result.mode, 'fallback')
  assert.match(result.text, /Home: 1 goal, 5 shots, 0.80 xG/)
  assert.match(result.text, /Away: 0 goals, 3 shots, xG unavailable/)
  assert.match(result.text, /Only 4 of 5 shots have xG/)
})

test('malformed or prototype success response is treated as fallback', async () => {
  for (const response of [{}, { summary: 23 }, { summary: '' }, { summary: 'Old prototype', is_placeholder: true }]) {
    const result = await loadAiSummary(stats, async () => response)
    assert.equal(result.mode, 'fallback')
    assert.match(result.message, /invalid output/)
  }
  assert.throws(() => interpretAiResponse(null), /valid summary/)
})

test('abort propagates without showing fallback from a stale request', async () => {
  const controller = new AbortController()
  controller.abort()
  await assert.rejects(
    loadAiSummary(stats, async () => { throw new Error('aborted') }, controller.signal),
    /aborted/
  )
})

test('AI API client sends exact JSON POST to Django, with abort signal', async () => {
  const originalFetch = globalThis.fetch
  const controller = new AbortController()
  let request
  globalThis.fetch = async (url, options) => {
    request = { url, options }
    return { ok: true, json: async () => ({ summary: 'Test summary', is_placeholder: false }) }
  }
  try {
    assert.equal((await getAiMatchSummary(stats, { signal: controller.signal })).summary, 'Test summary')
    assert.equal(request.url, 'http://localhost:8000/api/ai/match-summary/')
    assert.equal(request.options.method, 'POST')
    assert.equal(request.options.signal, controller.signal)
    assert.deepEqual(JSON.parse(request.options.body), stats)
    assert.equal(request.options.headers['Content-Type'], 'application/json')
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('fallback text does not invent match statistics when input is unusable', () => {
  assert.equal(fallbackText(null), 'The match statistics are unavailable right now.')
})
