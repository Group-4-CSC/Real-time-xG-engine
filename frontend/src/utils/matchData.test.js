import test from 'node:test'
import assert from 'node:assert/strict'
import { shotsFromMatches } from './matchData.js'
import { sampleShots } from '../data/mockShots.js'

test('match API: transforms grouped matches into shots shared by all frontend views', () => {
  const result = shotsFromMatches([{ match_id: 'M1', shots: sampleShots }])
  assert.equal(result.length, sampleShots.length)
  assert.equal(result[0].team, 'Farmingdale State')
  assert.equal(result[0].xg, 0.31)
  assert.equal(result[0].match_id, 'M1')
})

test('match API: supports wrapped payload and shot IDs from backend', () => {
  const first = { ...sampleShots[0], id: undefined, shot_id: 'ABC', match_id: undefined }
  const result = shotsFromMatches({ matches: [{ id: 'M2', shots: [first] }] })
  assert.equal(result[0].id, 'ABC')
  assert.equal(result[0].match_id, 'M2')
})

test('match API: preserves missing xG as pending rather than zero', () => {
  const shot = { ...sampleShots[0], xg: null, xg_status: undefined }
  const result = shotsFromMatches([{ match_id: 'M1', shots: [shot] }])
  assert.equal(result[0].xg, null)
  assert.equal(result[0].xg_status, 'pending')
})

test('match API: rejects invalid response and incomplete shot records', () => {
  assert.throws(() => shotsFromMatches({ wrong: [] }), /array of matches/)
  assert.throws(() => shotsFromMatches([{ match_id: 'M1' }]), /shots array/)
  assert.throws(() => shotsFromMatches([{ match_id: 'M1', shots: [{ ...sampleShots[0], team: '' }] }]), /missing team/)
  assert.throws(() => shotsFromMatches([{ match_id: 'M1', shots: [{ ...sampleShots[0], xg: 2 }] }]), /invalid xG/)
})

test('match API: handles multiple matches and empty datasets', () => {
  const result = shotsFromMatches([
    { match_id: 'M1', shots: [sampleShots[0]] },
    { match_id: 'M2', shots: [sampleShots[1]] },
  ])
  assert.deepEqual(result.map(s => s.match_id), ['M1', 'M2'])
  assert.deepEqual(shotsFromMatches([]), [])
})
