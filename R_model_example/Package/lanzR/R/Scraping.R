
scrape_indiv <- function (web_page, x_path) {

  value <- html_nodes(web_page, xpath = x_path) %>%
    html_text() %>%
    replace(length(.)==0, NA) %>%
    str_replace_all("[\r\n]" , "") %>%
    trimws(which = c("both")) %>%
    na_if("character(0)")

  return(value)

}


scrape_mult <- function (web_page, x_path_pt1, x_path_pt2, x_list) {

  value <- lapply(x_list, function(x) html_text(html_nodes(web_page, xpath = paste(x_path_pt1, x, x_path_pt2)))) %>%
    replace(length(.)==0, NA) %>%
    str_replace_all("[\r\n]" , "") %>%
    trimws(which = c("both")) %>%
    na_if("character(0)")

  return(value)

}
