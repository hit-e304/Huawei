# README

## workspace.py

### 更新日志

- 2019.4.3
  
  1. 针对复赛要求，更新preset车辆信息，尝试对判题器修改，适应含优先级车辆
  2. 更换信息存储方式，全部由List转为Dict

### 程序导图

1. readInf

    - roadInf
    - crossInf
    - carInf : 新增两个属性，priority、preset
    - presetAnswer ： 对应 carInf 中 preset == 1 的车

2. infInit

    初始化对象，从inf读入其参数

    - NAMESPACE
      - CARNAMESPACE
      - PRESETCARNAMESPACE
      - ROADNAMESPACE
      - CROSSNAMESPACE
    - DICT
      - CARDICT
      - ROADDICT
      - CROSSDICT
    - else
      - CROSSROADDICT {crossId: {crossId: roadId}}: 用于 dij 搜图，存储所有可联通的cross之间的roadId
      - CROSSLOSSDICT {crossId: {crossID: loss}}
      - CROSSLENGTHDICT {crossId:{crossId: length}} ：用于存储两节点间道路长度，用于将 dij 的输出从节点转为道路
      - TIME [ ]：用于存贮推进时间片
      - CARRDISTRIBUTION [ num, num, num ]：未出发车数、上路车数、到达终点数

3. simulateStep

   - stepInit : 将标志位清零，初始化road和cross
     - cross.setDone()
       - self.setDone = Flase
     - road.stepInit()
       - 所有标志位、tube清零
       - 道路中所有车辆 state=1
       - 进行一次更新 updateChannel()
     - 初始化unfinishedCross = CROSSNAMESPACE

   - loop 按cross遍历，更新路口车辆
     - deadSign = True
     - for cross in unfinished: cross.step()
       - cross.update = False
       - for road in cross: road.setBucket()
      *** 加入优先车辆的判断 ***
       - for road in cross
         - road.findPriorityCar()
           - 按先y后x顺序遍历，直到找到第一个移动距离过路口，且其前方无车的车
           - 若没有，retrun -1， provideDone=True
         - if firstCarId exist:
           - 统计该道路车辆路口优先级
       - crossLoop 循环更新该路口车辆，直到所有路口都完成更新
         - roadInCrossLoop
           - 如果当前道路第一优先级车辆优先级低于其他道路第一优先级车，进入当前路口下一道路
           - 如果该路口优先级的车为当前路口最高优先级：
             - 到达终点, updateChannel(), cross.update = True
             - 进入下一道路, updateChannel(), cross.update = True
         - 如果有未完成更新的车，cross.done = False
         - 判断死锁：cross.update = 0 and cross.done = 0, then deadLock; 即该路口有车没走完，该时间片一辆车都没走，则认为已经死锁

   - loop 每个路口放车出库
     - 初始化 setBucket()
     - cross.outOfPriCarport()
     - cross.outOfCarport()

4. receiveCar()

    return = 0，等待更新；1，未过路口；2，已过路口

   - if not receiveTube: error
   - calculate leftX
   - judge nextCrossId = startId_ or endId_
   - for chanel in road:
     - if leftX <= 0 : car.state = 2, return 1
     - if no previousCar in cross : move to leftX, car.state=2, return 0
     - if have previousCar:
       - if previousCar.state = 1 : wait, reuturn 2
       - if previousCar.state = 2 and have empty pos : move behind it , car.state=2, return 0
   - if no space in any channel : move to top of current road, car.state = 2 return 1

5. updateChannel()

    初始更新一次，该道路每有一个车过了路口，更新一次

   - for car in current channel:
     - v = min(speedlim, v)
       - if 当前车更新过，不动
       - if 不会撞上前车，且不过马路 直接移动到对应位置
       - if 会撞上前车，且前车state=2 贴上去
       - if 前车未更新，或当前车是第一辆车，但会过马路， 等待

6. firstPriorityCar()

   - init firstLowPriority 储存找到的每个channel第一辆低优先级车
   - while True：
     - if 找完了全部长度
       - 有低优先级车辆：取出位置最高的
       - 没有低优先车辆：return -1
     - elif 全部channel找到了第一辆低优先级车
       - 从其中选X最小的输出
     - elif 当前channel第一低优先级车已找到
       - 跳过当前channel，搜索下一位置
     - else：
       - 如果当前位置有车：
         - 如果是高优先级
           - 直接输出
         - 如果是低优先级
           - 存入firstLowPriority[channel]
           - 搜索下一位置
       - 如果当前位置没车
         - 搜索下一位置