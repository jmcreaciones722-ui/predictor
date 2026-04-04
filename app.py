from flask import Flask, render_template_string, request, session, jsonify
import requests
from datetime import datetime
import random
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave123')

API_KEY = "67a8f29d5a4de82b616e920824663e3a"

# Usuarios
USUARIOS = {
    'admin@predictor.com': hashlib.sha256('admin123'.encode()).hexdigest(),
    'demo@predictor.com': hashlib.sha256('demo123'.encode()).hexdigest()
}

# HTML completo
HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PREDICTOR</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #0a0a0a; color: white; }
        .header { background: linear-gradient(135deg, #c00a0a, #8b0000); padding: 20px; text-align: center; }
        h1 { font-size: 2rem; letter-spacing: 3px; }
        small { font-size: 0.7rem; opacity: 0.8; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .login-box, .card { background: #1e1e2e; border-radius: 15px; padding: 30px; margin: 20px 0; text-align: center; }
        input, button { padding: 12px; margin: 5px; border-radius: 8px; border: none; }
        input { background: #2a2a3e; color: white; width: 80%; }
        button { background: #c00a0a; color: white; cursor: pointer; font-weight: bold; }
        .game-card { background: #1e1e2e; border-radius: 10px; padding: 15px; margin: 10px 0; border-left: 4px solid #c00a0a; }
        .menu { display: flex; gap: 10px; justify-content: center; margin: 20px 0; flex-wrap: wrap; }
        .menu-btn { background: #333; padding: 10px 20px; text-decoration: none; color: white; border-radius: 8px; }
        .menu-btn.active { background: #c00a0a; }
        .prob-bar { background: #333; border-radius: 10px; height: 30px; margin: 10px 0; overflow: hidden; }
        .prob-home { background: #c00a0a; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 12px; }
        .badge { display: inline-block; background: #c00a0a; padding: 5px 10px; border-radius: 20px; font-size: 12px; margin: 5px; }
        .footer { text-align: center; padding: 20px; font-size: 11px; color: #555; }
        @media (max-width: 600px) { .menu-btn { padding: 8px 12px; font-size: 12px; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 PREDICTOR</h1>
        <small>byjmcreaciones</small>
    </div>
    
    {% if not session.user %}
    <div class="container">
        <div class="login-box">
            <h2>Iniciar Sesión</h2>
            <form method="POST">
                <input type="email" name="email" placeholder="Email" required><br>
                <input type="password" name="password" placeholder="Contraseña" required><br>
                <button type="submit">Ingresar</button>
            </form>
            <p style="margin-top:20px; font-size:12px;">Demo: demo@predictor.com / demo123<br>Admin: admin@predictor.com / admin123</p>
        </div>
    </div>
    {% else %}
    <div class="container">
        <div class="menu">
            <a href="/?liga=NBA" class="menu-btn {% if liga == 'NBA' %}active{% endif %}">🏀 NBA</a>
            <a href="/?liga=MLB" class="menu-btn {% if liga == 'MLB' %}active{% endif %}">⚾ MLB</a>
            <a href="/?liga=Premier%20League" class="menu-btn {% if liga == 'Premier League' %}active{% endif %}">⚽ Premier</a>
            <a href="/logout" class="menu-btn">🚪 Salir</a>
        </div>
        
        <h2 style="text-align:center;">{{ liga }}</h2>
        
        {% for g in games %}
        <div class="game-card">
            <h3>{{ g.away }} @ {{ g.home }}</h3>
            <div class="prob-bar">
                <div class="prob-home" style="width: {{ g.prob_home }}%;">{{ g.prob_home }}% 🏠</div>
            </div>
            <div>
                <span class="badge">🏆 {{ g.winner }}</span>
                <span class="badge">📝 {{ g.score }}</span>
            </div>
            <div style="margin-top:10px;">
                <span class="badge">💰 {{ g.home }}: {{ g.home_odds }}</span>
                <span class="badge">💰 {{ g.away }}: {{ g.away_odds }}</span>
            </div>
        </div>
        {% endfor %}
        
        <div class="footer">
            <p>⚠️ Las apuestas deportivas conllevan riesgo. Juegue responsablemente.</p>
            <p>Datos en tiempo real desde The Odds API</p>
        </div>
    </div>
    {% endif %}
</body>
</html>
'''

def get_odds(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {'apiKey': API_KEY, 'regions': 'us', 'markets': 'h2h', 'oddsFormat': 'american'}
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json() if r.status_code == 200 else []
    except:
        return []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email in USUARIOS and USUARIOS[email] == hashlib.sha256(password.encode()).hexdigest():
            session['user'] = email
    
    liga = request.args.get('liga', 'NBA')
    sport_keys = {'NBA': 'basketball_nba', 'MLB': 'baseball_mlb', 'Premier League': 'soccer_epl'}
    sport_key = sport_keys.get(liga, 'basketball_nba')
    
    data = get_odds(sport_key)
    games = []
    
    for g in data[:10]:
        home = g['home_team']
        away = g['away_team']
        
        home_odds = away_odds = None
        for book in g.get('bookmakers', []):
            for market in book.get('markets', []):
                if market['key'] == 'h2h':
                    for o in market['outcomes']:
                        if o['name'] == home:
                            home_odds = o['price']
                        elif o['name'] == away:
                            away_odds = o['price']
                    break
            if home_odds:
                break
        
        def prob(odds):
            if not odds:
                return 50
            return round(abs(odds) / (abs(odds) + 100) * 100, 1) if odds < 0 else round(100 / (odds + 100) * 100, 1)
        
        p_home = prob(home_odds)
        p_away = prob(away_odds)
        total = p_home + p_away
        p_home_norm = round(p_home / total * 100, 1)
        p_away_norm = round(p_away / total * 100, 1)
        
        winner = home if p_home > p_away else away
        pts_home = 105 + random.randint(-10, 20)
        pts_away = 105 + random.randint(-10, 20)
        score = f"{pts_home} - {pts_away}"
        
        games.append({
            'home': home,
            'away': away,
            'home_odds': home_odds,
            'away_odds': away_odds,
            'prob_home': p_home_norm,
            'prob_away': p_away_norm,
            'winner': winner,
            'score': score
        })
    
    return render_template_string(HTML, liga=liga, games=games, session=session)

@app.route('/logout')
def logout():
    session.clear()
    return index()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
