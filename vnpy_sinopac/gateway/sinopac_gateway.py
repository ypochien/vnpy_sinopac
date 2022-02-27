# -*- coding: UTF-8 -*-
# author: ypochien
from copy import copy
from datetime import datetime
from typing import Dict

import pytz
from shioaji import Shioaji
from shioaji.account import StockAccount, FutureAccount
import shioaji.constant as sj_contant
from vnpy.trader.constant import Exchange, Product, OptionType
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import (
    ContractData,
    OrderRequest,
    CancelRequest,
    SubscribeRequest,
    TickData,
    PositionData,
    Direction,
)

TW_TZ = pytz.timezone("Asia/Taipei")

EXCHANGE_VT2SINOPAC = {Exchange.LOCAL: "LOCAL"}
EXCHANGE_SINOPAC2VT = {v: k for k, v in EXCHANGE_VT2SINOPAC.items()}


class SinopacGateway(BaseGateway):
    """
    Sinopac Securities - Shioaji for VeighNa Gateway
    """

    default_name: str = "Sinopac"
    default_setting: Dict[str, str] = {
        "登入帳號": "",
        "密碼": "",
        "憑證檔案路徑": "",
        "憑證密碼": "",
        "預設現貨帳號": "0",
        "預設期貨帳號": "0",
    }

    exchanges = list(EXCHANGE_SINOPAC2VT.values())

    def __init__(self, event_engine, gateway_name: str) -> None:
        """初始化"""
        super().__init__(event_engine, gateway_name)
        self.api: Shioaji = Shioaji()

        self.code2contract = {}
        self.subscribed = set()
        self.ticks = {}

        self.api.quote.set_on_tick_fop_v1_callback(self.tick_fop_v1_callback)
        self.api.quote.set_on_tick_stk_v1_callback(self.tick_stk_v1_callback)
        self.api.quote.set_on_bidask_fop_v1_callback(self.bidask_v1_callback)
        self.api.quote.set_on_bidask_stk_v1_callback(self.bidask_v1_callback)

    def tick_stk_v1_callback(self, _, tick) -> None:
        """
        :param _: non-used (Exchange)
        :param tick: Realtime tick data
        :return: None
        """
        one_tick = self.ticks.get(tick.code, None)
        contract = self.code2contract.get(tick.code, None)
        if one_tick is None:
            one_tick = TickData(
                symbol=tick.code,
                exchange=Exchange.LOCAL,
                name=f"{contract['name']}{contract['delivery_month']}",
                datetime=tick.datetime,
                gateway_name=self.gateway_name,
            )
            self.ticks[tick.code] = one_tick
        if tick.simtrade == 1:
            one_tick.name = f"{contract['name']}{contract['delivery_month']}(試搓)"
        else:
            one_tick.name = f"{contract['name']}{contract['delivery_month']}"

        one_tick.datetime = tick.datetime
        one_tick.volume = tick.volume
        one_tick.last_price = tick.close
        one_tick.limit_up = contract.limit_up
        one_tick.open_interest = 0
        one_tick.limit_down = contract.limit_down
        one_tick.open_price = tick.open
        one_tick.high_price = tick.high
        one_tick.low_price = tick.low
        one_tick.pre_close = tick.close - tick.price_chg
        one_tick.localtime = datetime.now()
        self.on_tick(copy(one_tick))

    def tick_fop_v1_callback(self, _, tick):
        """
        期貨、選擇權報價 FOP_V1
        """
        one_tick = self.ticks.get(tick.code, None)
        contract = self.code2contract.get(tick.code, None)
        if one_tick is None:
            one_tick = TickData(
                symbol=tick.code,
                exchange=Exchange.LOCAL,
                name=f"{contract['name']}{contract['delivery_month']}",
                datetime=tick.datetime,
                gateway_name=self.gateway_name,
            )
            self.ticks[tick.code] = one_tick
        if tick.simtrade == 1:
            one_tick.name = f"{contract['name']}{contract['delivery_month']}(試搓)"
        else:
            one_tick.name = f"{contract['name']}{contract['delivery_month']}"

        one_tick.datetime = tick.datetime
        one_tick.volume = tick.volume
        one_tick.last_price = tick.closeq
        one_tick.limit_up = contract.limit_up
        one_tick.open_interest = 0
        one_tick.limit_down = contract.limit_down
        one_tick.open_price = tick.open
        one_tick.high_price = tick.high
        one_tick.low_price = tick.low
        one_tick.pre_close = tick.close - tick.price_chg
        one_tick.localtime = datetime.now()
        self.on_tick(copy(one_tick))

    def bidask_v1_callback(self, _, tick):
        one_tick = self.ticks.get(tick.code, None)
        contract = self.code2contract[tick.code]
        if one_tick is None:
            one_tick = TickData(
                symbol=tick.code,
                exchange=Exchange.LOCAL,
                name=f"{contract['name']}{contract['delivery_month']}",
                datetime=tick.datetime,
                gateway_name=self.gateway_name,
            )
            self.ticks[tick.code] = one_tick
        one_tick.bid_price_1 = tick["bid_price"][0]
        one_tick.bid_price_2 = tick["bid_price"][1]
        one_tick.bid_price_3 = tick["bid_price"][2]
        one_tick.bid_price_4 = tick["bid_price"][3]
        one_tick.bid_price_5 = tick["bid_price"][4]
        one_tick.ask_price_1 = tick["ask_price"][0]
        one_tick.ask_price_2 = tick["ask_price"][1]
        one_tick.ask_price_3 = tick["ask_price"][2]
        one_tick.ask_price_4 = tick["ask_price"][3]
        one_tick.ask_price_5 = tick["ask_price"][4]
        one_tick.bid_volume_1 = tick["bid_volume"][0]
        one_tick.bid_volume_2 = tick["bid_volume"][1]
        one_tick.bid_volume_3 = tick["bid_volume"][2]
        one_tick.bid_volume_4 = tick["bid_volume"][3]
        one_tick.bid_volume_5 = tick["bid_volume"][4]
        one_tick.ask_volume_1 = tick["ask_volume"][0]
        one_tick.ask_volume_2 = tick["ask_volume"][1]
        one_tick.ask_volume_3 = tick["ask_volume"][2]
        one_tick.ask_volume_4 = tick["ask_volume"][3]
        one_tick.ask_volume_5 = tick["ask_volume"][4]
        self.on_tick(copy(one_tick))

    def query_contract(self, securities_type=None):
        self.write_log(f"商品檔 {securities_type} 下載完畢.")
        for category in self.api.Contracts.Futures:
            for contract in category:
                data = ContractData(
                    symbol=f"{contract.code}",
                    exchange=Exchange.LOCAL,
                    name=contract.name + contract.delivery_month,
                    product=Product.FUTURES,
                    size=200,
                    pricetick=contract.unit,
                    net_position=True,
                    min_volume=1,
                    gateway_name=self.gateway_name,
                )
                self.on_contract(data)
                self.code2contract[contract.code] = contract

        for category in self.api.Contracts.Options:
            for contract in category:
                data = ContractData(
                    symbol=f"{contract.code} {contract.name}",
                    exchange=Exchange.LOCAL,
                    name=f"{contract.name}{contract.delivery_month}",
                    product=Product.OPTION,
                    size=50,
                    net_position=True,
                    pricetick=0.01,
                    min_volume=1,
                    gateway_name=self.gateway_name,
                    option_strike=contract.strike_price,
                    option_underlying=contract.underlying_code,
                    option_type=OptionType.CALL
                    if contract.option_right == "C"
                    else OptionType.PUT,
                    option_expiry=datetime.strptime(contract.delivery_date, "%Y/%m/%d"),
                )
                self.on_contract(data)
                self.code2contract[contract.code] = contract

        for category in self.api.Contracts.Stocks:
            for contract in category:
                data = ContractData(
                    symbol=f"{contract.code}",
                    exchange=Exchange.LOCAL,
                    name=contract.name,
                    product=Product.EQUITY,
                    size=1,
                    net_position=False,
                    pricetick=0.01,
                    min_volume=1,
                    gateway_name=self.gateway_name,
                )
                self.on_contract(data)
                self.code2contract[contract.code] = contract

    def connect(self, setting: dict) -> None:
        """連接 Shioaji"""
        userid: str = setting["登入帳號"]
        password: str = setting["密碼"]
        try:
            all_account = self.api.login(
                userid, password, contracts_cb=self.query_contract
            )
        except Exception as exc:
            self.write_log(f"登入失败. [{exc}]")
            return
        self.write_log(f"登入成功. [{userid}]")
        for acc in all_account:
            self.write_log(acc)
        self.register_all_event()
        self.select_default_account(setting.get("預設現貨帳號", 0), setting.get("預設期貨帳號", 0))
        if setting["憑證檔案路徑"] != "":
            self.api.activate_ca(setting["憑證檔案路徑"], setting["憑證密碼"], setting["登入帳號"])
            self.write_log(f"{setting.get('登入帳號')} 憑證 已啟用.")

    def register_all_event(self):
        self.query_position()

    def select_default_account(self, select_stock_number, select_futures_number):
        stock_account_count = 0
        futures_account_count = 0
        for acc in self.api.list_accounts():
            if isinstance(acc, StockAccount):
                self.write_log(
                    f"股票帳號: [{stock_account_count}] - {acc.broker_id}-{acc.account_id} {acc.username}"
                )
                stock_account_count += 1
            if isinstance(acc, FutureAccount):
                self.write_log(
                    f"期貨帳號: [{futures_account_count}] - {acc.broker_id}-{acc.account_id} {acc.username}"
                )
                futures_account_count += 1

        if stock_account_count >= 2:
            acc = self.api.list_accounts()[int(select_stock_number)]
            self.api.set_default_account(acc)
            self.write_log(
                f"***預設 現貨下單帳號 - [{select_stock_number}] {acc.broker_id}-{acc.account_id} {acc.username}"
            )

        if futures_account_count >= 2:
            acc = self.api.list_accounts()[int(select_futures_number)]
            self.api.set_default_account(acc)
            self.write_log(
                f"***預設 期貨下單帳號 - [{select_futures_number}] {acc.broker_id}-{acc.account_id} {acc.username}"
            )

    def list_position_callback(self, positions):
        # Stock account
        for pos in positions:
            if pos.last_price == 0:
                self.write_log(f"忽略 {pos.code} 已下市，無法交易.")
                continue
            direction = (
                Direction.LONG
                if pos.direction is sj_contant.Action.Buy
                else Direction.SHORT
            )
            volume = pos.quantity
            total_qty = pos.quantity
            yd_qty = pos.yd_quantity
            pos = PositionData(
                symbol=f"{pos.code}",
                exchange=Exchange.LOCAL,
                direction=direction,
                volume=float(volume),
                frozen=float(total_qty - yd_qty),
                price=float(pos.price),
                pnl=float(pos.pnl),
                yd_volume=yd_qty,
                gateway_name=self.gateway_name,
            )
            self.on_position(pos)

    def get_contract_snapshot(self, contract):
        self.tick_snapshot(contract, Exchange.LOCAL)

    def tick_snapshot(self, contract, exchange):
        snapshots = self.api.snapshots([contract])
        code = contract.code
        tick = self.ticks.get(code, None)
        if tick is None:
            timestamp = snapshots[0].ts / 10**9 - 8 * 60 * 60
            dt = datetime.fromtimestamp(timestamp)

            tick = TickData(
                symbol=code,
                exchange=exchange,
                name=f"{contract['name']}",
                datetime=dt,
                gateway_name=self.gateway_name,
            )
        tick.volume = snapshots[0].total_volume
        tick.last_price = snapshots[0].close
        tick.limit_up = contract.limit_up
        tick.open_interest = 0
        tick.limit_down = contract.limit_down
        tick.open_price = snapshots[0].open
        tick.high_price = snapshots[0].high
        tick.low_price = snapshots[0].low
        tick.pre_close = contract.reference
        tick.bid_price_1 = snapshots[0].buy_price
        tick.bid_volume_1 = snapshots[0].buy_volume
        tick.ask_price_1 = snapshots[0].sell_price
        tick.ask_volume_1 = snapshots[0].sell_volume

        self.ticks[code] = tick
        self.on_tick(copy(tick))

    def cancel_order(self, req: CancelRequest) -> None:
        """委托撤单"""
        pass

    def close(self) -> None:
        """关闭接口"""
        self.api.logout()

    def query_account(self) -> None:
        """查询资金"""
        # self.reqid += 1
        pass

    def query_position(self) -> None:
        """查询持仓"""
        # Stock account
        self.api.list_positions(timeout=0, cb=self.list_position_callback)

        # Future account
        try:
            all_pos = self.api.get_account_openposition(query_type="1").data()
        except AttributeError:
            all_pos = []
            self.write_log("get_account_openposition fail.")
        for pos in all_pos:
            if len(pos.items()) == 0:
                continue
            pos = PositionData(
                symbol=f"{pos.get('Code')}",
                exchange=EXCHANGE_SINOPAC2VT.get("TFE", Exchange.TFE),
                direction=Direction.LONG
                if pos.get("OrderBS") == "B"
                else Direction.SHORT,
                volume=float(pos.get("Volume")),
                frozen=0,
                price=float(pos.get("ContractAverPrice")),
                pnl=float(pos.get("FlowProfitLoss")),
                yd_volume=0,
                gateway_name=self.gateway_name,
            )
            self.on_position(pos)

    def send_order(self, req: OrderRequest) -> str:
        """委托下单"""

        return "12345"

    def subscribe(self, req: SubscribeRequest) -> None:
        """订阅行情"""
        if req.symbol in self.subscribed:
            return

        contract = self.code2contract.get(req.symbol, None)
        if contract:
            self.get_contract_snapshot(contract)
            self.api.quote.subscribe(contract, quote_type="tick", version="v1")
            self.api.quote.subscribe(contract, quote_type="bidask", version="v1")
            self.write_log(f"訂閱 {contract.code} {contract.name}")
            self.subscribed.add(req.symbol)
        else:
            self.write_log(f"無此訂閱商品[{req.symbol}].")
