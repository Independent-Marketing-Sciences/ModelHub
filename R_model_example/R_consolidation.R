
# SETUP *************************************************************************************************************************************
# *******************************************************************************************************************************************

# This bit of code is only used when the user is debugging. Change depending on the user
userDir <- "C:/Users/David Lanham/OneDrive - im-sciences.com/Documents/RandExcelRegression"

# Set working directory from clipboard
wdDir <- readClipboard()
if (grepl("\\", paste(wdDir, " ", sep = ""), fixed = TRUE)) {
  setwd(wdDir)
} else {
  # No clipboard available (must be manual debugging). Use the user directory instead
  if (dir.exists(userDir)) {
    setwd(userDir)
  } else {    
    # error message
    winDialog("ok", paste("The given user directory does not exist; ", userDir, sep = ""))
    stop()
  }
}

print("Loading packages")

# Check if any packages are yet to be installed
my_packages <- c("tidyverse", "mgsub", "devtools", "readxl", "reshape2", "pivottabler")
not_installed <- my_packages[!(my_packages %in% installed.packages()[, "Package"])]
if (!(length(not_installed) == 0)) {
  errorMessage <- "Some required packages are yet to be installed on your computer"
} else {
  errorMessage <- ""
}

library("tidyverse")
library("mgsub")
library("devtools")
library("readxl")
library("reshape2")
library("pivottabler")
load_all('Package/lanzR')

# If there are missing packages, return error and terminate
if (errorMessage == "Some required packages are yet to be installed on your computer") {
  write.csv(errorMessage,"Cons_Output/errorMessage.csv", row.names = FALSE)
  stop()
}

print("Clear existing outputs")

# Empty existing output csvS
write.csv(NULL,"Cons_Output/contributionsDf.csv", row.names = FALSE)
write.csv(NULL,"Cons_Output/avmDf.csv", row.names = FALSE)
write.csv(NULL,"Cons_Output/errorMessage.csv", row.names = FALSE)
write.csv(NULL,"Cons_Output/newVariableDetails.csv", row.names = FALSE)
write.csv(NULL,"Cons_Output/medSpDf.csv", row.names = FALSE)

# READ IN LOOKUP TABLES **************************************************************************************************************************
source("Cons_Code/R_importLutsRawData.R")

# DYNAMIC VARIABLES; STEP 1 **********************************************************************************************************************
# ************************************************************************************************************************************************

modelDirectories <- unique(modelConsDetailsCsv$Directory) 
modelFileNames <- sub("^.+\\\\", "", modelDirectories)

# LOOP THROUGH AND READ IN MODELLING FILE OUTPUTS ************************************************************************************************
source("Cons_Code/R_importDecomps.R")

# DATA WRANGLING *********************************************************************************************************************************
source("Cons_Code/R_dataWrangling.R")

# # DL test - media split first
source("Cons_Code/R_splitContsByMedia.R")

# REATTRIBUTE NESTING *****************************************************************************************************************************
source("Cons_Code/R_reattributeNesting.R")

# PIVOT TABLE GENERATION **************************************************************************************************************************
source("Cons_Code/R_generatePivotTables.R")

# CALCULATE REVENUE AND MARGIN **********************************************************************************************************************
source("Cons_Code/R_calcRevenueMargin.R")

# # EXPORT MEDIA SPENDS *****************************************************************************************************************************
source("Cons_Code/R_exportMediaSpends.R")

# # FILTER AND EXPORT TABLES ***********************************************************************************************************************
source("Cons_Code/R_reduceAndExport.R")

rm(list = ls(all.names = TRUE)) #will clear all objects includes hidden objects.
gc() #free up memory and report the memory usage.
