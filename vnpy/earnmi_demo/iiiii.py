import numpy as np
def correlation(x, y):
    upside = ((x - x.mean()) * (y - y.mean())).sum()
    dnside = x.std() * y.std()
    result = upside / dnside
    return result

def a_correlation(x,y,d,nd=False):
    #print("%d days(dims) of x reduction" % (d-1))
    res = map(lambda t: np.correlate(x[t:t+d],y[t:t+d]).tolist()[0],range(len(x)-d+1))
    return res;# if not nd else np.array(res)

r1 = [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
r2 = [6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
a = np.array(r1)
b = np.array(r2)
c = a_correlation(a,b,10,nd=False)

print(list(range(5)))

print(list(c))
