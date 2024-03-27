"""Streamlit dashboard showing visualisations for an FPL Classic League."""

from concurrent.futures import ThreadPoolExecutor
import time

import altair as alt
import requests
import streamlit as st
import polars as pl

from extract import get_raw_league_data, get_league_name, get_manager_data, get_league_rankings_for_gw, get_latest_gameweek, get_player_data, get_player_score, get_manager_captain_picks
from extract import get_manager_prev_scores, make_scores_graph


def reset_rankings() -> None:
    """Callback function which resets session state rankings data."""

    st.session_state['rankings_data'] = None


if __name__ == "__main__":

    st.set_page_config(page_title="FPLiser",
                       page_icon="⚽️", layout='wide')

    st.title("⚽️ FPL League Analysis")

    with st.sidebar.form('League Code Input'):
        league_code = st.number_input(
            label="Enter league code", step=1, value=None)
        st.form_submit_button("Submit", on_click=reset_rankings)

    if league_code:

        tab1, tab2, tab3 = st.tabs(
            ['League Rankings', 'Captain Performance', 'Overall Rankings'])

        league_data = get_raw_league_data(league_code)

        league_name = get_league_name(league_data)

        st.header(league_name)

        manager_data = get_manager_data(league_data)

        current_gw = get_latest_gameweek()

        if st.session_state.get('rankings_data') is None:

            rankings = []

            with st.spinner('Fetching league data...'):

                with requests.Session() as session:

                    start = time.time()
                    with ThreadPoolExecutor() as executor:
                        for gw in range(1, current_gw + 1):
                            rankings += executor.submit(get_league_rankings_for_gw,
                                                        manager_data, gw, session).result()
                    # for gw in range(1, current_gw + 1):
                    #     rankings += get_league_rankings_for_gw(
                    #         manager_data, gw, session)

            end = time.time()
            print(end - start)
            rankings_df = pl.DataFrame(rankings)
            print(rankings_df)

            rankings_data = rankings_df.join(manager_data, on='manager_id')

            st.session_state['rankings_data'] = rankings_data

        rankings_data = st.session_state['rankings_data']

        with tab1:

            st.header('Leage Rankings')

            selected_players = st.multiselect(
                'Select Managers', options=manager_data['player_name'], default=manager_data['player_name'].to_list())

            chart_data = rankings_data.filter(
                pl.col('player_name').is_in(selected_players))

            highlight = alt.selection_point(
                on='mouseover', fields=['player_name'], nearest=True, empty=True)

            base = alt.Chart(chart_data).encode(
                x=alt.X('gameweek:N', title='Gameweek',
                        scale=alt.Scale(zero=False), axis=alt.Axis(grid=True)),
                y=alt.Y('rank:N', title='League Rank', axis=alt.Axis(
                    grid=True), scale=alt.Scale(zero=False)),
                color=alt.Color('player_name', title='Manager'),
                tooltip=alt.Tooltip('player_name', title='Manager')
            ).properties(height=400)

            points = base.mark_circle().encode(
                opacity=alt.value(0)
            ).add_params(
                highlight
            )

            points_2 = base.mark_circle(size=120, opacity=1)

            lines = base.mark_line(point=alt.OverlayMarkDef(filled=True, size=120)).encode(
                size=alt.condition(~highlight, alt.value(1), alt.value(5))
            )

            test_chart = points + lines

            st.altair_chart(test_chart, use_container_width=True)

        # rank_chart = alt.Chart(chart_data).mark_line(point=alt.OverlayMarkDef(filled=True, size=80)).encode(
        #     x=alt.X('gameweek:N', title='Gameweek',
        #             scale=alt.Scale(zero=False), axis=alt.Axis(grid=True)),
        #     y=alt.Y('rank:N', title='League Rank', axis=alt.Axis(
        #         grid=True), scale=alt.Scale(zero=False)),
        #     color=alt.Color('player_name', title='Manager'),
        #     tooltip=alt.Tooltip('player_name', title='Manager')
        # ).properties(height=400)

        # st.altair_chart(rank_chart, use_container_width=True)

        with tab2:

            st.header('Captain Performance')

            if st.session_state.get('captains_data') is None:

                player_data = get_player_data()

                captain_picks_df = pl.DataFrame()

                for id in manager_data["manager_id"]:
                    temp_df = get_manager_captain_picks(id, player_data)
                    captain_picks_df = pl.concat([captain_picks_df, temp_df])

                captain_picks_df = captain_picks_df.with_columns(
                    pl.struct(['id', 'gameweek']).map_elements(lambda x: get_player_score(x['id'], x['gameweek'])).alias('player_score'))

                captain_picks_df = captain_picks_df.join(
                    manager_data, left_on=pl.col("manager_id").cast(pl.Int64), right_on=pl.col("manager_id").cast(pl.Int64))

                print(captain_picks_df)

                st.session_state['captains_data'] = captain_picks_df

            captain_picks_df: pl.DataFrame = st.session_state['captains_data']

            selected_manager = st.selectbox(
                "Select Manager", options=manager_data['player_name'])

            player_captains = captain_picks_df.filter(
                pl.col('player_name') == selected_manager)

            captains_chart = alt.Chart(player_captains).mark_bar().encode(
                x=alt.X('gameweek:N'),
                y=alt.Y('player_score:Q', title="Captain Score"),
                color=alt.Color('web_name:N', title='Player'),
                tooltip=[alt.Tooltip('web_name', title='Player'),
                         alt.Tooltip('player_score', title='Score')]
            ).properties(height=500)

            st.altair_chart(captains_chart, use_container_width=True)

        with tab3:
            st.header('Overall Rankings')

            gameweek_df = pl.DataFrame()

            for id in manager_data["manager_id"]:
                temp_df = get_manager_prev_scores(id)
                gameweek_df = pl.concat([gameweek_df, temp_df])

            print(gameweek_df)

            gameweeks = st.slider('Select Gameweeks', min_value=1,
                                  max_value=get_latest_gameweek(), value=(1, get_latest_gameweek()))

            print(gameweeks)

            cum_gameweeks_df = gameweek_df.select(pl.col('Gameweek'), pl.col(
                'Manager ID'), pl.col('Points').cum_sum().over('Manager ID'))

            print(cum_gameweeks_df)

            gameweek_chart_data = cum_gameweeks_df.filter(
                pl.col('Gameweek').is_between(gameweeks[0], gameweeks[1]))

            graph = make_scores_graph(gameweek_chart_data)

            st.altair_chart(graph, use_container_width=True)
