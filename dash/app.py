# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
from dash import html
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, use_pages=True, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP], meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ])

app.layout = dbc.Container(className="p-0", fluid=True, children=[
    dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="..")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Cornell", href="dashboard?building=campus"),
                dbc.DropdownMenuItem("Buildings", header=True),
                dbc.DropdownMenuItem("Biotech Shortcut", href="dashboard?building=biotech&floor=4&lab=441"),
                dbc.DropdownMenuItem("Baker", href="dashboard"),
            ],
            nav=True,
            in_navbar=True,
            label="Dashboard",
        ),
        dbc.NavItem(dbc.NavLink("About", href="about")),
        dbc.NavItem(dbc.NavLink("Help", href="404")),
        dbc.NavItem(dbc.NavLink("Admin", href="admin")),
        
    ],
    brand=html.Img(src="/assets/esw_logo.png", height="80px", width="auto"),
    brand_href="#",
    color="#B5E0BC",
    dark=False,
),

	dash.page_container
])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8055)