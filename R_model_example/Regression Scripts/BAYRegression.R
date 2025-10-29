################################################################################

print("5.1 Bayesian Regression")

# Settings
rstan_options(auto_write = TRUE)

### Extract information to run Bayesian Regression
nChains <- modelDetailsCsv[modelDetailsCsv$Metric == "Bayesian Chains","Detail"]
nIter <- modelDetailsCsv[modelDetailsCsv$Metric == "Bayesian Iteration","Detail"]
nWarmUp <- modelDetailsCsv[modelDetailsCsv$Metric == "Bayesian Warm-up","Detail"]
estimateMeanVar <- modelDetailsCsv[modelDetailsCsv$Metric == "Estimate Mean/Variance from OLS","Detail"]
nScalarVar <- modelDetailsCsv[modelDetailsCsv$Metric == "Scalar for Variance","Detail"]
strAdaptDelta <- modelDetailsCsv[modelDetailsCsv$Metric == "Adapt Delta","Detail"]
strMaxTreeDepth <- modelDetailsCsv[modelDetailsCsv$Metric == "Max Tree Depth","Detail"]
strInit <- modelDetailsCsv[modelDetailsCsv$Metric == "Initial Value","Detail"]
defaultPrior <- "default"
numCrossSection <- length(xsNames)

# Extract constraints to apply on coefficients (exclude first row because it's the
# dependent variable - we don't need to apply a prior to that)
coeffMinSelected <- modVarByXsNames[-1,"Coeff.Min"]
coeffMaxSelected <- modVarByXsNames[-1,"Coeff.Max"]

# Extract selected priors (exclude first row because it's the
# dependent variable - we don't need to apply a prior to that)
priorSelected <- modVarByXsNames[-1,"Prior"]

### Change variable names for the Bayesian regression
# Easier to write the model structure if we rename the variables in a way that 
# they have ordinal values contained in it, i.e. x1, x2, etc.
# First two columns are: obsList, xsList (we don't need them). Then we have the
# kpi (which is "y"), given that we start from zero we have k-1 regressors (including
# the constant). Hence we have n-4 variable to rename.
bayVarNames <- c("y",sprintf("v%0d", seq(0,length(transVarByXsDataLong)-4)))

### Create dataset for Bayesian regression (we don't need obsList, xsList), using
# variable names created above.
regBayData <- transVarByXsDataLong %>%
  select(.,-c(obsList,xsList)) %>%
  `colnames<-`(bayVarNames)

# Extract variable names
origVariableNames <- colnames(transVarByXsDataLong)[(which(colnames(transVarByXsDataLong)==kpiVarName)+1):length(transVarByXsDataLong)]

### Bayesian regression
# If we have the flag of "estimateVariance" set to "yes", we will run a standard
# OLS regression, extract the mean and the standard error squared of coefficients, 
# multiply variance by a scalar and use it as parameters for the normally distributed
# priors. Alternatively, we use flat priors for variables that didn't specify any priors
defaultPriorToApply <- defaultPrior

if(tolower(estimateMeanVar) == "yes"){
  
  defaultPriorToApply <- setPriorsFromOLSUsingNormalDistr(regBayData,coeffMinSelected,
                                        coeffMaxSelected,nScalarVar)
  
}

priors <- createPriorDf(defaultPriorToApply,priorSelected,coeffMinSelected,
                        coeffMaxSelected,numCrossSection)

# Bayesian settings
chains <- as.numeric(fillEmptyValuesFun(nChains,4))
iter <- as.numeric(fillEmptyValuesFun(nIter,2000))
warmup <- as.numeric(fillEmptyValuesFun(nWarmUp,floor(iter)/2))
adaptDelta <- as.numeric(fillEmptyValuesFun(strAdaptDelta,0.8))
maxTreeDepth <- as.numeric(fillEmptyValuesFun(strMaxTreeDepth,10))
init <- fillEmptyValuesFun(as.numeric(strInit),NULL)
baySoftware <- fillEmptyValuesFun(baySoftware,'na')

### Setting for parallel computation
ncores <- detectCores()-1
betweenChainCores <- ifelse(chains<ncores,chains,ncores)
withinChainCores <- max(floor((ncores-betweenChainCores)/chains),1) # we should set at least one core

### Bayesian Software
if(baySoftware != "python"){
  print("5.1 R Bayesian Regression");source("Regression Scripts/RBAYRegression.R")
}else{
  reticulate::py_run_file("Regression Scripts/Python Scripts/PyBayRegression.py")
  bayOutputCoeff = py$summary_to_export
  row.names(bayOutputCoeff) = origVariableNames
  bayOutput = replaceCoeffForZeroSumVariableWithFixValue(bayOutputCoeff,
                                                         regBayData, 0)
  rhat_summary <- rep(NA,3)
  ratio_ess_summary <- rep(NA,3)
  num_divergences <- NA
  pct_divergences <- NA
  bayBMFI <- NA
  lowestBayBMFI <- NA
  bay_fitted_values <- as.numeric(unlist(py$fitted_values['y_fitted']))
  bay_r2 <- py$bayesian_r2
  bay_modstderr <- py$bay_standard_error
}

### Remove variables created in this script
rm(bayVarNames,regBayData,coeffMinSelected,coeffMaxSelected,defaultPriorToApply,
   priors,priorSelected,model_structure,bform,chains,iter,warmup,ncores,betweenChainCores,
   withinChainCores,coln,nChains,nIter,nWarmUp,estimateMeanVar,nScalarVar,
   defaultPrior,numCrossSection)
