"""Bridge golden fixtures to PR #58 without importing or editing the backend."""
from copy import deepcopy


def swap_names(example):
    swapped = deepcopy(example)
    a, b = swapped['input']['team_a'], swapped['input']['team_b']
    a['name'], b['name'] = b['name'], a['name']
    return swapped


def to_backend(example, half='all'):
    if half not in ('all', '1', '2'):
        raise ValueError('half must be all, 1, or 2')
    teams = []
    for slot in ('team_a', 'team_b'):
        team = example['input'][slot]
        teams.append({
            'name': team['name'], 'shots': team['shots'], 'goals': team['goals'],
            'xg': team['xg'], 'xg_calculated_shots': team['supported_shots'],
            'xg_missing_shots': team['shots'] - team['supported_shots'],
        })
    return {'match_id': example['id'], 'half': half, 'teams': teams}
