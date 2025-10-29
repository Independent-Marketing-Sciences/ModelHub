
print("Data Wrangling")

# CONVERT ALL TABLES TO LOWER CASE ***************************************************************************************************************
# ************************************************************************************************************************************************

modelConsDetailsCsv <- to.lower.db(modelConsDetailsCsv)
obsDetailsCsv <- to.lower.db(obsDetailsCsv)
toplineDetailsCsv <- to.lower.db(toplineDetailsCsv)
varConsDetailsCsv <- to.lower.db(varConsDetailsCsv)
mediaDetailsCsv <- to.lower.db(mediaDetailsCsv)
rawInputCsv <- to.lower.db(rawInputCsv)
varContsDb <- to.lower.db(varContsDb)
avmDb <- to.lower.db(avmDb)
mediaByXsDetails <- to.lower.db(mediaByXsDetails)

rawInputCsv <- rawInputCsv %>% `colnames<-`(tolower(colnames(rawInputCsv)))

# CONVERT ANY NUMBER DATES TO DATES ***************************************************************************************************************
# ************************************************************************************************************************************************

for (x in 1:ncol(obsDetailsCsv)) {
  if (class(obsDetailsCsv$OBS)[1] != "Date") {
    if ((obsDetailsCsv[1, x] >= 30000) & (obsDetailsCsv[1, x] <= 60000)) {
      obsDetailsCsv[,x] <- as.Date(obsDetailsCsv[,x], origin = "1899-12-30")
    }
  }
}

# Convert OBS to date, removing any UTC reference
if (class(varContsDb$OBS)[1] != "Date") {
  if ((varContsDb$OBS[1] >= 30000) & (varContsDb$OBS[1] <= 60000)) {
    varContsDb$OBS <- as.Date(varContsDb$OBS, origin = "1899-12-30")
  }
}

if (class(avmDb$OBS)[1] != "Date") {
  if ((avmDb$OBS[1] >= 30000) & (avmDb$OBS[1] <= 60000)) {
    avmDb$OBS <- as.Date(avmDb$OBS, origin = "1899-12-30")
  }
}

varContsDb$OBS <- as.Date(varContsDb$OBS)  
avmDb$OBS <- as.Date(avmDb$OBS)

# Attach on the model name (note - definition of model here is akin to cross section within panel data models)

varContsDb <- cbind(KPI.Name = modelConsDetailsCsv$KPI.Name[
  match(paste(varContsDb$fileName, "|", varContsDb$CrossSection, sep = ""), 
        paste(modelConsDetailsCsv$fileName, "|", modelConsDetailsCsv$CrossSection, sep = ""))], 
  varContsDb)

# Check if any of the cross section names is incorrectly labelled
if (NA %in% varContsDb$KPI.Name) {
  mislabelledFileName <- varContsDb[match(NA, varContsDb$KPI.Name), "fileName"]
  errorMessage <- paste("At least one of the cross sections is incorrectly labelled in the Model Details tab for the following model file; ", 
                        mislabelledFileName, sep = "")
  write.csv(errorMessage,"Cons_Output/errorMessage.csv", row.names = FALSE)
  stop()
}

# unique(modelConsDetailsCsv$CrossSection) %in% unique(varContsDb$CrossSection)


avmDb <- cbind(KPI.Name = modelConsDetailsCsv$KPI.Name[
  match(paste(avmDb$fileName, "|", avmDb$CrossSection, sep = ""), 
        paste(modelConsDetailsCsv$fileName, "|", modelConsDetailsCsv$CrossSection, sep = ""))], 
  avmDb)

# Left joining LUTs *******************************************************************************************************************************
# *************************************************************************************************************************************************

varContsDb <- merge(x=varContsDb, y=subset(modelConsDetailsCsv, select = -c(CrossSection, fileName)), by.x = "KPI.Name", by.y = "KPI.Name")
varContsDb <- merge(x=varContsDb, y=obsDetailsCsv, by.x = "OBS", by.y = "OBS")
varContsDb <- merge(x=varContsDb, y=varConsDetailsCsv, by.x = "variable", by.y = "Variable.Name")

avmDb <- merge(x=avmDb, y=subset(modelConsDetailsCsv, select = -c(CrossSection, fileName)), by.x = "KPI.Name", by.y = "KPI.Name")
avmDb <- merge(x=avmDb, y=obsDetailsCsv, by.x = "OBS", by.y = "OBS")

# Sort Db by columns ******************************************************************************************************************************
# *************************************************************************************************************************************************

varContsDb <- varContsDb[with(varContsDb, order(KPI.Name, variable, OBS)),]
avmDb <- avmDb[with(avmDb, order(KPI.Name, OBS)),]
