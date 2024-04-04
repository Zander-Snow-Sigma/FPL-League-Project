"""Streamlit dashboard showing visualisations for an FPL Classic League."""

import logging

import streamlit as st

from extract import get_raw_league_data, get_manager_data
from components import (render_initial_page,
                        render_summary_section,
                        render_captains_tab,
                        render_league_rankings_tab,
                        render_points_progression_tab,
                        render_chip_usage_tab,
                        render_overall_rankings_tab)


def reset_session() -> None:
    """Callback function which resets session state data."""

    st.session_state['rankings_data'] = None
    st.session_state['captains_data'] = None
    st.session_state['chip_data'] = None
    st.session_state['points_progression'] = None
    st.session_state['overall_rankings'] = None


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, filename='app.log',
                        format='%(asctime)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S')

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

        render_summary_section(league_data)

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            'League Rankings',
            'Captain Performance',
            'Points Progression',
            'Chip Usage',
            'Overall Rankings'
        ])

        manager_data = get_manager_data(league_data)

        with tab1:
            render_league_rankings_tab(manager_data)

        with tab2:
            render_captains_tab(manager_data)

        with tab3:
            render_points_progression_tab(manager_data)

        with tab4:
            render_chip_usage_tab(manager_data)

        with tab5:
            render_overall_rankings_tab(manager_data)
