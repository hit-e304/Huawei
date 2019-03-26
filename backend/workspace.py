import sys
import numpy as np
import time


car_per_sec = 25
interval_time = 1
car_in_map = 1000
delta1 = 75
delta2 = 10


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


TIME = [0]
CARDISTRIBUTION = [0,0,0]
CARNAMESPACE,ROADNAMESPACE,CROSSNAMESPACE = [],[],[]
CROSSDICT,CARDICT,ROADDICT,CARREADYDICT ={},{},{},{}
ROUTEMAP ={}


class Car():
    def __init__(self, carInfLine_):
        #### input parameters ####
        self.id_, self.startId_, self.endId_, self.speed_, self.startTime_ = carInfLine_
        #### simulate parameters ####
        # car state: 0,1,2,3 in carport,waiting,finishing,end
        self.presentRoad, self.nextCrossId = None, self.startId_
        self.state, self.x, self.y = 0, 0, 0
        self.moveX, self.moveY = 0, 0
        self.isWaiting = False
        self.route, self.routeIndex, self.start_time = None, None, None
    
    def simulateInit(self, planTime, route):
        self.startTime_, self.route, self.routeIndex = planTime, route, 0

    # def updatePlan(self, planLine):
    #     # car in carport or waiting, change it's start road and replan
    #     # TODO: may cause bug if car is waiting !!!
    #     if self.state == 0:
    #         self.start_time, self.route = planLine[1], planLine[2:]
    #     elif self.state in [1, 2]:
    #         cur_routeIndex = self.routeIndex
    #         cur_road = self.route[cur_routeIndex]
    #         self.start_time = planLine[1]
    #         self.route = planLine[2:]
    #         self.routeIndex = self.route.index(cur_road)
    
    def updateParameter(self, state, x=None, y=None, presentRoad=None, roadSpeed=None, nextCrossId=None):
        if self.state != 0 or presentRoad is not None:
            self.state = state
        if presentRoad is not None and self.state != 0 and self.routeIndex < self.route.__len__():
            self.routeIndex += 1
        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y
        self.presentRoad = presentRoad if presentRoad is not None else self.presentRoad
        if nextCrossId is not None:
            self.nextCrossId = nextCrossId
            toX, toY = CROSSDICT[self.endId_].__getPar__('loc')
            nextCrossX, nextCrossY = CROSSDICT[nextCrossId].__getPar__('loc')
            self.deltaX, self.deltaY = toX - nextCrossX, toY - nextCrossY

    def __getPar__(self, parName):
        if parName == 'id':
            return self.id_
        elif parName == 'startId':
            return self.startId_
        elif parName == 'endId':
            return self.endId_
        elif parName == 'speed':
            return self.speed_
        elif parName == 'startTime':
            return self.startTime_
        elif parName == 'state':
            return self.state
        elif parName == 'x':
            return self.x
        elif parName == 'y':
            return self.y
        elif parName == 'presentRoad':
            return self.nextCrossId
        elif parName == 'nextCrossId':
            return self.nextCrossId
        elif parName == 'deltaX':
            return self.deltaX
        elif parName == 'deltaY':
            return self.deltaY
        elif parName == 'isWaiting':
            return self.isWaiting
        elif parName == 'route':
            return self.route
        elif parName == 'routeIndex':
            return self.routeIndex
        elif parName == 'v':
            return min(self.speed_, ROADDICT[self.presentRoad].__getPar__('speed'))
        elif parName == 'distance':
            return abs(self.deltaX) + abs(self.deltaY)
        elif parName == 'nextRoad':
            try:
                return self.route[self.routeIndex]
            except:
                return -1
        else:
            print('Wrong key name !!!')


class Road():
    def __init__(self, roadInfLine_):
        #### input parameters ####
        self.id_, self.length_, self.speed_, self.channel_, self.startId_, self.endId_, self.isDuplex_ = roadInfLine_
        self.roadFlow = self.channel_ * self.length_
        #### simulate parameters ####
        self.forwardTube = {i: [None for j in range(self.channel_)] for i in range(self.length_)}
        if self.isDuplex_:
            self.backwardTube = {i: [None for j in range(self.channel_)] for i in range(self.length_)}
        else:
            self.backwardTube = None
        # BUG: delete some pars
        # self.provideTube, self.receiveTube = None, None
        # self.px, self.py, self.provideNum, self.receiveNum = None, None, None, None
        # self.provideDone = None
        self.fx, self.fy, self.bx, self.by, self.forwardNum, self.backwardNum = 0, 0, 0, 0, 0, 0
        self.forwardDone, self.backwardDone = [False], [False]
        # relative bucket
        self.provideTube, self.receiveTube = None, None
        self.px, self.py, self.provideNum, self.receiveNum = None, None, None, None
        self.provideDone = None

    def calcongestion(self):
        forwardCarNum, backwardCarNum = 0, 0
        for i in range(self.length_):
            for j in range(self.channel_):
                if self.forwardTube[i][j] is not None:
                    forwardCarNum += 1
        fcongestion = forwardCarNum / self.roadFlow

        if self.isDuplex_:
            for i in range(self.length_):
                for j in range(self.channel_):
                   if self.backwardTube[i][j] is not None:
                        backwardCarNum += 1
            bcongestion = backwardCarNum / self.roadFlow
        else:
            bcongestion = None
        return fcongestion, bcongestion
    
    def chooseDirection(self, crossId):
        if crossId == self.startId_:
            return 'backward'
        elif crossId == self.endId_:
            return 'forward'
        else:
            print('wrong crossID in chooseDirection')
    # BUG: May cause bug
    # def setBucket(self, crossId):
    #     direction = self.chooseDirection(crossId)
    #     if direction == 'forward':
    #         self.provideTube, self.px, self.py = self.forwardTube, 0, 0
    #         if self.isDuplex_:
    #             self.receiveTube, self.provideNum, self.receiveNum = self.backwardTube, 0, 0
    #         else:
    #             self.receiveTube, self.receiveNum = None, None
    #     else:
    #         self.receiveTube, self.receiveNum = self.forwardTube, 0
    #         if self.isDuplex_:
    #             self.provideTube, self.px, self.py = self.backwardTube, 0, 0
    #         else:
    #             self.provideTube, self.px, self.py = None, None, None
    def setBucket(self,crossId):
        bucket = self.chooseDirection(crossId)
        if bucket == 'forward':
            self.provideTube, self.px, self.py, self.provideDone, self.provideNum = \
                [self.forwardTube, self.fx, self.fy, self.forwardDone, self.forwardNum]
            if self.isDuplex_:
                self.receiveTube, self.receiveNum = \
                    self.backwardTube, self.backwardNum
            else:
                self.receiveTube, self.receiveNum = None, None
        else:
            self.receiveTube, self.receiveNum = \
                self.forwardTube, self.forwardNum
            if self.isDuplex_:
                self.provideTube, self.px, self.py, self.provideDone, self.provideNum = \
                    self.backwardTube, self.bx, self.by, self.backwardDone, self.backwardNum
            else:
                self.provideTube, self.px, self.py, self.provideDone, self.provideNum = \
                    None, None, None, None, None


    def stepInit(self):
        self.fx, self.fy, self.bx, self.by = 0, 0, 0, 0
        self.forwardDone, self.backwardDone = False, False
        self.provideTube, self.receiveTube = None, None
        self.px, self.py, self.provideNum, self.receiveNum  = None, None, None, None
        self.provideDone = None

        for i in range(self.length_):
            for j in range(self.channel_):
                if self.forwardTube[i][j] is not None:
                    car = CARDICT[self.forwardTube[i][j]]
                    car.updateParameter(state=1)
                if self.isDuplex_:
                    if self.backwardTube[i][j] is not None:
                        car = CARDICT[self.backwardTube[i][j]]
                        car.updateParameter(state=1)
        # first step
        for channel in range(self.channel_):
            self.updateChannel(self.forwardTube, channel)
            if self.isDuplex_:
                self.updateChannel(self.backwardTube, channel)
    
    def updateChannel(self, tube, channel):
        previousCar, previousState = -1, 1
        for i in range(self.length_):
            if tube[i][channel] is not None:
                car = CARDICT[tube[i][channel]]
                v = car.__getPar__('v')
                if car.__getPar__('state') == 2:
                    previousCar, previousState = i, 2
                    continue
                elif i - v > previousCar:
                    tube[i-v][channel] = tube[i][channel]
                    tube[i][channel] = None
                    previousCar, previousState = i - v, 2
                    car.updateParameter(state=2, x=previousCar) 
                elif previousState == 2:
                    if previousCar + 1 != i:
                        tube[previousCar + 1][channel] = tube[i][channel]
                        tube[i][channel] = None
                    previousCar, previousState = previousCar + 1, 2
                    car.updateParameter(state=2, x=previousCar)
                else:
                    previousCar, previousState = i, 1
    
    def searchCar(self, start, end, channel, tube):
        for i in range(end, start, -1):
            if tube[i][channel] is not None:
                return i
        return -1
    
    def firstPriorityCar(self):
        while True:
            if self.px == self.length_:
                break
            carId = self.provideTube[self.px][self.py]
            if carId is not None and CARDICT[carId].__getPar__('state') != 2:
                car = CARDICT[carId]
                left = car.__getPar__('v')
                if left > self.px and self.searchCar(-1, self.px-1, self.py, self.provideTube) == -1:
                    return self.provideTube[self.px][self.py]
            if self.py == self.channel_ - 1:
                self.px, self.py = self.px + 1, 0
            else:
                self.py += 1
        self.provideDone = True
        return -1
    
    def firstPriorityCarAct(self, action):
        if action == 0:
            self.provideTube[self.px][self.py] = None
            self.provideNum -= 1
        elif action == 1:
            carId = self.provideTube[self.px][self.py]
            self.provideTube[self.px][self.py] = None
            self.provideTube[0][self.py] = carId
        self.updateChannel(self.provideTube, self.py)
    
    # return: 1 means car's leftX = 0; 2 means wait for previous car moving;
    #         3 means next cross has no place; 
    def receiveCar(self, carId):
        car = CARDICT[carId]
        leftX = max(min(self.speed_, car.__getPar__('speed')) - car.__getPar__('x'), 0)
        if car.__getPar__('nextCrossId') != self.startId_:
            nextCrossId = self.startId_
        else:
            nextCrossId = self.endId_
        if leftX == 0:
            car.updateParameter(state=2, x=0)
            return 1
        for i in range(self.channel_):
            previousCarPos = self.searchCar(self.length_ - leftX - 1, self.length_ - 1, i, self.receiveTube)

            if previousCarPos == -1:
                self.receiveTube[self.length_ - leftX][i] = carId
                self.receiveNum += 1
                car.updateParameter(state=2, x=self.length_-leftX, y=i, presentRoad=self.id_,
                                    roadSpeed=self.speed_, nextCrossId=nextCrossId)
                return 0
            previousCar = CARDICT[self.receiveTube[previousCarPos][i]]
            if previousCar.__getPar__('state') == 1:
                return 2
            elif previousCarPos != self.length_ - 1:
                self.receiveTube[previousCarPos + 1][i] = carId
                self.receiveNum += 1
                car.updateParameter(state=2, x=previousCarPos+1, y=i, presentRoad=self.id_,
                                    roadSpeed=self.speed_, nextCrossId=nextCrossId)
                return 0
            else:
                continue
        car.updateParameter(state=2, x=0)
        # BUG: add 3 to 1 when using
        return 1

    def __getPar__(self, parName):
        if parName == 'id':
            return self.id_
        elif parName == 'length':
            return self.length_
        elif parName == 'speed':
            return self.speed_
        elif parName == 'channel':
            return self.channel_
        elif parName == 'startId':
            return self.startId_
        elif parName == 'endId':
            return self.endId_
        elif parName == 'isDuplex':
            return self.isDuplex_
        elif parName == 'roadFlow':
            return self.roadFlow
        elif parName == 'forwardTube':
            return self.forwardTube
        elif parName == 'backwardTube':
            return self.backwardTube
        elif parName == 'provideTube':
            return self.provideTube
        elif parName ==  'receiveTube':
            return self.receiveTube


class Cross():
    def __init__(self, crossInfLine):
        self.id_, self.roadIds = crossInfLine[0], crossInfLine[1:]
        self.carport = {}
        self.left = []
        self.priorityMap = {self.roadIds[0]: {self.roadIds[1]: 0, self.roadIds[2]: 2, self.roadIds[3]: 1}, 
                            self.roadIds[1]: {self.roadIds[2]: 0, self.roadIds[3]: 2, self.roadIds[0]: 1}, 
                            self.roadIds[2]: {self.roadIds[3]: 0, self.roadIds[0]: 2, self.roadIds[1]: 1}, 
                            self.roadIds[3]: {self.roadIds[0]: 0, self.roadIds[1]: 2, self.roadIds[2]: 1}}
        self.providerIndex, self.receiverIndex, self.validRoadIndex = [], [], []
        for index, roadId in enumerate(self.roadIds):
            road = ROADDICT[roadId] if roadId != -1 else None
            if road is not None and (road.__getPar__('isDuplex') or road.__getPar__('endId') == self.id_):
                self.providerIndex.append(index)
            if road is not None and (road.__getPar__('isDuplex') or road.__getPar__('startId') == self.id_):
                self.receiverIndex.append(index)
            if road is not None:
                self.validRoadIndex.append(index)
        self.provider = [self.roadIds[index] for index in self.providerIndex]
        self.receiver = [self.roadIds[index] for index in self.receiverIndex]
        self.validRoad = [self.roadIds[index] for index in self.validRoadIndex]
        self.provider.sort() # [5001 , 5002, 5007, 5008]
        # **** dynamic parameters ****#
        self.readyCars = []
        self.carportCarNum = 0
        self.finishCarNum = 0
        self.x, self.y = 0, 0
        # **** flag ****#
        self.done = False
        self.update = False

    def step(self):
        self.update = False
        for roadId in self.validRoad:
            ROADDICT[roadId].setBucket(self.id_)
        firstCarId, firstCar, nextRoad, nextCarPriority = [], [], [], []
        for provideIndex in range(self.provider.__len__()): # provideIndex [0, 1, 2, 3]
            # print(self.validRoad)
            firstCarId.append(ROADDICT[self.provider[provideIndex]].firstPriorityCar()) # [fisrt car in 5001, fisrt car in 5002 ....]
            # if first priority car exists
            if firstCarId[provideIndex]!=-1:
                firstCar.append(CARDICT[firstCarId[provideIndex]]) # [Car..., Car..., Car..., ]
                nextRoad.append(firstCar[provideIndex].__getPar__('nextRoad')) # [5007, 5007, 5008, 5001]
                # nextRoad == -1 => terminal
                if nextRoad[provideIndex] == -1:
                    nextCarPriority.append(2)
                else:
                    nextCarPriority.append(self.prority(self.provider[provideIndex], nextRoad[provideIndex]))
            else:
                firstCar.append(-1)
                nextRoad.append(-1)
                nextCarPriority.append(-1)
                # get priority [1, 1, 0, 2]
        # loop
        for provideIndex in range(self.provider.__len__()):
            while firstCar[provideIndex]!=-1:
                # same next road and high priority lead to conflict
                provider = ROADDICT[self.provider[provideIndex]]
                for i in range(self.provider.__len__()):
                    # if conflict(same direction and low priority)
                    if nextRoad[i]==nextRoad[provideIndex] and nextCarPriority[i]>nextCarPriority[provideIndex]:
                        break
                
                if nextRoad[provideIndex] == -1:
                    provider.firstPriorityCarAct(0)
                    self.update = True
                    CARDISTRIBUTION[1]-=1
                    CARDISTRIBUTION[2]+=1
                else:
                    nextroad_ = ROADDICT[nextRoad[provideIndex]]
                    action = nextroad_.receiveCar(firstCar[provideIndex].__getPar__('id'))
                    if action == 2:
                        break
                    provider.firstPriorityCarAct(action)
                    self.update = True
                firstCarId[provideIndex] = provider.firstPriorityCar()
                if firstCarId[provideIndex] != -1:
                    firstCar[provideIndex] = CARDICT[firstCarId[provideIndex]]
                    nextRoad[provideIndex] = firstCar[provideIndex].__getPar__('nextRoad')
                    # nextRoad == -1 => terminal
                    if nextRoad[provideIndex] == -1:
                        nextCarPriority[provideIndex] = 2
                    else:
                        nextCarPriority[provideIndex]= self.prority(self.provider[provideIndex], nextRoad[provideIndex])
                else:
                    firstCar[provideIndex] = -1
                    nextRoad[provideIndex]= -1
                    nextCarPriority[provideIndex] = -1
        done = True
        for provideIndex in range(self.provider.__len__()):
            if firstCar[provideIndex] != -1:
                done = False
        self.done = done

    def outOfCarport(self):
        self.readyCars = self.left
        self.left=[]
        if TIME[0] in self.carport.keys():
            self.carport[TIME[0]].sort()
            self.readyCars.extend(self.carport[TIME[0]])
        if self.readyCars.__len__() == 0:
            return
        #self.readyCars.sort()
        for roadId in self.receiver:
            ROADDICT[roadId].setBucket(self.id_)
        for i in range(self.readyCars.__len__()):
            carId = self.readyCars[i]
            roadId = CARDICT[carId].__getPar__('nextRoad')
            road = ROADDICT[roadId]
            if roadId not in self.receiver:
                print("Car(%d).Road(%d) not in cross(%d).function:class.outOfCarport"%(carId,roadId,self.id_))
            act = road.receiveCar(carId)
            if act!= 0:
                self.left.append(self.readyCars[i])
            else:
                self.carportCarNum -= 1
                CARDISTRIBUTION[0] -= 1
                CARDISTRIBUTION[1] += 1
    
    def prority(self,providerId,receiverId):
        return self.priorityMap[providerId][receiverId]
    def setDone(self,bool):
        self.done = bool
    def setLoc(self,x,y):
        self.x,self.y = x,y
    def setMapLoc(self,mapX,mapY):
        self.mapX,self.mapY = mapX,mapY
    def roadDirection(self,roadId):
        if self.roadIds[0]==roadId:
            return 0
        elif self.roadIds[1]==roadId:
            return 1
        elif self.roadIds[2]==roadId:
            return 2
        elif self.roadIds[3]==roadId:
            return 3
        else:
            return -1
    def carportInitial(self, timePlan, carId):
        if timePlan not in self.carport.keys():
            self.carport[timePlan] = [carId]
        else:
            self.carport[timePlan].append(carId)
        self.carportCarNum += 1
    
    def __getPar__(self, parName):
        if parName == 'id':
            return self.id_
        if parName == 'validRoad':
            return self.validRoad
        if parName == 'x':
            return self.x
        if parName == 'y':
            return self.y
        if parName == 'done':
            return self.done
        if parName == 'update':
            return self.update
        if parName == 'loc':
            return self.x, self.y


def simulateStep():

    for crossId in CROSSNAMESPACE:
        CROSSDICT[crossId].setDone(False)
    for road in ROADNAMESPACE:
        ROADDICT[road].stepInit()
    unfinishedCross = CROSSNAMESPACE
    # update current in-map Cars
    while unfinishedCross.__len__() > 0:
        dead_sign = True
        nextCross = []
        for crossId in unfinishedCross:
            cross = CROSSDICT[crossId]
            cross.step()
            if not cross.__getPar__('done'):
                nextCross.append(crossId)
            if cross.__getPar__('update') or cross.__getPar__('done'):
                    dead_sign = False
        unfinishedCross = nextCross
        if dead_sign:
            print('dead lock in', unfinishedCross)
            return dead_sign
    for i in range(CROSSNAMESPACE.__len__()):
        crossId = CROSSNAMESPACE[i]
        for roadId in CROSSDICT[crossId].__getPar__('validRoad'):
            ROADDICT[roadId].setBucket(crossId)
        CROSSDICT[crossId].outOfCarport()
    
    return dead_sign


def map_graph(cross, road):
    """
    input: cross, cross_inf; road, road_inf
    """
    a = len(cross)
    graph = {}
    array_dis = np.zeros([a, a]) + 999999 - 999999 * np.eye(a)
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


def time_split(group, car_inf, car_per_sec, time, interval_time, speed, car_id_bias, car_position):

    cur_batch = []
    group_divide_time = []
    group_len = len(group)

    if speed in [1, 2]:
        car_per_batch = car_per_sec * interval_time
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


def cal_car_path(map_loss_array, map_road_array, car_inf, batch, road_bias, road_inf, speed, time):

    path = []
    path_road_time = []
    
    for i in batch:
        car = CARDICT[i]
        path = dijkstra_minpath(car.__getPar__('startId')-1, car.__getPar__('endId')-1, map_loss_array)
        path_center = []
        a = len(path)
    
        path_center.append(car.__getPar__('id'))
        path_center.append(max(car.__getPar__('startTime'), time))
        for j in range(a-1):
            path_center.append(int(map_road_array[path[j]][path[j+1]]))
        path_road_time.append(path_center)

        run_time = 0
        for i in path_center[2:]:
            run_time += road_inf[i-road_bias][1] / min(speed, road_inf[i-road_bias][2])

    return path_road_time


def update_loss(array_loss, array_dis, road_inf, road_use_dic, road_id_bias, speed, cross_loss):

    for i in road_inf:
        id_, length, channel, speed_lim, start_id, end_id, is_dux = i
        start_id -= 1
        end_id -= 1
        forward_use = road_use_dic[id_][0]
        backward_use = road_use_dic[id_][1]
        # loss = length * (1 + 2 / channel / channel) - 0.5 * min(speed_lim, speed) + 20
        # array_loss[start_id][end_id] = length * (1 / min(speed_lim, speed) + 100 * forward_use) + 200 * cross_loss[start_id][end_id]
        array_loss[start_id][end_id] = length * 1 / min(speed_lim, speed) + delta1 * forward_use + delta2 * cross_loss[start_id][end_id]  * cross_loss[start_id][end_id]

        if is_dux == 1:
            # array_dis[end_id][start_id] = length * (1 / min(speed_lim, speed) + 100 * backward_use) + 200 * cross_loss[start_id][end_id]
            array_loss[end_id][start_id] = length * 1 / min(speed_lim, speed) + delta1 * backward_use + delta2 * cross_loss[end_id][start_id] * cross_loss[end_id][start_id]
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


def cal_cross_loss(cross_inf, road_inf, map_road_array, speed):
    road_flow = {}
    a = len(cross_inf)
    map_cross_loss = np.zeros([a, a])
    for road in road_inf:
        road_flow[road[0]] = road[3] * min(speed, road[2])
    
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

                loss = max((in_flow / num_avail - road_flow[cross[dir_out]]), 0) / road_flow[cross[dir_out]] / road_flow[cross[dir_out]]

                map_cross_loss[i][j] = loss
    return map_cross_loss


def getRoadCrowd(road_use_dic):
    for roadId in ROADNAMESPACE:
        road = ROADDICT[roadId]
        fcong, bcong = road.calcongestion()
        road_use_dic[roadId] = [fcong, bcong]
    return road_use_dic 


def infInit(crossPath, roadPath, carPath):
    crossInf = read_inf(crossPath)
    roadInf = read_inf(roadPath)
    carInf = read_inf(carPath)

    for line in carInf:
        CARNAMESPACE.append(line[0])
        CARDICT[line[0]] = Car(line)
    for line in roadInf:
        ROADNAMESPACE.append(line[0])
        ROADDICT[line[0]] = Road(line)
    for line in crossInf:
        CROSSNAMESPACE.append(line[0])
        CROSSDICT[line[0]] = Cross(line)

    CARDISTRIBUTION[0] = CARNAMESPACE.__len__()
    CARNAMESPACE.sort()
    CROSSNAMESPACE.sort()

    return crossInf, roadInf, carInf


def carplan(pathTimeInf):
    readyDic = {}
    for line in pathTimeInf:
        carId = int(line[0])
        planTime_ = int(line[1])
        route = [int(roadId) for roadId in line[2:]]
        CARDICT[carId].simulateInit(planTime_,route)
        readyDic[carId] = CARDICT[carId]
    return readyDic

def main():

    car_path = sys.argv[1]
    road_path = sys.argv[2]
    cross_path = sys.argv[3]
    answer_path = sys.argv[4]
    loss_path = 'loss.txt'

    cross_inf, road_inf, car_inf = infInit(cross_path, road_path, car_path)

    _, map_dis_array, map_road_array, map_loss_array, _, _ = map_graph(cross_inf, road_inf)
    car_divide_speed = speed_split(car_inf)

    time0, car_id_bias, road_id_bias = 1, car_inf[0][0], road_inf[0][0]
    car_position = {}
    answer, speed_list = [], []
    roadUseDic = {}

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

        cross_loss = cal_cross_loss(cross_inf, road_inf, map_road_array, speed)
        # cross_loss_output = []
        # for line in road_inf:
        #     cross_loss_output.append([line[0], cross_loss[line[4]-1][line[5]-1], cross_loss[line[5]-1][line[4]-1]])
        # with open(loss_path, 'w') as fp:
        #     fp.write('\n'.join(str(tuple(x)) for x in cross_loss_output)) 
        # print(cross_loss)

        speed_group = car_sort_time(cur_group, speed, car_inf, road_inf, map_dis_array, map_road_array, car_id_bias, road_id_bias)
        group_divide_time = time_split(speed_group, car_inf, car_per_sec, time0, interval_time, speed, car_id_bias, car_position)
        
        for batch in group_divide_time:
            # print(CARDISTRIBUTION)
            batch_len = len(batch)
            while (CARDISTRIBUTION[1] > (car_in_map - batch_len)):
                simulateStep()
                time0 += 1
                TIME[0] += 1
            roadUseDic = getRoadCrowd(roadUseDic)
            map_loss_array = update_loss(map_loss_array, map_dis_array, road_inf, roadUseDic, road_id_bias, speed, cross_loss)
            batch_path_time = cal_car_path(map_loss_array, map_road_array, car_inf, batch, road_id_bias, road_inf, speed, time0)
            CARREADYDICT = carplan(batch_path_time)
            # print(batch_path_time)
            for carId in CARREADYDICT:
                CROSSDICT[CARDICT[carId].__getPar__('startId')].carportInitial(CARDICT[carId].__getPar__('startTime'), carId)
            dead_flag = simulateStep()
            # print(map_loss_array[27][35])
            # print(map_loss_array[28][36])
            # print(map_loss_array[29][37])
            if dead_flag:
                break
            time0 += 1
            TIME[0] += 1
            answer += batch_path_time
        
        if dead_flag:
            break

    with open(answer_path, 'w') as fp:
        fp.write('\n'.join(str(tuple(x)) for x in answer))


if __name__ == "__main__":
    main()
