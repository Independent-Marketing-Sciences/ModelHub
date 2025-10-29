library("devtools")
library("dplyr")
library("stringr")
library("remotes")
library("freepst")
library("lubridate")
library("striprtf")
library("rJava")
# install.packages("rJava")

  # https://rdrr.io/github/hrbrmstr/freepst/man/read_pst.html

# Other ideas
# https://www.reddit.com/r/Outlook/comments/1cxbmir/recommendations_for_outlook_pst_file_readers/

# Set working directory from clipboard
wdDir <- readClipboard()
if (grepl("\\", paste(wdDir, " ", sep = ""), fixed = TRUE)) {
  setwd(wdDir)
} else {
  
  if (Sys.getenv("USERNAME") == "David Lanham") {
    setwd("C:/Users/David Lanham/OneDrive - im-sciences.com/Documents/RandExcelRegression")
  } else if (Sys.getenv("USERNAME") == "Huy Nguyen") {
    setwd("C:/Users/david/OneDrive/Documents/RandExcelRegression4.2.1") # to update
  } else if (Sys.getenv("USERNAME") == "AndreaRimondi") {
    setwd("C:/Users/AndreaRimondi/Documents/RModellingTool") # to update
  } else if (Sys.getenv("USERNAME") == "IlonaZasadzinska") {
    setwd("C:/Users/IlonaZasadzinska/Documents/RandExcelRegression") # to update
    # etc.
  }  else if (Sys.getenv("USERNAME") == "Luke Hamilton") {
    setwd("C:/Users/Luke Hamilton/Documents/R Modelling Tool") # to update
    # etc.
  } else if (Sys.getenv("USERNAME") == "VMUser") {
    setwd("C:/Users/VMUser/Documents/RModellingTool") # to update
    # etc.
  } else if (Sys.getenv("USERNAME") == "DanielHallsworth") {
    setwd("C:/Users/DanielHallsworth/Documents/R Modelling Tool") # to update
    # etc.
  }
}

load_all('Package/lanzR')

print("Step 1")

# Write as null as to make sure the code below updates the csv from the latest pst
write.csv(NULL,"Ticketing_Output/TicketingOutput.csv", row.names = FALSE)

# import the Setup tab
setupCsv <- read.csv("Ticketing_Input/tktSetup.csv", stringsAsFactors = FALSE)

# Extract string of our required pst file
pstPath <- setupCsv[setupCsv$Metric == "Ticket PST File Location", "Detail"]

# Read in previously processed Email Database from shared drive
emails_db_old <- readRDS(file = gsub(basename(pstPath), "ticketing.rds", pstPath))

# Use this to refresh the old database
# emails_db_old <- emails_db_old[1, , drop = FALSE]

print("Step 2")

# Extract emails from PST
emails_raw <- read_pst(pstPath)
emails_raw$body <- paste(emails_raw$bodyHTML, emails_raw$bodyRTS)

emails_db <- data.frame(
  TicketNumber = paste("E", c(1:nrow(emails_raw)), sep = ""),
  Sender = emails_raw$sent_by,
  Receiver = emails_raw$received_by,
  SentTime = emails_raw$sent_time %>% as.POSIXct(format = "%a %b %d %H:%M:%S BST %Y"),
  AttachmentCount = emails_raw$attachment_count,
  Subject = emails_raw$subject,
  IssueCategory = emails_raw$body %>% str_match(pattern = "Issue_Category \\s*(.*?)\\s* Issue_Name") %>% as.data.frame %>% select(2),
  IssueName = emails_raw$body %>% str_match(pattern = "Issue_Name \\s*(.*?)\\s* Issue_Summary") %>% as.data.frame %>% select(2),
  IssueSummary = emails_raw$body %>% str_match(pattern = "Issue_Summary \\s*(.*?)\\s* Additional_Info") %>% as.data.frame %>% select(2),
  AdditionalInfo = emails_raw$body %>% str_match(pattern = "Additional_Info \\s*(.*?)\\s* Additional_Links") %>% as.data.frame %>% select(2),
  AdditionalLinks = emails_raw$body %>% str_match(pattern = "Additional_Links \\s*(.*?)\\s* _end_") %>% as.data.frame %>% select(2)
)

emails_db <- emails_db %>%
  `colnames<-`(c(colnames(emails_db)[1:6], "IssueCategory", "IssueName", "IssueSummary", "AdditionalInfo", "AdditionalLinks"))

print("Step 3")

# Merge with old emails database before saving
emails_db <- rbind(emails_db_old, emails_db)
# Overwrite ticket numbers
emails_db$TicketNumber = rep("NA", nrow(emails_db))
# Sort by date received
emails_db <- emails_db[order(emails_db$SentTime), ]
# Return only unique tickets
emails_db <- emails_db[!duplicated(emails_db[, c("SentTime", "Sender")]), ]
# Give each ticket a number
emails_db$TicketNumber = paste("E", c(1:nrow(emails_db)), sep = "")

print("Step 4")

# Save as RDS on shared drive
saveRDS(emails_db,
        file = gsub(basename(pstPath), "ticketing.rds", pstPath))

# Save as CSV
write.csv(emails_db,
          # "C:/Users/David Lanham/im-sciences.com/FileShare - Documents/MasterDrive/Dev/COE/Ticketing/Emails/Output/TicketingOutput.csv", 
          "Ticketing_Output/TicketingOutput.csv", 
          row.names = FALSE,
          fileEncoding = "UTF-8"
          )

print("Complete!")

Sys.sleep(1)
