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

