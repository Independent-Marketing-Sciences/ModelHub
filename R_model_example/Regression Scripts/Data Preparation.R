# VARIABLE NAMES WITH CROSS SECTION SUBSTITUTION APPLIED *************************************************************

print("2.1 Substituting Cross Section specific variable names")

# Tidy raw csv by changing all values to numeric and removing blanks and NAs
RawInputCsv <- RawInputCsv %>%
  mutate(across(-all_of("obs"), ~ ifelse(. == "", 0, as.numeric(as.character(.)))))

# Check for NAs and print NA count
na_counts <- sapply(RawInputCsv, function(x) sum(is.na(x)))

# New vector containing both kpi and modeled variable names
kpiAndModVarNames <- c(kpiVarName, modelledVarNames)

# Create grid of combo variable names required for modeling
subVarNames <- rep(kpiAndModVarNames, times = length(xsNames)) %>%
  matrix(nrow = length(kpiAndModVarNames), ncol = length(xsNames)) %>%
  as.data.frame(stringsAsFactors = FALSE)
subVarNames <- lapply(1:length(xsNames), function(x) mgsub(pull(subVarNames, x), paste(".", xsCat, ".", sep = ""), as.character(as.vector(xsDetailsCsv[x,])))) %>%
  do.call(rbind, .) %>%
  as.data.frame(stringsAsFactors = FALSE) %>%
  `colnames<-`(c("V0", unique(VariableDetailsCsv$Index))) # KPI denoted as V0

# Unique list of substituted variable names
uniqueSubVarNames <- subVarNames %>%
  gather() %>%
  unique() %>%
  rbind(., c("VOBS", identVarName)) %>%
  # adding in reference points for later
  # left_join(VariableDetailsCsv[, c("Index", "Reference.Point")], by = c("key"="Index")) %>%
  # `colnames<-`(c("SourceCode", "Names", "RefPoint"))
  left_join(VariableDetailsCsv[, c("Index", "Reference.Point", "Coeff.Min", "Coeff.Max", "Importance")], by = c("key"="Index")) %>%
  `colnames<-`(c("SourceCode", "Names", "RefPoint", "CoeffMin", "CoeffMax", "Importance"))

# SUBSTITUTION (PIPING) SETUP ********************************************************************************************************************************
# ************************************************************************************************************************************************************

# We need to amend our unique sub variable names list such that it includes all the piping value permutations. 
# Must be done before we transform the data

subData <- VariableDetailsCsv$Substitution %>%
  gsub(" ", "", .) %>%
  strsplit("),") %>%
  unique() %>%
  unlist() %>%
  gsub(")", "", .) %>%
  sort()
subNames <- substr(subData, 1, 2) # pipe names
subValues <- substr(subData, 4, 999) %>% # possible values for each pipe name
  strsplit(",")
names(subValues) <- subNames

rm(subData)

# Generate substitution options grid - pipe values in columns, permutations in rows
subOptionsGrid <- subValues %>%
  do.call(expand.grid, .) %>%
  lapply(as.character) %>%
  as.data.frame() %>%
  `colnames<-`(subNames)

# Get Get list of unique variables - including sub strings
subTemp <- uniqueSubVarNames$Names # set up for the below
sub.list = list()

# Generate grid showing if the sub var names can be found in the unique variable names
subFoundGrid <- lapply(1:length(subNames), function(x) str_detect(uniqueSubVarNames$Names, subNames[x])) %>% 
  do.call(cbind, .)

# Next step generates a grid;
# rows; unique variable names, with ¬ names subbed for values
# columns; an index column, then one column for each possible ¬, with their required values in the table. NA if not applicable

# list of all modeled variables - containing all possible permutations from piping
for (x in 1:nrow(subOptionsGrid)) { # number of possible permutations across all substitution combinations
  for (y in 1:length(subNames)) { # number of variables that have substitutions
    # sub out ¬ name for numerical value
    subTemp <- gsub(subNames[y], subOptionsGrid[x, y], subTemp)
  }
  sub.list[[x]] <- cbind(NamePipeSub = subTemp, tempIndex = 1:length(subTemp), 
                         ifelse(c(subFoundGrid) == T, c(subOptionsGrid[rep(1, length(subTemp)), ]) %>% unlist(), NA) %>% 
                           matrix(ncol = length(subNames)) %>% `colnames<-`(subNames))
  subTemp <- uniqueSubVarNames$Names
}

# merge all tables - across the different sub variable (¬) permutations. Note - duplicates removed later on
subVarsStacked <- do.call(rbind, sub.list)
rm(subTemp, subFoundGrid)

# Overwrite the existing uniqueSubVarNames with a longer list including all possible piping permutations

# First, add on new piping info columns  - can simplify this bit ***edit***
uniqueSubVarNamesNew <- do.call("rbind", replicate(nrow(subOptionsGrid), uniqueSubVarNames, simplify = FALSE)) %>% cbind(subVarsStacked) 
# Next, get rid of duplicates (variables that did not require piping)
uniqueSubVarNamesNew = uniqueSubVarNamesNew[!duplicated(uniqueSubVarNamesNew$NamePipeSub),]
# Reorder to match original, then remove index column
uniqueSubVarNamesNew <- uniqueSubVarNamesNew[order(as.integer(uniqueSubVarNamesNew$tempIndex)),] %>% subset(select = -tempIndex)
# Lastly, overwrite
uniqueSubVarNames <- uniqueSubVarNamesNew

rm(uniqueSubVarNamesNew, subVarsStacked, sub.list, subValues)

# Update the subVarNames grid, used for stacking variables from wide to long by XS ************************************************************************

sub2.list = list()
kpiAndModVarNamesTemp <- kpiAndModVarNames

# generating new tables for each piping permutation;
# rows; modeled variables - with named XS substitution (e.g. ".CrossSection.")
# columns; index, along with variable name

for (x in 1:nrow(subOptionsGrid)) { # number of possible permutations across all substitution combinations
  for (y in 1:length(subNames)) { # number of variables that have substitutions
    kpiAndModVarNamesTemp <- gsub(subNames[y], subOptionsGrid[x, y], kpiAndModVarNamesTemp)
  }
  # note; adding on XS Grouping for lookups below
  sub2.list[[x]] <- cbind(kpiAndModVarNamesTemp, tempIndex = 1:length(kpiAndModVarNames), 
                          rbind(rep(NA, 11), VariableDetailsCsv))
  kpiAndModVarNamesTemp <- kpiAndModVarNames
}

# merge tables - can simplify this bit ***edit***
kpiAndModVarNamesNew <- do.call(rbind, sub2.list) %>% as.data.frame()
# remove duplicate rows (variables without any piping)
kpiAndModVarNamesNew = kpiAndModVarNamesNew[!duplicated(kpiAndModVarNamesNew$kpiAndModVarNamesTemp),]
# reorder to original using index column, then drop index. Keep variables and XS details for later
kpiVarAndXsDets <- kpiAndModVarNamesNew[order(as.integer(kpiAndModVarNamesNew$tempIndex)),] %>% subset(select = -tempIndex)
# Convert to vector
kpiAndModVarNamesNew <- kpiVarAndXsDets$kpiAndModVarNamesTemp
# Overwrite original
kpiAndModVarNames <- kpiAndModVarNamesNew

rm(kpiAndModVarNamesTemp, kpiAndModVarNamesNew, sub2.list)

# Create grid of combo variable names required for modeling
subVarNamesNew <- rep(kpiAndModVarNames, times = length(xsNames)) %>%
  matrix(nrow = length(kpiAndModVarNames), ncol = length(xsNames)) %>%
  as.data.frame(stringsAsFactors = FALSE)
subVarNamesNew <- lapply(1:length(xsNames), function(x) mgsub(pull(subVarNamesNew, x), paste(".", xsCat, ".", sep = ""), as.character(as.vector(xsDetailsCsv[x,])))) %>%
  do.call(rbind, .) %>%
  as.data.frame(stringsAsFactors = FALSE) %>%
  # `colnames<-`(paste("V", 0:(length(kpiAndModVarNames)-1), sep = "")) # KPI denoted as V0
  `colnames<-`(kpiAndModVarNames) # KPI denoted as V0

# Overwrite
subVarNames <- subVarNamesNew
rm(subVarNamesNew)