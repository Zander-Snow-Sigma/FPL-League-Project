"""Streamlit dashboard showing visualisations for an FPL Classic League."""

import streamlit as st
import polars as pl

from extract import get_raw_league_data, get_league_name, get_manager_data, get_rankings, get_latest_gameweek
from components import (render_initial_page,
                        render_captains_tab,
                        render_league_rankings_tab,
                        render_points_progression_tab,
                        render_chip_usage_tab)


def reset_session() -> None:
    """Callback function which resets session state data."""

    st.session_state['rankings_data'] = None
    st.session_state['captains_data'] = None
    st.session_state['chip_data'] = None
    st.session_state['points_progression'] = None


if __name__ == "__main__":

    st.set_page_config(page_title="FPL Lab",
                       page_icon="🧪", layout='wide')

    st.sidebar.title("FPL Lab 🧪")

    with st.sidebar.form('League Code Input'):
        league_code = st.number_input(
            label="Enter league code", step=1, value=None)
        st.form_submit_button("Submit", on_click=reset_session)

    if not league_code:
        render_initial_page()

    else:
        league_data = get_raw_league_data(league_code)
        league_name = get_league_name(league_data)

        # top_manager = league_data['standings']['results'][0]['player_name']

        # top_manager_delta = league_data['standings']['results'][0]['last_rank'] - \
        #     league_data['standings']['results'][0]['last_rank']

        st.title(league_name)

        rankings = get_rankings(league_data)

        top_manager = rankings.sort(by='Rank')[0]

        top_latest_manager = rankings.sort(
            by='Latest Score', descending=True)[0]

        col1, col2 = st.columns([1, 2])

        with col1:

            st.metric(
                'Leading Manager', top_manager['Manager'][0], delta=top_manager['Total Points'][0])
            st.metric(f'GW {get_latest_gameweek()} Top Manager',
                      top_latest_manager['Manager'][0], delta=top_latest_manager['Latest Score'][0])

        with col2:

            st.dataframe(rankings, hide_index=True, use_container_width=True)

        tab1, tab2, tab3, tab4 = st.tabs(
            ['League Rankings', 'Captain Performance', 'Points Progression', 'Chip Usage'])

        manager_data = get_manager_data(league_data)

        with tab1:
            render_league_rankings_tab(manager_data)

        with tab2:
            render_captains_tab(manager_data)

        with tab3:
            render_points_progression_tab(manager_data)

        with tab4:
            render_chip_usage_tab(manager_data)
