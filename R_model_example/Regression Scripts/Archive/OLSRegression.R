# REGRESSION - INITIAL RUN TO OBSERVE VARIABLES THAT FAIL COEFFICIENT RESTRICTIONS *************************************************************
# **********************************************************************************************************************************************

failFlag <- NULL

if (modelDetailsCsv[modelDetailsCsv$Metric == "Prioritise dropping tricky variables", "Detail"] == "yes") {
  
  transVarByXsDataLongQuick <- transVarByXsDataLong
  colnames(transVarByXsDataLongQuick) <- c(colnames(transVarByXsDataLongQuick)[1:2], 
                                           colnames(transVarByXsDataLongQuick)[3:(ncol(transVarByXsDataLongQuick))] %>% 
                                             gsub("[*-+/()^,!<>=-]", "ß", .) %>% gsub("'", "ß", .) %>% paste("ßßß", ., "ßßß", sep = ""))
  
  modVarQuick <- modVarSubGrouped$varForPerm[2:nrow(modVarSubGrouped)] %>% 
    gsub("[*-+/()^,!<>=-]", "ß", .) %>% gsub("'", "ß", .) %>% paste("ßßß", ., "ßßß", sep = "")
  
  # starting string for model equation
  modelFormText <- paste(colnames(transVarByXsDataLongQuick[3]),"~", 
                         paste(modVarQuick, collapse=" + "), 
                         "+0", collapse=" ") #create reg formula
  
  # repeat and join the table above for each possible combination of piping variables
  pipeQuick <- subOptionsGrid[1:nrow(subOptionsGrid), ] # %>% t()
  
  # # insert pipe values to explanatory variables string
  # for (p in 1:length(subNames)) {
  #   modelFormText <- gsub(paste("¬", p, sep = ""), pipeQuick[p], modelFormText)
  # }
  
  # insert pipe values to explanatory variables string. Use first permutation values
  if (length(subNames) == 1) {
    modelFormText <- gsub(paste("¬", 1, sep = ""), pipeQuick[1], modelFormText)
  } else {
    for (p in 1:length(subNames)) {
      modelFormText <- gsub(paste("¬", p, sep = ""), pipeQuick[1, p], modelFormText)
    }
  }
  
  #convert to formula
  modelForm <- as.formula(modelFormText)
  modelFit <- lm( modelForm, data=transVarByXsDataLongQuick)
  
  
  permCoefficientInitial <- modelFit$coefficients
  minCoeffValid <- !(F %in% (modVarSubGrouped$Coeff.Min[2:nrow(modVarSubGrouped)] <= permCoefficientInitial))
  maxCoeffValid <- !(F %in% (modVarSubGrouped$Coeff.Max[2:nrow(modVarSubGrouped)] >= permCoefficientInitial))
  
  # Check if there are any failed restrictions
  if (!all(c(minCoeffValid, maxCoeffValid))) {
    
    # attach fail flag column to subOptionsGrid
    failFlag <- (!(((modVarSubGrouped$Coeff.Min[2:nrow(modVarSubGrouped)] <= permCoefficientInitial) &
                      (modVarSubGrouped$Coeff.Max[2:nrow(modVarSubGrouped)] >= permCoefficientInitial)) %>% 
                     as.vector()) %>% is.na()) %>% as.numeric()
    
  }
  
  modVarSubGrouped <- cbind(modVarSubGrouped, failFlag = c(0, failFlag))
  
  rm(transVarByXsDataLongQuick, pipeQuick, modVarQuick)
  
  # 1 - think we're skipping over double fixed variables. need to incorporate
  
} else {
  
  modVarSubGrouped <- cbind(modVarSubGrouped, failFlag = rep(0, nrow(modVarSubGrouped)))
  
}


# PERMUTATION MANAGEMENT ***********************************************************************************************************************
# **********************************************************************************************************************************************

# Look up the permutation details for each variable
permVarDetails <- modVarSubGrouped[2:nrow(modVarSubGrouped), c("varForPerm", "Variable", "Short.Variable.Name", "Coeff.Min", 
                                                               "Coeff.Max", "Importance", "failFlag")] %>%
  map_df(rev) %>% # the more frequently changing variables need to be at the top
  arrange(Importance, desc(failFlag)) %>% # the least important variables are the first to be turned on and off
  transform(Coeff.Min = as.numeric(Coeff.Min)) %>%
  transform(Coeff.Max = as.numeric(Coeff.Max)) %>% # was being read as a boolean before - which mucked up sorting below
  transform(Importance = as.numeric(Importance))

# Extract coefficient options for each modeled variable
permOptions <- lapply(1:nrow(permVarDetails), function(x)
  c(permVarDetails[x, "Coeff.Min"], permVarDetails[x, "Coeff.Max"], 
    # If importance is zero, add the permutation of ommiting this variable
    if (permVarDetails[x, "Importance"] == 0) {0} else {
      if (is.na(permVarDetails[x, "Coeff.Min"]) | is.na(permVarDetails[x, "Coeff.Max"])) {NA} else # formula won't work with n/a's
        # If min and max settings are the same, don't include floating option (NA)
        if (permVarDetails[x, "Coeff.Min"] == permVarDetails[x, "Coeff.Max"]) {permVarDetails[x, "Coeff.Min"]} else {NA}}) %>% 
    unique() %>%   unlist() %>%   replace_na(-9999999999) %>% sort() %>% na_if(-9999999999)) %>%
  `names<-`(permVarDetails$varForPerm)

varItStop <- 0

# Check if there is a restricted number of model runs
if ((all_of(maxModCombo) < 99999999) & (all_of(maxModCombo) < prod(as.vector(lengths(permOptions)))*nrow(subOptionsGrid))) {
  # Restricted number of model runs
  varOptions <- lengths(permOptions)
  x <- 0
  # Count the number of variables that will contain different iterations, given the maximum number of models we will run
  for (x in 1:nrow(permVarDetails)) {
    if (prod(varOptions[1:x]) * nrow(subOptionsGrid) >= all_of(maxModCombo)) {
      varItStop <- x
      break
    }
  }  
  # Overwrite the options for remaining variables with just the first available value
  for (x in (varItStop+1):nrow(permVarDetails)) {
    permOptions[[x]] <- permOptions[[x]][1]
  }
} else {
  # Unrestricted number of model runs - update number of permutations
  maxModCombo <- prod(as.vector(lengths(permOptions))) * nrow(subOptionsGrid)
}

# Check if there are any input variables with no variance (which shouldn't be modeled)
# First sub out the pipe variables for initial values
modelVarTextCheck <- names(permOptions)
for (p in 1:length(subNames)) {
  modelVarTextCheck <- gsub(paste("¬", p, sep = ""), subOptionsGrid[1, p], modelVarTextCheck)
}

# Loop through variables and check for zero standard deviation. If so, variable should be turned off
constCnt <- 0
for (x in 1:length(permOptions)) {
  # Check if the standard dev of the variable is zero
  if (sd(transVarByXsDataLong[, modelVarTextCheck[x]]) == 0) {
    # Unless it's the first occurrence of a constant, we need to remove it from modeling
    if ((sum(transVarByXsDataLong[, modelVarTextCheck[x]]) == 0) | (constCnt > 0)) {
      permOptions[[x]] <- 0
    } else {
      constCnt <- constCnt + 1
    }
  }
}

maxModPerm <- prod(as.vector(lengths(permOptions)))
maxModCombo <- min(maxModCombo, prod(as.vector(lengths(permOptions))) * nrow(subOptionsGrid))

# Generate permutations grid (ignoring piping variable permutations)
permGridTemp <- permOptions %>%
  do.call(expand.grid, .) %>%
  t() %>%
  as.data.frame() %>%
  select(1:all_of(maxModPerm)) %>%
  `rownames<-`(permVarDetails$varForPerm) %>%
  `colnames<-`(paste("Run.", 1:all_of(maxModPerm), sep = ""))

# Reorder based on initial variable order (ignoring piping variable permutations)
permGrid <- permGridTemp[match(modVarSubGrouped[2:nrow(modVarSubGrouped), "varForPerm"], row.names(permGridTemp)), ] %>%
  as.data.frame() %>% # so it has at least 1 column to read in
  `rownames<-`(modVarSubGrouped[2:nrow(modVarSubGrouped), "varForPerm"]) %>%
  `colnames<-`(paste("Run.", 1:all_of(maxModPerm), sep = ""))

# List of required pipe variable values for each model run
permGridBig <- permGrid[, rep(seq_len(ncol(permGrid)), each = nrow(subOptionsGrid))] %>%
  as.data.frame() %>%
  select(1:all_of(maxModCombo)) %>%
  `rownames<-`(rownames(permGrid)) %>%
  `colnames<-`(paste("Run.", 1:(all_of(maxModCombo)), sep = ""))

# repeat and join the table above for each possible combination of piping variables
pipeGridBig <- subOptionsGrid[rep(1:nrow(subOptionsGrid), ncol(permGrid)), ] %>%
  t() %>%
  as.data.frame() %>%
  select(1:all_of(maxModCombo)) %>%
  `rownames<-`(colnames(subOptionsGrid)) %>%
  `colnames<-`(paste("Run.", 1:(all_of(maxModCombo)), sep = ""))

rm(permGridTemp, permOptions, permGrid, constCnt)

kpi.list <- list()

fixedVarNames <- row.names(filter(permGridBig, !is.na(eval(parse(text=colnames(permGridBig)[ncol(permGridBig)])))))
fixedVarIndex <- match(fixedVarNames, rownames(permGridBig))

# Subtract the fixed variable contributions from each KPI, giving different iterations
kpi.list <- lapply(1:ncol(pipeGridBig), function(x)
  transVarByXsDataLong[, 3] - 
    if (length(fixedVarIndex) != 1) {
      rowSums(as.matrix(transVarByXsDataLong[, fixedVarIndex + 3]) %*% 
                diag(replace_na(permGridBig[, x], 0)[fixedVarIndex]))
    } else {
      rowSums(as.matrix(transVarByXsDataLong[, fixedVarIndex + 3]) %*% 
                diag(replace_na(permGridBig[, x], 0)[fixedVarIndex] %>% as.matrix()))
    }
)

newActual <- do.call(cbind, kpi.list) %>%
  `colnames<-`(paste("V0.Run", 1:ncol(pipeGridBig), sep = "")) %>%
  as.data.frame()

# Attach these onto the end of model source database
transVarByXsDataLong <- cbind(transVarByXsDataLong, newActual)

# List of modeled variables to run under each permutation
modVarCode <- lapply(1:ncol(permGridBig), function(x) 
  rownames(permGridBig)[is.na(permGridBig[, x])])

# rename transVarByXsDataLong such that there are no operation in column names
modVarCodeNoOp <- lapply(1:ncol(permGridBig), function(x) 
  rownames(permGridBig)[is.na(permGridBig[, x])] %>% gsub("[*-+/()^,!<>=-]", "ß", .) %>% gsub("'", "ß", .) %>% paste("ßßß", ., "ßßß", sep = ""))

colnames(transVarByXsDataLong) <- c(colnames(transVarByXsDataLong)[1:2], 
                                    colnames(transVarByXsDataLong)[3:(ncol(transVarByXsDataLong)-ncol(pipeGridBig))] %>% 
                                      gsub("[*-+/()^,!<>=-]", "ß", .) %>% gsub("'", "ß", .) %>% paste("ßßß", ., "ßßß", sep = ""), 
                                    colnames(transVarByXsDataLong)[(ncol(transVarByXsDataLong)-ncol(pipeGridBig)+1):ncol(transVarByXsDataLong)])

rm(kpi.list, newActual, fixedVarIndex)

# REGRESSION - MODEL COMPARISON ****************************************************************************************************************
# **********************************************************************************************************************************************

print("5.1 Running regression")

permRSq = list()
permAdjRSq = list()
permDurbinWatson = list()
permCoefficient = list()
permTStat = list()
permPValue = list()
permStandardError = list()
permValid = list()
permX <- 0
exitPermLoop <- F

while ((exitPermLoop == F) & (permX < min(ncol(permGridBig), maxModCombo))) {
  # While there isn't a valid model, or have exhausted all permutations, or setting is to run all models
  
  permX = permX + 1
  
  # starting string for model equation
  modelFormText <- paste(paste("V0.Run", permX, sep = ""),"~", paste(modVarCodeNoOp[permX][[1]], collapse=" + "), "+0", collapse=" ") #create reg formula
  # insert pipe values to explanatory variables string
  for (p in 1:length(subNames)) {
    modelFormText <- gsub(paste("¬", p, sep = ""), pipeGridBig[p, permX], modelFormText)
  }
  #convert to formula
  modelForm <- as.formula(modelFormText)
  modelFit <- lm( modelForm, data=transVarByXsDataLong)
  
  # Update names within list - from "no operator" variables to original names
  names(modelFit[["coefficients"]]) = modVarByXsNames$varForPerm[match(names(modelFit[["coefficients"]]), modVarByXsNames$varNamesNoOperator)]
  names(modelFit[["effects"]]) = modVarByXsNames$varForPerm[match(names(modelFit[["effects"]]), modVarByXsNames$varNamesNoOperator)]
  names(modelFit[["model"]])[2:length(names(modelFit[["model"]]))] = modVarByXsNames$varForPerm[match(names(modelFit[["model"]])[2:length(names(modelFit[["model"]]))],
                                                                                                      modVarByXsNames$varNamesNoOperator)]
  # Store topline stats
  permRSq[[permX]]=summary(modelFit)$r.squared
  permAdjRSq[[permX]]=summary(modelFit)$adj.r.squared
  # permCoefficient[[permX]]=modelFit$coefficients[match(modVarCode[1][[1]], modVarCode[permX][[1]])] # extract coeffs, but then space out based on omitted variables
  # Coefficients need to combine those calcuated in regression with fixed coefficients  
  permCoefficient[[permX]] <- coalesce(permGridBig[, permX], 0) + coalesce(modelFit$coefficients[match(row.names(permGridBig), modVarCode[permX][[1]])], 0)
  permTStat[[permX]]=summary(modelFit)[["coefficients"]][, "t value"][match(row.names(permGridBig), modVarCode[permX][[1]])]
  permPValue[[permX]]=summary(modelFit)[["coefficients"]][, "Pr(>|t|)"][match(row.names(permGridBig), modVarCode[permX][[1]])]
  permStandardError[[permX]]=summary(modelFit)[["coefficients"]][, "Std. Error"][match(row.names(permGridBig), modVarCode[permX][[1]])]
  
  # Detailed Run
  
  # # run Durbin Watson Test
  # modelDw <- dwtest(modelFit, order.by = NULL, alternative = c("greater", "two.sided", "less"), 
  #                   iterations = 15, exact = NULL, tol = 1E-10)
  
  # permDurbinWatson[[permX]]=modelDw$statistic
  
  print(paste("Run ", permX, "/", ncol(permGridBig), sep = ""))
  
  # Coefficient Min & Max tests
  minCoeffValid <- !(F %in% (permVarDetails$Coeff.Min[match(row.names(permGridBig), permVarDetails$varForPerm)] <= permCoefficient[[permX]]))
  maxCoeffValid <- !(F %in% (permVarDetails$Coeff.Max[match(row.names(permGridBig), permVarDetails$varForPerm)] >= permCoefficient[[permX]]))
  permValid[[permX]] <- all(c(minCoeffValid, maxCoeffValid))
  exitPermLoop <- (all(c(minCoeffValid, maxCoeffValid, validModelStop)) | largestModelStop)
  
}

permRSqDb <- do.call(rbind, permRSq)
permAdjRSqDb <- do.call(rbind, permAdjRSq)
permCoefficientDb <- do.call(rbind, permCoefficient) %>% `colnames<-`(row.names(permGridBig))
permTStatDb <- do.call(rbind, permTStat) %>% `colnames<-`(row.names(permGridBig))
permPValueDb <- do.call(rbind, permPValue) %>% `colnames<-`(row.names(permGridBig))
permStandardErrorDb <- do.call(rbind, permStandardError) %>% `colnames<-`(row.names(permGridBig))
permValidDb <- do.call(rbind, permValid)
permPipeValues <- (pipeGridBig)[, 1:permX] %>% as.data.frame() %>% t()

# Create Permutation Results Summary - merge data
modelPermSummary <- cbind(colnames(permGridBig)[1:permX], permRSqDb, permAdjRSqDb, permPipeValues, 
                          permCoefficientDb, permTStatDb, permPValueDb, permStandardErrorDb, permValidDb) 

# Attach on variable names, categories etc.  
modelPermSummary <- rbind(c("Min", NA, NA, rep(NA, length(subNames)), 
                            modVarByXsNames[match(row.names(permGridBig), modVarByXsNames$varForPerm),"Coeff.Min"], rep(NA, ncol(permTStatDb)*3), NA),
                          c("Max", NA, NA, rep(NA, length(subNames)), 
                            modVarByXsNames[match(row.names(permGridBig), modVarByXsNames$varForPerm),"Coeff.Max"], rep(NA, ncol(permTStatDb)*3), NA),
                          c("Run", "Rsq", "AdjRsq", subNames, rep("Coeff", ncol(permCoefficientDb)), rep("TStat", ncol(permTStatDb)), 
                            rep("PValue", ncol(permPValueDb)), rep("StError", ncol(permStandardErrorDb)), "Valid"),
                          modVarByXsNames$Short.Variable.Name[match(colnames(modelPermSummary), modVarByXsNames$varForPerm)], 
                          modVarByXsNames$xsGroupName[match(colnames(modelPermSummary), modVarByXsNames$varForPerm)],
                          modelPermSummary) %>%
  as.data.frame()

rm(modelFormText, modelForm, permRSq, permRSqDb, permAdjRSq, permAdjRSqDb, permCoefficient, permCoefficientDb, permTStat, permTStatDb, permPValue, permPValueDb,
   permStandardError, permStandardErrorDb, permValid)

# Select Model to run report on *** MORE WORK NEEDED HERE TO SELECT THE BEST MODEL
if (runAllModels == TRUE) {
  permSelected <- 1
} else {
  permSelected <- permX
}

# REGRESSION - FOCUS MODEL *****************************************************************************************************************
# ******************************************************************************************************************************************

# Rerun the selected model

# starting string for model equation
modelFormText <- paste(paste("V0.Run", permSelected, sep = ""),"~", paste(modVarCodeNoOp[permSelected][[1]], collapse=" + "), "+0", collapse=" ") #create reg formula
# insert pipe values to explanatory variables string
for (p in 1:length(subNames)) {
  modelFormText <- gsub(paste("¬", p, sep = ""), pipeGridBig[p, permSelected], modelFormText)
}
#convert to formula
modelForm <- as.formula(modelFormText)
modelFit <- lm( modelForm, data=transVarByXsDataLong)

# newey west standard errors
if(NeweyWest == "yes"){
  N <- nrow(transVarByXsDataLong)
  m <- floor(0.75 * N^(1/3))
  NeweyWestVarCov <- NeweyWest(lm( modelForm, data=transVarByXsDataLong), lag = m - 1, prewhite = F, adjust = T)
  NWStandardError <- sqrt(diag(NeweyWestVarCov))
  #T test of Coefficient test
  NWTtest <- coeftest(lm( modelForm, data=transVarByXsDataLong), vcov. = NeweyWestVarCov)
}

# the original standard errors
origStandardError <- sqrt(diag(vcov(modelFit)))

# For later, get a vector of explanatory variables with pipe variables subbed for values
modVarFinal <- modVarCode[[permSelected]]
modVarFinalWithFixed <- rownames(permGridBig)
for (p in 1:length(subNames)) {
  modVarFinal <- gsub(paste("¬", p, sep = ""), pipeGridBig[p, permSelected], modVarFinal)
  modVarFinalWithFixed <- gsub(paste("¬", p, sep = ""), pipeGridBig[p, permSelected], modVarFinalWithFixed)
}

rm(modelFormText, modelForm, modVarCodeNoOp)

vcov_mat <- vcov(modelFit)
vcov_mat <- data.frame(vcov_mat)
library("writexl")
write_xlsx(vcov_mat,"C:/Users/Tom Gray/im-sciences.com/FileShare - MasterDrive/Dev/Optimisation/Measures of Risk/Covariance matrix methodology/Abbott Lyon Test/AL Cov Mat.xlsx")
