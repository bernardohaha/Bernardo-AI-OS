import asyncio
import time
from backend.agents.agent_scalping import agent_scalping
from backend.config.config_scalping import SCALPING_CONFIG

# ⚙️ Parâmetros configuráveis
SYMBOLS = SCALPING_CONFIG.get("symbols_to_trade", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
LOOP_DELAY = SCALPING_CONFIG.get("check_interval_seconds", 0.8)


async def run_symbol_loop(symbol: str):
    """
    Loop assíncrono individual para um símbolo.
    Executa o agente de scalping ciclicamente com um delay fixo.
    """
    while True:
        try:
            start = time.perf_counter()
            print(f"[{symbol}] 🚀 Início da análise")

            await agent_scalping(symbol)

            duration = time.perf_counter() - start
            print(
                f"[{symbol}] ✅ Concluído em {duration:.2f}s. Pausa de {LOOP_DELAY}s...\n"
            )

        except Exception as e:
            print(f"[{symbol}] ❌ Erro inesperado: {e}")

        await asyncio.sleep(LOOP_DELAY)


async def main():
    """
    Inicia todos os loops assíncronos em paralelo.
    """
    print(f"🔁 Iniciando scalping para {len(SYMBOLS)} símbolos: {', '.join(SYMBOLS)}")
    tasks = [run_symbol_loop(symbol) for symbol in SYMBOLS]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Execução interrompida manualmente.")
