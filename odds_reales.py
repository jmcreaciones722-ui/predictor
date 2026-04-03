"""
PRONÓSTICOS REALES CON ODDS EN VIVO
Usando API key
"""

import requests
from datetime import datetime

# TU API KEY
API_KEY = "67a8f29d5a4de82b616e920824663e3a"

def get_nfl_odds_live():
    """Obtiene odds EN VIVO de la NFL hoy"""
    
    url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
    
    params = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'h2h,spreads,totals',
        'bookmakers': 'draftkings,fanduel,betmgm',
        'oddsFormat': 'american'
    }
    
    print("📡 Conectando a The Odds API...")
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            games = response.json()
            print(f"✅ Conexión exitosa! Juegos encontrados: {len(games)}")
            return games
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def convert_odds_to_probability(odds):
    """Convierte odds americanas a probabilidad"""
    if odds is None:
        return 0.5
    
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)

def display_live_odds():
    """Muestra odds en vivo"""
    
    games = get_nfl_odds_live()
    
    if not games:
        print("\n❌ No se pudieron obtener odds")
        return
    
    print("\n" + "=" * 70)
    print(f"🏈 ODDS EN VIVO - NFL {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    for idx, game in enumerate(games, 1):
        home = game['home_team']
        away = game['away_team']
        
        print(f"\n{idx}. {away} @ {home}")
        
        # Buscar odds
        for bookmaker in game['bookmakers']:
            for market in bookmaker['markets']:
                if market['key'] == 'h2h':
                    outcomes = market['outcomes']
                    
                    home_odds = next((o['price'] for o in outcomes if o['name'] == home), None)
                    away_odds = next((o['price'] for o in outcomes if o['name'] == away), None)
                    
                    if home_odds and away_odds:
                        home_prob = convert_odds_to_probability(home_odds)
                        
                        print(f"   📊 {bookmaker['key'].upper()}:")
                        print(f"      {home}: {home_odds} ({home_prob:.1%})")
                        print(f"      {away}: {away_odds}")
                        
                        if home_odds < 0:
                            print(f"      ⭐ Favorito: {home}")
                        elif away_odds < 0:
                            print(f"      ⭐ Favorito: {away}")
                        break
    
    # Mostrar resumen de cuotas
    print("\n" + "=" * 70)
    print("📊 ANÁLISIS DE PARLEY - FAVORITOS")
    print("=" * 70)
    
    # Encontrar los 3 favoritos más probables
    favorites = []
    
    for game in games[:10]:
        home = game['home_team']
        away = game['away_team']
        
        for bookmaker in game['bookmakers']:
            for market in bookmaker['markets']:
                if market['key'] == 'h2h':
                    outcomes = market['outcomes']
                    
                    home_odds = next((o['price'] for o in outcomes if o['name'] == home), None)
                    away_odds = next((o['price'] for o in outcomes if o['name'] == away), None)
                    
                    if home_odds and away_odds:
                        home_prob = convert_odds_to_probability(home_odds)
                        
                        if home_odds < 0:
                            favorites.append({
                                'game': f"{away} @ {home}",
                                'favorite': home,
                                'odds': home_odds,
                                'prob': home_prob
                            })
                        elif away_odds < 0:
                            favorites.append({
                                'game': f"{away} @ {home}",
                                'favorite': away,
                                'odds': away_odds,
                                'prob': 1 - home_prob
                            })
                        break
            break
    
    # Ordenar por probabilidad
    favorites.sort(key=lambda x: x['prob'], reverse=True)
    
    print("\n🎯 TOP 3 FAVORITOS DEL DÍA:")
    for i, fav in enumerate(favorites[:3], 1):
        print(f"\n{i}. {fav['game']}")
        print(f"   Favorito: {fav['favorite']} (Odds: {fav['odds']})")
        print(f"   Probabilidad: {fav['prob']:.1%}")
    
    # Calcular parley de 3
    if len(favorites) >= 3:
        combined_prob = favorites[0]['prob'] * favorites[1]['prob'] * favorites[2]['prob']
        
        print("\n" + "=" * 70)
        print("🎲 PARLEY DE 3 EQUIPOS (apostando a los favoritos)")
        print("=" * 70)
        print(f"📈 Probabilidad de éxito: {combined_prob:.2%}")
        
        # Payout típico parley 3 equipos es 6:1
        expected_value = (combined_prob * 6) - (1 - combined_prob)
        print(f"💵 Valor esperado: {expected_value:.2%}")
        
        if expected_value > 0.15:
            print("✅ RECOMENDACIÓN: MUY FAVORABLE")
            print("💰 Stake sugerido: 3-5% del bankroll")
        elif expected_value > 0:
            print("⚠️ RECOMENDACIÓN: VALOR JUSTO")
            print("💰 Stake sugerido: 1-2% del bankroll")
        else:
            print("❌ RECOMENDACIÓN: EVITAR")
            print("💰 Stake sugerido: 0%")

# EJECUTAR
if __name__ == "__main__":
    print("=" * 70)
    print("🏈 ODDS REALES NFL - EN VIVO")
    print("=" * 70)
    
    display_live_odds()
    
    print("\n" + "=" * 70)
    print("⚠️ IMPORTANTE:")
    print("• Estos son odds REALES en vivo")
    print("• Las probabilidades cambian constantemente")
    print("• Apostar conlleva riesgo")
    print("=" * 70)