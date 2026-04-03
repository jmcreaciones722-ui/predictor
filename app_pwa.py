from flask import Flask, render_template_string, jsonify, request, session
import requests
from datetime import datetime, timedelta
import random
import hashlib
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_secreta_12345')

API_KEY = "67a8f29d5a4de82b616e920824663e3a"

# ========== USUARIOS ==========
USUARIOS_DB = {
    'admin@predictor.com': {
        'password': hashlib.sha256('admin123'.encode()).hexdigest(),
        'nombre': 'Administrador',
        'plan': 'admin',
        'activo': True
    },
    'demo@predictor.com': {
        'password': hashlib.sha256('demo123'.encode()).hexdigest(),
        'nombre': 'Usuario Demo',
        'plan': 'free',
        'activo': True
    }
}

# ========== LIGAS ==========
LIGAS = {
    'NBA': {'key': 'basketball_nba', 'premium': False},
    'MLB': {'key': 'baseball_mlb', 'premium': False},
    'NHL': {'key': 'icehockey_nhl', 'premium': True},
    'NFL': {'key': 'americanfootball_nfl', 'premium': True},
    'Premier League': {'key': 'soccer_epl', 'premium': False},
    'La Liga': {'key': 'soccer_spain_la_liga', 'premium': True},
}

def get_real_data(sport_key):
    """Obtiene datos de la API"""
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'h2h',
        'oddsFormat': 'american'
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def convert_odds_to_prob(odds):
    if odds is None:
        return 50
    if odds < 0:
        return (abs(odds) / (abs(odds) + 100)) * 100
    return (100 / (odds + 100)) * 100

# ========== RUTAS ==========
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
        'activo': True
    }
    
    return jsonify({'success': True, 'message': 'Usuario registrado.'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    usuario = USUARIOS_DB.get(email)
    if not usuario or usuario['password'] != hashlib.sha256(password.encode()).hexdigest():
        return jsonify({'error': 'Credenciales incorrectas'}), 401
    
    session['usuario_email'] = email
    session['usuario_nombre'] = usuario['nombre']
    session['usuario_plan'] = usuario['plan']
    
    return jsonify({
        'success': True,
        'user': {
            'email': email,
            'nombre': usuario['nombre'],
            'plan': usuario['plan'],
            'es_admin': usuario['plan'] == 'admin'
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
        return jsonify({'authenticated': False})
    
    return jsonify({
        'authenticated': True,
        'user': {
            'email': session['usuario_email'],
            'nombre': usuario['nombre'],
            'plan': usuario['plan'],
            'es_admin': usuario['plan'] == 'admin'
        }
    })

@app.route('/api/predictions')
def get_predictions():
    liga_nombre = request.args.get('liga', 'NBA')
    
    if 'usuario_email' not in session:
        return jsonify({'error': 'No autorizado', 'require_auth': True}), 401
    
    usuario = USUARIOS_DB.get(session['usuario_email'])
    es_premium = usuario['plan'] in ['premium', 'admin']
    
    if LIGAS[liga_nombre].get('premium', False) and not es_premium:
        return jsonify({'error': 'Liga Premium. Mejora tu plan.', 'premium_required': True}), 403
    
    sport_key = LIGAS[liga_nombre]['key']
    
    games = get_real_data(sport_key)
    
    if not games:
        return jsonify({'error': 'No hay partidos disponibles', 'juegos': []}), 200
    
    results = []
    for game in games[:10]:
        home = game['home_team']
        away = game['away_team']
        
        home_odds = None
        away_odds = None
        
        for bookmaker in game.get('bookmakers', []):
            if bookmaker['key'] in ['draftkings', 'fanduel', 'pinnacle']:
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            if outcome['name'] == home:
                                home_odds = outcome['price']
                            elif outcome['name'] == away:
                                away_odds = outcome['price']
                        break
                break
        
        p_home = convert_odds_to_prob(home_odds)
        p_away = convert_odds_to_prob(away_odds)
        total = p_home + p_away
        
        winner = home if p_home > p_away else away
        
        prob_factor = (p_home - p_away) / 100
        margin = int(prob_factor * 20)
        pts_home = 110 + margin + random.randint(-8, 8)
        pts_away = 110 - margin + random.randint(-8, 8)
        pts_home = max(85, min(135, pts_home))
        pts_away = max(85, min(135, pts_away))
        marcador = f"{pts_home} - {pts_away}"
        
        results.append({
            'home': home,
            'away': away,
            'home_odds': home_odds,
            'away_odds': away_odds,
            'prob_home': round(p_home/total * 100, 1),
            'prob_away': round(p_away/total * 100, 1),
            'winner': winner,
            'marcador': marcador,
            'home_logo': None,
            'away_logo': None
        })
    
    return jsonify({
        'liga': liga_nombre,
        'fecha': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'juegos': results
    })

@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    if 'usuario_email' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    usuario = USUARIOS_DB.get(session['usuario_email'])
    if not usuario or usuario['plan'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    users = []
    for email, data in USUARIOS_DB.items():
        users.append({
            'email': email,
            'nombre': data['nombre'],
            'plan': data['plan']
        })
    return jsonify({'users': users})

@app.route('/api/admin/user/<email>', methods=['PUT'])
def admin_update_user(email):
    if 'usuario_email' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    usuario = USUARIOS_DB.get(session['usuario_email'])
    if not usuario or usuario['plan'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    if email not in USUARIOS_DB:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    data = request.json
    if 'plan' in data:
        USUARIOS_DB[email]['plan'] = data['plan']
    
    return jsonify({'success': True})

# ========== HTML TEMPLATE ==========
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PREDICTOR</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Roboto', sans-serif; background: #0a0a0a; color: #fff; min-height: 100vh; }
        
        .login-screen {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #0a0a0a, #1a1a2e);
            z-index: 2000;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .login-box {
            background: linear-gradient(135deg, #1e1e2e, #16162a);
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
        }
        .login-box .switch-link { margin-top: 20px; color: #888; cursor: pointer; }
        .login-box .switch-link:hover { color: #c00a0a; }
        
        .app-container { display: none; }
        .app-container.visible { display: block; }
        
        .header {
            background: linear-gradient(135deg, #c00a0a, #8b0000);
            padding: 12px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .logo-main { font-size: 1.5rem; font-weight: 900; letter-spacing: 2px; }
        .logo-sub { font-size: 0.6rem; opacity: 0.8; }
        
        .menu-container { position: relative; }
        .menu-btn {
            background: rgba(0,0,0,0.3);
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
        }
        .dropdown {
            position: absolute;
            top: 100%;
            right: 0;
            background: #1a1a2e;
            border-radius: 12px;
            width: 260px;
            display: none;
            z-index: 200;
            margin-top: 10px;
        }
        .dropdown.active { display: block; }
        .dropdown-category { padding: 10px 15px; font-weight: bold; background: #0f0f1a; }
        .dropdown-item { padding: 8px 15px 8px 30px; cursor: pointer; }
        .dropdown-item:hover { background: #c00a0a; }
        .premium-badge {
            background: #ffd700;
            color: #000;
            padding: 2px 8px;
            border-radius: 20px;
            font-size: 0.65rem;
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
        .dropdown-item { padding: 12px 15px; cursor: pointer; border-bottom: 1px solid #2a2a3e; }
        .dropdown-item:hover { background: #c00a0a; }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .fecha { text-align: center; color: #888; margin-bottom: 20px; }
        
        .game-card {
            background: linear-gradient(135deg, #1e1e2e, #16162a);
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
        .team-display { display: flex; align-items: center; gap: 15px; justify-content: center; flex-wrap: wrap; }
        .team {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 5px;
            min-width: 100px;
        }
        .team-logo { width: 45px; height: 45px; object-fit: contain; }
        .team-name { font-size: 0.8rem; text-align: center; }
        .vs { font-size: 1rem; font-weight: bold; color: #c00a0a; }
        
        .game-details {
            padding: 0 15px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s;
        }
        .game-details.active { padding: 15px; max-height: 400px; }
        
        .prob-bar {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            height: 35px;
            display: flex;
            margin: 10px 0;
        }
        .prob-home {
            background: linear-gradient(90deg, #c00a0a, #ff4444);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
        }
        .prob-away {
            background: linear-gradient(90deg, #2c2c3e, #3a3a4e);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
        }
        
        .prediction-badge {
            display: inline-block;
            background: #c00a0a;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            margin: 5px 5px 0 0;
        }
        .prediction-badge.secondary { background: #2c2c3e; }
        .odds {
            display: inline-block;
            background: rgba(255,255,255,0.1);
            padding: 3px 8px;
            border-radius: 5px;
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
        
        @media (max-width: 768px) {
            .team { min-width: 70px; }
            .team-logo { width: 30px; height: 30px; }
            .team-name { font-size: 0.65rem; }
            .container { padding: 10px; }
            .header { flex-direction: column; text-align: center; }
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
                <div class="switch-link" onclick="showSignup()">¿No tienes cuenta? Regístrate</div>
            </div>
            <div id="signupForm" style="display:none;">
                <input type="text" id="signupNombre" placeholder="Nombre">
                <input type="email" id="signupEmail" placeholder="Email">
                <input type="password" id="signupPassword" placeholder="Contraseña">
                <button onclick="doSignup()">Registrarse</button>
                <div class="switch-link" onclick="showLogin()">← Volver</div>
            </div>
            <div style="margin-top:20px; font-size:12px;">Demo: demo@predictor.com / demo123<br>Admin: admin@predictor.com / admin123</div>
        </div>
    </div>
    
    <div class="app-container" id="appContainer">
        <div class="header">
            <div><div class="logo-main">PREDICTOR</div><div class="logo-sub">byjmcreaciones</div></div>
            <div style="display:flex; gap:10px;">
                <div class="menu-container">
                    <button class="menu-btn" id="menuBtn"><i class="fas fa-bars"></i> <span id="currentLiga">NBA</span></button>
                    <div class="dropdown" id="dropdown">
                        <div class="dropdown-category">🏀 BALONCESTO</div>
                        <div class="dropdown-item" data-liga="NBA">NBA <span class="premium-badge">FREE</span></div>
                        <div class="dropdown-category">⚾ BÉISBOL</div>
                        <div class="dropdown-item" data-liga="MLB">MLB <span class="premium-badge">FREE</span></div>
                        <div class="dropdown-category">🏒 HOCKEY</div>
                        <div class="dropdown-item" data-liga="NHL">NHL <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-category">🏈 FÚTBOL AMERICANO</div>
                        <div class="dropdown-item" data-liga="NFL">NFL <span class="premium-badge">PREMIUM</span></div>
                        <div class="dropdown-category">⚽ FÚTBOL</div>
                        <div class="dropdown-item" data-liga="Premier League">Premier League <span class="premium-badge">FREE</span></div>
                        <div class="dropdown-item" data-liga="La Liga">La Liga <span class="premium-badge">PREMIUM</span></div>
                    </div>
                </div>
                <div class="user-menu">
                    <div class="user-avatar" id="userAvatar"><i class="fas fa-user"></i></div>
                    <div class="user-dropdown" id="userDropdown">
                        <div class="dropdown-item" id="userPlanInfo"></div>
                        <div class="dropdown-item" id="adminPanelBtn" style="display:none;">📊 Panel Admin</div>
                        <div class="dropdown-item" id="logoutBtn">🚪 Cerrar Sesión</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="fecha" id="fecha"></div>
            <div id="adminPanel" style="display:none;"></div>
            <div id="content"><div class="loading"><i class="fas fa-chart-line"></i><p>Cargando partidos...</p></div></div>
        </div>
        
        <div class="footer">
            <p>⚠️ Las apuestas deportivas conllevan riesgo. Juegue responsablemente.</p>
            <p>PREDICTOR by jmcreaciones | Datos en tiempo real</p>
        </div>
    </div>
    
    <script>
        let currentLiga = 'NBA';
        let currentUser = null;
        
        async function doLogin() {
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, password})
            });
            const data = await res.json();
            if(data.success){
                currentUser = data.user;
                document.getElementById('loginScreen').style.display = 'none';
                document.getElementById('appContainer').classList.add('visible');
                cargarLiga('NBA');
                actualizarUI();
            } else {
                alert(data.error);
            }
        }
        
        async function doSignup() {
            const nombre = document.getElementById('signupNombre').value;
            const email = document.getElementById('signupEmail').value;
            const password = document.getElementById('signupPassword').value;
            const res = await fetch('/api/signup', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({nombre, email, password})
            });
            const data = await res.json();
            if(data.success){
                showLogin();
                alert('Registro exitoso. Inicia sesión.');
            } else {
                alert(data.error);
            }
        }
        
        function showSignup() {
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('signupForm').style.display = 'block';
        }
        
        function showLogin() {
            document.getElementById('loginForm').style.display = 'block';
            document.getElementById('signupForm').style.display = 'none';
        }
        
        async function logout() {
            await fetch('/api/logout', {method: 'POST'});
            location.reload();
        }
        
        function actualizarUI() {
            if(currentUser){
                document.getElementById('userPlanInfo').innerHTML = `📋 ${currentUser.plan} | ${currentUser.nombre}`;
                if(currentUser.es_admin){
                    document.getElementById('adminPanelBtn').style.display = 'block';
                }
            }
        }
        
        document.getElementById('logoutBtn').addEventListener('click', logout);
        document.getElementById('menuBtn').addEventListener('click', () => {
            document.getElementById('dropdown').classList.toggle('active');
        });
        
        document.querySelectorAll('.dropdown-item[data-liga]').forEach(item => {
            item.addEventListener('click', function() {
                currentLiga = this.dataset.liga;
                document.getElementById('currentLiga').innerHTML = currentLiga;
                document.getElementById('dropdown').classList.remove('active');
                cargarLiga(currentLiga);
            });
        });
        
        document.getElementById('userAvatar').addEventListener('click', () => {
            document.getElementById('userDropdown').classList.toggle('active');
        });
        
        document.addEventListener('click', (e) => {
            if(!e.target.closest('.menu-container')) document.getElementById('dropdown').classList.remove('active');
            if(!e.target.closest('.user-menu')) document.getElementById('userDropdown').classList.remove('active');
        });
        
        async function cargarLiga(liga) {
            const content = document.getElementById('content');
            content.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-pulse"></i><p>Cargando partidos...</p></div>';
            try {
                const res = await fetch(`/api/predictions?liga=${liga}`);
                const data = await res.json();
                if(data.error){
                    if(data.premium_required){
                        content.innerHTML = `<div class="warning">🔒 ${data.error}</div>`;
                    } else if(data.require_auth){
                        content.innerHTML = `<div class="warning">🔒 Inicia sesión para ver los partidos.</div>`;
                    } else {
                        content.innerHTML = `<div class="warning">❌ ${data.error}</div>`;
                    }
                    return;
                }
                document.getElementById('fecha').innerHTML = `<i class="far fa-calendar-alt"></i> ${data.fecha}`;
                let html = '';
                data.juegos.forEach((game, idx) => {
                    const homeLogo = `<div style="width:45px;height:45px;background:#c00a0a;border-radius:50%;display:flex;align-items:center;justify-content:center;">${game.home.charAt(0)}</div>`;
                    const awayLogo = `<div style="width:45px;height:45px;background:#c00a0a;border-radius:50%;display:flex;align-items:center;justify-content:center;">${game.away.charAt(0)}</div>`;
                    html += `
                    <div class="game-card">
                        <div class="game-header" onclick="toggleGame(${idx})">
                            <div class="team-display">
                                <div class="team">${awayLogo}<div class="team-name">${game.away}</div></div>
                                <div class="vs">VS</div>
                                <div class="team">${homeLogo}<div class="team-name">${game.home}</div></div>
                            </div>
                            <div id="toggle-${idx}">▼</div>
                        </div>
                        <div class="game-details" id="details-${idx}">
                            <div class="prob-bar"><div class="prob-home" style="width:${game.prob_home}%;">🏠 ${game.prob_home}%</div><div class="prob-away" style="width:${game.prob_away}%;">✈️ ${game.prob_away}%</div></div>
                            <div><span class="prediction-badge">🏆 GANA: ${game.winner}</span><span class="prediction-badge secondary">📝 ${game.marcador}</span></div>
                            <div><span class="odds">💰 ${game.home}: ${game.home_odds||'N/A'}</span><span class="odds">${game.away}: ${game.away_odds||'N/A'}</span></div>
                        </div>
                    </div>`;
                });
                content.innerHTML = html;
            } catch(e) {
                content.innerHTML = '<div class="warning">❌ Error al cargar los datos</div>';
            }
        }
        
        function toggleGame(idx){
            const details = document.getElementById(`details-${idx}`);
            const toggle = document.getElementById(`toggle-${idx}`);
            details.classList.toggle('active');
            toggle.style.transform = details.classList.contains('active') ? 'rotate(180deg)' : 'rotate(0deg)';
        }
        
        document.getElementById('adminPanelBtn').addEventListener('click', async () => {
            const res = await fetch('/api/admin/users');
            const data = await res.json();
            let html = '<h3>👑 Panel Admin</h3><table class="admin-table"><tr><th>Email</th><th>Plan</th><th>Acciones</th></tr>';
            data.users.forEach(u => {
                html += `<tr><td>${u.email}</td><td>${u.plan}</td><td><button class="btn-small btn-edit" onclick="editarUsuario('${u.email}','${u.plan}')">Editar</button></td></tr>`;
            });
            html += '</table>';
            document.getElementById('adminPanel').innerHTML = html;
            document.getElementById('adminPanel').style.display = 'block';
        });
        
        function editarUsuario(email, plan){
            const nuevoPlan = prompt('Nuevo plan (free/premium/admin):', plan);
            if(nuevoPlan){
                fetch(`/api/admin/user/${email}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({plan: nuevoPlan})
                }).then(() => {
                    alert('Usuario actualizado');
                    document.getElementById('adminPanelBtn').click();
                });
            }
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
