import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import requests

# Charger les données
data = pd.read_csv('data/Data_Department.csv', delimiter=';')
data['annais'] = data['annais'].astype(int)
data['dpt'] = data['dpt'].astype(str).str.zfill(2)  # S'assurer que les codes des départements sont des chaînes de caractères de deux chiffres

# URL du GeoJSON des départements français
geojson_url = 'https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson'
geojson = requests.get(geojson_url).json()

# Initialiser l'application Dash
app = Dash(__name__)

# Fonction pour générer les options de dropdown
def generate_dropdown_options(column):
    return [{'label': value, 'value': value} for value in column.unique()]

# Fonction de filtre des données
def filter_data(name, sex, depts, years):
    filtered = data[(data['preusuel'] == name) & (data['sexe'] == sex) &
                    (data['annais'] >= years[0]) & (data['annais'] <= years[1])]
    return filtered[filtered['dpt'].isin(depts)] if depts else filtered

# Layout de l'application
app.layout = html.Div([
    html.H1("Graphique des naissances par année, sexe et département"),
    dcc.Dropdown(id='name-dropdown', options=generate_dropdown_options(data['preusuel']),
                 value=data['preusuel'].unique()[0], clearable=False),
    dcc.RadioItems(id='sex-radio', options=[{'label': 'Masculin', 'value': 1},
                                            {'label': 'Féminin', 'value': 2}],
                   value=1, labelStyle={'display': 'inline-block'}),
    dcc.Dropdown(id='dept-dropdown', options=generate_dropdown_options(data['dpt']),
                 value=[], multi=True),
    dcc.RangeSlider(id='year-slider', min=data['annais'].min(), max=data['annais'].max(),
                    step=1, value=[data['annais'].min(), data['annais'].max()],
                    marks={str(year): str(year) for year in range(data['annais'].min(), data['annais'].max() + 1, 5)}),
    dcc.Graph(id='birth-graph'),
    dcc.Graph(id='map-graph')
])

# Callback pour mettre à jour le graphique
@app.callback(
    Output('birth-graph', 'figure'),
    [Input('name-dropdown', 'value'),
     Input('sex-radio', 'value'),
     Input('dept-dropdown', 'value'),
     Input('year-slider', 'value')]
)
def update_graph(name, sex, depts, years):
    filtered_data = filter_data(name, sex, depts, years)
    birth_count = filtered_data.groupby('annais')['nombre'].sum().reset_index()
    title = f"Nombre de naissances pour le prénom {name} ({'Masculin' if sex == 1 else 'Féminin'}) par année"
    title += ' dans les départements sélectionnés' if depts else ' (tous départements)'

    fig = px.line(birth_count, x='annais', y='nombre', title=title)
    fig.update_layout(xaxis_title="Année", yaxis_title="Nombre de naissances")
    return fig

# Callback pour mettre à jour la carte
@app.callback(
    Output('map-graph', 'figure'),
    [Input('dept-dropdown', 'value')]
)
def update_map(depts):
    filtered_data = data[data['dpt'].isin(depts)] if depts else data
    dept_count = filtered_data.groupby('dpt')['nombre'].sum().reset_index()

    fig = px.choropleth(dept_count, geojson=geojson, locations='dpt', featureidkey="properties.code", color='nombre',
                        hover_name='dpt', color_continuous_scale="Viridis",
                        title="Nombre de naissances par département")

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, geo=dict(
        projection_scale=5,
        center=dict(lat=46.603354, lon=1.888334)
    ))
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
