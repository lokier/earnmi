import datetime
from abc import abstractmethod
from typing import Sequence

from earnmi.core.Context import Context
from earnmi.data.BarDriver import DayRange
from earnmi.data.BarStorage import BarStorage
from earnmi.data.driver.JoinQuantBarDriver import JoinQuantBarDriver
from earnmi.data.driver.SinaUtil import SinaUtil
from earnmi.model.bar import LatestBar, BarData
from vnpy.trader.constant import Interval


class ZZ500StockDriver(JoinQuantBarDriver):

    NAME:str = '中证500'
    DESCRIPTION:str = '中证500的股票列表，过滤掉最近2年新上市的，总共485个'
    SYMBOAL_MAP = {'000008': '神州高铁', '000009': '中国宝安', '000012': '南玻A', '000021': '深科技', '000025': '特力A', '000027': '深圳能源', '000028': '国药一致', '000031': '大悦城', '000039': '中集集团', '000046': '泛海控股', '000050': '深天马A', '000060': '中金岭南', '000061': '农产品', '000062': '深圳华强', '000078': '海王生物', '000089': '深圳机场', '000090': '天健集团', '000156': '华数传媒', '000158': '常山北明', '000301': '东方盛虹', '000400': '许继电气', '000401': '冀东水泥', '000402': '金融街', '000415': '渤海租赁', '000488': '晨鸣纸业', '000501': '鄂武商A', '000513': '丽珠集团', '000519': '中兵红箭', '000528': '柳工', '000537': '广宇发展', '000543': '皖能电力', '000547': '航天发展', '000553': '安道麦A', '000559': '万向钱潮', '000563': '陕国投A', '000564': '供销大集', '000581': '威孚高科', '000598': '兴蓉环境', '000600': '建投能源', '000623': '吉林敖东', '000629': '攀钢钒钛', '000630': '铜陵有色', '000636': '风华高科', '000681': '视觉中国', '000685': '中山公用', '000686': '东北证券', '000690': '宝新能源', '000712': '锦龙股份', '000717': '韶钢松山', '000718': '苏宁环球', '000729': '燕京啤酒', '000732': '泰禾集团', '000738': '航发控制', '000739': '普洛药业', '000750': '国海证券', '000758': '中色股份', '000778': '新兴铸管', '000785': '居然之家', '000800': '一汽解放', '000807': '云铝股份', '000813': '德展健康', '000825': '太钢不锈', '000826': '启迪环境', '000830': '鲁西化工', '000848': '承德露露', '000869': '张裕A', '000877': '天山股份', '000878': '云南铜业', '000883': '湖北能源', '000887': '中鼎股份', '000898': '鞍钢股份', '000930': '中粮科技', '000932': '华菱钢铁', '000937': '冀中能源', '000959': '首钢股份', '000960': '锡业股份', '000967': '盈峰环境', '000970': '中科三环', '000975': '银泰黄金', '000983': '山西焦煤', '000987': '越秀金控', '000988': '华工科技', '000990': '诚志股份', '000997': '新大陆', '000998': '隆平高科', '000999': '华润三九', '001872': '招商港口', '001914': '招商积余', '002002': '鸿达兴业', '002004': '华邦健康', '002010': '传化智联', '002013': '中航机电', '002019': '亿帆医药', '002028': '思源电气', '002030': '达安基因', '002038': '双鹭药业', '002048': '宁波华翔', '002051': '中工国际', '002056': '横店东磁', '002064': '华峰化学', '002074': '国轩高科', '002075': '沙钢股份', '002078': '太阳纸业', '002080': '中材科技', '002081': '金螳螂', '002085': '万丰奥威', '002092': '中泰化学', '002093': '国脉科技', '002110': '三钢闽光', '002118': '紫鑫药业', '002124': '天邦股份', '002127': '南极电商', '002128': '露天煤业', '002131': '利欧股份', '002138': '顺络电子', '002152': '广电运通', '002155': '湖南黄金', '002156': '通富微电', '002174': '游族网络', '002183': '怡亚通', '002185': '华天科技', '002191': '劲嘉股份', '002195': '二三四五', '002203': '海亮股份', '002212': '天融信', '002217': '合力泰', '002221': '东华能源', '002223': '鱼跃医疗', '002233': '塔牌集团', '002242': '九阳股份', '002244': '滨江集团', '002249': '大洋电机', '002250': '联化科技', '002266': '浙富控股', '002268': '卫士通', '002273': '水晶光电', '002281': '光迅科技', '002285': '世联行', '002294': '信立泰', '002302': '西部建设', '002317': '众生药业', '002340': '格林美', '002353': '杰瑞股份', '002368': '太极股份', '002372': '伟星新材', '002373': '千方科技', '002375': '亚厦股份', '002382': '蓝帆医疗', '002385': '大北农', '002387': '维信诺', '002390': '信邦制药', '002396': '星网锐捷', '002399': '海普瑞', '002407': '多氟多', '002408': '齐翔腾达', '002414': '高德红外', '002416': '爱施德', '002419': '天虹股份', '002423': '中粮资本', '002424': '贵州百灵', '002429': '兆驰股份', '002434': '万里扬', '002439': '启明星辰', '002440': '闰土股份', '002444': '巨星科技', '002458': '益生股份', '002465': '海格通信', '002491': '通鼎互联', '002500': '山西证券', '002503': '搜于特', '002505': '鹏都农牧', '002506': '协鑫集成', '002507': '涪陵榨菜', '002511': '中顺洁柔', '002544': '杰赛科技', '002557': '洽洽食品', '002563': '森马服饰', '002572': '索菲亚', '002583': '海能达', '002589': '瑞康医药', '002595': '豪迈科技', '002603': '以岭药业', '002625': '光启技术', '002635': '安洁科技', '002640': '跨境通', '002648': '卫星石化', '002653': '海思科', '002665': '首航高科', '002670': '国盛金控', '002690': '美亚光电', '002701': '奥瑞金', '002709': '天赐材料', '002745': '木林森', '002797': '第一创业', '002807': '江阴银行', '002815': '崇达技术', '002818': '富森美', '002821': '凯莱英', '002831': '裕同科技', '002839': '张家港行', '002867': '周大生', '002901': '大博医疗', '002920': '德赛西威', '002925': '盈趣科技', '002926': '华西证券', '002936': '郑州银行', '300001': '特锐德', '300002': '神州泰岳', '300009': '安科生物', '300010': '豆神教育', '300012': '华测检测', '300017': '网宿科技', '300024': '机器人', '300026': '红日药业', '300058': '蓝色光标', '300070': '碧水源', '300072': '三聚环保', '300088': '长信科技', '300113': '顺网科技', '300115': '长盈精密', '300133': '华策影视', '300134': '大富科技', '300166': '东方国信', '300168': '万达信息', '300180': '华峰超纤', '300182': '捷成股份', '300197': '铁汉生态', '300207': '欣旺达', '300212': '易华录', '300244': '迪安诊断', '300251': '光线传媒', '300253': '卫宁健康', '300257': '开山股份', '300271': '华宇软件', '300274': '阳光电源', '300285': '国瓷材料', '300296': '利亚德', '300315': '掌趣科技', '300316': '晶盛机电', '300324': '旋极信息', '300357': '我武生物', '300376': '易事特', '300418': '昆仑万维', '300459': '金科文化', '300474': '景嘉微', '300482': '万孚生物', '300496': '中科创达', '300558': '贝达药业', '300595': '欧普康视', '300618': '寒锐钴业', '300630': '普利制药', '600006': '东风汽车', '600008': '首创股份', '600017': '日照港', '600021': '上海电力', '600022': '山东钢铁', '600026': '中远海能', '600037': '歌华有线', '600039': '四川路桥', '600053': '九鼎投资', '600056': '中国医药', '600058': '五矿发展', '600060': '海信视像', '600062': '华润双鹤', '600064': '南京高科', '600073': '上海梅林', '600079': '人福医药', '600094': '大名城', '600120': '浙江东方', '600125': '铁龙物流', '600126': '杭钢股份', '600132': '重庆啤酒', '600138': '中青旅', '600141': '兴发集团', '600143': '金发科技', '600153': '建发股份', '600155': '华创阳安', '600158': '中体产业', '600160': '巨化股份', '600161': '天坛生物', '600166': '福田汽车', '600167': '联美控股', '600171': '上海贝岭', '600195': '中牧股份', '600201': '生物股份', '600216': '浙江医药', '600256': '广汇能源', '600258': '首旅酒店', '600259': '广晟有色', '600260': '凯乐科技', '600266': '城建发展', '600273': '嘉化能源', '600277': '亿利洁能', '600282': '南钢股份', '600291': '西水股份', '600298': '安琪酵母', '600307': '酒钢宏兴', '600312': '平高电气', '600315': '上海家化', '600316': '洪都航空', '600325': '华发股份', '600329': '中新药业', '600335': '国机汽车', '600338': '西藏珠峰', '600339': '中油工程', '600348': '阳泉煤业', '600350': '山东高速', '600373': '中文传媒', '600376': '首开股份', '600380': '健康元', '600388': '龙净环保', '600392': '盛和资源', '600409': '三友化工', '600410': '华胜天成', '600415': '小商品城', '600418': '江淮汽车', '600426': '华鲁恒升', '600428': '中远海特', '600435': '北方导航', '600446': '金证股份', '600460': '士兰微', '600466': '蓝光发展', '600478': '科力远', '600486': '扬农化工', '600497': '驰宏锌锗', '600500': '中化国际', '600507': '方大特钢', '600511': '国药股份', '600515': '海航基础', '600521': '华海药业', '600528': '中铁工业', '600529': '山东药玻', '600535': '天士力', '600545': '卓郎智能', '600549': '厦门钨业', '600557': '康缘药业', '600563': '法拉电子', '600565': '迪马股份', '600566': '济川药业', '600567': '山鹰国际', '600572': '康恩贝', '600575': '淮河能源', '600580': '卧龙电驱', '600582': '天地科技', '600597': '光明乳业', '600598': '北大荒', '600623': '华谊集团', '600633': '浙数文化', '600639': '浦东金桥', '600640': '号百控股', '600642': '申能股份', '600643': '爱建集团', '600645': '中源协和', '600648': '外高桥', '600649': '城投控股', '600657': '信达地产', '600664': '哈药股份', '600667': '太极实业', '600673': '东阳光', '600675': '中华企业', '600694': '大商股份', '600699': '均胜电子', '600704': '物产中大', '600707': '彩虹股份', '600717': '天津港', '600718': '东软集团', '600728': '佳都科技', '600729': '重庆百货', '600733': '北汽蓝谷', '600737': '中粮糖业', '600739': '辽宁成大', '600748': '上实发展', '600751': '海航科技', '600754': '锦江酒店', '600755': '厦门国贸', '600757': '长江传媒', '600765': '中航重机', '600770': '综艺股份', '600776': '东方通信', '600777': '新潮能源', '600779': '水井坊', '600782': '新钢股份', '600787': '中储股份', '600801': '华新水泥', '600804': '鹏博士', '600808': '马钢股份', '600811': '东方集团', '600820': '隧道股份', '600823': '世茂股份', '600827': '百联股份', '600835': '上海机电', '600839': '四川长虹', '600845': '宝信软件', '600859': '王府井', '600862': '中航高科', '600863': '内蒙华电', '600869': '远东股份', '600874': '创业环保', '600875': '东方电气', '600879': '航天电子', '600881': '亚泰集团', '600884': '杉杉股份', '600885': '宏发股份', '600895': '张江高科', '600901': '江苏租赁', '600903': '贵州燃气', '600908': '无锡银行', '600909': '华安证券', '600917': '重庆燃气', '600959': '江苏有线', '600967': '内蒙一机', '600970': '中材国际', '600985': '淮北矿业', '600996': '贵广网络', '601000': '唐山港', '601003': '柳钢股份', '601005': '重庆钢铁', '601016': '节能风电', '601019': '山东出版', '601068': '中铝国际', '601098': '中南传媒', '601099': '太平洋', '601106': '中国一重', '601118': '海南橡胶', '601127': '小康股份', '601128': '常熟银行', '601139': '深圳燃气', '601168': '西部矿业', '601179': '中国西电', '601200': '上海环境', '601228': '广州港', '601233': '桐昆股份', '601333': '广深铁路', '601608': '中信重工', '601611': '中国核建', '601678': '滨化股份', '601689': '拓普集团', '601699': '潞安环能', '601717': '郑煤机', '601718': '际华集团', '601799': '星宇股份', '601801': '皖新传媒', '601811': '新华文轩', '601866': '中远海发', '601869': '长飞光纤', '601880': '大连港', '601928': '凤凰传媒', '601958': '金钼股份', '601966': '玲珑轮胎', '601969': '海南矿业', '603000': '人民网', '603025': '大豪科技', '603056': '德邦股份', '603077': '和邦生物', '603198': '迎驾贡酒', '603225': '新凤鸣', '603228': '景旺电子', '603233': '大参林', '603328': '依顿电子', '603338': '浙江鼎力', '603355': '莱克电气', '603377': '东方时尚', '603444': '吉比特', '603486': '科沃斯', '603515': '欧普照明', '603517': '绝味食品', '603556': '海兴电力', '603568': '伟明环保', '603605': '珀莱雅', '603650': '彤程新材', '603659': '璞泰来', '603707': '健友股份', '603708': '家家悦', '603712': '七一二', '603766': '隆鑫通用', '603806': '福斯特', '603816': '顾家家居', '603858': '步长制药', '603866': '桃李面包', '603868': '飞科电器', '603882': '金域医学', '603883': '老百姓', '603885': '吉祥航空', '603888': '新华网', '603939': '益丰药房'}


    @abstractmethod
    def get_name(self):
        return ZZ500StockDriver.NAME

    def get_description(self):
        return ZZ500StockDriver.DESCRIPTION

    @abstractmethod
    def get_symbol_lists(self):
        return list(ZZ500StockDriver.SYMBOAL_MAP.keys())

    @abstractmethod
    def get_symbol_name(self,symbol:str)->str:
        return ZZ500StockDriver.SYMBOAL_MAP.get(symbol)

    @abstractmethod
    def support_interval(self,interval:Interval)->bool:
        return interval == Interval.DAILY

    def to_jq_code(self,symbol:str)->str:
        if symbol.startswith("6"):
            return f"{symbol}.XSHG"
        else:
            return f"{symbol}.XSHE"

    @abstractmethod
    def download_bars_from_net(self, context:Context, symbol:str, days:DayRange, storage: BarStorage):
        """
        下载历史行情数据到数据库。
        """
        return super().download_bars_from_jq(context, symbol, days.start(), days.end(), Interval.DAILY,storage)

    @abstractmethod
    def fetch_latest_bar(self,symbol_list:['str'])->Sequence["LatestBar"]:
        """
        获取今天的行情数据。如果今天没有开盘的话，换回None。
        """
        return SinaUtil.fetch_latest_bar(symbol_list)


if __name__ == "__main__":
    pass