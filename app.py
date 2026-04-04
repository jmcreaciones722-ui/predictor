from flask import Flask, render_template_string, jsonify, request, session
import requests
from datetime import datetime, timedelta
import random
import threading
import time
import schedule
import hashlib
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

API_KEY = "67a8f29d5a4de82b616e920824663e3a"

# ========== BASE DE DATOS DE USUARIOS ==========
USUARIOS_DB = {
    'admin@predictor.com': {
        'password': hashlib.sha256('admin123'.encode()).hexdigest(),
        'nombre': 'Administrador',
        'plan': 'admin',
        'fecha_registro': datetime.now().isoformat(),
        'ultimo_acceso': datetime.now().isoformat(),
        'suscripcion_valida_hasta': (datetime.now() + timedelta(days=3650)).isoformat(),
        'activo': True
    },
    'demo@predictor.com': {
        'password': hashlib.sha256('demo123'.encode()).hexdigest(),
        'nombre': 'Usuario Demo',
        'plan': 'free',
        'fecha_registro': datetime.now().isoformat(),
        'ultimo_acceso': datetime.now().isoformat(),
        'suscripcion_valida_hasta': (datetime.now() + timedelta(days=7)).isoformat(),
        'activo': True
    }
}

SUSCRIPCIONES = {
    'free': {'nombre': 'Gratuito', 'max_consultas_dia': 10, 'precio': 0},
    'premium': {'nombre': 'Premium', 'max_consultas_dia': 999, 'precio': 9.99},
    'profesional': {'nombre': 'Profesional', 'max_consultas_dia': 9999, 'precio': 29.99},
    'admin': {'nombre': 'Administrador', 'max_consultas_dia': 99999, 'precio': 0}
}

# ========== LOGOS OFICIALES - MAPEO DIRECTO ==========

# NBA Logos
NBA_LOGOS = {
    'Hawks': 'https://cdn.nba.com/logos/nba/1610612737/primary/L/logo.svg',
    'Celtics': 'https://cdn.nba.com/logos/nba/1610612738/primary/L/logo.svg',
    'Nets': 'https://cdn.nba.com/logos/nba/1610612751/primary/L/logo.svg',
    'Hornets': 'https://cdn.nba.com/logos/nba/1610612766/primary/L/logo.svg',
    'Bulls': 'https://cdn.nba.com/logos/nba/1610612741/primary/L/logo.svg',
    'Cavaliers': 'https://cdn.nba.com/logos/nba/1610612739/primary/L/logo.svg',
    'Mavericks': 'https://cdn.nba.com/logos/nba/1610612742/primary/L/logo.svg',
    'Nuggets': 'https://cdn.nba.com/logos/nba/1610612743/primary/L/logo.svg',
    'Pistons': 'https://cdn.nba.com/logos/nba/1610612765/primary/L/logo.svg',
    'Warriors': 'https://cdn.nba.com/logos/nba/1610612744/primary/L/logo.svg',
    'Rockets': 'https://cdn.nba.com/logos/nba/1610612745/primary/L/logo.svg',
    'Pacers': 'https://cdn.nba.com/logos/nba/1610612754/primary/L/logo.svg',
    'Clippers': 'https://cdn.nba.com/logos/nba/1610612746/primary/L/logo.svg',
    'Lakers': 'https://cdn.nba.com/logos/nba/1610612747/primary/L/logo.svg',
    'Grizzlies': 'https://cdn.nba.com/logos/nba/1610612763/primary/L/logo.svg',
    'Heat': 'https://cdn.nba.com/logos/nba/1610612748/primary/L/logo.svg',
    'Bucks': 'https://cdn.nba.com/logos/nba/1610612749/primary/L/logo.svg',
    'Timberwolves': 'https://cdn.nba.com/logos/nba/1610612750/primary/L/logo.svg',
    'Pelicans': 'https://cdn.nba.com/logos/nba/1610612740/primary/L/logo.svg',
    'Knicks': 'https://cdn.nba.com/logos/nba/1610612752/primary/L/logo.svg',
    'Thunder': 'https://cdn.nba.com/logos/nba/1610612760/primary/L/logo.svg',
    'Magic': 'https://cdn.nba.com/logos/nba/1610612753/primary/L/logo.svg',
    '76ers': 'https://cdn.nba.com/logos/nba/1610612755/primary/L/logo.svg',
    'Suns': 'https://cdn.nba.com/logos/nba/1610612756/primary/L/logo.svg',
    'Trail Blazers': 'https://cdn.nba.com/logos/nba/1610612757/primary/L/logo.svg',
    'Kings': 'https://cdn.nba.com/logos/nba/1610612758/primary/L/logo.svg',
    'Spurs': 'https://cdn.nba.com/logos/nba/1610612759/primary/L/logo.svg',
    'Raptors': 'https://cdn.nba.com/logos/nba/1610612761/primary/L/logo.svg',
    'Jazz': 'https://cdn.nba.com/logos/nba/1610612762/primary/L/logo.svg',
    'Wizards': 'https://cdn.nba.com/logos/nba/1610612764/primary/L/logo.svg',
}

# MLB Logos (ESPN)
MLB_LOGOS = {
    'Diamondbacks': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/ari.png',
    'Braves': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/atl.png',
    'Orioles': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/bal.png',
    'Red Sox': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/bos.png',
    'Cubs': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/chc.png',
    'White Sox': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/chw.png',
    'Reds': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/cin.png',
    'Guardians': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/cle.png',
    'Rockies': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/col.png',
    'Tigers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/det.png',
    'Astros': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/hou.png',
    'Royals': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/kc.png',
    'Angels': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/laa.png',
    'Dodgers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/lad.png',
    'Marlins': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/mia.png',
    'Brewers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/mil.png',
    'Twins': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/min.png',
    'Mets': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/nym.png',
    'Yankees': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/nyy.png',
    'Athletics': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/oak.png',
    'Phillies': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/phi.png',
    'Pirates': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/pit.png',
    'Padres': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/sd.png',
    'Giants': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/sf.png',
    'Mariners': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/sea.png',
    'Cardinals': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/stl.png',
    'Rays': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/tb.png',
    'Rangers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/tex.png',
    'Blue Jays': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/tor.png',
    'Nationals': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/wsh.png',
}

# NHL Logos (ESPN)
NHL_LOGOS = {
    'Ducks': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/ana.png',
    'Coyotes': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/ari.png',
    'Bruins': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/bos.png',
    'Sabres': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/buf.png',
    'Flames': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/cgy.png',
    'Hurricanes': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/car.png',
    'Blackhawks': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/chi.png',
    'Avalanche': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/col.png',
    'Blue Jackets': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/cbj.png',
    'Stars': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/dal.png',
    'Red Wings': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/det.png',
    'Oilers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/edm.png',
    'Panthers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/fla.png',
    'Kings': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/la.png',
    'Wild': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/min.png',
    'Canadiens': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/mon.png',
    'Predators': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/nsh.png',
    'Devils': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/nj.png',
    'Islanders': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/nyi.png',
    'Rangers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/nyr.png',
    'Senators': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/ott.png',
    'Flyers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/phi.png',
    'Penguins': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/pit.png',
    'Sharks': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/sj.png',
    'Kraken': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/sea.png',
    'Blues': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/stl.png',
    'Lightning': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/tb.png',
    'Maple Leafs': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/tor.png',
    'Canucks': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/van.png',
    'Golden Knights': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/vgk.png',
    'Capitals': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/wsh.png',
    'Jets': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nhl/500/wpg.png',
}

# NFL Logos (ESPN)
NFL_LOGOS = {
    'Cardinals': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/ari.png',
    'Falcons': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/atl.png',
    'Ravens': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/bal.png',
    'Bills': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/buf.png',
    'Panthers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/car.png',
    'Bears': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/chi.png',
    'Bengals': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/cin.png',
    'Browns': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/cle.png',
    'Cowboys': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/dal.png',
    'Broncos': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/den.png',
    'Lions': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/det.png',
    'Packers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/gb.png',
    'Texans': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/hou.png',
    'Colts': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/ind.png',
    'Jaguars': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/jax.png',
    'Chiefs': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/kc.png',
    'Raiders': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/lv.png',
    'Chargers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/lac.png',
    'Rams': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/lar.png',
    'Dolphins': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/mia.png',
    'Vikings': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/min.png',
    'Patriots': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/ne.png',
    'Saints': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/no.png',
    'Giants': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/nyg.png',
    'Jets': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/nyj.png',
    'Eagles': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/phi.png',
    'Steelers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/pit.png',
    '49ers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/sf.png',
    'Seahawks': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/sea.png',
    'Buccaneers': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/tb.png',
    'Titans': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/ten.png',
    'Commanders': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/wsh.png',
}

# ========== LOGOS DE FÚTBOL (La Liga, Premier League, Serie A, etc.) ==========
# Usando CDNs oficiales

def get_la_liga_logo(team_name):
    """Logos oficiales de La Liga"""
    logos = {
        'Real Madrid': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/86.png',
        'Barcelona': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/83.png',
        'Atletico Madrid': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/78.png',
        'Sevilla': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/105.png',
        'Real Betis': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/84.png',
        'Real Sociedad': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/104.png',
        'Villarreal': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/111.png',
        'Athletic Bilbao': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/80.png',
        'Valencia': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/110.png',
        'Osasuna': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/99.png',
        'Celta Vigo': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/87.png',
        'Getafe': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/91.png',
        'Elche': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/2029.png',
        'Elche CF': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/2029.png',
        'Espanyol': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/89.png',
        'Rayo Vallecano': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/103.png',
        'Mallorca': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/95.png',
        'Granada': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/92.png',
        'Almeria': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/77.png',
        'Cadiz': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/85.png',
        'Girona': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/2031.png',
        'Las Palmas': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/94.png',
        'Alaves': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/76.png',
    }
    return logos.get(team_name)

def get_premier_league_logo(team_name):
    """Logos oficiales de Premier League"""
    logos = {
        'Manchester United': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/360.png',
        'Manchester City': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/382.png',
        'Liverpool': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/364.png',
        'Arsenal': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/359.png',
        'Chelsea': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/363.png',
        'Tottenham': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/367.png',
        'Tottenham Hotspur': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/367.png',
        'Newcastle': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/361.png',
        'Newcastle United': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/361.png',
        'Aston Villa': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/358.png',
        'West Ham': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/370.png',
        'West Ham United': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/370.png',
        'Brighton': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/373.png',
        'Brentford': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/2134.png',
        'Fulham': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/368.png',
        'Crystal Palace': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/365.png',
        'Wolves': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/372.png',
        'Everton': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/369.png',
        'Nottingham Forest': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/380.png',
        'Bournemouth': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/371.png',
        'Leicester': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/376.png',
        'Leeds': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/375.png',
        'Southampton': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/379.png',
    }
    return logos.get(team_name)

def get_serie_a_logo(team_name):
    """Logos oficiales de Serie A"""
    logos = {
        'Juventus': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/114.png',
        'AC Milan': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/1108.png',
        'Inter Milan': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/110.png',
        'Roma': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/119.png',
        'AS Roma': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/119.png',
        'Lazio': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/115.png',
        'Napoli': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/118.png',
        'Fiorentina': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/112.png',
        'Atalanta': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/111.png',
        'Bologna': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/113.png',
        'Torino': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/122.png',
        'Sassuolo': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/121.png',
        'Udinese': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/124.png',
        'Empoli': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/1119.png',
        'Verona': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/126.png',
        'Hellas Verona': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/126.png',
        'Cagliari': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/117.png',
        'Lecce': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/116.png',
        'Monza': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11103.png',
        'Cremonese': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11099.png',
        'Salernitana': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11097.png',
    }
    return logos.get(team_name)

def get_bundesliga_logo(team_name):
    """Logos oficiales de Bundesliga"""
    logos = {
        'Bayern Munich': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/132.png',
        'Bayern München': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/132.png',
        'Borussia Dortmund': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/134.png',
        'RB Leipzig': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/3258.png',
        'Bayer Leverkusen': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/133.png',
        'Union Berlin': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/138.png',
        'Freiburg': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/136.png',
        'Mainz': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/140.png',
        'Wolfsburg': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/143.png',
        'Monchengladbach': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/141.png',
        'Stuttgart': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/142.png',
        'Augsburg': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/131.png',
        'Bochum': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11107.png',
        'Hertha Berlin': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/137.png',
        'Schalke': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/139.png',
        'Hoffenheim': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/145.png',
    }
    return logos.get(team_name)

def get_ligue1_logo(team_name):
    """Logos oficiales de Ligue 1"""
    logos = {
        'Paris Saint-Germain': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/160.png',
        'PSG': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/160.png',
        'Marseille': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/158.png',
        'Lyon': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/155.png',
        'Monaco': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/159.png',
        'Lille': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/157.png',
        'Rennes': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/161.png',
        'Nice': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/156.png',
        'Lens': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/154.png',
        'Nantes': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/164.png',
        'Strasbourg': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/165.png',
        'Montpellier': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/163.png',
        'Bordeaux': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/151.png',
        'Toulouse': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/167.png',
        'Reims': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/166.png',
        'Clermont': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11112.png',
        'Brest': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/152.png',
        'Le Havre': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11113.png',
        'Metz': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/11114.png',
    }
    return logos.get(team_name)

def get_soccer_logo(team_name, liga):
    """Obtiene logo oficial de fútbol según la liga"""
    
    # Limpiar nombre
    clean_name = team_name.replace('FC', '').replace('CF', '').replace('SC', '').strip()
    
    # Buscar por liga
    if liga == 'La Liga':
        logo = get_la_liga_logo(clean_name)
        if logo: return logo
        logo = get_la_liga_logo(team_name)
        if logo: return logo
    
    elif liga == 'Premier League':
        logo = get_premier_league_logo(clean_name)
        if logo: return logo
        logo = get_premier_league_logo(team_name)
        if logo: return logo
    
    elif liga == 'Serie A':
        logo = get_serie_a_logo(clean_name)
        if logo: return logo
        logo = get_serie_a_logo(team_name)
        if logo: return logo
    
    elif liga == 'Bundesliga':
        logo = get_bundesliga_logo(clean_name)
        if logo: return logo
        logo = get_bundesliga_logo(team_name)
        if logo: return logo
    
    elif liga == 'Ligue 1':
        logo = get_ligue1_logo(clean_name)
        if logo: return logo
        logo = get_ligue1_logo(team_name)
        if logo: return logo
    
    return None

def get_nba_logo(team_name):
    name_parts = team_name.split()
    simple_name = name_parts[-1] if len(name_parts) > 1 else team_name
    return NBA_LOGOS.get(simple_name)

def get_mlb_logo(team_name):
    name_parts = team_name.split()
    simple_name = name_parts[-1] if len(name_parts) > 1 else team_name
    return MLB_LOGOS.get(simple_name)

def get_nhl_logo(team_name):
    name_parts = team_name.split()
    simple_name = name_parts[-1] if len(name_parts) > 1 else team_name
    return NHL_LOGOS.get(simple_name)

def get_nfl_logo(team_name):
    name_parts = team_name.split()
    simple_name = name_parts[-1] if len(name_parts) > 1 else team_name
    return NFL_LOGOS.get(simple_name)

def get_logo_url(team_name, liga):
    """Obtiene URL del logo oficial del equipo"""
    
    if liga == 'NBA':
        return get_nba_logo(team_name)
    elif liga == 'MLB':
        return get_mlb_logo(team_name)
    elif liga == 'NHL':
        return get_nhl_logo(team_name)
    elif liga == 'NFL':
        return get_nfl_logo(team_name)
    elif liga in ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1',
                  'Champions League', 'Brasileirão', 'Liga Argentina', 'Liga MX', 'MLS']:
        return get_soccer_logo(team_name, liga)
    
    return None

# ========== ESTADÍSTICAS ==========
ESTADISTICAS_EQUIPOS = {
    'Charlotte Hornets': {'record': '7-3', 'ppg': 119.7, 'opp_ppg': 105.1},
    'Indiana Pacers': {'record': '3-7', 'ppg': 121.4, 'opp_ppg': 125.3},
    'Philadelphia 76ers': {'record': '6-4', 'ppg': 115.8, 'opp_ppg': 113.2},
    'Minnesota Timberwolves': {'record': '5-5', 'ppg': 112.4, 'opp_ppg': 111.9},
    'Atlanta Hawks': {'record': '8-2', 'ppg': 122.1, 'opp_ppg': 114.3},
    'Brooklyn Nets': {'record': '2-8', 'ppg': 108.7, 'opp_ppg': 119.4},
    'New York Knicks': {'record': '7-3', 'ppg': 118.2, 'opp_ppg': 110.5},
    'Chicago Bulls': {'record': '4-6', 'ppg': 113.5, 'opp_ppg': 115.8},
    'Boston Celtics': {'record': '9-1', 'ppg': 121.3, 'opp_ppg': 108.7},
    'Milwaukee Bucks': {'record': '6-4', 'ppg': 117.8, 'opp_ppg': 114.2},
    'Houston Rockets': {'record': '8-2', 'ppg': 120.3, 'opp_ppg': 111.6},
    'Utah Jazz': {'record': '2-8', 'ppg': 109.8, 'opp_ppg': 120.1},
    'Toronto Raptors': {'record': '8-2', 'ppg': 118.9, 'opp_ppg': 110.3},
    'Memphis Grizzlies': {'record': '4-6', 'ppg': 114.2, 'opp_ppg': 116.7},
    'Orlando Magic': {'record': '7-3', 'ppg': 116.5, 'opp_ppg': 109.8},
    'Dallas Mavericks': {'record': '4-6', 'ppg': 111.3, 'opp_ppg': 113.9},
    'New Orleans Pelicans': {'record': '6-4', 'ppg': 117.4, 'opp_ppg': 114.6},
    'Sacramento Kings': {'record': '5-5', 'ppg': 115.1, 'opp_ppg': 114.8},
}

# ========== LIGAS ==========
LIGAS = {
    'NBA': {'key': 'basketball_nba', 'deporte': 'baloncesto', 'logo': '🏀', 'premium': False},
    'NCAA Basketball': {'key': 'basketball_ncaab', 'deporte': 'baloncesto', 'logo': '🏀', 'premium': True},
    'MLB': {'key': 'baseball_mlb', 'deporte': 'beisbol', 'logo': '⚾', 'premium': False},
    'NHL': {'key': 'icehockey_nhl', 'deporte': 'hockey', 'logo': '🏒', 'premium': True},
    'NFL': {'key': 'americanfootball_nfl', 'deporte': 'football', 'logo': '🏈', 'premium': True},
    'NCAA Football': {'key': 'americanfootball_ncaaf', 'deporte': 'football', 'logo': '🏈', 'premium': True},
    'Premier League': {'key': 'soccer_epl', 'deporte': 'futbol', 'logo': '⚽', 'premium': False},
    'La Liga': {'key': 'soccer_spain_la_liga', 'deporte': 'futbol', 'logo': '⚽', 'premium': True},
    'Serie A': {'key': 'soccer_italy_serie_a', 'deporte': 'futbol', 'logo': '⚽', 'premium': True},
    'Bundesliga': {'key': 'soccer_germany_bundesliga', 'deporte': 'futbol', 'logo': '⚽', 'premium': True},
    'Ligue 1': {'key': 'soccer_france_ligue_one', 'deporte': 'futbol', 'logo': '⚽', 'premium': True},
    'Champions League': {'key': 'soccer_uefa_champs_league', 'deporte': 'futbol', 'logo': '🏆', 'premium': True},
    'Brasileirão': {'key': 'soccer_brazil_campeonato', 'deporte': 'futbol', 'logo': '⚽', 'premium': True},
    'Liga Argentina': {'key': 'soccer_argentina_primera_division', 'deporte': 'futbol', 'logo': '⚽', 'premium': True},
    'Liga MX': {'key': 'soccer_mexico_liga_mx', 'deporte': 'futbol', 'logo': '⚽', 'premium': True},
    'MLS': {'key': 'soccer_usa_mls', 'deporte': 'futbol', 'logo': '⚽', 'premium': True},
}

# ========== FUNCIONES DE DATOS ==========
def get_real_data(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {'apiKey': API_KEY, 'regions': 'us', 'markets': 'h2h,totals', 'oddsFormat': 'american'}
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def convert_odds_to_prob(odds):
    if odds is None:
        return 33.33
    if odds < 0:
        return (abs(odds) / (abs(odds) + 100)) * 100
    else:
        return (100 / (odds + 100)) * 100

def obtener_estadisticas_equipo(team_name):
    return ESTADISTICAS_EQUIPOS.get(team_name)

def generar_prediccion_final(home, away, p_home, p_away, deporte):
    stats_home = obtener_estadisticas_equipo(home)
    stats_away = obtener_estadisticas_equipo(away)
    
    if deporte == 'baloncesto':
        pts_home = stats_home['ppg'] if stats_home and 'ppg' in stats_home else 110
        pts_away = stats_away['ppg'] if stats_away and 'ppg' in stats_away else 110
        prob_factor = (p_home - p_away) / 100
        margin = int(prob_factor * 20)
        
        if p_home > p_away:
            pts_home = int(pts_home + margin + random.randint(-5, 8))
            pts_away = int(pts_away - margin + random.randint(-8, 5))
        else:
            pts_home = int(pts_home - abs(margin) + random.randint(-8, 5))
            pts_away = int(pts_away + abs(margin) + random.randint(-5, 8))
        
        pts_home = max(95, min(135, pts_home))
        pts_away = max(95, min(135, pts_away))
        return f"{pts_home} - {pts_away}"
    
    elif deporte == 'beisbol':
        return f"{random.randint(2,7)} - {random.randint(1,5)}"
    
    elif deporte == 'futbol':
        if p_home > 55:
            return f"{random.randint(1,3)} - {random.randint(0,1)}"
        elif p_away > 55:
            return f"{random.randint(0,1)} - {random.randint(1,3)}"
        else:
            return f"{random.randint(0,2)} - {random.randint(0,2)}"
    
    elif deporte == 'hockey':
        g1 = random.randint(2, 5)
        g2 = random.randint(1, 4)
        if p_home > p_away:
            g1 += random.randint(0, 2)
        else:
            g2 += random.randint(0, 2)
        return f"{g1} - {g2}"
    
    elif deporte == 'football':
        if p_home > p_away:
            return f"{random.choice([24,27,28,31])} - {random.choice([17,20,21])}"
        else:
            return f"{random.choice([17,20,21])} - {random.choice([24,27,28,31])}"
    
    return "N/A"

# ========== AUTENTICACIÓN ==========
def requiere_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_email' not in session:
            return jsonify({'error': 'No autorizado', 'require_auth': True}), 401
        return f(*args, **kwargs)
    return decorated_function

def requiere_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_email' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        usuario = USUARIOS_DB.get(session['usuario_email'])
        if not usuario or usuario.get('plan') != 'admin':
            return jsonify({'error': 'Se requieren permisos de administrador'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ========== ACTUALIZACIÓN AUTOMÁTICA ==========
CACHE_GLOBAL = {}
ULTIMA_ACTUALIZACION = None

def actualizar_cache():
    global CACHE_GLOBAL, ULTIMA_ACTUALIZACION
    print(f"[{datetime.now()}] 🔄 Actualizando caché...")
    for liga_nombre, liga_info in LIGAS.items():
        sport_key = liga_info['key']
        try:
            datos = get_real_data(sport_key)
            CACHE_GLOBAL[liga_nombre] = {'datos': datos, 'fecha': datetime.now().isoformat()}
            print(f"   ✅ {liga_nombre}: {len(datos)} juegos")
        except:
            print(f"   ❌ {liga_nombre}: Error")
    ULTIMA_ACTUALIZACION = datetime.now()
    print(f"[{datetime.now()}] ✅ Actualización completada")

def ejecutar_actualizacion_diaria():
    while True:
        schedule.run_pending()
        time.sleep(60)

schedule.every().day.at("06:00").do(actualizar_cache)
threading.Thread(target=ejecutar_actualizacion_diaria, daemon=True).start()
actualizar_cache()

# ========== RUTAS API ==========
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    nombre = data.get('nombre')
    
    if not email or not password:
        return jsonify({'error': 'Email y contraseña requeridos'}), 400
    
    if email in USUARIOS_DB:
        return jsonify({'error': 'El email ya está registrado'}), 400
    
    USUARIOS_DB[email] = {
        'password': hashlib.sha256(password.encode()).hexdigest(),
        'nombre': nombre or email.split('@')[0],
        'plan': 'free',
        'fecha_registro': datetime.now().isoformat(),
        'ultimo_acceso': datetime.now().isoformat(),
        'suscripcion_valida_hasta': (datetime.now() + timedelta(days=7)).isoformat(),
        'activo': True
    }
    
    return jsonify({'success': True, 'message': 'Usuario registrado. 7 días gratis.'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    usuario = USUARIOS_DB.get(email)
    if not usuario or usuario['password'] != hashlib.sha256(password.encode()).hexdigest():
        return jsonify({'error': 'Credenciales incorrectas'}), 401
    
    if not usuario.get('activo', True):
        return jsonify({'error': 'Usuario desactivado'}), 401
    
    usuario['ultimo_acceso'] = datetime.now().isoformat()
    session['usuario_email'] = email
    session['usuario_nombre'] = usuario['nombre']
    session['usuario_plan'] = usuario['plan']
    
    suscripcion_valida_hasta = datetime.fromisoformat(usuario.get('suscripcion_valida_hasta', '2000-01-01'))
    dias_restantes = (suscripcion_valida_hasta - datetime.now()).days
    
    return jsonify({
        'success': True,
        'user': {
            'email': email,
            'nombre': usuario['nombre'],
            'plan': usuario['plan'],
            'es_admin': usuario['plan'] == 'admin',
            'dias_restantes': max(0, dias_restantes)
        }
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/user_info')
def user_info():
    if 'usuario_email' not in session:
        return jsonify({'authenticated': False})
    
    usuario = USUARIOS_DB.get(session['usuario_email'])
    if not usuario:
        session.clear()
        return jsonify({'authenticated': False})
    
    suscripcion_valida_hasta = datetime.fromisoformat(usuario.get('suscripcion_valida_hasta', '2000-01-01'))
    dias_restantes = (suscripcion_valida_hasta - datetime.now()).days
    
    return jsonify({
        'authenticated': True,
        'user': {
            'email': session['usuario_email'],
            'nombre': usuario['nombre'],
            'plan': usuario['plan'],
            'es_admin': usuario['plan'] == 'admin',
            'dias_restantes': max(0, dias_restantes),
            'limite_consultas': SUSCRIPCIONES[usuario['plan']]['max_consultas_dia']
        }
    })

# ========== RUTAS ADMIN ==========
@app.route('/api/admin/users', methods=['GET'])
@requiere_admin
def admin_get_users():
    users = []
    for email, data in USUARIOS_DB.items():
        users.append({
            'email': email,
            'nombre': data['nombre'],
            'plan': data['plan'],
            'fecha_registro': data['fecha_registro'],
            'ultimo_acceso': data['ultimo_acceso'],
            'activo': data.get('activo', True),
            'suscripcion_valida_hasta': data.get('suscripcion_valida_hasta')
        })
    return jsonify({'users': users})

@app.route('/api/admin/user/<email>', methods=['PUT'])
@requiere_admin
def admin_update_user(email):
    if email not in USUARIOS_DB:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    data = request.json
    usuario = USUARIOS_DB[email]
    
    if 'plan' in data and data['plan'] in SUSCRIPCIONES:
        usuario['plan'] = data['plan']
    if 'activo' in data:
        usuario['activo'] = data['activo']
    if 'dias_suscripcion' in data:
        nueva_fecha = datetime.now() + timedelta(days=data['dias_suscripcion'])
        usuario['suscripcion_valida_hasta'] = nueva_fecha.isoformat()
    
    return jsonify({'success': True})

@app.route('/api/admin/user/<email>', methods=['DELETE'])
@requiere_admin
def admin_delete_user(email):
    if email not in USUARIOS_DB:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    if email == 'admin@predictor.com':
        return jsonify({'error': 'No se puede eliminar al administrador'}), 400
    del USUARIOS_DB[email]
    return jsonify({'success': True})

@app.route('/api/predictions')
@requiere_auth
def get_predictions():
    liga_nombre = request.args.get('liga', 'NBA')
    
    if liga_nombre not in LIGAS:
        return jsonify({'error': 'Liga no encontrada'}), 404
    
    usuario = USUARIOS_DB.get(session['usuario_email'])
    es_premium = usuario['plan'] in ['premium', 'profesional', 'admin']
    
    if LIGAS[liga_nombre].get('premium', False) and not es_premium:
        return jsonify({'error': 'Liga Premium. Mejora tu plan para acceder.', 'premium_required': True}), 403
    
    liga = LIGAS[liga_nombre]
    sport_key = liga['key']
    deporte = liga['deporte']
    
    games = CACHE_GLOBAL.get(liga_nombre, {}).get('datos', [])
    if not games:
        games = get_real_data(sport_key)
    
    results = []
    for game in games[:15]:
        home = game['home_team']
        away = game['away_team']
        
        home_odds = away_odds = None
        for bookmaker in game.get('bookmakers', []):
            if bookmaker['key'] in ['draftkings', 'fanduel', 'pinnacle']:
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'h2h':
                        for o in market['outcomes']:
                            if o['name'] == home:
                                home_odds = o['price']
                            elif o['name'] == away:
                                away_odds = o['price']
                        break
                break
        
        p_home = convert_odds_to_prob(home_odds)
        p_away = convert_odds_to_prob(away_odds)
        total = p_home + p_away
        
        winner = home if p_home > p_away else away
        marcador = generar_prediccion_final(home, away, p_home, p_away, deporte)
        
        home_logo = get_logo_url(home, liga_nombre)
        away_logo = get_logo_url(away, liga_nombre)
        
        results.append({
            'home': home,
            'away': away,
            'home_odds': home_odds,
            'away_odds': away_odds,
            'prob_home': round(p_home/total * 100, 1),
            'prob_away': round(p_away/total * 100, 1),
            'winner': winner,
            'marcador': marcador,
            'home_logo': home_logo,
            'away_logo': away_logo
        })
    
    return jsonify({
        'liga': liga_nombre,
        'es_premium': LIGAS[liga_nombre].get('premium', False),
        'fecha': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'juegos': results
    })

# ========== HTML TEMPLATE ==========
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="theme-color" content="#c00a0a">
    <title>PREDICTOR - Pronósticos Deportivos</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Roboto', sans-serif; background: #0a0a0a; color: #ffffff; min-height: 100vh; }
        
        .login-screen {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            z-index: 2000;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .login-box {
            background: linear-gradient(135deg, #1e1e2e 0%, #16162a 100%);
            border-radius: 25px;
            padding: 40px;
            width: 90%;
            max-width: 400px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .login-box .logo-main { font-size: 2.5rem; font-weight: 900; letter-spacing: 3px; }
        .login-box .logo-sub { font-size: 0.75rem; opacity: 0.7; margin-bottom: 30px; }
        .login-box input {
            width: 100%;
            padding: 14px;
            margin: 10px 0;
            background: #2a2a3e;
            border: none;
            border-radius: 10px;
            color: white;
            font-size: 1rem;
        }
        .login-box button {
            width: 100%;
            padding: 14px;
            background: #c00a0a;
            border: none;
            border-radius: 10px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            font-size: 1rem;
            margin-top: 10px;
        }
        .login-box .switch-link { margin-top: 20px; color: #888; cursor: pointer; }
        .login-box .switch-link:hover { color: #c00a0a; }
        .error-msg { color: #ff4444; margin-top: 10px; font-size: 0.8rem; }
        
        .app-container { display: none; }
        .app-container.visible { display: block; }
        
        .header {
            background: linear-gradient(135deg, #c00a0a 0%, #8b0000 100%);
            padding: 12px 20px;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .logo-container { text-align: center; }
        .logo-main { font-size: 1.8rem; font-weight: 900; letter-spacing: 2px; }
        .logo-sub { font-size: 0.65rem; font-weight: 300; opacity: 0.8; }
        
        .menu-container { position: relative; }
        .menu-btn {
            background: rgba(0,0,0,0.3);
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .dropdown {
            position: absolute;
            top: 100%;
            right: 0;
            background: #1a1a2e;
            border-radius: 12px;
            width: 260px;
            max-height: 500px;
            overflow-y: auto;
            display: none;
            z-index: 200;
            margin-top: 10px;
        }
        .dropdown.active { display: block; }
        .dropdown-category {
            padding: 10px 15px;
            font-weight: 700;
            background: #0f0f1a;
            border-bottom: 1px solid #2a2a3e;
            font-size: 0.85rem;
        }
        .dropdown-item {
            padding: 8px 15px 8px 30px;
            cursor: pointer;
            font-size: 0.85rem;
        }
        .dropdown-item:hover { background: #c00a0a; }
        .premium-badge {
            background: #ffd700;
            color: #000;
            padding: 2px 8px;
            border-radius: 20px;
            font-size: 0.65rem;
            font-weight: bold;
            margin-left: 8px;
        }
        
        .user-info { display: flex; align-items: center; gap: 15px; }
        .user-avatar {
            width: 38px;
            height: 38px;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }
        .user-menu { position: relative; }
        .user-dropdown {
            position: absolute;
            top: 100%;
            right: 0;
            background: #1a1a2e;
            border-radius: 12px;
            width: 220px;
            display: none;
            z-index: 200;
            margin-top: 10px;
        }
        .user-dropdown.active { display: block; }
        .dropdown-item {
            padding: 12px 15px;
            cursor: pointer;
            border-bottom: 1px solid #2a2a3e;
            font-size: 0.85rem;
        }
        .dropdown-item:hover { background: #c00a0a; }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .fecha { text-align: center; color: #888; margin-bottom: 20px; font-size: 0.8rem; }
        
        .game-card {
            background: linear-gradient(135deg, #1e1e2e 0%, #16162a 100%);
            border-radius: 12px;
            margin-bottom: 12px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .game-header {
            padding: 12px 15px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0,0,0,0.2);
        }
        .team-display { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; justify-content: center; }
        .team {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 5px;
            min-width: 100px;
        }
        .team-logo { width: 45px; height: 45px; object-fit: contain; }
        .team-name { font-size: 0.8rem; font-weight: 500; text-align: center; }
        .vs { font-size: 1rem; font-weight: bold; color: #c00a0a; }
        
        .game-details {
            padding: 0 15px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s ease;
        }
        .game-details.active { padding: 15px; max-height: 500px; }
        
        .prob-bar {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            height: 35px;
            overflow: hidden;
            margin: 10px 0;
            display: flex;
        }
        .prob-home {
            background: linear-gradient(90deg, #c00a0a, #ff4444);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .prob-away {
            background: linear-gradient(90deg, #2c2c3e, #3a3a4e);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .prediction-badge {
            display: inline-block;
            background: #c00a0a;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: bold;
            margin: 5px 5px 5px 0;
        }
        .prediction-badge.secondary { background: #2c2c3e; }
        .odds {
            display: inline-block;
            background: rgba(255,255,255,0.1);
            padding: 3px 8px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 0.8rem;
            margin-right: 8px;
        }
        
        .loading { text-align: center; padding: 50px; }
        .loading i { font-size: 3rem; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .footer {
            text-align: center;
            padding: 15px;
            font-size: 0.65rem;
            color: #555;
            border-top: 1px solid #1a1a2e;
            margin-top: 20px;
        }
        
        .warning {
            background: #ff9800;
            color: #000;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 15px;
        }
        
        .admin-panel {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .admin-table { width: 100%; border-collapse: collapse; }
        .admin-table th, .admin-table td { padding: 10px; text-align: left; border-bottom: 1px solid #2a2a3e; }
        .btn-small { padding: 5px 10px; font-size: 0.7rem; margin: 0 2px; cursor: pointer; border-radius: 5px; border: none; }
        .btn-edit { background: #2196F3; color: white; }
        .btn-delete { background: #f44336; color: white; }
        
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 3000;
            display: none;
            align-items: center;
            justify-content: center;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: #1a1a2e;
            border-radius: 20px;
            padding: 30px;
            max-width: 400px;
            width: 90%;
        }
        .modal-content input, .modal-content select {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: #2a2a3e;
            border: none;
            border-radius: 8px;
            color: white;
        }
        .modal-content button {
            width: 100%;
            padding: 12px;
            background: #c00a0a;
            border: none;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            margin-top: 10px;
        }
        
        @media (max-width: 768px) {
            .header { flex-direction: column; text-align: center; }
            .team { min-width: 70px; }
            .team-logo { width: 30px; height: 30px; }
            .team-name { font-size: 0.65rem; }
            .container { padding: 10px; }
        }
    </style>
</head>
<body>
    <div class="login-screen" id="loginScreen">
        <div class="login-box">
            <div class="logo-main">PREDICTOR</div>
            <div class="logo-sub">byjmcreaciones</div>
            
            <div id="loginForm">
                <input type="email" id="loginEmail" placeholder="Email">
                <input type="password" id="loginPassword" placeholder="Contraseña">
                <button onclick="doLogin()">Iniciar Sesión</button>
                <div class="switch-link" onclick="showSignup()">¿No tienes cuenta? Regístrate gratis</div>
                <div id="loginError" class="error-msg"></div>
            </div>
            
            <div id="signupForm" style="display:none;">
                <input type="text" id="signupNombre" placeholder="Nombre">
                <input type="email" id="signupEmail" placeholder="Email">
                <input type="password" id="signupPassword" placeholder="Contraseña">
                <button onclick="doSignup()">Registrarse</button>
                <div class="switch-link" onclick="showLogin()">← Volver</div>
                <div id="signupError" class="error-msg"></div>
            </div>
            
            <div style="margin-top: 20px; font-size: 0.65rem; color: #555;">
                Demo: demo@predictor.com / demo123<br>
                Admin: admin@predictor.com / admin123
            </div>
        </div>
    </div>
    
    <div class="app-container" id="appContainer">
        <div class="header">
            <div class="logo-container">
                <div class="logo-main">PREDICTOR</div>
                <div class="logo-sub">byjmcreaciones</div>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <div class="menu-container">
                    <button class="menu-btn" id="menuBtn">
                        <i class="fas fa-bars"></i> <span id="currentLiga">NBA</span> <i class="fas fa-chevron-down"></i>
                    </button>
                    <div class="dropdown" id="dropdown">
                        <div class="dropdown-category">🏀 BALONCESTO</div>
                        <div class="dropdown-item" data-liga="NBA">NBA <span class="premium-badge">FREE</span></div>
                        <div class="dropdown-item" data-liga="NCAA Basketball">NCAA Basketball <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-category">⚾ BÉISBOL</div>
                        <div class="dropdown-item" data-liga="MLB">MLB <span class="premium-badge">FREE</span></div>
                        <div class="dropdown-category">🏒 HOCKEY</div>
                        <div class="dropdown-item" data-liga="NHL">NHL <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-category">🏈 FÚTBOL AMERICANO</div>
                        <div class="dropdown-item" data-liga="NFL">NFL <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-item" data-liga="NCAA Football">NCAA Football <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-category">⚽ FÚTBOL - EUROPA</div>
                        <div class="dropdown-item" data-liga="Premier League">Premier League <span class="premium-badge">FREE</span></div>
                        <div class="dropdown-item" data-liga="La Liga">La Liga <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-item" data-liga="Serie A">Serie A <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-item" data-liga="Bundesliga">Bundesliga <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-item" data-liga="Ligue 1">Ligue 1 <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-category">🏆 UEFA</div>
                        <div class="dropdown-item" data-liga="Champions League">Champions League <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-category">🌎 SUDAMÉRICA</div>
                        <div class="dropdown-item" data-liga="Brasileirão">Brasileirão <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-item" data-liga="Liga Argentina">Liga Argentina <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-category">🇲🇽 NORTEAMÉRICA</div>
                        <div class="dropdown-item" data-liga="Liga MX">Liga MX <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-item" data-liga="MLS">MLS <span class="premium-badge">PREMIUM</span></div>
                    </div>
                </div>
                <div class="user-info">
                    <div class="user-menu">
                        <div class="user-avatar" id="userAvatar">
                            <i class="fas fa-user"></i>
                        </div>
                        <div class="user-dropdown" id="userDropdown">
                            <div class="dropdown-item" id="userPlanInfo"></div>
                            <div class="dropdown-item" id="adminPanelBtn" style="display:none;">📊 Panel Admin</div>
                            <div class="dropdown-item" id="logoutBtn">🚪 Cerrar Sesión</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="fecha" id="fecha"></div>
            <div id="warningMessage" style="display:none;" class="warning"></div>
            <div id="adminPanel" style="display:none;"></div>
            <div id="content"><div class="loading"><i class="fas fa-chart-line"></i><p>Cargando partidos...</p></div></div>
        </div>
        
        <div class="footer">
            <p>⚠️ Las apuestas deportivas conllevan riesgo. Juegue responsablemente.</p>
            <p>Datos en tiempo real | Logos oficiales ESPN/NBA/MLB/NHL/NFL | Actualización diaria 6:00 AM</p>
        </div>
    </div>
    
    <div class="modal" id="adminUserModal">
        <div class="modal-content">
            <h2 id="adminModalTitle">Editar Usuario</h2>
            <input type="email" id="adminUserEmail" readonly>
            <select id="adminUserPlan">
                <option value="free">Gratuito</option>
                <option value="premium">Premium</option>
                <option value="profesional">Profesional</option>
            </select>
            <input type="number" id="adminUserDays" placeholder="Días de suscripción">
            <label><input type="checkbox" id="adminUserActive"> Usuario activo</label>
            <button onclick="saveUserEdit()">Guardar</button>
            <button onclick="closeModal('adminUserModal')">Cancelar</button>
        </div>
    </div>
    
    <script>
        let currentLiga = 'NBA';
        let currentUser = null;
        
        async function doLogin() {
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const res = await fetch('/api/login', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});
            const data = await res.json();
            if(data.success){
                currentUser = data.user;
                document.getElementById('loginScreen').style.opacity='0';
                setTimeout(()=>{
                    document.getElementById('loginScreen').style.display='none';
                    document.getElementById('appContainer').classList.add('visible');
                },500);
                cargarLiga('NBA');
                actualizarUI();
            } else {
                document.getElementById('loginError').innerText = data.error;
            }
        }
        
        async function doSignup() {
            const nombre = document.getElementById('signupNombre').value;
            const email = document.getElementById('signupEmail').value;
            const password = document.getElementById('signupPassword').value;
            const res = await fetch('/api/signup', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nombre,email,password})});
            const data = await res.json();
            if(data.success){
                showLogin();
                document.getElementById('loginEmail').value = email;
                document.getElementById('loginError').innerText = '✅ Registro exitoso. Inicia sesión.';
            } else {
                document.getElementById('signupError').innerText = data.error;
            }
        }
        
        function showSignup() {
            document.getElementById('loginForm').style.display='none';
            document.getElementById('signupForm').style.display='block';
        }
        
        function showLogin() {
            document.getElementById('loginForm').style.display='block';
            document.getElementById('signupForm').style.display='none';
        }
        
        async function logout() {
            await fetch('/api/logout', {method:'POST'});
            currentUser = null;
            document.getElementById('appContainer').classList.remove('visible');
            document.getElementById('loginScreen').style.display='flex';
            document.getElementById('loginScreen').style.opacity='1';
        }
        
        function actualizarUI() {
            if(currentUser){
                document.getElementById('userPlanInfo').innerHTML = `📋 ${currentUser.plan} | ${currentUser.dias_restantes} días`;
                if(currentUser.es_admin) document.getElementById('adminPanelBtn').style.display='block';
            }
        }
        
        async function cargarLiga(liga) {
            const content = document.getElementById('content');
            content.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-pulse"></i><p>Cargando...</p></div>';
            try {
                const res = await fetch(`/api/predictions?liga=${encodeURIComponent(liga)}`);
                const data = await res.json();
                if(data.error){
                    if(data.premium_required) content.innerHTML = `<div class="warning">🔒 Liga Premium. Mejora tu plan para acceder a ${liga}.</div>`;
                    else content.innerHTML = `<div class="warning">❌ ${data.error}</div>`;
                    return;
                }
                document.getElementById('fecha').innerHTML = `<i class="far fa-calendar-alt"></i> ${data.fecha}`;
                let html = '';
                data.juegos.forEach((game, idx) => {
                    const homeLogo = game.home_logo ? `<img class="team-logo" src="${game.home_logo}" onerror="this.style.display='none'">` : `<div style="width:45px;height:45px;background:#2a2a3e;border-radius:50%;display:flex;align-items:center;justify-content:center;">${game.home.charAt(0)}</div>`;
                    const awayLogo = game.away_logo ? `<img class="team-logo" src="${game.away_logo}" onerror="this.style.display='none'">` : `<div style="width:45px;height:45px;background:#2a2a3e;border-radius:50%;display:flex;align-items:center;justify-content:center;">${game.away.charAt(0)}</div>`;
                    html += `<div class="game-card"><div class="game-header" onclick="toggleGame(${idx})"><div class="team-display"><div class="team">${awayLogo}<span class="team-name">${game.away}</span></div><div class="vs">VS</div><div class="team">${homeLogo}<span class="team-name">${game.home}</span></div></div><div class="game-toggle" id="toggle-${idx}">▼</div></div><div class="game-details" id="details-${idx}"><div class="prob-bar"><div class="prob-home" style="width:${game.prob_home}%;">🏠 ${game.prob_home}%</div><div class="prob-away" style="width:${game.prob_away}%;">✈️ ${game.prob_away}%</div></div><div><span class="prediction-badge">🏆 GANA: ${game.winner}</span><span class="prediction-badge secondary">📝 ${game.marcador}</span></div><div><span class="odds">💰 ${game.home}: ${game.home_odds||'N/A'}</span><span class="odds">${game.away}: ${game.away_odds||'N/A'}</span></div></div></div>`;
                });
                content.innerHTML = html;
            } catch(e){ content.innerHTML = '<div class="warning">❌ Error al cargar</div>'; }
        }
        
        function toggleGame(idx){
            const details = document.getElementById(`details-${idx}`);
            const toggle = document.getElementById(`toggle-${idx}`);
            details.classList.toggle('active');
            toggle.style.transform = details.classList.contains('active') ? 'rotate(180deg)' : 'rotate(0deg)';
        }
        
        async function cargarAdminPanel(){
            if(!currentUser?.es_admin) return;
            const res = await fetch('/api/admin/users');
            const data = await res.json();
            let html = '<h3>👑 Panel Administrador</h3><table class="admin-table"><tr><th>Email</th><th>Plan</th><th>Activo</th><th>Acciones</th></tr>';
            data.users.forEach(u => {
                html += `<tr><td>${u.email}</td><td>${u.plan}</td><td>${u.activo?'✅':'❌'}</td><td><button class="btn-small btn-edit" onclick="editarUsuario('${u.email}','${u.plan}',${u.activo})">Editar</button><button class="btn-small btn-delete" onclick="eliminarUsuario('${u.email}')">Eliminar</button></td></tr>`;
            });
            html += '</table>';
            document.getElementById('adminPanel').innerHTML = html;
            document.getElementById('adminPanel').style.display = 'block';
        }
        
        function editarUsuario(email, plan, activo){
            document.getElementById('adminUserEmail').value = email;
            document.getElementById('adminUserPlan').value = plan;
            document.getElementById('adminUserActive').checked = activo;
            document.getElementById('adminUserDays').value = '';
            document.getElementById('adminUserModal').classList.add('active');
        }
        
        async function saveUserEdit(){
            const email = document.getElementById('adminUserEmail').value;
            const plan = document.getElementById('adminUserPlan').value;
            const activo = document.getElementById('adminUserActive').checked;
            const dias = document.getElementById('adminUserDays').value;
            const data = {plan,activo};
            if(dias) data.dias_suscripcion = parseInt(dias);
            await fetch(`/api/admin/user/${email}`, {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
            closeModal('adminUserModal');
            cargarAdminPanel();
        }
        
        async function eliminarUsuario(email){
            if(confirm(`¿Eliminar ${email}?`)) await fetch(`/api/admin/user/${email}`, {method:'DELETE'});
            cargarAdminPanel();
        }
        
        function closeModal(id){ document.getElementById(id).classList.remove('active'); }
        
        document.getElementById('menuBtn').addEventListener('click', e => { e.stopPropagation(); document.getElementById('dropdown').classList.toggle('active'); });
        document.addEventListener('click', () => { document.getElementById('dropdown').classList.remove('active'); document.getElementById('userDropdown').classList.remove('active'); });
        document.getElementById('userAvatar').addEventListener('click', e => { e.stopPropagation(); document.getElementById('userDropdown').classList.toggle('active'); });
        document.querySelectorAll('.dropdown-item[data-liga]').forEach(item => {
            item.addEventListener('click', function() {
                currentLiga = this.dataset.liga;
                document.getElementById('currentLiga').innerHTML = currentLiga;
                cargarLiga(currentLiga);
            });
        });
        document.getElementById('adminPanelBtn').addEventListener('click', () => cargarAdminPanel());
        document.getElementById('logoutBtn').addEventListener('click', logout);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("=" * 60)
    print("🏆 PREDICTOR - byjmcreaciones 🏆")
    print("=" * 60)
    print("📱 Abrí: http://localhost:8080")
    print("")
    print("📋 ACCESO:")
    print("   Demo: demo@predictor.com / demo123")
    print("   Admin: admin@predictor.com / admin123")
    print("")
    print("🔄 Actualización automática: 6:00 AM")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
