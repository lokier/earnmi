from earnmi.model.CoreEngine import CoreEngine


class ProjectRunner():

    def __init__(self,engine:CoreEngine):
        self.coreEngine:CoreEngine = engine

    def onCreateProject(self):
        pass

    def runBackTest(self):
        pass


if __name__ == "__main__":
    pass

