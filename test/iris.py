
import numpy  as np
import scipy  as sp
import pandas as pd
import matplotlib.pyplot as mp
from kmeans import kmeans

import Numnum

def iris(k):
    data                = pd.read_csv("test/iris.dat")
    (means,clusts, err) = kmeans( data.loc[:, "sepal_length":"petal_width"].values , k)


    if False:
        f = mp.figure(1)
        for c in data["class"].unique():
            points = data[ data["class"] == c ]
            mp.plot( points["sepal_length"], points["sepal_width"], "o", color=np.random.random((3, 1)))
        mp.plot( means[:,0], means[:,1], "ko", markersize=7)
        mp.show()


# iris(3)

# TODO
# Numnum.record("python.mat", kmeans, data.loc[:, "sepal_length":"petal_width"].values , k)


Numnum.replay("iris.mat", -1)

# Numnum.replay("python.mat", kmeans, data.loc[:, "sepal_length":"petal_width"].values , k)
