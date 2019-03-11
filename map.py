import numpy as np

cross_addr = 'cross.txt'
road_addr = 'road.txt'
car_addr = 'car.txt'

def read_inf(filename):
    out_list = []
    with open(filename, 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break            
            if line[0] == '#':
                continue
            
            out0 = line.replace('(', '')
            out0 = out0.replace(')', '')
            out0 = out0.strip()
            out1 = [int(i) for i in out0.split(',')]

            out_list.append(out1)
    return out_list

cross = read_inf(cross_addr)
road = read_inf(road_addr)
car = read_inf(car_addr)

def find_path(graph, start, end, path=[]):
        path = path + [start]
        if start == end:
            return path
        # if not graph.has_key(start):
        #     return None
        for node in graph[start]:
            if node not in path:
                newpath = find_path(graph, node, end, path)
                if newpath: return newpath
        return None

def find_all_paths(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return [path]
    # if not graph.has_key(start):
    #     return []
    paths = []
    for node in graph[start]:
        if node not in path:
            newpaths = find_all_paths(graph, node, end, path)
            for newpath in newpaths:
                paths.append(newpath)
    return paths

def find_shortest_path(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return path
    # if not graph.has_key(start):
    #     return None
    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = find_shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath
    return shortest

def delete(li, index):
    li_back = li[:index] + li[index+1:]
    return li_back

def map_graph(cross, road):
    a = len(cross)
    graph = {}
    array = np.zeros([a, a])
    for i in range(a):
        cross_i = cross[i]
        cross_else = delete(cross, i)
        connect_i = []

        for j in cross_else:
            for k in [1, 2, 3, 4]:
                if j[k] in cross_i and j[k] != -1:
                    connect_i.append(j[0])
                    array[i][j[0]-1] = j[k]
        
        graph[cross_i[0]] = connect_i
    return graph, array
