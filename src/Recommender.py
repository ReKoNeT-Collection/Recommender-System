import numpy as np
import pandas as pd
import scipy.sparse as sparse
import implicit
from pathlib import Path

import requests
import random as rd


class RecommenderObject:
    model = None
    interactions = None
    
    workcenters = None
    
    id2workcenters = None
    workcenters2id = None

    workcenter_part = None
    part_workcenter = None
    id2parts = None
    parts2id = None

    def getValues(self, dict_, keys):
        return [dict_[k] for k in keys]


    def prepare(self):
        workcenters = pd.unique(self.interactions.WorkcenterType)

        self.id2workcenters = dict(zip(np.arange(0,workcenters.shape[0]), workcenters))
        self.workcenters2id = dict(zip(workcenters, np.arange(0,workcenters.shape[0])))
        
        # parts ID Transformation
        parts = pd.unique(self.interactions.PartID)
        self.id2parts = dict(zip(np.arange(0,parts.shape[0]), parts))
        self.parts2id = dict(zip(parts, np.arange(0,parts.shape[0])))
        
        # create csrdata
        self.workcenter_part = sparse.csr_matrix( (self.interactions['interaction'],
                           (self.getValues(self.workcenters2id, self.interactions['WorkcenterType']),
                            self.getValues(self.parts2id, self.interactions['PartID']))),
                           shape = (workcenters.shape[0], parts.shape[0]))

        self.part_workcenter = self.workcenter_part.T.tocsr()
    
    #not working
    # def similar_users(self, part, N = 6):
    #     partID = self.parts2id[part]
    #     similarusers = self.model.similar_users(partID, N)
    #     #return(similarusers)
    #     similarusers = [(self.id2parts[sim[0]], sim[1]) for sim in similarusers]        
    #     return similarusers

    # currently not working 
    # def similar_items(self, machine, N = 6):
    #     machineID = self.workcenters2id[machine]
    #     similaritems = self.model.similar_items(machineID, N)
    #     #return(similaritems)
    #     similaritems = [ (self.id2workcenters[sim[0]], sim[1]) for sim in similaritems]
    #     return similaritems

class Recommender:
    
    def getValues(self, dict_, keys):
        return [dict_[k] for k in keys]

    def __getModel(self):
        return self.__model

    model = property(__getModel)

    def recommend(self, part, N = 5):
        #translate Part-ID
        partID = self.parts2id[part]
        #recommend
        recommendation = self.model.recommend(partID, self.part_workcenter, N)        
        #translate recommendation
        recommendation = [ (self.id2workcenters[rec[0]], rec[1]) for rec in recommendation]        
        return recommendation
 
    def train(self, interactions, factors = 10, show_progress=True):
        self.interactions = interactions

        # workcenter ID Transformation
        workcenters = pd.unique(self.interactions.WorkcenterType)
        self.id2workcenters = dict(zip(np.arange(0,workcenters.shape[0]), workcenters))
        self.workcenters2id = dict(zip(workcenters, np.arange(0,workcenters.shape[0])))
        
        # parts ID Transformation
        parts = pd.unique(self.interactions.PartID)
        self.id2parts = dict(zip(np.arange(0,parts.shape[0]), parts))
        self.parts2id = dict(zip(parts, np.arange(0,parts.shape[0])))
        
        # create csrdata
        self.workcenter_part = sparse.csr_matrix( (self.interactions['interaction'],
                           (self.getValues(self.workcenters2id, self.interactions['WorkcenterType']),
                            self.getValues(self.parts2id, self.interactions['PartID']))),
                           shape = (workcenters.shape[0], parts.shape[0]))

        self.part_workcenter = self.workcenter_part.T.tocsr()
        # sparse.csr_matrix( (self.interactions['interaction'],
        #                    (self.getValues(self.parts2id, self.interactions['PartID']),
        #                     self.getValues(self.workcenters2id, self.interactions['WorkcenterType']))),
        #                    shape = (parts.shape[0], workcenters.shape[0]))
                
        #train model
        self.__model = implicit.als.AlternatingLeastSquares(factors, regularization=20)    
        self.__model.fit(self.workcenter_part, show_progress)

    def similar_users(self, part, N = 6):
        partID = self.parts2id[part]
        similarusers = self.model.similar_users(partID, N)
        #return(similarusers)
        similarusers = [(self.id2parts[sim[0]], sim[1]) for sim in similarusers]        
        return similarusers

    def similar_items(self, machine, N = 6):
        machineID = self.workcenters2id[machine]
        similaritems = self.model.similar_items(machineID, N)
        #return(similaritems)
        similaritems = [ (self.id2workcenters[sim[0]], sim[1]) for sim in similaritems]
        return similaritems

class RecommenderByTech:

    model_mill = RecommenderObject()
    modell_turn = RecommenderObject()
    
    def train(self, interactions, factors = 10, show_progress=True):     
        self.interactions = interactions
        self.model_mill.interactions = interactions[interactions["GlobalTechnologyName"]=="Milling"]
        self.modell_turn.interactions = interactions[interactions["GlobalTechnologyName"]=="Turning"]

        self.model_mill.prepare()
        self.modell_turn.prepare()

        #train model for Milling
        self.model_mill.model = implicit.als.AlternatingLeastSquares(factors, regularization=20)    
        self.model_mill.model.fit(self.model_mill.workcenter_part, show_progress)     
        #train model for Turning
        self.modell_turn.model = implicit.als.AlternatingLeastSquares(factors, regularization=20)    
        self.modell_turn.model.fit(self.modell_turn.workcenter_part, show_progress)     
        
    ###Recommendation now consists of recommendation of never used machies [0] and similar materials [1]
    def recommend(self, part, N = 5, techProvided = 0):
        #Filter data down to the Part and have a count of the technology use. If Milling has more entries then turning it is highly probable a milling part
        df = self.interactions.groupby(['PartID', 'GlobalTechnologyName']).agg(['count']).reset_index()
        df2 = df[df['PartID']==part]
        s_model = None

        #It is now possible to tell the recommender which technology it should use
        if techProvided > 0:
            if techProvided == 1:
                s_model = self.model_mill
            else:
                s_model = self.modell_turn
        else:
            #PartID nicht enthalten
            if df2.shape[0] == 0:
                raise Exception
            
            #PartID nutzt nur eine Technologie
            if df2.shape[0] == 1:
                if df2.iloc[0, 1] == 'Milling':
                    s_model = self.model_mill
                else:
                    s_model = self.modell_turn
            #more then 1 Technology in entries
            elif df2.iloc[0, 2] > df2.iloc[1, 2]: #Milling? Yes Milling is always first
                s_model = self.model_mill         
            else:
                s_model = self.modell_turn

        #translate Part-ID
        partID = s_model.parts2id[part]
        #recommend
        recommendation = s_model.model.recommend(partID, s_model.part_workcenter, N)                
        #translate recommendation
        recommendation = [ (s_model.id2workcenters[rec[0]], rec[1]) for rec in recommendation]
        
        similarusers = s_model.model.similar_users(partID, N)

        similarusers = [(s_model.id2parts[sim[0]], sim[1]) for sim in similarusers]      

        res = np.array([recommendation, similarusers])
        return res

