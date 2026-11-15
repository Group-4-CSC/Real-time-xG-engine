import { sampleShots } from '../data/mockShots.js'
import { shotsFromMatches } from './matchData.js'

// Loads match data for all three screens. The backend matches route is still
// pending, so demo mode is the default and network failures fall back safely.
export async function loadMatchShots({ useLiveMatches = false, fetchMatches }) {
  try {
    const matches = await fetchMatches({ useMock: !useLiveMatches })
    return {
      shots: shotsFromMatches(matches),
      source: useLiveMatches ? 'api' : 'demo',
      error: '',
    }
  } catch (error) {
    return {
      shots: sampleShots.map(shot => ({ ...shot })),
      source: 'demo',
      error: useLiveMatches
        ? `Could not load matches from the API: ${error.message}. Showing sample data instead.`
        : `Could not load sample matches: ${error.message}. Showing bundled sample data instead.`,
    }
  }
}
