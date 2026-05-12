import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


app = dash.Dash(__name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True
)
app.title = "Beauty Commerce Marketing Analytics"

nykaa = pd.read_csv("data/nykaa_campaign_data.csv")
purplle = pd.read_csv("data/purplle_campaign_data.csv")
tira = pd.read_csv("data/tira_campaign_data.csv")


for df in [nykaa, purplle, tira]:
    df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")

# Add source
nykaa["source"] = "Nykaa"
purplle["source"] = "Purplle"
tira["source"] = "Tira"

# Combine all data
df = pd.concat([nykaa, purplle, tira], ignore_index=True)

# Process channels
df["channel_list"] = df["channel_used"].str.split(",")
df["channel_list"] = df["channel_list"].apply(lambda x: [i.strip().lower() for i in x])

# Calculate metrics
df["ctr"] = df["clicks"] / df["impressions"]
df["lead_rate"] = df["leads"] / df["clicks"]
df["conversion_rate"] = df["conversions"] / df["leads"]
df["cost_per_conversion"] = df["acquisition_cost"] / df["conversions"]
df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")

# Convert to USD (₹83 ≈ $1)
conversion_rate_usd = 83
df["revenue_usd"] = df["revenue"] / conversion_rate_usd
df["acquisition_cost_usd"] = df["acquisition_cost"] / conversion_rate_usd
df["cost_per_conversion_usd"] = df["cost_per_conversion"] / conversion_rate_usd

# Explode channels for analysis
df_exploded = df.explode("channel_list")

# ============== COMPUTE ACTUAL KPIs ==============
total_revenue = float(df["revenue_usd"].sum())
total_impressions = int(df["impressions"].sum())
total_clicks = int(df["clicks"].sum())
total_leads = int(df["leads"].sum())
total_conversions = int(df["conversions"].sum())

overall_ctr = float(total_clicks / total_impressions * 100)
overall_conversion_rate = float(total_conversions / total_leads * 100)
overall_roi = float(df["revenue_usd"].sum() / df["acquisition_cost_usd"].sum())
total_acquisition_cost = float(df["acquisition_cost_usd"].sum())

# Revenue by channel
revenue_by_channel = df_exploded.groupby("channel_list")["revenue_usd"].sum().sort_values(ascending=True)

# Channel metrics
channel_metrics = df_exploded.groupby("channel_list").agg(
    impressions=("impressions", "sum"),
    clicks=("clicks", "sum"),
    leads=("leads", "sum"),
    conversions=("conversions", "sum"),
    revenue=("revenue_usd", "sum"),
    acquisition_cost=("acquisition_cost_usd", "sum"),
    roi=("roi", "mean"),
    engagement_score=("engagement_score", "mean")
).reset_index()

channel_metrics["ctr"] = channel_metrics["clicks"] / channel_metrics["impressions"]
channel_metrics["conversion_rate"] = channel_metrics["conversions"] / channel_metrics["leads"]
channel_metrics["cost_per_conversion"] = channel_metrics["acquisition_cost"] / channel_metrics["conversions"]

# Revenue by source
revenue_by_source = df.groupby("source")["revenue_usd"].sum()

# Revenue by campaign type
revenue_by_campaign = df.groupby("campaign_type")["revenue_usd"].sum().sort_values()

# Funnel data by channel
funnel_by_channel = df_exploded.groupby("channel_list").agg(
    impressions=("impressions", "sum"),
    clicks=("clicks", "sum"),
    leads=("leads", "sum"),
    conversions=("conversions", "sum")
)

# Duration slider values (converted to native Python ints)
duration_min = int(df["duration"].min())
duration_max = int(df["duration"].max())
duration_mid = int((duration_min + duration_max) // 2)

# ============== NAVBAR ==============
navbar = dbc.Navbar(
    dbc.Container([
        dbc.Row([
            dbc.Col(html.I(className="bi bi-graph-up-arrow me-2", style={"font-size": "1.5rem"})),
            dbc.Col(dbc.NavbarBrand("Beauty Commerce Analytics", className="ms-2")),
        ], align="center"),
        dbc.Nav([
            dbc.NavItem(dbc.NavLink("Overview", href="/", active="exact")),
            dbc.NavItem(dbc.NavLink("Channel Analysis", href="/channels", active="exact")),
            dbc.NavItem(dbc.NavLink("Campaign Performance", href="/campaigns", active="exact")),
        ], pills=True),
    ]),
    color="primary",
    dark=True,
    className="mb-4"
)

# ============== APP LAYOUT ==============
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content', className="container-fluid")
])

# ============== OVERVIEW PAGE ==============
overview_page = html.Div([
    # KPI Cards
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Total Revenue", className="card-title text-muted"),
                html.H2(f"${total_revenue/1e9:.2f}B", className="text-primary"),
                html.P("Total across all platforms", className="card-text text-muted small")
            ])
        ], className="shadow-sm border-start border-primary border-4"), md=3),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Total Impressions", className="card-title text-muted"),
                html.H2(f"{total_impressions/1e9:.2f}B", className="text-success"),
                html.P("Across all channels", className="card-text text-muted small")
            ])
        ], className="shadow-sm border-start border-success border-4"), md=3),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Overall CTR", className="card-title text-muted"),
                html.H2(f"{overall_ctr:.2f}%", className="text-info"),
                html.P("Average click-through rate", className="card-text text-muted small")
            ])
        ], className="shadow-sm border-start border-info border-4"), md=3),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Conversion Rate", className="card-title text-muted"),
                html.H2(f"{overall_conversion_rate:.2f}%", className="text-warning"),
                html.P("Lead to conversion", className="card-text text-muted small")
            ])
        ], className="shadow-sm border-start border-warning border-4"), md=3),
    ], className="mb-4"),
    
    # Additional KPI Row
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Total Conversions", className="card-title text-muted"),
                html.H2(f"{total_conversions/1e6:.2f}M", className="text-danger"),
                html.P("Across all platforms", className="card-text text-muted small")
            ])
        ], className="shadow-sm"), md=3),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Total Acquisition Cost", className="card-title text-muted"),
                html.H2(f"${total_acquisition_cost/1e6:.2f}M", className="text-dark"),
                html.P("Total marketing spend", className="card-text text-muted small")
            ])
        ], className="shadow-sm"), md=3),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Overall ROI", className="card-title text-muted"),
                html.H2(f"{overall_roi:.2f}x", className="text-success"),
                html.P("Revenue per $1 spent", className="card-text text-muted small")
            ])
        ], className="shadow-sm"), md=3),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Avg Cost/Conversion", className="card-title text-muted"),
                html.H2(f"${float(df['cost_per_conversion_usd'].mean()):.2f}", className="text-info"),
                html.P("Average cost per conversion", className="card-text text-muted small")
            ])
        ], className="shadow-sm"), md=3),
    ], className="mb-4"),
    
    # Charts Row 1
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Revenue by Channel", className="fw-bold"),
            dbc.CardBody([
                dcc.Graph(
                    figure=px.bar(
                        x=revenue_by_channel.values,
                        y=[c.title() for c in revenue_by_channel.index],
                        orientation='h',
                        title="Revenue Distribution by Channel (USD)",
                        labels={'x': 'Revenue (USD)', 'y': 'Channel'},
                        text=[f"${v/1e9:.2f}B" for v in revenue_by_channel.values]
                    ).update_traces(textposition='outside').update_layout(showlegend=False)
                )
            ])
        ], className="shadow-sm"), md=6),
        
        dbc.Col(dbc.Card([
            dbc.CardHeader("Marketing Funnel", className="fw-bold"),
            dbc.CardBody([
                dcc.Graph(
                    figure=go.Figure(go.Funnel(
                        y=['Impressions', 'Clicks', 'Leads', 'Conversions'],
                        x=[total_impressions, total_clicks, total_leads, total_conversions],
                        textinfo="value+percent previous",
                        texttemplate="%{value:,.0f}<br>%{percentPrevious:.1%}"
                    )).update_layout(title="Overall Conversion Funnel")
                )
            ])
        ], className="shadow-sm"), md=6),
    ], className="mb-4"),
    
    # Charts Row 2
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Revenue by Campaign Type", className="fw-bold"),
            dbc.CardBody([
                dcc.Graph(
                    figure=px.bar(
                        x=revenue_by_campaign.values,
                        y=revenue_by_campaign.index,
                        orientation='h',
                        title="Revenue by Campaign Type (USD)",
                        labels={'x': 'Revenue (USD)', 'y': 'Campaign Type'},
                        text=[f"${v/1e6:.2f}M" for v in revenue_by_campaign.values]
                    ).update_traces(textposition='outside').update_layout(showlegend=False)
                )
            ])
        ], className="shadow-sm"), md=6),
        
        dbc.Col(dbc.Card([
            dbc.CardHeader("Revenue by Platform", className="fw-bold"),
            dbc.CardBody([
                dcc.Graph(
                    figure=px.pie(
                        values=revenue_by_source.values,
                        names=revenue_by_source.index,
                        title="Revenue Share by Platform (USD)",
                        hole=0.3
                    ).update_traces(texttemplate='$%{value:,.0f}<br>%{percent}')
                )
            ])
        ], className="shadow-sm"), md=6),
    ], className="mb-4"),
    
    # Platform Comparison
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Platform Performance Comparison", className="fw-bold"),
            dbc.CardBody([
                dcc.Dropdown(
                    id='platform-metric-dropdown',
                    options=[
                        {'label': 'Revenue (USD)', 'value': 'revenue'},
                        {'label': 'ROI', 'value': 'roi'},
                        {'label': 'Conversion Rate', 'value': 'conversion_rate'},
                        {'label': 'CTR', 'value': 'ctr'},
                        {'label': 'Cost per Conversion (USD)', 'value': 'cost_per_conversion'}
                    ],
                    value='revenue',
                    className="mb-3"
                ),
                dcc.Graph(id='platform-comparison-chart')
            ])
        ], className="shadow-sm"), md=12),
    ]),
])

# ============== CHANNEL ANALYSIS PAGE ==============
channel_page = html.Div([
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Channel Selection", className="fw-bold"),
            dbc.CardBody([
                dbc.Checklist(
                    id='channel-selector',
                    options=[
                        {'label': ch.title(), 'value': ch} 
                        for ch in sorted(df_exploded["channel_list"].unique())
                    ],
                    value=['email', 'instagram'],
                    inline=True,
                    className="mb-3"
                ),
                html.Hr(),
                html.H6("Metric to Display:", className="text-muted"),
                dcc.RadioItems(
                    id='channel-metric-radio',
                    options=[
                        {'label': 'Conversion Rate', 'value': 'conversion_rate'},
                        {'label': 'ROI', 'value': 'roi'},
                        {'label': 'CTR', 'value': 'ctr'},
                        {'label': 'Cost per Conversion (USD)', 'value': 'cost_per_conversion'},
                        {'label': 'Engagement Score', 'value': 'engagement_score'}
                    ],
                    value='conversion_rate',
                    inline=True
                )
            ])
        ], className="shadow-sm"), md=3),
        
        dbc.Col([
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5("Channel Metric Comparison", className="card-title"),
                        dcc.Graph(id='channel-metric-chart')
                    ])
                ], className="shadow-sm"), md=12),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5("Channel Funnel Analysis", className="card-title"),
                        dcc.Graph(id='channel-funnel-chart')
                    ])
                ], className="shadow-sm"), md=6),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5("Revenue Share", className="card-title"),
                        dcc.Graph(id='channel-revenue-share')
                    ])
                ], className="shadow-sm"), md=6),
            ]),
        ], md=9),
    ]),
])

# ============== CAMPAIGN PERFORMANCE PAGE ==============
campaign_page = html.Div([
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Filters", className="fw-bold"),
            dbc.CardBody([
                html.Label("Select Platform:", className="fw-bold"),
                dcc.Dropdown(
                    id='platform-filter',
                    options=[
                        {'label': 'All Platforms', 'value': 'all'},
                        {'label': 'Nykaa', 'value': 'Nykaa'},
                        {'label': 'Purplle', 'value': 'Purplle'},
                        {'label': 'Tira', 'value': 'Tira'}
                    ],
                    value='all',
                    className="mb-3"
                ),
                
                html.Label("Campaign Type:", className="fw-bold"),
                dcc.Dropdown(
                    id='campaign-type-filter',
                    options=[
                        {'label': 'All Types', 'value': 'all'}
                    ] + [{'label': ct, 'value': ct} for ct in sorted(df["campaign_type"].unique())],
                    value='all',
                    className="mb-3"
                ),
                
                html.Label(f"Duration Range (Days):", className="fw-bold"),
                dcc.RangeSlider(
                    id='duration-slider',
                    min=duration_min,
                    max=duration_max,
                    step=1,
                    value=[duration_min, duration_max],
                    marks={
                        duration_min: str(duration_min),
                        duration_max: str(duration_max),
                        duration_mid: str(duration_mid)
                    },
                    className="mb-3"
                ),
                
                html.Label("Target Audience:", className="fw-bold"),
                dbc.Checklist(
                    id='audience-filter',
                    options=[{'label': au, 'value': au} for au in sorted(df["target_audience"].unique())],
                    value=sorted(df["target_audience"].unique())[:2],
                ),
                
                html.Hr(),
                dbc.Button("Reset Filters", id="reset-filters", color="secondary", className="w-100")
            ])
        ], className="shadow-sm"), md=3),
        
        dbc.Col([
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5("Revenue vs Impressions", className="card-title"),
                        dcc.Graph(id='campaign-scatter')
                    ])
                ], className="shadow-sm"), md=6),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5("Revenue Distribution", className="card-title"),
                        dcc.Graph(id='revenue-distribution')
                    ])
                ], className="shadow-sm"), md=6),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5("Engagement Score by Campaign Type", className="card-title"),
                        dcc.Graph(id='engagement-boxplot')
                    ])
                ], className="shadow-sm"), md=12),
            ]),
        ], md=9),
    ]),
])

# ============== PAGE ROUTER ==============
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/channels':
        return channel_page
    elif pathname == '/campaigns':
        return campaign_page
    else:
        return overview_page

# ============== CALLBACKS ==============

# Platform comparison chart
@app.callback(
    Output('platform-comparison-chart', 'figure'),
    Input('platform-metric-dropdown', 'value')
)
def update_platform_comparison(metric):
    platform_stats = df.groupby("source").agg(
        revenue=("revenue_usd", "sum"),
        roi=("roi", "mean"),
        conversion_rate=("conversion_rate", "mean"),
        ctr=("ctr", "mean"),
        cost_per_conversion=("cost_per_conversion_usd", "mean")
    ).reset_index()
    
    metric_labels = {
        'revenue': 'Revenue (USD)',
        'roi': 'ROI',
        'conversion_rate': 'Conversion Rate',
        'ctr': 'CTR',
        'cost_per_conversion': 'Cost per Conversion (USD)'
    }
    
    fig = px.bar(
        platform_stats,
        x='source',
        y=metric,
        title=f'{metric_labels.get(metric, metric)} by Platform',
        color='source',
        text=platform_stats[metric].apply(lambda x: f'${x:,.2f}' if metric == 'revenue' 
                                          else f'${x:.4f}' if metric == 'cost_per_conversion'
                                          else f'{x:.4f}')
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(showlegend=False)
    
    return fig

# Channel metric comparison
@app.callback(
    Output('channel-metric-chart', 'figure'),
    [Input('channel-selector', 'value'),
     Input('channel-metric-radio', 'value')]
)
def update_channel_metrics(selected_channels, metric):
    filtered = channel_metrics[channel_metrics["channel_list"].isin(selected_channels)]
    filtered = filtered.sort_values(metric, ascending=True)
    
    metric_labels = {
        'conversion_rate': 'Conversion Rate',
        'roi': 'ROI',
        'ctr': 'CTR',
        'cost_per_conversion': 'Cost per Conversion (USD)',
        'engagement_score': 'Engagement Score'
    }
    
    fig = px.bar(
        filtered,
        x='channel_list',
        y=metric,
        title=f'{metric_labels.get(metric, metric)} by Channel',
        color='channel_list',
        text=filtered[metric].apply(lambda x: f'${x:.4f}' if metric == 'cost_per_conversion' else f'{x:.4f}')
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(showlegend=False)
    
    return fig

# Channel funnel
@app.callback(
    Output('channel-funnel-chart', 'figure'),
    Input('channel-selector', 'value')
)
def update_channel_funnel(selected_channels):
    if not selected_channels:
        return go.Figure()
    
    channel = selected_channels[0]
    row = funnel_by_channel.loc[channel]
    
    fig = go.Figure(go.Funnel(
        y=['Impressions', 'Clicks', 'Leads', 'Conversions'],
        x=[int(row['impressions']), int(row['clicks']), int(row['leads']), int(row['conversions'])],
        textinfo="value+percent previous",
        texttemplate="%{value:,.0f}<br>%{percentPrevious:.1%}"
    ))
    fig.update_layout(title=f'Funnel: {channel.title()}')
    
    return fig

# Revenue share
@app.callback(
    Output('channel-revenue-share', 'figure'),
    Input('channel-selector', 'value')
)
def update_revenue_share(selected_channels):
    filtered = channel_metrics[channel_metrics["channel_list"].isin(selected_channels)]
    
    fig = px.pie(
        values=filtered['revenue'],
        names=filtered['channel_list'].str.title(),
        title='Revenue Distribution (USD)',
        hole=0.3
    ).update_traces(texttemplate='$%{value:,.0f}<br>%{percent}')
    
    return fig

# Campaign charts
@app.callback(
    [Output('campaign-scatter', 'figure'),
     Output('revenue-distribution', 'figure'),
     Output('engagement-boxplot', 'figure')],
    [Input('platform-filter', 'value'),
     Input('campaign-type-filter', 'value'),
     Input('duration-slider', 'value'),
     Input('audience-filter', 'value')]
)
def update_campaign_charts(platform, campaign_type, duration_range, audiences):
    filtered_df = df.copy()
    
    if platform != 'all':
        filtered_df = filtered_df[filtered_df["source"] == platform]
    if campaign_type != 'all':
        filtered_df = filtered_df[filtered_df["campaign_type"] == campaign_type]
    
    filtered_df = filtered_df[
        (filtered_df["duration"] >= duration_range[0]) & 
        (filtered_df["duration"] <= duration_range[1])
    ]
    
    if audiences:
        filtered_df = filtered_df[filtered_df["target_audience"].isin(audiences)]
    
    # Scatter plot
    scatter_fig = px.scatter(
        filtered_df,
        x='impressions',
        y='revenue_usd',
        color='campaign_type',
        title='Revenue (USD) vs Impressions',
        labels={'impressions': 'Impressions', 'revenue_usd': 'Revenue (USD)'},
        opacity=0.6,
        hover_data=['source', 'campaign_type', 'roi']
    )
    scatter_fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02))
    
    # Revenue distribution
    dist_fig = px.histogram(
        filtered_df,
        x='revenue_usd',
        title='Revenue Distribution (USD)',
        labels={'revenue_usd': 'Revenue (USD)'},
        color='source',
        opacity=0.7,
        nbins=30
    )
    dist_fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02))
    
    # Engagement box plot
    box_fig = px.box(
        filtered_df,
        x='campaign_type',
        y='engagement_score',
        color='campaign_type',
        title='Engagement Score by Campaign Type',
        labels={'engagement_score': 'Engagement Score', 'campaign_type': 'Campaign Type'}
    )
    box_fig.update_layout(showlegend=False)
    
    return scatter_fig, dist_fig, box_fig


@app.callback(
    [Output('platform-filter', 'value'),
     Output('campaign-type-filter', 'value'),
     Output('duration-slider', 'value'),
     Output('audience-filter', 'value')],
    Input('reset-filters', 'n_clicks'),
    prevent_initial_call=True
)
def reset_filters(n_clicks):
    return 'all', 'all', [duration_min, duration_max], sorted(df["target_audience"].unique())[:2]

# ============== SERVER ==============
server = app.server

if __name__ == '__main__':
    app.run(debug=True, port=8050)