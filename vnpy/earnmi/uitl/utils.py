from vnpy.trader.constant import Interval, Exchange, Status, Direction

class utils:
    def to_vt_symbol(code: str) -> str:
        if (not code.__contains__(".")):
            symbol = f"{code}.{Exchange.SZSE.value}"
            if code.startswith("6"):
                symbol = f"{code}.{Exchange.SSE.value}"
            return symbol
        return code

    def getExchange(self, code: str) -> Exchange:
        if code.startswith("6"):
            return Exchange.SSE
        return Exchange.SZSE
