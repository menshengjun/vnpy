# encoding: UTF-8

"""
S002 KK
"""

from __future__ import division

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator, 
                                                     ArrayManager)


########################################################################
class S002_KK_Strategy(CtaTemplate):
    """基于King Keltner通道的交易策略"""
    className = 'S002_KK_Strategy'
    author = u'zpf'

    # 策略参数
    kkLength = 50           # 计算通道中值的窗口数
    kkDev = 2               # 计算通道宽度的偏差
    initDays = 30           # 初始化数据所用的天数
    fixedSize = 0           # 每次交易的数量

    # 策略变量

    intraTradeHigh = 0                  # 持仓期内的最高点
    intraTradeLow = 0                   # 持仓期内的最低点

    buyOrderIDList = []                 # OCO委托买入开仓的委托号
    shortOrderIDList = []               # OCO委托卖出开仓的委托号
    orderList = []                      # 保存委托代码的列表

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'kkLength',
                 'kkDev',
                 'fixedSize']

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'kkUp',
               'kkDown']
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos',
                'intraTradeHigh',
                'intraTradeLow']    

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(S002_KK_Strategy, self).__init__(ctaEngine, setting)
        
        self.bg = BarGenerator(self.onBar, 60, self.on60Bar)     # 创建K线合成器对象
        self.am = ArrayManager()
        
        self.buyOrderIDList = []
        self.shortOrderIDList = []
        self.orderList = []

        self.kkUp = 0                            # KK通道上轨
        self.kkDown = 0                          # KK通道下轨
        self.mid = 0                             # KK通道中轨

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
        self.writeCtaLog(u'%s策略启动' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）""" 
        self.bg.updateTick(tick)

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        self.bg.updateBar(bar)
    
    #----------------------------------------------------------------------
    def on60Bar(self, bar):
        """收到60分钟K线"""
        # 撤单撤掉之前发的所有单
        self.cancelAll()
    
        # 保存K线数据
        am = self.am
        am.updateBar(bar)
        if not am.inited:
            return
        
        # 计算指标数值
        self.kkUp, self.kkDown ,self.mid= am.keltner(self.kkLength, self.kkDev, array=True)
        
        # 判断是否要进行交易
    
        # 当前无仓位，发送多仓或者空仓
        if self.pos == 0:
            if self.mid[-1] > self.mid[-2]: # 当均线向上的时候
                self.buy(self.kkUp[-1], self.fixedSize, True)
            if self.mid[-1] < self.mid[-2]: # 当均线向下的时候
                self.short(self.kkDown[-1], self.fixedSize, True)

        # 持有多头仓位
        elif self.pos > 0:
            self.sell(self.mid[-1], abs(self.pos), True)
    
        # 持有空头仓位
        elif self.pos < 0:
            self.cover(self.mid[-1], abs(self.pos), True)
    
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
        print u"%s %s %s %s %s %s " % (trade.symbol,trade.direction,trade.offset,trade.price,trade.volume, trade.tradeTime)
                
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass