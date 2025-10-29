
print("Calculate Revenue and Margin")

# For the contributions Database

combo.row <- match(varContsDb$OBS, rawInputCsv$obs)
price.col <- match(varContsDb$Price.Variable.Name, colnames(rawInputCsv))
margin.col <- match(varContsDb$Margin.Variable.Name, colnames(rawInputCsv))

price.number <- lapply(1:nrow(varContsDb), function(x) 
  rawInputCsv[combo.row[x], price.col[x]]) %>%
  do.call(rbind, .) %>%
  as.vector()

margin.number <- lapply(1:nrow(varContsDb), function(x) 
  rawInputCsv[combo.row[x], margin.col[x]]) %>%
  do.call(rbind, .) %>%
  as.vector()

revenue.sales <- varContsDb$value * price.number
margin.sales <- revenue.sales * margin.number

varContsDb <- varContsDb %>%
  cbind(Sales.Revenue = revenue.sales, Sales.Margin = margin.sales)

# For the AvM Database

combo.row <- match(avmDb$OBS, rawInputCsv$obs)
price.col <- match(avmDb$Price.Variable.Name, colnames(rawInputCsv))
margin.col <- match(avmDb$Margin.Variable.Name, colnames(rawInputCsv))

price.number <- lapply(1:nrow(avmDb), function(x) 
  rawInputCsv[combo.row[x], price.col[x]]) %>%
  do.call(rbind, .) %>%
  as.vector()

margin.number <- lapply(1:nrow(avmDb), function(x) 
  rawInputCsv[combo.row[x], margin.col[x]]) %>%
  do.call(rbind, .) %>%
  as.vector()

revenue.sales <- avmDb$value * price.number
margin.sales <- revenue.sales * margin.number

avmDb <- avmDb %>%
  cbind(Sales.Revenue = revenue.sales, Sales.Margin = margin.sales)

rm(combo.row, margin.col, margin.number, margin.sales, price.col, price.number, revenue.sales)
