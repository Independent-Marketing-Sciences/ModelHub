### Create the model structure

# Example of model structure:

# bf(log(kpi_val_sml_cld_nat) ~ a+b1+b2,
#             nl = TRUE) +
#   lf(a ~ 0+constant, cmc = FALSE) +
#   lf(b1 ~ 0+tax_digital_build, cmc = FALSE) +
#   lf(b2 ~ 0+seas_jan_feb_2019, cmc = FALSE)

buildBayModelStrFun <- function(varslist, nXs){

  # Define number of rows
  nrows <- length(varslist)

  # We try to speed up the code if we have only one cross-section
  if(nXs > 1){

    ### Portion of the bf function
    # Here we need to specify the structure of the model

    # Write the formula starting form the KPI. Then, Write the coefficients
    # (we have n-1, where n is the number of rows, remaining coefficients because
    # we have the y variable . The latest one doesn't have the "+" sign and we have
    # to add "nl = TRUE) +". Note that, we have n-3 in the second part because we
    # start from 0 and exclude the latest coefficient whose index is n-2.
    bf_string <- paste("bf(",varslist[1]," ~ ", # KPI
                       paste(sprintf("b%s+",seq(0,(nrows-3),1)),collapse = ""), # n-1 coefficients
                       "b",nrows-2,", nl = TRUE) + ",sep = "") # last coefficient

    ### Portion of the lf function
    # Here we need to specify the name of the variables composing the model

    # Define the intercept and then the variables for each coefficient. We start from
    # b1 (as b0 is the intercept), but the index of the first variable starts from 3
    # (as 1 is y and 2 is usually the constant).
    lf_string <- paste0(paste0(sprintf("lf(b%s ~ 0+",seq(0,(nrows-3),1)), # Specify variables for each coefficient
                               varslist[seq(2,(nrows-1),1)],", cmc = FALSE) + ",collapse = ""),
                        "lf(b",nrows-2," ~ 0+",varslist[nrows],", cmc = FALSE)",sep = "")

  }else{

    # Portion of the bf function
    bf_string <- paste("bf(",varslist[1]," ~ ", # KPI
                       "a+", # Intercept
                       paste(sprintf("b%s+",seq(1,(nrows-3),1)),collapse = ""), # n-2 coefficients
                       "b",nrows-2,", nl = TRUE) + ",sep = "") # last coefficient



    #bf_init_seq <- paste("bf(",log(y)," ~ a+", sep = "")
    #bf_coef_seq <- paste(sprintf("b%s+",seq(1:(nrows-2))),collapse = "")
    #bf_string <- paste(bf_init_seq,bf_coef_seq,"b",nrows-1,", nl = TRUE) + ",sep = "")

    # Portion of the lf function
    lf_string <- paste0("lf(a ~ 1, center = TRUE) + ",paste0(sprintf("lf(b%s ~ 0+",seq(1,(nrows-3),1)), # Specify variables for each coefficient
                               varslist[seq(3,(nrows-1),1)],", cmc = FALSE) + ",collapse = ""),
                        "lf(b",nrows-2," ~ 0+",varslist[nrows],", cmc = FALSE)",sep = "")


    # #lf_init_seq <- "lf(a ~ 1, center = TRUE) + "
    # #lf_coef_seq <- paste(sprintf("lf(b%s ~ 0+v%s, cmc = FALSE) + ",seq(2:(nrows-1)),
    #                              seq(2:(nrows-1))+1),collapse = "")
    # #lf_string <- paste(lf_init_seq,lf_coef_seq,"lf(b",nrows-1," ~ 0+v",
    #                    nrows,", cmc = FALSE)",sep = "")
  }

  # Combine the two portions
  out <- paste(bf_string,lf_string,sep = "")

  # Return output
  return(out)
}


### Set priors

# Example of priors setting:

# prior(normal(10, 8), class = "b", nlpar = "a") +
#   prior(normal(0, 8), class = "b", nlpar = "b1") +
#   prior(gamma(3,50), class = "b", nlpar = "b2", lb = 0)

writeStringOfPriors <- function(pPrior,pCoeffMin,pCoeffMax,pNumCrossSection){

  # Define number of rows
  nrows <- length(pPrior)

  # Define variables to create the prior string
  priors <- pPrior
  lb <- pCoeffMin
  ub <- pCoeffMax

  # Create the string to set the priors for each variable. We start with the intercept
  # and we keep it separate from the other because it has a different class (when we
  # have just one cross-section), then we set priors for all variables (including upper and lower bound).
  # Finally, we set the prior for the latest variable (we keep it separate so we
  # can get rid of the "+" sign)

  if(pNumCrossSection > 1){

    prior_string <- paste0(paste0("prior(",tolower(priors[seq(1,(nrows-1),1)]), # Set priors for variables
                                  sprintf(", class = \"b\", nlpar = \"b%s\", lb = ",
                                          seq(0,(nrows-2),1)),
                                  lb[seq(1,(nrows-1),1)],", ub = ",ub[seq(1,(nrows-1),1)],") + ", collapse = ""), # set lower and upper bound
                           "prior(",tolower(priors[nrows]),", class = \"b\", nlpar = \"b",nrows-1, # Set prior for the latest variable
                           "\", lb = ",lb[nrows],", ub = ",ub[nrows],")", sep = "")

  }else{

    prior_string <- paste0("prior(",tolower(priors[1]),", class = \"Intercept\", nlpar = \"a", # Set prior for the intercept
                           "\", lb = ",lb[1],", ub = ",ub[1],") + ",
                           paste0("prior(",tolower(priors[seq(2,(nrows-1),1)]), # Set priors for variables
                                  sprintf(", class = \"b\", nlpar = \"b%s\", lb = ",
                                          seq(1,(nrows-2),1)),
                                  lb[seq(2,(nrows-1),1)],", ub = ",ub[seq(2,(nrows-1),1)],") + ", collapse = ""), # set lower and upper bound
                           "prior(",tolower(priors[nrows]),", class = \"b\", nlpar = \"b",nrows-1, # Set prior for the latest variable
                           "\", lb = ",lb[nrows],", ub = ",ub[nrows],")", sep = "")

  }

  return(prior_string)
}

### Create dataframe for bayesian regression output
createMatrixForBayRegOutput <- function(pBayFitOutput,pRowNames,pDataset,pFixVal){

  renamedBayFitMatrix <- renameRowsBayRegOutput(pBayFitOutput,pRowNames)
  bayOutputMatrix <- replaceCoeffForZeroSumVariableWithFixValue(renamedBayFitMatrix,pDataset,pFixVal)

  return(bayOutputMatrix)
}

### Fix coefficients to fixed value if the original variable contain all zeros
replaceCoeffForZeroSumVariableWithFixValue <- function(pBayFitOutput,pDataset,pFixVal){

  indexToFixValue <- which(colSums(pDataset)==0) %>%
                      as.numeric()

  if(length(indexToFixValue)!= 0){pBayFitOutput[indexToFixValue,] <- pFixVal}

  return(pBayFitOutput)
}

### Rename rows in Bayesian Regression Output
renameRowsBayRegOutput <- function(pBayFitOutput,pRowNames){
  renamedBayFitOutput <- fixef(pBayFitOutput) %>%
    `row.names<-`(pRowNames)
  return(renamedBayFitOutput)
}

### Fill empty prior
fillEmptyValuesFun <- function(x,def_val){

  # If x is empty of NA, we replace it with the default value
  if(x == "" || is.na(x) || identical(x, character(0))){
    x <- def_val
  }

  return(x)
}

vfillEmptyValuesFun <- Vectorize(fillEmptyValuesFun)


### Run OLS and return the list of coefficients and variance from regression
getCoeffAndVarianceFromOLSReg <- function(pDataFrame){

  # Estimate mean and variance from OLS
  olsLinearRegression <- lm(y~.-1, data = pDataFrame)
  coeffMean <- as.numeric(olsLinearRegression$coefficients)
  coeffVar <- as.numeric(diag(vcov(olsLinearRegression)))

  return(list("coeff" = coeffMean, "variance" = coeffVar))

}

### Set constraints to coefficients
setConstraintsToCoeff <- function(pEstimateCoeff, pCoeffMin, pCoeffMax){

  coeffConstrained <- pEstimateCoeff

  # For the mean we need to take constraints into account, so we need to replace
  # the estimated coefficients to reflect constraints
  applyConstraints <- ifelse(pEstimateCoeff < pCoeffMin,
                             pCoeffMin,
                             ifelse(pEstimateCoeff > pCoeffMax,
                                    pCoeffMax,
                                    pEstimateCoeff))

  # Replace estimated coefficients with constrained ones
  # Coeff Min and Coeff Max have NAs apart from the specific constraint, so when
  # values are different from NAs, it means that we have to apply the constraint
  coeffConstrained[which(!is.na(applyConstraints))] <- applyConstraints[which(!is.na(applyConstraints))]

  return(coeffConstrained)
}

### Return priors estimated from OLS using Normal Distribution
setPriorsFromOLSUsingNormalDistr <- function(pDataFrame, pCoeffMin,
                                                  pCoeffMax, pVarScalar){

  # If nScalarVar is empty, replace it with 100
  scalarVar <- as.numeric(fillEmptyValuesFun(pVarScalar,100))

  # Run OLS and return the list of coefficients and variance from regression
  listCoeffMeanAndCoeffVar <- getCoeffAndVarianceFromOLSReg(pDataFrame)
  coeffMean <- listCoeffMeanAndCoeffVar$coeff
  coeffVar <- listCoeffMeanAndCoeffVar$variance

  # Apply constraints to the mean of coefficients
  constrainedMeanCoff <- setConstraintsToCoeff(coeffMean, pCoeffMin, pCoeffMax)

  # Apply scalar to the variance of coefficients
  # Multiply the variance by a scalar (to add uncertainty, given that here we didn't
  # specify any prior)
  scaledVarCoeff <- scalarVar*coeffVar

  # default priors (the table that we use contains the kpi in the first row, so
  # we need to create one additional "fake" prior)
  dfPriorsFromOLS <- c(paste0("Normal(",constrainedMeanCoff,",",scaledVarCoeff,")",
                        sep = ""))

  return(dfPriorsFromOLS)
}


### Create a dataframe with priors
createPriorDf <- function(pDefaultPrior,pPriorSelected,pCoeffMin,pCoeffMax,
                          pNumCrossSection){

  # Replace empty spaces (no prior specified) with the default prior (we need to do it
  # because otherwise the eval function won't work)
  priorToApply <- vfillEmptyValuesFun(pPriorSelected,pDefaultPrior)

  priorString <- writeStringOfPriors(priorToApply,pCoeffMin,pCoeffMax,pNumCrossSection)

  # Create a dataframe from string
  priorDataFrame <- eval(parse(text = priorString))

  # Replace the default prior with the empty value so the tool will apply
  # a flat prior
  priorDataFrame$prior <- gsub(pDefaultPrior,"",priorDataFrame$prior)

  return(priorDataFrame)

}

# Calculate the ratio between ESS and Number of transiction for coefficients and
# model variance, log posterior and log prior distributions.
calcESSRatio <- function(pBayFitObject,pNumTransiction){

  # Necessary to unlock statistics
  print(pBayFitObject$fit)

  ess_coeff <- pBayFitObject$fit@.MISC$summary$ess[1:(length(pBayFitObject$fit@.MISC$summary$ess)-3)]
  ess_summary <- pBayFitObject$fit@.MISC$summary$ess[(length(pBayFitObject$fit@.MISC$summary$ess)-2):(length(pBayFitObject$fit@.MISC$summary$ess))]

  ratio_ess_coeff <- ess_coeff/pNumTransiction
  ratio_ess_summary <- ess_summary/pNumTransiction

  ratios <- list("ratio_ess_coeff" = ratio_ess_coeff, "ratio_ess_summary" = ratio_ess_summary)

  return(ratios)
}
