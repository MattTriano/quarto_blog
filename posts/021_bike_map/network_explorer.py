"""
Bike Network Explorer
=====================
Interactive folium-based explorer for OSMnx bike network graphs in Jupyter notebooks.
Visualizes weakly connected components with distinct colors, shows OSM tags on click,
and helps diagnose why edges are or aren't included in the bike network.

Usage:
    import osmnx as ox
    from bike_network_explorer import BikeNetworkExplorer

    G = ox.graph_from_place("Some City, State", network_type="bike")
    explorer = BikeNetworkExplorer(G)
    explorer.show()                # basic component map
    explorer.show(show_tags=True)  # click edges/nodes to see OSM tags
    explorer.component_summary()   # print stats per component
"""

import folium
import folium.plugins
import networkx as nx
import osmnx as ox
import json
from collections import Counter


# Default color palette — visually distinct, color-blind-friendly-ish
DEFAULT_COLORS = [
    "#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4",
    "#42d4f4", "#f032e6", "#bfef45", "#fabed4", "#469990",
    "#dcbeff", "#9A6324", "#fffac8", "#800000", "#aaffc3",
    "#808000", "#ffd8b1", "#000075", "#a9a9a9", "#000000",
]


class BikeNetworkExplorer:
    """Interactive folium map for exploring OSMnx bike network components.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        An OSMnx street network graph.
    colors : list[str], optional
        Hex color strings for components. Defaults to a 20-color palette.
    """

    def __init__(self, G, colors=None):
        self.G = G
        self.colors = colors or DEFAULT_COLORS

        # Compute weakly connected components, sorted largest-first
        self._components = sorted(
            nx.weakly_connected_components(G),
            key=len,
            reverse=True,
        )

        # Map each node to its component index
        self._node_comp = {}
        for i, comp in enumerate(self._components):
            for node in comp:
                self._node_comp[node] = i

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    @property
    def components(self):
        """List of node sets, one per weakly connected component (largest first)."""
        return self._components

    @property
    def num_components(self):
        return len(self._components)

    def color_for(self, component_index):
        """Return the color assigned to a component index."""
        return self.colors[component_index % len(self.colors)]

    def component_summary(self):
        """Print a summary table of all components."""
        print(f"{'Comp':>5}  {'Nodes':>7}  {'Edges':>7}  Color")
        print("-" * 38)
        for i, comp in enumerate(self._components):
            sub = self.G.subgraph(comp)
            print(
                f"{i:>5}  {sub.number_of_nodes():>7}  "
                f"{sub.number_of_edges():>7}  {self.color_for(i)}"
            )
        print(f"\nTotal: {self.num_components} components, "
              f"{self.G.number_of_nodes()} nodes, "
              f"{self.G.number_of_edges()} edges")

    def show(
        self,
        zoom_start=15,
        show_nodes=True,
        show_tags=True,
        edge_weight=2,
        edge_opacity=0.6,
        node_radius=3,
        node_opacity=0.6,
        min_component_size=1,
        max_components=None,
        tiles="CartoDB positron",
    ):
        """Build and return an interactive folium Map.

        Parameters
        ----------
        zoom_start : int
            Initial zoom level.
        show_nodes : bool
            Whether to draw circle markers at nodes.
        show_tags : bool
            If True, clicking edges/nodes shows their OSM tags in a popup.
        edge_weight : int
            Line thickness for edges.
        edge_opacity : float
            Line opacity for edges.
        node_radius : int
            Circle radius for nodes.
        node_opacity : float
            Opacity for nodes.
        min_component_size : int
            Hide components with fewer nodes than this.
        max_components : int or None
            Only show the N largest components. None = show all.
        tiles : str
            Folium tile layer name.

        Returns
        -------
        folium.Map
        """
        nodes_gdf = ox.graph_to_gdfs(self.G, edges=False)
        center_lat = nodes_gdf["y"].mean()
        center_lon = nodes_gdf["x"].mean()

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_start,
            tiles=tiles,
        )

        # Determine which components to render
        comps_to_draw = [
            (i, comp)
            for i, comp in enumerate(self._components)
            if len(comp) >= min_component_size
        ]
        if max_components is not None:
            comps_to_draw = comps_to_draw[:max_components]

        drawn_comp_indices = {i for i, _ in comps_to_draw}

        # -- Edges --------------------------------------------------------
        for u, v, key, data in self.G.edges(keys=True, data=True):
            comp_idx = self._node_comp[u]
            if comp_idx not in drawn_comp_indices:
                continue

            coords = self._edge_coords(u, v, data)
            color = self.color_for(comp_idx)

            popup = None
            if show_tags:
                popup = self._edge_popup(u, v, key, data, comp_idx)

            folium.PolyLine(
                coords,
                color=color,
                weight=edge_weight,
                opacity=edge_opacity,
                popup=popup,
            ).add_to(m)

        # -- Nodes --------------------------------------------------------
        if show_nodes:
            for node, data in self.G.nodes(data=True):
                comp_idx = self._node_comp[node]
                if comp_idx not in drawn_comp_indices:
                    continue

                color = self.color_for(comp_idx)

                popup = None
                if show_tags:
                    popup = self._node_popup(node, data, comp_idx)

                folium.CircleMarker(
                    location=[data["y"], data["x"]],
                    radius=node_radius,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=node_opacity,
                    popup=popup,
                ).add_to(m)

        # -- Legend --------------------------------------------------------
        self._add_legend(m, comps_to_draw)

        return m

    def show_component(self, index, context_buffer=0.001, **kwargs):
        """Zoom into a single component.

        Parameters
        ----------
        index : int
            Component index (0-based, largest first).
        context_buffer : float
            Lat/lon padding around the component bounds.
        **kwargs
            Passed through to `show()`.

        Returns
        -------
        folium.Map
        """
        comp = self._components[index]
        sub = self.G.subgraph(comp)
        nodes_gdf = ox.graph_to_gdfs(sub, edges=False)

        m = self.show(max_components=None, min_component_size=1, **kwargs)

        # Fit bounds to the chosen component
        sw = [nodes_gdf["y"].min() - context_buffer,
              nodes_gdf["x"].min() - context_buffer]
        ne = [nodes_gdf["y"].max() + context_buffer,
              nodes_gdf["x"].max() + context_buffer]
        m.fit_bounds([sw, ne])

        return m

    def edge_tags(self, component_index=None):
        """Return a list of all edge tag dicts, optionally filtered by component.

        Useful for programmatic inspection:
            df = pd.DataFrame(explorer.edge_tags(component_index=3))
        """
        results = []
        for u, v, key, data in self.G.edges(keys=True, data=True):
            if component_index is not None and self._node_comp[u] != component_index:
                continue
            row = {"u": u, "v": v, "key": key, "component": self._node_comp[u]}
            row.update({k: v for k, v in data.items() if k != "geometry"})
            results.append(row)
        return results

    def highway_tag_summary(self, component_index=None):
        """Print frequency of `highway` tag values across edges."""
        tags = self.edge_tags(component_index)
        counts = Counter(t.get("highway", "<missing>") for t in tags)
        print(f"highway tag distribution (component={component_index}):")
        for tag, count in counts.most_common():
            print(f"  {tag:30s}  {count}")

    # ------------------------------------------------------------------ #
    #  Internals
    # ------------------------------------------------------------------ #

    def _edge_coords(self, u, v, data):
        """Extract (lat, lon) coordinate list for an edge."""
        if "geometry" in data:
            return [(lat, lon) for lon, lat in data["geometry"].coords]
        return [
            (self.G.nodes[u]["y"], self.G.nodes[u]["x"]),
            (self.G.nodes[v]["y"], self.G.nodes[v]["x"]),
        ]

    def _edge_popup(self, u, v, key, data, comp_idx):
        """Build an HTML popup showing edge tags."""
        osm_id = data.get("osmid", "?")
        # osmid can be a list if the edge was simplified from multiple ways
        if isinstance(osm_id, list):
            osm_links = ", ".join(
                f'<a href="https://www.openstreetmap.org/way/{wid}" target="_blank">{wid}</a>'
                for wid in osm_id
            )
        else:
            osm_links = (
                f'<a href="https://www.openstreetmap.org/way/{osm_id}" target="_blank">{osm_id}</a>'
            )

        skip = {"geometry", "osmid"}
        tag_rows = "".join(
            f"<tr><td style='padding:2px 6px;font-weight:600;'>{k}</td>"
            f"<td style='padding:2px 6px;'>{v}</td></tr>"
            for k, v in sorted(data.items())
            if k not in skip
        )

        html = f"""
        <div style="font-family:monospace;font-size:12px;max-width:350px;">
            <div style="margin-bottom:4px;">
                <b>Edge</b> {u} → {v} (key {key})<br>
                <b>Component</b> {comp_idx}<br>
                <b>OSM way</b>: {osm_links}
            </div>
            <table style="border-collapse:collapse;">
                <tr style="border-bottom:1px solid #ccc;">
                    <th style="padding:2px 6px;text-align:left;">Tag</th>
                    <th style="padding:2px 6px;text-align:left;">Value</th>
                </tr>
                {tag_rows}
            </table>
        </div>
        """
        return folium.Popup(html, max_width=400)

    def _node_popup(self, node, data, comp_idx):
        """Build an HTML popup showing node attributes."""
        osm_link = (
            f'<a href="https://www.openstreetmap.org/node/{node}" '
            f'target="_blank">{node}</a>'
        )

        skip = {"x", "y"}
        tag_rows = "".join(
            f"<tr><td style='padding:2px 6px;font-weight:600;'>{k}</td>"
            f"<td style='padding:2px 6px;'>{v}</td></tr>"
            for k, v in sorted(data.items())
            if k not in skip
        )

        html = f"""
        <div style="font-family:monospace;font-size:12px;max-width:300px;">
            <div style="margin-bottom:4px;">
                <b>Node</b>: {osm_link}<br>
                <b>Component</b> {comp_idx}<br>
                <b>Coords</b>: {data['y']:.6f}, {data['x']:.6f}
            </div>
            <table style="border-collapse:collapse;">
                {tag_rows}
            </table>
        </div>
        """
        return folium.Popup(html, max_width=350)

    def _add_legend(self, m, comps_to_draw):
        """Add a fixed-position legend to the map."""
        items = ""
        for i, comp in comps_to_draw:
            c = self.color_for(i)
            sub = self.G.subgraph(comp)
            items += (
                f'<div style="margin:3px 0;">'
                f'<span style="display:inline-block;width:14px;height:14px;'
                f'background:{c};border-radius:2px;vertical-align:middle;'
                f'margin-right:6px;"></span>'
                f'<span style="vertical-align:middle;">'
                f'Comp {i}: {len(comp)}n / {sub.number_of_edges()}e</span></div>'
            )

        legend_html = f"""
        <div style="
            position:fixed;
            bottom:20px;
            left:20px;
            z-index:1000;
            background:white;
            padding:10px 14px;
            border-radius:6px;
            border:1px solid #ccc;
            font-family:monospace;
            font-size:11px;
            max-height:300px;
            overflow-y:auto;
            box-shadow:0 2px 6px rgba(0,0,0,0.15);
        ">
            <div style="font-weight:700;margin-bottom:6px;">Components</div>
            {items}
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

    def __repr__(self):
        return (
            f"BikeNetworkExplorer("
            f"{self.G.number_of_nodes()} nodes, "
            f"{self.G.number_of_edges()} edges, "
            f"{self.num_components} components)"
        )
