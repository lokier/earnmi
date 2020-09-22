import numpy as np
import talib

def correlation(x, y):
    upside = ((x - x.mean()) * (y - y.mean())).sum()
    dnside = x.std() * y.std()
    result = upside / dnside
    return result

def a_correlation(x,y,d,nd=False):
    #print("%d days(dims) of x reduction" % (d-1))
    res = map(lambda t: np.correlate(x[t:t+d],y[t:t+d]).tolist()[0],range(len(x)-d+1))
    return res;# if not nd else np.array(res)

r1 = [3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0,11.0,12.0,13.0,14.0,15.0,16.0,17.0,18.0,19.0,20.0]
r2 = [6.0,7.0,8.0,9.0,10.0,11.0,12.0,13.0,14.0,15.0,16.0,17.0,18.0,19.0,20.0,21.0,22.0,23.0]
print(f'%4d,len:{len(r1)},%.4'
      f'f,%.4f' %  (34,3.434344,54.45566))

a = np.array(r1)
b = np.array(r2)
c = a_correlation(a,b,10,nd=False)
#d = talib.CORREL(a,b,5)
d = talib.LINEARREG(a,15);


class base(object):
    pass
e = base()
e.ef = 34
print(f"ef:{e.ef}")
print(list(range(5)))

print(list(c))
print(list(d))
