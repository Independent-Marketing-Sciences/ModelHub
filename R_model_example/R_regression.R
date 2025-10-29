# SETUP *************************************************************************************************************************************
# *******************************************************************************************************************************************

# Suppress warnings
options(warn = -1) 

print("Loading packages")

library("lmtest")
library("tidyverse")
library("mgsub")
library("devtools")
library("tseries")
library("FinTS")
library("sandwich")
library("stringi")
library("car")
library("AEP")

# Set working directory from clipboard
wdDir <- readClipboard()
if (grepl("\\", paste(wdDir, " ", sep = ""), fixed = TRUE)) {
  setwd(wdDir)
} else {

  if (Sys.getenv("USERNAME") == "David Lanham") {
    setwd("C:/Users/David Lanham/OneDrive - im-sciences.com/Documents/RandExcelRegression")
  } else if (Sys.getenv("USERNAME") == "Huy Nguyen") {
    setwd("C:/Users/david/OneDrive/Documents/RandExcelRegression4.2.1") # to update
  } else if (Sys.getenv("USERNAME") == "AndreaRimondi") {
    setwd("C:/Users/AndreaRimondi/Documents/RModellingTool") # to update
  } else if (Sys.getenv("USERNAME") == "IlonaZasadzinska") {
    setwd("C:/Users/IlonaZasadzinska/Documents/R modelling tool") # to update
    # etc.
  }  else if (Sys.getenv("USERNAME") == "Luke Hamilton") {
    setwd("C:/Users/Luke Hamilton/Documents/R Modelling Tool") # to update
    # etc.
  } else if (Sys.getenv("USERNAME") == "vmadmin") {
    setwd("C:/Users/vmadmin/Documents/RModellingTooll") # to update
    # etc.
  } else if (Sys.getenv("USERNAME") == "DanielHallsworth") {
    setwd("C:/Users/DanielHallsworth/Documents/R Modelling Tool") # to update
    # etc.
  }
}

load_all('Package/lanzR')

# Importing Data
print("1. Importing Data");source("Regression Scripts/Importing Data.R")

# Data Preparation
print("2. Data Preparation");source("Regression Scripts/Data Preparation.R")

# Variable Transformations
print("3. Variable Transformations");source("Regression Scripts/Variable Transformations.R")

# Regression Setup
print("4. Regression Setup");source("Regression Scripts/Regression Setup.R")


if(regApproach != "bayesian") {
  
  # Frequentist Regression
  print("5. Regression");source("Regression Scripts/OLSRegression.R")
  
  # Diagnostic Tests
  print("5.2. Diagnostic Tests");source("Regression Scripts/Diagnostic Tests.R")
  
} else {
  
  # Libraries
  library("brms")
  library("rstan")
  library("parallel")
  library("bayestestR")
  library("reticulate")
  
  # Bayesian Regression
  print("5. Regression");source("Regression Scripts/BAYRegression.R")
  
}

# Contributions & Model Outputs
print("6. Model Decomp");source("Regression Scripts/Model Decomp.R")

# Post Modeling Analysis
print("7. Post Modelling Analysis");source("Regression Scripts/Post Modelling Analysis.R")

# Export (bulk) ***********************************************************************************************************************************
# *************************************************************************************************************************************************

rm(modelDetailsCsv, xsDetailsCsv, VariableDetailsCsv, redRawVarData, transVarByXsDataLong,  modelDw, modelFit, modVarCode,
   obsCnt)
rm(identVarName, kpiVarName, modelledVarNames)

print("Writing outputs")
                       
# Export Outputs
write.csv(avmDetailsXsDf,"RegressionTables/avmDetailsXsDf.csv", row.names = FALSE)
write.csv(avmDetailsTotDf,"RegressionTables/avmDetailsTotDf.csv", row.names = FALSE)
write.csv(varContsXsDf,"RegressionTables/VarContsXsDf.csv", row.names = FALSE)
write.csv(varContsTotDf,"RegressionTables/varContsTotDf.csv", row.names = FALSE)
write.csv(catContsXsDf,"RegressionTables/catContsXsDf.csv", row.names = FALSE)
write.csv(catContsTotDf,"RegressionTables/catContsTotDf.csv", row.names = FALSE)
write.csv(regVariableDetailsDf,"RegressionTables/VariableDetails.csv", row.names = FALSE)
write.csv(regVarDetailsStackedDf,"RegressionTables/regVarDetailsStackedDf.csv", row.names = FALSE)
write.csv(modelDetailsDf,"RegressionTables/modelDetails.csv", row.names = TRUE)
write.csv(regCatStatsDf,"RegressionTables/regCatStatsDf.csv", row.names = FALSE)
write.csv(prevRunDetails,"RegressionTables/prevRunDetails.csv", row.names = FALSE)
write.table(modelPermSummary, "RegressionTables/permSummary.csv", row.names = FALSE, col.names = FALSE, sep=",") # write.table needed to remove col names

rm(list = ls(all.names = TRUE)) #will clear all objects includes hidden objects.
gc() #free up memory and report the memory usage.
