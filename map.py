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
    road_list = []

    for i in range(len(road)):
        road_list.append(road[i][0])

    for i in range(a):
        cross_i = cross[i]
        cross_else = delete(cross, i)
        connect_i = []

        for j in cross_else:
            for k in [1, 2, 3, 4]:
                if j[k] in cross_i and j[k] != -1:
                    connect_i.append(j[0])
                    array[i][j[0]-1] = road[road_list.index(j[k])][1]
        
        graph[cross_i[0]] = connect_i
    return graph, array


class Car:
    def __init__(self, input_info, **kwargs):
        self.num = input_info[0]
        self.init_cross = input_info[1]
        self.final_cross = input_info[2] 
        self.speed = input_info[3]
        self.init_time = input_info[4]

        self.start_flag = 0
        self.running_flag = 0
        self.in_cross_flag = 0
        self.cur_road = 0
        self.next_road = 0
        self.cur_channel = 0
        self.cur_pos = 0
        self.cur_speed = 0

    # step为按规则计算后能走的步数，由规则层提供;
    # cross_avail_flag为判断当前路口是否允许进入（非满）
    def update_pos_cross(self, step, cross_avail_flag, ):
        # init
        if self.start_flag == 0:
            self.next_road = self.init_cross
        else:
            self.next_road = self.cal_next_road()

        if cross_avail_flag:
            pass

    def update_pos_road(self, step):
        pass
    
    def whether_in_cross(self):
        pass
    
    def cal_next_road(self):
        return 0


class Road:
    def __init__(self, input_info, **kwargs):
        self.num = input_info[0]
        self.len = input_info[1]
        self.max_speed = input_info[2]
        self.channel_num = input_info[3]
        self.is_duplex = input_info[6]
        self.channel = np.zeros([self.channel_num, self.len])

        self.is_full = 0
        self.car_account = 0
    
    def update_inf(self):
        pass


class Cross:
    def __init__(self, input_info, **kwargs):
        self.num = input_info[0]
        self.road_north = input_info[1]
        self.road_east = input_info[2]
        self.road_south = input_info[3]
        self.road_west = input_info[4]
    
    def update_pos(self):
        pass
        


if __name__ == '__main__':
    cross_inf = read_inf(cross_addr)
    road_inf = read_inf(road_addr)
    car_inf = read_inf(car_addr)

    car_namespace = []
    road_namespace = []
    cross_namespace = []

    # road init
    names = locals()
    for i in range(len(road_inf)):
        names['road_' + str(road_inf[i][0])] = Road(road_inf[i])
        road_namespace.append('road_' + str(road_inf[i][0]))

    # car init
    for i in range(len(car_inf)):
        names['car_' + str(car_inf[i][0])] = Car(car_inf[i])
        car_namespace.append('car_' + str(car_inf[i][0]))
    
    # cross init
    for i in range(len(cross_inf)):
        names['cross_' + str(cross_inf[i][0])] = Cross(cross_inf[i])
        cross_namespace.append('cross_' + str(cross_inf[i][0]))
