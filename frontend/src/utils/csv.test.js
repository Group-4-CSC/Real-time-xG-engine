import test from 'node:test'
import assert from 'node:assert/strict'
import { parseCsv, parseCsvWithErrors } from './csv.js'

const headers = 'id,match_id,player,team,minute,period,x,y,outcome,body_part,assist_type'
const row = (overrides = {}) => {
  const shot = {
    id: 'S1', match_id: 'M1', player: 'J. Rivera', team: 'Farmingdale State',
    minute: '12', period: '1', x: '88', y: '48', outcome: 'goal',
    body_part: 'right_foot', assist_type: 'pass', ...overrides,
  }
  return Object.values(shot).join(',')
}

test('CSV Upload: valid CSV previews each shot with typed coordinates and optional xG', () => {
  const csv = headers + ',xg\n' + row() + ',0.31\n' +
    row({ id: 'S2', player: 'M. Chen', outcome: 'saved' }) + ','
  const shots = parseCsv(csv)
  assert.equal(shots.length, 2)
  assert.equal(shots[0].player, 'J. Rivera')
  assert.equal(shots[0].x, 88)
  assert.equal(shots[0].y, 48)
  assert.equal(shots[0].minute, 12)
  assert.equal(shots[0].xg, 0.31)
  assert.equal(shots[0].xg_status, 'calculated')
  assert.equal(shots[1].xg, null)
  assert.equal(shots[1].xg_status, 'pending')
})

test('CSV Upload: quoted fields with commas are preserved in preview data', () => {
  const csv = headers + '\n' + row({ player: '"Rivera, Jay"' })
  assert.equal(parseCsv(csv)[0].player, 'Rivera, Jay')
})

test('CSV Upload: missing required columns prevent importing a file', () => {
  const csv = 'id,match_id,player\nS1,M1,Jay'
  assert.throws(() => parseCsv(csv), /Missing required columns:.*team/)
})

test('CSV Upload: invalid outcome or out-of-range coordinates report the row', () => {
  assert.throws(
    () => parseCsv(headers + '\n' + row({ outcome: 'unknown' })),
    /Invalid outcome on row 2/,
  )
  assert.throws(
    () => parseCsv(headers + '\n' + row({ x: '101' })),
    /Coordinates must be 0–100 \(row 2\)/,
  )
})

test('CSV Upload: malformed rows, xG conflicts, and unclosed quotes are rejected', () => {
  assert.throws(() => parseCsv(headers + '\nS1,M1'), /Row 2 has the wrong number/)
  assert.throws(
    () => parseCsv(headers + ',xg,xg_status\n' + row() + ',0.42,unsupported'),
    /xg_status conflicts with numeric xG/,
  )
  assert.throws(() => parseCsv(headers + '\n"unterminated'), /unclosed quotation mark/)
})

test('CSV Upload: reports every invalid CSV row without losing row numbers', () => {
  const csv = headers + '\n' +
    row({ x: '101' }) + '\n' +
    row({ outcome: 'unknown' }) + '\n' +
    row({ minute: 'oops' }) + '\n' +
    row({ id: 'S4' })
  const result = parseCsvWithErrors(csv)
  assert.equal(result.shots.length, 1)
  assert.equal(result.shots[0].id, 'S4')
  assert.deepEqual(result.errors.map(e => e.row), [2, 3, 4])
  assert.match(result.errors[0].message, /Coordinates must be 0–100/)
  assert.match(result.errors[1].message, /Invalid outcome/)
  assert.match(result.errors[2].message, /Invalid minute/)
  assert.throws(() => parseCsv(csv), /row 2/)
})

test('CSV Upload: valid files return no row errors', () => {
  const result = parseCsvWithErrors(headers + '\n' + row())
  assert.equal(result.errors.length, 0)
  assert.equal(result.shots.length, 1)
})

test('CSV Upload: column-count errors do not hide errors from later rows', () => {
  const result = parseCsvWithErrors(headers + '\nS1,M1\n' + row({ x: 'bad' }))
  assert.deepEqual(result.errors.map(e => e.row), [2, 3])
  assert.equal(result.shots.length, 0)
})
