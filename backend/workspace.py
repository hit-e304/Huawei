import sys
import numpy as np
import time
import math
from numba import jit


carPerSec = 25
intervalTime = 1
carInMap = 1000
delta1 = 75
delta2 = 10


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


TIME = [0]
CARDISTRIBUTION = [0,0,0]
CARNAMESPACE,ROADNAMESPACE,CROSSNAMESPACE = [],[],[]  # save Id of each kind
CROSSDICT,CARDICT,ROADDICT,CARREADYDICT ={},{},{},{}  # save Object of each kind
ROUTEMAP ={}
ROADCROSSDICT = {} # {crossId: {crossId: roadId}}


class Car():
    def __init__(self, carInfLine_):
        #### input parameters ####
        self.id_, self.startId_, self.endId_, self.speed_, self.startTime_ = carInfLine_
        #### simulate parameters ####
        # car state: 0,1,2,3 in carport,waiting,finishing,end
        self.presentRoad, self.nextCrossId = None, self.startId_
        self.state, self.x, self.y = 0, 0, 0
        self.moveX, self.moveY = 0, 0
        self.leftX = 0
        self.isWaiting = False
        self.route, self.routeIndex, self.startTime = None, None, None
    
    def simulateInit(self, planTime, route):
        self.startTime, self.route, self.routeIndex = planTime, route, 0

    # def updatePlan(self, planLine):
    #     # car in carport or waiting, change it's start road and replan
    #     # TODO: may cause bug if car is waiting !!!
    #     if self.state == 0:
    #         self.startTime, self.route = planLine[1], planLine[2:]
    #     elif self.state in [1, 2]:
    #         cur_routeIndex = self.routeIndex
    #         cur_road = self.route[cur_routeIndex]
    #         self.startTime = planLine[1]
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
        '''
        Usage: find cars in each side of road
        '''
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
                    # TODO: update current car; BUG: may cause bug

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

    # def findNeighbor(self):
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


def infInit(crossPath, roadPath, carPath):
    crossInf = readInf(crossPath)
    roadInf = readInf(roadPath)
    carInf = readInf(carPath)

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

    #### Update 2019.4.1 ####
    for crossId in CROSSNAMESPACE:
        ROADCROSSDICT[line[0]] = {} 
    for roadId in ROADNAMESPACE:
        road = ROADDICT[roadId]
        ROADCROSSDICT[road.__getPar__('startId')][road.__getPar__('endId')] = road.__getPar__('id')
        if road.__getPar__('isDuplex'):
            ROADCROSSDICT[road.__getPar__('endId')][road.__getPar__('startId')] = road.__getPar__('id')

    return crossInf, roadInf, carInf


def simulateStep():
    """
    Usage: Step simulation, including: initial Cross, initial Road, update Cross(Road), input new Cars
    """

    for crossId in CROSSNAMESPACE:
        CROSSDICT[crossId].setDone(False)
    for road in ROADNAMESPACE:
        ROADDICT[road].stepInit()
    unfinishedCross = CROSSNAMESPACE
    # update current in-map Cars
    # BUG:只更新路口，而不更新道路，若把路口和道路分别搜索？？？
    while unfinishedCross.__len__() > 0:
        deadSign = True
        nextCross = []
        for crossId in unfinishedCross:
            cross = CROSSDICT[crossId]
            cross.step()
            if not cross.__getPar__('done'):
                nextCross.append(crossId)
            if cross.__getPar__('update') or cross.__getPar__('done'):
                    deadSign = False
        unfinishedCross = nextCross
        if deadSign:
            print('dead lock in', unfinishedCross)
            return deadSign
    for i in range(CROSSNAMESPACE.__len__()):
        crossId = CROSSNAMESPACE[i]
        for roadId in CROSSDICT[crossId].__getPar__('validRoad'):
            ROADDICT[roadId].setBucket(crossId)
        CROSSDICT[crossId].outOfCarport()
    
    return deadSign


def speed_split(carInf):
    max_speed = 0
    carDivideSpeed = []

    # split car by speed, carDivideSpeed[k] means car speed as k+1
    for i in carInf:
        if i[3] > max_speed:
            max_speed = i[3]
    for i in range(max_speed):
        carDivideSpeed.append([])
    for i in carInf:
        carDivideSpeed[i[3] - 1].append(i[0])
 
    output_dic = {}
    for i in range(max_speed):
        output_dic[i+1] = carDivideSpeed[i]
    return output_dic


def timeSplit(group, carInf, carPerSec, time, intervalTime, speed, carIdBias, carPosition):

    curBatch = []
    groupDivideTime = []
    group_len = len(group)

    if speed in [1, 2]:
        carPerBatch = carPerSec * intervalTime
    elif speed in [3, 4]:
        carPerBatch = int(carPerSec * intervalTime * 1.1)
    elif speed in [5, 6]:
        carPerBatch = int(carPerSec * intervalTime * 1.1)
    else:
        carPerBatch = int(carPerSec * intervalTime * 1.1) 

    batch_num = int(group_len / carPerBatch) + 1
    # for i in group:
    #     group_position.append(carPosition[i])

    for i in range(batch_num):
        curBatch = []
        for j in range(carPerBatch):
            try: 
                curBatch.append(group.pop())
            except:
                break
        groupDivideTime.append(curBatch)
    
    return groupDivideTime


def dijkstraMinpath(start, end, matrix):
    inf = 10000
    length = len(matrix)
    pathArray = []
    tempArray = []
    pathArray.extend(matrix[start])
    tempArray.extend(matrix[start])
    tempArray[start] = inf
    already_traversal = [start]
    path_parent = [start] * length

    i = start
    while(i != end):
        i = tempArray.index(min(tempArray))
        tempArray[i] = inf
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
                if (pathArray[i] + matrix[i][j]) < pathArray[j]:
                    pathArray[j] = tempArray[j] = pathArray[i] + matrix[i][j]
                    path_parent[j] = i
    return path


# def calc_heuristic(n1, n2, crossMap=crossMap):
#     n1X, n1Y = crossMap[n1]
#     n2X, n2Y = crossMap[n2]
#     return (abs(n1X - n2X) + abs(n1Y - n2Y))


# def a_star(startId, endId, crossMap):
#     openSet, closeSet = [], []
#     openSet.append(startId)
#     comeFrom = {}
#     gScore, fScore = {}
#     gScore[startId], fScore[startId] = 0, calc_heuristic(startId, endId)
#     path = []

#     while openSet is not empty:
#         curCrossId = min(fScore, key=fScore.get) # find the cross with smallest fScore
#         if curCrossId == endId:
#             return path
#         # put curCrossId into closeSet
#         openSet.remove(curCrossId)
#         closeSet.append(curCrossId)

        # TODO: Find neighbor of curCrossId in class Cross
        # for neighbor in 


def cal_car_path(mapLossArray, mapRoadArray, carInf, batch, roadBias, roadInf, speed, time):

    path = []
    path_road_time = []
    
    for i in batch:
        car = CARDICT[i]
        path = dijkstraMinpath(car.__getPar__('startId')-1, car.__getPar__('endId')-1, mapLossArray)
        path_center = []
        a = len(path)
    
        path_center.append(car.__getPar__('id'))
        path_center.append(max(car.__getPar__('startTime'), time))
        for j in range(a-1):
            path_center.append(int(mapRoadArray[path[j]][path[j+1]]))
        path_road_time.append(path_center)

        runTime = 0
        for i in path_center[2:]:
            runTime += roadInf[i-roadBias][1] / min(speed, roadInf[i-roadBias][2])

    return path_road_time


def updateLoss(arrayLoss, arrayDis, roadInf, roadUseDic, roadIdBias, speed, crossLoss):

    for i in roadInf:
        id_, length, channel, speedLim, startId, endId, isDux = i
        startId -= 1
        endId -= 1
        forward_use = roadUseDic[id_][0]
        backward_use = roadUseDic[id_][1]
        # loss = length * (1 + 2 / channel / channel) - 0.5 * min(speedLim, speed) + 20
        # arrayLoss[startId][endId] = length * (1 / min(speedLim, speed) + 100 * forward_use) + 200 * crossLoss[startId][endId]
        arrayLoss[startId][endId] = length * 1 / min(speedLim, speed) + delta1 * forward_use + delta2 * crossLoss[startId][endId]  * crossLoss[startId][endId]

        if isDux == 1:
            # arrayDis[endId][startId] = length * (1 / min(speedLim, speed) + 100 * backward_use) + 200 * crossLoss[startId][endId]
            arrayLoss[endId][startId] = length * 1 / min(speedLim, speed) + delta1 * backward_use + delta2 * crossLoss[endId][startId] * crossLoss[endId][startId]
        else:
            arrayLoss[endId][startId] = 10000
    
    return arrayLoss


def update_car(finalTime, time):
    newFinalTime = []
    for i in finalTime:
        if i > time:
            newFinalTime.append(i)
    
    return newFinalTime


def carSortTime(curGroup, speed, carInf, roadInf, mapDisArray, mapRoadArray, carIdBias, roadIdBias):
    path = []
    carTime = []
    returnCarTime = []

    for car in curGroup:
        carId = car - carIdBias
        path = dijkstraMinpath(carInf[carId][1]-1, carInf[carId][2]-1, mapDisArray)
        path_center = []
        a = len(path)
    
        for j in range(a-1):
            path_center.append(int(mapRoadArray[path[j]][path[j+1]]))

        runTime = 0
        for i in path_center[2:]:
            runTime += roadInf[i-roadIdBias][1] / min(speed, roadInf[i-roadIdBias][2])
        
        carTime.append([car, runTime])
    
    carTime = sorted(carTime, key=(lambda x:x[1]), reverse=True)
    a = len(carTime)
    for i in range(a):
        returnCarTime.append(carTime[i][0])

    return returnCarTime


def calCrossLoss(crossInf, roadInf, mapRoadArray, speed):
    roadFlow = {}
    a = len(crossInf)
    mapCrossLoss = np.zeros([a, a])
    for road in roadInf:
        roadFlow[road[0]] = road[3] * min(speed, road[2])
    
    for i in range(a):
        for j in range(a):
            if mapRoadArray[i][j] not in [10000, 0]:
                cross = crossInf[i]
                roadId = int(mapRoadArray[i][j])
                dirOut = cross.index(roadId)

                dirc = [1, 2, 3, 4]
                for k in [1, 2, 3, 4]:
                    if cross[k] == -1:
                        dirc.remove(k)
                numAvail = len(dirc) - 1
                inFlow = 0
                for m in dirc:
                    if m == dirOut:
                        continue
                    inFlow += roadFlow[cross[m]]

                loss = max((inFlow / numAvail - roadFlow[cross[dirOut]]), 0) / roadFlow[cross[dirOut]] / roadFlow[cross[dirOut]]

                mapCrossLoss[i][j] = loss
    return mapCrossLoss


def getRoadCrowd(roadUseDic):
    for roadId in ROADNAMESPACE:
        road = ROADDICT[roadId]
        fcong, bcong = road.calcongestion()
        roadUseDic[roadId] = [fcong, bcong]
    return roadUseDic 


def car_plan(pathTimeInf):
    readyDic = {}
    for line in pathTimeInf:
        carId = int(line[0])
        planTime_ = int(line[1])
        route = [int(roadId) for roadId in line[2:]]
        CARDICT[carId].simulateInit(planTime_,route)
        readyDic[carId] = CARDICT[carId]
    return readyDic


def createCrossMap(crossInf, roadInf, roadIdBias):
    '''
    Usage: Create cross map in xoy sys
    Input: crossInf / roadInf:list[int]  roadIdBias:int
    output: mapDic:dict{[int]}  mapLim:list[int]
    '''
    crossLen = 1
    initX, initY = 0, 0
    maxX, maxY = 0, 0
    minX, minY =0, 0
    mapDic = {crossInf[0][0]:[initX, initY]}
    finishCross = [crossInf[0][0]]
    crossNum = len(crossInf)
    while len(finishCross) < crossNum:
        reverseList = reversed(finishCross)
        for cross in reverseList:
            crossId, roadLine = crossInf[cross-1][0], crossInf[cross-1][1:] 
            curX, curY = mapDic[crossId] # curX, curY: Int
            for i, road in enumerate(roadLine):
                if road != -1:
                    roadInf = roadInf[road-roadIdBias]
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
    mapLim = [maxX, minX, maxY, minY]
    return mapDic, mapLim


def printCrossLoss(roadInf, crossLoss, lossPath):
    '''
    Usage: Print loss of each cross into text
    '''
    crossLossOutput = []
    for line in roadInf:
        crossLossOutput.append([line[0], crossLoss[line[4]-1][line[5]-1], crossLoss[line[5]-1][line[4]-1]])
    with open(lossPath, 'w') as fp:
        fp.write('\n'.join(str(tuple(x)) for x in crossLossOutput)) 


def main():

    car_path = sys.argv[1]
    road_path = sys.argv[2]
    crossPath = sys.argv[3]
    answer_path = sys.argv[4]

    crossInf, roadInf, carInf = infInit(crossPath, road_path, car_path)
    # _, mapDisArray, mapRoadArray, mapLossArray, _, _ = mapGraph(crossInf, roadInf)
    carDivideSpeed = speed_split(carInf)

    time0, carIdBias, roadIdBias = 1, carInf[0][0], roadInf[0][0]
    carPosition = {}
    answer, speed_list = [], []
    roadUseDic = {}
    crossMap = createCrossMap(crossInf, roadInf, roadIdBias)

    # 1. divide by speed
    # 2. calculate time by position (TODO)
    # 3. loop: calculate path ; record road ; update map (TODO)
    for speed in carDivideSpeed:
        speed_list.append(speed)
    speed_list.reverse()

    for speed in speed_list:
        curGroup = carDivideSpeed[speed]
        if not curGroup:
            continue

        crossLoss = calCrossLoss(crossInf, roadInf, mapRoadArray, speed)

        speedGroup = carSortTime(curGroup, speed, carInf, roadInf, mapDisArray, mapRoadArray, carIdBias, roadIdBias)
        groupDivideTime = timeSplit(speedGroup, carInf, carPerSec, time0, intervalTime, speed, carIdBias, carPosition)
        
        for batch in groupDivideTime:
            # print(CARDISTRIBUTION)
            batch_len = len(batch)
            while (CARDISTRIBUTION[1] > (carInMap - batch_len)):
                simulateStep()
                time0 += 1
                TIME[0] += 1
            roadUseDic = getRoadCrowd(roadUseDic)
            mapLossArray = updateLoss(mapLossArray, mapDisArray, roadInf, roadUseDic, roadIdBias, speed, crossLoss)
            batchPathTime = cal_car_path(mapLossArray, mapRoadArray, carInf, batch, roadIdBias, roadInf, speed, time0)
            CARREADYDICT = car_plan(batchPathTime)
            for carId in CARREADYDICT:
                CROSSDICT[CARDICT[carId].__getPar__('startId')].carportInitial(CARDICT[carId].__getPar__('startTime'), carId)
            dead_flag = simulateStep()
            if dead_flag:
                break
            time0 += 1
            TIME[0] += 1
            answer += batchPathTime
        
        if dead_flag:
            break

    with open(answer_path, 'w') as fp:
        fp.write('\n'.join(str(tuple(x)) for x in answer))


if __name__ == "__main__":
    main()
