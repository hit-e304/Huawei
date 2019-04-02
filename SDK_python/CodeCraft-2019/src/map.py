import matplotlib.pyplot as plt
road_id_bias = 5000


cross_path = 'cross.txt'
road_path = 'road.txt'
car_path = 'car.txt'
answer_path = 'answer.txt'


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


def id2pos(i):
    a = i // 8
    b = i - 8 * a
    return a, b


def map(cross_inf, road_inf, line, road_id_bias):

    mngr = plt.get_current_fig_manager()
    mngr.window.wm_geometry("+380+310")
        
    x = []
    y = []

    for i in range(64):
        a, b = id2pos(i)
        x.append(a)
        y.append(b)

    plt.plot(x, y, 'ro')

    # for line in answer[2:]:
    for road in line:
        start_id = road_inf[road - road_id_bias][4]
        end_id = road_inf[road - road_id_bias][5]

        a0, b0 = id2pos(start_id-1)
        a1, b1 = id2pos(end_id-1)
        x0 = [a0, a1]
        y0 = [b0, b1]

        plt.plot(x0, y0, color='b')
    plt.ion()


cross_inf = read_inf(cross_path)
road_inf = read_inf(road_path)
car_inf = read_inf(car_path)
answer = read_inf(answer_path)

batch = 10
for i in range(1000):

    batch_road = answer[batch * i + 5000 : (batch*i+ batch) + 5000]
    for line in batch_road:

        line_read = line[2:]
        map(cross_inf, road_inf, line_read, road_id_bias)
        plt.pause(0.25)
        input()
       
        # plt.close()
        plt.clf()
    
