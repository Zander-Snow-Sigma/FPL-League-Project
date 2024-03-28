"""Components for the Streamlit app."""

import polars as pl
import streamlit as st

from extract import (get_league_captain_picks,
                     get_season_league_rankings,
                     get_overall_rankings_data,
                     get_latest_gameweek,
                     get_league_chip_data)

from visualisations import (get_manager_captains_chart,
                            get_league_rankings_chart,
                            get_overall_rankings_chart,
                            get_chips_chart)


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


def render_captains_tab(manager_data: pl.DataFrame) -> None:
    """Renders the captain performance tab."""

    st.header('Captain Performance')

    if st.session_state.get('captains_data') is None:

        with st.spinner('Fetching captain data...'):

            captain_picks_df = get_league_captain_picks(manager_data)
            st.session_state['captains_data'] = captain_picks_df

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
        with st.spinner('Fetching league data...'):
            rankings_data = get_season_league_rankings(manager_data)
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


def render_overall_rankings_tab(manager_data: pl.DataFrame) -> None:
    """Renders the overall rankings tab."""

    st.header('Overall Rankings')

    gameweek_df = get_overall_rankings_data(manager_data)

    gameweeks = st.slider('Select Gameweeks', min_value=1,
                          max_value=get_latest_gameweek(), value=(1, get_latest_gameweek()))

    gameweek_chart_data = gameweek_df.filter(
        pl.col('Gameweek').is_between(gameweeks[0], gameweeks[1]))

    overall_rankings_chart = get_overall_rankings_chart(
        gameweek_chart_data)

    st.altair_chart(overall_rankings_chart, use_container_width=True)


def render_chip_usage_tab(manager_data: pl.DataFrame) -> None:
    """Renders the chip usage tab."""

    st.header("Chip Usage")

    chip_data = get_league_chip_data(manager_data)

    chips_chart = get_chips_chart(chip_data)

    st.altair_chart(chips_chart)
