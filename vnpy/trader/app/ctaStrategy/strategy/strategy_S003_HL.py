# encoding: UTF-8

"""
S002
"""

from __future__ import division

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator, 
                                                     ArrayManager)


########################################################################
class S003_HL_Strategy(CtaTemplate):
    """基于HL的交易策略"""
    className = 'S003_HL_Strategy'
    author = u'zpf'

    # 策略参数
    longLength = 55         # 计算通道中值的窗口数
    shortLength = 27        # 计算通道中值的窗口数
    initDays = 30           # 初始化数据所用的天数
    fixedSize = 1           # 每次交易的数量

    # 策略变量
    longUp = 0                            # 长通道上轨
    longDown = 0                          # 长通道下轨
    shortUp = 0                           # 短通道上轨
    shortDown = 0                         # 短通道下轨


    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 ]

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'longUp',
               'longDown',
               'shortUp',
               'shortDown',
               ]
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos',
                ]

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(S003_HL_Strategy, self).__init__(ctaEngine, setting)
        
        self.bg = BarGenerator(self.onBar, 60, self.on_60_Bar)     # 创建K线合成器对象
        self.am = ArrayManager()
        
        self.buyOrderIDList = []
        self.shortOrderIDList = []
        self.orderList = []
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' %self.name)

        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)

        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动, 目前仓位 %d' % (self.name, self.pos))
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        # 过滤无效tick
        if self.filterTick(tick):
            return

        self.bg.updateTick(tick)

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        # 过滤无效K线
        if self.filterBar(bar):
            return

        # print u"1 min bar %s  %s" % (bar.symbol, bar.datetime)
        self.bg.updateBar(bar)
    
    #----------------------------------------------------------------------
    def on_60_Bar(self, bar):
        """收到1小时K线"""
        # 全撤之前发出的委托
        self.cancelAll()
    
        # 保存K线数据
        am = self.am
        am.updateBar(bar)
        if not am.inited:
            return

        # 计算指标数值
        self.longUp, self.longDown   = am.donchian(self.longLength, True)
        self.shortUp, self.shortDown = am.donchian(self.shortLength,True)

        # 打印行情,load的时候只打印屏幕，实盘打印记录
        if self.trading:
            self.writeCtaLog( u"bar %s  %s,   %d, %d, %d, %d    长上 %d 长下 %d  短上 %d 短下 %d   pos = %d"
                              % (bar.symbol, bar.datetime, bar.open,bar.high,bar.low,bar.close, self.longUp[-1],self.longDown[-1],self.shortUp[-1],self.shortDown[-1],self.pos))
        else:
            print ( u"bar %s  %s,   %d, %d, %d, %d    长上 %d 长下 %d  短上 %d 短下 %d   pos = %d"
                    % (bar.symbol, bar.datetime, bar.open,bar.high,bar.low,bar.close, self.longUp[-1],self.longDown[-1],self.shortUp[-1],self.shortDown[-1],self.pos))

        # 判断是否要进行交易
    
        # 当前无仓位，发送开仓委托
        if self.pos == 0:
            self.buy(self.longUp[-1], self.fixedSize, True)
            self.short(self.longDown[-1], self.fixedSize, True)

        # 持有多头仓位
        elif self.pos > 0:
            self.sell(self.shortDown[-1], abs(self.pos), True)
            self.short(self.longDown[-1], self.fixedSize, True)
    
        # 持有空头仓位
        elif self.pos < 0:
            self.cover(self.shortUp[-1], abs(self.pos), True)
            self.buy(self.longUp[-1], self.fixedSize, True)
    
        # 同步数据到数据库
        self.saveSyncData()    
    
        # 发出状态更新事件
        self.putEvent()        

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """"""
        self.writeCtaLog(u'%s %s %s %d %d %s' % (trade.symbol, trade.direction, trade.offset ,trade.price, trade.volume , trade.tradeTime))
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass