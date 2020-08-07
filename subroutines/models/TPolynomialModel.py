# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 15:06:55 2019

Polynomial Regression Class

@author: Dr. Dr. Danny E. P. Vanpoucke
@web   : https://dannyvanpoucke.be
"""
import pandas as pd
from TModelClass import TModelClass
import numpy as np
from TModelResults import TModelResults
from Bootstrap import TBootstrap
from TModelQualityData import TModelQualityData
from sklearn.pipeline import Pipeline

class TPolynomialModel(TModelClass):
    """
    Child class representing the Polynomial regression model
    """
    def __init__(self,name,Target, Feature: pd.DataFrame, 
                 Target_test, Feature_test: pd.DataFrame,
                 Pipeline: Pipeline,
                 EnsemblePipeline: Pipeline,
                 Degree: int=2, Interaction: bool=False, Bias: bool=True):
        """
        Constructor to set up a polynomial model.
    
        parameters:
         - name : the name of the object instance
         - Feature : The features to use & transform
         - Target     : the training target data
         - Target_test: the test target data
         - Feature_test: the untransformed features for testing.
         - Pipeline : a pipeline generated by the PipelineFactory
         - EnsemblePipeline : the pipeline generated by the PipelineFactory for the entire ensemble dataset
         - Degree  : The polynomial degree (integer), DEFAULT=2
         - Interaction : Boolean variable indicating if ONLY interaction terms are included in the 
                     polynomial features (True) or that all terms are included (False), DEFAULT=False
         - Bias    : Boolean indicating if a bias column is added (i.e. where all powers 
                      are zero, acts as intercept in linear model). [DEFAULT = True]
     
        It sets the following properties
         - pipeline : a pipeline object containing the preprocessing transformations (excluding the fitter function)
         - model    : the fitter function to be used (should be an sklearn function with "fit" method)
         - feature_tf: the transformed features as obtained by the pipeline    
        """
        #from sklearn.preprocessing import StandardScaler
        #from sklearn.preprocessing import PolynomialFeatures
        from sklearn.linear_model import LinearRegression
        
        super().__init__(name,Target, Feature,Target_test, Feature_test)
        self.nameModel='Polynomial Model'
        self.name=name
        print("Initialising the child class:",self.nameModel)
        #create a pipeline (can be extended to contain more functions, p67)
        self.pipeline = Pipeline
        self.EnsPipe = EnsemblePipeline
#        Pipeline([
#            ('poly_features',PolynomialFeatures(degree=Degree,interaction_only=Interaction ,include_bias=Bias)),# polynamial terms up to degree 3, and no bias column (this would be intercept in case of linear fit)
#            ('std_scaler', StandardScaler(with_mean=False, with_std=False)),#a standard scaler which does nothing
#            #('std_scaler', StandardScaler()),  #scaling to be centered on 0, with unit variance...since the values are quite different, this will help things
#        ]) #don't include the fitter
        self.feature_tf = self.pipeline.fit_transform(Feature) #this is a numpy array...
        self.model = LinearRegression(fit_intercept=True, normalize=False, copy_X=True, n_jobs=None) #default values..explicitly set
        
        
    def fitSanityCheck(self)-> int:
        """
        Class method which should cover/deal with failures of sklearn.
        
        For some reason, sklearn LinearRegression randomly fails on small datasets.
        Since polynomial regression is just an extension build on top of a linear-regression 
        the same issues are expected to pop up.
        This failure gives rise to huge coefficents. Hoever, just shuffling the 
        data seems to resolve the issue.
        
        This function returns the number of shuffles needed to regain sanity.
        """
        import sys
        #first find out if we have "infinite" coefficients
        cnt=0
        insane=(abs(sum(self.model.coef_)/len(self.model.coef_))>1.0E9) #larger than 1 billion should be a clear sign
        while (insane and (cnt<100)): #try up to 100x ... if non are OK, then it will never be fixed
            cnt+=1
            #then we shuffle the features & targets...
            #1) recombine in 1 pandas dataframe
            combo=pd.concat([self.feature,self.target], axis=1, sort=False, join='outer')
            #2) shuffle: https://stackoverflow.com/questions/29576430/shuffle-dataframe-rows
            combo=combo.sample(frac=1).reset_index(drop=True)
            #3) re-store in target/feature/feature_tf
            self.target=combo[combo.columns[-1]].copy()
            self.feature=combo.drop(combo.columns[-1],axis=1)
            self.feature_tf = self.pipeline.fit_transform(self.feature) #this is a numpy array...
            #4) finally refit
            self.fit()
            insane=(abs(sum(abs(self.model.coef_))/len(self.model.coef_))>self.sanityThresshold)
             
        if (cnt>0):#update the coefficients
            self.setCoefficients()
            
        if insane:
            print("EPIC FAIL, 100 attempts at sanity failed in the ",self.name,". Terminating this sick job!")
            sys.exit()
        
        return cnt

##serial        
#    def setAverageCoefficients(self, EnsembleData: TModelResults, setCI: bool):
#        """
#        Use the ensemble data to create an "average" model, and set the "coefficients"
#        in the current model. This should be performed in each model separately
#        """
#        #import time
#        
#        # 1. Calculate the average coefficients
#        # 1.1. transform them to arrays
#        #start = time.perf_counter_ns()
#        #print("3.1) Average Coefficients : AVG")
#        intercept=np.zeros(EnsembleData.NData)
#        coef=np.zeros((EnsembleData.NData,EnsembleData.modelCoef[0]['coef_'][1].shape[1]))
#        for i in range(EnsembleData.NData):
#            mcf=EnsembleData.modelCoef[i]
#            intercept[i]=np.asarray(mcf['intercept_'][1]).ravel()
#            coef[i,:]=np.asarray(mcf['coef_'][1]).ravel()
#            print(i,")",coef[i,:])
#            
#        mean_intercept=np.mean(intercept,axis=0)#axis is the varying direction, so 0 means we calculate the average of a column by varying the row
#        mean_coef=np.mean(coef,axis=0) 
#        print("MEANS=> Int=",mean_intercept,"  COEF=",mean_coef)
#        # 2. Set the model coefficients to these averaged values
#        self.model.intercept_=mean_intercept
#        self.model.coef_=mean_coef
#        self.isAverage = True
#        self.hasCI=False
#        if setCI:
#            #end = time.perf_counter_ns()
#            #print("3.2.a) Average Coefficients : CI Intercept ",(end-start)/10E9)
#            # 3. Calculate Confidence Interval using Bootstrapper tech?
#            # & 4. Store the CI data
#            ## For the intercept
#            boot=TBootstrap(data=intercept,Func=np.mean)
#            #end = time.perf_counter_ns()
#            #print("3.2.b) NPboot",(end-start)/1E9)
#            boot.NPbootstrap(n_iter=2000, Jackknife=True)
#            #end = time.perf_counter_ns()
#            #print("3.2.c) Con Int",(end-start)/1E9)
#            avgm, avgp = boot.ConfidenceInterval(CItype="BCa",alpha=0.05,n_samples=2000)#95%confidence interval
#            self.CI["intercept_lo"]=avgm
#            self.CI["intercept_hi"]=avgp
#            ## For the coefficients
#            avgml=list()
#            avgpl=list()
#            for col in range(EnsembleData.modelCoef[0]['coef_'][1].shape[1]):
#                #end = time.perf_counter_ns()
#                #print("3.2) Average Coefficients : CI Coef ",col," ",(end-start)/1E9)
#                boot=TBootstrap(data=coef[:,col],Func=np.mean)
#                boot.NPbootstrap(n_iter=2000, Jackknife=True)
#                avgm, avgp = boot.ConfidenceInterval(CItype="BCa",alpha=0.05)#95%confidence interval
#                avgml.append(avgm)
#                avgpl.append(avgp)
#                
#            self.CI["coef_lo"]=avgml
#            self.CI["coef_hi"]=avgpl
#            self.hasCI = True
#            
#        #store the resulting coefficients in our wrapper tracker...and we are done
#        self.setCoefficients()
#        self.Quality=TModelQualityData(EData=EnsembleData)



    #Important note: onle one pre-underscore is allowed, otherwise python does not find this function
    def _BootstrapAvg_1Col(self,col:int, coeflst:list, alpha:float)->tuple:
        """
        Single line parallellizable bootstrap for a column of coefficients.
        
        parameters:
            - col: the index of the column (for administrative purposes upon return)
            - coeflst: the list of coefficients
            - alpha: the BCa alpha value for the CI, default=0.05
        return:
            tuple(col-index, CIlow, CIhigh)
        """
        #print("$$$$$$$$$$$$$$$ boot1 col=",col)
        boot=TBootstrap(data=coeflst,Func=np.mean)
        boot.NPbootstrap(n_iter=2000, Jackknife=True)
        avgm, avgp = boot.ConfidenceInterval(CItype="BCa",alpha=alpha)#95%confidence interval
        
        return tuple([col,avgm,avgp])
     
#parallel        
    def setAverageCoefficients(self, EnsembleData: TModelResults, setCI: bool):
        """
        Use the ensemble data to create an "average" model, and set the "coefficients"
        in the current model. This should be performed in each model separately
        """
        import multiprocessing as mp
        from HPCTools import get_num_procs
        
        # 1. Calculate the average coefficients
        # 1.1. transform them to arrays
        #start = time.perf_counter_ns()
        #print("3.1) Average Coefficients : AVG")
        intercept=np.zeros(EnsembleData.NData)
        coef=np.zeros((EnsembleData.NData,EnsembleData.modelCoef[0]['coef_'][1].shape[1]))
        for i in range(EnsembleData.NData):
            mcf=EnsembleData.modelCoef[i]
            intercept[i]=np.asarray(mcf['intercept_'][1]).ravel()
            coef[i,:]=np.asarray(mcf['coef_'][1]).ravel()
            print(i,")",coef[i,:])
            
        mean_intercept=np.mean(intercept,axis=0)#axis is the varying direction, so 0 means we calculate the average of a column by varying the row
        mean_coef=np.mean(coef,axis=0) 
        print("MEANS=> Int=",mean_intercept,"  COEF=",mean_coef)
        # 2. Set the model coefficients to these averaged values
        self.model.intercept_=mean_intercept
        self.model.coef_=mean_coef
        self.isAverage = True
        self.hasCI=False
        if setCI:
            #end = time.perf_counter_ns()
            #print("3.2.a) Average Coefficients : CI Intercept ",(end-start)/10E9)
            # 3. Calculate Confidence Interval using Bootstrapper tech?
            # & 4. Store the CI data
            ## For the intercept
            boot=TBootstrap(data=intercept,Func=np.mean)
            #end = time.perf_counter_ns()
            #print("3.2.b) NPboot",(end-start)/1E9)
            boot.NPbootstrap(n_iter=2000, Jackknife=True)
            #end = time.perf_counter_ns()
            #print("3.2.c) Con Int",(end-start)/1E9)
            avgm, avgp = boot.ConfidenceInterval(CItype="BCa",alpha=0.05,n_samples=2000)#95%confidence interval
            self.CI["intercept_lo"]=avgm
            self.CI["intercept_hi"]=avgp
            ## For the coefficients
            # Parallelisation for sections performing bootstraps. 
            # Parallelization at the highest level of a column, 
            # ??Is the overhead sufficiently low to have benefits?
            # 1. create our process pool with as many processes as physical cores
            pool=mp.Pool(processes=get_num_procs(-1))
            # 2. set drones to work
            alpha=0.05 #95%confidence interval
            drones=[pool.apply_async(self._BootstrapAvg_1Col, args=(col,coef[:,col],alpha)) for col in range(EnsembleData.modelCoef[0]['coef_'][1].shape[1])]
            # 3. as we can not assume the cols to be produced in the correct order
            #    --> make it a dict
            ciDict=dict()
            for drone in drones:
                col,avgm,avgp=drone.get()
                ciDict[col]=list([avgm,avgp])
            # 4. wait untill all processes are finished
            pool.close()
            pool.join()
            # 5. and put then in the corrcet order in the list        
            avgml=list()
            avgpl=list()
            for col in range(EnsembleData.modelCoef[0]['coef_'][1].shape[1]):
                avgml.append(ciDict[col][0])
                avgpl.append(ciDict[col][1])
                           
            self.CI["coef_lo"]=avgml
            self.CI["coef_hi"]=avgpl
            self.hasCI = True
            
        #store the resulting coefficients in our wrapper tracker...and we are done
        self.setCoefficients()
        self.Quality=TModelQualityData(EData=EnsembleData)

    
    def printAverageCoefficients(self, File: str=None):
        """
        Print a block of information to a file, containing the averaged coefficients for the 
        polynomial model.
        
        parameters:
            - self:
            - File: string containing a filename, if None standard output is used. Default=None
        """
        coefstr=list()
        
        pipeline=None
        for name, step in self.EnsPipe.steps:
            if (name == 'poly_features'):
                pipeline=self.EnsPipe
        if pipeline==None:
            for name, step in self.pipeline.steps:
                if (name == 'poly_features'):
                    pipeline=self.pipeline
        
        for i in range(pipeline['poly_features'].powers_.shape[0]):
            line="("
            for j in range(pipeline['poly_features'].powers_.shape[1]):
                pw=pipeline['poly_features'].powers_[i,j]
                if (pw != 0):
                    line=line+"x_"+str(j)+"^"+str(pw)
            line=line+")"
            if len(line)==2: #so this term is missing
                line="(1)"
            coefstr.append(line)
        
        if File is None:
            print("======= THE AVERAGED MODEL ==============")
            print(" Model : ",self.name)
            print(self.Quality.QualitiesText())
            if self.hasCI:
                print("Intercept  : ",self.model.intercept_," and CI=[",self.CI["intercept_lo"]," ; ",self.CI["intercept_hi"],"]")
                for col in range(len(self.model.coef_)):
                    print("coef ",coefstr[col]," : ",self.model.coef_[col]," and CI=[",self.CI["coef_lo"][col]," ; ",self.CI["coef_hi"][col],"]")
            else:
                print("Intercept  : ",self.model.intercept_)
                for col in range(len(self.model.coef_)):
                    print("coef ",coefstr[col]," : ",self.model.coef_[col])
            print("====================================\n\n")
        else:
            foo=open(File,"a+",)
            foo.write("======= THE AVERAGED MODEL ==============\n")
            line=" Model : "+self.name+"\n"
            foo.write(line)
            foo.write(self.Quality.QualitiesText())
            if self.hasCI:
                line="Intercept  : "+str(self.model.intercept_)+" and CI=["+str(self.CI["intercept_lo"])+" ; "+str(self.CI["intercept_hi"])+"] \n"
                foo.write(line)
                for col in range(len(self.model.coef_)):
                    line="coef "+coefstr[col]+" : "+str(self.model.coef_[col])+" and CI=["+str(self.CI["coef_lo"][col])+" ; "+str(self.CI["coef_hi"][col])+"] \n"
                    foo.write(line)
            else:
                line="Intercept  : "+str(self.model.intercept_)+"\n"
                foo.write(line)
                for col in range(len(self.model.coef_)):
                    line="coef "+coefstr[col]+" : "+str(self.model.coef_[col])+"\n"
                    foo.write(line)
            foo.write("====================================\n\n")
            foo.close()
    
    def setCoefficients(self):
        """
        Class-method printing the fitting coefficients for a polynomial regression
        """
        import numpy as np
        super().setCoefficients()
        self.modelcoef['header_coef']=[self.coefindex,"The coefficients for each target (one per row) are given by:"]
        self.modelcoef['coef_']=[self.coefindex+1,np.array([self.model.coef_])]
        self.modelcoef['header_intercept']=[self.coefindex+2,"The intercepts for each target (one per row) are given by:"]
        self.modelcoef['intercept_']=[self.coefindex+3,np.array([self.model.intercept_])]
        self.coefindex+=4