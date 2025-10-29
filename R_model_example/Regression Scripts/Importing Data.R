print("1.1 Clear existing outputs")

# Empty existing output csvS
write.csv(NULL,"RegressionTables/avmDetailsXsDf.csv", row.names = FALSE)
write.csv(NULL,"RegressionTables/avmDetailsTotDf.csv", row.names = FALSE)
write.csv(NULL,"RegressionTables/VarContsXsDf.csv", row.names = FALSE)
write.csv(NULL,"RegressionTables/varContsTotDf.csv", row.names = FALSE)
write.csv(NULL,"RegressionTables/catContsXsDf.csv", row.names = FALSE)
write.csv(NULL,"RegressionTables/catContsTotDf.csv", row.names = FALSE)
write.csv(NULL,"RegressionTables/VariableDetails.csv", row.names = FALSE)
write.csv(NULL,"RegressionTables/modelDetails.csv", row.names = TRUE)
write.csv(NULL,"RegressionTables/regVarDetailsStackedDf.csv", row.names = FALSE)
write.csv(NULL,"RegressionTables/regCatStatsDf.csv", row.names = FALSE)
write.csv(NULL,"RegressionTables/RawInput.csv", row.names = FALSE)
write.csv(NULL,"RegressionTables/residualCorr.csv", row.names = FALSE)
write.csv(NULL,"RegressionTables/responseCurves.csv", row.names = FALSE)
write.csv(NULL,"RegressionTables/permSummary.csv", row.names = FALSE)
write.csv(NULL,"RegressionTables/transVarByXsLongDf.csv", row.names = FALSE)

# READ IN DATA ***********************************************************************************************************************************
# ************************************************************************************************************************************************

print("1.2 Importing Data")

modelDetailsCsv <- read.csv("Input/modelDetailsCsv.csv", stringsAsFactors = FALSE) %>%
  mutate(Detail = tolower(Detail))
xsDetailsCsv <- read.csv("Input/xsDetailsCsv.csv", stringsAsFactors = FALSE)

# Get rid of any blank lines that are read in after the last Cross Section
if (!(match("", xsDetailsCsv$CrossSection) %in% NA)) { 
  xsDetailsCsv <- xsDetailsCsv[1:(match("", xsDetailsCsv$CrossSection)-1),]
}

# Get rid of any blank columns that are read in after the last Cross Section
xsDetailsCsv[is.na(xsDetailsCsv)] = ""
if (!(match("", xsDetailsCsv[1, ]) %in% NA)) { 
  xsDetailsCsv <- xsDetailsCsv[ , 1:(match("", xsDetailsCsv[1, ])-1)]
}

xsDetailsCsv <- lapply(1:ncol(xsDetailsCsv), function(x) tolower(xsDetailsCsv[, x])) %>% # convert XS ident to lower case
  do.call(cbind, .) %>%
  as.data.frame(stringsAsFactors = FALSE) %>%
  `colnames<-`(tolower(colnames(xsDetailsCsv)))
VariableDetailsCsv <- read.csv("Input/VariableDetailsCsv.csv", stringsAsFactors = FALSE, fileEncoding="latin1") %>%
  mutate(Variable = tolower(Variable)) %>%
  mutate(XS.Grouping = tolower(XS.Grouping)) %>%
  mutate(Reference.Point = tolower(Reference.Point)) %>%
  mutate(Variable = gsub(" ", "", Variable)) %>% # get rid of any spaces
  mutate(Variable = gsub(",f)", ",F)", Variable)) %>% # False or True argument will only work if in caps, otherwise text
  mutate(Variable = gsub(",t)", ",T)", Variable))
modelDetailsCsv <- modelDetailsCsv[,1:2] # Cut unused rows and columns (if there are any)
VariableDetailsCsv <- VariableDetailsCsv[,1:12]

# Get rid of any lines after a blank in the variables (within Variable Details)
if (!(match("", VariableDetailsCsv$Variable) %in% NA)) {
  VariableDetailsCsv <- VariableDetailsCsv[1:(match("", VariableDetailsCsv$Variable)-1),]
}

# Format the min and max coefficient columns as number
VariableDetailsCsv <- VariableDetailsCsv %>% 
  transform(Coeff.Min = as.numeric(Coeff.Min), 
            Coeff.Max = as.numeric(Coeff.Max))

# Clear any rows for which the min and max coefficient are zero
VariableDetailsCsv <- VariableDetailsCsv[!(coalesce(VariableDetailsCsv$Coeff.Max == 0 & VariableDetailsCsv$Coeff.Min == 0, F)), ]

# Add in a placeholder piping permutation if there are none (to save rewriting code below)
if ((all(is.na(VariableDetailsCsv$Substitution))) | (paste(VariableDetailsCsv$Substitution, collapse = '') == "")) {
  VariableDetailsCsv[1, "Substitution"] <- "¬0(0)"
}

# Get the name of the KPI
kpiVarName <- modelDetailsCsv[modelDetailsCsv$Metric == "KPI Name", "Detail"]

prevRunDetails = read.csv("RegressionTables/prevRunDetails.csv", stringsAsFactors = FALSE)
prevRunTimeStamp <- prevRunDetails[1,1]
prevRunKpi <- prevRunDetails[1,2]
# Overwrite to  - so if the code crashes out, we know to re-import raw data fully in the next run
write.csv(matrix("crash run", 2, 2),"RegressionTables/prevRunDetails.csv", row.names = FALSE)

# Look up timestamp of the Raw Data Import being used in current model
rawDataTimestamp <- file.info(modelDetailsCsv[modelDetailsCsv$Metric == "Raw Data Directory", "Detail"])$mtime

# Check if the timestamps between this raw data and previous raw data are different
if (as.character(rawDataTimestamp)!=prevRunTimeStamp | kpiVarName!=prevRunKpi) {
  
  # The timestamps are different - raw data could be different
  
  # Import Raw Data from csv (takes a bit longer)
  RawInputCsv = read.csv(modelDetailsCsv[modelDetailsCsv$Metric == "Raw Data Directory", "Detail"], stringsAsFactors = FALSE, fileEncoding="UTF-8-BOM")
  RawInputCsv[is.na(RawInputCsv)] <- 0 # replace blanks with zeros, otherwise adstocking issues later
  names(RawInputCsv) <- tolower(names(RawInputCsv)) # Convert headers to lower case 
  
  # Save Raw Data in Library
  saveRDS(RawInputCsv, file = "RegressionTables/rawDataLibrary")
  
  # clear historic transformed data
  saveRDS(NULL, file = "RegressionTables/transformedDataLibrary")
  transformedDataLibrary <- NULL
  
} else {
  
  # The timestamps are the same - full reimport not required
  
  # Import Raw Data from rds (much quicker)
  RawInputCsv <- readRDS(file = "RegressionTables/rawDataLibrary")
  
  # The historic transformed variables are valid to import
  transformedDataLibrary <- readRDS(file = "RegressionTables/transformedDataLibrary")
}

# Save Raw data as csv if import to excel model file is required
if (modelDetailsCsv[modelDetailsCsv$Metric == "Import Raw Data?", "Detail"] == "yes") {
  write.csv(RawInputCsv,"RegressionTables/RawInput.csv", row.names = FALSE)
}

# identifier column name (normally dates)
identVarName <- modelDetailsCsv[modelDetailsCsv$Metric == "Observation Name", "Detail"]

# Get a list of cross sections
xsNames <- as.character(xsDetailsCsv$crosssection)

# Get a list of unique category names
catNames <- unique(VariableDetailsCsv$Category)

# Get a list of cross section Categorisations
xsCat <- colnames(xsDetailsCsv)

# Get a list of the explanatory variables that we will model
modelledVarNames <- VariableDetailsCsv$Variable

# Approach type (frequentist or bayesian)
regApproach <- modelDetailsCsv[modelDetailsCsv$Metric == "Regression Approach", "Detail"] %>% tolower()

# Bayesian software (R or Python)
baySoftware <- modelDetailsCsv[modelDetailsCsv$Metric == "Bayesian Software", "Detail"] %>% tolower()

# Are we running a logged KPI model?
logModel <- modelDetailsCsv[modelDetailsCsv$Metric == "Log Modelling?", "Detail"] %>% tolower()

# Use Newey Standard Errors
NeweyWest <- modelDetailsCsv[modelDetailsCsv$Metric == "Use Newey Standard Errors?", "Detail"] %>% tolower()

maxModCombo <- modelDetailsCsv[modelDetailsCsv$Metric == "Max number of models run", "Detail"] %>% as.numeric() %>% replace_na(99999999)

# Read in the Model Permutations Option
validModelStop <- modelDetailsCsv[modelDetailsCsv$Metric == "Model Permutations Options", "Detail"] == "run until valid model is reached"
largestModelStop <- modelDetailsCsv[modelDetailsCsv$Metric == "Model Permutations Options", "Detail"] == "run largest model only"
runAllModels <- modelDetailsCsv[modelDetailsCsv$Metric == "Model Permutations Options", "Detail"] == "run all variable permutations"

# Start Date (converted) as text
startDate = as.character(modelDetailsCsv[modelDetailsCsv$Metric == "Model Start Date", "Detail"]) %>%
  as.Date(tryFormats = "%m/%d/%Y") %>%
  format("%d/%m/%Y") %>%
  as.character()

# End Date (converted) as text
endDate = as.character(modelDetailsCsv[modelDetailsCsv$Metric == "Model End Date", "Detail"]) %>%
  as.Date(tryFormats = "%m/%d/%Y") %>%
  format("%d/%m/%Y") %>%
  as.character()

# Create list of weeks - THIS WILL ONLY WORK FOR WEEKLY DATA ***
if (tolower(modelDetailsCsv[modelDetailsCsv$Metric == "Modelling Frequency", "Detail"])=="daily") {
  obsList <- seq(as.Date(startDate, tryFormats = "%d/%m/%Y"), as.Date(endDate, tryFormats = "%d/%m/%Y"), "days")
} else if (tolower(modelDetailsCsv[modelDetailsCsv$Metric == "Modelling Frequency", "Detail"])=="weekly") {
  obsList <- seq(as.Date(startDate, tryFormats = "%d/%m/%Y"), as.Date(endDate, tryFormats = "%d/%m/%Y"), "weeks")
} else if (tolower(modelDetailsCsv[modelDetailsCsv$Metric == "Modelling Frequency", "Detail"])=="monthly") {
  obsList <- seq(as.Date(startDate, tryFormats = "%d/%m/%Y"), as.Date(endDate, tryFormats = "%d/%m/%Y"), "months")
}

if (modelDetailsCsv[modelDetailsCsv$Metric == "Generate Response Curves?", "Detail"] == "yes") {
  
  # import the equivalent media spend variables
  rcMedSpCsv <- read.csv(modelDetailsCsv[modelDetailsCsv$Metric == "RC Media Spend Directory", "Detail"], stringsAsFactors = FALSE, fileEncoding="UTF-8-BOM")
  colnames(rcMedSpCsv)[1:2] <- c("raw_variable", "equiv_spend_variable")
  # Convert to lower case
  rcMedSpCsv <- rcMedSpCsv %>% mutate(across(where(is.character), tolower))
  
}
