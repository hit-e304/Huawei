from kmeans import kMeans
import numpy as np

test_data = np.random.rand(40, 2)
datMat = np.mat(test_data)
myCentroids,clustAssing = kMeans(datMat,4)

a, b = kMeans(datMat, 4)
c = b.tolist()

d = [0, 0, 0, 0]
e = [[None]] * 4
for i in range(len(c)):
    class_id = int(c[i][0])
    d[class_id] += 1
    

