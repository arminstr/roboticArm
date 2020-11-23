# copyright 2020 Armin Straller
import os, json, uuid, math
import numpy as np
from mathModel import DynamicModel
from controller import PDController

class RobotArm(object):
    def __init__(self, uI):
        self.updateInterval = uI
        #axis limits
        self.limitP = np.array([math.pi * (3/4), math.pi * (3/4), math.pi * (3/4), 0.1])
        self.limitN = np.array([- math.pi * (3/4), - math.pi * (3/4), - math.pi * (3/4), 0])
        
        # motor torque limit and torque transmission
        self.limitTau = np.array([[1.9, 1.9, 10, 0.9]]).T
        self.tauTransmission = np.array([[2, 2, 4, 2]]).T

         # motor speed limit and torque transmission
        self.limitSpeed = np.array([[20, 20, 1, 20]]).T
        self.tauTransmission = np.array([[2, 2, 4, 2]]).T
        self.limitSpeedTrans = (math.pi * 2 * self.limitSpeed) / self.tauTransmission

        # math models
        self.dynModel = DynamicModel(0.25, 0.25, 0, 0.12, 0.13, 2, 3, 1, 0.02, 0.01, 1.35e-5, self.tauTransmission)

        # position controllers 
        self.qControlP = np.array([[320,  10,  2000,  0.5]]).T 
        self.qControlD = np.array([[80,  1.3,  100,  1e-3]]).T 
        self.qControl = PDController(self.qControlP, self.qControlD, self.limitTau)
        
        self.qTarget = np.zeros((4,1))
        self.q = np.zeros((4,1))
        self.qdot = np.zeros((4,1))
        self.qdotdot = np.zeros((4,1))
        #interval for visu update
        self.visuInterval = 50
        self.intervalCounter = 0
        
    def update(self):
        torqueCommand = self.qControl.update(self.qTarget, self.q, self.qdot)
        self.dynModel.update(self.q, self.qdot, torqueCommand)
        self.qdotdot = self.dynModel.qdotdot
        
        self.qdot += self.qdotdot * self.updateInterval
        for i in range(4):
            if(self.qdot[i] > 0.9 * self.limitSpeedTrans[i]):
                self.qdot[i] = 0.9 * self.limitSpeedTrans[i]
            if(self.qdot[i] < - 0.9 * self.limitSpeedTrans[i]):    
                self.qdot[i] = - 0.9 * self.limitSpeedTrans[i]
        
        self.q += self.qdot * self.updateInterval
        #updating the visualization
        if(self.intervalCounter > self.visuInterval):
            self.updateVisu(self.q)
            self.intervalCounter = 0
        self.intervalCounter += 1

    #storing current position to json file
    def updateVisu(self, q):
        if isinstance(q, np.ndarray):
            q =  q.ravel().tolist()
        filename = 'control.json'
        with open(filename, 'r') as f:
            data = json.load(f)
            data["robotPosition"]["a1"] =   q[0]
            data["robotPosition"]["a2"] =   q[1]
            data["robotPosition"]["a3"] =   q[3]
            data["robotPosition"]["z"] =    q[2] * 1000 # convert from m to mm
        # create randomly named temporary file to avoid 
        # interference with other thread/asynchronous request
        tempfile = os.path.join(os.path.dirname(filename), str(uuid.uuid4()))
        with open(tempfile, 'w') as f:
            json.dump(data, f, indent=4)
        # rename temporary file replacing old file
        os.rename(tempfile, filename)

    #setter function for Target Axis position
    def setTargetPosAxis(self, theta1, theta2, d3, theta4):
        self.qTarget = np.array([[theta1, theta2, d3, theta4]]).T
            
        
