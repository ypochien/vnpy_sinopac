[![GitHub license](https://img.shields.io/github/license/ypochien/vnpy_sinopac)](https://github.com/ypochien/vnpy_sinopac/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/ypochien/vnpy_sinopac?style=plastic)](https://github.com/ypochien/vnpy_sinopac/issues)
![GitHub Workflow Status (event)](https://img.shields.io/github/workflow/status/ypochien/vnpy_sinopac/Deploy?event=push)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/vnpy_sinopac)
![PyPI](https://img.shields.io/pypi/v/vnpy_sinopac)

# Sinopac API - Shioaji 交易接口 for VeighNa框架

# ⚠️ Warning ⚠️
* ⚠️ 如果你的 shioaji 為 0.x 版本，請安裝 vnpy_sinopac v1.5
* ⚠️ 如果你的 shioaji 為 1.0 版本之後，請安裝 vnpy_sinopac v2.0 之後的版本
```
import shioaji
print(shioaji.__version__)
```


## 
- Sinopac API - shioaji - https://sinotrade.github.io/
- VeighNa (VNPY) - https://github.com/vnpy/vnpy/
- vnpy_sinopac - https://github.com/ypochien/vnpy_sinopac

## Requirement
* Shioaji >= 1.0
* VeighNa 3.0~3.5
* Python 3.10 / 3.9 / 3.8 / 3.7  (建議用 Anaconda)
## Installation
```
pip install vnpy_sinopac
```
## Quickstarts
```
python scripy/run.py
```
or add below
```
from vnpy_sinopac import SinopacGateway

main_engine.add_gateway(SinopacGateway)
```


## 關於下單方式
### 股票


### 期權



## 贊助 Donating
* 如果你發現這個專案有幫助到你，請考慮 [贊助](https://etherscan.io/address/ypochien.eth)
* ETH是最棒的，但其他TOKEN也都歡迎。
* ![ypochien.eth.png](ypochien.eth.png)



