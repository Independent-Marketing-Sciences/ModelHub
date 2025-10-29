# LOOKUP RELEVANT DATA AND CONVERT FROM WIDE TO LONG *********************************************************************************************
# ************************************************************************************************************************************************

print("4.1 Regression setup")

# Reduce matrix based on modeled time period
transVarDataWide <- transVarDataWide[match(startDate, row.names(transVarDataWide)):
                                       match(endDate, row.names(transVarDataWide)), 2:ncol(transVarDataWide)] %>%
  cbind(obsList, .)

# Reduce matrix based on variables needed 
transVarDataWide <- select(transVarDataWide, c("obsList", uniqueSubVarNames$NamePipeSub))

# Count number of observations
obsCnt <- nrow(transVarDataWide)

# REFERENCE POINTS *********************************************************************************************************************************
# **************************************************************************************************************************************************

# move the obs column to the end of the transVarDataWide DB
transVarDataWide <- transVarDataWide %>% select(-obs, obs)

# Generate 'small' - i.e. the smallest non zero number
small.temp <- lapply(3:ncol(transVarDataWide)-1, function(x) 
  if (all(transVarDataWide[, x] == 0)) {0} else {
    min(transVarDataWide[transVarDataWide[, x] != 0 & !is.na(transVarDataWide[, x]), x])
  }) %>%
  do.call(cbind, .) %>%
  as.vector()

# append min, max and none reference points onto existing dates for each variable transformation
transVarDataWideRefAppend <- transVarDataWide[, 3:ncol(transVarDataWide)-1] %>%
  rbind(., "min" = apply(., 2, min), 
        "max" = apply(., 2, max), 
        "small" = small.temp, 
        "none" = c(rep(0, ncol(.))))

# Convert row names to Excel numeric. Easier to do this way around than converting the lookup to a date/character format
rownames(transVarDataWideRefAppend) <- c(as.numeric(as.Date(as.Date(row.names(transVarDataWide), tryFormats = "%d/%m/%Y")) - 
                                                      as.Date(0, origin="1899-12-30", tz='UTC')), "min", "max", "small", "none")

# Create reference point grid
refNumbers <- transVarDataWideRefAppend[uniqueSubVarNames[1:nrow(uniqueSubVarNames)-1, "RefPoint"] %>% 
                                          replace_na(., "none") %>% 
                                          sub("^$", "none", .), ] %>% # tidy blanks and na's
  as.matrix() %>%
  diag() %>%
  as.numeric() %>%
  rep(nrow(transVarDataWide)) %>%
  matrix(nrow = ncol(transVarDataWideRefAppend), ncol = nrow(transVarDataWide)) %>%
  t() %>%
  as.data.frame() %>%
  `colnames<-`(colnames(transVarDataWideRefAppend)) %>%
  `rownames<-`(rownames(transVarDataWide))

# subtract the reference points from the raw data (2 tables of data)
transVarDataWide[, 3:ncol(transVarDataWide)-1] = transVarDataWide[, 3:ncol(transVarDataWide)-1] - refNumbers

rm(transVarDataWideRefAppend, refNumbers, small.temp)

# WIDE TO LONG *************************************************************************************************************************************
# **************************************************************************************************************************************************

# (long)
transVarDataLong <- lapply(1:length(xsNames), function(x) 
  transVarDataWide[as.character(as.vector(subVarNames[x,]))] %>% 
    # `colnames<-`(paste("V", 0:(length(kpiAndModVarNames)-1), sep = ""))) %>% # KPI denoted as V0
    `colnames<-`(kpiAndModVarNames)) %>% # KPI denoted as V0
  do.call(rbind, .) %>%
  cbind("xsList" = rep(xsNames, each = obsCnt), .) %>% # attach cross section
  cbind("obsList" = rep(obsList, times = length(xsNames)), .) # attach dates

# create Cross Section Details Dummies
# 3 bindings - each xs category, each unique value within category, and binding values across cross secitons
xsDetailsDummyVars <- lapply(1:length(xsCat), function(x) 
  lapply(1:nrow(unique(select(xsDetailsCsv, xsCat[x]))), function(y)
    rep(as.integer(unique(select(xsDetailsCsv, xsCat[x]))[y,] == xsDetailsCsv[, xsCat[x]]), each=obsCnt)) %>%
    do.call(cbind, .) %>% 
    as.data.frame() %>% 
    `colnames<-`(unique(select(xsDetailsCsv, xsCat[x])) %>% unlist)) %>%
  do.call(cbind, .)

# create cross section specific variables where necessary
# by multiply existing long variables with cross section details dummies
transVarByXsDataLong <- lapply(1:(length(kpiAndModVarNames)-1), function(x) 
  if(kpiVarAndXsDets[1+x, "XS.Grouping"] == "" | is.na(kpiVarAndXsDets[1+x, "XS.Grouping"])) {
    select(transVarDataLong, 3+x)
  } else {
    lapply(1:nrow(unique(select(xsDetailsCsv, kpiVarAndXsDets[1+x, "XS.Grouping"]))), function(y) 
      select(transVarDataLong, 3+x) * 
        select(xsDetailsDummyVars, as.character(unique(select(xsDetailsCsv, kpiVarAndXsDets[1+x, "XS.Grouping"]))[y,1]))) %>%
      do.call(cbind, .) %>%
      `colnames<-`(paste(kpiAndModVarNames[x+1], "µ", 1:nrow(unique(select(xsDetailsCsv, kpiVarAndXsDets[1+x, "XS.Grouping"]))), sep = ""))
  }) %>%
  do.call(cbind, .) %>%
  cbind(select(transVarDataLong, 3), .) %>% # reattach kpi
  `rownames<-`(1:nrow(.)) %>%
  cbind("xsList" = rep(xsNames, each = obsCnt), .) %>% # attach cross section
  cbind("obsList" = rep(obsList, times = length(xsNames)), .) # attach dates

# Export the transVarByXsDataLong database if required
if (modelDetailsCsv[modelDetailsCsv$Metric == "Import Transformed Data?", "Detail"] == "yes") {
  write.csv(transVarByXsDataLong,"RegressionTables/transVarByXsLongDf.csv", row.names = FALSE)
}

# store code variable names with and without the xs extensions (for aggregation later)
modVarByXsNames <- data.frame(varCodeWithXs = colnames(select(transVarByXsDataLong, 3:ncol(transVarByXsDataLong))), 
                              varCodeWoXs = gsub("\\µ.*", "", colnames(select(transVarByXsDataLong, 3:ncol(transVarByXsDataLong))))) %>%
  left_join(kpiVarAndXsDets, by = c("varCodeWoXs"="kpiAndModVarNamesTemp")) %>%
  cbind(xsGroupIndex = gsub(".*\\µ", "", colnames(select(transVarByXsDataLong, 3:ncol(transVarByXsDataLong)))), 
        # create another version of the variable names without operations - needed for the regression stage
        varNamesNoOperator = colnames(transVarByXsDataLong[, 3:ncol(transVarByXsDataLong)]) %>% 
          gsub("[*-+/()^,!<>=-]", "ß", .) %>% gsub("'", "ß", .) %>% paste("ßßß", ., "ßßß", sep = "")) %>%
  mutate(varCodeWithXs = as.character(varCodeWithXs))
# Below naming convention needed for permutations generation
modVarByXsNames$varForPerm = ifelse(grepl("µ", modVarByXsNames$varCodeWithXs), modVarByXsNames$varCodeWithXs, modVarByXsNames$Variable)

# add column looking up the cross section categorization group name
modVarByXsNames <- cbind(modVarByXsNames, 
                         xsGroupName = lapply(1:nrow(modVarByXsNames), function(x) 
                           if(modVarByXsNames[x, "XS.Grouping"] %in% xsCat) {
                             unique(select(xsDetailsCsv, modVarByXsNames[x, "XS.Grouping"]))[as.integer(modVarByXsNames[x, "xsGroupIndex"]), 1] %>% 
                               as.character()
                           } else {"NA"}) %>%
                           do.call(rbind, .))

# add column for cross section cat column name
modVarByXsNames <- cbind(modVarByXsNames, 
                         xsGroupCat = VariableDetailsCsv[match(modVarByXsNames$varCodeWoXs, VariableDetailsCsv$Variable), "XS.Grouping"])

# add in dummies for where each cross section is active
modVarByXsNames <- lapply(1:length(xsNames), function(y)
  lapply(1:nrow(modVarByXsNames), function(x)
    if(modVarByXsNames[x, "xsGroupName"] %in% c("NA", xsDetailsCsv[y,modVarByXsNames[x, "xsGroupCat"]])) {1} else {0}) %>%
    do.call(rbind, .)) %>%
  do.call(cbind, .) %>%
  `colnames<-`(paste("dum.", xsNames, sep = "")) %>%
  as.data.frame() %>%
  cbind(modVarByXsNames, .)
# Set KPI interval to 99 - as it's never used in log decomp
modVarByXsNames[1, "Interval"] <- 99

# Apply any Cross Section Weightings to the KPIs
if (modelDetailsCsv[modelDetailsCsv$Metric == "Weight Cross Sections", "Detail"] != "none") {
  # Look up the weighting numbers to be used
  xsWeightings <- xsDetailsCsv[, modelDetailsCsv[modelDetailsCsv$Metric == "Weight Cross Sections", "Detail"]] %>%
    as.numeric()
  # Overwrite existing KPIs with weighted KPIs
  transVarByXsDataLong[, 3:ncol(transVarByXsDataLong)] <- transVarByXsDataLong[, 3:ncol(transVarByXsDataLong)] * rep(xsWeightings, each = obsCnt)
} else {
  xsWeightings <- 0
}

# Create new lookup based off sub variable names as variables rather than values (for permutation management)
modVarSubGrouped <- modVarByXsNames[, -which(names(modVarByXsNames) %in% c("varCodeWithXs", "varCodeWoXs", "xsGroupIndex", "varNamesNoOperator"))] %>%
  distinct()

# drop redundant variables
rm(xsDetailsDummyVars, transVarDataLong)