#%%
import sys
import numpy as np
import time
import math
import cv2 as cv

import heap


carPerSec = 40
intervalTime = 1
carInMap = 2000
delta1 = 75
delta2 = 10

TIME = [0]
CARDISTRIBUTION = [0,0,0]
CARNAMESPACE, PRESETCARNAMESPACE, ROADNAMESPACE,CROSSNAMESPACE = [],[],[], []  # save Id of each kind
CROSSDICT,CARDICT,ROADDICT ={},{},{} # save Object of each kind
ROUTEMAP ={}
CROSSROADDICT, CROSSLOSSDICT, CROSSLENGTHDICT = {}, {}, {} # {crossId: {crossId: roadId}} {crossId: {crossId: loss}}, {startId:{endId: length}}
ROADLOSSDICT, ROADUSEDICT = {}, {} #{crossId: {crossId: loss}}

#%%
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


class Car():
    def __init__(self, carInfLine_):
        #### input parameters ####
        self.id_, self.startId_, self.endId_, self.speed_, self.startTime_, self.priority_, self.preset_ = carInfLine_
        #### simulate parameters ####
        # car state: 0,1,2,3 in carport,waiting,finishing,end
        self.presentRoad, self.nextCrossId = None, self.startId_
        self.state, self.x, self.y = 0, 0, 0
        self.moveX, self.moveY = 0, 0
        self.leftX = 0
        self.isWaiting = False
        self.route, self.routeIndex, self.startTime = None, None, None
        self.carColor = [int(value) for value in np.random.random_integers(0, 255, [3])]
    
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
        # BUG
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
            return self.startTime
        elif parName == 'state':
            return self.state
        elif parName == 'priority':
            return self.priority_
        elif parName == 'x':
            return self.x
        elif parName == 'y':
            return self.y
        elif parName == 'presentRoad':
            return self.presentRoad
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
        elif parName == 'carColor':
            return self.carColor
        else:
            print('Wrong key name %s!' % parName)


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

    def calCongestion(self):
        '''
        Usage: count cars in one road
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
                    previousCar, previousState = i, 1
    
    def searchCar(self, start, end, channel, tube):
        for i in range(end, start, -1):
            if tube[i][channel] is not None:
                return i
        return -1
    
    def firstPriorityCar(self):

        firstPriorityCar = [None] * self.channel_
        firstPriorityCarPoint = [-10000] * self.channel_
        for y in range(self.channel_):
            for x in range(self.length_):
                if self.provideTube[x][y] != None:
                    carId = self.provideTube[x][y]
                    car = CARDICT[carId]
                    left = car.__getPar__('v')
                    priority = car.__getPar__('priority')              
                    if left > x and car.state == 1:
                        firstPriorityCar[y] = x
                        firstPriorityCarPoint[y] = priority * 10000 - self.channel_ * y - x
                    break

        maxNum = -10000
        for i in range(self.channel_):
            if firstPriorityCarPoint[i] > maxNum:
                maxNum = firstPriorityCarPoint[i]
                self.px, self.py = firstPriorityCar[i], i
        if maxNum == -10000:
            return -1
        else:
            return self.provideTube[self.px][self.py]

    
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
        if self.receiveTube is None:
            print("Please do ROAD.setBucket() first!")
        car = CARDICT[carId]
        leftX = max(min(self.speed_, car.__getPar__('speed')) - car.__getPar__('x'), 0)
        if car.__getPar__('nextCrossId') != self.startId_:
            nextCrossId = self.startId_
        else:
            nextCrossId = self.endId_ # 16619958513
        if leftX <= 0:
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
        self.carport, self.priCarport = {}, {}
        self.left, self.priLeft = [], []
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
        self.readyCars, self.readyPriCars = [], []
        self.carportCarNum, self.priCarportCarNum = 0, 0
        self.finishCarNum, self.priFinishCarNum = 0, 0
        self.x, self.y = 0, 0
        self.mapX,self.mapY = 0,0
        # **** flag ****#
        self.done = False
        self.update = False

    # Update 2019.4.4 : add priorityBias for high priority cars
    def step(self):
        self.update = False
        for roadId in self.validRoad:
            ROADDICT[roadId].setBucket(self.id_)
        firstCarId, firstCar, nextRoad, nextCarPriority = [], [], [], []
        # print(self.provider)
        for provideIndex in range(self.provider.__len__()): # provideIndex [0, 1, 2, 3]
            # TODO : change firstPriorityCar
            firstCarId.append(ROADDICT[self.provider[provideIndex]].firstPriorityCar()) # [fisrt car in 5001, fisrt car in 5002 ....]
            # if first priority car exists
            if firstCarId[provideIndex] != -1:
                firstCar.append(CARDICT[firstCarId[provideIndex]]) # [Car..., Car..., Car..., ]
                nextRoad.append(firstCar[provideIndex].__getPar__('nextRoad')) # [5007, 5007, 5008, 5001]
                # if car is high priority, priority += 3
                priorityBias = 3 * firstCar[provideIndex].__getPar__('priority')
                # nextRoad == -1 => terminal
                if nextRoad[provideIndex] == -1:
                    nextCarPriority.append(priorityBias + 2)
                else:
                    nextCarPriority.append(priorityBias + self.priority(self.provider[provideIndex], nextRoad[provideIndex]))
            else:
                firstCar.append(-1)
                nextRoad.append(-1)
                nextCarPriority.append(-1)
        
        roadNum = self.provider.__len__()
        actionFlag = [0] * roadNum
        for i in range(roadNum):
            if self.provider[i] != -1:
                provideIndex = i
                break
        # while (actionFlag[]不都为1 or firstCarId不都为-1):
        while sum(actionFlag[:]) != roadNum and sum(firstCarId[:]) != -roadNum:
            if(firstCarId[provideIndex] != -1):
                for i in range(roadNum):
                    # if conflict(same direction and low priority)
                    if nextRoad[i] == nextRoad[provideIndex] and nextCarPriority[i] > nextCarPriority[provideIndex] and actionFlag[i] != 1:
                        provideIndex = i
                provider = ROADDICT[self.provider[provideIndex]]
                if nextRoad[provideIndex] == -1:
                    provider.firstPriorityCarAct(0)
                    self.update = True
                    CARDISTRIBUTION[1] -= 1
                    CARDISTRIBUTION[2] += 1
                else:
                    nextroad_ = ROADDICT[nextRoad[provideIndex]]
                    action = nextroad_.receiveCar(firstCar[provideIndex].__getPar__('id'))
                    if action == 2:
                        #堵塞标志赋值
                        actionFlag[provideIndex] = 1
                        #找下一个provideIndex 并且把值赋给provideIndex
                        provideIndex = (provideIndex + 1) % roadNum
                        continue
                    provider.firstPriorityCarAct(action)
                    self.update = True
                firstCarId[provideIndex] = provider.firstPriorityCar()
                if firstCarId[provideIndex] != -1:
                    #换车后拥堵标志位清空
                    actionFlag[provideIndex] = 0                                                                                                                                                                                                                                                                                                
                    firstCar[provideIndex] = CARDICT[firstCarId[provideIndex]]
                    nextRoad[provideIndex] = firstCar[provideIndex].__getPar__('nextRoad')
                    # nextRoad == -1 => terminal
                    if nextRoad[provideIndex] == -1:
                        nextCarPriority[provideIndex] = 2
                    else:
                        nextCarPriority[provideIndex]= self.priority(self.provider[provideIndex], nextRoad[provideIndex])
                else:
                    firstCar[provideIndex] = -1
                    nextRoad[provideIndex]= -1
                    nextCarPriority[provideIndex] = -1
            else:
                actionFlag[provideIndex] = 1
                #找下一个provideIndex 并且把值赋给provideIndex
                provideIndex = (provideIndex + 1) % roadNum
        done = True
        for i in range(roadNum):
            if firstCar[i] != -1:
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
        self.readyCars.sort()
        for roadId in self.receiver:
            ROADDICT[roadId].setBucket(self.id_)
        for i in range(self.readyCars.__len__()):
            carId = self.readyCars[i]
            roadId = CARDICT[carId].__getPar__('nextRoad')
            road = ROADDICT[roadId]
            # print(CARDICT[carId].__getPar__('routeIndex'))
            if roadId not in self.receiver:
                print("Car(%d).Road(%d) not in cross(%d).function:class.outOfCarport"%(carId,roadId,self.id_))
            act = road.receiveCar(carId)
            if act != 0:
                self.left.append(self.readyCars[i])
            else:
                self.carportCarNum -= 1
                CARDISTRIBUTION[0] -= 1
                CARDISTRIBUTION[1] += 1

    def outOfPriCarport(self):
        self.readyPriCars = self.priLeft
        self.priLeft=[]
        if TIME[0] in self.priCarport.keys():
            self.priCarport[TIME[0]].sort()
            self.readyPriCars.extend(self.priCarport[TIME[0]])
        if self.readyPriCars.__len__() == 0:
            return
        self.readyPriCars.sort()
        for roadId in self.receiver:
            ROADDICT[roadId].setBucket(self.id_)
        for i in range(self.readyPriCars.__len__()):
            carId = self.readyPriCars[i]
            roadId = CARDICT[carId].__getPar__('nextRoad')
            road = ROADDICT[roadId]
            if roadId not in self.receiver:
                print("Car(%d).Road(%d) not in cross(%d).function:class.outOfPriCarport"%(carId,roadId,self.id_))
            act = road.receiveCar(carId)
            if act != 0:
                self.priLeft.append(carId)
            else:
                self.priCarportCarNum -= 1
                CARDISTRIBUTION[0] -= 1
                CARDISTRIBUTION[1] += 1
    
    def priority(self,providerId,receiverId):
        return self.priorityMap[providerId][receiverId]
    def setDone(self,bool):
        self.done = bool
    def setLoc(self,x,y):
        self.x,self.y = x,y
    def setMapLoc(self,mapX,mapY):
        self.mapX,self.mapY = mapX,mapY
    # BUG: To be test
    def roadDirection(self,roadId):
        try:
            return(self.roadIds.index(roadId))
        except:
            return -1
    def carportInitial(self, timePlan, carId):
        if timePlan not in self.carport.keys():
            self.carport[timePlan] = [carId]
        else:
            self.carport[timePlan].append(carId)
        self.carportCarNum += 1
    def priCarportInitial(self, timePlan, carId):
        if timePlan not in self.priCarport.keys():
            self.priCarport[timePlan] = [carId]
        else:
            self.priCarport[timePlan].append(carId)
        self.priCarportCarNum += 1

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
        if parName == 'mapLoc':
            return self.mapX,self.mapY


class visualization(object):
    def __init__(self):
        self.maxX,self.maxY = 0,0
        self.savePath = '../sim'
        # ** cross param **#
        self.crossRadius = 14
        self.crossDistance = 150
        self.crossColor = [25,200,0]
        # ** road param **#
        self.roadColor = [0,0,0] #black
        self.roadLineType = 4
        self.channelWidth = 5
        self.channelDistance = 3
        self.lineWidth = 2
        self.time = 0
    #
    # cross location gen
    #
    def crossLocGen(self):
        #**** relative location ****#
        # denote the first cross as the origin of coordinates
        for crossId in CROSSNAMESPACE:
            CROSSDICT[crossId].setDone(False)
        crossList = [CROSSNAMESPACE[0]]
        minX,minY = 0,0
        while(crossList.__len__()>0):
            nextCrossList = []
            for crossId in crossList:
                presentX,presntY = CROSSDICT[crossId].__getPar__('loc')
                validRoad = CROSSDICT[crossId].__getPar__('validRoad')
                for roadId in validRoad:
                    #next cross id
                    nextCrossId = ROADDICT[roadId].__getPar__('startId') if ROADDICT[roadId].__getPar__('startId') != crossId \
                                                            else ROADDICT[roadId].__getPar__('endId')
                    # if next cross is visited
                    if not CROSSDICT[nextCrossId].__getPar__('done'):
                        # visit sets true
                        CROSSDICT[nextCrossId].setDone(True)
                        # relative location of nextcross
                        nextX,nextY = self.crossRelativeLoc(presentX,presntY,crossId,roadId)
                        # update location
                        CROSSDICT[nextCrossId].setLoc(nextX,nextY)
                        minX,minY,self.maxX,self.maxY=\
                                    min(nextX,minX),min(nextY,minY),max(nextX,self.maxX),max(nextY,self.maxY)
                        nextCrossList.append(nextCrossId)
            crossList = nextCrossList
        self.maxX,self.maxY = (self.maxX-minX+2)*self.crossDistance,(self.maxY-minY+2)*self.crossDistance
        for crossId in CROSSNAMESPACE:
            x,y = CROSSDICT[crossId].__getPar__('loc')
            CROSSDICT[crossId].setLoc(x-minX,y-minY)
            CROSSDICT[crossId].setMapLoc((x - minX+1)*self.crossDistance, (y - minY+1)*self.crossDistance)
    def crossRelativeLoc(self,x,y,crossId,roadId):
        roadDirection = CROSSDICT[crossId].roadDirection(roadId)
        if roadDirection==0:
            return x,y-1
        elif roadDirection==1:
            return x+1,y
        elif roadDirection==2:
            return x,y+1
        elif roadDirection==3:
            return x-1,y

    #
    # draw functions
    #
    def drawMap(self):
        img = np.ones((self.maxX,self.maxY,3),np.uint8)*255
        #draw road
        for roadId in ROADNAMESPACE:
            self.plotRoad(roadId,img)
        # draw cross
        for crossId in CROSSNAMESPACE:
            self.plotCross(crossId,img)
        # plot info
        self.plotInfo(img)
        cv.imwrite(self.savePath+'/%d.jpg'%TIME[0],img)
    def plotCross(self,crossId,img):
        x, y = CROSSDICT[crossId].__getPar__('mapLoc')
        cv.circle(img,(x,y),self.crossRadius,color=self.crossColor,thickness=-1,lineType=-1)
        if crossId>=10:
            xx, yy = int(x - 4*self.crossRadius/5), int(y + self.crossRadius / 2)
        else:
            xx, yy = int(x- self.crossRadius/2), int(y + self.crossRadius / 2)
        cv.putText(img,str(crossId),(xx,yy ),cv.FONT_HERSHEY_SIMPLEX,0.6,[0,0,255],2)
    def plotRoad(self,roadId,img):
        # get road info
        road = ROADDICT[roadId]
        fromX, fromY = CROSSDICT[road.__getPar__('startId')].__getPar__('mapLoc')
        toX, toY = CROSSDICT[road.__getPar__('endId')].__getPar__('mapLoc')
        # plot line
        cv.line(img,(fromX, fromY),(toX, toY),color=self.roadColor,thickness=2)
        # plot bucket
        self.drawBucket(road,'forward',img)
        if road.__getPar__('isDuplex'):
            self.drawBucket(road,'backward',img)
    def drawBucket(self,road,lane,img):
        bucket = road.__getPar__('forwardTube') if lane !='backward' else road.__getPar__('backwardTube')
        length = road.__getPar__('length')
        channel = road.__getPar__('channel')
        fromX, fromY = CROSSDICT[road.__getPar__('startId')].__getPar__('mapLoc')
        toX, toY = CROSSDICT[road.__getPar__('endId')].__getPar__('mapLoc')
        XY, intervalXY, rectangleSize, channel2XY, length2XY = self.bucketDrawInitial(fromX,fromY,toX,toY,lane,length)
        for i in range(length):
            for j in range(channel):
                xRD,yRD = int(XY[0]+rectangleSize[0]),int(XY[1]+rectangleSize[1])
                if bucket[i][j] is  None:
                    cv.rectangle(img,(int(XY[0]),int(XY[1])),(xRD,yRD),(0,0,0),1)
                else:
                    color = CARDICT[bucket[i][j]].__getPar__('carColor')
                    cv.rectangle(img, (int(XY[0]), int(XY[1])),(xRD, yRD),color=color,thickness=-1)
                XY[channel2XY] = XY[channel2XY] + intervalXY[channel2XY]
            XY[channel2XY] = XY[channel2XY] - intervalXY[channel2XY]*channel
            XY[length2XY] = XY[length2XY] + intervalXY[length2XY]
    def bucketDrawInitial(self,fromX,fromY,toX,toY,lane,length):
        direction = self.bucketDirection(fromX,fromY,toX,toY,lane)
        unitLength = (self.crossDistance - self.crossRadius * 4) / length
        if lane=='backward':
            toY=fromY
            toX=fromX
        if direction == 'north':
            XY = [fromX + self.channelDistance,toY + self.crossRadius * 2]
            intervalXY = self.channelDistance  + self.channelWidth , unitLength
            rectangleSize = self.channelWidth , unitLength
            channel2XY, length2XY = 0, 1
        elif direction == 'south':
            XY = [fromX - self.channelDistance - self.channelWidth,toY - self.crossRadius * 2 - unitLength]
            intervalXY = -(self.channelDistance  + self.channelWidth ), -unitLength
            rectangleSize = self.channelWidth , unitLength
            channel2XY, length2XY = 0, 1
        elif direction == 'east':
            XY = [toX - self.crossRadius * 2 - unitLength,fromY + self.channelDistance]
            intervalXY = -unitLength, self.channelDistance + self.channelWidth
            rectangleSize = unitLength, self.channelWidth
            channel2XY, length2XY = 1, 0
        elif direction == 'west':
            XY = [toX + self.crossRadius * 2, fromY - self.channelDistance - self.channelWidth]
            intervalXY = unitLength, -(self.channelDistance + self.channelWidth)
            rectangleSize = unitLength, self.channelWidth
            channel2XY, length2XY = 1, 0
        return XY,intervalXY,rectangleSize,channel2XY,length2XY
    def bucketDirection(self,fromX,fromY,toX,toY,lane):
        if fromY > toY:
            direction = 'north' if lane=='forward' else 'south'
        elif fromY < toY:
            direction = 'south' if lane == 'forward' else 'north'
        elif fromX < toX:
            direction = 'east' if lane == 'forward' else 'west'
        else:
            direction = 'west' if lane == 'forward' else 'east'
        return direction
    def plotInfo(self,img):
        for crossId in CROSSNAMESPACE:
            cross = CROSSDICT[crossId]
            x,y = cross.__getPar__('mapLoc')
            cn,fn = cross.__getPar__('carportCarNum'),cross.__getPar__('finishCarNum')
            # cv.putText(img,"%d,%d"%(cn,fn),(int(x),int(y-1.1*self.crossRadius)),\
            #            cv.FONT_HERSHEY_SIMPLEX,0.4,[0,0,255],1)
        cv.putText(img, "in the carport:%d,on the road:%d,end of the trip:%d" % (CARDISTRIBUTION[0],CARDISTRIBUTION[1],CARDISTRIBUTION[2]),(30,30), \
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, [0, 0, 255], 2)


def infInit(crossPath, roadPath, carPath, presetPath):
    crossInf = readInf(crossPath)
    roadInf = readInf(roadPath)
    carInf = readInf(carPath)
    presetInf = readInf(presetPath)

    for line in carInf:
        #### Update 2019.4.3 : divide car whether preset ####
        CARNAMESPACE.append(line[0])
        CARDICT[line[0]] = Car(line)
        if line[6] == 1:
            PRESETCARNAMESPACE.append(line[0])

    for line in roadInf:
        ROADNAMESPACE.append(line[0])
        ROADDICT[line[0]] = Road(line)

        visitDone = {}
    for line in crossInf:
        id_= line[0]
        CROSSNAMESPACE.append(int(id_))
        visitDone[int(id_)] = False
        CROSSDICT[int(id_)] = line[1:]

    def remaster(crossId, direction=None, preCrossId=None):
        if visitDone[crossId]:
            return
        visitDone[crossId] = True
        if preCrossId is not None:
            for i in range(4):
                roadId = CROSSDICT[crossId][i]
                if roadId != -1:
                    pcId = ROADDICT[roadId].__getPar__('startId') if ROADDICT[roadId].__getPar__('startId')!= crossId else ROADDICT[roadId].__getPar__('endId')
                    if pcId == preCrossId:
                        break
            shift = ((i + 2) % 4 - direction) % 4
            for i in range(shift):
                CROSSDICT[crossId]=[CROSSDICT[crossId][1],CROSSDICT[crossId][2],CROSSDICT[crossId][3],CROSSDICT[crossId][0]]
        for i in range(4):
            roadId = CROSSDICT[crossId][i]
            if roadId != -1:
                nextCrossId = ROADDICT[roadId].__getPar__('startId') if ROADDICT[roadId].__getPar__('startId')!= crossId else ROADDICT[roadId].__getPar__('endId')
                remaster(nextCrossId,i,crossId)

    remaster(CROSSNAMESPACE[0])
    for crossId in CROSSNAMESPACE:
        line = [crossId] + CROSSDICT[crossId]
        CROSSDICT[crossId] = Cross(line)
        ROADLOSSDICT[crossId] = {}

    CARDISTRIBUTION[0] = CARNAMESPACE.__len__()
    CARNAMESPACE.sort()
    PRESETCARNAMESPACE.sort()
    CROSSNAMESPACE.sort()

    #### Update 2019.4.1 ####
    for crossId in CROSSNAMESPACE:
        CROSSROADDICT[crossId] = {} 
    for roadId in ROADNAMESPACE:
        road = ROADDICT[roadId]
        CROSSROADDICT[road.__getPar__('startId')][road.__getPar__('endId')] = road.__getPar__('id')
        if road.__getPar__('isDuplex'):
            CROSSROADDICT[road.__getPar__('endId')][road.__getPar__('startId')] = road.__getPar__('id')

    #### Update 2019.4.2 : add map_graph {startId:{endId: length}} ####
    for line in roadInf:
        _, length, _, _, start_id, end_id, is_dux = line
        if start_id not in CROSSLENGTHDICT.keys():
            CROSSLENGTHDICT[start_id] = {}
        CROSSLENGTHDICT[start_id][end_id] = length
        if is_dux:
            if end_id not in CROSSLENGTHDICT.keys():
                CROSSLENGTHDICT[end_id] = {}
            CROSSLENGTHDICT[end_id][start_id] = length

    return presetInf


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
    while unfinishedCross.__len__() > 0:
        deadSign = True
        nextCross = []
        for crossId in unfinishedCross:
            cross = CROSSDICT[crossId]
            # print('inStep')
            cross.step()
            # print('outStep')
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
        #### Update 2019.4.3 add out of priority caport ####
        CROSSDICT[crossId].outOfPriCarport()
    for i in range(CROSSNAMESPACE.__len__()):
        crossId = CROSSNAMESPACE[i]
        for roadId in CROSSDICT[crossId].__getPar__('validRoad'):
            ROADDICT[roadId].setBucket(crossId)
        CROSSDICT[crossId].outOfCarport()
    
    return deadSign


def speedSplit():
    """
    Usage: divide car by speed
    """
    max_speed = 0
    carDivideSpeed = {}

    unPresetCar = set(CARNAMESPACE) - set(PRESETCARNAMESPACE)
    for carId in unPresetCar:
        car = CARDICT[carId]
        speed = car.__getPar__('speed')
        if speed > max_speed:
            max_speed = speed
        if speed not in carDivideSpeed.keys():
            carDivideSpeed[speed] = []
        carDivideSpeed[speed].append(carId)
 
    return carDivideSpeed


def timeSplit(group, carPerSec, intervalTime, speed):

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

    for i in range(batch_num):
        curBatch = []
        for j in range(carPerBatch):
            try: 
                curBatch.append(group.pop())
            except:
                break
        groupDivideTime.append(curBatch)
    
    return groupDivideTime


def dijkstra(G, start):  ###dijkstra算法
    INF = float('inf')

    dis = dict((key, INF) for key in G)  # start到每个点的距离
    dis[start] = 0
    vis = dict((key, False) for key in G)  # 是否访问过，1位访问过，0为未访问
    ###堆优化
    pq = []  # 存放排序后的值
    heap.heappush(pq, [dis[start], start])

    path = dict((key, [start]) for key in G)  # 记录到每个点的路径
    while len(pq) > 0:
        _, v = heap.heappop(pq)  # 未访问点中距离最小的点和对应的距离
        if vis[v] == True:
            continue
        vis[v] = True
        p = path[v].copy()  # 到v的最短路径
        for node in G[v]:  # 与v直接相连的点
            new_dis = dis[v] + float(G[v][node])
            if new_dis < dis[node] and (not vis[node]):  # 如果与v直接相连的node通过v到src的距离小于dis中对应的node的值,则用小的值替换
                dis[node] = new_dis  # 更新点的距离
                #  dis_un[node][0] = new_dis    #更新未访问的点到start的距离
                heap.heappush(pq, [dis[node], node])
                temp = p.copy()
                temp.append(node)  # 更新node的路径
                path[node] = temp  # 将新路径赋值给temp

    return path


#### TODO: optimization ####
def calCarPath(batch, curTime):

    path, pathRoadTime = [], []
    
    for carId in batch:
        car = CARDICT[carId]
        path = dijkstra(ROADLOSSDICT, car.__getPar__('startId'))[car.__getPar__('endId')]
        pathCenter = []
        a = len(path)
    
        pathCenter.append(car.__getPar__('id'))
        pathCenter.append(max(car.startTime_, curTime))
        for j in range(a-1):
            pathCenter.append(CROSSROADDICT[path[j]][path[j+1]])
        pathRoadTime.append(pathCenter)

    return pathRoadTime


#### Update 2019.4.3 ####
def updateLoss(speed):

    for roadId in ROADNAMESPACE:
        road = ROADDICT[roadId]
        startId, endId = road.__getPar__('startId'), road.__getPar__('endId')
        length, speedLim = road.__getPar__('length'), road.__getPar__('speed')
        ROADLOSSDICT[startId][endId] = length * 1 / min(speedLim, speed) + delta1 * ROADUSEDICT[roadId][0] + delta2 * CROSSLOSSDICT[startId][endId] ** 2
        if road.__getPar__('isDuplex') == 1:
            ROADLOSSDICT[endId][startId] = length * 1 / min(speedLim, speed) + delta1 * ROADUSEDICT[roadId][1]+ delta2 * CROSSLOSSDICT[endId][startId] ** 2
        else:
            ROADLOSSDICT[endId][startId] = float('inf')


def update_car(finalTime, time):
    newFinalTime = []
    for i in finalTime:
        if i > time:
            newFinalTime.append(i)
    
    return newFinalTime


def calCrossLoss():
    """
    Usage: Calculate loss of road in each cross. 
           loss = (average of otherRoadFlow - curRoadFlow) / curRoadFlow ** 2 
    """
    for startId in CROSSNAMESPACE:
        roadNum = len(CROSSROADDICT[startId].keys())
        roadIds = list(CROSSROADDICT[startId].values())
        if startId not in CROSSLOSSDICT.keys():
            CROSSLOSSDICT[startId] = {}   

        for endId in CROSSROADDICT[startId].keys():
            curRoadId = CROSSROADDICT[startId][endId]
            curRoadFlow = ROADDICT[curRoadId].__getPar__('roadFlow')
            inFlow = 0
            for roadId in roadIds:
                if roadId == curRoadId:
                    continue
                inFlow += ROADDICT[roadId].__getPar__('roadFlow')
            CROSSLOSSDICT[startId][endId]= max((inFlow / (roadNum - 1) - curRoadFlow), 0) / curRoadFlow ** 2


def getRoadCrowd():
    for roadId in ROADNAMESPACE:
        road = ROADDICT[roadId]
        fcong, bcong = road.calCongestion()
        ROADUSEDICT[roadId] = [fcong, bcong]


#### Update 2019.4.3 ####
def carPlan(pathTimeInf):
    carReadyDict = {}
    for line in pathTimeInf:
        carId = int(line[0])
        planTime = int(line[1])
        route = [int(roadId) for roadId in line[2:]]
        CARDICT[carId].simulateInit(planTime, route)
        carReadyDict[carId] = CARDICT[carId]
    for carId in carReadyDict:
        car = CARDICT[carId]
        if car.__getPar__('priority') == 0:
            CROSSDICT[car.__getPar__('startId')].carportInitial(CARDICT[carId].__getPar__('startTime'), carId)
        elif car.__getPar__('priority') == 1: 
            CROSSDICT[car.__getPar__('startId')].priCarportInitial(CARDICT[carId].__getPar__('startTime'), carId)


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

    # car_path = sys.argv[1]
    # road_path = sys.argv[2]
    # cross_path = sys.argv[3]
    # preset_path = sys.argv[4]
    # answer_path = sys.argv[5]

    relate_path = 'Map/2-map-training-1'
    cross_path = '../' + relate_path + '/cross.txt'
    road_path = '../' + relate_path + '/road.txt'
    car_path = '../' + relate_path + '/car.txt'
    answer_path = '../' + relate_path + '/answer1.txt'
    preset_path = '../' + relate_path + '/presetAnswer.txt'

    presetInf = infInit(cross_path, road_path, car_path, preset_path)
    visualize = visualization()
    visualize.crossLocGen()
    calCrossLoss()
    carPlan(presetInf)

    carDivideSpeed = speedSplit()
    answer, speed_list = [], []
    dijTime = 0
    # crossMap = createCrossMap(crossInf, roadInf, roadIdBias)

    # 1. divide by speed
    # 2. calculate time by position (TODO)
    # 3. loop: calculate path ; record road ; update map (TODO)
    for speed in carDivideSpeed:
        speed_list.append(speed)
    speed_list.reverse()
    dead_flag = False
    for speed in speed_list:
        curGroup = carDivideSpeed[speed]
        if not curGroup:
            continue
        groupDivideTime = timeSplit(curGroup, carPerSec, intervalTime, speed)

        for batch in groupDivideTime:
            batch_len = len(batch)
            while (CARDISTRIBUTION[1] > (carInMap - batch_len)):
                dead_flag = simulateStep()
                # visualize.drawMap()       
                TIME[0] += 1
                print(TIME[0], CARDISTRIBUTION)
                if dead_flag:
                    break
            if dead_flag:
                break
            getRoadCrowd()
            updateLoss(speed)
            dij = time.time()
            batchPathTime = calCarPath(batch, TIME[0])
            carPlan(batchPathTime)
            dijTime += time.time() - dij
            dead_flag = simulateStep()
            # visualize.drawMap()
            if dead_flag:
                break
            TIME[0] += 1
            print(TIME[0], CARDISTRIBUTION)
            answer += batchPathTime
        if dead_flag:
            break
    while CARDISTRIBUTION[0] + CARDISTRIBUTION[1] != 0:
        if dead_flag:
            break        
        dead_flag = simulateStep()
        # visualize.drawMap()


    with open(answer_path, 'w') as fp:
        fp.write('\n'.join(str(tuple(x)) for x in answer))
    print(dijTime)

if __name__ == "__main__":
    a = time.time()
    main()
    print(time.time() - a)