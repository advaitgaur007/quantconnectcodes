# region imports
from AlgorithmImports import *
# endregion
'''
Universe Selection: Select stocks with a market capitalization above $10 billion 
and an average daily volume greater than 1 million shares.
Task: Implement a strategy that takes a long position when the 14-day RSI crosses above 30 
and the 20-day SMA crosses above the 50-day SMA, 
and takes a short position when the RSI crosses below 70 
and the 20-day SMA crosses below the 50-day SMA.

'''
class FatBlackKangaroo(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2021,1,1)
        self.SetEndDate(2022,1,1)
        self.SetCash(100000)
        self.AddUniverse(self.CoarseFilter,self.FineFilter)
        self.UniverseSettings.Resolution=Resolution.Minute 
        self.activestocks=[]
        self.stma={}
        self.ltma={}
        self.ltrsi={}
        self.strsi={}
    
    def CoarseFilter(self,coarse):
        sortbyvol= sorted(coarse,key=lambda x:x.DollarVolume,reverse=True)
        return [x.Symbol for x in sortbyvol if x.HasFundamentalData and x.DollarVolume>1000000]
    
    def FineFilter(self,fine):

        sortbymcap=sorted(fine,key=lambda x:x.MarketCap,reverse=True)
        return [x.Symbol for x in sortbymcap if x.MarketCap>1000000000][:10]
    
    def OnSecuritiesChanged(self,changes):

        for i in changes.RemovedSecurities:
            if i.Symbol in self.activestocks:
                self.activestocks.remove(i.Symbol)
            if i.Symbol in self.stma:
                del self.stma[i.Symbol]
            if i.Symbol in self.ltma:
                del self.ltma[i.Symbol]
            if i.Symbol in self.strsi:
                del self.strsi[i.Symbol]
            if i.Symbol in self.ltrsi:
                del self.ltrsi[i.Symbol]
        
        for i in changes.AddedSecurities:
            if i.Symbol not in self.activestocks:
                self.activestocks.append(i.Symbol)
            if i.Symbol not in self.stma:
                self.stma[i.Symbol]=self.SMA(i.Symbol,20,Resolution.Daily)
            if i.Symbol not in self.ltma:
                self.ltma[i.Symbol]=self.SMA(i.Symbol,50,Resolution.Daily)
            if i.Symbol not in self.strsi:
                self.strsi[i.Symbol]=self.RSI(i.Symbol,14,Resolution.Daily)
            if i.Symbol not in self.ltrsi:
                self.ltrsi[i.Symbol]=self.RSI(i.Symbol,30,Resolution.Daily)
        
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
                if not self.stma[self.activestocks[i]].IsReady:
                    continue 
                if not self.ltma[self.activestocks[i]].IsReady:
                    continue
                if not self.strsi[self.activestocks[i]].IsReady:
                    continue
                if not self.ltrsi[self.activestocks[i]].IsReady:
                    continue
                cp=data[self.activestocks[i]].Price
                stma=self.stma[self.activestocks[i]].Current.Value
                ltma=self.ltma[self.activestocks[i]].Current.Value
                strsi=self.strsi[self.activestocks[i]].Current.Value
                ltrsi=self.ltrsi[self.activestocks[i]].Current.Value
                if (self.current_position[i]==0):
                    if stma>ltma and strsi>ltrsi:
                        self.SetHoldings(self.activestocks[i],1/len(self.activestocks))
                        self.current_position[i]=1
                        self.entryprice[i]=cp
                        self.sl[i]=self.entryprice[i]*0.85
                        self.tp[i]=self.entryprice[i]*1.15
                        self.Log("Entering Long Position")
                    
                    elif ltma>stma and ltrsi>strsi:
                        self.SetHoldings(self.activestocks[i],-1/len(self.activestocks))
                        self.current_position[i]=-1
                        self.entryprice[i]=cp 
                        self.sl[i]=self.entryprice[i]*1.15
                        self.tp[i]=self.entryprice[i]*0.85
                        self.Log("Entering Short Position")
                
                elif (self.current_position[i]==1):

                    if cp>=self.tp[i] or cp<=self.sl[i]:
                        self.Liquidate(self.activestocks[i])
                        self.entryprice[i]=0
                        self.sl[i]=0
                        self.tp[i]=0
                        self.Log("Exiting Long Position")
                    
                    elif cp>self.entryprice[i]:
                        self.sl[i]=cp*0.85
                
                elif (self.current_position[i]==-1):
                    if cp<=self.tp[i] or cp>=self.sl[i]:
                        self.Liquidate(self.activestocks[i])
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
            self.entryprice[i]=0
            self.sl[i]=0
            self.tp[i]=0
        self.Log("Day End Liquidation")



                    

            

            




