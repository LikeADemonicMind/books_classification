import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px


# Charger les logs
def load_logs():
    # Assurez-vous que 'date' est converti en datetime
    logs = pd.read_csv("predictions_log.csv")
    logs["date"] = pd.to_datetime(logs["date"], errors="coerce")  # Convertir en datetime
    return logs


# Créer une application Dash
app = dash.Dash(__name__, requests_pathname_prefix="/dashboard/")

# Charger les données initiales
logs = load_logs()

# Mise en page de l'application
app.layout = html.Div([
    html.H1("Tableau de bord des prédictions de genres de livres", style={"text-align": "center"}),
    
    dcc.DatePickerSingle(
        id="date-picker",
        min_date_allowed=logs["date"].min().date(),
        max_date_allowed=logs["date"].max().date(),
        placeholder="Sélectionnez une date",
    ),

    html.Button("Voir tous les jours", id="reset-button", n_clicks=0, style={"margin-left": "10px"}),
    
    html.Div(id="output-date", style={"margin-top": "20px"}),

    dcc.Graph(id="daily-requests-plot"),
    dcc.Graph(id="genre-pie-chart"),

    html.H3("Données des prédictions", style={"text-align": "center"}),
    dash_table.DataTable(id="logs-table",
                         columns=[
                             {"name": col, "id": col} for col in ["date", "input_summary", "predicted_genre", "elapsed_time"]
                         ],
                         style_table={"overflowX": "auto"},
                         style_cell={"textAlign": "left"}),
])


# Callback pour mettre à jour les graphiques et le tableau
@app.callback(
    [Output("daily-requests-plot", "figure"),
     Output("genre-pie-chart", "figure"),
     Output("logs-table", "data"),
     Output("date-picker", "date")],
    [Input("date-picker", "date"),
     Input("reset-button", "n_clicks")],
    [State("date-picker", "date")]
)
def update_graphs(selected_date, reset_clicks, current_date):
    # Charger les logs mis à jour
    logs = load_logs()

    # Vérifier si le bouton reset est cliqué
    if reset_clicks > 0:
        selected_date = None

    # Filtrer par date si une date est sélectionnée
    if selected_date:
        logs = logs[logs["date"].dt.date == pd.to_datetime(selected_date).date()]

    # Graphique des requêtes par jour
    requests_per_day = logs["date"].dt.date.value_counts().sort_index()
    daily_requests_fig = px.bar(
        x=requests_per_day.index,
        y=requests_per_day.values,
        labels={"x": "Date", "y": "Nombre de requêtes"},
        title="Nombre de requêtes par jour",
    )

    # Graphique en camembert pour les genres prédits
    genre_counts = logs["predicted_genre"].value_counts()
    genre_pie_chart = px.pie(
        values=genre_counts.values,
        names=genre_counts.index,
        title="Répartition des genres prédits",
    )

    # Préparer les données pour le tableau
    table_data = logs[["date", "input_summary", "predicted_genre", "elapsed_time"]].to_dict("records")

    return daily_requests_fig, genre_pie_chart, table_data, None if reset_clicks > 0 else selected_date


# Exporter l'application Dash
dash_app = app.server
