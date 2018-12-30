import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from test.test_support import FUZZ

class FuzzySystem(object):
    
    def __init__(self):
        hue = ctrl.Antecedent(np.arange(0, 180, 1), 'hue')
        saturation = ctrl.Antecedent(np.arange(0, 255, 1), 'saturation')
        output = ctrl.Consequent(np.arange(0, 100, 1), 'decision')
        
        # membership functions for hue
        hue['red_left'] = fuzz.trimf(hue.universe, [0,0,30])
        hue['yellow'] = fuzz.trimf(hue.universe, [0,30,60])
        hue['green'] = fuzz.trimf(hue.universe, [30,60,90])
        hue['cyan'] = fuzz.trimf(hue.universe, [60,90,120])
        hue['blue'] = fuzz.trimf(hue.universe, [90,120,150])
        hue['magenta'] = fuzz.trimf(hue.universe, [120,150,180])
        hue['red_right'] = fuzz.trimf(hue.universe, [150,180,180])
        # membership functions for saturation - automatic 5 functions
        saturation.automf(5)
        # Consequent membership function
        output['option_1'] = fuzz.trapmf(output.universe, [0,0,20,30])
        output['option_2'] = fuzz.trapmf(output.universe, [20,30,70,80])
        output['option_3'] = fuzz.trapmf(output.universe, [70,80,100,100])
        # inference rules
        rule1 = ctrl.Rule(hue['yellow'] & saturation['poor'], output['option_1'])
        rule2 = ctrl.Rule(hue['blue'] & saturation['poor'], output['option_2'])
        
        self.ExpSys_ctrl = ctrl.ControlSystem([rule1, rule2])
        #self.hue.view()
        #self.saturation.view()
        #self.output.view()
        
    def computeOutput(self, hue, saturation):
        ExpSys = ctrl.ControlSystemSimulation(self.ExpSys_ctrl)
        ExpSys.input['hue'] = hue
        ExpSys.input['saturation'] = saturation
        ExpSys.compute()
        
        return ExpSys.output['output']
    
    def __normalizeHue(self, hue):
        temp_hue = hue+15
        if(temp_hue<180):
            return temp_hue
        else:
            return temp_hue-180
