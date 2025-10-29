lastmon <- function(x) 7 * floor(as.numeric(x-1+4)/7) + as.Date(1-4, origin="1970-01-01")

lastsun <- function(x) 7 * floor(as.numeric(x-1+5)/7) + as.Date(1-5, origin="1970-01-01")

thissun <- function(x) 7 * floor(as.numeric(x-1+4)/7) + as.Date(1-5, origin="1970-01-08")

thissat <- function(x) 7 * floor(as.numeric(x-1+5)/7) + as.Date(1-6, origin="1970-01-08")
