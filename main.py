import sys
import numpy as np
import time


cross_path = 'cross.txt'
road_path = 'road.txt'
car_path = 'car.txt'
answer_path = 'answer.txt'

car_per_sec = 10


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


def delete(li, index):
    li_back = li[:index] + li[index+1:]
    return li_back


def map_graph(cross, road):
    """
    input: cross, cross_inf; road, road_inf
    """
    a = len(cross)
    graph = {}
    array = np.zeros([a, a]) + 10000 - 10000 * np.eye(a)
    array_road = np.zeros([a, a])
    road_list = []
    cross_list  = []

    for i in range(len(road)):
        road_list.append(road[i][0])
    
    for i in range(len(cross)):
        cross_list.append(cross[i][0])

    for i in range(a):
        cross_i = cross[i]
        cross_else = delete(cross, i)
        connect_i = []

        for j in cross_else:
            for k in [1, 2, 3, 4]:
                if j[k] in cross_i and j[k] != -1:
                    connect_i.append(j[0])
                    array[i][j[0]-1] = road[road_list.index(j[k])][1]
                    array_road[i][j[0]-1] = road[road_list.index(j[k])][0]
        
        graph[cross_i[0]] = connect_i

    create map by road
    for i in road:
        name = i[0]
        length = i[1]
        start_id = i[4] - 1
        end_id = i[5] - 1

        if i[6] == 1:
            array[start_id][end_id] = array[end_id][start_id] = length
            array_road[start_id][end_id] = array_road[end_id][start_id] = name
        else:
            array[start_id][end_id] = length
            array_road[start_id][end_id] = name

    return graph, array, array_road, cross_list, road_list


def Dijkstra_minpath(start, end, matrix):
    inf = 10000
    length = len(matrix)
    path_array = []
    temp_array = []
    path_array.extend(matrix[start])
    temp_array.extend(matrix[start])
    temp_array[start] = inf
    already_traversal = [start]
    path_parent = [start] * length

    i = start
    while(i != end):
        i = temp_array.index(min(temp_array))
        temp_array[i] = inf
        path = []
        path.append(i)
        k = i
        while (path_parent[k] != start):
            path.append(path_parent[k])
            k = path_parent[k]
        path.append(start)
        path.reverse()
        already_traversal.append(i)
        for j in range(length):
            if j not in already_traversal:
                if (path_array[i] + matrix[i][j]) < path_array[j]:
                    path_array[j] = temp_array[j] = path_array[i] + matrix[i][j]
                    path_parent[j] = i
    return path


def all_car_path(map_array, map_road_array, car_inf, car_time_sche):

    # map_len = len(map_array)
    car_len = len(car_inf)

    # start = time.time()
    path = []
    path_road = []
    for i in range(car_len):
        path = Dijkstra_minpath(car_inf[i][1]-1, car_inf[i][2]-1, map_array)
        path_center = []
        for j in range(len(path)-1):
            path_center.append(int(map_road_array[path[j]][path[j+1]]))
        
        time = car_time_sche[car_inf[i][0]]
        path_road.append(tuple([car_inf[i][0], max(car_inf[i][4], time)] + path_center))
    # end = time.time()
    # print(end - start)
    return path_road


# calculate start time of each car by speed
def time_split(car_inf, car_per_sec):
    max_speed = 0
    car_divide_speed = []
    car_time_sche = {}

    # split car by speed, car_divide_speed[k] means car speed as k+1
    for i in car_inf:
        if i[3] > max_speed:
            max_speed = i[3]
    for i in range(max_speed):
        car_divide_speed.append([])
    for i in car_inf:
        car_divide_speed[i[3] - 1].append(i[0])
    
    # calculate start time
    time = 0
    for k in range(max_speed):
        time += 1
        cur_group = car_divide_speed[-k]
        if not cur_group:
            continue
        cur_amount = len(cur_group)
        
        for i in range(cur_amount):
            car_time_sche[cur_group[i]] = time
            if (i+1) % car_per_sec == 0:
                time += 1

    return car_time_sche


def main():

    # car_path = sys.argv[1]
    # road_path = sys.argv[2]
    # cross_path = sys.argv[3]
    # answer_path = sys.argv[4]

    cross_inf = read_inf(cross_path)
    road_inf = read_inf(road_path)
    car_inf = read_inf(car_path)

    _, map_array, map_road_array, _, _ = map_graph(cross_inf, road_inf)
    car_time_sche = time_split(car_inf, car_per_sec)
    answer = all_car_path(map_array, map_road_array, car_inf, car_time_sche)

    with open(answer_path, 'w') as fp:
        fp.write('\n'.join(str(x) for x in answer))


if __name__ == "__main__":
    # start = time.time()
    main()
    # print(time.time() - start)