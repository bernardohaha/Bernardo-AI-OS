import time
from backend.services.advisor import positions_advisor, technical_advisor


def run_advisors():
    print("🚀 Início da Análise Completa")

    print("\n📊 Analisando Posições Reais...")
    positions_advisor.analyze_positions()

    print("\n📈 Analisando Análise Técnica (Watchlist)...")
    technical_advisor.analyze_symbols()

    print("✅ Análise concluída.\n")


if __name__ == "__main__":
    while True:
        run_advisors()
        print("⏳ A aguardar próximo ciclo...\n")
        time.sleep(60 * 15)  # Faz a análise a cada 15 minutos
