
"""
  浮点值范围编码值
"""
class FloatEncoder:

    def __init__(self,splits:['float']):
        self.splits = splits
        self.n = len(splits)
        pass
    """
    掩码值
    """
    def mask(self) ->int:
        return self.n + 1

    def encode(self,value:float)->int:
        code = 0
        for i in range(self.n, 0, -1):
            if value > self.splits[i - 1]:
                code = i
                break
        return code

    def descriptEncdoe(self,encode:int):
        if encode < 0 or encode > self.n:
            raise RuntimeError("out of range encode")
        if encode == 0:
            return f"[-max,{self.splits[encode]}]"
        if encode < self.n:
            return f"[{self.splits[encode-1]},{self.splits[encode]}]"
        return f"[{self.splits[self.n - 1]},max]"



if __name__ == "__main__":
    pct_split = [-7, -5, -3, -1.5, -0.5, 0.5, 1.5, 3, 5, 7]
    pctEncoder = FloatEncoder(pct_split)


    print(f"pctEncoder.encode(-6.2) : {pctEncoder.descriptEncdoe(pctEncoder.encode(-6.2))}")
    print(f"pctEncoder.encode(2.2) : {pctEncoder.descriptEncdoe(pctEncoder.encode(2.2))}")
    print(f"pctEncoder.encode(-7) : {pctEncoder.descriptEncdoe(pctEncoder.encode(-7))}")
    print(f"pctEncoder.encode(-7.3) : {pctEncoder.descriptEncdoe(pctEncoder.encode(-7.3))}")
    print(f"pctEncoder.encode(7.2) : {pctEncoder.descriptEncdoe(pctEncoder.encode(7.2))}")