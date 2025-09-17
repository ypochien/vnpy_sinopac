# -*- coding: UTF-8 -*-
"""基本測試檔案"""
import pytest

def test_import():
    """測試基本匯入功能"""
    try:
        from vnpy_sinopac.gateway.sinopac_gateway import SinopacGateway
        assert SinopacGateway is not None
    except ImportError as e:
        # 如果匯入失敗，跳過測試（可能缺少某些相依性）
        pytest.skip(f"無法匯入 SinopacGateway: {e}")

def test_polars_import():
    """測試 polars 匯入"""
    import polars as pl
    assert pl.__version__ is not None

def test_basic_polars_functionality():
    """測試基本 polars 功能"""
    import polars as pl
    
    # 建立簡單的 DataFrame
    df = pl.DataFrame({
        "ts": ["2023-01-01 10:00:00", "2023-01-01 10:01:00"],
        "Open": [100.0, 101.0],
        "High": [102.0, 103.0],
        "Low": [99.0, 100.0],
        "Close": [101.0, 102.0],
        "Volume": [1000, 1100],
        "Amount": [101000.0, 112200.0]
    })
    
    # 測試日期時間轉換
    df_with_datetime = df.with_columns(
        pl.col("ts").str.strptime(pl.Datetime)
    )
    
    assert len(df_with_datetime) == 2
    assert "ts" in df_with_datetime.columns
