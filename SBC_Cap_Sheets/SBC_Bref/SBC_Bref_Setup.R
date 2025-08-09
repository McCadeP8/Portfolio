library(httr)
library(jsonlite)
library(googlesheets4)

league_id <- "ka3frpayly11teos"
url <- paste0("https://www.fantrax.com/fxea/general/getLeagueInfo?leagueId=", league_id)
response <- GET(url, add_headers(Cookie = paste0("JSESSIONID=")))
  league_info <- content(response, as = "text", encoding = "UTF-8")
  league_data <- fromJSON(league_info, flatten = TRUE)
matchups_nested <- league_data$matchups
matchups_expanded1 <- matchups_nested %>%
  unnest(matchupList) %>%
  mutate(Year = 2025)

league_id <- "gtwh5nrblj1ihcat"
url <- paste0("https://www.fantrax.com/fxea/general/getLeagueInfo?leagueId=", league_id)
response <- GET(url, add_headers(Cookie = paste0("JSESSIONID=")))
league_info <- content(response, as = "text", encoding = "UTF-8")
league_data <- fromJSON(league_info, flatten = TRUE)
matchups_nested <- league_data$matchups
matchups_expanded2 <- matchups_nested %>%
  unnest(matchupList) %>%
  mutate(Year = 2024)

league_id <- "s439fm8el4exlavc"
url <- paste0("https://www.fantrax.com/fxea/general/getLeagueInfo?leagueId=", league_id)
response <- GET(url, add_headers(Cookie = paste0("JSESSIONID=")))
league_info <- content(response, as = "text", encoding = "UTF-8")
league_data <- fromJSON(league_info, flatten = TRUE)
matchups_nested <- league_data$matchups
matchups_expanded3 <- matchups_nested %>%
  unnest(matchupList) %>%
  mutate(Year = 2023)

league_id <- "4l1tn8uakrp6cwcq"
url <- paste0("https://www.fantrax.com/fxea/general/getLeagueInfo?leagueId=", league_id)
response <- GET(url, add_headers(Cookie = paste0("JSESSIONID=")))
league_info <- content(response, as = "text", encoding = "UTF-8")
league_data <- fromJSON(league_info, flatten = TRUE)
matchups_nested <- league_data$matchups
matchups_expanded4 <- matchups_nested %>%
  unnest(matchupList) %>%
  mutate(Year = 2022)

league_id <- "gt9buxv4kg3a9bgq"
url <- paste0("https://www.fantrax.com/fxea/general/getLeagueInfo?leagueId=", league_id)
response <- GET(url, add_headers(Cookie = paste0("JSESSIONID=")))
league_info <- content(response, as = "text", encoding = "UTF-8")
league_data <- fromJSON(league_info, flatten = TRUE)
matchups_nested <- league_data$matchups
matchups_expanded5 <- matchups_nested %>%
  unnest(matchupList) %>%
  mutate(Year = 2021) %>%
  select(-home.bye)

AllMatchups <- rbind(matchups_expanded1, matchups_expanded2, matchups_expanded3, matchups_expanded4, matchups_expanded5)

sheet_write(data = player_df, ss = sheet_id, sheet = "All-Time Games")


rlibrary(httr)
library(jsonlite)
library(dplyr)
library(purrr)

league_id <- "ka3frpayly11teos"
all_rosters_data <- data.frame()

for (period in 1:163) {
  cat("Processing period", period, "of 163\n")
  roster_url <- paste0("https://www.fantrax.com/fxea/general/getTeamRosters?leagueId=", league_id, "&period=", period)
  response <- GET(roster_url, add_headers(Cookie = paste0("JSESSIONID=")))
  if (status_code(response) == 200) {
    roster_json <- content(response, as = "text", encoding = "UTF-8")
    roster_data <- fromJSON(roster_json, flatten = TRUE)
      rosters <- roster_data$rosters
  for (i in 1:length(rosters)) {
      team_name <- rosters[[i]]$teamName
      roster_items <- rosters[[i]]$rosterItems
      if (!is.null(roster_items) && nrow(roster_items) > 0) {
        roster_items$team_name <- team_name
        roster_items$period <- period
        all_rosters_data <- rbind(all_rosters_data, roster_items)
      }
    }
  } else {
    warning(paste("Failed to fetch data for period", period, "- Status code:", status_code(response)))
  }
  Sys.sleep(0.1)
}

cat("Complete! Final dataframe has", nrow(all_rosters_data), "rows and", ncol(all_rosters_data), "columns\n")



url <- "https://www.fantrax.com/fxea/general/getPlayerIds?sport=NBA"
response <- GET(url, add_headers(Cookie = paste0("JSESSIONID=")))
  player_json <- content(response, as = "text", encoding = "UTF-8")
  player_data <- fromJSON(player_json, flatten = TRUE)


  player_df <- lapply(player_data, function(player) {
    data.frame(
      name = player$name,
      fantraxId = player$fantraxId,
      stringsAsFactors = FALSE
    )
  }) %>%
    bind_rows()
  
  player_df <- player_df %>%
    filter(name != "Team") %>%
    mutate(
      name = str_trim(str_replace(name, "^(.*),\\s*(.*)$", "\\2 \\1"))
    ) %>%
    arrange(name)
  
  sheet_id <- "1yQFnD0MK0cjO68_Mri6N115EmblyDW7Bza2hbY9Rerg"
  
  # Upload AllMatchups to the tab "All-Time Games"
  sheet_write(data = all_rosters_data, ss = sheet_id, sheet = "roster2")
  