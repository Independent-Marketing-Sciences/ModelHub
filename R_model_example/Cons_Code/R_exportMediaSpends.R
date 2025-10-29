
print("Export Media Spends")

# Write the media spends into a DB
medSpDf <- mediaSpendDb %>%
  melt(id.vars=c("obs")) %>%
  `colnames<-`(c("obs", "spend.mod.var.name.byxs", "spend")) %>%
  merge(mediaByXsDetails, by="spend.mod.var.name.byxs", all.x = TRUE) %>%
  select("obs", "Media.Name", "spend.mod.var.name.byxs", "Spend.Mod.Var.Name", "XsAppliesTo", "spend")

medSpDf <- merge(x=medSpDf, y=obsDetailsCsv, by.x = "obs", by.y = "OBS")
medSpDf <- merge(x=medSpDf, y=varConsDetailsCsv, by.x = "Media.Name", by.y = "Variable.Name")
medSpDf <- merge(x=medSpDf, y=mediaDetailsCsv[, -which(names(mediaDetailsCsv) == "Spend.Mod.Var.Name")], by.x = "Media.Name", by.y = "Media.Name")

write.csv(medSpDf,"Cons_Output/medSpDf.csv", row.names = FALSE)
