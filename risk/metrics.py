import numpy as np
import pandas as pd


def sharpe_ratio(returns: pd.Series, periods_per_year: int = 24 * 365) -> float:
    returns = returns.dropna()
    if returns.empty or returns.std() == 0:
        return 0.0
    return float(np.sqrt(periods_per_year) * returns.mean() / returns.std())
