import traceback
from backend.services.scalping_logic_service import (
    detect_entry_signal,
    detect_exit_signal,
    get_latest_price,
    get_atr,
)
from backend.services.trade_executor_service import (
    execute_buy_order,
    execute_sell_order,
    get_current_position,
    get_trade_fees,
)
from backend.services.risk_management_service import (
    calculate_position_size,
    is_circuit_breaker_triggered,
    can_open_new_trade,
    update_daily_loss,
)
from backend.services.memory_service import (
    save_trade_state,
    purge_closed_trades,
)
from backend.services.config_scalping import SCALPING_CONFIG
from backend.services.logger_service import log_trade_event
from backend.services.stop_exit_logic import (
    calculate_take_profit,
    calculate_stop_loss,
    should_exit_trade,
)
from backend.services.scalping_pressure_service import (  # Nova importação
    generate_pressure_signal,  # Nova importação
)


async def agent_scalping(symbol: str):
    """
    Agente de scalping refinado, assíncrono, com gestão de TP/SL e execução automatizada.
    Integra a análise de pressão de mercado para decisões de entrada e saída.
    """
    try:
        if await is_circuit_breaker_triggered():
            await log_trade_event(symbol, "CIRCUIT_BREAKER", "Bot pausado por perdas")
            return

        position = await get_current_position(symbol)

        # Obter os dados de pressão antes de qualquer decisão
        pressure_data = await generate_pressure_signal(symbol)
        market_pressure_signal = pressure_data["signal"]
        await log_trade_event(
            symbol,
            "MARKET_PRESSURE",
            f"Sinal de Pressão: {market_pressure_signal} | Fatores Compra: {pressure_data['buy_factors']} | Fatores Venda: {pressure_data['sell_factors']}",
        )

        if position:
            current_price = await get_latest_price(symbol)
            tp_price = position.get("tp_price")
            sl_price = position.get("sl_price")

            # ✅ Verificar TP ou SL antes do sinal técnico
            tp_hit, reason = should_exit_trade(
                position["entry_price"], current_price, tp_price, sl_price
            )

            if tp_hit:
                try:
                    sell_order = await execute_sell_order(symbol, position["quantity"])
                    if sell_order:
                        exit_price = sell_order["price"]
                        fee_saida = await get_trade_fees(sell_order)
                        fee_entrada = position.get("fee", 0.0)

                        pnl = ((exit_price * position["quantity"]) - fee_saida) - (
                            (position["entry_price"] * position["quantity"])
                            + fee_entrada
                        )

                        await update_daily_loss(pnl)
                        await purge_closed_trades(symbol)
                        await log_trade_event(
                            symbol,
                            "SELL",
                            f"Saída a {exit_price} | Lucro líquido: {pnl:.4f} USD | Motivo: {reason}",
                        )
                    else:
                        await log_trade_event(
                            symbol, "ORDER_FAIL", "Falha na execução de venda"
                        )

                except Exception as e:
                    await log_trade_event(
                        symbol, "API_ERROR", f"Erro na venda: {str(e)}"
                    )
                    traceback.print_exc()
                return  # já vendeu, não continua

            # ✅ Se não atingiu TP/SL, verifica lógica técnica E pressão de mercado
            exit_signal, reason = await detect_exit_signal(symbol, position)

            # Adiciona a condição de pressão para saída: se há um sinal de venda agressivo da pressão
            if exit_signal or market_pressure_signal in [
                "SELL_AGGRESSIVE",
                "SELL_MODERATE",
            ]:
                if (
                    market_pressure_signal in ["SELL_AGGRESSIVE", "SELL_MODERATE"]
                    and not exit_signal
                ):
                    reason = f"Sinal de Pressão para Saída: {market_pressure_signal}"

                try:
                    sell_order = await execute_sell_order(symbol, position["quantity"])
                    if sell_order:
                        exit_price = sell_order["price"]
                        fee_saida = await get_trade_fees(sell_order)
                        fee_entrada = position.get("fee", 0.0)

                        pnl = ((exit_price * position["quantity"]) - fee_saida) - (
                            (position["entry_price"] * position["quantity"])
                            + fee_entrada
                        )

                        await update_daily_loss(pnl)
                        await purge_closed_trades(symbol)
                        await log_trade_event(
                            symbol,
                            "SELL",
                            f"Saída a {exit_price} | Lucro líquido: {pnl:.4f} USD | Motivo: {reason}",
                        )
                    else:
                        await log_trade_event(
                            symbol, "ORDER_FAIL", "Falha na execução de venda"
                        )

                except Exception as e:
                    await log_trade_event(
                        symbol, "API_ERROR", f"Erro na venda: {str(e)}"
                    )
                    traceback.print_exc()

        else:  # Não há posição aberta
            if not await can_open_new_trade(symbol):
                return

            entry_signal, entry_data = await detect_entry_signal(symbol)

            # Adiciona a condição de pressão para entrada: só entra se houver sinal técnico E pressão de compra
            if entry_signal and market_pressure_signal in [
                "BUY_AGGRESSIVE",
                "BUY_MODERATE",
            ]:
                try:
                    position_size = await calculate_position_size(symbol)
                    buy_order = await execute_buy_order(symbol, position_size)
                    if buy_order:
                        entry_price = buy_order["price"]
                        fee_entrada = await get_trade_fees(buy_order)

                        atr = await get_atr(symbol)
                        tp_price = calculate_take_profit(entry_price, atr)
                        sl_price = calculate_stop_loss(entry_price, atr)

                        await save_trade_state(
                            symbol,
                            entry_price,
                            position_size,
                            entry_data,
                            fee_entrada,
                            tp_price,
                            sl_price,
                        )
                        await log_trade_event(
                            symbol,
                            "BUY",
                            f"Entrada a {entry_price} com qty {position_size} | TP: {tp_price} | SL: {sl_price} | Pressão: {market_pressure_signal}",
                        )
                    else:
                        await log_trade_event(
                            symbol, "ORDER_FAIL", "Falha na execução de compra"
                        )

                except Exception as e:
                    await log_trade_event(
                        symbol, "API_ERROR", f"Erro na compra: {str(e)}"
                    )
                    traceback.print_exc()
            elif (
                entry_signal
            ):  # Log apenas para quando há sinal técnico, mas não de pressão
                await log_trade_event(
                    symbol,
                    "NO_ENTRY",
                    f"Sinal técnico presente, mas sem pressão de compra forte. Pressão: {market_pressure_signal}",
                )

    except Exception as e:
        await log_trade_event(symbol, "FATAL_ERROR", f"Erro inesperado: {str(e)}")
        traceback.print_exc()
