import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


df = pd.read_csv("stocks.csv")
stocks = ['AMZN','GOOGL','META','MSFT','NVDA']


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])



app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Stock prices dashboard", className="text-center"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id="stock_selector", options=[{"label":x, "value":x} for x in stocks], value = stocks[0]),
            dcc.Graph(id="stock_selector_graph", figure={})
        ], width=6),
        dbc.Col([
            dcc.Dropdown(id="multi_selector", options=[{"label":x, "value":x} for x in stocks], value = [stocks[0]], multi=True),
            dcc.Graph(id="comparison_graph", figure={})
        ], width=6),

    ]),
    dbc.Row([

    ]),

])


@app.callback(
        Output(component_id="stock_selector_graph", component_property="figure"),
        Input("stock_selector", "value")
)
def update_graph(stock):
    fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                        open=df[f'Open_{stock}'], high=df[f'High_{stock}'],
                        low=df[f'Low_{stock}'], close=df[f'Close_{stock}'])
                        ])
    fig.update_layout(xaxis_rangeslider_visible=False)

    return fig



@app.callback(
        Output(component_id="comparison_graph", component_property="figure"),
        Input("multi_selector", "value")
)
def update_graph(stocks):
    fig = go.Figure()
    for stock in stocks:
        fig.add_trace(go.Scatter(x=df['Date'], y=df[f'Close_{stock}'], mode='lines', name=stock))

    fig.update_layout(xaxis_rangeslider_visible=False)
    return fig



if __name__ == "__main__":
    app.run(debug=True, port=8070)




# df.head()



# stock = "GOOGL"
# fig = go.Figure(data=[go.Candlestick(x=df['Date'],
#                         open=df[f'Open_{stock}'], high=df[f'High_{stock}'],
#                         low=df[f'Low_{stock}'], close=df[f'Close_{stock}'])
#                         ])
# fig.update_layout(xaxis_rangeslider_visible=False)

# fig.show()


