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
         - road.setBucket()
         - road.findPriorityCar() *** 加入优先车辆的判断 ***
         - crossLoop 循环更新该路口车辆，直到所有路口都完成更新
           - roadInCrossLoop
             - 如果当前道路第一优先级车辆优先级低于其他道路第一优先级车，进入当前路口下一道路
             - 如果该路口优先级的车为当前路口最高优先级：
               - 到达终点, cross.update = True
               - 进入下一道路, cross.update = True
           - 如果有未完成更新的车，cross.done = False
           - 判断死锁：cross.update = 0 and cross.done = 0, then deadLock; 即该路口有车没走完，该时间片一辆车都没走，则认为已经死锁
     - loop 每个路口放车出库 *** 加入优先车辆判断 *** finished
       - 初始化 setBucket()
       - cross.outOfPriCarport()
       - cross.outOfCarport()