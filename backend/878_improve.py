import sys
import numpy as np
import time


car_per_sec = 29
interval_time = 1
car_in_map = 2000
delta1 = 80
delta2 = 5


def readInf(filename):
    outList = []
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

            outList.append(out1)
    return outList


def map_graph(cross, road):
    """
    input: cross, cross_inf; road, road_inf
    """
    a = len(cross)
    graph = {}
    array_dis = np.zeros([a, a]) + 10000 - 10000 * np.eye(a)
    array_road = np.zeros([a, a])
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

        if is_dux == 1:
            array_dis[start_id][end_id] = array_dis[end_id][start_id] = length
            array_road[start_id][end_id] = array_road[end_id][start_id] = name
        else:
            array_dis[start_id][end_id] = length
            array_road[start_id][end_id] = name
    array_loss = array_dis

    return graph, array_dis, array_road, array_loss, cross_list, road_list


def record_road(batch, road_use_list, road_percent_list, road_id_bias):
    for i in batch:
        for j in i[2:]:
            road_use_list[j-road_id_bias] += 1
    
    sum_use = sum(road_use_list)
    a = len(road_use_list)
    for i in range(a):
        road_percent_list[i] = road_use_list[i] / sum_use
    
    return road_use_list, road_percent_list


def speed_split(car_inf):
    max_speed = 0
    car_divide_speed = []

    # split car by speed, car_divide_speed[k] means car speed as k+1
    for i in car_inf:
        if i[3] > max_speed:
            max_speed = i[3]
    for i in range(max_speed):
        car_divide_speed.append([])
    for i in car_inf:
        car_divide_speed[i[3] - 1].append(i[0])
 
    output_dic = {}
    for i in range(max_speed):
        output_dic[i+1] = car_divide_speed[i]
    return output_dic


# TODO: jv li jin de xian fa che
# calculate start time of each car by position
def time_split(group, car_inf, car_per_sec, time, interval_time, speed, car_id_bias, car_position):

    cur_batch = []
    group_divide_time = []
    group_len = len(group)

    if speed in [1, 2]:
        car_per_batch = int(car_per_sec * interval_time)
    elif speed in [3, 4]:
        car_per_batch = int(car_per_sec * interval_time * 1.1)
    elif speed in [5, 6]:
        car_per_batch = int(car_per_sec * interval_time * 1.1)
    else:
        car_per_batch = int(car_per_sec * interval_time * 1.1) 

    batch_num = int(group_len / car_per_batch) + 1
    # for i in group:
    #     group_position.append(car_position[i])

    for i in range(batch_num):
        cur_batch = []
        for j in range(car_per_batch):
            try: 
                cur_batch.append(group.pop())
            except:
                break
        group_divide_time.append(cur_batch)
    
    return group_divide_time


def dijkstra_minpath(start, end, matrix):
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


# update 3.19: change all to batch planning
# car_id_bias: car_id0 - 0; batch: [car_id1, car_id2, ...]
def cal_car_path(map_loss_array, map_road_array, car_inf, batch, car_id_bias, road_bias, road_inf, speed, time, final_time, all_time):

    path = []
    path_road_time = []
    
    for i in batch:
        car_id = i - car_id_bias
        path = dijkstra_minpath(car_inf[car_id][1]-1, car_inf[car_id][2]-1, map_loss_array)
        path_center = []
        a = len(path)
    
        path_center.append(car_inf[car_id][0])
        path_center.append(max(car_inf[car_id][4], time))
        for j in range(a-1):
            path_center.append(int(map_road_array[path[j]][path[j+1]]))
        path_road_time.append(path_center)

        run_time = 0
        for i in path_center[2:]:
            run_time += road_inf[i-road_bias][1] / min(speed, road_inf[i-road_bias][2])
        final_time.append(int(run_time) + 1 + time)
        all_time += run_time

    return path_road_time, final_time, all_time


def update_loss(array_loss, array_dis, road_inf, road_percent_list, road_id_bias, speed, cross_loss):
    """
    update: change loss function
    """
    for i in road_inf:
        name, length, channel, speed_lim, start_id, end_id, is_dux = i
        start_id -= 1
        end_id -= 1
        name -= road_id_bias
        use_rate = road_percent_list[name]
        # loss = length * (1 + 2 / channel / channel) - 0.5 * min(speed_lim, speed) + 20
        array_loss[start_id][end_id] = length * 1 / min(speed_lim, speed) + delta1 * use_rate / channel / length + delta2 * cross_loss[start_id][end_id]
        if is_dux == 1:
            array_dis[end_id][start_id] = length * 1 / min(speed_lim, speed) + delta1 * use_rate / channel / length + delta2 * cross_loss[end_id][start_id]
        else:
            array_loss[end_id][start_id] = 10000
    
    return array_loss


def update_car(final_time, time):
    new_final_time = []
    for i in final_time:
        if i > time:
            new_final_time.append(i)
    
    return new_final_time


def car_sort_time(cur_group, speed, car_inf, road_inf, map_dis_array, map_road_array, car_id_bias, road_id_bias):
    path = []
    car_time = []
    return_car_time = []

    for car in cur_group:
        car_id = car - car_id_bias
        path = dijkstra_minpath(car_inf[car_id][1]-1, car_inf[car_id][2]-1, map_dis_array)
        path_center = []
        a = len(path)
    
        for j in range(a-1):
            path_center.append(int(map_road_array[path[j]][path[j+1]]))

        run_time = 0
        for i in path_center[2:]:
            run_time += road_inf[i-road_id_bias][1] / min(speed, road_inf[i-road_id_bias][2])
        
        car_time.append([car, run_time])
    
    car_time = sorted(car_time, key=(lambda x:x[1]), reverse=True)
    a = len(car_time)
    for i in range(a):
        return_car_time.append(car_time[i][0])

    return return_car_time


def cal_cross_loss(cross_inf, road_inf, map_road_array):
    """
    update: calculate loss with each side
    """
    road_flow = {}
    a = len(cross_inf)
    map_cross_loss = np.zeros([a, a])
    for road in road_inf:
        road_flow[road[0]] = road[3] * road[2]
    
    for i in range(a):
        for j in range(a):
            if map_road_array[i][j] not in [10000, 0]:
                cross = cross_inf[i]
                road_id = int(map_road_array[i][j])
                dir_out = cross.index(road_id)

                dirc = [1, 2, 3, 4]
                for k in [1, 2, 3, 4]:
                    if cross[k] == -1:
                        dirc.remove(k)
                num_avail = len(dirc) - 1
                in_flow = 0
                for m in dirc:
                    if m == dir_out:
                        continue
                    in_flow += road_flow[cross[m]]

                loss = max((in_flow / num_avail - road_flow[cross[dir_out]]), 0) / road_flow[cross[dir_out]]

                map_cross_loss[i][j] = loss
    return map_cross_loss


def main():

    # car_path = sys.argv[1]
    # road_path = sys.argv[2]
    # cross_path = sys.argv[3]
    # answer_path = sys.argv[4]

    cross_path = '../SDK_python/CodeCraft-2019/config/cross.txt'
    road_path = '../SDK_python/CodeCraft-2019/config/road.txt'
    car_path = '../SDK_python/CodeCraft-2019/config/car.txt'
    answer_path = '../SDK_python/CodeCraft-2019/config/answer.txt'

    cross_inf = readInf(cross_path)
    road_inf = readInf(road_path)
    car_inf = readInf(car_path)

    _, map_dis_array, map_road_array, map_loss_array, _, _ = map_graph(cross_inf, road_inf)
    cross_loss = cal_cross_loss(cross_inf, road_inf, map_road_array)
    car_divide_speed = speed_split(car_inf)

    time = 1
    all_time = 0
    car_id_bias = car_inf[0][0]
    road_id_bias = road_inf[0][0]
    car_position = {}
    answer = []
    speed_list = []
    final_time = []
    road_use_list = road_percent_list = [0] * len(road_inf)

    # 1. divide by speed
    # 2. calculate time by position (TODO)
    # 3. loop: calculate path ; record road ; update map (TODO)
    for speed in car_divide_speed:
        speed_list.append(speed)
    speed_list.reverse()

    for speed in speed_list:
        cur_group = car_divide_speed[speed]
        if not cur_group:
            continue 

        group_divide_time = time_split(cur_group, car_inf, car_per_sec, time, interval_time, speed, car_id_bias, car_position)
        
        for batch in group_divide_time:
            batch_len = len(batch)
            while (len(final_time) > (car_in_map - batch_len)):
                time += 1
                final_time = update_car(final_time, time)
            
            batch_path_time, final_time, all_time = cal_car_path(map_loss_array, map_road_array, car_inf, batch, car_id_bias, road_id_bias, road_inf, speed, time, final_time, all_time)
            time += interval_time
            answer += batch_path_time
            road_use_list, road_percent_list = record_road(batch_path_time, road_use_list, road_percent_list, road_id_bias)
            map_loss_array = update_loss(map_loss_array, map_dis_array, road_inf, road_percent_list, road_id_bias, speed, cross_loss)



    # path_road = all_car_path(map_loss_array, map_road_array, car_inf)
    # car_time_sche = time_split(car_inf, car_per_sec, path_road)
    # answer = combine_time_path(car_inf, car_time_sche, path_road)
    # answer = all_car_path(map_dis_array, map_road_array, car_inf, car_time_sche)
    
    with open(answer_path, 'w') as fp:
        fp.write('\n'.join(str(tuple(x)) for x in answer))


if __name__ == "__main__":
    a = time.time()
    main()
    print(time.time() - a)