
print("Looping through and importing Models")

varContsList = list()
avmList = list()
varDetList = list()

# Below sometimes runs into a character limit with directories used

# Look through model files and merge data
for (x in 1:length(modelDirectories)) {
  if (file.exists(modelDirectories[x])) {
    # Copy over the model Excel file to the Cons_Input/Temp folder
    # This is so we don't run into issues with read_excel where the file path character limit is breached
    file.copy(modelDirectories[x], "Cons_Input/Temp")
    focusModelDir <- paste("Cons_Input/Temp/", modelFileNames[x], sep = "")
    # Copy over individual tabs
    varContsList[[x]] <- read_excel(focusModelDir, sheet = "VarConts byXS") %>% melt(id.vars=c("CrossSection", "OBS")) %>%
      cbind(fileName = rep(modelFileNames[x], nrow(.)), .)
    avmList[[x]] <- read_excel(focusModelDir, sheet = "AvM byXS") %>% melt(id.vars=c("CrossSection", "OBS")) %>%
      cbind(fileName = rep(modelFileNames[x], nrow(.)), .)
    varDetList[[x]] <- read_excel(focusModelDir, sheet = "Variable Details") %>% 
      select(1:11) %>%
      `colnames<-`(c("Index",	"Variable",	"XS Grouping",	"Reference Point",	"Interval",	"Category",	"Coeff Min",	
                     "Coeff Max",	"Importance",	"Short Variable Name",	"Substitution")) %>%
      filter(!is.na(Index))
    # Delete Excel file
    unlink(paste("Cons_Input/Temp/", modelFileNames[x], sep = ""), recursive = FALSE, force = FALSE)
  } else {
    # Update error message
    errorMessage <- paste("The following model file does not exist; ", modelDirectories[x], sep = "")
    write.csv(errorMessage,"Cons_Output/errorMessage.csv", row.names = FALSE)
    stop()
  }
}

# Below inserts dots into variable names

# # Look through model files and merge data
# for (x in 1:length(modelDirectories)) {
#   varContsList[[x]] <- openxlsx::read.xlsx(modelDirectories[x], sheet = "VarConts byXS") %>% melt(id.vars=c("CrossSection", "OBS")) %>%
#     cbind(fileName = rep(modelFileNames[x], nrow(.)), .)
#   avmList[[x]] <- openxlsx::read.xlsx(modelDirectories[x], sheet = "AvM byXS") %>% melt(id.vars=c("CrossSection", "OBS")) %>%
#     cbind(fileName = rep(modelFileNames[x], nrow(.)), .)
# }

varContsDb <- do.call(rbind, varContsList)
avmDb <- do.call(rbind, avmList)
varDetDb <- do.call(rbind, varDetList)
# Convert variable columns from factor to character
varContsDb$variable <- as.character(varContsDb$variable)
avmDb$variable <- as.character(avmDb$variable)
# Convert value columns to numeric
varContsDb$value <- as.numeric(varContsDb$value)
avmDb$value <- as.numeric(avmDb$value)
# Convert variable names to lower case
varContsDb$variable <- tolower(varContsDb$variable)
varDetDb$`Short Variable Name` <- tolower(varDetDb$`Short Variable Name`)
varDetDb$Category <- tolower(varDetDb$Category)
# Convert price and margin variable names to lower case
modelConsDetailsCsv$Price.Variable.Name <- tolower(modelConsDetailsCsv$Price.Variable.Name)
modelConsDetailsCsv$Margin.Variable.Name <- tolower(modelConsDetailsCsv$Margin.Variable.Name)

rm(avmList, varContsList, varDetList, focusModelDir)

# Checks

# Are there any duplicate variable names
if (length(tolower(varConsDetailsCsv$Variable.Name)) != length(unique(tolower(varConsDetailsCsv$Variable.Name)))) {
  # Update error message
  errorMessage <- "Duplicated variable names exist in the Variable Details Tab"
  write.csv(errorMessage,"Cons_Output/errorMessage.csv", row.names = FALSE)
  
  stop()
  
}

# Are there any variables in the Media Details tab, that are yet to be categorized in the Variable Details tab?
if (length(setdiff(unique(tolower(mediaDetailsCsv$Media.Name)), tolower(varConsDetailsCsv$Variable.Name))) != 0) {
  
  # Extract the new variables
  newVars <- setdiff(unique(tolower(mediaDetailsCsv$Media.Name)), tolower(varConsDetailsCsv$Variable.Name))
  
  # Append the new variable names onto the existing Variable Details table
  varConsDetailsCsvNew <- varConsDetailsCsv
  varConsDetailsCsvNew[(nrow(varConsDetailsCsv)+1):(nrow(varConsDetailsCsv)+length(newVars)), ] <- ""
  varConsDetailsCsvNew$Variable.Name <- c(varConsDetailsCsv$Variable.Name, newVars)
  
  # Update error message
  errorMessage <- "Some of the variables in the Media Details tab are yet to be categorised in the Variable Details tab"
  write.csv(errorMessage,"Cons_Output/errorMessage.csv", row.names = FALSE)
  
  write.csv(varConsDetailsCsvNew,"Cons_Output/newVariableDetails.csv", row.names = FALSE)
  
  stop()
  
}

# Are there any variables in the decomposition, that are yet to be categorized in the Variable Details tab?
if (length(setdiff(unique(tolower(varContsDb$variable)), tolower(varConsDetailsCsv$Variable.Name))) != 0) {
  
  # Extract the new variables
  newVars <- setdiff(unique(tolower(varContsDb$variable)), tolower(varConsDetailsCsv$Variable.Name))
  
  # Append the new variable names onto the existing Variable Details table
  varConsDetailsCsvNew <- varConsDetailsCsv
  varConsDetailsCsvNew[(nrow(varConsDetailsCsv)+1):(nrow(varConsDetailsCsv)+length(newVars)), ] <- ""
  varConsDetailsCsvNew$Variable.Name <- c(varConsDetailsCsv$Variable.Name, newVars)
  # Overwrite the Model Categorization 
  varConsDetailsCsvNew$Model.Categorisation <- ifelse(varDetDb$Category[match(varConsDetailsCsvNew$Variable.Name, 
                                                      varDetDb$`Short Variable Name`)] %>% replace_na("") == "", 
                            varConsDetailsCsvNew$Model.Categorisation, 
                            varDetDb$Category[match(varConsDetailsCsvNew$Variable.Name, varDetDb$`Short Variable Name`)] %>% replace_na(""))
  
  # varConsDetailsCsvNew$Model.Categorisation <- varDetDb$Category[match(varConsDetailsCsvNew$Variable.Name, varDetDb$`Short Variable Name`)] %>% 
  #   replace_na("")
  
  # Update error message
  errorMessage <- "Some of the variables in your decomp are yet to be categorised in the Variable Details Tab"
  write.csv(errorMessage,"Cons_Output/errorMessage.csv", row.names = FALSE)
  
  write.csv(varConsDetailsCsvNew,"Cons_Output/newVariableDetails.csv", row.names = FALSE)
  
  stop()
  
}

# Do the given price variables exist within the raw dataset?
if (!(all(unique(modelConsDetailsCsv$Price.Variable.Name) %in% colnames(rawInputCsv)))) {
  errorMessage <- "At least one price variable listed in the Model Details tab does not exist within the dataset"
  write.csv(errorMessage,"Cons_Output/errorMessage.csv", row.names = FALSE)
  stop()
}

# Do the given margin variables exist within the raw dataset?
if (!(all(unique(modelConsDetailsCsv$Margin.Variable.Name) %in% colnames(rawInputCsv)))) {
  errorMessage <- "At least one margin variable listed in the Model Details tab does not exist within the dataset"
  write.csv(errorMessage,"Cons_Output/errorMessage.csv", row.names = FALSE)
  stop()
}

