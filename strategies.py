"""
Estrategias. Cada una recibe el DataFrame OHLCV y devuelve una Serie de señales:
1 = quiero estar comprado, 0 = quiero estar fuera.
Regla de oro: solo usar datos hasta el día actual (nada de mirar el futuro).
"""

import pandas as pd


def buy_and_hold(df: pd.DataFrame) -> pd.Series:
    """Línea base: comprar el día 1 y no tocar nada. A esto hay que ganarle."""
    return pd.Series(1, index=df.index)


def sma_crossover(df: pd.DataFrame, fast: int = 20, slow: int = 60) -> pd.Series:
    """
    Cruce de medias móviles (seguimiento de tendencia).
    Comprado cuando la media rápida está por encima de la lenta.
    Idea: si el promedio reciente supera al promedio largo, hay tendencia alcista.
    """
    sma_fast = df["close"].rolling(fast).mean()
    sma_slow = df["close"].rolling(slow).mean()
    return (sma_fast > sma_slow).astype(int)


def rsi_reversion(df: pd.DataFrame, period: int = 14, buy_below: int = 30, sell_above: int = 60) -> pd.Series:
    """
    Reversión a la media con RSI.
    RSI < 30 = "sobrevendido" -> comprar. RSI > 60 -> vender.
    Idea: los pánicos de corto plazo tienden a rebotar.
    """
    delta = df["close"].diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss
    rsi = 100 - 100 / (1 + rs)

    # Máquina de estados: entra en sobreventa, sale en fuerza
    signal = pd.Series(0, index=df.index)
    holding = False
    for i in range(len(df)):
        if not holding and rsi.iloc[i] < buy_below:
            holding = True
        elif holding and rsi.iloc[i] > sell_above:
            holding = False
        signal.iloc[i] = 1 if holding else 0
    return signal


ESTRATEGIAS = {
    "Buy & Hold": buy_and_hold,
    "SMA 20/60 crossover": sma_crossover,
    "RSI reversion (30/60)": rsi_reversion,
}
