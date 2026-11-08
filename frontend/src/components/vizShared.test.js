import test from 'node:test'
import assert from 'node:assert/strict'
import { coverageText, periodMatches, statsFor, teamColors, xgCellText, xgScopeLabel, xgStatus } from './vizShared.js'

test('US-2.2: supported team xG totals disclose unsupported shots', () => {
  const stats = statsFor([
    { outcome: 'goal', xg: 0.3 },
    { outcome: 'saved', xg: 0.2 },
    { outcome: 'goal', xg: null, xg_status: 'unsupported' },
  ])
  assert.equal(stats.xg, 0.5)
  assert.equal(stats.goals, 2)
  assert.equal(stats.goalsCalc, 1)
  assert.equal(xgScopeLabel(stats), 'supported shots only')
  assert.equal(coverageText(stats), 'xG from 2 of 3 shots (1 outside the model)')
})

test('XG-1 display: unsupported and pending are distinct from a numeric zero', () => {
  assert.equal(xgCellText({ xg: null, xg_status: 'unsupported' }), '–')
  assert.equal(xgCellText({ xg: null }), 'pending')
  assert.equal(xgCellText({ xg: 0, xg_status: 'computed' }), '0.00')
  assert.equal(xgStatus({ xg: 0.3, xg_status: 'computed' }), 'calculated')
  assert.equal(statsFor([{ xg: null, xg_status: 'unsupported' }]).xg, null)
})

test('US-6.2 helper: half selection includes requested periods only', () => {
  const shots = [{ period: 1 }, { period: 2 }, { period: 3 }, { period: 4 }]
  assert.deepEqual(shots.filter(s => periodMatches(s.period, '1')), [{ period: 1 }])
  assert.deepEqual(shots.filter(s => periodMatches(s.period, 'et')), [{ period: 3 }, { period: 4 }])
  assert.equal(shots.filter(s => periodMatches(s.period, 'all')).length, 4)
})

test('US-6.1 helper: home-team color is stable across shot ordering', () => {
  const first = teamColors([{ team: 'Away' }, { team: 'Home' }], 'Home')
  const reversed = teamColors([{ team: 'Home' }, { team: 'Away' }], 'Home')
  assert.deepEqual(first, reversed)
  assert.notEqual(first.Home, first.Away)
})
