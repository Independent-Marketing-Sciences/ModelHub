adstock <- function (series.x, ads.rate) {

  ads.x <- rep(0, length(series.x))

  for (i in 1:length(series.x)) {
    if (i == 1) {
      ads.x[i] <- series.x[i]
    } else {
      ads.x[i] <- series.x[i] + ads.x[i-1] * ads.rate
      }
    }

  return(ads.x)

}

n_adstock <- function (series.x, ads.rate) {

  ads.x <- rep(0, length(series.x))

  for (i in 1:length(series.x)) {
    if (i == 1) {
      ads.x[i] <- series.x[i]
    } else {
      ads.x[i] <- series.x[i] + ads.x[i-1] * ads.rate
    }
  }

  # ads.x <- ads.x * (sum(series.x) / sum(ads.x))
  ads.x <- ads.x * (1 - ads.rate)

  return(ads.x)

}

dimret <- function(series.x, dr.info, pctConv = TRUE) {

  dr.x <- rep(0, length(series.x))
  dr.alpha <- 0

  if (sum(series.x) != 0) {

    if (pctConv == TRUE) {
      dr.alpha <- -1 * log(1 - dr.info) / mean(series.x[series.x > 0])
    } else {
      dr.alpha <- dr.info
    }

    dr.x <- 1 - exp(-1 * dr.alpha * series.x)

  } else {

    dr.x <- series.x

  }

  return(dr.x)

}


n_dimret <- function(series.x, dr.info, pctConv = TRUE) {

  dr.x <- rep(0, length(series.x))
  dr.alpha <- 0

  if (sum(series.x) != 0) {

    if (pctConv == TRUE) {
      dr.alpha <- -1 * log(1 - dr.info) / mean(series.x[series.x > 0])
    } else {
      dr.alpha <- dr.info
    }

    dr.x <- 1 - exp(-1 * dr.alpha * series.x)

    dr.x <- dr.x * (sum(series.x) / sum(dr.x))

  } else {

    dr.x <- series.x

  }

  return(dr.x)

}

dimret_adstock <- function(series.x, ads.rate, dr.info, pctConv = TRUE) {

  dr.ads.x <- rep(0, length(series.x))
  dr.alpha <- 0


  for (i in 1:length(series.x)) {
    if (i == 1) {
      dr.ads.x[i] <- series.x[i]
    } else {
      dr.ads.x[i] <- series.x[i] + dr.ads.x[i-1] * ads.rate
    }
  }

  if (sum(series.x) != 0) {

    if (pctConv == TRUE) {

      # dr.alpha <- -1 * log(1 - dr.info) / mean(series.x[series.x > 0])
      dr.alpha <- -1 * log(1 - dr.info) / mean(series.x[series.x > 0 & redRawVarDataRDate$obs <= as.Date(endDate, tryFormats = c("%d/%m/%Y"))])

      } else {

        dr.alpha <- dr.info

        }

    dr.ads.x <- 1 - exp(-1 * dr.alpha * dr.ads.x)

    } else {

    # DimRet transformation is not possible - leave dr.ads.x alone

  }

  return(dr.ads.x)

}

n_dimret_adstock <- function(series.x, ads.rate, dr.info, pctConv = TRUE) {

  dr.ads.x <- rep(0, length(series.x))
  dr.alpha <- 0

  if (sum(series.x) != 0) {

    for (i in 1:length(series.x)) {
      if (i == 1) {
        dr.ads.x[i] <- series.x[i]
      } else {
        dr.ads.x[i] <- series.x[i] + dr.ads.x[i-1] * ads.rate
      }
    }


    if (pctConv == TRUE) {
      dr.alpha <- -1 * log(1 - dr.info) / mean(series.x[series.x > 0])
    } else {
      dr.alpha <- dr.info
    }

    dr.ads.x <- 1 - exp(-1 * dr.alpha * dr.ads.x)

    dr.ads.x <- dr.ads.x * (sum(series.x) / sum(dr.ads.x))

  } else {

    dr.ads.x <- series.x

  }

  return(dr.ads.x)

}

push_forward_na <- function(x) {
  na <- is.na(x)
  c(x[na], x[!na])
}

is.date <- function(x) inherits(x, 'Date')

# Simplified Asymmetric Exponential Power distribution function
# For reference, check: https://cran.r-project.org/web/packages/AEP/AEP.pdf
saep_transf <- function(x, alpha, sigma, mu, epsilon){

  if(!require("AEP", quietly = TRUE)){
    install.packages("AEP")
  }

  library("AEP")

  #   Parameters:
  #
  #   -inf < x < +inf
  #   0 < alpha <= 2
  #   sigma > 0
  #   -inf < mu < +inf
  #   -1 < epsilon < 1

  f = x*daep(x = x, alpha = alpha, sigma = sigma, mu = mu, epsilon = epsilon, log = FALSE)

  return(f)
}
