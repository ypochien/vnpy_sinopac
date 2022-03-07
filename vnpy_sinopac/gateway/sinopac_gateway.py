# -*- coding: UTF-8 -*-
# author: ypochien
import time
from copy import copy
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any

import pandas as pd
import pytz
import shioaji.constant as sj_constant
import shioaji.contracts
import xxhash
from shioaji import Shioaji, contracts
from shioaji.account import StockAccount, FutureAccount
from shioaji.order import Status as SinopacStatus
from shioaji.order import Trade,Deal
from vnpy.trader.constant import (
    Exchange,
    Product,
    OptionType,
    Interval,
    Offset,
    OrderType,
)
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import (
    ContractData,
    OrderRequest,
    CancelRequest,
    SubscribeRequest,
    TickData,
    Status,
    PositionData,
    Direction,
    HistoryRequest,
    BarData,
    OrderData,
    TradeData,
)
from vnpy.trader.utility import round_to

TW_TZ = pytz.timezone("Asia/Taipei")

EXCHANGE_VT2SINOPAC = {Exchange.LOCAL: "LOCAL"}
EXCHANGE_SINOPAC2VT = {v: k for k, v in EXCHANGE_VT2SINOPAC.items()}

STATUS_SINOPAC2VT = {
    SinopacStatus.Cancelled: Status.CANCELLED,
    SinopacStatus.Failed: Status.REJECTED,
    SinopacStatus.Filled: Status.ALLTRADED,
    SinopacStatus.PreSubmitted: Status.SUBMITTING,
    SinopacStatus.Submitted: Status.NOTTRADED,
    SinopacStatus.PendingSubmit: Status.SUBMITTING,
    SinopacStatus.Inactive: Status.SUBMITTING,
}

PRICETYPE_SINOPAC2VT = {
    sj_constant.FuturesPriceType.MKT: OrderType.MARKET,
    sj_constant.FuturesPriceType.MKP: OrderType.MARKET,
    sj_constant.FuturesPriceType.LMT: OrderType.LIMIT,
}

PRICETYPE_FUT_VT2SINOPAC: Dict[OrderType, Any] = {
    OrderType.MARKET: (
        sj_constant.FuturesPriceType.MKP,
        sj_constant.FuturesOrderType.ROD,
    ),
    OrderType.LIMIT: (
        sj_constant.FuturesPriceType.LMT,
        sj_constant.FuturesOrderType.ROD,
    ),
    OrderType.FAK: (sj_constant.FuturesPriceType.LMT, sj_constant.FuturesOrderType.IOC),
    OrderType.FOK: (sj_constant.FuturesPriceType.LMT, sj_constant.FuturesOrderType.FOK),
}

OFFSET_FUT_SINOPAC2VT = {
    sj_constant.FuturesOCType.Auto: Offset.NONE,
    sj_constant.FuturesOCType.New: Offset.OPEN,
    sj_constant.FuturesOCType.Cover: Offset.CLOSE,
    sj_constant.FuturesOCType.DayTrade: Offset.CLOSETODAY,
}
OFFSET_FUT_VT2SINOPAC = {v: k for k, v in OFFSET_FUT_SINOPAC2VT.items()}

OFFSET_STK_VT2SINOPAC: Dict[Offset, Any] = {
    Offset.NONE: (sj_constant.StockOrderCond.Cash, sj_constant.StockFirstSell.No),
    Offset.OPEN: (
        sj_constant.StockOrderCond.MarginTrading,
        sj_constant.StockFirstSell.No,
    ),
    Offset.CLOSE: (
        sj_constant.StockOrderCond.ShortSelling,
        sj_constant.StockFirstSell.No,
    ),
    Offset.CLOSETODAY: (
        sj_constant.StockOrderCond.Cash,
        sj_constant.StockFirstSell.Yes,
    ),
    Offset.CLOSEYESTERDAY: (None, None),
}
OFFSET_STK_SINOPAC2VT: Dict[Any, Offset] = {
    v: k for k, v in OFFSET_STK_VT2SINOPAC.items()
}

DIRECTION_VT2SHIOAJI: Dict[Direction, str] = {
    Direction.LONG: sj_constant.Action.Buy,
    Direction.SHORT: sj_constant.Action.Sell,
}
DIRECTION_SHIOAJI2VT: Dict[str, Direction] = {
    v: k for k, v in DIRECTION_VT2SHIOAJI.items()
}


class RelayOPType(str, Enum):
    New = "New"
    Cancel = "Cancel"
    UpdateQty = "UpdateQty"
    UpdatePrice = "UpdatePrice"


class RelayOpcode(str, Enum):
    Success = "00"
    Failure = "88"


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
        self.orders = {}  # for vnpy
        self.trades = {}  # for sj

        self.api.set_order_callback(self.relay_callback)
        self.api.quote.set_on_tick_fop_v1_callback(self.tick_v1_callback)
        self.api.quote.set_on_tick_stk_v1_callback(self.tick_v1_callback)
        self.api.quote.set_on_bidask_fop_v1_callback(self.bidask_v1_callback)
        self.api.quote.set_on_bidask_stk_v1_callback(self.bidask_v1_callback)

    def tick_v1_callback(self, _, tick) -> None:
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
        one_tick.last_price = float(tick.close)
        one_tick.limit_up = contract.limit_up
        one_tick.open_interest = 0
        one_tick.limit_down = contract.limit_down
        one_tick.open_price = float(tick.open)
        one_tick.high_price = float(tick.high)
        one_tick.low_price = float(tick.low)
        one_tick.pre_close = float(tick.close - tick.price_chg)
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

    def relay_callback(self, topic, relay_data):
        # self.write_log(
        #     f"relay_cb {topic} -{relay_data['order']['id']} {relay_data['operation']}"
        # )
        if topic in [sj_constant.OrderState.FOrder, sj_constant.OrderState.TFTOrder]:
            self.impl_order(relay_data)
        elif topic == sj_constant.OrderState.FDeal:
            self.impl_deal(self.api.futopt_account, relay_data)
        elif topic == sj_constant.OrderState.TFTDeal:
            self.impl_deal(self.api.stock_account, relay_data)

    def impl_order(self, relay_data):
        orderid = relay_data["order"]["id"]
        order_data: OrderData = self.orders.get(orderid, None)
        sj_trade: Trade = self.trades.get(orderid, None)
        acc_type = relay_data["order"]["account"]["account_type"]  # "F" or "S"

        if sj_trade is None:
            seq_no = relay_data["order"]["seqno"]
            account = (
                self.api.stock_account if acc_type == "S" else self.api.futopt_account
            )
            sj_trade = self.get_trade_by_seqno(account, seq_no)
            self.trades[orderid] = sj_trade
        if order_data is None:
            order_data = OrderData(
                symbol=sj_trade["contract"]["code"],
                exchange=Exchange.LOCAL,
                type=PRICETYPE_SINOPAC2VT[
                    relay_data["order"].get(
                        "price_type", sj_constant.FuturesPriceType.LMT
                    )
                ],
                orderid=orderid,
                direction=DIRECTION_SHIOAJI2VT[relay_data["order"]["action"]],
                volume=relay_data["order"]["quantity"],
                gateway_name=self.gateway_name,
            )
            order_data.offset = (
                OFFSET_STK_SINOPAC2VT[
                    (relay_data["order"]["order_cond"], sj_constant.StockFirstSell.No)
                ]
                if acc_type == "S"
                else OFFSET_FUT_SINOPAC2VT[relay_data["order"]["oc_type"]]
            )
            order_data.price = round_to(relay_data["order"]["price"], 0.00001)
            order_data.volume = round_to(relay_data["order"]["quantity"], 1)
            order_data.status = Status.SUBMITTING
            order_data.datetime = datetime.fromtimestamp(
                relay_data["status"]["exchange_ts"]
            )
        op = relay_data["operation"]
        order_data.reference = op.get("op_msg", "")
        if op.get("op_code") == "00":
            if op.get("op_type") == RelayOPType.New:
                order_data.status = Status.NOTTRADED
            elif op.get("op_type") == RelayOPType.Cancel:
                order_data.status = Status.CANCELLED
            elif op.get("op_type") == RelayOPType.UpdateQty:
                order_data.volume -= relay_data["status"]["order_quantity"]
                if order_data.volume <= 0:
                    order_data.status = Status.CANCELLED
            elif op.get("op_type") == RelayOPType.UpdatePrice:
                order_data.price = relay_data["status"]["modified_price"]
        else:  # if op.get("op_code") != "00":
            order_data.reference = op.get("op_msg", "")
            if op.get("op_type") == RelayOPType.New:
                order_data.status = Status.REJECTED
        self.orders[orderid] = order_data
        self.on_order(order_data)

    def get_trade_by_seqno(self, account, seq_no):
        try:
            self.api._solace.update_status(account=account, seqno=seq_no)
            sj_trade = self.api._solace._trades[xxhash.xxh32_hexdigest(seq_no)]
        except:
            time.sleep(0.1)
            self.api._solace.update_status(account=account, seqno=seq_no)
            sj_trade = self.api._solace._trades[xxhash.xxh32_hexdigest(seq_no)]
        return sj_trade

    def impl_deal(self, account, relay_data):
        """trade_id='11d6f902' seqno='123696' ordno='qn08zA1F' exchange_seq='f4005559' broker_id='F002000' account_id='1627187' action=<Action.Buy: 'Buy'> code='MXF' price=17800.0 quantity=4 subaccount='' security_type=<SecurityType.Future: 'FUT'> delivery_month='202203' strike_price=0.0 option_right=<CallPut.Future: 'Future'> market_type='Day' combo=False ts=1646194001"""
        orderid = relay_data["trade_id"]
        sj_trade: Trade = self.trades.get(orderid, None)
        if sj_trade is None:
            seq_no = relay_data["order"]["seqno"]
            sj_trade = self.get_trade_by_seqno(account, seq_no)
            self.trades[orderid] = sj_trade

        trade: TradeData = TradeData(
            symbol=sj_trade.contract.code,
            exchange=Exchange.LOCAL,
            orderid=orderid,
            tradeid=relay_data["exchange_seq"],
            direction=DIRECTION_SHIOAJI2VT[relay_data["action"]],
            offset=Offset.NONE,
            price=relay_data["price"],
            volume=relay_data["quantity"],
            datetime=datetime.fromtimestamp(relay_data["ts"]),
            gateway_name=self.gateway_name,
        )
        self.on_trade(trade)

        vn_order:OrderData = self.orders.get(orderid,None)
        if vn_order:
            vn_order.traded += relay_data["quantity"]
            self.on_order(vn_order)
        else:
            return 


    def query_contract(self, securities_type=None):
        self.write_log(f"商品檔 {securities_type} 下載完畢.")
        for category in self.api.Contracts.Futures:
            for contract in category:
                data = ContractData(
                    symbol=contract.code,
                    exchange=Exchange.LOCAL,
                    name=contract.name + contract.delivery_month,
                    product=Product.FUTURES,
                    size=200,
                    pricetick=contract.unit,
                    net_position=True,
                    min_volume=1,
                    history_data=True,
                    gateway_name=self.gateway_name,
                )
                self.on_contract(data)
                self.code2contract[contract.code] = contract

        for category in self.api.Contracts.Options:
            for contract in category:
                data = ContractData(
                    symbol=contract.code,
                    exchange=Exchange.LOCAL,
                    name=contract.name.replace(" ", ""),
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
                    history_data=True,
                    option_expiry=datetime.strptime(contract.delivery_date, "%Y/%m/%d"),
                )
                self.on_contract(data)
                self.code2contract[contract.code] = contract

        for category in self.api.Contracts.Stocks:
            for contract in category:
                data = ContractData(
                    symbol=contract.code,
                    exchange=Exchange.LOCAL,
                    name=contract.name,
                    product=Product.EQUITY,
                    size=1,
                    net_position=False,
                    pricetick=0.01,
                    min_volume=1,
                    history_data=True,
                    gateway_name=self.gateway_name,
                )
                self.on_contract(data)
                self.code2contract[contract.code] = contract

    def connect(self, setting: dict) -> None:
        """連接 Shioaji"""
        userid: str = setting["登入帳號"]
        password: str = setting["密碼"]
        try:
            self.api.login(userid, password, contracts_cb=self.query_contract)
        except Exception as exc:
            self.write_log(f"登入失败. [{exc}]")
            return
        self.write_log(f"登入成功. [{userid}]")
        for acc in self.api.list_accounts():
            self.write_log(acc)
        self.register_all_event()
        self.select_default_account(setting.get("預設現貨帳號", 0), setting.get("預設期貨帳號", 0))
        if setting["憑證檔案路徑"] != "":
            self.api.activate_ca(setting["憑證檔案路徑"], setting["憑證密碼"], setting["登入帳號"])
            self.write_log(f"{setting.get('登入帳號')} 憑證 已啟用.")

    def update_trades(self, reload=False):
        def convert_deal2vntrade(vn_order:OrderData,sjdeal:Deal)->TradeData:
            """Deal(seq='j5014266', price=55.0, quantity=1, ts=1646672854)]"""
            vn_trade = TradeData(gateway_name=vn_order.gateway_name,symbol=vn_order.symbol,exchange=vn_order.exchange,orderid=vn_order.orderid,tradeid=sjdeal.seq,direction=vn_order.direction,price=sjdeal.price,volume=sjdeal.quantity,datetime=datetime.fromtimestamp(sjdeal.ts))
            return vn_trade

        def convert_sjtrade2vnorder(sjtrade: Trade) -> OrderData:
            vt_offset = Offset.NONE
            if sjtrade.order.account.broker_id.startswith("F"):
                vt_offset = OFFSET_FUT_SINOPAC2VT[sjtrade.order.octype]
            else:
                vt_offset = OFFSET_STK_SINOPAC2VT[
                    (sjtrade.order.order_cond, sjtrade.order.first_sell)
                ]
            vn_order_data: OrderData = OrderData(
                symbol=sjtrade.contract.code,
                exchange=Exchange.LOCAL,
                orderid=sjtrade.order.id,
                direction=DIRECTION_SHIOAJI2VT[sjtrade.order.action],
                price=round_to(sjtrade.order.price, 0.00001),
                volume=round_to(sjtrade.order.quantity, 1),
                traded=round_to(sjtrade.status.deal_quantity, 1),
                status=STATUS_SINOPAC2VT[sjtrade.status.status],
                type=PRICETYPE_SINOPAC2VT[sjtrade.order.price_type],
                offset=vt_offset,
                datetime=sjtrade.status.order_datetime,
                reference=sjtrade.status.msg,
                gateway_name=self.gateway_name,
            )
            self.orders[sjtrade.order.id] = vn_order_data
            self.trades[sjtrade.order.id] = sjtrade
            return vn_order_data

        if reload:
            self.api.update_status()
        for sj_trade in self.api.list_trades():
            vn_order = convert_sjtrade2vnorder(sj_trade)
            self.on_order(vn_order)
            for deal in sj_trade.status.deals:
                vn_trade = convert_deal2vntrade(vn_order,deal)
                self.on_trade(vn_trade)

    def register_all_event(self):
        self.query_position()
        self.update_trades(reload=True)

    def select_default_account(self, select_stock_number, select_futures_number):
        stock_account_count = 0
        futures_account_count = 0
        for acc in self.api.list_accounts():
            if isinstance(acc, StockAccount):
                msg = f"股票帳號: [{stock_account_count}] {'已簽署' if acc.signed else '未簽署'} - {acc.broker_id}-{acc.account_id} {acc.username}"
                self.write_log(msg)
                stock_account_count += 1
            if isinstance(acc, FutureAccount):
                msg = f"期貨帳號: [{futures_account_count}] {'已簽署' if acc.signed else '未簽署'} - {acc.broker_id}-{acc.account_id} {acc.username}"
                self.write_log(msg)
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
                if pos.direction is sj_constant.Action.Buy
                else Direction.SHORT
            )
            volume = pos.quantity
            total_qty = pos.quantity
            yd_qty = pos.yd_quantity
            pos = PositionData(
                symbol=pos.code,
                exchange=Exchange.LOCAL,
                direction=direction,
                volume=round_to(volume, 1),
                frozen=round_to(total_qty - yd_qty, 1),
                price=round_to(pos.price, 0.0001),
                pnl=round_to(pos.pnl, 1),
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

        def cancel_cb(_: Trade):
            self.write_log(f"Cancel {req.orderid}")

        sj_trade: Trade = self.trades.get(req.orderid, None)
        if sj_trade:
            self.api.cancel_order(self.trades[req.orderid], timeout=0, cb=cancel_cb)
        else:
            self.write_log(f"Cancel {req.symbol} {req.orderid} not found.")

    def close(self) -> None:
        """Shioaji Session Logout"""
        self.api.logout()

    def query_account(self) -> None:
        """Query Account"""
        # self.req_id += 1
        pass

    def query_position(self) -> None:
        """Query hold positions"""
        # Stock account
        self.api.list_positions(timeout=0, cb=self.list_position_callback)

        # Future account
        """Todo : 當期貨查詢改為sw後，記得修正"""
        if self.api.futopt_account:
            try:
                all_pos = self.api.get_account_openposition(query_type="1").data()
            except AttributeError:
                all_pos = []
                self.write_log("get_account_open_position fail.")
            for pos in all_pos:
                if len(pos.items()) == 0:
                    continue
                pos = PositionData(
                    symbol=f"{pos.get('Code')}",
                    exchange=Exchange.LOCAL,
                    direction=Direction.LONG
                    if pos.get("OrderBS") == "B"
                    else Direction.SHORT,
                    volume=round_to(pos.get("Volume"), 1),
                    frozen=0,
                    price=round_to(pos.get("ContractAverPrice"), 0.0001),
                    pnl=round_to(pos.get("FlowProfitLoss"), 1),
                    yd_volume=0,
                    gateway_name=self.gateway_name,
                )
                self.on_position(pos)

    def place_order_callback(self, trade: Trade):
        sj_contract: shioaji.contracts.Contract = trade["contract"]
        order_data: OrderData = self.orders.get(trade.order.id, None)

        if self.trades.get(trade.order.id, None) is None:
            self.trades[trade.order.id] = trade
        if order_data is None:
            order_data: OrderData = OrderData(
                symbol=sj_contract["code"],
                exchange=Exchange.LOCAL,
                type=PRICETYPE_SINOPAC2VT[trade.order.price_type],
                orderid=trade.order.id,
                direction=DIRECTION_SHIOAJI2VT[trade.order.action],
                volume=trade.order.quantity,
                gateway_name=self.gateway_name,
            )
            order_data.price = round_to(trade.order.price, 0.00001)
            order_data.volume = round_to(trade.order.quantity, 1)
            order_data.traded = round_to(trade.status.deal_quantity, 1)
            order_data.status = STATUS_SINOPAC2VT[trade.status.status]
            order_data.datetime = trade.status.order_datetime
            order_data.reference = trade.status.msg
            self.orders[trade.order.id] = order_data
        self.on_order(order_data)

    def send_order(self, req: OrderRequest) -> str:
        """委托下单"""
        """
        Send a new order to server.

        implementation should finish the tasks blow:
        * create an OrderData from req using OrderRequest.create_order_data
        * assign a unique(gateway instance scope) id to OrderData.orderid
        * send request to server
            * if request is sent, OrderData.status should be set to Status.SUBMITTING
            * if request is failed to sent, OrderData.status should be set to Status.REJECTED
        * response on_order:
        * return vt_orderid

        :return str vt_orderid for created OrderData
        """
        contract = self.code2contract.get(req.symbol, None)
        sj_order = None
        if any(isinstance(contract, i) for i in [contracts.Future, contracts.Option]):
            action = DIRECTION_VT2SHIOAJI[req.direction]
            price_type, order_type = PRICETYPE_FUT_VT2SINOPAC.get(
                req.type, (None, None)
            )
            if not all([price_type, order_type]):
                self.write_log(f"{req.symbol} 不支援 { req.type.value } 下單")
                return ""
            sj_order = self.api.Order(
                req.price,
                req.volume,
                octype=OFFSET_FUT_VT2SINOPAC[req.offset],
                action=action,
                price_type=price_type,
                order_type=order_type,
            )

        elif isinstance(contract, contracts.Stock):
            action = DIRECTION_VT2SHIOAJI[req.direction]
            price_type, order_type = PRICETYPE_FUT_VT2SINOPAC.get(
                req.type, (None, None)
            )
            if not all([price_type, order_type]):
                self.write_log(f"{req.symbol} 不支援 { req.type.value } 下單")
                return ""
            order_cond, first_sell = OFFSET_STK_VT2SINOPAC[req.offset]
            if not all([order_cond, first_sell]):
                self.write_log(f"{req.symbol} 不支援 { req.offset.value } 下單")
                return ""
            sj_order = self.api.Order(
                price=req.price,
                quantity=int(req.volume),
                action=action,
                price_type=price_type,
                order_type=order_type,
                order_cond=order_cond,
                first_sell=first_sell,
            )

        self.api.place_order(contract, sj_order, 0, self.place_order_callback)
        return ""

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

    def query_history(self, req: HistoryRequest) -> List[BarData]:
        self.write_log(f"Download kbar {req.symbol} {req.start}")
        symbol = req.symbol
        exchange = req.exchange
        interval = req.interval
        start = datetime.strftime(req.start, "%Y-%m-%d")
        end = datetime.strftime(req.end, "%Y-%m-%d")

        sj_contract = self.code2contract.get(symbol)
        data: List[BarData] = []

        if interval == Interval.MINUTE:
            minute_bars = self.api.kbars(sj_contract, start, end)
            df = pd.DataFrame({**minute_bars})
            df.ts = pd.to_datetime(df.ts)
            if df is not None:
                for ix, row in df.iterrows():
                    dt = row.ts.to_pydatetime()
                    dt = TW_TZ.localize(dt)

                    bar = BarData(
                        symbol=symbol,
                        exchange=exchange,
                        interval=interval,
                        datetime=dt,
                        open_price=round_to(row["Open"], 0.000001),
                        high_price=round_to(row["High"], 0.000001),
                        low_price=round_to(row["Low"], 0.000001),
                        close_price=round_to(row["Close"], 0.000001),
                        volume=row["Volume"],
                        turnover=row["Amount"],
                        open_interest=0,
                        gateway_name=self.gateway_name,
                    )
                    data.append(bar)
        return data
