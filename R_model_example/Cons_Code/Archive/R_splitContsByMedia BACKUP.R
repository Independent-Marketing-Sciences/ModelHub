
print("Split Media Contributions based on Spends")

# We're doing the media split before the nesting reattribution. For the moment, assume pre and post contributions are the same. This will be edited later on
varContsDb <- varContsDb %>%
  cbind(PreNestCont = rep(TRUE, nrow(varContsDb)), 
        PostNestCont = rep(TRUE, nrow(varContsDb))
  )

# Update such that we're not looking at Nested contribution (that could be spend)
varContsDb$PreNestCont[(varContsDb$Sales.Category == "nested")] = FALSE
varContsDb$PostNestCont[(varContsDb$Sales.Category == "nested")] = FALSE

# more here...?

# # Import in spends - to comment out
# mediaSpendDb <- rawInputCsv[, c("obs", mediaDetailsCsv$Spend.Mod.Var.Name)]
# mediaSpendDb[is.na(mediaSpendDb)] = 0

# Unique list of transformed media variables
wholeSpendFormula <- varConsDetailsCsv$Associated.Spend.Formula[!is.na(varConsDetailsCsv$Associated.Spend.Formula)] %>% gsub(" ", "", .)

# List of the raw variables contained within the unique list of substituted variable names
partSpendFormula <- gsub("[+]", "@", wholeSpendFormula) %>% strsplit("@")  %>% unlist() %>% unique()
partSpendList <- gsub("[+]", "@", wholeSpendFormula) %>% strsplit("@")

# Vector of modeled cross sections / models
# xsNames <- modelConsDetailsCsv$KPI.Name[modelConsDetailsCsv$Core.or.Nested != "nested"]
xsNames <- modelConsDetailsCsv$KPI.Name # DL changed this bit ***

# Both the PreNestedConts and PostNestedConts variables can have values of either TRUE or FALSE
booNames <- c(TRUE, FALSE)

# First 2 columns
splitMediaDb <- matrix(NA, nrow = length(wholeSpendFormula), ncol = length(partSpendFormula))
for (i in 1:length(wholeSpendFormula)) {
  for (j in 1:length(partSpendFormula)) {
    splitMediaDb[i, j] <- partSpendFormula[j] %in% partSpendList[[i]]
  }
}
splitMediaDb <- splitMediaDb %>%
  as.data.frame() %>%
  `colnames<-`(partSpendFormula) %>%
  cbind(wholeSpendFormula, .) %>%
  cbind(Variable.Name = varConsDetailsCsv$Variable.Name[!is.na(varConsDetailsCsv$Associated.Spend.Formula)], .) %>%
  melt(id.vars=c("Variable.Name", "wholeSpendFormula")) %>%
  `colnames<-`(c("Variable.Name", "wholeSpendFormula", "partSpendFormula", "temp")) %>%
  filter(temp==TRUE) %>%
  select(wholeSpendFormula, partSpendFormula, Variable.Name)

# Convert from factor to character
splitMediaDb$partSpendFormula <- as.character(splitMediaDb$partSpendFormula)

# Attach on raw modeled variable name
splitMediaDb$rawSpendVar <- rep(NA, nrow(splitMediaDb))
for (x in 1:nrow(splitMediaDb)) {
  if (substr(splitMediaDb$partSpendFormula[x], 1, 10) == "n_adstock(") {
    splitMediaDb$rawSpendVar[x] <- substr(splitMediaDb$partSpendFormula[x], 11, gregexpr(",", splitMediaDb$partSpendFormula[x])[[1]][1]-1)
  } else if (substr(splitMediaDb$partSpendFormula[x], 1, 9) == "n_dimret(") {
    splitMediaDb$rawSpendVar[x] <- substr(splitMediaDb$partSpendFormula[x], 10, gregexpr(",", splitMediaDb$partSpendFormula[x])[[1]][1]-1)
  } else if (substr(splitMediaDb$partSpendFormula[x], 1, 17) == "n_dimret_adstock(") {
    splitMediaDb$rawSpendVar[x] <- substr(splitMediaDb$partSpendFormula[x], 18, gregexpr(",", splitMediaDb$partSpendFormula[x])[[1]][1]-1)
  } else if (substr(splitMediaDb$partSpendFormula[x], 1, 15) == "dimret_adstock(") {
    splitMediaDb$rawSpendVar[x] <- substr(splitMediaDb$partSpendFormula[x], 16, gregexpr(",", splitMediaDb$partSpendFormula[x])[[1]][1]-1)
  } else if (substr(splitMediaDb$partSpendFormula[x], 1, 8) == "adstock(") {
    splitMediaDb$rawSpendVar[x] <- substr(splitMediaDb$partSpendFormula[x], 9, gregexpr(",", splitMediaDb$partSpendFormula[x])[[1]][1]-1)
  } else {
    splitMediaDb$rawSpendVar[x] <- splitMediaDb$partSpendFormula[x]
  }
  if (grepl("*", splitMediaDb$rawSpendVar[x])) {
    splitMediaDb$rawSpendVar[x] <- gsub("\\*.*", "", splitMediaDb$rawSpendVar[x])
  }
  if (grepl("/", splitMediaDb$rawSpendVar[x])) {
    splitMediaDb$rawSpendVar[x] <- gsub("/.*", "", splitMediaDb$rawSpendVar[x])
  }
}

# Attach on associated media name
splitMediaDb$Media.Name <- mediaDetailsCsv$Media.Name[match(splitMediaDb$rawSpendVar, mediaDetailsCsv$Spend.Mod.Var.Name)]

# Vector of all media short variable names
mediaSvNames <- unique(splitMediaDb$Variable.Name)

relevantSpendsByXs = list()

# Before evaluating each split formula, check that the stated media variables exist within the dataset
partSpendMedVars <- partSpendFormula %>%
  gsub("n_adstock", "", .) %>%
  gsub("[()]", "", .) %>% 
  gsub(",.*", "", .) %>%
  unique()

if (!all(partSpendMedVars %in% colnames(mediaSpendDb))) {
  errorMessage <- paste("The following media spend variable stated in the Variable Details tab does not exist; ", 
                        partSpendMedVars[match(FALSE, partSpendMedVars %in% colnames(mediaSpendDb))], sep = "")
  write.csv(errorMessage,"Cons_Output/errorMessage.csv", row.names = FALSE)
  stop()
}

for (b in 1:length(xsNames)) {
  
  # Replace any .crosssection. strings with the relevant cross section name
  partSpendFormulaForXs <- str_replace_all(partSpendFormula, ".crosssection.", modelConsDetailsCsv[b, "CrossSection"])
  
  # Generate the transformed media database (adstocks etc)
  transformedMediaSpendDb <- lapply(1:length(partSpendFormulaForXs), function(x)
    transmute(mediaSpendDb, eval(parse(text=as.character(partSpendFormulaForXs[x]))))) %>%
    do.call(cbind, .) %>%
    `colnames<-`(partSpendFormula) %>%
    cbind("obs" = as.Date(mediaSpendDb$obs, "%d/%m/%Y"), .)
  
  # Reduce the transformed media database so we're just analyzing over the modeled time period
  transformedMediaSpendDb <- transformedMediaSpendDb %>% filter(obs >= min(avmDb$OBS) & obs <= max(avmDb$OBS))
  
  relevantSpends <- lapply(1:length(mediaSvNames), function(x)
    transformedMediaSpendDb %>% select(splitMediaDb$partSpendFormula[splitMediaDb$Variable.Name == mediaSvNames[x]]) %>%
      `colnames<-`(splitMediaDb$Media.Name[splitMediaDb$Variable.Name == mediaSvNames[x]])
  ) %>%
    `names<-`(mediaSvNames)
  
  # Store list of spends relevant to XS in a new list for each cross section
  relevantSpendsByXs[[length(relevantSpendsByXs)+1]] <- relevantSpends 
  
}

rm(relevantSpends)

# Assign XS name to the list
names(relevantSpendsByXs) <- xsNames

varContReduced <- varContsDb %>% select(variable, OBS, KPI.Name, value, PreNestCont, PostNestCont)

# Some of the models may be shorter than others. This code fills any missing dates in models with zeros

obsList <- varContReduced$OBS %>% unique() %>% sort()

varContReducedAllDates <- varContReduced %>%
  select(variable, KPI.Name, PreNestCont, PostNestCont) %>%
  unique() %>%
  cbind(value = 0) %>%
  replicate(length(obsList), ., simplify = FALSE) %>%
  do.call("rbind", .) %>%
  cbind(OBS = rep(obsList, each = nrow(.) / length(obsList))) %>%
  select(variable, OBS, KPI.Name, value, PreNestCont, PostNestCont) %>%
  rbind(varContReduced, .)

varContReducedAllDates <- varContReducedAllDates[!duplicated(varContReducedAllDates[c("variable", "OBS", "KPI.Name", "PreNestCont", "PostNestCont")]),] %>%
  arrange(KPI.Name, PreNestCont, PostNestCont, variable, OBS)

varContReduced <- varContReducedAllDates

rm(obsList, varContReducedAllDates)

# Select Contributions, relevant to each short variable name
relevantConts <- lapply(1:2, function(v)
  lapply(1:2, function(w)
    lapply(1:length(xsNames), function(x)
      lapply(1:length(mediaSvNames), function(y)
        if (varContReduced %>% filter(variable == mediaSvNames[y], KPI.Name == xsNames[x], PreNestCont == booNames[v], PostNestCont == booNames[w]) %>% nrow() != 0) {
          varContReduced %>%
            filter(variable == mediaSvNames[y], KPI.Name == xsNames[x], PreNestCont == booNames[v], PostNestCont == booNames[w]) %>%
            group_by(OBS) %>%
            summarize(totalCont = sum(value))}
      ) %>%
        `names<-`(mediaSvNames)
    ) %>%
      `names<-`(xsNames)
  ) %>%
    `names<-`(booNames)
) %>%
  `names<-`(booNames)

# Calculate the split contributions
splitContsList <- lapply(1:2, function(v)
  lapply(1:2, function(w)
    lapply(1:length(xsNames), function(x)
      lapply(1:length(mediaSvNames), function(y)
        # Check if there is no contribution for this short variable name and cross section
        if (length(relevantConts[[v]][[w]][[x]][[y]]["totalCont"]) == 0) {
          # No contribution - skip
          # Otherwise, check if there is only a single media variable to allocate the contribution to
        } else if (length(relevantSpendsByXs[[x]][[y]]) == 1) {
          relevantConts[[v]][[w]][[x]][[y]]["totalCont"] %>% unlist() %>% as.data.frame() %>%
            # assign sole media name to contribution
            `colnames<-`(names(relevantSpendsByXs[[x]][[y]])[1]) %>%
            # attach on observations and cross section name
            cbind(OBS = relevantConts[[v]][[w]][[x]][[y]]["OBS"], KPI.Name = names(relevantConts[[v]][[w]])[x],
                  PreNestCont = names(relevantConts)[v], PostNestCont = names(relevantConts[[v]])[w], .) %>%
            melt(id.vars=c("KPI.Name", "OBS", "PreNestCont", "PostNestCont"))
          # Otherwise, we need to split the contribution among multiple media spends
        } else {
          # Extract the relevant contribution for this cross section and short variable name (in diagonal form)
          diag(relevantConts[[v]][[w]][[x]][[y]]["totalCont"] %>% unlist() %>% as.vector()) %*%
            # Look up relevant spend variables, calc "share of spend" and multiply through
            ((diag(1/rowSums(relevantSpendsByXs[[x]][[y]] %>% as.matrix())) %*% (relevantSpendsByXs[[x]][[y]] %>% as.matrix())) %>%
               # If there is no spend in a particular week, share contribution equally based off number of spend variables
               replace(is.na(.), 1/length(relevantSpendsByXs[[x]][[y]]))) %>%
            # attach on observations and cross section name
            cbind(OBS = relevantConts[[v]][[w]][[x]][[y]]["OBS"], KPI.Name = names(relevantConts[[v]][[w]])[x],
                  PreNestCont = names(relevantConts)[v], PostNestCont = names(relevantConts[[v]])[w], .) %>%
            melt(id.vars=c("KPI.Name", "OBS", "PreNestCont", "PostNestCont"))
        }
      ) %>%
        `names<-`(mediaSvNames)
    ) %>%
      `names<-`(xsNames)
  ) %>%
    `names<-`(booNames)
) %>%
  `names<-`(booNames)

splitConts <- splitContsList %>%
  do.call(rbind, .) %>%
  do.call(rbind, .) %>%
  do.call(rbind, .) %>%
  do.call(rbind, .) %>%
  group_by(KPI.Name, OBS, PreNestCont, PostNestCont, variable) %>%
  summarize(value = sum(value), .groups = 'drop') %>%
  cbind(., PreMedSpCont = FALSE, PostMedSpCont = TRUE)
splitConts$variable <- as.character(splitConts$variable)

# Create a blank DF - so the pivot table in Excel has some observations for at least every media channel

# First observation in modeled period
media.blank <- data.frame(KPI.Name = rep(xsNames, each = nrow(mediaDetailsCsv)),
              OBS = rep(obsDetailsCsv[match(1, obsDetailsCsv$Modelled.Period), "OBS"], nrow(mediaDetailsCsv) * length(xsNames)),
              PreNestCont = rep(TRUE, nrow(mediaDetailsCsv) * length(xsNames)),
              PostNestCont = rep(TRUE, nrow(mediaDetailsCsv) * length(xsNames)),
              variable = rep(mediaDetailsCsv$Media.Name, length(xsNames)),
              value = rep(0, nrow(mediaDetailsCsv) * length(xsNames)),
              PreMedSpCont = rep(FALSE, nrow(mediaDetailsCsv) * length(xsNames)),
              PostMedSpCont = rep(TRUE, nrow(mediaDetailsCsv) * length(xsNames)))

# Last observation in modeled period
media.blank.2 <- data.frame(KPI.Name = rep(xsNames, each = nrow(mediaDetailsCsv)),
                          OBS = rep(obsDetailsCsv[nrow(obsDetailsCsv)-match(1, rev(obsDetailsCsv$Modelled.Period))+1, "OBS"], 
                                    nrow(mediaDetailsCsv) * length(xsNames)),
                          PreNestCont = rep(TRUE, nrow(mediaDetailsCsv) * length(xsNames)),
                          PostNestCont = rep(TRUE, nrow(mediaDetailsCsv) * length(xsNames)),
                          variable = rep(mediaDetailsCsv$Media.Name, length(xsNames)),
                          value = rep(0, nrow(mediaDetailsCsv) * length(xsNames)),
                          PreMedSpCont = rep(FALSE, nrow(mediaDetailsCsv) * length(xsNames)),
                          PostMedSpCont = rep(TRUE, nrow(mediaDetailsCsv) * length(xsNames)))

# One more for the year before
media.blank.3 <- data.frame(KPI.Name = rep(xsNames, each = nrow(mediaDetailsCsv)),
                            OBS = rep(obsDetailsCsv[nrow(obsDetailsCsv)-match(1, rev(obsDetailsCsv$Modelled.Period))+1, "OBS"]-52*7, 
                                      nrow(mediaDetailsCsv) * length(xsNames)),
                            PreNestCont = rep(TRUE, nrow(mediaDetailsCsv) * length(xsNames)),
                            PostNestCont = rep(TRUE, nrow(mediaDetailsCsv) * length(xsNames)),
                            variable = rep(mediaDetailsCsv$Media.Name, length(xsNames)),
                            value = rep(0, nrow(mediaDetailsCsv) * length(xsNames)),
                            PreMedSpCont = rep(FALSE, nrow(mediaDetailsCsv) * length(xsNames)),
                            PostMedSpCont = rep(TRUE, nrow(mediaDetailsCsv) * length(xsNames)))

# check if we've specified to generate a specific additional blank date for media contributions in the Topline Details tab
if ((toplineDetailsCsv[toplineDetailsCsv$Metric == "blank dates to generate?", "Detail"] %>% tolower()) != "no") {
  
  blankDate <- toplineDetailsCsv[toplineDetailsCsv$Metric == "blank dates to generate?", "Detail"] %>% as.numeric %>% as.Date(origin = "1899-12-30")
  
  media.blank.4 <- data.frame(KPI.Name = rep(xsNames, each = nrow(mediaDetailsCsv)),
                              OBS = rep(blankDate, # this is the substitute out bit
                                        nrow(mediaDetailsCsv) * length(xsNames)), 
                              PreNestCont = rep(TRUE, nrow(mediaDetailsCsv) * length(xsNames)),
                              PostNestCont = rep(TRUE, nrow(mediaDetailsCsv) * length(xsNames)),
                              variable = rep(mediaDetailsCsv$Media.Name, length(xsNames)),
                              value = rep(0, nrow(mediaDetailsCsv) * length(xsNames)),
                              PreMedSpCont = rep(FALSE, nrow(mediaDetailsCsv) * length(xsNames)),
                              PostMedSpCont = rep(TRUE, nrow(mediaDetailsCsv) * length(xsNames)))
  
  # Merge with existing split contributions
  splitConts <- rbind(splitConts, media.blank, media.blank.2, media.blank.3, media.blank.4)
  
} else {
  
  # Merge with existing split contributions
  splitConts <- rbind(splitConts, media.blank, media.blank.2, media.blank.3)
  
}


# Merge with existing split contributions
splitConts <- rbind(splitConts, media.blank, media.blank.2, media.blank.3)

# Left Join additional columns
splitConts <- merge(x=splitConts, y=modelConsDetailsCsv, by.x = "KPI.Name", by.y = "KPI.Name")
splitConts <- merge(x=splitConts, y=obsDetailsCsv, by.x = "OBS", by.y = "OBS")
splitConts <- merge(x=splitConts, y=varConsDetailsCsv, by.x = "variable", by.y = "Variable.Name")

# Amend varContsDb to give additional media split filters
varContsDb <- varContsDb %>%
  cbind(., PreMedSpCont = TRUE, PostMedSpCont = !(varContsDb$variable %in% mediaSvNames))

# Merge the old VarContsDb with the new splitConts database
varContsDb <- varContsDb %>%
  rbind(., select(splitConts, colnames(varContsDb)))

rm(varContReduced, splitContsList, media.blank, media.blank.2, media.blank.3)
