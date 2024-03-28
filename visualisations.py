"""Visualisation functions for the Streamlit app."""

import altair as alt
import polars as pl


def get_league_rankings_chart(rankings_data: pl.DataFrame) -> alt.Chart:
    """Returns the league rankings chart."""

    highlight = alt.selection_point(
        on='mouseover', fields=['player_name'], nearest=True, empty=True)

    base = alt.Chart(rankings_data).encode(
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

    points_2 = base.mark_circle(size=100, opacity=1)

    lines = base.mark_line(point=alt.OverlayMarkDef(filled=True, size=100)).encode(
        size=alt.condition(~highlight, alt.value(1), alt.value(5))
    )

    return points + lines


def get_manager_captains_chart(manager: str, captain_picks: pl.DataFrame) -> alt.Chart:
    """Returns a bar chart of the manager's captain picks."""

    manager_captains = captain_picks.filter(
        pl.col('player_name') == manager)

    captains_chart = alt.Chart(manager_captains).mark_bar().encode(
        x=alt.X('gameweek:N'),
        y=alt.Y('player_score:Q', title="Captain Score"),
        color=alt.Color('web_name:N', title='Player'),
        tooltip=[alt.Tooltip('web_name', title='Player'),
                 alt.Tooltip('player_score', title='Score')]
    ).properties(height=500)

    return captains_chart


def get_overall_rankings_chart(score_data: pl.DataFrame) -> alt.Chart:
    """Returns a graph."""

    chart = alt.Chart(score_data, height=700).mark_line().encode(
        color=alt.Color('Manager ID:N'),
        x=alt.X('Gameweek:N'),
        y=alt.Y('Points:Q', scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip('Manager ID', title='Manager'),
                 alt.Tooltip('Points', title='Total Points')]
    )

    return chart
