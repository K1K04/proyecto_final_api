import os
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
import json

app = Flask(__name__)

def get_teams_besoccer(api_key, competition_id):
    url = f"https://apiclient.besoccerapps.com/scripts/api/api.php?key={api_key}&format=json&req=teams&league={competition_id}&tz=Europe/Madrid"
    response = requests.get(url)
    data = response.json()
    return data

def get_league_table_besoccer(api_key, competition_id, group_id=None):
    url = f"https://apiclient.besoccerapps.com/scripts/api/api.php?key={api_key}&format=json&req=tables&league={competition_id}"
    if group_id:
        url += f"&group={group_id}"
    response = requests.get(url)
    data = response.json()
    return data

def get_matches_world(api_key):
    url = 'https://api.football-data.org/v4/matches/'
    headers = {'X-Auth-Token': api_key}
    response = requests.get(url, headers=headers)
    data = response.json()
    return data

def get_matches_summary(api_key):
    url = f"https://www.scorebat.com/video-api/v3/feed/?token={api_key}"
    response = requests.get(url)
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
        teams = [team for team in teams_data_besoccer['team'] if name_filter.lower() in team['nameShow'].lower()]
    else:
        teams = teams_data_besoccer['team']

    return render_template('team_list.html', teams=teams)

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
    if email:
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
    api_key = "MTU1NTA5XzE3MTQ0NjQxMTJfMmIzNTIzY2JmZDczM2Y4ZTdkN2MyZjQ2OTZiNjFlZDIwNjRhMWE2MA=="
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

if __name__ == "__main__":
    app.run(debug=True)