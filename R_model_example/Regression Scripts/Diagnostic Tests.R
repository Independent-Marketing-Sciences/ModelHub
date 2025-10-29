# MODEL OUTPUTS ****************************************************************************************************************************
# ******************************************************************************************************************************************


# run Durbin Watson Test
modelDw <- dwtest(modelFit, order.by = NULL, alternative = c("greater", "two.sided", "less"), 
                  iterations = 15, exact = NULL, tol = 1E-10)

# run other diagnostic tests
ramseyResetTest <- resettest(modelFit, power = 2, type = "regressor") # this one takes the longest
jarqueBeraTest <- jarque.bera.test(as.vector(modelFit$residuals))
archTestOutput <- ArchTest(as.vector(modelFit$residuals), lag=1)
breuschPaganTest <- bptest(modelFit, studentize = TRUE)
breuschGodfreyTest <- bgtest(modelFit, order = 1)

# white test is complicated; https://sramblings.wordpress.com/2017/02/07/easy-white-test-in-r/ ***

# Update names within list - from "no operator" variables to original names
names(modelFit[["coefficients"]]) = modVarByXsNames$varForPerm[match(names(modelFit[["coefficients"]]), modVarByXsNames$varNamesNoOperator)]
names(modelFit[["effects"]]) = modVarByXsNames$varForPerm[match(names(modelFit[["effects"]]), modVarByXsNames$varNamesNoOperator)]
names(modelFit[["model"]])[2:length(names(modelFit[["model"]]))] = modVarByXsNames$varForPerm[match(names(modelFit[["model"]])[2:length(names(modelFit[["model"]]))],
                                                                                                    modVarByXsNames$varNamesNoOperator)]
names(breuschGodfreyTest[["coefficients"]]) = modVarByXsNames$varForPerm[match(names(breuschGodfreyTest[["coefficients"]]), modVarByXsNames$varNamesNoOperator)]

tStats <- summary(modelFit)[["coefficients"]][, "t value"] %>% as.vector()
pValues <- summary(modelFit)[["coefficients"]][, "Pr(>|t|)"] %>% as.vector()
standardErrors <- summary(modelFit)[["coefficients"]][, "Std. Error"] %>% as.vector()

# Substitute back in the original column names for transVarByXsDataLong
colnames(transVarByXsDataLong)[3:(ncol(transVarByXsDataLong)-ncol(permGridBig))] <- 
  modVarByXsNames$varCodeWithXs[match(colnames(transVarByXsDataLong)[3:(ncol(transVarByXsDataLong)-ncol(permGridBig))], modVarByXsNames$varNamesNoOperator)]

# ADDING FIXED CONTRIBUTIONS TO MODELS *****************************************************************************************************
# ******************************************************************************************************************************************

modelFitTemp <- modelFit

# Multiply fixed coefficients by the required variables
fixedVarNames <- setdiff(modVarFinalWithFixed, modVarFinal)

if (length(fixedVarNames) != 0) {
  
  fixedConts <- mapply('*', select(transVarByXsDataLong[!is.na(transVarByXsDataLong[,3]), ], all_of(modVarFinalWithFixed)), coalesce(permGridBig[, permSelected], 0)) %>%
    as.data.frame() %>% `colnames<-`(rownames(permGridBig))
  
  # Coefficients
  modelFitTemp[["coefficients"]] <- coalesce(permGridBig[, permSelected], 0) + coalesce(modelFit$coefficients[match(row.names(permGridBig), modVarCode[permSelected][[1]])], 0)
  names(modelFitTemp[["coefficients"]]) <- rownames(permGridBig)
  # Fitted Values
  modelFitTemp[["fitted.values"]] <- modelFit[["fitted.values"]] + rowSums(fixedConts)
  # Model - first column is Actual KPI, remainder are individual variable contributions
  tempKpi <- modelFit[["model"]][1] + rowSums(fixedConts)
  tempExplStart <- modelFit[["model"]][2:(length(modVarFinal)+1)]
  tempExplNull <- matrix(0, nrow(fixedConts), length(fixedVarNames)) %>% as.data.frame() %>% `colnames<-`(fixedVarNames)
  tempExplMerged <- cbind(tempExplStart, tempExplNull)
  tempExpl <- fixedConts + tempExplMerged[, colnames(fixedConts)] %>% `colnames<-`(fixedVarNames)
  modelFitTemp[["model"]] <- cbind(tempKpi, tempExpl)
  
  # Overwrite original modelFit
  modelFit <- modelFitTemp
  
  rm(tempKpi, tempExplStart, tempExplNull, tempExplMerged, tempExpl, fixedConts, modelFitTemp)
  
}
