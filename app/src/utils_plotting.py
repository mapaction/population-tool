"""Functions for plotting."""
import math
import urllib.request
from typing import List, Optional, Union

import folium
import geopandas as gpd
import matplotlib
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots


def display_polygons_on_map(
    gdf: gpd.GeoDataFrame,
    add_countryborders: bool = True,
    high_res: bool = False,
    world_gdf: Optional[gpd.GeoDataFrame] = None,
) -> folium.Map:
    """
    Display polygons on a map.

    If not given, country borders are retrieved from NaturalEarth
    (10m resolution).

    Inputs
    -------
    gdf (geopandas.GeoDataFrame): GeoDataFrame containing Polygon geometries.
    add_countryborders (bool, optional): if True, draw country borders. Default
        to True.
    high_res (bool, optional): if True, retrieve country borders at high
        resolution (1:10m instead of 1:110m). Used only if add_countryborders
        is True and world_gdf is None.
    world_gdf (geopandas.GeoDataFrame, optional): world countries geometries.
        If None, country borders will be retrieved from NaturalEarth (10m
        resolution).

    Returns
    -------
    m (folium.Map): folium Map with geometries.
    """
    if add_countryborders and world_gdf is None:
        if high_res:
            link = (
                "https://www.naturalearthdata.com/http//www.naturalearthdata."
                "com/"
                "download/10m/cultural/ne_10m_admin_0_countries.zip"
            )
            header = (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 "
                "Safari/537.36"
            )
            req = urllib.request.Request(link, headers={"User-Agent": header})
            world_gdf = gpd.read_file(urllib.request.urlopen(req))
        else:
            world_gdf = gpd.read_file(
                gpd.datasets.get_path("naturalearth_lowres")
            )

    m = folium.Map(
        zoom_start=10,
        control_scale=True,
    )

    # restrict maps to boundaries geodataframe
    bounds = gdf.total_bounds
    m.fit_bounds([bounds[:2].tolist()[::-1], bounds[2:].tolist()[::-1]])

    # add country borders as a GeoJSON layer
    if add_countryborders:
        country_borders = world_gdf
        folium.GeoJson(
            country_borders,
            style_function=lambda feature: {
                "fillColor": "white",
                "color": "black",
                "weight": 1,
                "fillOpacity": 0,
            },
        ).add_to(m)

    folium.GeoJson(
        gdf,
        style_function=lambda feature: {
            "fillColor": "blue",
            "color": "red",
            "weight": 1,
            "fillOpacity": 0.5,
        },
    ).add_to(m)

    return m


def color_list_from_cmap(cmap_name: str, n: int) -> Union[List[str], str]:
    """
    Generate a list of n colors from a specified color map.

    Inputs
    -------
    cmap_name (str): name of the color map to use. This should be a valid
    color map name recognized by matplotlib.cm.get_cmap().

    n (int): number of colors to generate in the color list.

    Returns
    -------
    color_list (list of str): list of n colors represented as hexadecimal
        strings.
    """
    cmap = matplotlib.cm.get_cmap(cmap_name)
    color_list = cmap(np.array(np.rint(np.linspace(0, cmap.N, n)), dtype=int))
    return [matplotlib.colors.to_hex(c) for c in color_list]


def plot_pop_data(
    gdf: gpd.GeoDataFrame,
    col_label: str,
    legend_title: str,
    plot_title: str,
    aggregated: bool = True,
    joint: bool = False,
    cmap_name: str = "viridis",
) -> go.Figure:
    """
    Plot population data on a bar chart.

    Inputs
    -------
    gdf (geopandas.GeoDataFrame): GeoDataFrame object containing geographic
        data.
    col_label (str): column in the GeoDataFrame that contains the labels
        for plotting.
    legend_title (str): title of the legend for the plot (when
        plotting disaggregated joint data) or the label of the y-axis (when
        plotting aggregated data).
    plot_title (str): title of the plot (only used when plotting
        disaggregated disjoint data).
    aggregated (bool, optional): boolean indicating whether the population
        data aggregated or not. Default to True.
    joint (bool, optional): boolean indicating whether a joint plot should be
        created. This parameter is only used if aggregated is False.
        Default to False.
    cmap_name (str, optional): name of the color map to be used for the
        plot. Default to "viridis".

    Returns
    -------
    fig (plotly.graph_objs.Figure): plotly figure object containing the plot.

    """
    if aggregated:
        return plot_pop_data_aggregated(
            gdf=gdf,
            col_label=col_label,
            label_title=legend_title,
            cmap_name=cmap_name,
        )
    else:
        return plot_pop_data_disaggregated(
            gdf=gdf,
            col_label=col_label,
            legend_title=legend_title,
            plot_title=plot_title,
            joint=joint,
            cmap_name=cmap_name,
        )


def plot_pop_data_aggregated(
    gdf: gpd.GeoDataFrame,
    col_label: str,
    label_title: str,
    cmap_name: str = "viridis",
) -> go.Figure:
    """
    Plot aggregated population data on a bar chart.

    Inputs
    -------
    gdf (geopandas.GeoDataFrame): GeoDataFrame object containing geographic
        data.
    col_label (str): column in the GeoDataFrame that contains the labels
        for plotting.
    label_title (str): label for the y-axis.
    cmap_name (str, optional): name of the color map to be used for the
        plot. Default to "viridis".

    Returns
    -------
    fig (plotly.graph_objs.Figure): plotly figure object containing the plot.

    """
    y = gdf[col_label].tolist()
    colors = color_list_from_cmap(cmap_name, len(gdf))[::-1]

    fig = go.Figure(
        data=[
            go.Bar(
                y=y,
                x=gdf["pop_tot"].tolist(),
                orientation="h",
                hoverinfo="x",
                marker_color=colors,
            )
        ]
    )

    fig.update_layout(
        yaxis={
            "title": label_title,
            "type": "category",
            "categoryorder": "total descending",
        },
        xaxis={"title": "Population"},
        margin=dict(pad=5),
    )

    fig.update_yaxes(title_standoff=20)
    fig.update_xaxes(title_standoff=20)

    return fig


def plot_pop_data_disaggregated(
    gdf: gpd.GeoDataFrame,
    col_label: str,
    legend_title: str,
    plot_title: str,
    joint: bool = False,
    cmap_name: str = "viridis",
) -> go.Figure:
    """
    Plot disaggregated population data on a bar chart.

    Inputs
    -------
    gdf (geopandas.GeoDataFrame): GeoDataFrame object containing geographic
        data.
    col_label (str): column in the GeoDataFrame that contains the labels
        for plotting.
    legend_title (str): title of the legend for the plot.
    plot_title (str): title of the plot (only used when plotting
        disaggregated disjoint data).
    joint (bool, optional): boolean indicating whether a joint plot should be
        created. Default to False.
    cmap_name (str, optional): name of the color map to be used for the
        plot. Default to "viridis".

    Returns
    -------
    fig (plotly.graph_objs.Figure): plotly figure object containing the plot.

    """
    if joint:
        return plot_pop_data_joint(
            gdf=gdf,
            col_label=col_label,
            legend_title=legend_title,
            cmap_name=cmap_name,
        )
    else:
        return plot_pop_data_split(
            gdf=gdf, col_label=col_label, plot_title=plot_title
        )


def plot_pop_data_split(
    gdf: gpd.GeoDataFrame,
    col_label: str,
    plot_title: str,
) -> go.Figure:
    """
    Plot disaggregated disjoint population data on a bar chart.

    One plot per gender/age will be visualised.

    Inputs
    -------
    gdf (geopandas.GeoDataFrame): GeoDataFrame object containing geographic
        data.
    col_label (str): column in the GeoDataFrame that contains the labels
        for plotting.
    plot_title (str): title of the plot.

    Returns
    -------
    fig (plotly.graph_objs.Figure): plotly figure object containing the plot.

    """
    data_pop = gdf[[col for col in gdf.columns if "pop_m" in col]].values
    data_max = data_pop.max()

    order_or_mag = math.floor(math.log(data_max, 10))
    axis_max = math.ceil(data_max / (10**order_or_mag)) * 10**order_or_mag
    ticks = list(range(0, axis_max + 10**order_or_mag, 10**order_or_mag))

    y = [int(col[-2:]) for col in gdf.columns if "pop_m" in col]

    fig = go.Figure()

    for i in range(len(gdf)):
        visible = True if i == 0 else False
        fig = fig.add_trace(
            go.Bar(
                y=y,
                x=gdf.iloc[i][
                    [col for col in gdf.columns if "pop_m" in col]
                ].values,
                orientation="h",
                name="Men",
                hoverinfo="x",
                marker=dict(color="powderblue"),
                width=3,
                visible=visible,
            )
        )
        fig = fig.add_trace(
            go.Bar(
                y=y,
                x=gdf.iloc[i][
                    [col for col in gdf.columns if "pop_f" in col]
                ].values
                * -1,
                orientation="h",
                name="Women",
                hoverinfo="x",
                marker=dict(color="seagreen"),
                width=3,
                visible=visible,
            )
        )

    update_dict_list = [
        dict(
            label=gdf[col_label].tolist()[i],
            method="update",
            args=[
                {
                    "visible": [
                        True if k == i * 2 or k == i * 2 + 1 else False
                        for k in range(2 * len(gdf))
                    ]
                },
                {
                    "title": f"<b>{plot_title}: {gdf[col_label].tolist()[i]}",
                    "showlegend": True,
                },
            ],
        )
        for i in range(len(gdf))
    ]

    fig = fig.update_xaxes(
        range=[-axis_max, axis_max],
        showline=True,
        linecolor="#000",
        tickvals=[-t for t in ticks if t != 0][::-1] + ticks,
        ticktext=[t for t in ticks if t != 0][::-1] + ticks,
    )

    fig = fig.update_layout(
        barmode="overlay",
        template="ggplot2",
        updatemenus=[
            go.layout.Updatemenu(
                active=0,
                buttons=list(update_dict_list),
                direction="up",
                x=1.05,
                xanchor="left",
                y=0.05,
                yanchor="bottom",
                font=dict(size=11),
            )
        ],
    )

    fig.update_layout(
        title_text=f"<b>{plot_title}: {gdf[col_label].tolist()[0]}"
    )

    return fig


def plot_pop_data_joint(
    gdf: gpd.GeoDataFrame,
    col_label: str,
    legend_title: str,
    cmap_name: str = "viridis",
) -> go.Figure:
    """
    Plot disaggregated stacked population data on a bar chart.

    Inputs
    -------
    gdf (geopandas.GeoDataFrame): GeoDataFrame object containing geographic
        data.
    col_label (str): column in the GeoDataFrame that contains the labels
        for plotting.
    legend_title (str): title of the legend for the plot.
    cmap_name (str, optional): name of the color map to be used for the
        plot. Default to "viridis".

    Returns
    -------
    fig (plotly.graph_objs.Figure): plotly figure object containing the plot.

    """
    y = [int(col[-2:]) for col in gdf.columns if "pop_m" in col]
    colors = color_list_from_cmap(cmap_name, len(gdf))[::-1]

    fig = go.Figure()

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["<b>Women", "<b>Men"],
        shared_yaxes=True,
        horizontal_spacing=0,
    )

    for i in range(len(gdf)):
        fig.add_trace(
            go.Bar(
                y=y,
                x=gdf.iloc[i][
                    [col for col in gdf.columns if "pop_m" in col]
                ].values,
                orientation="h",
                name=gdf[col_label].tolist()[i],
                hoverinfo="x",
                marker=dict(color=colors[i]),
                width=3,
            ),
            row=1,
            col=2,
        )
        fig.add_trace(
            go.Bar(
                y=y,
                x=gdf.iloc[i][
                    [col for col in gdf.columns if "pop_f" in col]
                ].values
                * -1,
                orientation="h",
                #             name='Women',
                hoverinfo="x",
                marker=dict(color=colors[i]),
                width=3,
                showlegend=False,
            ),
            row=1,
            col=1,
        )

    fig.update_layout(
        barmode="stack",
        template="ggplot2",
        legend={"title": legend_title + "\n", "traceorder": "normal"},
    )

    return fig
