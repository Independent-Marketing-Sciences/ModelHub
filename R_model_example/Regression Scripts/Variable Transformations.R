# EXTRACT RAW VARIABLES REQUIRED ********************************************************************************************************************
# ***************************************************************************************************************************************************

print("3.1 Extracting raw variables required")

# List of all raw variables 
allRawVarNames <- colnames(RawInputCsv)

# List of the raw variables contained within the unique list of substituted variable names
buildSubVarNames <- gsub("[*-+/()^,-]", "@", uniqueSubVarNames$Names) %>%
  gsub("[*]", "@", .) %>%
  gsub("[>]", "@", .) %>%
  gsub("[<]", "@", .) %>%
  gsub("[=]", "@", .) %>%
  strsplit("@")  %>% unlist() %>% unique()
usedRawVarNames <- allRawVarNames[allRawVarNames %in% buildSubVarNames]

# If response curves are required, we may also need the equivalent spend variable names. Also extract these

if (modelDetailsCsv[modelDetailsCsv$Metric == "Generate Response Curves?", "Detail"] == "yes") {
  usedRawVarNames <- c(usedRawVarNames, rcMedSpCsv[rcMedSpCsv$raw_variable %in% usedRawVarNames, 2]) %>%
    unique()
}

# New raw dataset containing only used variables
redRawVarData <- RawInputCsv %>% select(all_of(usedRawVarNames))

redRawVarDataRDate <- mutate(redRawVarData, obs = as.Date(obs, "%d/%m/%Y"))

# drop redundant variables
rm(allRawVarNames, buildSubVarNames)

# VARIABLE TRANSFORMATIONS *****************************************************************************************************************************
# ******************************************************************************************************************************************************

print("3.2 Transforming variables")

if (is.null(transformedDataLibrary)) {
  
  # No historic transformed variables stored - transform all raw data
  # Transformed Variables - run calculations from variable name strings
  transVarDataWide <- lapply(1:nrow(uniqueSubVarNames), function(x) 
    transmute(redRawVarDataRDate, eval(parse(text=as.character(uniqueSubVarNames[x, "NamePipeSub"]))))) %>%
    do.call(cbind, .) %>%
    `colnames<-`(uniqueSubVarNames$NamePipeSub) %>%
    `rownames<-`(as.character(redRawVarData[, identVarName]) %>% as.Date(tryFormats = "%d/%m/%Y") %>% format("%d/%m/%Y") %>% as.character()) %>%
    cbind("OBS" = as.Date(redRawVarData$obs, "%d/%m/%Y"), .)
  
} else {
  
  # Merge historic transformed variables with any new transformed variables
  
  # List of new transformed variables
  lastRunTransVarNames <- colnames(transformedDataLibrary)
  thisRunTransVarNames <- uniqueSubVarNames$NamePipeSub
  newTransVarNames <- thisRunTransVarNames[!(thisRunTransVarNames %in% lastRunTransVarNames)]
  
  # If no new variables, use historic file
  if (is_empty(newTransVarNames)) {
    
    transVarDataWide <- transformedDataLibrary
    
  } else {
    
    # Transformed Variables - run calculations from variable name strings
    transVarDataWide <- lapply(1:length(newTransVarNames), function(x) 
      transmute(redRawVarDataRDate, eval(parse(text=as.character(newTransVarNames[x]))))) %>%
      do.call(cbind, .) %>%
      `colnames<-`(newTransVarNames) %>%
      # `rownames<-`(redRawVarData[, identVarName]) %>% remove if the below works
      `rownames<-`(as.character(redRawVarData[, identVarName]) %>% as.Date(tryFormats = "%d/%m/%Y") %>% format("%d/%m/%Y") %>% as.character()) %>%
      cbind("OBS" = as.Date(redRawVarData$obs, "%d/%m/%Y"), ., transformedDataLibrary[, 2:ncol(transformedDataLibrary)])
    
  }
}

# Replace any infinite values with NA
is.na(transVarDataWide) <- sapply(transVarDataWide, is.infinite)

# Save the transformed data - to use in the next regression run to speed up time unless the raw data has been resaved
saveRDS(transVarDataWide, file = "RegressionTables/transformedDataLibrary")

# rm(transformedDataLibrary, redRawVarDataRDate)
rm(transformedDataLibrary)
