import matplotlib.pyplot as plt
import math
import numpy as np

show_animation = True


class Node:

    def __init__(self, x, y, cost, pind):
        self.x = x
        self.y = y
        self.cost = cost
        self.pind = pind

    def __str__(self):
        return str(self.x) + "," + str(self.y) + "," + str(self.cost) + "," + str(self.pind)


def calc_fianl_path(ngoal, closedset, reso):
    # generate final course
    rx, ry = [ngoal.x * reso], [ngoal.y * reso]
    pind = ngoal.pind
    while pind != -1:
        n = closedset[pind]
        rx.append(n.x * reso)
        ry.append(n.y * reso)
        pind = n.pind

    return rx, ry


def a_star_planning(sx, sy, gx, gy, reso, crossMap):
    """
    gx: goal x position [m]
    gx: goal x position [m]
    ox: x position list of Obstacles [m]
    oy: y position list of Obstacles [m]
    reso: grid resolution [m]
    rr: robot radius[m]
    """

    nstart = Node(round(sx / reso), round(sy / reso), 0.0, -1)
    ngoal = Node(round(gx / reso), round(gy / reso), 0.0, -1)
    # ox = [iox / reso for iox in ox]
    # oy = [ioy / reso for ioy in oy]
    minx = 0
    miny = 0
    maxx = 7
    maxy = 7
    xw = 7

    # obmap, minx, miny, maxx, maxy, xw, yw = calc_obstacle_map(ox, oy, reso, rr)

    motion = get_motion_model()

    openset, closedset = dict(), dict()
    # openset[0] = nstart
    # openset[list(crossMap.keys())[list(crossMap.values()).index('[%d, %d]' % (nstart.x, nstart.y))]] = nstart
    openset[calc_index(nstart, xw, minx, miny)] = nstart

    while 1:
        c_id = min(openset, key=lambda o: openset[o].cost + calc_heuristic(ngoal, openset[o]))
        current = openset[c_id]

        # show graph
        # if show_animation:
        #     plt.plot(current.x * reso, current.y * reso, "xc")
        #     if len(closedset.keys()) % 10 == 0:
        #         plt.pause(0.001)

        if current.x == ngoal.x and current.y == ngoal.y:
            print("Find goal")
            ngoal.pind = current.pind
            ngoal.cost = current.cost
            break

        # Remove the item from the open set
        del openset[c_id]
        # Add it to the closed set
        closedset[c_id] = current

        # expand search grid based on motion model
        for i in range(len(motion)):
            node = Node(current.x + motion[i][0],
                        current.y + motion[i][1],
                        current.cost + motion[i][2], c_id)
            n_id = calc_index(node, xw, minx, miny)

            if n_id in closedset:
                continue

            if not verify_node(node, minx, miny, maxx, maxy):
                continue

            if n_id not in openset:
                openset[n_id] = node  # Discover a new node

            tcost = current.cost + calc_heuristic(current, node)

            if tcost >= node.cost:
                continue  # this is not a better path

            node.cost = tcost
            openset[n_id] = node  # This path is the best unitl now. record it!

    rx, ry = calc_fianl_path(ngoal, closedset, reso)

    return rx, ry


def calc_heuristic(n1, n2):
    w = 1.0  # weight of heuristic
    d = w * math.sqrt((n1.x - n2.x) ** 2 + (n1.y - n2.y) ** 2)
    return d


def verify_node(node, minx, miny, maxx, maxy):
    if node.x < minx:
        return False
    elif node.y < miny:
        return False
    elif node.x >= maxx:
        return False
    elif node.y >= maxy:
        return False

    # if obmap[node.x][node.y]:
    #     return False

    return True


# def calc_obstacle_map(ox, oy, reso, vr):
#     minx = round(min(ox))
#     miny = round(min(oy))
#     maxx = round(max(ox))
#     maxy = round(max(oy))
#     #  print("minx:", minx)
#     #  print("miny:", miny)
#     #  print("maxx:", maxx)
#     #  print("maxy:", maxy)
#
#     xwidth = int(round(maxx - minx))
#     ywidth = int(round(maxy - miny))
#     #  print("xwidth:", xwidth)
#     #  print("ywidth:", ywidth)
#
#     # obstacle map generation
#     obmap = [[False for i in range(xwidth)] for i in range(ywidth)]
#     for ix in range(xwidth):
#         x = ix + minx
#         for iy in range(ywidth):
#             y = iy + miny
#             #  print(x, y)
#             for iox, ioy in zip(ox, oy):
#                 d = math.sqrt((iox - x) ** 2 + (ioy - y) ** 2)
#                 if d <= vr / reso:
#                     obmap[ix][iy] = True
#                     break
#
#     return obmap, minx, miny, maxx, maxy, xwidth, ywidth


def calc_index(node, xwidth, xmin, ymin):
    return (node.y - ymin) * xwidth + (node.x - xmin)


def get_motion_model():
    # dx, dy, cost
    motion = [[1, 0, 1],
              [0, 1, 1],
              [-1, 0, 1],
              [0, -1, 1]]
              # [-1, -1, math.sqrt(2)],
              # [-1, 1, math.sqrt(2)],
              # [1, -1, math.sqrt(2)],
              # [1, 1, math.sqrt(2)]]

    return motion

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


def createCrossMap(cross_inf, road_inf, road_id_bias):
    '''
    Usage: Create cross map in xoy sys
    Input: cross_inf / road_inf:list[int]  road_id_bias:int
    output: mapDic:dict{[int]}  map_lim:list[int]
    '''
    crossLen = 1
    initX, initY = 0, 0
    maxX, maxY = 0, 0
    minX, minY =0, 0
    mapDic = {cross_inf[0][0]:[initX, initY]}
    finishCross = [cross_inf[0][0]]
    crossNum = len(cross_inf)
    while len(finishCross) < crossNum:
        reverseList = reversed(finishCross)
        for cross in reverseList:
            crossId, roadLine = cross_inf[cross-1][0], cross_inf[cross-1][1:]
            curX, curY = mapDic[crossId]
            for i, road in enumerate(roadLine):
                if road != -1:
                    roadInf = road_inf[road-road_id_bias]
                else:
                    continue
                crossFrom, crossTo = roadInf[4], roadInf[5]
                if crossFrom == crossId and crossTo not in finishCross:
                    if i == 0:
                        mapDic[crossTo] = [curX, curY+crossLen]
                        maxY = max(maxY, curY+crossLen)
                    elif i == 1:
                        mapDic[crossTo] = [curX+crossLen, curY]
                        maxX = max(curX+crossLen, maxX)
                    elif i == 2:
                        mapDic[crossTo] = [curX, curY-crossLen]
                        minY = min(maxY, curY-crossLen)
                    elif i == 3:
                        mapDic[crossTo] = [curX-crossLen, curY]
                        minX = min(minX, curX-crossLen)
                    finishCross.append(crossTo)
                elif crossTo == crossId and crossFrom not in finishCross:
                    if i == 0:
                        mapDic[crossFrom] = [curX, curY+crossLen]
                        maxY = max(maxY, curY+crossLen)
                    elif i == 1:
                        mapDic[crossFrom] = [curX+crossLen, curY]
                        maxX = max(curX+crossLen, maxX)
                    elif i == 2:
                        mapDic[crossFrom] = [curX, curY-crossLen]
                        minY = min(maxY, curY-crossLen)
                    elif i == 3:
                        mapDic[crossFrom] = [curX-crossLen, curY]
                        minX = min(minX, curX-crossLen)
                    finishCross.append(crossFrom)
                else:
                    continue
    map_lim = [maxX, minX, maxY, minY]
    return mapDic, map_lim

def main():
    print(__file__ + " start!!")

    cross_path = 'cross.txt'
    road_path = 'road.txt'
    car_path = 'car.txt'
    answer_path = 'answer.txt'

    cross_inf = read_inf(cross_path)
    road_inf = read_inf(road_path)
    car_inf = read_inf(car_path)

    road_id_bias = road_inf[0][0]

    crossMap, _ = createCrossMap(cross_inf, road_inf, road_id_bias)

    sx = 0
    sy = 0
    gx = 4
    gy = 4
    reso = 1

    rx, ry = a_star_planning(sx, sy, gx, gy, reso, crossMap)

    # # start and goal position
    # sx = 10.0  # [m]
    # sy = 10.0  # [m]
    # gx = 50.0  # [m]
    # gy = 50.0  # [m]
    # grid_size = 1.0  # [m]
    # robot_size = 1.0  # [m]
    #
    # ox, oy = [], []
    #
    # for i in range(60):
    #     ox.append(i)
    #     oy.append(0.0)
    # for i in range(60):
    #     ox.append(60.0)
    #     oy.append(i)
    # for i in range(61):
    #     ox.append(i)
    #     oy.append(60.0)
    # for i in range(61):
    #     ox.append(0.0)
    #     oy.append(i)
    # for i in range(40):
    #     ox.append(20.0)
    #     oy.append(i)
    # for i in range(40):
    #     ox.append(40.0)
    #     oy.append(60.0 - i)
    #
    # if show_animation:
    #     plt.plot(ox, oy, ".k")
    #     plt.plot(sx, sy, "xr")
    #     plt.plot(gx, gy, "xb")
    #     plt.grid(True)
    #     plt.axis("equal")
    #
    # rx, ry = a_star_planning(sx, sy, gx, gy, ox, oy, grid_size, robot_size)
    #
    if show_animation:
        plt.plot(rx, ry, "-r")
        plt.show()


if __name__ == '__main__':
    main()