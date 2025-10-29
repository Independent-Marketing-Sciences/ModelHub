# Build Bayesian model structure
model_structure <- buildBayModelStrFun(bayVarNames,numCrossSection)
bform <- eval(parse(text=model_structure))

# Fitting Bayesian regression
bayFit <- brm(formula = bform,
              data = regBayData,
              prior = priors,
              seed = 123,
              init = init,
              chains = chains,
              iter = iter,
              warmup = warmup,
              cores = betweenChainCores,
              control = list(max_treedepth = maxTreeDepth,
                             adapt_delta = adaptDelta))

### Regression output
# See https://www.r-bloggers.com/2020/02/the-p-direction-a-bayesian-equivalent-of-the-p-value/
pd <- p_direction(bayFit) %>%
  .$pd
pvalue <- pd_to_p(pd)

### Set to zero coefficients whose variables sum to 0
# Export summary of the regression and change the row names (so we match the
# name of the variables). We have to exclude the first three columns:
# Column 1 is obs, column 2 is xsList, column 3 is the KPI (we are interested in 
# the regressors here).
# Bayesian regression returns a coefficient even if the sum of the column is 0,
# so we replace 0 to the coefficients which column sum is 0. This happens inside
# the bayOutputFun.

bayOutputCoeff <- createMatrixForBayRegOutput(bayFit,
                                              origVariableNames,
                                              regBayData,0)

### Bayesian Diagnostic
# Useful links:
# https://mc-stan.org/users/documentation/case-studies/rstan_workflow.html
# https://mc-stan.org/misc/warnings.html#divergent-transitions-after-warmup
# https://github.com/betanalpha/knitr_case_studies/blob/master/rstan_workflow/stan_utility.R

# Rhat: we have an Rhat for each coefficient and for 3 more items: 
# sigma (variance of the model), logprior and logposterior distributions
# We display rhat_coeff in the variable tab and rhat_summary in the summary tab
rhat_coeff <- rhat(bayFit)[1:(length(rhat(bayFit))-3)]
rhat_summary <- rhat(bayFit)[(length(rhat(bayFit))-2):(length(rhat(bayFit)))]

# ESS
# We have ESS / n_transiction that should be greater than 0.001. We display one by
# coefficient in the variable tab and the ones related to sigma, logprior and logposterior
# in the summary tab
ratios <- unname(bayesplot::neff_ratio(bayFit))
ratio_ess_coeff <- ratios[1:(length(ratios)-3)]
ratio_ess_summary <- ratios[(length(ratios)-2):length(ratios)]

# Divergences
# Ideally we don't want any divergence in the MCMC (Monte Carlo Markov Chain) iteration
n_transiction <- (iter-warmup)*chains
num_divergences <- get_num_divergent(bayFit$fit)
pct_divergences <- num_divergences/n_transiction

# BMIF
# Ideally we want to have a BMFI greater than 0.3 for all chains
bayBMFI <- get_bfmi(bayFit$fit)
lowestBayBMFI <- min(bayBMFI)

# fitted values
bay_fitted_values <- predict(bayFit)[,1]

# Bayesian R-squared
bay_r2 <- bayes_R2(bayFit)[1]

# Bayesian R-squared
bay_modstderr <- bayes_R2(bayFit)[2]

### Final Output for Coefficients
bayOutput <- cbind(bayOutputCoeff,pvalue,rhat_coeff,ratio_ess_coeff)