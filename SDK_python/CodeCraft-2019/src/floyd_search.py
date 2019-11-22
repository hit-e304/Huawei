# /usr/bin/python3
import numpy as np

def make_mat(m, n, fill=None):
    mat = []
    for i in range(m):
        mat.append([fill] * n)
    return mat

INF = 1e6


def show(dis, path):
    m = len(path)
    for i in range(m):
        for j in range(i + 1, m):
            print("%d->%d: " % (i, j), end="")
            k = path[i][j]
            print(i, end=" ")
            while k != j:
                print(k, end=" ")
                k = path[k][j]

            print(j)
            print(dis[i][j])


def floyd(graph):
    m = len(graph)
    dis = make_mat(m, m, fill = 0)
    # dis = np.zeros([m, m])
    path = make_mat(m, m, fill = 0)
    # path = np.zeros([m, m])
    for i in range(m):
        for j in range(m):
            dis[i][j] = graph[i][j]
            path[i][j] = j

    for k in range(m):
        for i in range(m):
            for j in range(m):
                if dis[i][k] + dis[k][j] < dis[i][j]:
                    dis[i][j] = dis[i][k] + dis[k][j]
                    path[i][j] = path[i][k]

    return dis, path


if __name__ == '__main__':
    graph = make_mat(5, 5, fill=INF)
    graph[0][1] = -1
    graph[0][2] = 3
    graph[1][2] = 3
    graph[1][3] = 2
    graph[1][4] = 2
    graph[3][1] = 1
    graph[3][2] = 5
    graph[4][3] = -3

    dis, path = floyd(graph)
    show(dis, path)

