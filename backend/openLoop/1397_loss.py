import sys
import numpy as np
import time

car_per_sec = 17 # can't higher than 17

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
    array_dis = np.zeros([a, a]) + 10000 - 10000 * np.eye(a)
    array_road = np.zeros([a, a])
    array_loss = np.zeros([a, a]) + 10000 - 10000 * np.eye(a)
    road_list = []
    cross_list  = []

    for i in range(len(road)):
        road_list.append(road[i][0])
    
    for i in range(len(cross)):
        cross_list.append(cross[i][0])

    for i in road:
        name, length, channel, speed_lim, start_id, end_id, is_dux = i ###### is_dux = i[6]???
        start_id -= 1
        end_id -= 1
        loss = length * (1 + 2 / channel) - 0 * speed_lim + 20

        if is_dux == 1:
            array_dis[start_id][end_id] = array_dis[end_id][start_id] = length
            array_road[start_id][end_id] = array_road[end_id][start_id] = name
            #TODO: design of loss 
            array_loss[start_id][end_id] = array_loss[end_id][start_id] = loss
        else:
            array_dis[start_id][end_id] = length
            array_road[start_id][end_id] = name
            #TODO: design of loss
            array_loss[start_id][end_id] = loss

    return graph, array_dis, array_road, array_loss, cross_list, road_list


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
        #TODO: this can to be changed to better function
        delta = 1 + (k-1) * 0.01
        cur_group = car_divide_speed[-k]
        if not cur_group:
            continue
        cur_amount = len(cur_group)
        
        for i in range(cur_amount):
            car_time_sche[cur_group[i]] = time
            if (i+1) % int(car_per_sec * delta * 10) == 0:
                time += 10

    return car_time_sche


def main():

    car_path = sys.argv[1]
    road_path = sys.argv[2]
    cross_path = sys.argv[3]
    answer_path = sys.argv[4]

    cross_inf = read_inf(cross_path)
    road_inf = read_inf(road_path)
    car_inf = read_inf(car_path)

    _, map_dis_array, map_road_array, map_loss_array, _, _ = map_graph(cross_inf, road_inf)
    car_time_sche = time_split(car_inf, car_per_sec)
    answer = all_car_path(map_loss_array, map_road_array, car_inf, car_time_sche)
    # answer = all_car_path(map_dis_array, map_road_array, car_inf, car_time_sche)
    

    with open(answer_path, 'w') as fp:
        fp.write('\n'.join(str(x) for x in answer))


if __name__ == "__main__":
    main()