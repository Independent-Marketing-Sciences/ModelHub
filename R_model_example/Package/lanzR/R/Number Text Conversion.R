
text.to.number <- function (text_vector) {

  number_vector <- text_vector %>%
    gsub(",", "", .) %>%
    gsub("bn", "*1000000000", .) %>%
    gsub("m", "*1000000", .) %>%
    gsub("k", "*1000", .) %>%
    gsub("%", "*0.01", .) %>%
    gsub("B", "*1000000000", .) %>%
    trimws(which = c("both")) %>%
    lapply(function(x) eval(parse(text=c(x)))) %>%
    do.call(rbind, .) %>%
    drop() %>%
    as.numeric()

  return(number_vector)

}

to.lower.db <- function (db.input) {

  db.x <- data.frame(lapply(db.input,
                            function(variables) {
                              if (is.character(variables)) {
                                return(tolower(variables))
                                } else {
                                  return(variables)
                                  }
                              }),
                     stringsAsFactors = FALSE)

return(db.x)

}
