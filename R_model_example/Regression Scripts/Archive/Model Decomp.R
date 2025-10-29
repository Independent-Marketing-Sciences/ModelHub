# MODEL DECOMPOSITION **********************************************************
# ******************************************************************************

# ******************************************************************************
if(regApproach != "bayesian"){
  
  # Define variables to generalised the script
  fitted_values <- modelFit$fitted.values
  coeff <- modelFit$coefficients
  
  # Create variable summary statistics with gaps for fixed coefficients
  if (NeweyWest == "yes") {
    # Step 1: Create a named vector with NA values for tStats, pValues, and standardErrors
    num_vars <- length(names(modelFit[["coefficients"]]))
    tStats <- setNames(rep(NA, num_vars), names(modelFit[["coefficients"]]))
    pValues <- setNames(rep(NA, num_vars), names(modelFit[["coefficients"]]))
    standardErrors <- setNames(rep(NA, num_vars), names(modelFit[["coefficients"]]))
    
    # Step 2: Update tStats, pValues, and standardErrors for matching variable names
    match_indices <- match(names(modelFit[["coefficients"]]), modVarCode[permSelected][[1]])
    tStats[!is.na(match_indices)] <- NWTtest[, 3][match_indices[!is.na(match_indices)]] %>% as.vector()
    pValues[!is.na(match_indices)] <- NWTtest[, 4][match_indices[!is.na(match_indices)]] %>% as.vector()
    standardErrors[!is.na(match_indices)] <- NWStandardError[match_indices[!is.na(match_indices)]] %>% as.vector()
  }else{
    tStats <- tStats[match(names(modelFit[["coefficients"]]), modVarCode[permSelected][[1]])] %>% as.vector()
    pValues <- pValues[match(names(modelFit[["coefficients"]]), modVarCode[permSelected][[1]])] %>% as.vector()
    standardErrors <- standardErrors[match(names(modelFit[["coefficients"]]), modVarCode[permSelected][[1]])] %>% as.vector()
  }
  
  # Statistics used in Bayesian Regression
  rhat <- NA
  ratioESS <- NA
  
  # Multiply fixed coefficients by the required variables
  fixedVarNames <- setdiff(modVarFinalWithFixed, modVarFinal)
  
  # Reduce down model variable names table to include only the final model's variables. To include any fixed variables
  modVarByXsNamesFin <- modVarByXsNames[modVarByXsNames$varForPerm %in% names(modelFit[["coefficients"]]), ]
  modVarByXsNamesFin <- modVarByXsNamesFin[modVarByXsNamesFin$varCodeWithXs %in% modVarFinalWithFixed, ]
  
  # Variables for the ModelStats tab
  rsq <- summary(modelFit)$r.squared
  adjR2 <- summary(modelFit)$adj.r.squared
  modErrVar <- sum(as.vector(modelFit$residuals) ^ 2) / df.residual(modelFit)
  modStdErr <- sqrt(sum(as.vector(modelFit$residuals) ^ 2) / df.residual(modelFit))
  dwStat <- modelDw$statistic; dwPVal <- modelDw$p.value
  bgStat <- breuschGodfreyTest$statistic; bgPVal <- breuschGodfreyTest$p.value
  bpStat <- breuschPaganTest$statistic; bpPVal <- breuschPaganTest$p.value
  archStat <- archTestOutput$statistic; archPVal <- archTestOutput$p.value
  jbStat <- jarqueBeraTest$statistic; jbPVal <- jarqueBeraTest$p.value
  rrStat <- ramseyResetTest$statistic; rrPVal <- ramseyResetTest$p.value
  rhatSigma <- NA
  rhatLPrior <- NA
  rhatLPost <- NA
  ratioESSSigma <- NA
  ratioESSLPrior <- NA
  ratioESSLPost <- NA
  lowestBMFI <- NA
  numDivergences <- NA
  pctDivergences <- NA
  
}else{
  
  # Define variable for consistency
  fitted_values <- predict(bayFit)[,1]
  coeff <- bayOutput[,"Estimate"]
  tStats <- NA
  pValues <- bayOutput[,"pvalue"]
  standardErrors <- bayOutput[,"Est.Error"]
  rhat <- bayOutput[,"rhat_coeff"]
  ratioESS <- bayOutput[,"ratio_ess_coeff"]
  modVarFinalWithFixed <- row.names(bayOutput)
  
  # Needed for consistency (this variables are generated inside the standard
  # regression script)
  modVarByXsNamesFin <- modVarByXsNames[modVarByXsNames$varForPerm %in% row.names(bayOutput), ]
  modVarByXsNamesFin <- modVarByXsNamesFin[modVarByXsNamesFin$varCodeWithXs %in% modVarFinalWithFixed, ]
  
  # Variables for the ModelStats tab
  
  rsq <- bayes_R2(bayFit)[1]
  adjR2 <- NA
  modErrVar <- NA
  modStdErr <- bayes_R2(bayFit)[2]
  dwStat <- NA; dwPVal <- NA
  bgStat <- NA; bgPVal <- NA
  bpStat <- NA; bpPVal <- NA
  archStat <- NA; archPVal <- NA
  jbStat <- NA; jbPVal <- NA
  rrStat <- NA; rrPVal <- NA
  rhatSigma <- unname(rhat_summary[1])
  rhatLPrior <- unname(rhat_summary[2])
  rhatLPost <- unname(rhat_summary[3])
  ratioESSSigma <- ratio_ess_summary[1]
  ratioESSLPrior <- ratio_ess_summary[2]
  ratioESSLPost <- ratio_ess_summary[3]
  lowestBMFI <- lowestBayBMFI
  numDivergences <- num_divergences
  pctDivergences <- pct_divergences
  
  # Required for the export
  modelPermSummary <- NA
}


# ******************************************************************************

#Output; Actual vs Model by XS
avmDetailsXsDf <- lapply(1:length(xsNames), function(x) 
  data.frame(CrossSection = rep(xsNames[x], obsCnt), # stacking on top of each other for each cross section
             OBS = obsList,
             Actual = select(transVarDataWide, subVarNames[x,1]))) %>%
  lapply(setNames, c("CrossSection", "OBS", "Actual")) %>% # all columns need the same names before rbinding
  do.call(rbind, .)
# Create Model including any NA values
ModelWithNas <- data.frame(seq(1:nrow(avmDetailsXsDf))) %>% # sequence with all possible obs
  `colnames<-`("Index") %>%
  merge(cbind("Model" = fitted_values, "Index" = rownames(as.data.frame(fitted_values))),
        #rownames excludes observations that had NAs - to merge with complete sequence
        by = c("Index"="Index"), all = TRUE) %>%
  select(Model) %>%
  unlist() %>%
  as.vector() %>%
  as.double()
# If XS weightings were applied, divide throughout by scaling factors
if (length(xsWeightings) > 1) {
  ModelWithNas <- ModelWithNas / rep(xsWeightings, each = obsCnt)
} 
# Merge with existing avmDetails, and calculate residuals
avmDetailsXsDfNew <- avmDetailsXsDf %>%
  cbind(Model = ModelWithNas) %>%
  mutate(Residual = Actual - Model)
# Overwrite existing model
avmDetailsXsDf <- avmDetailsXsDfNew

# Remove redundant variables
rm(avmDetailsXsDfNew, ModelWithNas, transVarDataWide)

# dummy for modeled observations
modelledObs <- rep(1, nrow(transVarByXsDataLong)) * (!is.na(avmDetailsXsDf$Model))

#Output; Variable Contributions by XS

# Contributions including separated XS modeled variables
varContsLargeXsDf <- mapply('*', select(transVarByXsDataLong, all_of(modVarFinalWithFixed)), coeff) %>%
  as.data.frame() %>%
  mapply('*', ., as.data.frame(modelledObs)) %>%
  cbind(select(avmDetailsXsDf, 1:2), .)

# If XS weightings were applied, divide throughout by scaling factors
if (length(xsWeightings) > 1) {
  varContsLargeXsDf[, 3:ncol(varContsLargeXsDf)] <- varContsLargeXsDf[, 3:ncol(varContsLargeXsDf)] / rep(xsWeightings, each = obsCnt)
} 


# Calcs if we're looking at a log model

if (logModel == "yes") {
  
  # LOG TRANSFORMATION BIAS ADJUSTMENT********************************************************************************************************
  # ******************************************************************************************************************************************
  # Calculate how much needs to be added on to each constant to lead to zero sum residuals on an exp level
  
  logTransBiasAdj <- modelDetailsCsv[modelDetailsCsv$Metric == "Adjust for log trans bias", "Detail"]
  
  if (logTransBiasAdj == "yes") {
    
    # calculate the constant adjustment needed to give zero total error in the exp model. Similar to solver
    constAdjList = list()
    f <- function(param, modData, actData) sum((exp(modData + rep(param, length(modData))) - exp(actData)))^2
    for (q in 1:length(xsNames)) {
      result <- optim(par = 0, f,
                      modData = avmDetailsXsDf[!is.na(avmDetailsXsDf$Residual) & avmDetailsXsDf$CrossSection == xsNames[q], "Model"],
                      actData = avmDetailsXsDf[!is.na(avmDetailsXsDf$Residual) & avmDetailsXsDf$CrossSection == xsNames[q], "Actual"],
                      method = "Brent", lower = -1, upper = 1)
      constAdjList[q] <- result$par
    }
    constAdj <- do.call(rbind, constAdjList) %>% as.vector()
    
    # make a column of adjustments needed by week / cross section
    constAdjCol = rep(constAdj, each = length(obsList))
    # we're just going to split this across variables belonging to interval one. extract these variables
    intOneVarConts <- varContsLargeXsDf[, modVarByXsNamesFin$varCodeWithXs[modVarByXsNamesFin$Interval == 1]] %>% as.data.frame() %>%
      `colnames<-`(modVarByXsNamesFin$varCodeWithXs[modVarByXsNamesFin$Interval == 1])
    # calc the share of the adjustment to go into each explanatory variable
    constSplitVar1 <- matrix(0, nrow = length(constAdjCol), ncol = sum(modVarByXsNamesFin$Interval != 1)) %>% as.data.frame() %>%
      `colnames<-`(modVarByXsNamesFin$varCodeWithXs[modVarByXsNamesFin$Interval != 1]) %>%
      cbind(constAdjCol * intOneVarConts / rowSums(intOneVarConts))
    # reorder
    constSplitVar2 <- select(constSplitVar1, colnames(varContsLargeXsDf)[3:ncol(varContsLargeXsDf)])
    # Overwrite the original contributions - to include log trans bias adjustment
    varContsLargeXsDf[3:ncol(varContsLargeXsDf)] <- varContsLargeXsDf[3:ncol(varContsLargeXsDf)] + constSplitVar2
    
    rm(result, constAdjList, constAdjCol, intOneVarConts, constSplitVar1, constSplitVar2)
    
  } else {
    # No constant adjustment made
    constAdj = rep(0, length(xsNames))
  }
  
  # Modify Actual vs Model to get normal level results
  avmDetailsXsDf[, "Actual Logged"] <- avmDetailsXsDf[, "Actual"]
  avmDetailsXsDf[, "Model Logged"] <- avmDetailsXsDf[, "Model"]
  avmDetailsXsDf[, "Residual Logged"] <- avmDetailsXsDf[, "Residual"]
  avmDetailsXsDf[, "Actual"] <- exp(avmDetailsXsDf[, "Actual"])
  avmDetailsXsDf[, "Model"] <- exp(rowSums(varContsLargeXsDf[3:ncol(varContsLargeXsDf)]))
  avmDetailsXsDf[, "Residual"] <- avmDetailsXsDf$Actual - avmDetailsXsDf$Model
 
  # log modeling prep
  antiLogsMid <- modelDetailsCsv[modelDetailsCsv$Metric == "Take Anti-logs at midpoints", "Detail"]
  if (antiLogsMid == "yes") {
    param1 <- 0.5
    param2 <- -0.5
  } else {
    param1 <- 1
    param2 <- 0
  }
  
  # Update intervals based off positive and negative contributions - such that +ve and -ve cross products are not mixed
  # First, transform the interval column to numeric (if not so already)
  modVarByXsNamesFin$Interval <- as.numeric(modVarByXsNamesFin$Interval)
  for (q in 1:nrow(modVarByXsNamesFin)) {
    if ((modVarByXsNamesFin[q, "Interval"] >= 2) & !(any(varContsLargeXsDf[ , modVarByXsNamesFin[q, "varCodeWithXs"]] %>% replace_na(0) > 0))) {
      # all values are negative (or zero)
      modVarByXsNamesFin[q, "Interval"] <- modVarByXsNamesFin[q, "Interval"] + 0.1
    } else if ((modVarByXsNamesFin[q, "Interval"] >= 2) & !(any(varContsLargeXsDf[ , modVarByXsNamesFin[q, "varCodeWithXs"]] %>% replace_na(0) < 0))) {
      # all values are positive (or zero)
      modVarByXsNamesFin[q, "Interval"] <- modVarByXsNamesFin[q, "Interval"] + 0.2
    }
  }
  # reorder to integers
  modVarByXsNamesFin$Interval <- match(modVarByXsNamesFin$Interval, modVarByXsNamesFin$Interval %>% unique() %>% sort())
  
  # Decomposition steps
  intCumulativeDb <- lapply(1:max(modVarByXsNamesFin$Interval), function(x) 
    rowSums(cbind(varContsLargeXsDf[,modVarByXsNamesFin[modVarByXsNamesFin$Interval < x, "varCodeWithXs"]], 
                  cbind(rep(0, nrow(varContsLargeXsDf)), rep(0, nrow(varContsLargeXsDf)))))) %>%
    do.call(cbind, .) %>% 
    `colnames<-`(1:max(modVarByXsNamesFin$Interval)) %>%
    as.data.frame()
  postExpDb <- lapply(1:length(modVarFinalWithFixed), function(x) 
    if(modVarByXsNamesFin[modVarByXsNamesFin$varCodeWithXs == modVarFinalWithFixed[x], "Interval"] == 1) {
      exp(varContsLargeXsDf[,modVarFinalWithFixed[x]]*param1)-exp(varContsLargeXsDf[,modVarFinalWithFixed[x]]*param2)+
        as.numeric((varContsLargeXsDf[,modVarFinalWithFixed[x]] > 0))
    } else {
      exp(intCumulativeDb[,modVarByXsNamesFin[modVarByXsNamesFin$varCodeWithXs == modVarFinalWithFixed[x], "Interval"]]+
            varContsLargeXsDf[,modVarFinalWithFixed[x]]*param1)-
        exp(intCumulativeDb[,modVarByXsNamesFin[modVarByXsNamesFin$varCodeWithXs == modVarFinalWithFixed[x], "Interval"]]+
              varContsLargeXsDf[,modVarFinalWithFixed[x]]*param2)
    }) %>%
    do.call(cbind, .) %>%
    `colnames<-`(modVarFinalWithFixed) %>%
    as.data.frame()
  withinIntSyn <- lapply(1:max(modVarByXsNamesFin$Interval), function(x) 
    exp(rowSums(cbind(varContsLargeXsDf[,modVarByXsNamesFin[modVarByXsNamesFin$Interval <= x, "varCodeWithXs"]], 
                      rep(0, nrow(varContsLargeXsDf))))) - 
      exp(rowSums(cbind(varContsLargeXsDf[,modVarByXsNamesFin[modVarByXsNamesFin$Interval < x, "varCodeWithXs"]], 
                        cbind(rep(0, nrow(varContsLargeXsDf)), rep(0, nrow(varContsLargeXsDf)))))) - 
      rowSums(cbind(postExpDb[,modVarByXsNamesFin[modVarByXsNamesFin$Interval == x, "varCodeWithXs"]]),
              rep(0, nrow(varContsLargeXsDf))) +
      if (x == 1) {rep(1, nrow(varContsLargeXsDf))} else {rep(0, nrow(varContsLargeXsDf))}
  ) %>%
    do.call(cbind, .) %>%
    `colnames<-`(1:max(modVarByXsNamesFin$Interval)) %>%
    as.data.frame()
  
  newvarContsLargeXsDf <- lapply(1:length(modVarFinalWithFixed), function(x) 
    if (setequal(postExpDb[, x], rep(0, nrow(postExpDb)))) {postExpDb[, x]} else {
      postExpDb[, x] +
        withinIntSyn[, modVarByXsNamesFin[modVarByXsNamesFin$varCodeWithXs == modVarFinalWithFixed[x], "Interval"]] * 
        abs(postExpDb[, x]) / 
        rowSums(cbind(abs(postExpDb[, modVarByXsNamesFin[modVarByXsNamesFin$Interval == modVarByXsNamesFin[
          modVarByXsNamesFin$varCodeWithXs == modVarFinalWithFixed[x], "Interval"], "varCodeWithXs"]]),
          rep(0, nrow(varContsLargeXsDf))))}) %>%
    do.call(cbind, .) %>%
    `colnames<-`(modVarFinalWithFixed) %>%
    cbind(avmDetailsXsDf[, 1:2], .) %>%
    as.data.frame()
  
  # Replace NAs with zeros
  newvarContsLargeXsDf[is.na(newvarContsLargeXsDf)] <- 0
  # Overwrite old dataframe
  varContsLargeXsDf <- newvarContsLargeXsDf
  # Clear redundant variables
  rm(param1, param2, intCumulativeDb, postExpDb, withinIntSyn, newvarContsLargeXsDf)
  
} else {
  # No constant adjustment made
  constAdj = rep(0, length(xsNames))
}

# Standardized residuals
residTable <- avmDetailsXsDf[, c("CrossSection", "Residual")] %>% 
  filter(!is.na(Residual)) %>% 
  group_by(CrossSection) %>% 
  summarize(mean = mean(Residual), sd = sd(Residual)) %>%
  slice(rep(1:n(), each = (nrow(avmDetailsXsDf)/length(xsNames))))
avmDetailsXsDf[, "Residual Std"] <- (avmDetailsXsDf$Residual - residTable$mean) / residTable$sd
rm(residTable)

# Save a histogram image for the xs residuals
for (p in 1:length(xsNames)) {
  png(file=paste("RegressionTables/Histograms/histogramXs", p, ".png", sep = ""),
      width=600, height=350)
  hist(avmDetailsXsDf$`Residual Std`[avmDetailsXsDf$CrossSection == xsNames[p]], 
       main=paste("Histogram ", xsNames[p], sep = ""), 
       xlab="Residual Std",
       col="darkmagenta", 
       breaks=20)
  dev.off()
}

# Aggregate the XS modeled variables to give variables as denoted in Variable Details tab
modVarFinalWithFixedNum <- modVarByXsNamesFin$varCodeWoXs %>% unique()
varContsXsDf <- lapply(1:length(modVarFinalWithFixedNum), function(x) 
  rowSums(varContsLargeXsDf[as.vector(modVarByXsNamesFin[modVarByXsNamesFin$varCodeWoXs == modVarFinalWithFixedNum[x],"varCodeWithXs"])])) %>%
  do.call(cbind, .) %>%
  # column names cannot have spaces
  `colnames<-`(gsub(" ", "_", modVarByXsNamesFin$Short.Variable.Name[match(modVarFinalWithFixedNum, modVarByXsNamesFin$varCodeWoXs)])) %>% 
  data.frame(select(avmDetailsXsDf, 1:2), .)

#Output; Actual vs Model Totaled
avmDetailsTotDf <- aggregate(. ~ OBS, data=avmDetailsXsDf[,-1], sum) %>% select(-"Residual Std") # all cols bar the XS column
residMeanCol <- avmDetailsTotDf$Residual[!is.na(avmDetailsTotDf$Residual)] %>% mean() %>% rep(nrow(avmDetailsTotDf))
residSdCol <- avmDetailsTotDf$Residual[!is.na(avmDetailsTotDf$Residual)] %>% sd() %>% rep(nrow(avmDetailsTotDf))
avmDetailsTotDf[, "Residual Std"] <- (avmDetailsTotDf$Residual - residMeanCol) / residSdCol

# Save a histogram image for the total residuals
png(file="RegressionTables/Histograms/histogramTot.png",
    width=600, height=350)
hist(avmDetailsTotDf[, "Residual Std"], 
     main="Histogram Total", 
     xlab="Residual Std",
     col="darkmagenta",
     breaks=20)
dev.off()

### Plot Posterior distribution
if (regApproach == "bayesian"){
  
  # Density overlay
  png(file="RegressionTables/Histograms/posteriorCheckDens.png",
      width=600, height=350)
  plot(pp_check(bayFit, ndraws = n_transiction, type = "dens_overlay"))
  dev.off()
  
  # Stat 2d
  png(file="RegressionTables/Histograms/posteriorCheckStat.png",
      width=600, height=350)
  plot(pp_check(bayFit, ndraws = n_transiction, type = "stat_2d"))
  dev.off()
}

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

#Output; Regression Variable Details
regVariableDetailsDf <- data.frame(row.names=modVarFinalWithFixed,
                                   Code=modVarFinalWithFixed, 
                                   Variable=modVarByXsNamesFin[,"Short.Variable.Name"],
                                   xsGroup=modVarByXsNamesFin[,"xsGroupName"],
                                   Coefficient=coeff, 
                                   tStat=tStats,
                                   pValue=pValues, 
                                   StandardError=standardErrors,
                                   Rhat = rhat,
                                   RatioEss = ratioESS,
                                   AbsCont=apply(varContsLargeXsDf[, 3:ncol(varContsLargeXsDf)], 2, sum), # sums the variable contribution columns                                 
                                   PerCont=apply(varContsLargeXsDf[, 3:ncol(varContsLargeXsDf)], 2, sum) / sum(varContsLargeXsDf[, 3:ncol(varContsLargeXsDf)])) %>%
  mutate(pValue = round(pValue, digit = 10)) # round to avoid text output errors

# Calculate R2 for every cross section
RSqByXs <- lapply(1:length(xsNames), function(x) 
  cor(avmDetailsXsDf[((x-1)*obsCnt):(x*obsCnt), "Actual"], avmDetailsXsDf[((x-1)*obsCnt):(x*obsCnt), "Model"], use = "complete.obs") ^ 2) %>%
  do.call(rbind, .) %>% as.vector()

if (logModel == "no") {
  
  # Calculate Durbin Watson Statistic for every cross section
  DwByXs <- lapply(1:length(xsNames), function(x) 
    dwtest(avmDetailsXsDf[((x-1)*obsCnt):(x*obsCnt), "Actual"] ~ avmDetailsXsDf[((x-1)*obsCnt):(x*obsCnt), "Model"], 
           order.by = NULL, alternative = c("greater", "two.sided", "less"), iterations = 15, exact = NULL, tol = 1E-10)[1]) %>%
    do.call(rbind, .) %>% do.call(rbind, .) %>% as.vector()
  
} else {
  
  # Calculate Durbin Watson Statistic for every cross section
  DwByXs <- lapply(1:length(xsNames), function(x) 
    dwtest(log(avmDetailsXsDf[((x-1)*obsCnt):(x*obsCnt), "Actual"]) ~ log(avmDetailsXsDf[((x-1)*obsCnt):(x*obsCnt), "Model"]), 
           order.by = NULL, alternative = c("greater", "two.sided", "less"), iterations = 15, exact = NULL, tol = 1E-10)[1]) %>%
    do.call(rbind, .) %>% do.call(rbind, .) %>% as.vector()
  
}

# Calculate weighted R2 and weighted DW
if (length(xsWeightings) > 1) {
  RSqTotalWghtd <- sum(RSqByXs * xsWeightings) / sum(xsWeightings)
  DwTotalWghtd <- sum(DwByXs * xsWeightings) / sum(xsWeightings)
  
} else {
  RSqTotalWghtd <- mean(RSqByXs)
  DwTotalWghtd <- mean(DwByXs)
}

#Output; Regression Variable Details, by input variable, stacked
regVarDetailsStackedDf <- regVariableDetailsDf %>%
  select(c("Code", "Variable", "Coefficient", "StandardError", "tStat", "pValue", "Rhat", "RatioEss")) %>%
  `colnames<-`(c("Code", "Variable", "1.Coefficient", "4.StandardError", "2.tStat", "3.pValue", "5.Rhat", "6.RatioESS")) %>%
  cbind(modVarByXsNamesFin[ , c("varCodeWoXs", "Variable", paste("dum.", xsNames, sep = ""))]) %>%
  reshape(direction = "long", 
          varying = c("1.Coefficient", "4.StandardError", "2.tStat", "3.pValue", "5.Rhat", "6.RatioESS"),
          v.names = "Value",
          idvar = c("VarName"),
          timevar = "Metric",
          times = c("1.Coefficient", "4.StandardError", "2.tStat", "3.pValue", "5.Rhat", "6.RatioESS"))
# multiply the values column by the cross section dummies
regVarDetailsStackedDf <- lapply(1:length(xsNames), function(x)
  regVarDetailsStackedDf[, paste("dum.", xsNames[x], sep = "")] * regVarDetailsStackedDf$Value) %>%
  do.call(cbind, .) %>%
  `colnames<-`(xsNames) %>%
  cbind(regVarDetailsStackedDf, ., TempOrder = match(regVarDetailsStackedDf$varCodeWoXs, modVarFinalWithFixedNum))
# Variable Contributions Totaled
regVarDetailsStackedDf <- aggregate(. ~ varCodeWoXs + Variable + Metric + TempOrder, 
                                    data=regVarDetailsStackedDf[,c(xsNames, "varCodeWoXs", "Metric", "Variable", "TempOrder")], 
                                    sum, na.action = 'na.pass') %>%
  `colnames<-`(c("Code", "Variable", "Metric", "TempOrder", xsNames)) %>%
  select(c("Metric", "Code", "Variable", "TempOrder", all_of(xsNames))) %>% # rearrange column order
  .[with(., order(Metric, TempOrder)), ] %>% # sort by metric, then by code name
  select(-c("TempOrder")) %>% # drop the row sorter variable
  rbind(c("0.Rsq", NA, NA, RSqByXs), 
        c("0.DW", NA, NA, DwByXs), 
        c("0.LogBiasAdj", NA, NA, constAdj), 
        .) # Attach the cross section R2s and DWs

#Output; Category stats
regCatStatsDf <- regVariableDetailsDf %>%
  select(c("Variable", "AbsCont", "PerCont")) %>%
  left_join(VariableDetailsCsv[, c("Short.Variable.Name", "Category")], by = c("Variable"="Short.Variable.Name")) %>%
  select(c("Category", "AbsCont", "PerCont")) %>%
  aggregate(. ~ Category, data=., sum)

#Output; Regression Model  Details
modelDetailsDf <- rbind(rSq=c("Topline", rsq, NA),
                        AdjRSq=c("Topline", adjR2, NA),
                        WghtdRsq=c("Topline", RSqTotalWghtd, NA),
                        VariableCount=c("Topline", length(coeff), NA),
                        ObservationCount=c("Topline", length(fitted_values), NA),
                        CrossSectionCount=c("Topline", length(xsNames), NA),
                        DegreesOfFreedom=c("Topline", length(fitted_values)-length(coeff), NA),
                        ModelErrorVariance=c("Topline",modErrVar, NA),
                        ModelStandardError=c("Topline",modStdErr, NA),
                        DurbinWatson=c("Serial Correlation", dwStat, dwPVal),
                        WghtdDw=c("Serial Correlation", DwTotalWghtd, NA),
                        BreuschGodfrey=c("Serial Correlation",bgStat, bgPVal),
                        BreuschPagan=c("Heteroskedasticity",bpStat, bpPVal),
                        ARCH1=c("Heteroskedasticity", archStat, archPVal),
                        JarqueBera=c("Normality of Residual",jbStat, jbPVal),
                        RamseyReset=c("Functional Form",rrStat, rrPVal),
                        RhatSigma=c("Bayesian", rhatSigma, NA),
                        RhatLPrior=c("Bayesian", rhatLPrior, NA),
                        RhatLPosterior=c("Bayesian", rhatLPost, NA),
                        RatioESSSigma=c("Bayesian", ratioESSSigma, NA),
                        RatioESSLPrior=c("Bayesian", ratioESSLPrior, NA),
                        RatioESSLPosterior=c("Bayesian", ratioESSLPost, NA),
                        LowestBMFIChain=c("Bayesian", lowestBMFI, NA),
                        noDivergences=c("Bayesian", numDivergences, pctDivergences)) %>%
  as.data.frame %>%
  setNames(c("Category", "Statistic", "P-value"))

rm(ramseyResetTest, jarqueBeraTest, archTestOutput, breuschPaganTest, breuschGodfreyTest, constAdj)

#Run Details (to save time in the next run)
prevRunDetails <- data.frame("PrevRawDataTs" = rawDataTimestamp, "PrevKpi" = kpiVarName[1])
