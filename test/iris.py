
import numpy  as np
import scipy  as sp
import pandas as pd
import matplotlib.pyplot as mp
import Numnum

# NB: all unit testable functions need to be in this namespace
from kmeans import *

def iris(k=3):
    data = pd.read_csv("test/iris.dat")
    (means,clusts, err) = kmeans( data.loc[:, "sepal_length":"petal_width"].values, k)

    f = mp.figure(1)
    for c in data["class"].unique():
        points = data[ data["class"] == c ]
        mp.plot( points["sepal_length"], points["sepal_width"], "o", color=np.random.random((3, 1)))
    mp.plot( means[:,0], means[:,1], "ko", markersize=7)
    mp.show()


# iris(3)

# run all tests
#Numnum.replay("test/iris.mat")

# run integration test
#Numnum.replay("test/iris.mat",  1)

# run all unit tests
Numnum.replay("test/iris.mat", -1)

# run all unit tests for specific function
Numnum.replay("test/iris.mat", "distances")


# TODO
# Numnum.record("python.mat", kmeans, data.loc[:, "sepal_length":"petal_width"].values , k)
