from FuzzySystem import *

class ExpertSystem(object):
    
    def __init__(self):
        try:
            self.fuzzySystem = FuzzySystem()
        except IOError as e:
            self.fuzzySystem = None
            raise
    