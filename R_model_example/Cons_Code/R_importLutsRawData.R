print("Importing Lookup Tables and Raw Data")

modelConsDetailsCsv <- read.csv("Cons_Input/modelConsDetailsCsv.csv", stringsAsFactors = FALSE)
obsDetailsCsv <- read.csv("Cons_Input/obsDetailsCsv.csv", stringsAsFactors = FALSE)
toplineDetailsCsv <- read.csv("Cons_Input/toplineDetailsCsv.csv", stringsAsFactors = FALSE)
varConsDetailsCsv <- read.csv("Cons_Input/variableConsDetailsCsv.csv", stringsAsFactors = FALSE)
mediaDetailsCsv <- read.csv("Cons_Input/mediaDetailsCsv.csv", stringsAsFactors = FALSE)

modelConsDetailsCsv <- cbind(fileName = sub("^.+\\\\", "", modelConsDetailsCsv$Directory), modelConsDetailsCsv)

# Read in raw data csv
if (file.exists(toplineDetailsCsv[toplineDetailsCsv$Metric == "Raw Data Directory", "Detail"])) {
  rawInputCsv = read.csv(toplineDetailsCsv[toplineDetailsCsv$Metric == "Raw Data Directory", "Detail"], stringsAsFactors = FALSE)
} else {
  # Update error message
  errorMessage <- paste("The following Raw Data file does not exist; ", 
                        toplineDetailsCsv[toplineDetailsCsv$Metric == "Raw Data Directory", "Detail"], sep = "")
  write.csv(errorMessage,"Cons_Output/errorMessage.csv", row.names = FALSE)
}

# Get rid of any blank lines that are read in after the last Cross Section
if (!(match("", modelConsDetailsCsv$CrossSection) %in% NA)) { 
  modelConsDetailsCsv <- modelConsDetailsCsv[1:(match("", modelConsDetailsCsv$CrossSection)-1),]
}

# Update the column name for OBS if it's changed to "?..OBS"
if (nchar(colnames(rawInputCsv)[1]) != 3) {
  names(rawInputCsv)[1] <- 'obs'
}

# Convert column headers to lower case
colnames(rawInputCsv) <- tolower(colnames(rawInputCsv))
# Format as date
rawInputCsv$obs <- as.Date(rawInputCsv$obs, tryFormats = "%d/%m/%Y")

# Convert media variable names to lower case
mediaDetailsCsv$Spend.Mod.Var.Name <- tolower(mediaDetailsCsv$Spend.Mod.Var.Name)
mediaDetailsCsv$Media.Name <- tolower(mediaDetailsCsv$Media.Name)

# Get rid of any lines after a blank in the variables (within Variable Details)
if (!(match("", varConsDetailsCsv$Variable.Name) %in% NA)) {
  varConsDetailsCsv <- varConsDetailsCsv[1:(match("", varConsDetailsCsv$Variable.Name)-1),]
}

# Convert spend formulas and all variable names to lower case
varConsDetailsCsv$Associated.Spend.Formula <- tolower(varConsDetailsCsv$Associated.Spend.Formula)
varConsDetailsCsv$Variable.Name <- tolower(varConsDetailsCsv$Variable.Name)

# Import media spends

# Get a unique list of cross sections - for .CrossSection. substitution
xs.unique <- modelConsDetailsCsv[modelConsDetailsCsv$Core.or.Nested != "Nested", "CrossSection"] %>%
  unique()

# Substitute out .CrossSection. for the XS names, and create database
mediaByXsDetails <- lapply(1:length(xs.unique), function(x) 
  cbind(str_replace_all(mediaDetailsCsv$Spend.Mod.Var.Name, ".CrossSection.", xs.unique[x])
        , mediaDetailsCsv$Spend.Mod.Var.Name,
        xs.unique[x])) %>%
  do.call(rbind, .) %>%
  as.data.frame() %>%
  `colnames<-`(c("spend.mod.var.name.byxs", "Spend.Mod.Var.Name", "CrossSection")) %>%
  # Find out which variables are XS specific, and which cover all XSs (i.e. are Total)
  mutate(XsAppliesTo = case_when(!(grepl(".CrossSection.", Spend.Mod.Var.Name)) ~ "total",
                          (grepl(".CrossSection.", Spend.Mod.Var.Name)) ~ CrossSection)) %>%
  merge(mediaDetailsCsv[, c("Media.Name", "Spend.Mod.Var.Name")], by="Spend.Mod.Var.Name", all.x = TRUE) %>%
  select("spend.mod.var.name.byxs", "Spend.Mod.Var.Name", "Media.Name", "XsAppliesTo") %>%
  unique()

# Check if any listed spend variables do not exist within the dataset
if (length(mediaByXsDetails$spend.mod.var.name.byxs[!mediaByXsDetails$spend.mod.var.name.byxs %in% colnames(rawInputCsv)]) != 0) {

  errorMessage <- paste("The following listed spend variable does not exist within your raw data; ",
        mediaByXsDetails$spend.mod.var.name.byxs[!mediaByXsDetails$spend.mod.var.name.byxs %in% colnames(rawInputCsv)][1], sep = "")
  write.csv(errorMessage,"Cons_Output/errorMessage.csv", row.names = FALSE)

  stop()

}

# write.csv(1,"Cons_Output/testMessage.csv", row.names = FALSE)

# Import in spends
mediaSpendDb <- rawInputCsv[, c("obs", mediaByXsDetails$spend.mod.var.name.byxs)]
mediaSpendDb[is.na(mediaSpendDb)] = 0

# Convert spend names to lower case
names(mediaSpendDb) <- tolower(names(mediaSpendDb))

# Convert column headers to lower case
colnames(mediaSpendDb) <- tolower(colnames(mediaSpendDb))
colnames(rawInputCsv) <- tolower(colnames(rawInputCsv))

# Obtain a list of column headers to drop from final Contributions DB and AvM DB
colsDropString <- toplineDetailsCsv[match("Columns to drop", toplineDetailsCsv$Metric), 2]
if (is.na(colsDropString)) {
  colsDropVec <- NA
} else {
  colsDropVec <- colsDropString %>%
    strsplit(split = ",") %>%
    unlist() %>%
    trimws(which = "both") %>%
    gsub(" ", ".", .)
}
