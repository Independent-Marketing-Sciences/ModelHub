# Run residual Correlations ***********************************************************************************************************************
# *************************************************************************************************************************************************

if (modelDetailsCsv[modelDetailsCsv$Metric == "Run Residual Correlation?", "Detail"] == "yes") {
  
  print("7.1 Running Residual Correlations")
  
  # zeros omitted from months and days in raw data. quick fix - but to edit data input ***
  tempDates <- (as.character(RawInputCsv$obs) %>% as.Date(tryFormats = "%d/%m/%Y") %>% format("%d/%m/%Y") %>% as.character())
  
  
  
  # bobby1 <- RawInputCsv[which(tempDates == startDate):which(tempDates == endDate), 2:ncol(RawInputCsv)] %>% sapply(as.numeric) %>% as.data.frame()
  # bobbyResidual <- matrix(avmDetailsXsDf$Residual, nrow = obsCnt, ncol = length(xsNames)) %>% as.data.frame()
  # write.csv(bobby1,"RegressionTables/bobby1.csv", row.names = FALSE)
  # write.csv(bobbyResidual,"RegressionTables/bobbyResidual.csv", row.names = FALSE)
  # write.csv(residCorrByXs,"RegressionTables/bobbyresidCorr.csv", row.names = TRUE)
  
  if (logModel == "yes") {
    residCorrSeries <- avmDetailsXsDf$`Residual Logged`
  } else {
    residCorrSeries <- avmDetailsXsDf$Residual
  }
  
  residCorrByXs <- RawInputCsv[which(tempDates == startDate):which(tempDates == endDate), 2:ncol(RawInputCsv)] %>% sapply(as.numeric) %>% as.data.frame() %>%
    cor(matrix(residCorrSeries, nrow = obsCnt, ncol = length(xsNames)) %>% as.data.frame(), use = "pairwise.complete.obs") %>%
    as.data.frame() %>%
    `colnames<-`(xsNames)
  
  # residCorrByXs <- RawInputCsv[which(tempDates == startDate):which(tempDates == endDate), 2:ncol(RawInputCsv)] %>% sapply(as.numeric) %>% as.data.frame() %>%
  #   cor(matrix(avmDetailsXsDf$Residual, nrow = obsCnt, ncol = length(xsNames)) %>% as.data.frame(), use = "pairwise.complete.obs") %>%
  #   as.data.frame() %>%
  #   `colnames<-`(xsNames)
  
  if (length(xsNames) > 1) {
    # Multiple cross sections - to calculate overall correlation
    residCorrByTot <- (do.call("rbind", replicate(length(xsNames), 
                                                  RawInputCsv[which(tempDates == startDate):which(tempDates == endDate), 
                                                              2:ncol(RawInputCsv)], simplify = FALSE)) %>% # stack raw data on top of each other over modeled time period
                         sapply(as.numeric)) %>%
      
      # cor(avmDetailsXsDf$Residual, ., use = "complete.obs") %>% # correlate against residual, ignoring NA periods - THIS CORRELATED AGAINST ACTUAL RESIDS RATHER THAN LOGGED. EDITED BELOW
      cor(residCorrSeries, ., use = "complete.obs") %>% # correlate against residual, ignoring NA periods
      
      # cor(avmDetailsXsDf$Residual, ., use = "na.or.complete") %>% # correlate against residual, ignoring NA periods  
      t() %>%
      as.data.frame() %>%
      rename(ResidCorr=V1) # %>%
    # arrange(desc(ResidCorr))
    residCorrDf <- cbind(residCorrByTot, residCorrByXs) %>%
      `colnames<-`(c("Total", xsNames)) %>%
      arrange(desc(Total))
  } else {
    # Just the one cross section
    residCorrDf <- residCorrByXs %>%
      `colnames<-`("Total") %>%
      arrange(desc(Total))
  }
  
  # # remove rows that are NA only in the total column
  # residCorrDf <- residCorrDf[complete.cases(residCorrDf[, "Total"]),] # converts from DB to vector, with no row names :(
  
  # Write csv
  write.csv(residCorrDf,"RegressionTables/residualCorr.csv", row.names = TRUE)
  rm(tempDates)
  
}


  # Generate Response Curves **********************************************************************************************************************************
# ***********************************************************************************************************************************************************

if (modelDetailsCsv[modelDetailsCsv$Metric == "Generate Response Curves?", "Detail"] == "yes") {
  
  # library(stringi)
  
  # # import the equivalent media spend variables
  # rcMedSpCsv <- read.csv(modelDetailsCsv[modelDetailsCsv$Metric == "RC Media Spend Directory", "Detail"], stringsAsFactors = FALSE, fileEncoding="UTF-8-BOM")
  # colnames(rcMedSpCsv)[1:2] <- c("raw_variable", "equiv_spend_variable")

  # obtain a unique list of modeled variable names that include a diminishing returns transformation
  dimRetVar <- NULL
  for (i in 1:ncol(subVarNames)) {
    if (grepl("dimret_adstock(", subVarNames[1, i], fixed = TRUE)) {
      dimRetVar <- append(dimRetVar, subVarNames[, i] %>% unique())
    } else if (grepl("dimret(", subVarNames[1, i], fixed = TRUE)) {
      dimRetVar <- append(dimRetVar, subVarNames[, i] %>% unique())
    } else if (grepl("atan(", subVarNames[1, i], fixed = TRUE)) {
      dimRetVar <- append(dimRetVar, subVarNames[, i] %>% unique())
    }
  }

  # filter out any modeled variables containing multiple diminishing returns transformations. These should not be permitted within the tool
  dimRetVar <- dimRetVar[(str_count(dimRetVar, 'dimret') <= 1) &
                            (str_count(dimRetVar, 'dimret_adstock') <= 1) &
                            (str_count(dimRetVar, 'atan') <= 1)]
  
  # We need to check if the response curve variable contains any of the raw media variables listed in the Media Spend CSV file. If not, we won't chart
  medVarCnt <- lapply(1:nrow(rcMedSpCsv), function(x) 
    grepl(rcMedSpCsv$raw_variable[x], dimRetVar) %>% as.numeric()) %>%
    unlist() %>%
    matrix(ncol = nrow(rcMedSpCsv)) %>%
    as.data.frame() %>%
    rowSums()
  
  dimRetVar <- dimRetVar[medVarCnt != 0]
  
  if (length(dimRetVar) == 0) {
    
    write.csv("No response curve variables detected","RegressionTables/responseCurves.csv", row.names = FALSE)
    
  } else {
  
  # Obtain a list of media variables pre the diminishing returns transformation
  preDimRetVar <- NULL

  for (i in 1:length(dimRetVar)) {

    # i <- 1
    
    endVarTxt <- ""
    
    if (grepl("dimret_adstock(", dimRetVar[i], fixed = TRUE)) {

      functLoc <- unlist(gregexpr("dimret_adstock", dimRetVar[i]))[1]
      commaLoc <- unlist(gregexpr(",", dimRetVar[i]))[2]
      bracketLoc <- unlist(gregexpr(")", dimRetVar[i]))[1]

      if (bracketLoc != nchar(dimRetVar[i])) {
        endVarTxt <- substring(dimRetVar[i], bracketLoc + 1, nchar(dimRetVar[i]))
      } else {
        endVarTxt <- ""
      }
      
      temp <- paste(if (functLoc > 1) {substring(dimRetVar[i], 1, functLoc - 1)} else {""},
                    "adstock(",
                    substring(dimRetVar[i], functLoc + 15, commaLoc - 1),
                    substring(dimRetVar[i], bracketLoc, str_length(dimRetVar[i])),
                    # endVarTxt, # don't need this bit - code in line above goes up to end of whole string. 129 even needed?
                    sep = "")

    } else if (grepl("dimret(", dimRetVar[i], fixed = TRUE)) {

      functLoc <- unlist(gregexpr("dimret", dimRetVar[i]))[1]
      commaLoc <- unlist(gregexpr(",", dimRetVar[i]))[1]
      bracketLoc <- unlist(gregexpr(")", dimRetVar[i]))[1]

      if (bracketLoc != nchar(dimRetVar[i])) {
        endVarTxt <- substring(dimRetVar[i], bracketLoc + 1, nchar(dimRetVar[i]))
      } else {
        endVarTxt <- ""
      }
      
      temp <- paste(if (functLoc > 1) {substring(dimRetVar[i], 1, functLoc - 1)} else {""},
                    substring(dimRetVar[i], functLoc + 7, commaLoc - 1),
                    endVarTxt,
                    sep = "")

    } else if (grepl("atan(", dimRetVar[i], fixed = TRUE)) {

      functLoc <- unlist(gregexpr("atan", dimRetVar[i]))[1]
      divLoc <- unlist(gregexpr("/", dimRetVar[i]))[1]
      
      # if there is an adstock function within, we're looking for the second bracket location
      if (grepl("adstock(", dimRetVar[i], fixed = TRUE)) {
        bracketLoc <- unlist(gregexpr(")", dimRetVar[i]))[2]
      } else {
        bracketLoc <- unlist(gregexpr(")", dimRetVar[i]))[1]
      }

      if (bracketLoc != nchar(dimRetVar[i])) {
        endVarTxt <- substring(dimRetVar[i], bracketLoc + 1, nchar(dimRetVar[i]))
      } else {
        endVarTxt <- ""
      }
      
      temp <- paste(if (functLoc > 1) {substring(dimRetVar[i], 1, functLoc - 1)} else {""},
                    substring(dimRetVar[i], functLoc + 5, divLoc - 1),
                    endVarTxt,
                    sep = "")

    }

    preDimRetVar <- append(preDimRetVar, temp)

  }

  # Transformed Variables - run calculations from variable name strings
  preDrModVarDb <- lapply(1:length(preDimRetVar), function(x)
    transmute(redRawVarDataRDate, eval(parse(text=as.character(preDimRetVar[x]))))) %>%
    do.call(cbind, .) %>%
    `colnames<-`(preDimRetVar) %>%
    `rownames<-`(as.character(redRawVarData[, identVarName]) %>% as.Date(tryFormats = "%d/%m/%Y") %>% format("%d/%m/%Y") %>% as.character()) %>%
    cbind("OBS" = as.Date(redRawVarData$obs, "%d/%m/%Y"), .) %>%
    filter(OBS %in% obsList)
  
  # Create a version of the table above, but transforming the equivalent spend variables rather than the modelled variables
  preDimRetSpVar <- stri_replace_all_regex(preDimRetVar, 
                                           pattern = rcMedSpCsv$raw_variable, 
                                           replacement = rcMedSpCsv$equiv_spend_variable, 
                                           vectorize = FALSE)
  
  preDrModSpDb <- lapply(1:length(preDimRetSpVar), function(x)
    transmute(redRawVarDataRDate, eval(parse(text=as.character(preDimRetSpVar[x]))))) %>%
    do.call(cbind, .) %>%
    `colnames<-`(preDimRetSpVar) %>%
    `rownames<-`(as.character(redRawVarData[, identVarName]) %>% as.Date(tryFormats = "%d/%m/%Y") %>% format("%d/%m/%Y") %>% as.character()) %>%
    cbind("OBS" = as.Date(redRawVarData$obs, "%d/%m/%Y"), .) %>%
    filter(OBS %in% obsList)
  
  # Calculate the cost per input metric over the modeled time period for each variable
  metricScalingRatios <- colSums(preDrModSpDb[2:ncol(preDrModSpDb)]) / colSums(preDrModVarDb[2:ncol(preDrModVarDb)])
  
  # Scale down all of the X value inputs to reflect spend rather than the input metric
  preDrScaledSpDb <- data.frame(mapply(`*`, preDrModVarDb[2:ncol(preDrModSpDb)], metricScalingRatios)) %>%
    # `colnames<-`(colnames(preDrModVarDb)[2:ncol(preDrModSpDb)]) %>%
    `colnames<-`(modVarByXsNamesFin$Short.Variable.Name[match(colnames(preDrModVarDb)[2:ncol(preDrModVarDb)], 
                                                              modVarByXsNamesFin$varCodeWoXs)]) %>%
    cbind(OBS = preDrModVarDb$OBS, .)
  
  # Generate transformed variables post diminishing returns
  postDrModVarDb <- lapply(1:length(dimRetVar), function(x)
    transmute(redRawVarDataRDate, eval(parse(text=as.character(dimRetVar[x]))))) %>%
    do.call(cbind, .) %>%
    `colnames<-`(dimRetVar) %>%
    `rownames<-`(as.character(redRawVarData[, identVarName]) %>% as.Date(tryFormats = "%d/%m/%Y") %>% format("%d/%m/%Y") %>% as.character()) %>%
    cbind("OBS" = as.Date(redRawVarData$obs, "%d/%m/%Y"), .) %>%
    filter(OBS %in% obsList)
  
  # Extract corresponding variables post exp
  postDrAndExpVarDb <- varContsXsDf[, match(dimRetVar, VariableDetailsCsv$Variable) + 2] %>%
    cbind(OBS = obsList, .)
  
  # Calculate the scaling ratio needed to get from transformed data through to post exp contributions, by variable
  if (ncol(postDrAndExpVarDb) == 2) {
    # just one dimension
    rcContScalingRatios <- sum(postDrAndExpVarDb[2]) / sum(postDrModVarDb[2])
  } else {
    # multiple dimensions
    rcContScalingRatios <- colSums(postDrAndExpVarDb[2:ncol(postDrAndExpVarDb)]) / colSums(postDrModVarDb[2:ncol(postDrModVarDb)])
  }
  
  # Scale up all of the y value outputs to reflect actual contributions
  postExpScaledContDb <- data.frame(mapply(`*`, postDrModVarDb[2:ncol(postDrModVarDb)], rcContScalingRatios)) %>%
    # `colnames<-`(colnames(postDrModVarDb)[2:ncol(postDrModVarDb)]) %>%
    `colnames<-`(modVarByXsNamesFin$Short.Variable.Name[match(colnames(postDrModVarDb)[2:ncol(postDrModVarDb)], 
                                                              modVarByXsNamesFin$varCodeWoXs)]) %>%
    cbind(OBS = obsList, .)
  
  # Generate Response Curve output table

  # generate repeated identity matrix
  tempIdent <- diag(ncol(postExpScaledContDb)-1)
  identDb <- tempIdent[rep(seq_len(nrow(tempIdent)), each = length(obsList)), ]
  
  # multiply the repeated identity matrix by the post exp contributions
  respCurveTable <- do.call("rbind", replicate(ncol(postExpScaledContDb)-1, postExpScaledContDb[2:ncol(postExpScaledContDb)], simplify = FALSE)) * 
    identDb # %>%
    # `colnames<-`(colnames(postExpScaledContDb)[2:ncol(postExpScaledContDb)])
    
  # stack the spends into a single column
  rcStackedSp <- as.vector(preDrScaledSpDb[2:ncol(preDrScaledSpDb)]) %>% unlist() %>% as.vector()
  
  # merge together the final output table
  respCurveTable <- cbind(Variable = rep(colnames(postExpScaledContDb)[2:ncol(postExpScaledContDb)], each = length(obsList)), 
                          OBS = rep(obsList, times = ncol(postExpScaledContDb)-1), 
                          Spend = rcStackedSp, respCurveTable)
  
  # filter out rows that sum to zero
  respCurveTable <- respCurveTable %>% filter(rowSums(across(where(is.numeric)))!=0)
  
  # # sort by channel then by spend
  # respCurveTable <- respCurveTable[order(respCurveTable[, "Variable"], respCurveTable[, "Spend"]), ]
  
  # replace all zeros with blanks
  respCurveTable[respCurveTable == 0] <- ""
  
  # block of diagonal zeros - to ensure every response curve goes through the origin
  blockDb <- data.frame(Variable = colnames(postExpScaledContDb)[2:ncol(postExpScaledContDb)], 
                   OBS = rep(NA, ncol(postExpScaledContDb)-1), 
                   Spend = rep(0, ncol(postExpScaledContDb)-1),
                   matrix(NA, ncol(postExpScaledContDb)-1, ncol(postExpScaledContDb)-1) %>% `diag<-`(., 0)) %>%
    `colnames<-`(colnames(respCurveTable))
  blockDb[is.na(blockDb)] <- ""
  
  # append the block zero data onto the end of the response curve data
  respCurveTable <- rbind(respCurveTable, blockDb)

  # sort by channel then by spend
  respCurveTable <- respCurveTable[order(respCurveTable[, "Variable"], respCurveTable[, "Spend"]), ]
  # then sort columns alphabetically (if we have more than one media variable)
  if (ncol(respCurveTable) > 4) {
    respCurveTable <- respCurveTable %>% select(Variable, OBS, Spend, order(colnames(respCurveTable[, 4:ncol(respCurveTable)]))+3)
  }
  
  rm(tempIdent, identDb, rcStackedSp)
  
  write.csv(respCurveTable,"RegressionTables/responseCurves.csv", row.names = FALSE)
  
  }
  
}

# Residual splits *******************************************************************************************************************************************
# ***********************************************************************************************************************************************************

# # temp
# temp <- "Base, Other Seasonality, Covid, Growth"
# temp <- "Base"


if (modelDetailsCsv[modelDetailsCsv$Metric == "Residual Split", "Detail"] != "no") {

  # Identify which variables are included in the residual splitting

  if (modelDetailsCsv[modelDetailsCsv$Metric == "Residual Split", "Detail"] == "yes") {

    # All variables included in variable split
    residSplitVars <- VariableDetailsCsv$Short.Variable.Name

  } else {

    # Identify categories that qualify for residual split
    residSplitCats <- strsplit(gsub(",", ", ", modelDetailsCsv[modelDetailsCsv$Metric == "Residual Split", "Detail"]),
                               split=", ",fixed=TRUE)[[1]] %>% trimws()
    residSplitVars <- VariableDetailsCsv$Short.Variable.Name[tolower(VariableDetailsCsv$Category) %in% residSplitCats]

  }

  # Dummy grid for the variables we want to split residuals over
  residDumGrid <- as.numeric(VariableDetailsCsv$Short.Variable.Name %in% residSplitVars) %>%
    replicate(nrow(varContsXsDf), .) %>%
    t()
  # Calculate the shares we need to take from the residual by variable
  absConts <- as.data.frame(residDumGrid * as.matrix(varContsXsDf[, 3:ncol(varContsXsDf)])) %>%
    abs()
  residShares <- absConts / rowSums(absConts)

  is.nan.data.frame <- function(x)
    do.call(cbind, lapply(x, is.nan))

  residShares[is.nan(residShares)] <- 0

  # multiply this by the residuals
  residSplits <- residShares * avmDetailsXsDf$Residual %>% replace_na(0)

  # Add these split out residuals to the original contributions
  varContsXsDfNew <- cbind(varContsXsDf[, 1:2],
                 varContsXsDf[, 3:ncol(varContsXsDf)] + residSplits)

  # Overwrite existing varContsXsDf
  varContsXsDf <- varContsXsDfNew

  rm(residDumGrid, absConts, residShares, residSplits, varContsXsDfNew)

  # Refresh the Cat Conts and Total Conts

  #Output; Variable Contributions Totaled
  varContsTotDf <- aggregate(. ~ OBS, data=varContsXsDf[,-1], sum)

  #Output; Categorized Contributions Totaled
  catContsXsDf <- lapply(1:length(catNames), function(x)
    rowSums(varContsXsDf[gsub(" ", "_", unique(modVarByXsNamesFin[modVarByXsNamesFin$Category == catNames[x],"Short.Variable.Name"]))])) %>%
    do.call(cbind, .) %>%
    `colnames<-`(catNames) %>%
    data.frame(select(avmDetailsXsDf, 1:2), .)

  #Output; Categorized Contributions Totaled
  catContsTotDf <- aggregate(. ~ OBS, data=catContsXsDf[,-1], sum)

}
