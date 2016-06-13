
import numpy as np
import Numnum

import pdb
import matplotlib.pyplot as mp

def kmeans(data, k):
    Numnum.arguments('data', data, 'k', k);    
    (means, clust, err) = kmeans_internal(data, k)
    for i in range(0, 5):
        (means_, clust_, err_) = kmeans_internal(data, k)
        if err_ < err:
            means = means_
            clust = clust_
            err   = err_
    # NB: we need to convert indices and type to be same as Matlab!
    Numnum.returns('means', means, 'clust', clust+1, 'err', float(err))
    return (means, clust, err)

def distances(mu, data):
    d = np.zeros((data.shape[0], 1))
    Numnum.arguments("mu", mu, "data", data)
    for j in range(0, data.shape[0]):
        dist = data[j, :] - mu
        d[j] = np.dot(dist, dist.T)
    Numnum.returns("d", d)
    return d

def kmeans_internal(data, k):
    n = data.shape[0]
    p = data.shape[1]
    
    idx   = np.floor(Numnum.rand(k,1) * n).astype(int)
    means = data[idx[:,0]] + Numnum.randn(k, p) * 1e-3
    dists = np.zeros((n, k))
    clust = np.zeros((n, 1))
    done  = 0
    err   = 0.0

    while done != k:
        done = 0
        for i in range(0, k):
            mu = means[i, :]
            dists[:,i] = distances(mu, data)
        vals  = np.amin(dists,  axis=1)
        clust = np.argmin(dists, axis=1)
        err   = vals.sum()

        for i in range(0, k):
            mem = data[clust == i]
            if mem.shape[0]:
                mu  = mem.mean(axis=0)
                eps = np.linalg.norm(means[i, :] - mu) 
                if eps < 1e-3:
                    done = done + 1
                means[i, :] = mu
    return (means, clust, err)
