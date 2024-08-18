# region imports
from AlgorithmImports import *
# endregion
'''

Select stocks from the technology sector with a market cap above $5 billion.
Implement a strategy that takes a long position when the Stochastic Oscillator (14, 3) 
crosses above 20 and the MACD histogram is positive, 
and takes a short position when the Stochastic Oscillator crosses below 80 
and the MACD histogram is negative.


'''

class FormalYellowGreenParrot(QCAlgorithm):

    def Initialize(self):
        self.SetCash(100000)
        self.SetStartDate(2021,1,1)
        self.SetEndDate(2022,1,1)
        self.AddUniverse(self.CoarseFilter,self.FineFilter)
        self.UniverseSettings.Resolution=Resolution.Minute 
        self.activestocks=[]
        self.macd={}
        self.stoch={}
    
    def CoarseFilter(self,coarse):

        return [x.Symbol for x in coarse if x.HasFundamentalData][:30]
    
    def FineFilter(self,fine):

        return [x.Symbol for x in fine if x.AssetClassification.MorningstarSectorCode==MorningstarSectorCode.TECHNOLOGY]
    
    def OnSecuritiesChanged(self,changes):

        for i in changes.RemovedSecurities:
            if i.Symbol in self.activestocks:
                self.activestocks.remove(i.Symbol)
            if i.Symbol in self.macd:
                del self.macd[i.Symbol]
            if i.Symbol in self.stoch:
                del self.stoch[i.Symbol]
        
        for i in changes.AddedSecurities:
            if i.Symbol not in self.activestocks:
                self.activestocks.append(i.Symbol)
            if i.Symbol not in self.macd:
                self.macd[i.Symbol]=self.MACD(i.Symbol,12,26,9)
            if i.Symbol not in self.stoch:
                self.stoch[i.Symbol]=self.STO(i.Symbol,14,14,3)
        
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
                if not self.macd[self.activestocks[i]].IsReady or not self.stoch[self.activestocks[i]].IsReady:
                    continue
                cp=data[self.activestocks[i]].Price
                stoch=self.stoch[self.activestocks[i]].stoch_k.Current.Value
                hist=self.macd[self.activestocks[i]].histogram.Current.Value
                if (self.current_position[i]==0):
                    if stoch>20 and hist>0:
                        self.SetHoldings(self.activestocks[i],1/len(self.activestocks))
                        self.current_position[i]=1
                        self.entryprice[i]=cp
                        self.sl[i]=self.entryprice[i]*0.85
                        self.tp[i]=self.entryprice[i]*1.15
                        self.Log("Entering Long Position")
                    
                    elif stoch<80 and hist<0:
                        self.SetHoldings(self.activestocks[i],1/len(self.activestocks))
                        self.current_position[i]=-1
                        self.entryprice[i]=cp
                        self.sl[i]=self.entryprice[i]*0.85
                        self.tp[i]=self.entryprice[i]*1.15
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
                        self.Log("Exiting Long Position")
                    
                    elif cp<self.entryprice[i]:
                        self.sl[i]=cp*1.15
                
        else:
            pass
    
    def square_off(self):
        self.Liquidate()
        for i in range(0,len(self.activestocks)):
            self.current_position[i]=0
            self.entryprice[i]=0
            self.sl[i]=0
            self.tp[i]=0
        self.Log("Day End Liquidation")

                    

                
