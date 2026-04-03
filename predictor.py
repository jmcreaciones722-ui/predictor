"""
SISTEMA DE PREDICCIÓN PARLEY NFL - VERSIÓN PARA WINDOWS
Copia TODO este código en el Bloc de Notas y guarda (Ctrl+G)
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import warnings
warnings.filterwarnings('ignore')

class SimpleParleyPredictor:
    def __init__(self):
        self.model = None
        
    def create_sample_data(self):
        """Crea datos de ejemplo para probar"""
        np.random.seed(42)
        n_games = 500
        
        # Características simuladas
        data = {
            'home_offense': np.random.normal(100, 15, n_games),
            'home_defense': np.random.normal(100, 15, n_games),
            'away_offense': np.random.normal(100, 15, n_games),
            'away_defense': np.random.normal(100, 15, n_games),
            'home_rest_days': np.random.choice([4,6,7,8,10], n_games),
            'away_rest_days': np.random.choice([4,6,7,8,10], n_games),
        }
        
        df = pd.DataFrame(data)
        
        # Calcular probabilidad de victoria local
        df['home_advantage'] = (df['home_offense'] - df['away_defense']) / 100
        df['away_advantage'] = (df['away_offense'] - df['home_defense']) / 100
        df['rest_advantage'] = (df['home_rest_days'] - df['away_rest_days']) / 20
        df['win_prob'] = 0.5 + df['home_advantage'] - df['away_advantage'] + df['rest_advantage']
        df['win_prob'] = df['win_prob'].clip(0, 1)
        
        # Resultado (1 = gana local, 0 = pierde)
        df['home_win'] = (np.random.random(n_games) < df['win_prob']).astype(int)
        
        return df
    
    def train(self):
        """Entrena el modelo"""
        print("=" * 50)
        print("📊 Creando datos de entrenamiento...")
        print("=" * 50)
        df = self.create_sample_data()
        
        features = ['home_advantage', 'away_advantage', 'rest_advantage']
        X = df[features]
        y = df['home_win']
        
        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Entrenar modelo
        print("🤖 Entrenando modelo de Regresión Logística...")
        self.model = LogisticRegression()
        self.model.fit(X_train, y_train)
        
        # Evaluar
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n✅ Precisión del modelo: {accuracy:.2%}")
        print(f"\n📈 Coeficientes del modelo:")
        for feat, coef in zip(features, self.model.coef_[0]):
            print(f"   • {feat}: {coef:.4f}")
        
        return accuracy
    
    def predict(self, home_offense, home_defense, away_offense, away_defense, 
                home_rest, away_rest, home_name="Local", away_name="Visitante"):
        """Predice un juego específico"""
        if self.model is None:
            raise Exception("Primero ejecuta train()")
        
        # Calcular features
        home_advantage = (home_offense - away_defense) / 100
        away_advantage = (away_offense - home_defense) / 100
        rest_advantage = (home_rest - away_rest) / 20
        
        # Predicción
        X = np.array([[home_advantage, away_advantage, rest_advantage]])
        prob = self.model.predict_proba(X)[0, 1]
        
        # Determinar nivel de confianza
        if prob > 0.7:
            confidence_level = "ALTA"
        elif prob > 0.6:
            confidence_level = "MEDIA"
        else:
            confidence_level = "BAJA"
        
        return {
            'win_probability': prob,
            'prediction': f"{home_name} GANA" if prob > 0.5 else f"{away_name} GANA",
            'confidence': abs(prob - 0.5) * 2,
            'confidence_level': confidence_level
        }
    
    def simulate_parley(self, games):
        """Simula un parley con múltiples juegos"""
        combined_prob = 1
        for game in games:
            combined_prob *= game['win_probability']
        
        # Payout típico para diferentes tamaños de parley
        if len(games) == 2:
            payout = 2.6  # Odds típicas 2.6:1
        elif len(games) == 3:
            payout = 6    # 6:1
        elif len(games) == 4:
            payout = 12   # 12:1
        elif len(games) == 5:
            payout = 25   # 25:1
        else:
            payout = len(games) * 2
        
        expected_value = (combined_prob * payout) - (1 - combined_prob)
        
        # Recomendación basada en valor esperado
        if expected_value > 0.2:
            recommendation = "✅ MUY RECOMENDADO"
            stake = "3-5% del bankroll"
        elif expected_value > 0.1:
            recommendation = "⚠️ RECOMENDADO con precaución"
            stake = "1-2% del bankroll"
        elif expected_value > 0:
            recommendation = "📊 VALOR JUSTO"
            stake = "0.5-1% del bankroll"
        else:
            recommendation = "❌ NO RECOMENDADO"
            stake = "0% - No apostar"
        
        return {
            'games': len(games),
            'success_probability': combined_prob,
            'expected_value': expected_value,
            'recommendation': recommendation,
            'recommended_stake': stake
        }

def mostrar_menu():
    """Muestra el menú principal"""
    print("\n" + "=" * 50)
    print("🏈 SISTEMA DE PREDICCIÓN PARLEY NFL")
    print("=" * 50)
    print("1. Ver predicciones de ejemplo")
    print("2. Crear mi propio parley")
    print("3. Salir")
    print("=" * 50)

# EJECUTAR EL PROGRAMA
if __name__ == "__main__":
    # Crear y entrenar el predictor
    predictor = SimpleParleyPredictor()
    accuracy = predictor.train()
    
    while True:
        mostrar_menu()
        opcion = input("\nSelecciona una opción (1-3): ")
        
        if opcion == "1":
            print("\n" + "=" * 50)
            print("🎯 PREDICCIONES PARA LA SEMANA (EJEMPLO)")
            print("=" * 50)
            
            # Juego 1: Chiefs vs Bills
            pred1 = predictor.predict(
                home_offense=118, home_defense=95,  # Chiefs
                away_offense=112, away_defense=98,  # Bills
                home_rest=7, away_rest=7,
                home_name="Kansas City Chiefs", away_name="Buffalo Bills"
            )
            print(f"\n1. Kansas City Chiefs vs Buffalo Bills")
            print(f"   🏈 Probabilidad Chiefs: {pred1['win_probability']:.1%}")
            print(f"   📊 Predicción: {pred1['prediction']}")
            print(f"   ⭐ Confianza: {pred1['confidence_level']}")
            
            # Juego 2: 49ers vs Eagles
            pred2 = predictor.predict(
                home_offense=115, home_defense=90,  # 49ers
                away_offense=110, away_defense=96,  # Eagles
                home_rest=10, away_rest=7,
                home_name="San Francisco 49ers", away_name="Philadelphia Eagles"
            )
            print(f"\n2. San Francisco 49ers vs Philadelphia Eagles")
            print(f"   🏈 Probabilidad 49ers: {pred2['win_probability']:.1%}")
            print(f"   📊 Predicción: {pred2['prediction']}")
            print(f"   ⭐ Confianza: {pred2['confidence_level']}")
            
            # Juego 3: Ravens vs Lions
            pred3 = predictor.predict(
                home_offense=120, home_defense=92,  # Ravens
                away_offense=114, away_defense=94,  # Lions
                home_rest=7, away_rest=10,
                home_name="Baltimore Ravens", away_name="Detroit Lions"
            )
            print(f"\n3. Baltimore Ravens vs Detroit Lions")
            print(f"   🏈 Probabilidad Ravens: {pred3['win_probability']:.1%}")
            print(f"   📊 Predicción: {pred3['prediction']}")
            print(f"   ⭐ Confianza: {pred3['confidence_level']}")
            
            # Analizar parley de 3 juegos
            games = [pred1, pred2, pred3]
            print("\n" + "=" * 50)
            print("📊 ANÁLISIS DEL PARLEY (3 JUEGOS)")
            print("=" * 50)
            
            parley_result = predictor.simulate_parley(games)
            print(f"🎲 Parley de {parley_result['games']} equipos")
            print(f"📈 Probabilidad de éxito: {parley_result['success_probability']:.2%}")
            print(f"💵 Valor esperado: {parley_result['expected_value']:.2%}")
            print(f"🎯 Recomendación: {parley_result['recommendation']}")
            print(f"💰 Stake sugerido: {parley_result['recommended_stake']}")
            
            input("\nPresiona Enter para continuar...")
        
        elif opcion == "2":
            print("\n" + "=" * 50)
            print("🎯 CREAR MI PROPIO PARLEY")
            print("=" * 50)
            print("\nIngresa los datos de tus juegos:")
            
            games = []
            num_games = int(input("¿Cuántos juegos en tu parley? (2-5): "))
            
            for i in range(num_games):
                print(f"\n--- JUEGO {i+1} ---")
                home = input("Equipo Local: ")
                away = input("Equipo Visitante: ")
                
                print("\nEstadísticas (valores típicos: 80-120):")
                home_off = float(input("Ofensiva Local (ej: 115): "))
                home_def = float(input("Defensiva Local (ej: 95): "))
                away_off = float(input("Ofensiva Visitante (ej: 110): "))
                away_def = float(input("Defensiva Visitante (ej: 100): "))
                home_rest = int(input("Días de descanso Local (ej: 7): "))
                away_rest = int(input("Días de descanso Visitante (ej: 7): "))
                
                pred = predictor.predict(
                    home_off, home_def, away_off, away_def,
                    home_rest, away_rest,
                    home, away
                )
                
                games.append(pred)
                print(f"\n   Resultado: {pred['prediction']} (Prob: {pred['win_probability']:.1%})")
            
            print("\n" + "=" * 50)
            print("📊 ANÁLISIS DE TU PARLEY")
            print("=" * 50)
            
            parley_result = predictor.simulate_parley(games)
            print(f"🎲 Parley de {parley_result['games']} equipos")
            print(f"📈 Probabilidad de éxito: {parley_result['success_probability']:.2%}")
            print(f"💵 Valor esperado: {parley_result['expected_value']:.2%}")
            print(f"🎯 Recomendación: {parley_result['recommendation']}")
            print(f"💰 Stake sugerido: {parley_result['recommended_stake']}")
            
            input("\nPresiona Enter para continuar...")
        
        elif opcion == "3":
            print("\n👋 ¡Gracias por usar el sistema! Recuerda apostar con responsabilidad.")
            break
        
        else:
            print("\n❌ Opción inválida. Intenta de nuevo.")
    
    print("\n" + "=" * 50)
    print("⚠️ AVISO IMPORTANTE:")
    print("Este sistema es para fines educativos")
    print("Las apuestas deportivas conllevan riesgo")
    print("Siempre establece límites de bankroll")
    print("=" * 50)