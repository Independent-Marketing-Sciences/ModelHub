#' Get all messages in an OST/PST
#'
#' @param path path to OST/PST
#' @return data frame
#' @export
#' @examples
#' read_pst(system.file("extdata/example-2013.ost", package="freepst"))
#' read_pst(system.file("extdata/dist-list.pst", package="freepst"))
read_pst <- function(path) {

  # path <- "C:\\Users\\David Lanham\\im-sciences.com\\FileShare - Documents\\MasterDrive\\Dev\\COE\\Ticketing\\Emails\\Archive\\ticketingDlManual.pst"

  path <- path.expand(path)
  if (!file.exists(path)) stop(sprintf("'%s' not found.", path), call.=FALSE)
  f <- new(J("com.pff.PSTFile"), path)

  rf <- f$getRootFolder()

  depth <- -1

  msgs <- list()

  process_folder <- function(folder) {

    if (folder$hasSubfolders()) {
      child_folders <- folder$getSubFolders()
      lapply(as.list(child_folders), process_folder)
    }

    if (folder$getContentCount() > 0) {

      repeat {
        email <- folder$getNextChild()
        if (is.jnull(email)) break
        if (email$getMessageClass() == "IPM.Microsoft.ScheduleData.FreeBusy") next
        tmp <- list(
          folder = folder$getDisplayName() %l0% "",
          sent_by = email$getSenderName() %l0% "",
          sent_by_addr = email$getSenderEmailAddress() %l0% "",
          received_by = email$getReceivedByName() %l0% "",
          received_by_addr = email$getReceivedByAddress() %l0% "",
          recipients = email$getRecipientsString() %l0% "",
          sent_time = email$getClientSubmitTime()$toString() %l0% "",
          delivery_time = email$getMessageDeliveryTime()$toString() %l0% "",
          importance = email$getImportance() %l0% "",
          priority = email$getPriority() %l0% "",
          attachment_count = email$getNumberOfAttachments() %l0% "",
          subject = email$getSubject() %l0% "",
          bodyHTML = email$getBodyHTML() %l0% "" %>% htm2txt() %>% gsub("\n", " ", .),
          bodyRTS = email$getRTFBody() %l0% "" %>% strip_rtf() %>% paste(collapse = "") %>%
            gsub("\\*\\| ", "", .) %>% gsub(" \\| ", " ", .) %>% gsub("&quot;", "'", .),
          # body = paste(email$bodyHTML, email$bodyRTS, collapse = ""),
          headers = email$getTransportMessageHeaders() %l0% "",
          tostr = email$toString() %l0% ""
        )
        msgs <<- c(msgs, list(tmp))
      }

    }

  }

  process_folder(rf)

  msgs <- do.call(rbind.data.frame, msgs)

  class(msgs) <- c("tbl_df", "tbl", "data.frame")

  msgs

  # return(dplyr::bind_rows(msgs))

}

`%l0%` <- function(x, y) if (length(x) == 0) y else x
`%||%` <- function(x, y) if (is.null(x)) y else x
`%@%` <- function(x, name) attr(x, name, exact = TRUE)
`%nin%` <- function(x, table)  match(x, table, nomatch = 0) == 0


