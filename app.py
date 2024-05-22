import os
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
import json

app = Flask(__name__)

def get_teams_besoccer(api_key, competition_id):
    url = f"https://apiclient.besoccerapps.com/scripts/api/api.php?key={api_key}&format=json&req=teams&league={competition_id}&tz=Europe/Madrid"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data

def get_league_table_besoccer(api_key, competition_id, group_id=None):
    url = f"https://apiclient.besoccerapps.com/scripts/api/api.php?key={api_key}&format=json&req=tables&league={competition_id}"
    if group_id:
        url += f"&group={group_id}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data

def get_matches_world(api_key):
    url = 'https://api.football-data.org/v4/matches/'
    headers = {'X-Auth-Token': api_key}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data

def get_matches_summary(api_key):
    url = f"https://www.scorebat.com/video-api/v3/feed/?token={api_key}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data

@app.route('/subscribers')
def subscribers():
    subscribers = []
    if os.path.exists('subscribers.json'):
        with open('subscribers.json', 'r') as f:
            for line in f:
                subscribers.append(json.loads(line))
    return render_template('subscribers.html', subscribers=subscribers)

@app.route('/')
def index():
    besoccer_api_key = os.getenv("keyfut")
    competition_id = 1
    group_id = 1
    league_table_data = get_league_table_besoccer(besoccer_api_key, competition_id, group_id)
    return render_template('index.html', league_table_data=league_table_data)

@app.route('/teams', methods=['GET'])
def team_list():
    besoccer_api_key = os.getenv("keyfut")
    competition_id = 1
    teams_data_besoccer = get_teams_besoccer(besoccer_api_key, competition_id)

    name_filter = request.args.get('name')
    if name_filter:
        filtered_teams = [team for team in teams_data_besoccer['team'] if name_filter.lower() in team['nameShow'].lower()]
        if not filtered_teams:
            error_message = f"No se encontró ningún equipo con el nombre '{name_filter}'."
            return render_template('team_list.html', teams=None, error_message=error_message)
    else:
        filtered_teams = teams_data_besoccer['team']

    return render_template('team_list.html', teams=filtered_teams, error_message=None)

@app.route('/league_table')
def league_table():
    besoccer_api_key = os.getenv("keyfut")
    competition_id = 1
    group_id = 1
    league_table_data_besoccer = get_league_table_besoccer(besoccer_api_key, competition_id, group_id)

    for team in league_table_data_besoccer['table']:
        team['form'] = list(team['form'].lower())

    return render_template('league_table.html', league_table_data_besoccer=league_table_data_besoccer)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    if email and "@" in email:  # Simple email validation
        with open('subscribers.json', 'a') as f:
            json.dump({'email': email}, f)
            f.write("\n")
    return redirect(url_for('index'))

@app.route('/world_matches')
def world_matches():
    football_data_api_key = os.getenv("keyfut1")
    matches_world_data = get_matches_world(football_data_api_key)
    matches = matches_world_data.get('matches', [])
    return render_template('world_matches.html', matches=matches)

@app.route('/matches_summary')
def matches_summary():
    api_key = os.getenv("keyfut2")
    if not api_key:
        return "API key not found", 500
    data = get_matches_summary(api_key)['response']

    # Filtrar los datos para solo incluir "Highlights"
    filtered_data = []
    for match in data:
        for video in match['videos']:
            if "Highlights" in video['title']:
                filtered_data.append({
                    'title': match['title'],
                    'competition': match['competition'],
                    'matchviewUrl': match['matchviewUrl'],
                    'thumbnail': match['thumbnail'],
                    'date': match['date'],
                    'video': video  # Solo el video de "Highlights"
                })
                break  # Solo añadir el primer "Highlights" que encuentres

    return render_template('matches_summary.html', matches_summary_data=filtered_data)

@app.route('/team_details/<short_name>')
def team_details(short_name):
    football_data_api_key = os.getenv("keyfut1")
    if not football_data_api_key:
        return "API key not found", 500

    url = f'https://api.football-data.org/v4/competitions/2014/teams'
    headers = {'X-Auth-Token': football_data_api_key}
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Esto lanzará una excepción si la respuesta no es 200 OK
    data = response.json()

    team = next((team for team in data['teams'] if team['tla'] == short_name), None)
    if team:
        return render_template('team_details.html', team=team)
    else:
        return render_template('team_details.html', error_message=f"No se encontraron detalles para el equipo con short_name '{short_name}'")

@app.route('/advanced_search', methods=['GET'])
def advanced_search():
    # Obtener los parámetros de búsqueda del formulario
    competition = request.args.get('competition')
    season = request.args.get('season')
    date_from = request.args.get('dateFrom')
    date_to = request.args.get('dateTo')
    status = request.args.get('status')

    # Comprobación para asegurarse de que al menos un campo de búsqueda esté lleno
    if not any([competition, season, date_from, date_to, status]):
        error_message = "*Debes de rellenar los campos de fecha para la consulta."
        return render_template('advanced_search.html', error_message=error_message)

    headers = {
        'X-Auth-Token': os.getenv("keyfut1")
    }

    params = {}
    if date_from:
        params['dateFrom'] = date_from
    if date_to:
        params['dateTo'] = date_to
    if status:
        params['status'] = status

    response = requests.get('https://api.football-data.org/v4/matches', headers=headers, params=params)
    response.raise_for_status()
    raw_matches = response.json().get('matches', [])

    if not raw_matches:
        error_message = "No se han encontrado partidos con los datos introducidos."
        return render_template('search_results.html', matches=[], error_message=error_message)

    matches = []
    for match in raw_matches:
        home_score = match['score']['fullTime']['home']
        away_score = match['score']['fullTime']['away']
        if home_score is not None and away_score is not None:
            result = f"{home_score}-{away_score}"
        else:
            result = 'Not available'

        match_data = {
            'local_shield': match['homeTeam']['crest'],
            'visitor_shield': match['awayTeam']['crest'],
            'local': match['homeTeam']['name'],
            'visitor': match['awayTeam']['name'],
            'competition_name': match['competition']['name'],
            'date': match['utcDate'][:10],  # Assuming 'utcDate' is in ISO 8601 format
            'hour': match['utcDate'][11:13],  # Extracting hour
            'minute': match['utcDate'][14:16],  # Extracting minute
            'result': result,
            'status': match['status']
        }
        matches.append(match_data)

    return render_template('search_results.html', matches=matches, error_message=None)

if __name__ == "__main__":
    app.run(debug=True)