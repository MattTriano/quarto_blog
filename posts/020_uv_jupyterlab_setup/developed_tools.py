from typing import Optional

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


class ExtractedChicagoParkEventExplorer:
    def __init__(
        self,
        chicago_boundary: Optional[gpd.GeoDataFrame] = None,
        chicago_park_events: Optional[gpd.GeoDataFrame] = None
    ) -> None:
        self.load_chicago_boundary(chicago_boundary)
        self.load_chicago_park_events(chicago_park_events)

    def load_chicago_boundary(self, df: Optional[gpd.GeoDataFrame] = None) -> None:
        if df is not None:
            self.chicago_boundary = df.copy()
        else:
            self.chicago_boundary = gpd.read_file(
                "https://data.cityofchicago.org/api/geospatial/qqq8-j68g?"
                "method=export&format=GeoJSON"
            )
            self.chicago_boundary

    def load_chicago_park_events(self, df: Optional[gpd.GeoDataFrame] = None) -> None:
        if df is not None:
            self.chicago_park_events = df.copy()
        else:
            print("Getting fresh Chicago Parks Dept Events data.")
            self.chicago_park_events = gpd.read_file(
                "https://data.cityofchicago.org/api/geospatial/tn7v-6rnw?"
                "method=export&format=GeoJSON"
            )
        col_order = [
            "activity_id", "title", "description", "category", "activity_type",
            "start_date", "end_date", "registration_date", "date_notes", "age_range",
            "location_facility", "address", "zip", "fee", "information_link", "type",
            "movie_title", "movie_rating", "image_link", "registration_link",
            "event_cancelled", "season", "zone", "restrictions", "location_notes",
            "latitude", "longitude", "geometry"
        ]
        self.chicago_park_events = self.chicago_park_events[col_order].copy()
        self.chicago_park_events = self.chicago_park_events.convert_dtypes()

    @property
    def event_category_counts(self) -> pd.Series:
        return self.chicago_park_events["category"].value_counts(dropna=False)

    def plot_events(self, event_categories: list[str], fig_width: int = 8) -> plt.Axes:
        markers = ["o", "*", "x", "+", ".", "1", "2", "3", "4"]
        cmap = plt.get_cmap("tab10", len(markers))
        colors = [cmap(i) for i in range(len(markers))]
        if len(event_categories) > len(markers):
            print(f"Too many categories entered, showing the first {len(markers)}")
        fig, ax = plt.subplots(figsize=(fig_width, fig_width*1.618))
        ax = self.chicago_boundary.plot(facecolor="none", ax=ax)
        legend_elements = []
        for i, event_category in enumerate(event_categories):
            df = self.chicago_park_events.loc[
                self.chicago_park_events["category"] == event_category
            ].copy()
            ax = df.plot(
                marker=markers[i], markersize=fig_width*6, color=colors[i], ax=ax
            )
            legend_elements.append(Line2D(
                [0], [0], marker=markers[i], color="w", markerfacecolor=colors[i],
                markeredgecolor=colors[i], markersize=fig_width,
                markeredgewidth=fig_width*0.2, label=event_category
            ))
        _ = ax.legend(
            handles=legend_elements, loc="lower left", fontsize=fig_width*1.5,
            markerscale=2
        )
        return ax

    def plot_map_of_subset(
        self, gdf: gpd.GeoDataFrame, fig_width: int = 8
    ) -> plt.Axes:
        fig, ax = plt.subplots(figsize=(fig_width, fig_width*1.618))
        ax = self.chicago_boundary.plot(facecolor="none", ax=ax)
        ax = gdf.plot(markersize=fig_width*6, ax=ax)
        return ax
