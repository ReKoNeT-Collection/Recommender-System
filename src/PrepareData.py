import numpy as np
import pandas as pd
import pickle
import scipy.sparse as sparse
import implicit
import Recommender as rs
from pathlib import Path
import random as rd
import matplotlib.pyplot as plt
import requests


class PrepareData(object):
    def preapreFromFile(self, file):
        self.data = pd.read_csv(file, sep = ";")
        self.prepare()

    def prepareFromDF(self, df):
        self.data = df.copy()
        self.prepare()    

    def prepare(self):
        mTypes = self.getMachineTypes()
        #read in interactions and machines        
        self.dim_machine = pd.read_csv(mTypes, sep =";")

        # rename columns of interactions
        try:
            self.data.rename(columns={self.data.columns[0]:'Date', self.data.columns[1]:'WorkcenterID', self.data.columns[2]:'PartID', self.data.columns[3]:'Duration'}, inplace=True)
        except:
            print("Error: not able to read interactions. Bad format?4 columns needed")
            raise

        # rename columns of machinetypes
        try:
            self.dim_machine.rename(columns={self.dim_machine.columns[0]:'WorkcenterID',self.dim_machine.columns[1]:'Plant_Name', self.dim_machine.columns[2]:'PlantID', self.dim_machine.columns[3]:'WorkcenterNo', self.dim_machine.columns[5]:'WorkcenterType', self.dim_machine.columns[6]: 'GlobalTechnologyName'}, inplace=True)
        except:
            print("Error: not able to read machinesTypes. Bad format? 6 columns needed")
            raise            
          
        # prepare duration into numeric value
        self.data.Duration = self.data.Duration.str.replace(' MIN','')
        self.data.Duration = pd.to_numeric(self.data.Duration)

        # prepare dates into date format
        self.data.Date = self.data.Date.str.replace(r'\[\+\] ','')
        self.data.Date = pd.to_datetime(self.data.Date, format = '%m.%Y')

        #Merge interactions with types, too much loss by merging (missing type for an ID) will cause a warning
        curLen = len(self.data.index)
        self.interactions = pd.merge(self.data, self.dim_machine[['WorkcenterID', 'WorkcenterType', 'GlobalTechnologyName']], on='WorkcenterID')
        if len(self.interactions.index)/curLen < 0.9:
            print("WARNING: more than 10% data loss due to missing machinetypes to machine IDS. Please check the corresponding dictionariy data.")

        self.interactions = self.interactions[['WorkcenterType', 'PartID', 'GlobalTechnologyName', 'Duration']]

        #add column for interactions
        self.interactions['interaction'] = np.ones(self.interactions.shape[0])

        #aggregte data to meanvalues of duration
        self.interactions = self.interactions.groupby(['PartID', 'WorkcenterType', 'GlobalTechnologyName']).agg({'Duration':'mean', 'interaction':'sum'}).reset_index()

        #Ausschluss von Material-IDs die nur auf einem Maschinen-Typ gelaufen sind
        self.parts_considered = self.interactions.groupby(['PartID']).agg({'WorkcenterType':'nunique'})
        self.parts_considered = self.parts_considered.loc[self.parts_considered.WorkcenterType > 1].index.values
        self.interactions_small = self.interactions[self.interactions.PartID.isin(self.parts_considered)]


 ###Returns CSV Maschinetypes
    def getMachineTypes(self):
        ####try to get CSV internally
        try:
            response = requests.get("http://materials_api/MaschinenGruppen.csv")  
            #print(response.text)
            if response.text != '':
                f = open('MachineGroup.csv','w')
                f.write(response.text[3:]) #Give your csv text here.
                ## Python will convert \n to os.linesep
                f.close()


        except:
            print("loading data from internal system not successfull. Trying to load directly from local hard drive")
        
        #load locally
        vorhandene_maschinen = "MachineGroup.csv"
        #kostensatz ="Kostensatz.csv"

        return vorhandene_maschinen

    #derzeit lernt das System auf allen Werten
    def getInteractionTable(self):
        return self.interactions


