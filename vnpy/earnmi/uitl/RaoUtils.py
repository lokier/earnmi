

class RaoUtils:
    """
    股票市值编码：
    0    0
	10亿：  1
	25亿：  2
    78：  2
    78： 3
    117
	175
	262
	393
	590
	885
	1327
	1990
	2985
	4448
	6672
	10008
    """
    def encodeMarketValue(value:float)->int:
        value = value / 100000000
        __encode_list = [0,10,25,78,117,175,262,393,590,885,1327,1990,2985,4448,6672,10008]
        size = len(__encode_list)
        for i in range(1,size):
            if value <__encode_list[i]:
                return i - 1
        return size - 1;
