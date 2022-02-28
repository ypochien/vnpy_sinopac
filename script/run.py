# -*- coding: UTF-8 -*-
"""
@Author ：ypochien
@Date ：2022/2/23 下午 05:43 
"""

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

# from vnpy_datamanager import DataManagerApp
# from vnpy_chartwizard import ChartWizardApp
from vnpy_sinopac import SinopacGateway


def main():
    """主入口函数"""
    qapp = create_qapp()

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    # main_engine.add_app(DataManagerApp)
    # main_engine.add_app(ChartWizardApp)
    main_engine.add_gateway(SinopacGateway)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()
