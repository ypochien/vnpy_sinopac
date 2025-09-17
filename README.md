[![GitHub license](https://img.shields.io/github/license/ypochien/vnpy_sinopac)](https://github.com/ypochien/vnpy_sinopac/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/ypochien/vnpy_sinopac?style=plastic)](https://github.com/ypochien/vnpy_sinopac/issues)
[![GitHub Actions](https://github.com/ypochien/vnpy_sinopac/workflows/Deploy/badge.svg)](https://github.com/ypochien/vnpy_sinopac/actions)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/vnpy_sinopac)
![PyPI](https://img.shields.io/pypi/v/vnpy_sinopac)

# Sinopac API - Shioaji 交易接口 for VeighNa框架

VeighNa框架的永豐金證券 Shioaji API 交易接口，支援台股、期貨、選擇權等金融商品交易。

## 🔗 相關連結
- [Sinopac API - Shioaji 文件](https://sinotrade.github.io/)
- [VeighNa 量化交易框架](https://github.com/vnpy/vnpy/)
- [專案 GitHub](https://github.com/ypochien/vnpy_sinopac)

## 📋 系統需求
- **VeighNa**: 4.0+
- **Python**: 3.10 - 3.13
- **作業系統**: Windows / Linux / macOS

## 🚀 安裝方式

### 使用 pip 安裝
```bash
pip install vnpy_sinopac
```

### 使用 uv 安裝（推薦）
```bash
uv add vnpy_sinopac
```

## 🎯 快速開始
```bash
python script/run.py
```

## 📈 功能特色

- ✅ **即時行情**: 支援台股、期貨、選擇權即時報價
- ✅ **歷史資料**: K線、成交明細等歷史資料查詢
- ✅ **交易下單**: 股票、期貨、選擇權交易下單
- ✅ **帳戶查詢**: 資金、持倉、委託等帳戶資訊
- ✅ **高效能**: 使用 Polars 提升資料處理速度 10-30 倍
- ✅ **現代化**: 採用 uv 套件管理，安裝速度提升 10-100 倍

## ⚙️ 配置說明

### 1. 取得 API 金鑰
前往 [永豐金證券](https://www.sinotrade.com.tw/) 申請 Shioaji API 使用權限

### 2. 設定連線參數
```python
from vnpy_sinopac import SinopacGateway

# 在 VeighNa 中添加 Sinopac 接口
gateway = SinopacGateway(event_engine)
```

## 📊 交易說明

### 股票交易
- 支援現股買賣
- 支援融資融券
- 支援當沖交易
- 自動處理交易時間限制

### 期貨交易
- 支援期貨合約交易
- 支援選擇權交易
- 自動計算保證金
- 支援多種委託類型

### 選擇權交易
- 支援買權/賣權交易
- 支援履約價查詢
- 自動計算權利金
- 支援組合策略



## 🔧 開發環境

### 本地開發設置
```bash
# 克隆專案
git clone https://github.com/ypochien/vnpy_sinopac.git
cd vnpy_sinopac

# 安裝 uv（推薦）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安裝依賴
uv sync

# 運行測試
uv run pytest tests/
```

## 📝 版本歷史

- **v4.0.3**: 修正 GitHub Actions 設定，改善 CI/CD 流程
- **v4.0.2**: 更新支援 Python 3.13，改善建置系統
- **v4.0.1**: 升級至 VeighNa 4.x，採用 Polars 提升效能
- **v4.0.0**: 全面現代化架構，從 Poetry 遷移至 uv

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📄 授權

本專案使用 MIT 授權 - 詳見 [LICENSE](LICENSE) 檔案

## 💝 贊助

如果這個專案對您有幫助，歡迎考慮贊助支持開發：

- **以太坊地址**: [ypochien.eth](https://etherscan.io/address/ypochien.eth)
- **支援所有 ERC-20 代幣**

![ypochien.eth.png](ypochien.eth.png)

---

⭐ 如果這個專案對您有幫助，請給個星星支持！


