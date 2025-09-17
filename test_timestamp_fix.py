#!/usr/bin/env python
"""測試時間戳轉換修正"""

import polars as pl
from datetime import datetime

def test_timestamp_conversion():
    """測試不同型別的時間戳轉換"""
    
    # 測試案例 1: 整數時間戳（秒）
    print("測試案例 1: 整數時間戳（秒）")
    df1 = pl.DataFrame({
        "ts": [1700000000, 1700000060, 1700000120],
        "Open": [100.0, 101.0, 102.0],
        "High": [101.0, 102.0, 103.0],
        "Low": [99.0, 100.0, 101.0],
        "Close": [100.5, 101.5, 102.5],
        "Volume": [1000, 1100, 1200],
        "Amount": [100500.0, 111650.0, 123000.0]
    })
    
    print(f"原始 ts 型別: {df1['ts'].dtype}")
    
    # 轉換邏輯
    if df1["ts"].dtype == pl.Int64:
        ts_sample = df1["ts"][0]
        if ts_sample > 10**12:  # 毫秒
            df1 = df1.with_columns(
                pl.col("ts").cast(pl.Int64).truediv(1000).cast(pl.Datetime("s"))
            )
        else:  # 秒
            df1 = df1.with_columns(
                pl.col("ts").cast(pl.Datetime("s"))
            )
    
    print(f"轉換後 ts 型別: {df1['ts'].dtype}")
    print(df1.select("ts").head(3))
    print()
    
    # 測試案例 2: 整數時間戳（毫秒）
    print("測試案例 2: 整數時間戳（毫秒）")
    df2 = pl.DataFrame({
        "ts": [1700000000000, 1700000060000, 1700000120000],
        "Open": [100.0, 101.0, 102.0],
        "High": [101.0, 102.0, 103.0],
        "Low": [99.0, 100.0, 101.0],
        "Close": [100.5, 101.5, 102.5],
        "Volume": [1000, 1100, 1200],
        "Amount": [100500.0, 111650.0, 123000.0]
    })
    
    print(f"原始 ts 型別: {df2['ts'].dtype}")
    
    # 轉換邏輯
    if df2["ts"].dtype == pl.Int64:
        ts_sample = df2["ts"][0]
        if ts_sample > 10**12:  # 毫秒
            df2 = df2.with_columns(
                pl.col("ts").cast(pl.Int64).truediv(1000).cast(pl.Datetime("s"))
            )
        else:  # 秒
            df2 = df2.with_columns(
                pl.col("ts").cast(pl.Datetime("s"))
            )
    
    print(f"轉換後 ts 型別: {df2['ts'].dtype}")
    print(df2.select("ts").head(3))
    print()
    
    # 測試案例 3: 字串時間戳
    print("測試案例 3: 字串時間戳")
    df3 = pl.DataFrame({
        "ts": ["2023-11-15 10:00:00", "2023-11-15 10:01:00", "2023-11-15 10:02:00"],
        "Open": [100.0, 101.0, 102.0],
        "High": [101.0, 102.0, 103.0],
        "Low": [99.0, 100.0, 101.0],
        "Close": [100.5, 101.5, 102.5],
        "Volume": [1000, 1100, 1200],
        "Amount": [100500.0, 111650.0, 123000.0]
    })
    
    print(f"原始 ts 型別: {df3['ts'].dtype}")
    
    # 轉換邏輯
    if df3["ts"].dtype == pl.Utf8 or df3["ts"].dtype == pl.String:
        df3 = df3.with_columns(pl.col("ts").str.strptime(pl.Datetime))
    
    print(f"轉換後 ts 型別: {df3['ts'].dtype}")
    print(df3.select("ts").head(3))
    print()
    
    print("✅ 所有測試案例都成功執行！")

if __name__ == "__main__":
    test_timestamp_conversion()