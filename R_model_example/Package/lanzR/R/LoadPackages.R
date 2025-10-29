load_packages <- function(list_packages){
  # Install packages not yet installed (if needed)
  packages <- "librarian"
  installed_packages <- packages %in% rownames(installed.packages())
  if (any(installed_packages == FALSE)) {
    install.packages(packages[!installed_packages])
  }

  # Use librarian to install, update, and load packages (if needed)
  librarian::shelf(list_packages, quiet = TRUE)
}
