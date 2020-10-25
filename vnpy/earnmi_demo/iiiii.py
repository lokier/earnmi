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
r1=[12.27,13.5,13.04,12.81,11.68,11.52,12.03,12.22,12.12,11.99,12.17,12.09,13.3,12.77,12.47,12.6,12.32,12.4,12.81,12.46,12.63,12.97,12.78,12.,11.6,11.47,11.63,11.69,11.72,11.69]
r2=[8.13504080e+07,1.13646481e+08,-4.37074637e+07,-7.41894702e+07,-5.38809519e+07,-1.93572970e+07,4.39842442e+07,-5.67130411e+06,3.25975693e+07,2.34355329e+07,-2.35625847e+07,2.05248583e+07,1.04991195e+08,-8.16036959e+07,1.36948647e+07,-2.53111898e+07,-2.62525729e+07,1.90618240e+07,-6.09945652e+06,-2.65866030e+07,2.03893137e+07,1.66727989e+07,-4.33756070e+07,-2.69457281e+07,5.10129003e+06,4.81813960e+06,4.46477820e+06,8.67512624e+06,1.33603600e+06,0.00000000e+00]

r1= np.array(r1)
r2 = np.array(r2)
ret = talib.CORREL(r1, r2, timeperiod=len(r1))
print(f"v:{ret[-1]}")
r2 = r2 * 10000
ret = talib.CORREL(r1, r2, timeperiod=len(r1))
print(f"v:{ret[-1]}")
r1=  r1 /100
ret = talib.CORREL(r1, r2, timeperiod=len(r1))
print(f"v:{ret[-1]}")



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


bigNum = 1000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
sdf = bigNum * 3453454354354354353454356464564564645654645645646334564464
print(type(sdf))
print(sdf)
