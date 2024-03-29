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
        x=alt.X('gameweek:N', title='Gameweek'),
        y=alt.Y('player_score:Q', title="Captain Score"),
        color=alt.Color('web_name:N', title='Player'),
        tooltip=[alt.Tooltip('web_name', title='Player'),
                 alt.Tooltip('player_score', title='Score')]
    ).properties(height=500)

    return captains_chart


def get_points_progression_chart(score_data: pl.DataFrame) -> alt.Chart:
    """Returns a line chart of overall rankings for each manager over the season."""

    chart = alt.Chart(score_data, height=700).mark_line().encode(
        color=alt.Color('player_name:N', title='Manager'),
        x=alt.X('Gameweek:N', axis=alt.Axis(grid=True)),
        y=alt.Y('Points:Q', scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip('player_name:N', title='Manager'),
                 alt.Tooltip('Points', title='Total Points')]
    )

    return chart


def get_chips_chart(chip_data: pl.DataFrame) -> alt.Chart:
    """Returns a bar chart of chip usage over the season."""

    chart = alt.Chart(chip_data).mark_bar().encode(
        x=alt.X('player_name', axis=None),
        y=alt.Y('points', title='Score'),
        color=alt.Color('player_name', title='Manager'),
        column=alt.Column('chip', title=None, header=alt.Header(
            titleOrient='bottom', labelOrient='bottom', labelFontSize=15)),
        tooltip=[alt.Tooltip('player_name', title='Manager'),
                 alt.Tooltip('points', title='Score')]
    ).properties(width=200)
    return chart


def get_overall_rankings_chart(rankings_data: pl.DataFrame) -> alt.Chart:
    """Returns a line chart of overall rank progression for each manager in the league."""

    max_rank = rankings_data.sort(by='Overall Rank', descending=True)[
        0]['Overall Rank'][0]

    chart = alt.Chart(rankings_data).mark_line().encode(
        x=alt.X('Gameweek:N', axis=alt.Axis(grid=True)),
        y=alt.Y('Overall Rank', scale=alt.Scale(
            type='log', domainMax=max_rank)),
        color=alt.Color('player_name', title='Manager')
    ).properties(height=500)
    return chart
