from earnmi.chart.Chart import IndicatorItem


class IndicatorItemHelper(IndicatorItem):

    __cost_list = []
    __buy_price = None

    def buy(self,price:float):
        if not self.__buy_price is None:
            raise RuntimeError("error match!")
        self.__buy_price = price

    def sell(self,price:float):
        if  self.__buy_price is None:
            raise RuntimeError("error match!")
        cost = (price - self.__buy_price ) / self.__buy_price
        self.__buy_price = None
        self.__cost_list.append(cost)

    def hasBuy(self)->bool:
        return not self.__buy_price is None

    def getCostList(self):
        return self.__cost_list