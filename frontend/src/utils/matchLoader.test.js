import test from 'node:test'
import assert from 'node:assert/strict'
import { loadMatchShots } from './matchLoader.js'
import { sampleShots } from '../data/mockShots.js'
import { dashboardMetrics } from './dashboardMetrics.js'

const wrappedMatches = [{ match_id: 'M1', shots: sampleShots }]

test('frontend: demo mode uses mock matches without needing a backend', async () => {
  const result = await loadMatchShots({
    fetchMatches: async ({ useMock }) => {
      assert.equal(useMock, true)
      return wrappedMatches
    },
  })
  assert.equal(result.source, 'demo')
  assert.equal(result.error, '')
  assert.equal(result.shots.length, sampleShots.length)
})

test('frontend: live mode uses API records and feeds dashboard statistics', async () => {
  const shots = [{ ...sampleShots[0], match_id: 'SERVER-10', xg: 0.65 }]
  const result = await loadMatchShots({
    useLiveMatches: true,
    fetchMatches: async ({ useMock }) => {
      assert.equal(useMock, false)
      return [{ match_id: 'SERVER-10', shots }]
    },
  })
  assert.equal(result.source, 'api')
  assert.equal(result.error, '')
  assert.equal(result.shots[0].match_id, 'SERVER-10')
  const totals = dashboardMetrics(result.shots, 'Farmingdale State')
  assert.equal(totals.homeStats.shots, 1)
  assert.equal(totals.homeStats.goals, 1)
  assert.equal(totals.homeStats.xg, 0.65)
})

test('frontend: unavailable API displays an error and uses honest sample-data fallback', async () => {
  const result = await loadMatchShots({
    useLiveMatches: true,
    fetchMatches: async () => { throw new Error('API request failed (404)') },
  })
  assert.equal(result.source, 'demo')
  assert.match(result.error, /404/)
  assert.match(result.error, /Showing sample data/)
  assert.equal(result.shots.length, sampleShots.length)
})

test('frontend: invalid server response triggers fallback rather than breaking screens', async () => {
  const result = await loadMatchShots({
    useLiveMatches: true,
    fetchMatches: async () => ({ unknown: true }),
  })
  assert.equal(result.source, 'demo')
  assert.match(result.error, /array of matches/)
  assert.equal(result.shots.length, sampleShots.length)
})

test('frontend: empty valid API matches response remains empty, not disguised as demo', async () => {
  const result = await loadMatchShots({
    useLiveMatches: true,
    fetchMatches: async () => [],
  })
  assert.equal(result.source, 'api')
  assert.equal(result.error, '')
  assert.deepEqual(result.shots, [])
})
