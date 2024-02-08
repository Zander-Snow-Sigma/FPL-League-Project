"""Extract script for FPL League Pipeline."""

import pandas as pd
import requests


FPL_INFO_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
LEAGUE_BASE_URL = "https://fantasy.premierleague.com/api/leagues-classic"

MANAGER_COLS = ['entry', 'player_name', 'entry_name']


def get_manager_data(league_code: int) -> pd.DataFrame:
    """Returns data for each manager in a given league."""

    res = requests.get(
        f"{LEAGUE_BASE_URL}/{league_code}/standings", timeout=10)

    if res.status_code == 200:

        managers = res.json()['standings']['results']

        manager_df = pd.DataFrame(managers)

        return manager_df[MANAGER_COLS]

    return None


def get_latest_gameweek() -> int:
    """Returns the latest gameweek ID."""

    res = requests.get(FPL_INFO_URL, timeout=10)

    if res.status_code == 200:

        gameweeks = res.json()['events']

        for gw in gameweeks:
            if gw['is_current']:
                return gw['id']
    return None


def add_nums(a: int, b: int) -> int:
    """Adding function for test."""
    return a + b


if __name__ == "__main__":

    # manager_data = get_manager_data(19070)

    current_gw = get_latest_gameweek()
    print(current_gw)
