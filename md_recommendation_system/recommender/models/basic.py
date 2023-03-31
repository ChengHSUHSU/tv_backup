



from torch import nn





class BasicModel(nn.Module):    
    def __init__(self):
        super(BasicModel, self).__init__()
    
    def getUsersRating(self, users):
        raise NotImplementedError
    
    def getLoss(self, X, Y):
        raise NotImplementedError




