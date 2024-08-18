# region imports
from AlgorithmImports import *
# endregion
'''
Filter for stocks with a minimum daily volume of 500,000 shares and a price between $10 and $100.
Develop a strategy that takes a long position when the 10-day EMA crosses above the 50-day EMA 
and the ADX is above 25, 
and takes a short position when the 10-day EMA crosses below the 50-day EMA 
and the ADX is below 20.


'''

class CrawlingYellowGreenTermite(QCAlgorithm):

    def Initialize(self):
        self.SetCash(100000)
        self.SetStartDate(2021,1,1)
        self.SetEndDate(2022,1,1)
        self.AddUniverse(self.CoarseFilter)
        self.UniverseSettings.Resolution=Resolution.Minute 
        self.activestocks=[]
        self.lema={}
        self.sema={}
        self.adx={}
    
    def CoarseFilter(self,coarse):

        return [x.Symbol for x in coarse if x.DollarVolume>500000 and x.Price>=10 and x.Price<=100][:30]
    
    def OnSecuritiesChanged(self,changes):
        
        for i in changes.RemovedSecurities:
            if i.Symbol in self.activestocks:
                self.activestocks.remove(i.Symbol)
            if i.Symbol in self.lema:
                del self.lema[i.Symbol]
            if i.Symbol in self.sema:
                del self.sema[i.Symbol]
            if i.Symbol in self.adx:
                del self.adx[i.Symbol]
        
        for i in changes.AddedSecurities:
            if i.Symbol not in self.activestocks:
                self.activestocks.append(i.Symbol)
            if i.Symbol not in self.lema:
                self.lema[i.Symbol]=self.EMA(i.Symbol,50)
            if i.Symbol not in self.sema:
                self.sema[i.Symbol]=self.EMA(i.Symbol,10)
            if i.Symbol not in self.adx:
                self.adx[i.Symbol]=self.ADX(i.Symbol,20)
        
        self.current_position=np.zeros(len(self.activestocks))
        self.entryprice=np.zeros(len(self.activestocks))
        self.sl=np.zeros(len(self.activestocks))
        self.tp=np.zeros(len(self.activestocks))

        if self.activestocks!=[]:
            symbol=self.activestocks[0]
            self.Schedule.On(
                self.date_rules.every_day(),
                self.time_rules.before_market_close(symbol,minutes_before_close=2),
                self.square_off
            )
    
    def OnData(self,data):
        ct=self.Time.time()
        st=time(9,30)
        et=time(15,28)
        if ct>st and ct<et:
            for i in range(0,len(self.activestocks)):
                if self.activestocks[i] not in data.Bars:
                    continue
                if not self.sema[self.activestocks[i]].IsReady:
                    continue
                if not self.lema[self.activestocks[i]].IsReady:
                    continue
                if not self.adx[self.activestocks[i]].IsReady:
                    continue
                cp=data[self.activestocks[i]].Price 
                l=self.lema[self.activestocks[i]].Current.Value 
                s=self.sema[self.activestocks[i]].Current.Value 
                adx=self.adx[self.activestocks[i]].Current.Value 
                if (self.current_position[i]==0):
                    if s>l and adx>25:
                        self.SetHoldings(self.activestocks[i],1/len(self.activestocks))
                        self.current_position[i]=1
                        self.entryprice[i]=cp
                        self.sl[i]=self.entryprice[i]*0.85
                        self.tp[i]=self.entryprice[i]*1.15
                        self.Log('Entering Long Position')
                    
                    elif l>s and adx<20:
                        self.SetHoldings(self.activestocks[i],-1/len(self.activestocks))
                        self.current_position[i]=-1
                        self.entryprice[i]=cp 
                        self.sl[i]=self.entryprice[i]*1.15
                        self.tp[i]=self.entryprice[i]*0.85
                        self.Log("Entering Short Position")
                
                elif (self.current_position[i]==1):
                    if cp>=self.tp[i] or cp<=self.sl[i]:
                        self.Liquidate(self.activestocks[i])
                        self.current_position[i]=0
                        self.entryprice[i]=0
                        self.sl[i]=0
                        self.tp[i]=0
                        self.Log("Exiting Long Position")
                    elif cp>self.entryprice[i]:
                        self.sl[i]=cp*0.85
                
                elif (self.current_position[i]==-1):
                    if cp<=self.tp[i] or cp>=self.sl[i]:
                        self.Liquidate(self.activestocks[i])
                        self.current_position[i]=0
                        self.entryprice[i]=0
                        self.sl[i]=0
                        self.tp[i]=0
                        self.Log("Exiting Short Position")
                    elif cp<self.entryprice[i]:
                        self.sl[i]=cp*1.15
        
        else:
            pass
    
    def square_off(self):
        self.Liquidate()
        for i in range(0,len(self.activestocks)):
            self.Liquidate(self.activestocks[i])
            self.current_position[i]=0
            self.entryprice[i]=0
            self.sl[i]=0
            self.tp[i]=0
        self.Log("day end liquidation")

