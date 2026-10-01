import pandas as pd

from gb_ml.profiling.visualization import iqr_limits, iqr_outlier_mask


def test_iqr_limits_aplica_regra_de_tukey():
    series = pd.Series([1, 2, 3, 4, 100])

    limits = iqr_limits(series, multiplier=1.5)

    assert limits["q1"] == 2.0
    assert limits["q3"] == 4.0
    assert limits["iqr"] == 2.0
    assert limits["lower"] == -1.0
    assert limits["upper"] == 7.0


def test_iqr_outlier_mask_detecta_extremo():
    series = pd.Series([1, 2, 3, 4, 100])

    mask = iqr_outlier_mask(series)

    assert mask.tolist() == [False, False, False, False, True]
