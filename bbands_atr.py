# region imports
from AlgorithmImports import *
# endregion
'''
Select stocks with an average daily volume above 1 million 
and a market capitalization over $2 billion.

Create a strategy that takes a long position when the 
price closes above the upper Bollinger Band and the ATR (14) is increasing, 
and takes a short position when the price closes below the lower Bollinger Band 
and the ATR is decreasing.


'''

class DeterminedFluorescentPinkLemur(QCAlgorithm):

    def Initialize(self):
        self.SetCash(100000)
        self.SetStartDate(2022,1,1)
        self.SetEndDate(2023,1,1)
        self.AddUniverse(self.CoarseFilter,self.FineFilter)
        self.UniverseSettings.Resolution=Resolution.Minute 
        self.activestocks=[]
        self.atr={}
        self.bb={}
        self.comp_atr=[]
    
    def CoarseFilter(self,coarse):

        return [x.Symbol for x in coarse if x.DollarVolume>1000000 and x.HasFundamentalData][:30]
    
    def FineFilter(self,fine):

        return [x.Symbol for x in fine if x.MarketCap>2000000000]
    
    def OnSecuritiesChanged(self,changes):

        for i in changes.RemovedSecurities:
            if i.Symbol in self.activestocks:
                self.activestocks.remove(i.Symbol)
            if i.Symbol in self.atr:
                del self.atr[i.Symbol]
            if i.Symbol in self.bb:
                del self.bb[i.Symbol]
        
        for i in changes.AddedSecurities:
            if i.Symbol not in self.activestocks:
                self.activestocks.append(i.Symbol)
            if i.Symbol not in self.atr:
                self.atr[i.Symbol]=self.ATR(i.Symbol,14,MovingAverageType.Simple)
            if i.Symbol not in self.bb:
                self.bb[i.Symbol]=self.BB(i.Symbol,12,126,9)
        
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
                if not self.atr[self.activestocks[i]].IsReady:
                    continue
                if not self.bb[self.activestocks[i]].IsReady:
                    continue
                if len(self.comp_atr)<2:
                    continue
                cp=data[self.activestocks[i]].Price
                l=self.bb[self.activestocks[i]].lower_band.Current.Value
                u=self.bb[self.activestocks[i]].upper_band.Current.Value
                if len(self.comp_atr)>2:
                    self.com_atr.pop(0)
                self.comp_atr.append(self.atr[self.activestocks[i]].Current.Value)
                if (self.current_position[i]==0):
                    if self.comp_atr[-1]>self.comp_atr[0] and cp>l:
                        self.SetHoldings(self.activestocks[i],1/len(self.activestocks))
                        self.current_position[i]=1
                        self.entryprice[i]=cp 
                        self.sl[i]=self.entryprice[i]*0.85
                        self.tp[i]=self.entryprice[i]*1.15
                        self.Log("Entering Long Position")
                    
                    elif self.comp_atr[-1]<self.comp_atr[0] and cp<l:
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
            self.current_position[i]=0
            self.entryprice[i]=0
            self.sl[i]=0
            self.tp[i]=0
        self.Log("Day End Liquidation")



                
