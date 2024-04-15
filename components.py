"""Components for the Streamlit app."""

import logging
import time

import requests
import polars as pl
import streamlit as st

from extract import (get_league_captain_picks,
                     get_season_league_rankings,
                     get_points_progression_data,
                     get_points_average_data,
                     get_latest_gameweek,
                     get_league_chip_data,
                     get_overall_rankings_data,
                     get_rankings,
                     get_league_name)

from visualisations import (get_manager_captains_chart,
                            get_league_rankings_chart,
                            get_points_progression_chart,
                            get_chips_chart,
                            get_overall_rankings_chart,
                            get_points_average_chart)


def render_initial_page() -> None:
    """Renders the initial page before inputting a league code."""
    st.title("⚽️ Mini League Analysis")
    st.subheader('⬅ Please enter your league code in the sidebar')

    with st.expander('How do I get my league code?'):
        st.markdown("""
                    1. Log into your FPL account
                    2. Navigate to your league's homepage
                    3. Copy the number in the URL as shown below
                    """)
        st.image("./images/league_code.png", width=600)

    st.error(
        """
        Note, this is optimised for smaller leagues

        If your league has more than **15 participants**, please expect longer waiting times""", icon="🚨")


def render_summary_section(league_data: dict) -> None:
    """Renders the summary section."""

    league_name = get_league_name(league_data)

    st.title(league_name)

    with requests.Session() as session:
        start = time.time()
        with st.spinner('Fetching league data...'):
            rankings = get_rankings(league_data, session)
        end = time.time()
        time_elapsed = end - start
        logging.info(f'Summary section: {time_elapsed}s')

    top_manager = rankings.sort(by='Rank')[0]

    top_latest_manager = rankings.sort(
        by='Latest Score', descending=True)[0]

    col1, col2 = st.columns([1, 2])

    with col1:

        st.metric(
            'Leading Manager',
            top_manager['Manager'][0],
            delta=f"{top_manager['Total Points'][0]} points")

        st.metric(f'GW {get_latest_gameweek()} Top Manager',
                  top_latest_manager['Manager'][0],
                  delta=f"{top_latest_manager['Latest Score'][0]} points")

    with col2:
        st.dataframe(rankings, hide_index=True)


def render_captains_tab(manager_data: pl.DataFrame) -> None:
    """Renders the captain performance tab."""

    st.header('Captain Performance')

    if st.session_state.get('captains_data') is None:

        start = time.time()

        with st.spinner('Fetching captain data...'):

            captain_picks_df = get_league_captain_picks(manager_data)
            st.session_state['captains_data'] = captain_picks_df

        end = time.time()

        time_elapsed = end - start

        logging.info(f"Captain tab: {time_elapsed}s")

    captain_picks_df: pl.DataFrame = st.session_state['captains_data']

    selected_manager = st.selectbox(
        "Select Manager", options=manager_data['player_name'])

    captains_chart = get_manager_captains_chart(
        selected_manager, captain_picks_df)

    st.altair_chart(captains_chart, use_container_width=True)


def render_league_rankings_tab(manager_data: pl.DataFrame) -> None:
    """Renders the league rankings tab."""

    st.header('League Rankings')

    if st.session_state.get('rankings_data') is None:
        start = time.time()
        with st.spinner('Fetching league rankings...'):
            rankings_data = get_season_league_rankings(manager_data)
        end = time.time()
        time_elapsed = end - start
        logging.info(f'League rankings tab: {time_elapsed}')
        st.session_state['rankings_data'] = rankings_data

    rankings_data = st.session_state['rankings_data']

    # selected_players = st.multiselect(
    #     'Select Managers',
    #     options=manager_data['player_name'],
    #     default=manager_data['player_name'].to_list())

    # rankings_data = rankings_data.filter(
    #     pl.col('player_name').is_in(selected_players))

    rankings_chart = get_league_rankings_chart(rankings_data)

    st.altair_chart(rankings_chart, use_container_width=True)


def render_points_progression_tab(manager_data: pl.DataFrame) -> None:
    """Renders the points progression tab."""

    st.header('Points Progression')

    if st.session_state.get('points_progression') is None:

        start = time.time()

        with st.spinner('Fetching points...'):

            points_progression_data = get_points_progression_data(manager_data)

        end = time.time()
        time_elapsed = end - start
        logging.info(f'Points progression tab: {time_elapsed}')

        st.session_state['points_progression'] = points_progression_data
    points_progression_data = st.session_state['points_progression']

    gameweeks = st.slider('Select Gameweeks', min_value=1,
                          max_value=get_latest_gameweek(), value=(1, get_latest_gameweek()))

    filtered_points_data = points_progression_data.filter(
        pl.col('Gameweek').is_between(gameweeks[0], gameweeks[1]))

    points_progression_chart = get_points_progression_chart(
        filtered_points_data)

    st.altair_chart(points_progression_chart, use_container_width=True)


def render_points_average_tab(manager_data: pl.DataFrame) -> None:
    """Renders the points average tab."""

    st.header('Rolling Points Average')

    if st.session_state.get('points_average') is None:

        start = time.time()

        with st.spinner('Fetching averages...'):

            average_points_data = get_points_average_data(manager_data)

        end = time.time()
        time_elapsed = end - start
        logging.info(f'Points average tab: {time_elapsed}')

        st.session_state['points_average'] = average_points_data
    average_points_data = st.session_state['points_average']

    gameweeks = st.slider('Select Gameweeks', min_value=1,
                          max_value=get_latest_gameweek(), value=(1, get_latest_gameweek()), key='averages')

    filtered_points_data = average_points_data.filter(
        pl.col('Gameweek').is_between(gameweeks[0], gameweeks[1]))

    average_points_chart = get_points_average_chart(
        filtered_points_data)

    st.altair_chart(average_points_chart, use_container_width=True)


def render_chip_usage_tab(manager_data: pl.DataFrame) -> None:
    """Renders the chip usage tab."""

    st.header("Chip Usage")

    if st.session_state.get('chip_data') is None:

        start = time.time()

        with st.spinner("Fetching chip data..."):

            chip_data = get_league_chip_data(manager_data)

        end = time.time()

        time_elapsed = end - start

        logging.info(f'Chips tab: {time_elapsed}')

        st.session_state['chip_data'] = chip_data

    chip_data = st.session_state['chip_data']

    chips_chart = get_chips_chart(chip_data)

    st.altair_chart(chips_chart)


def render_overall_rankings_tab(manager_data: pl.DataFrame) -> None:
    """Renders the overall rankings tab."""

    st.header("Overall Rankings")

    if st.session_state.get('overall_rankings') is None:

        start = time.time()

        with st.spinner('Fetching rankings...'):
            rankings_data = get_overall_rankings_data(manager_data)

        end = time.time()
        time_elapsed = end - start
        logging.info(f'Overall points tab: {time_elapsed}')

        st.session_state['overall_rankings'] = rankings_data

    rankings_data = st.session_state['overall_rankings']

    gameweeks = st.slider('Select Gameweeks',
                          min_value=1,
                          max_value=get_latest_gameweek(),
                          value=(1, get_latest_gameweek()),
                          key='rankings_slider')

    filtered_rankings_data = rankings_data.filter(
        pl.col('Gameweek').is_between(gameweeks[0], gameweeks[1]))

    selected_players = st.multiselect(
        'Select Managers',
        options=manager_data['player_name'],
        default=manager_data['player_name'].to_list())

    if selected_players:

        filtered_rankings_data = filtered_rankings_data.filter(
            pl.col('player_name').is_in(selected_players))

        rankings_chart = get_overall_rankings_chart(filtered_rankings_data)
        st.altair_chart(rankings_chart, use_container_width=True)
