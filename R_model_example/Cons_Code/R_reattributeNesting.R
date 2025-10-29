
print("Reattributing Nested Contributions")

# Check if the Core or Nested column contains anything aside from Core models
if (!(all(modelConsDetailsCsv$Core.or.Nested == rep("core", nrow(modelConsDetailsCsv))))) {

  # Filter to nested models only
  nestingCalcDb <- varContsDb[varContsDb$Core.or.Nested == "nested", c("variable", "OBS", "KPI.Name", "value", "Core.or.Nested", "Nested.Categorisation", 
                                                                       "PreMedSpCont", "PostMedSpCont")]
  
  # Add on nested variable identifier column
  nestingCalcDb[, "NestedVar"] <- gsub("nested ", "", nestingCalcDb$KPI.Name)

  # # Filter down to just the post media split contributions
  # nestingCalcDb <- nestingCalcDb[(nestingCalcDb$PostMedSpCont == TRUE), ]
  
  # # Sum contributions over nested models - by week and model
  # nestAggKpiDb <- aggregate(value ~ OBS + KPI.Name, data = nestingCalcDb, FUN = sum) %>% `colnames<-`(c("OBS", "KPI.Name", "AggNestSpend"))
  # Sum contributions over nested models - by week and model - but just for the post media split totals (which will equal total media spend)
  nestAggKpiDb <- aggregate(value ~ OBS + KPI.Name, data = nestingCalcDb[(nestingCalcDb$PostMedSpCont == TRUE), ], FUN = sum) %>%
    `colnames<-`(c("OBS", "KPI.Name", "AggNestSpend"))
  
  # Attach on the total weekly nested spend
  nestingCalcDb <- cbind(AggNestSpend = nestAggKpiDb$AggNestSpend[
    match(paste(nestingCalcDb$KPI.Name, "|", nestingCalcDb$OBS, sep = ""),
          paste(nestAggKpiDb$KPI.Name, "|", nestAggKpiDb$OBS, sep = ""))],
    nestingCalcDb)

  # Calc share of nested contribution by variable
  nestingCalcDb$ShareNestValue <- with(nestingCalcDb, value / AggNestSpend)
  nestingCalcDb$ShareNestValue[is.na(nestingCalcDb$ShareNestValue)] <- 0

  # If the AggNestSpend is zero, we still need some instructions on where to allocate nested contribution (e.g. in the case of adstocked vars in main model)
  nestingCalcDb[mapply(all, nestingCalcDb$AggNestSpend == 0, nestingCalcDb$variable == "constant"), "ShareNestValue"] <- 1
  
  # Update Nested Categorisation column - direct is now a nested channel
  for (x in 1:nrow(nestingCalcDb)) {
    if (nestingCalcDb[x, "Nested.Categorisation"] == "direct") {
      nestingCalcDb[x, "VarNameNew"] <- substring(nestingCalcDb[x, "KPI.Name"], 8, 999)
    } else {
      nestingCalcDb[x, "VarNameNew"] <- nestingCalcDb[x, "Nested.Categorisation"]
    }
  }
  
  # Get names of non-nested KPIs
  kpiNameNoNest <- modelConsDetailsCsv$KPI.Name[modelConsDetailsCsv$Core.or.Nested == "core"]

  # Replicate for every model/cross section
  nestingCalcDb <- cbind(kpiNameNew = rep(kpiNameNoNest, each = nrow(nestingCalcDb)) ,
                       do.call("rbind", replicate(length(kpiNameNoNest), nestingCalcDb, simplify = FALSE)))

  # Look up pre nesting contribution
  nestingCalcDb <- cbind(nestingCalcDb, wholeNestCont = varContsDb$value[
    match(paste(nestingCalcDb$kpiNameNew, nestingCalcDb$OBS, nestingCalcDb$NestedVar, sep = "|"),
          paste(varContsDb$KPI.Name, varContsDb$OBS, varContsDb$variable, sep = "|"))])
  nestingCalcDb$wholeNestCont[is.na(nestingCalcDb$wholeNestCont)] <- 0
  
 #  write.csv(nestingCalcDb,"Cons_Output/temp.csv", row.names = FALSE)
  
  # Calc share of nested contribution by variable
  nestingCalcDb$ReattributedValue <- with(nestingCalcDb, wholeNestCont * ShareNestValue)

  # Add nesting detail columns to varContsDb
  varContsDb$PreNestCont <- !(grepl("nested ", varContsDb$KPI.Name, fixed = TRUE))
  varContsDb$PostNestCont <- (!(varContsDb$variable %in% unique(nestingCalcDb$NestedVar)) & !(grepl("nested ", varContsDb$KPI.Name, fixed = TRUE)))

  # Aggregate the direct contributions
  nestingCalcDb <- aggregate(ReattributedValue ~ VarNameNew + OBS + kpiNameNew + PreMedSpCont + PostMedSpCont, data = nestingCalcDb, FUN = sum) %>%
    `colnames<-`(c("variable", "OBS", "KPI.Name", "PreMedSpCont", "PostMedSpCont", "value"))

  # Add nesting detail columns to varContsDb
  nestingCalcDb$PreNestCont <- rep(FALSE, nrow(nestingCalcDb))
  nestingCalcDb$PostNestCont <- rep(TRUE, nrow(nestingCalcDb))

  # Left join details
  nestingCalcDb <- merge(x=nestingCalcDb, y=modelConsDetailsCsv, by.x = "KPI.Name", by.y = "KPI.Name")
  nestingCalcDb <- merge(x=nestingCalcDb, y=obsDetailsCsv, by.x = "OBS", by.y = "OBS")
  nestingCalcDb <- merge(x=nestingCalcDb, y=varConsDetailsCsv, by.x = "variable", by.y = "Variable.Name")

  # reorder columns and merge
  nestingCalcDb <- nestingCalcDb[, colnames(varContsDb)]
  varContsDb <- rbind(varContsDb, nestingCalcDb)

  # # temp export
  # write.csv(varContsDb,"Cons_Output/nestedTemp.csv", row.names = FALSE)

  } else {
  
    # Do nothing
    
    # # Only includes Core models - no nesting required
    # varContsDb <- varContsDb %>%
    #   cbind(PreNestCont = rep(TRUE, nrow(varContsDb)), 
    #         PostNestCont = rep(TRUE, nrow(varContsDb))
    #         )
  
  }
