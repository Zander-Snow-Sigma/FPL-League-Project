"""Functions which extract data for the Streamlit app."""

from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
import numpy

import altair as alt
import polars as pl
import requests
from requests.exceptions import RequestException
import streamlit as st


FPL_INFO_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
LEAGUE_BASE_URL = "https://fantasy.premierleague.com/api/leagues-classic"
MANAGER_BASE_URL = "https://fantasy.premierleague.com/api/entry"
GAMEWEEK_BASE_URL = "https://fantasy.premierleague.com/api/event"

GW_PICKS_URL = "https://fantasy.premierleague.com/api/entry/7251561/event/8/picks/"

MANAGER_COLS = ['entry', 'player_name', 'entry_name']


def get_raw_league_data(league_code: int) -> dict:
    """Returns a python dictionary of the raw data for a given league."""

    res = requests.get(
        f"{LEAGUE_BASE_URL}/{league_code}/standings", timeout=10)

    if res.status_code == 200:
        return res.json()

    raise RequestException("Error - invalid league code.")


def get_manager_data(league_data: dict) -> pl.DataFrame:
    """Returns data for each manager in a given league."""

    managers = league_data['standings']['results']

    manager_df = pl.DataFrame(managers)

    return manager_df[MANAGER_COLS].rename({'entry': 'manager_id'})


def get_league_name(league_data: dict) -> str:
    """Returns the league name from the raw league data."""

    return league_data['league']['name']


def get_latest_gameweek() -> int:
    """Returns the latest gameweek ID."""

    res = requests.get(FPL_INFO_URL, timeout=10)

    if res.status_code == 200:

        gameweeks = res.json()['events']

        for gw in gameweeks:
            if gw['is_current']:
                return gw['id']
    raise RequestException("Error - FPL API could not be accessed.")


def get_player_data() -> pl.DataFrame:
    """Returns basic player info."""

    res = requests.get(FPL_INFO_URL, timeout=10)

    if res.status_code == 200:

        player_data = res.json()['elements']

        return pl.DataFrame(player_data)[['id', 'web_name']]

    raise RequestException("Error - could not access the FPL API.")


def get_captain(
        manager_id: int,
        gw: int,
        player_data: pl.DataFrame,
        session: requests.Session) -> pl.DataFrame:
    """Returns the player ID of the managers captain for a given gameweek."""

    res = session.get(
        f"{MANAGER_BASE_URL}/{manager_id}/event/{gw}/picks", timeout=10)

    if res.status_code == 200:

        picks = res.json()['picks']

        captain_id = next(pick['element']
                          for pick in picks if pick['is_captain'])

        test = player_data.filter(id=captain_id)

        return test

    raise RequestException("Error - could not access FPL API.")


def get_manager_captain_picks(
        manager_id: int,
        player_data: pl.DataFrame,
        session: requests.Session) -> pl.DataFrame:
    """Returns the captain picks for a manager."""

    latest_gw = get_latest_gameweek()

    captain_picks = pl.DataFrame()

    for gw in range(1, latest_gw + 1):
        captain = get_captain(manager_id, gw, player_data, session)
        captain = captain.with_columns(
            pl.lit(gw).alias("gameweek")
        )
        captain = captain.with_columns(
            pl.lit(manager_id).alias("manager_id")
        )
        captain_picks = pl.concat([captain_picks, captain])

    return captain_picks


def get_manager_prev_scores(manager_id: int) -> pl.DataFrame:
    """Returns managers previous scores for this season."""

    res = requests.get(f"{MANAGER_BASE_URL}/{manager_id}/history", timeout=10)

    if res.status_code == 200:
        gameweeks = res.json()['current']

        gameweek_df = pl.DataFrame(gameweeks)

        gameweek_df = gameweek_df.rename(
            {"event": "Gameweek", "points": "Points"})

        gameweek_df = gameweek_df.with_columns(
            pl.lit(manager_id).alias('Manager ID'))

        return gameweek_df[["Gameweek", "Points", "Manager ID"]]

    raise ValueError("Error - invalid manager ID provided.")


def get_player_score(player_id: int, gw: int, session: requests.Session) -> int:
    """Returns the score of a player in a given gameweek."""

    res = session.get(f"{GAMEWEEK_BASE_URL}/{gw}/live", timeout=10)

    if res.status_code != 200:
        raise RequestException("Error - could not access FPL API.")

    players = res.json()['elements']

    player = next(player for player in players if player['id'] == player_id)

    return player['stats']['total_points']


def get_gw_manager_data(gameweek: int, manager_id: int):
    """Returns all the necessary data for a given manager in a given gameweek."""

    res = requests.get(
        f"{MANAGER_BASE_URL}/{manager_id}/event/{gameweek}/picks", timeout=10)

    if res.status_code != 200:
        raise ConnectionError("Could not connect to the API.")
    content = res.json()

    return content


def get_league_rankings_for_gw(
        manager_data: pl.DataFrame,
        gameweek: int,
        session: requests.Session) -> dict:
    """Returns the league standings for a given gameweek."""

    points = {}

    for manager_id in manager_data['manager_id']:
        res = session.get(
            f"{MANAGER_BASE_URL}/{manager_id}/event/{gameweek}/picks", timeout=10)
        if res.status_code != 200:
            print(res.status_code)
            print(res.headers)
            raise ConnectionError(
                f"Could not retrieve gameweek {gameweek} data for manager {manager_id}")
        data = res.json()
        total_points = data['entry_history']['total_points']
        points[manager_id] = total_points

    rankings = [{"manager_id": key, "rank": rank, "gameweek": gameweek} for rank, key in enumerate(
        sorted(points, key=points.get, reverse=True), 1)]

    return rankings


def get_season_league_rankings(manager_data: pl.DataFrame) -> pl.DataFrame:
    """Returns a dataframe of league rankings over the season."""

    league_size = manager_data['manager_id'].count()

    current_gw = get_latest_gameweek()
    chunks = (current_gw // 5) + 1
    gameweeks = list(range(1, current_gw + 1))
    gameweek_chunks = numpy.array_split(gameweeks, chunks)

    rankings = []

    if league_size < 10:

        for gws in gameweek_chunks:
            with requests.Session() as session:
                with ThreadPoolExecutor() as executor:
                    rankings += list(executor.map(get_league_rankings_for_gw, repeat(
                        manager_data), gws, repeat(session)))

        rankings = [item for row in rankings for item in row]

    else:
        with requests.Session() as session:
            with ThreadPoolExecutor() as executor:
                for gw in range(1, current_gw + 1):
                    rankings += executor.submit(get_league_rankings_for_gw,
                                                manager_data, gw, session).result()

    rankings_df = pl.DataFrame(rankings)

    rankings_data = rankings_df.join(manager_data, on='manager_id')

    return rankings_data


def get_league_captain_picks(manager_data: pl.DataFrame) -> pl.DataFrame:
    """Returns a dataframe of every manager's captain for each gameweek and their score."""

    player_data = get_player_data()

    captain_picks_df = pl.DataFrame()

    with requests.Session() as session:
        for manager_id in manager_data["manager_id"]:
            temp_df = get_manager_captain_picks(
                manager_id, player_data, session)
            captain_picks_df = pl.concat([captain_picks_df, temp_df])

        captain_picks_df = captain_picks_df.with_columns(
            pl.struct(['id', 'gameweek']).map_elements(
                lambda x: get_player_score(x['id'], x['gameweek'], session)
            ).alias('player_score'))

    captain_picks_df = captain_picks_df.join(
        manager_data,
        left_on=pl.col("manager_id").cast(pl.Int64),
        right_on=pl.col("manager_id").cast(pl.Int64))

    return captain_picks_df


def get_overall_rankings_data(manager_data: pl.DataFrame) -> pl.DataFrame:
    """Returns the overall rankings data for each manager over the season."""

    gameweek_df = pl.DataFrame()

    for manager_id in manager_data["manager_id"]:
        manager_df = get_manager_prev_scores(manager_id)
        gameweek_df = pl.concat([gameweek_df, manager_df])

    cum_gameweeks_df = gameweek_df.select(pl.col('Gameweek'), pl.col(
        'Manager ID'), pl.col('Points').cum_sum().over('Manager ID'))

    return cum_gameweeks_df


if __name__ == "__main__":

    raw_league = get_raw_league_data(19070)
    print(raw_league)
