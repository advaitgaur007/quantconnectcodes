# region imports
from AlgorithmImports import *
# endregion
'''
Select the top 100 stocks by dollar volume with a price greater than $20.
Create a strategy that takes a long position when the MACD line crosses above the signal line 
and the price is above the upper Bollinger Band, 
and takes a short position when the MACD line crosses below the signal line 
and the price is below the lower Bollinger Band.


'''

class UpgradedOrangeHyena(QCAlgorithm):

    def Initialize(self):
        self.SetCash(100000)
        self.SetStartDate(2021,1,1)
        self.SetEndDate(2022,1,1)
        self.AddUniverse(self.CoarseFilter)
        self.UniverseSettings.Resolution=Resolution.Minute 
        self.activestocks=[]
        self.macd={}
        self.bb={}
    
    def CoarseFilter(self,coarse):

        sortbyvol= sorted(coarse,key=lambda x:x.DollarVolume,reverse=True)
        return [x.Symbol for x in sortbyvol if x.HasFundamentalData and x.Price>20][:100]
    
    def OnSecuritiesChanged(self,changes):

        for i in changes.RemovedSecurities:
            if i.Symbol in self.activestocks:
                self.activestocks.remove(i.Symbol)
            if i.Symbol in self.macd:
                del self.macd[i.Symbol]
            if i.Symbol in self.bb:
                del self.bb[i.Symbol]
        
        for i in changes.AddedSecurities:
            if i.Symbol not in self.activestocks:
                self.activestocks.append(i.Symbol)
            if i.Symbol not in self.macd:
                self.macd[i.Symbol]=self.MACD(i.Symbol,12,26,9)
            if i.Symbol not in self.bb:
                self.bb[i.Symbol]=self.BB(i.Symbol,30,2)
        
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
                if not self.macd[self.activestocks[i]].IsReady or not self.bb[self.activestocks[i]].IsReady:
                    continue
                cp=data[self.activestocks[i]].Price 
                u=self.bb[self.activestocks[i]].upper_band.Current.Value
                l=self.bb[self.activestocks[i]].lower_band.Current.Value 
                signal=self.macd[self.activestocks[i]].signal.Current.Value
                line=self.macd[self.activestocks[i]].fast.Current.Value

                if self.current_position[i]==0:

                    if line>signal and cp>u:
                        self.SetHoldings(self.activestocks[i],1/len(self.activestocks))
                        self.current_position[i]=1
                        self.entryprice[i]=cp
                        self.sl[i]=self.entryprice[i]*0.85
                        self.tp[i]=self.entryprice[i]*1.15
                        self.Log("Entering Long Position")
                    
                    elif line<signal and cp<l:
                        self.SetHoldings(self.activestocks[i],-1/len(self.activestocks))
                        self.current_position[i]=-1
                        self.entryprice[i]=cp
                        self.sl[i]=self.entryprice[i]*1.15
                        self.tp[i]=self.entryprice[i]*0.85
                        self.Log("Entering short position")
                
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
        self.Log("Day end liquidation")



