# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案概述
這是 VeighNa 量化交易框架的永豐金證券 Shioaji API 交易接口，支援台股、期貨、選擇權等金融商品交易。專案使用 Polars 進行高效資料處理，並採用 uv 現代化套件管理工具。

## 開發指令

### 基礎開發
```bash
# 安裝依賴
uv sync

# 執行主程式
uv run python script/run.py

# 執行測試
uv run pytest tests/ -v

# 建置套件
uv build

# 發布到 PyPI
uv publish
```

### Make 指令
```bash
make install      # 安裝專案依賴
make test        # 執行測試
make test-cov    # 執行測試並產生覆蓋率報告  
make build       # 建置套件
make upload      # 上傳到 PyPI
make clean       # 清理建置產物
```

## 架構說明

### 核心模組結構
- `vnpy_sinopac/gateway/sinopac_gateway.py`: 主要閘道實作，處理所有與 Shioaji API 的互動
  - 資料型別轉換 (VeighNa ↔ Shioaji)
  - 交易執行邏輯
  - 即時行情處理
  - 帳戶管理

### 重要對應關係
- **交易所映射**: LOCAL (台灣本地交易所)
- **訂單狀態轉換**: Shioaji Status → VeighNa Status
- **委託類型映射**: 支援 MARKET, LIMIT, FAK, FOK
- **開平倉類型**: 支援現股、融資、融券、當沖

### 資料處理特點
- 使用 Polars DataFrame 替代 Pandas，效能提升 10-30 倍
- 時區處理統一使用 Asia/Taipei (TW_TZ)
- 使用 xxhash 進行高效雜湊計算

## 版本發布流程
1. 更新 `pyproject.toml` 中的版本號
2. 建立對應的 git tag (格式: v4.0.x)
3. 推送 tag 觸發 GitHub Actions 自動發布到 PyPI
4. 驗證版本號必須與 tag 一致才能發布

## 測試策略
- 基礎匯入測試確保模組可正常載入
- Polars 功能測試驗證資料處理能力
- GitHub Actions 在 Ubuntu 和 Windows 上執行 CI/CD

## 注意事項
- 需要先申請永豐金證券 Shioaji API 權限
- 支援 Python 3.10 至 3.13
- 使用 uv 作為主要套件管理工具（速度比 pip 快 10-100 倍）