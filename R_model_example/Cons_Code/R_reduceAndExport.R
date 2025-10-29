print("Exporting tables")

# Drop any columns requested
if (!all(is.na(colsDropVec))) {
  if (all(colsDropVec %in% colnames(varContsDb))) {
    varContsDb <- select(varContsDb, -colsDropVec)
    avmDb <- select(avmDb, -colsDropVec)
  } else {
    errorMessage <- "At least one of the listed columns to remove from the report does not exist"
    write.csv(errorMessage,"Cons_Output/errorMessage.csv", row.names = FALSE)
    stop()
  }
}

# Drop all of the contribution rows for pre nesting and pre media split, if requested
if (toplineDetailsCsv[match("drop the pre split rows", toplineDetailsCsv$Metric), "Detail"] == "yes") {
  # Reduce Contributions DB 
  varContsDb <- filter(varContsDb, PostNestCont == TRUE & PostMedSpCont == TRUE) %>%
    select(-c("PreNestCont", "PostNestCont", "PreMedSpCont", "PostMedSpCont"))
} else if (toplineDetailsCsv[match("drop the pre split rows", toplineDetailsCsv$Metric), "Detail"] == "no") {
  # Don't do anything
} else {
  errorMessage <- "Invalid option for Drop the pre split rows"
  write.csv(errorMessage,"Cons_Output/errorMessage.csv", row.names = FALSE)
}

write.csv(varContsDb,"Cons_Output/contributionsDf.csv", row.names = FALSE)
write.csv(avmDb,"Cons_Output/avmDf.csv", row.names = FALSE)