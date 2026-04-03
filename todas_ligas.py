"""
SISTEMA COMPLETO DE ODDS REALES
Múltiples Ligas: NBA, Fútbol (EPL/La Liga/Bundesliga/Serie A), NHL
Actualizado: Abril 2026
"""

import requests
from datetime import datetime
import json
import time

# TU API KEY
API_KEY = "67a8f29d5a4de82b616e920824663e3a"

# Configuración de ligas
LEAGUES = {
    # Baloncesto
    'NBA': {
        'sport': 'basketball_nba',
        'name': '🏀 NBA - Baloncesto',
        'region': 'us',
        'bookmakers': 'draftkings,fanduel',
        'emoji': '🏀'
    },
    'EuroLeague': {
        'sport': 'basketball_euroleague',
        'name': '🏀 EuroLeague',
        'region': 'eu',
        'bookmakers': 'bet365,williamhill',
        'emoji': '🏀'
    },
    'NCAA Basketball': {
        'sport': 'basketball_ncaab',
        'name': '🏀 NCAA Baloncesto',
        'region': 'us',
        'bookmakers': 'draftkings,fanduel',
        'emoji': '🏀'
    },
    
    # Fútbol (Soccer)
    'Premier League': {
        'sport': 'soccer_epl',
        'name': '⚽ Premier League (Inglaterra)',
        'region': 'uk',
        'bookmakers': 'bet365,williamhill',
        'emoji': '⚽'
    },
    'La Liga': {
        'sport': 'soccer_spain_la_liga',
        'name': '⚽ La Liga (España)',
        'region': 'eu',
        'bookmakers': 'bet365,williamhill',
        'emoji': '⚽'
    },
    'Bundesliga': {
        'sport': 'soccer_germany_bundesliga',
        'name': '⚽ Bundesliga (Alemania)',
        'region': 'eu',
        'bookmakers': 'bet365,williamhill',
        'emoji': '⚽'
    },
    'Serie A': {
        'sport': 'soccer_italy_serie_a',
        'name': '⚽ Serie A (Italia)',
        'region': 'eu',
        'bookmakers': 'bet365,williamhill',
        'emoji': '⚽'
    },
    'Ligue 1': {
        'sport': 'soccer_france_ligue_one',
        'name': '⚽ Ligue 1 (Francia)',
        'region': 'eu',
        'bookmakers': 'bet365,williamhill',
        'emoji': '⚽'
    },
    'UEFA Champions': {
        'sport': 'soccer_uefa_champs_league',
        'name': '⚽ UEFA Champions League',
        'region': 'eu',
        'bookmakers': 'bet365,williamhill',
        'emoji': '⚽'
    },
    'MLS': {
        'sport': 'soccer_usa_mls',
        'name': '⚽ MLS (USA)',
        'region': 'us',
        'bookmakers': 'draftkings,fanduel',
        'emoji': '⚽'
    },
    
    # Hockey
    'NHL': {
        'sport': 'icehockey_nhl',
        'name': '🏒 NHL - Hockey',
        'region': 'us',
        'bookmakers': 'draftkings,fanduel',
        'emoji': '🏒'
    },
    'KHL': {
        'sport': 'icehockey_khl',
        'name': '🏒 KHL (Rusia)',
        'region': 'eu',
        'bookmakers': 'bet365',
        'emoji': '🏒'
    },
    
    # Otros deportes populares
    'MLB': {
        'sport': 'baseball_mlb',
        'name': '⚾ MLB - Béisbol',
        'region': 'us',
        'bookmakers': 'draftkings,fanduel',
        'emoji': '⚾'
    },
    'NFL': {
        'sport': 'americanfootball_nfl',
        'name': '🏈 NFL - Fútbol Americano',
        'region': 'us',
        'bookmakers': 'draftkings,fanduel',
        'emoji': '🏈'
    },
    'Tennis ATP': {
        'sport': 'tennis_atp_french_open',
        'name': '🎾 Tennis ATP',
        'region': 'eu',
        'bookmakers': 'bet365',
        'emoji': '🎾'
    },
    'UFC': {
        'sport': 'mma_mixed_martial_arts',
        'name': '🥊 UFC',
        'region': 'us',
        'bookmakers': 'draftkings',
        'emoji': '🥊'
    }
}

def get_odds(sport_key, region='us', bookmakers='draftkings,fanduel'):
    """Obtiene odds de una liga específica"""
    
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    
    params = {
        'apiKey': API_KEY,
        'regions': region,
        'markets': 'h2h,spreads,totals',
        'bookmakers': bookmakers,
        'oddsFormat': 'american'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except Exception as e:
        return None

def convert_odds_to_probability(odds):
    """Convierte odds americanas a probabilidad"""
    if odds is None:
        return 0.5
    
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)

def analyze_parley(games, max_games=3):
    """Analiza parley con los mejores favoritos"""
    
    favorites = []
    
    for game in games:
        home = game.get('home_team', '')
        away = game.get('away_team', '')
        
        if not home or not away:
            continue
            
        for bookmaker in game.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market.get('key') == 'h2h':
                    outcomes = market.get('outcomes', [])
                    
                    home_odds = next((o.get('price') for o in outcomes if o.get('name') == home), None)
                    
                    if home_odds and home_odds < 0:
                        prob = convert_odds_to_probability(home_odds)
                        favorites.append({
                            'game': f"{away} @ {home}",
                            'favorite': home,
                            'odds': home_odds,
                            'prob': prob,
                            'bookmaker': bookmaker.get('key', 'unknown')
                        })
                    else:
                        # Buscar favorito visitante
                        away_odds = next((o.get('price') for o in outcomes if o.get('name') == away), None)
                        if away_odds and away_odds < 0:
                            prob = convert_odds_to_probability(away_odds)
                            favorites.append({
                                'game': f"{away} @ {home}",
                                'favorite': away,
                                'odds': away_odds,
                                'prob': prob,
                                'bookmaker': bookmaker.get('key', 'unknown')
                            })
                    break
            break
    
    # Ordenar por probabilidad
    favorites.sort(key=lambda x: x['prob'], reverse=True)
    
    if len(favorites) >= max_games:
        top_games = favorites[:max_games]
        combined_prob = 1
        for game in top_games:
            combined_prob *= game['prob']
        
        # Payouts típicos para parleys
        payouts = {2: 2.6, 3: 6, 4: 12, 5: 25}
        payout = payouts.get(max_games, max_games * 2)
        
        expected_value = (combined_prob * payout) - (1 - combined_prob)
        
        return {
            'success_probability': combined_prob,
            'expected_value': expected_value,
            'games': top_games,
            'recommended': expected_value > 0.1
        }
    
    return None

def display_league(league_key, league_info):
    """Muestra odds de una liga específica"""
    
    print(f"\n{'=' * 80}")
    print(f"{league_info['emoji']} {league_info['name']} {league_info['emoji']}")
    print(f"{'=' * 80}")
    
    games = get_odds(
        league_info['sport'],
        league_info['region'],
        league_info['bookmakers']
    )
    
    if not games:
        print(f"   ⚠️ No hay partidos disponibles hoy")
        return None
    
    print(f"   📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   🎯 Partidos encontrados: {len(games)}\n")
    
    all_games = []
    
    for idx, game in enumerate(games[:8], 1):  # Mostrar máx 8 partidos
        home = game.get('home_team', 'Unknown')
        away = game.get('away_team', 'Unknown')
        
        print(f"   {idx}. {away} @ {home}")
        
        game_info = {'home': home, 'away': away}
        
        for bookmaker in game.get('bookmakers', [])[:2]:  # Máx 2 casas
            for market in bookmaker.get('markets', []):
                if market.get('key') == 'h2h':
                    outcomes = market.get('outcomes', [])
                    
                    home_odds = next((o.get('price') for o in outcomes if o.get('name') == home), None)
                    away_odds = next((o.get('price') for o in outcomes if o.get('name') == away), None)
                    
                    if home_odds and away_odds:
                        home_prob = convert_odds_to_probability(home_odds)
                        
                        print(f"      📊 {bookmaker.get('key', 'unknown').upper()}:")
                        print(f"         {home}: {home_odds} ({home_prob:.1%})")
                        print(f"         {away}: {away_odds}")
                        
                        # Determinar favorito
                        if home_odds < 0:
                            print(f"         ⭐ FAVORITO: {home}")
                            game_info['favorite'] = home
                            game_info['favorite_odds'] = home_odds
                            game_info['favorite_prob'] = home_prob
                        elif away_odds < 0:
                            print(f"         ⭐ FAVORITO: {away}")
                            game_info['favorite'] = away
                            game_info['favorite_odds'] = away_odds
                            game_info['favorite_prob'] = 1 - home_prob
                        else:
                            print(f"         ⚖️ PARTIDO EQUILIBRADO")
                        break
            break
        
        all_games.append(game_info)
        print()
    
    # Analizar parley para esta liga
    if len(games) >= 3:
        parley_result = analyze_parley(games[:10], 3)
        if parley_result:
            print(f"\n   {'─' * 60}")
            print(f"   🎲 PARLEY DE 3 EQUIPOS ({league_info['emoji']})")
            print(f"   {'─' * 60}")
            print(f"   📈 Probabilidad de éxito: {parley_result['success_probability']:.2%}")
            print(f"   💵 Valor esperado: {parley_result['expected_value']:.2%}")
            
            if parley_result['expected_value'] > 0.15:
                print(f"   ✅ RECOMENDACIÓN: MUY FAVORABLE")
                print(f"   💰 Stake: 3-5% del bankroll")
            elif parley_result['expected_value'] > 0:
                print(f"   ⚠️ RECOMENDACIÓN: VALOR JUSTO")
                print(f"   💰 Stake: 1-2% del bankroll")
            else:
                print(f"   ❌ RECOMENDACIÓN: EVITAR")
            
            print(f"\n   Juegos incluidos:")
            for i, game in enumerate(parley_result['games'], 1):
                print(f"      {i}. {game['game']}")
                print(f"         Favorito: {game['favorite']} (Odds: {game['odds']})")
                print(f"         Prob: {game['prob']:.1%}")
    
    return all_games

def get_best_parley_across_leagues():
    """Encuentra el mejor parley combinando favoritos de diferentes ligas"""
    
    print("\n" + "=" * 80)
    print("🎯 TOP PARLEY - MEJORES FAVORITOS DE TODAS LAS LIGAS")
    print("=" * 80)
    
    all_favorites = []
    
    # Recolectar favoritos de cada liga
    for league_key, league_info in LEAGUES.items():
        games = get_odds(
            league_info['sport'],
            league_info['region'],
            league_info['bookmakers']
        )
        
        if games:
            for game in games[:3]:  # Tomar top 3 de cada liga
                home = game.get('home_team', '')
                away = game.get('away_team', '')
                
                for bookmaker in game.get('bookmakers', []):
                    for market in bookmaker.get('markets', []):
                        if market.get('key') == 'h2h':
                            outcomes = market.get('outcomes', [])
                            
                            home_odds = next((o.get('price') for o in outcomes if o.get('name') == home), None)
                            
                            if home_odds and home_odds < 0:
                                prob = convert_odds_to_probability(home_odds)
                                all_favorites.append({
                                    'league': league_info['name'],
                                    'emoji': league_info['emoji'],
                                    'game': f"{away} @ {home}",
                                    'favorite': home,
                                    'odds': home_odds,
                                    'prob': prob
                                })
                            else:
                                away_odds = next((o.get('price') for o in outcomes if o.get('name') == away), None)
                                if away_odds and away_odds < 0:
                                    prob = convert_odds_to_probability(away_odds)
                                    all_favorites.append({
                                        'league': league_info['name'],
                                        'emoji': league_info['emoji'],
                                        'game': f"{away} @ {home}",
                                        'favorite': away,
                                        'odds': away_odds,
                                        'prob': prob
                                    })
                            break
                    break
    
    # Ordenar por probabilidad
    all_favorites.sort(key=lambda x: x['prob'], reverse=True)
    
    # Mostrar top 10 favoritos
    print("\n📊 TOP 10 FAVORITOS DEL DÍA (TODAS LAS LIGAS):")
    print("-" * 80)
    
    for i, fav in enumerate(all_favorites[:10], 1):
        print(f"\n{i}. {fav['emoji']} {fav['league']}")
        print(f"   {fav['game']}")
        print(f"   🎯 Favorito: {fav['favorite']} (Odds: {fav['odds']})")
        print(f"   📈 Probabilidad: {fav['prob']:.1%}")
    
    # Analizar parleys de diferentes tamaños
    print("\n" + "=" * 80)
    print("🎲 ANÁLISIS DE PARLEYS (COMBINANDO LIGAS)")
    print("=" * 80)
    
    for size in [2, 3, 4]:
        if len(all_favorites) >= size:
            top_games = all_favorites[:size]
            combined_prob = 1
            for game in top_games:
                combined_prob *= game['prob']
            
            payouts = {2: 2.6, 3: 6, 4: 12}
            payout = payouts.get(size, size * 2)
            expected_value = (combined_prob * payout) - (1 - combined_prob)
            
            print(f"\n🎲 PARLEY DE {size} EQUIPOS:")
            print(f"   📈 Probabilidad de éxito: {combined_prob:.2%}")
            print(f"   💵 Valor esperado: {expected_value:.2%}")
            
            if expected_value > 0.15:
                print(f"   ✅ MUY RECOMENDADO - Stake: 3-5%")
            elif expected_value > 0.05:
                print(f"   ⚠️ RECOMENDADO - Stake: 1-2%")
            elif expected_value > 0:
                print(f"   📊 VALOR JUSTO - Stake: 0.5-1%")
            else:
                print(f"   ❌ NO RECOMENDADO - Evitar")
            
            print(f"\n   Juegos:")
            for i, game in enumerate(top_games, 1):
                print(f"      {i}. {game['emoji']} {game['game']}")
                print(f"         {game['favorite']} ({game['odds']}) - {game['prob']:.1%}")

def show_available_sports():
    """Muestra todos los deportes disponibles en la API"""
    
    print("\n" + "=" * 80)
    print("📋 DEPORTES DISPONIBLES EN LA API")
    print("=" * 80)
    
    url = "https://api.the-odds-api.com/v4/sports"
    params = {'apiKey': API_KEY}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            sports = response.json()
            print(f"\nTotal deportes disponibles: {len(sports)}\n")
            
            for sport in sports[:20]:  # Mostrar primeros 20
                key = sport.get('key', '')
                title = sport.get('title', '')
                active = sport.get('active', False)
                
                if active:
                    print(f"   ✅ {title} ({key})")
        else:
            print(f"   Error: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")

# MENÚ PRINCIPAL
def main():
    print("=" * 80)
    print("🏆 SISTEMA DE ODDS REALES - MÚLTIPLES LIGAS 🏆")
    print("=" * 80)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 API Key: {API_KEY[:8]}...")
    
    while True:
        print("\n" + "=" * 80)
        print("MENÚ PRINCIPAL")
        print("=" * 80)
        print("1. 🏀 NBA - Baloncesto")
        print("2. ⚽ Premier League - Fútbol Inglés")
        print("3. ⚽ La Liga - Fútbol Español")
        print("4. ⚽ Bundesliga - Fútbol Alemán")
        print("5. ⚽ Serie A - Fútbol Italiano")
        print("6. 🏒 NHL - Hockey")
        print("7. 🎯 MEJOR PARLEY (Todas las ligas)")
        print("8. 📋 Ver todos los deportes disponibles")
        print("9. ⚾ MLB - Béisbol")
        print("10. 🏈 NFL - Fútbol Americano")
        print("11. 🎾 Tennis ATP")
        print("12. 🥊 UFC")
        print("0. ❌ Salir")
        print("=" * 80)
        
        opcion = input("\nSelecciona una opción (0-12): ").strip()
        
        if opcion == "0":
            print("\n👋 ¡Gracias por usar el sistema!")
            print("⚠️ Recuerda: Las apuestas conllevan riesgo. Apuesta con responsabilidad.")
            break
        
        elif opcion == "1":
            display_league('NBA', LEAGUES['NBA'])
        
        elif opcion == "2":
            display_league('Premier League', LEAGUES['Premier League'])
        
        elif opcion == "3":
            display_league('La Liga', LEAGUES['La Liga'])
        
        elif opcion == "4":
            display_league('Bundesliga', LEAGUES['Bundesliga'])
        
        elif opcion == "5":
            display_league('Serie A', LEAGUES['Serie A'])
        
        elif opcion == "6":
            display_league('NHL', LEAGUES['NHL'])
        
        elif opcion == "7":
            get_best_parley_across_leagues()
        
        elif opcion == "8":
            show_available_sports()
        
        elif opcion == "9":
            display_league('MLB', LEAGUES['MLB'])
        
        elif opcion == "10":
            display_league('NFL', LEAGUES['NFL'])
        
        elif opcion == "11":
            display_league('Tennis ATP', LEAGUES['Tennis ATP'])
        
        elif opcion == "12":
            display_league('UFC', LEAGUES['UFC'])
        
        else:
            print("\n❌ Opción inválida")
        
        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()