import test from 'node:test'
import assert from 'node:assert/strict'
import { getMatches } from './api.js'
import { sampleShots } from './data/mockShots.js'

test('uses mock match data by default while matches endpoint is unavailable', async () => {
  const matches = await getMatches()
  assert.equal(matches.length, 1)
  assert.equal(matches[0].match_id, 'M1')
  assert.deepEqual(matches[0].teams, ['Farmingdale State', 'Adelphi'])
  assert.equal(matches[0].shots.length, sampleShots.length)
})

test('returns independent mock shot objects', async () => {
  const matches = await getMatches()
  matches[0].shots[0].player = 'Changed'
  const again = await getMatches()
  assert.equal(again[0].shots[0].player, sampleShots[0].player)
})

test('can request the backend matches endpoint when it becomes available', async () => {
  const originalFetch = globalThis.fetch
  let calledUrl
  globalThis.fetch = async url => {
    calledUrl = url
    return { ok: true, json: async () => [{ match_id: 'M2' }] }
  }
  try {
    assert.deepEqual(await getMatches({ useMock: false }), [{ match_id: 'M2' }])
    assert.equal(calledUrl, 'http://localhost:8000/api/matches/')
  } finally {
    globalThis.fetch = originalFetch
  }
})
