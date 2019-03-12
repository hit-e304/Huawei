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

cross_inf = read_inf(cross_addr)
road_inf = read_inf(road_addr)
car_inf = read_inf(car_addr)

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
                    array[i][j[0]-1] = int(j[k])
        
        graph[cross_i[0]] = connect_i
    return graph, array

class Car():
    def __init__(self, input_info, **kwargs):
        self.num = input_info[0]
        self.init_node = input_info[1]
        self.final_node = input_info[2] 
        self.speed = input_info[3]
        self.init_time = input_info[4]

        self.cur_road = 0
        self.cur_channel = 0
        self.cur_pos = 0

class Road:
    def __init__(self, input_info, **kwargs):
        self.num = input_info[0]
        self.len = input_info[1]
        self.max_speed = input_info[2]
        self.channel_num = input_info[3]
        self.is_duplex = input_info[6]
        self.channel = np.zeros([self.channel_num, self.len])

# road init
names = locals()
for i in range(len(road_inf)):
    names['road_' + str(road_inf[i][0])] = Road(road_inf[i])

# car init
names = locals()
for i in range(len(car_inf)):
    names['car_' + str(car_inf[i][0])] = Car(car_inf[i])