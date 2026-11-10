import test from 'node:test'
import assert from 'node:assert/strict'
import { dashboardMetrics } from './dashboardMetrics.js'
import { xgText } from '../components/vizShared.js'

const shots = [
  { id: '1', match_id: 'M1', team: 'Home', player: 'Alex', outcome: 'goal', xg: 0.4 },
  { id: '2', match_id: 'M1', team: 'Home', player: 'Alex', outcome: 'saved', xg: 0.1 },
  { id: '3', match_id: 'M2', team: 'Home', player: 'Sam', outcome: 'saved', xg: null, xg_status: 'unsupported' },
  { id: '4', match_id: 'M2', team: 'Away', player: 'Chris', outcome: 'goal', xg: 0.3 },
  { id: '5', match_id: 'M2', team: 'Away', player: 'Chris', outcome: 'saved', xg: null },
]

test('Coach Dashboard: selected team shows correct matches, shots, goals and xG', () => {
  const dashboard = dashboardMetrics(shots, 'Home')
  assert.equal(dashboard.matches, 2)
  assert.equal(dashboard.homeStats.shots, 3)
  assert.equal(dashboard.homeStats.goals, 1)
  assert.equal(dashboard.homeStats.xg, 0.5)
  assert.equal(xgText(dashboard.homeStats), '0.50')
  assert.equal(dashboard.homeStats.unsupported, 1)
  assert.equal(dashboard.awayStats.shots, 2)
  assert.equal(dashboard.awayStats.goals, 1)
  assert.equal(dashboard.awayStats.xg, 0.3)
})

test('Coach Dashboard: team selection changes the comparison and player table', () => {
  const dashboard = dashboardMetrics(shots, 'Away')
  assert.equal(dashboard.homeStats.shots, 2)
  assert.equal(dashboard.homeStats.goals, 1)
  assert.equal(dashboard.awayStats.shots, 3)
  assert.deepEqual(dashboard.playerStats.map(p => p.name), ['Chris'])
  assert.equal(dashboard.playerStats[0].shots, 2)
  assert.equal(dashboard.playerStats[0].xg, 0.3)
})

test('Coach Dashboard: player statistics count unsupported shots without adding missing xG', () => {
  const dashboard = dashboardMetrics(shots, 'Home')
  const alex = dashboard.playerStats.find(p => p.name === 'Alex')
  const sam = dashboard.playerStats.find(p => p.name === 'Sam')
  assert.equal(alex.goals, 1)
  assert.equal(alex.shots, 2)
  assert.equal(alex.xg, 0.5)
  assert.equal(sam.shots, 1)
  assert.equal(sam.unsupported, 1)
  assert.equal(sam.xg, null)
  assert.equal(xgText(sam), 'No xG')
})

test('Coach Dashboard: pending predictions are not presented as zero xG', () => {
  const dashboard = dashboardMetrics([
    { match_id: 'M3', team: 'Home', player: 'Jamie', outcome: 'saved', xg: null },
  ], 'Home')
  assert.equal(dashboard.homeStats.pending, 1)
  assert.equal(dashboard.homeStats.xg, null)
  assert.equal(xgText(dashboard.homeStats), 'xG pending')
})
