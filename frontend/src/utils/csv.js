
export const columns = [
  'id', 'match_id', 'player', 'team', 'minute', 'period',
  'x', 'y', 'outcome', 'body_part', 'assist_type',
]

export const allowedOutcomes = [
  'goal', 'saved', 'blocked', 'off_target', 'post',
]

// Supports quoted CSV fields, including commas inside quotes.
export function parseCsv(text) {
  const rows = []
  let row = [], field = '', quoted = false

  for (let i = 0; i < text.length; i++) {
    const char = text[i]

    if (char === '"') {
      if (quoted && text[i + 1] === '"') {
        field += '"'
        i++
      } else {
        quoted = !quoted
      }
    } else if (char === ',' && !quoted) {
      row.push(field.trim())
      field = ''
    } else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[i + 1] === '\n') i++
      row.push(field.trim())
      if (row.some(Boolean)) rows.push(row)
      row = []
      field = ''
    } else {
      field += char
    }
  }

  if (quoted) {
    throw new Error('The CSV contains an unclosed quotation mark.')
  }

  row.push(field.trim())
  if (row.some(Boolean)) rows.push(row)

  if (rows.length < 2) {
    throw new Error('The CSV must contain a header and at least one shot.')
  }

  const headers = rows[0].map(h => h.toLowerCase())
  const missing = columns.filter(c => !headers.includes(c))

  if (missing.length) {
    throw new Error(`Missing required columns: ${missing.join(', ')}`)
  }

  const shots = rows.slice(1).map((values, i) => {
    if (values.length !== headers.length) {
      throw new Error(`Row ${i + 2} has the wrong number of columns.`)
    }

    const s = Object.fromEntries(
      headers.map((h, j) => [h, values[j]])
    )

    for (const key of ['x', 'y', 'minute', 'period']) {
      if (s[key] === '' || !Number.isFinite(Number(s[key]))) {
        throw new Error(`Invalid ${key} on row ${i + 2}.`)
      }

      s[key] = Number(s[key])
    }

    if (s.x < 0 || s.x > 100 || s.y < 0 || s.y > 100) {
      throw new Error(`Coordinates must be 0–100 (row ${i + 2}).`)
    }

    if (!allowedOutcomes.includes(s.outcome)) {
      throw new Error(`Invalid outcome on row ${i + 2}.`)
    }

    // Normalize backend and local status names.
    const statuses = {
      computed: 'calculated',
      calculated: 'calculated',
      unsupported: 'outside_model',
      outside_model: 'outside_model',
      pending: 'pending',
    }

    const providedStatus = s.xg_status || ''
    const status = statuses[providedStatus]

    if (providedStatus && !status) {
      throw new Error(`Invalid xg_status on row ${i + 2}.`)
    }

    if (s.xg === undefined || s.xg === '') {
      s.xg = null

      if (status === 'calculated') {
        throw new Error(
          `Calculated shots need a numeric xG (row ${i + 2}).`
        )
      }

      s.xg_status = status || 'pending'
    } else {
      s.xg = Number(s.xg)

      if (!Number.isFinite(s.xg) || s.xg < 0 || s.xg > 1) {
        throw new Error(`xg must be 0–1 or blank (row ${i + 2}).`)
      }

      if (status === 'outside_model' || status === 'pending') {
        throw new Error(
          `xg_status conflicts with numeric xG (row ${i + 2}).`
        )
      }

      s.xg_status = 'calculated'
    }

    return s
  })

  return shots
}
