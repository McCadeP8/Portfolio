library(shiny)
library(hoopR)
library(googlesheets4)
library(tidyverse)
library(gt)
library(fontawesome)
library(gtExtras)
library(bslib)
library(bsicons)
library(ggimage)
library(httr)
library(ThemePark)
library(thematic)
library(sysfonts)
library(showtext)
library(ggforce)
gs4_deauth()
#setwd("C:/Users/mppac/Downloads/SBC_Bref")

ActivePlayers <- readRDS("activeplayers.rds")
Careers <- readRDS("careers.rds")
GameData <- readRDS("gamedata.rds")
Games <- readRDS("games.rds")
Players <- readRDS("players.rds")
PlayoffBracket <- readRDS("playoffbracket.rds")
PlayoffLines <- readRDS("playofflines.rds")
Rosters <- readRDS("rosters.rds")
Schedule <- readRDS("schedule.rds")
TeamInfo <- readRDS("teaminfo.rds")
TeamPeriodStats <- readRDS("teamperiodstats.rds")
IllegalRosters <- readRDS("illegalrosters.rds")
Standings <- readRDS("standings.rds")
ISTStandings <- readRDS("iststandings.rds")
RecordMatrix <- readRDS("recordmatrix.rds")
TeamTotalStats <- readRDS("teamtotalstats.rds")
TeamHistoryNotes <- readRDS("teamhistorynotes.rds")
PlayerNotes <- readRDS("playernotes.rds")


TeamInfo <- TeamInfo %>%
  filter(Nickname != "Seals" | is.na(Nickname) == T)
ScheduleInput <- Schedule %>%
  group_by(Period, Year) %>%
  summarize(SDate = min(Date),
            EDate = max(Date)) %>%
  ungroup() %>%
  mutate(SDate = format(as.Date(SDate), "%b %d"),
         EDate = format(as.Date(EDate), "%b %d"),
         Dates = paste0(SDate, "-", EDate)) %>%
  select(Year, Period, Dates)
# team_fonts <- data.frame(
#   Team = c("Albuquerque Armadillos", "Anaheim Mice", "Anchorage Killer Whales","Austin Bats", "Baltimore Blue Crabs", "Birmingham Bandits","Boise Spuds", # "Buffalo Daredevils", "Cincinnati Chili","Columbus Arches", "Des Moines Racoons", "El Paso Vipers","Honolulu Diamonds", "Jacksonville Manatees", "Kentucky # Thoroughbreds","Lansing Lagoon", "Lincoln Bully", "Little Rock Big Foot","Manchester Trout", "Nashville Strings", "Pittsburgh Bridge","Providence Pilgrims", # "San Diego Wave", "San Jose Seagulls","Seattle Brew", "St. Louis 66ers", "Tampa Bay Flamingos","Tulsa Tornado", "Vancouver Forest", "Vegas Blackjack"),
#   Wording = c("amatic", "baloo", "fjalla","creepster", "lobster", "rye","neucha", "teko", "satisfy","arvo", "cabin_sketch", "pathway","dancing", "pacifico", # "playfair","ubuntu", "bebas", "alfa","quicksand", "tangerine", "roboto_slab","fell_english", "comfortaa", "indie_flower","poppins", "oswald", "parisienne"# ,"permanent_marker", "shadows", "audiowide"))
# 
# font_add_google("Amatic SC", "amatic")
# font_add_google("Baloo 2", "baloo")
# font_add_google("Fjalla One", "fjalla")
# font_add_google("Creepster", "creepster")
# font_add_google("Lobster", "lobster")
# font_add_google("Rye", "rye")
# font_add_google("Neucha", "neucha")
# font_add_google("Teko", "teko")
# font_add_google("Satisfy", "satisfy")
# font_add_google("Arvo", "arvo")
# font_add_google("Cabin Sketch", "cabin_sketch")
# font_add_google("Pathway Gothic One", "pathway")
# font_add_google("Dancing Script", "dancing")
# font_add_google("Pacifico", "pacifico")
# font_add_google("Playfair Display", "playfair")
# font_add_google("Ubuntu", "ubuntu")
# font_add_google("Bebas Neue", "bebas")
# font_add_google("Alfa Slab One", "alfa")
# font_add_google("Quicksand", "quicksand")
# font_add_google("Tangerine", "tangerine")
# font_add_google("Roboto Slab", "roboto_slab")
# font_add_google("IM Fell English", "fell_english")
# font_add_google("Comfortaa", "comfortaa")
# font_add_google("Indie Flower", "indie_flower")
# font_add_google("Poppins", "poppins")
# font_add_google("Oswald", "oswald")
# font_add_google("Parisienne", "parisienne")
# font_add_google("Permanent Marker", "permanent_marker")
# font_add_google("Shadows Into Light Two", "shadows")
# font_add_google("Audiowide", "audiowide")
# showtext_auto()


GetGameScore <- function(i) {
  
  Order <- c("MP", "TSp", "FGM2", "FGA2", "FGp2", "FGM3", "FGA3", "FGp3", "FTM", "FTA", "FTp", "PTS", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "PM")
  TeamA <- Games$TeamA[i]
  TeamB <- Games$TeamB[i]
  GamePeriod <- Games$Period[i]
  GameYear <- Games$Year[i]
  
  TeamAResults <- TeamPeriodStats %>%
    filter(Period == GamePeriod) %>%
    filter(Year == GameYear) %>%
    filter(Team == TeamA)
  TeamBResults <- TeamPeriodStats %>%
    filter(Period == GamePeriod) %>%
    filter(Year == GameYear) %>%
    filter(Team == TeamB)
  Results <- rbind(TeamAResults,TeamBResults)
  Results <- Results %>%
    pivot_longer(-Team, names_to = "Stat", values_to = "Value") %>%
    pivot_wider(names_from = Team, values_from = Value) %>%
    mutate(Stat = factor(Stat, levels = Order)) %>%
    arrange(Stat) %>%
    mutate(Points = 0) %>%
    rename(TeamA = 2, TeamB = 3)
  Results$Points[1]  <- case_when(Results$TeamA[1]  < Results$TeamB[1]  ~ 11, Results$TeamA[1]  == Results$TeamB[1]  ~ 5.5, TRUE ~ 0)
  Results$Points[2]  <- case_when(Results$TeamA[2]  < Results$TeamB[2]  ~ 41, Results$TeamA[2]  == Results$TeamB[2]  ~ 20.5, TRUE ~ 0)
  Results$Points[5]  <- case_when(Results$TeamA[5]  < Results$TeamB[5]  ~ 31, Results$TeamA[5]  == Results$TeamB[5]  ~ 15.5, TRUE ~ 0)
  Results$Points[8]  <- case_when(Results$TeamA[8]  < Results$TeamB[8]  ~ 31, Results$TeamA[8]  == Results$TeamB[8]  ~ 15.5, TRUE ~ 0)
  Results$Points[11] <- case_when(Results$TeamA[11] < Results$TeamB[11] ~ 21, Results$TeamA[11] == Results$TeamB[11] ~ 10.5, TRUE ~ 0)
  Results$Points[12] <- case_when(Results$TeamA[12] < Results$TeamB[12] ~ 61, Results$TeamA[12] == Results$TeamB[12] ~ 30.5, TRUE ~ 0)
  Results$Points[13] <- case_when(Results$TeamA[13] < Results$TeamB[13] ~ 31, Results$TeamA[13] == Results$TeamB[13] ~ 15.5, TRUE ~ 0)
  Results$Points[14] <- case_when(Results$TeamA[14] < Results$TeamB[14] ~ 31, Results$TeamA[14] == Results$TeamB[14] ~ 15.5, TRUE ~ 0)
  Results$Points[15] <- case_when(Results$TeamA[15] < Results$TeamB[15] ~ 41, Results$TeamA[15] == Results$TeamB[15] ~ 20.5, TRUE ~ 0)
  Results$Points[16] <- case_when(Results$TeamA[16] < Results$TeamB[16] ~ 31, Results$TeamA[16] == Results$TeamB[16] ~ 15.5, TRUE ~ 0)
  Results$Points[17] <- case_when(Results$TeamA[17] < Results$TeamB[17] ~ 31, Results$TeamA[17] == Results$TeamB[17] ~ 15.5, TRUE ~ 0)
  TeamA_val <- ifelse(Results$TeamA[1] == 0, 1000, Results$TeamA[18])
  TeamB_val <- ifelse(Results$TeamB[1] == 0, 1000, Results$TeamB[18])
  Results$Points[18] <- case_when(TeamA_val > TeamB_val ~ 21, TeamA_val == TeamB_val ~ 10.5, TRUE ~ 0)
  Results$Points[19] <- case_when(Results$TeamA[19] < Results$TeamB[19] ~ 31, Results$TeamA[19] == Results$TeamB[19] ~ 15.5, TRUE ~ 0)
  
  GameScore <- paste0(413-sum(Results$Points),"-",sum(Results$Points))
  
  return(GameScore)
}
GameRecap <- function(i) {
  
  Order <- c("MP", "TSp", "FGM2", "FGA2", "FGp2", "FGM3", "FGA3", "FGp3", "FTM", "FTA", "FTp", "PTS", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "PM")
  TeamA <- Games$TeamA[i]
  TeamB <- Games$TeamB[i]
  GamePeriod <- Games$Period[i]
  GameYear <- Games$Year[i]
  
  TeamAInfo <- TeamInfo %>%
    filter(Team == TeamA)
  TeamBInfo <- TeamInfo %>%
    filter(Team == TeamB)
  
  Dates <- Schedule %>%
    filter(Year == GameYear) %>%
    filter(Period == GamePeriod) %>%
    select(-Period)
  
  MinDate <- min(Dates$Date)
  MaxDate <- max(Dates$Date)
  SDate <- format(MinDate, "%b %d")
  EDate <- format(MaxDate, "%b %d")
  CaptionText <- paste0(SDate, "-", EDate, "; ", GameYear-1,"-",GameYear-2000, " Season; *Lower Value Wins Turnover Category")
  
  
  team_a_name <- TeamAInfo$Team[1]
  team_a_color <- TeamAInfo$Color4[1]
  team_b_name <- TeamBInfo$Team[1]
  team_b_color <- TeamBInfo$Color4[1]
  title_text <- glue::glue("
**<span style='color:{team_a_color};'>{team_a_name}</span>
<span style='color:black;'>at</span>
<span style='color:{team_b_color};'>{team_b_name}</span>**")
  
  
  TeamAResults <- TeamPeriodStats %>%
    filter(Period == GamePeriod) %>%
    filter(Year == GameYear) %>%
    filter(Team == TeamA)
  TeamBResults <- TeamPeriodStats %>%
    filter(Period == GamePeriod) %>%
    filter(Year == GameYear) %>%
    filter(Team == TeamB)
  Results <- rbind(TeamAResults,TeamBResults)
  Results2 <- Results %>%
    pivot_longer(-Team, names_to = "Stat", values_to = "Value") %>%
    pivot_wider(names_from = Team, values_from = Value) %>%
    mutate(Stat = factor(Stat, levels = Order)) %>%
    arrange(Stat) %>%
    mutate(Points = 0) %>%
    rename(TeamA2 = 2, TeamB2 = 3) %>%
    filter(is.na(Stat) == F)
  
  Results2$Points[1]  <- case_when(Results2$TeamA2[1]  < Results2$TeamB2[1]  ~ 1, Results2$TeamA2[1]  == Results2$TeamB2[1]  ~ 0.5, TRUE ~ -1)
  Results2$Points[2]  <- case_when(Results2$TeamA2[2]  < Results2$TeamB2[2]  ~ 1, Results2$TeamA2[2]  == Results2$TeamB2[2]  ~ 0.5, TRUE ~ -1)
  Results2$Points[5]  <- case_when(Results2$TeamA2[5]  < Results2$TeamB2[5]  ~ 1, Results2$TeamA2[5]  == Results2$TeamB2[5]  ~ 0.5, TRUE ~ -1)
  Results2$Points[8]  <- case_when(Results2$TeamA2[8]  < Results2$TeamB2[8]  ~ 1, Results2$TeamA2[8]  == Results2$TeamB2[8]  ~ 0.5, TRUE ~ -1)
  Results2$Points[11] <- case_when(Results2$TeamA2[11] < Results2$TeamB2[11] ~ 1, Results2$TeamA2[11] == Results2$TeamB2[11] ~ 0.5, TRUE ~ -1)
  Results2$Points[12] <- case_when(Results2$TeamA2[12] < Results2$TeamB2[12] ~ 1, Results2$TeamA2[12] == Results2$TeamB2[12] ~ 0.5, TRUE ~ -1)
  Results2$Points[13] <- case_when(Results2$TeamA2[13] < Results2$TeamB2[13] ~ 1, Results2$TeamA2[13] == Results2$TeamB2[13] ~ 0.5, TRUE ~ -1)
  Results2$Points[14] <- case_when(Results2$TeamA2[14] < Results2$TeamB2[14] ~ 1, Results2$TeamA2[14] == Results2$TeamB2[14] ~ 0.5, TRUE ~ -1)
  Results2$Points[15] <- case_when(Results2$TeamA2[15] < Results2$TeamB2[15] ~ 1, Results2$TeamA2[15] == Results2$TeamB2[15] ~ 0.5, TRUE ~ -1)
  Results2$Points[16] <- case_when(Results2$TeamA2[16] < Results2$TeamB2[16] ~ 1, Results2$TeamA2[16] == Results2$TeamB2[16] ~ 0.5, TRUE ~ -1)
  Results2$Points[17] <- case_when(Results2$TeamA2[17] < Results2$TeamB2[17] ~ 1, Results2$TeamA2[17] == Results2$TeamB2[17] ~ 0.5, TRUE ~ -1)
  TeamA_val <- ifelse(Results2$TeamA2[1] == 0, 1000, Results2$TeamA2[18])
  TeamB_val <- ifelse(Results2$TeamB2[1] == 0, 1000, Results2$TeamB2[18])
  Results2$Points[18] <- case_when(TeamA_val > TeamB_val ~ 1, TeamA_val == TeamB_val ~ 0.5, TRUE ~ -1)
  Results2$Points[19] <- case_when(Results2$TeamA2[19] < Results2$TeamB2[19] ~ 1, Results2$TeamA2[19] == Results2$TeamB2[19] ~ 0.5, TRUE ~ -1)
  
Results2 <- Results2 %>%
  mutate(TeamA2 = ifelse(Stat %in% c("TSp", "FGp2", "FGp3", "FTp"), paste0(round(TeamA2, 4) * 100, "%"), TeamA2),
         TeamB2 = ifelse(Stat %in% c("TSp", "FGp2", "FGp3", "FTp"), paste0(round(TeamB2, 4) * 100, "%"), TeamB2))

Results3 <- Results %>%
  mutate(`2P` = paste0(FGM2,"/",FGA2),
       `3P` = paste0(FGM3,"/",FGA3),
       `FT` = paste0(FTM,"/",FTA)) %>%
  select(Team, `2P`, `3P`, `FT`) %>%
  pivot_longer(-Team, names_to = "Stat", values_to = "Value") %>%
  pivot_wider(names_from = Team, values_from = Value) %>%
  rename(TeamA2 = 2, TeamB2 = 3) %>%
  mutate(Points = as.numeric(NA))

Results4 <- data.frame(
  Stat = "SCORE",
  TeamA2 = Games$TeamAScore[i],
  TeamB2 = Games$TeamBScore[i],
  Points = ifelse(Games$TeamAScore[i] > Games$TeamBScore[i], -1, 1))

Results5 <- rbind(Results2,Results3, Results4)
  
Results5 <- Results5 %>%
  filter(Stat %in% c("MP", "TSp", "2P", "FGp2", "3P", "FGp3", "FT", "FTp", "PTS", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "PM", "SCORE")) %>%
  mutate(Stat = recode(Stat, "TSp" = "TS%", "FGp2" = "2P%", "FGp3" = "3P%", "FTp" = "FT%")) %>%
  mutate(Stat = factor(Stat, levels = c("MP", "TS%", "2P", "2P%", "3P", "3P%", "FT", "FT%", "PTS", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "PM", "SCORE"))) %>%
  arrange(Stat) %>%
  mutate(TeamAWinners = ifelse(Points == -1, "circle-arrow-left", NA),
         TeamAWinners = ifelse(Points == 0.5, "equals", TeamAWinners),
         TeamBWinners = ifelse(Points == 1, "circle-arrow-right", NA),
         TeamBWinners = ifelse(Points == 0.5, "equals", TeamBWinners)) %>%
  select(2,5,1,6,3,4)

GameType <- Games$Round[i]
GameType <- ifelse(GameType == "Regular", "Regular Season", GameType)

Results5$Category <- c("(11)", "(41)", "", "(31)", "", "(31)", "", "(21)", "(61)", "(31)", "(31)", "(41)", "(31)", "(31)", "(21*)", "(31)", "(413)")


gt(Results5) %>%
  fmt_icon(columns = c(TeamAWinners,TeamBWinners)) %>%
  gt_merge_stack(col1 = Stat, col2 = Category, palette = c("white","white"), font_weight = c("bold","normal")) %>%
  sub_missing(columns = everything(), missing_text = "") %>%
  tab_style(style = cell_text(align = "center"), locations = cells_column_labels(columns = c(TeamA2,TeamB2))) %>%
  cols_align(columns = c(TeamA2), align = "right") %>%
  cols_align(columns = c(TeamB2), align = "left") %>%
  cols_align(columns = c(Stat, TeamBWinners, TeamAWinners), align = "center") %>%
  gt_theme_538() %>%
  tab_style(style = list(cell_fill(color = TeamAInfo$Color1[1]), cell_text(color = TeamAInfo$Color3[1])), locations = cells_body(columns = c(TeamA2, TeamAWinners))) %>%
  tab_style(style = list(cell_fill(color = TeamBInfo$Color1[1]), cell_text(color = TeamBInfo$Color3[1])), locations = cells_body(columns = c(TeamB2, TeamBWinners))) %>%
  tab_style(style = list(cell_fill(color = TeamAInfo$Color1[1]), cell_text(color = TeamAInfo$Color3[1])), locations = cells_column_labels(columns = c(TeamA2, TeamAWinners))) %>%
  tab_style(style = list(cell_fill(color = TeamBInfo$Color1[1]), cell_text(color = TeamBInfo$Color3[1])), locations = cells_column_labels(columns = c(TeamB2, TeamBWinners))) %>%
  tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_body(columns = c(Stat))) %>%
  tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_column_labels(columns = c(Stat))) %>%
  tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_title(groups = c("title", "subtitle"))) %>%
  tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_source_notes()) %>%
  cols_label(TeamA2 = TeamA, TeamAWinners = "", Stat = "Cat", TeamBWinners = "", TeamB2 = TeamB) %>%
  tab_header(title = md(title_text), subtitle = GameType) %>%
  tab_source_note(source_note = md(CaptionText)) %>%
  tab_options(heading.align = "center") %>%
  cols_label_with(columns = TeamA2, fn = function(x) {
    out <- paste0("<img src=\"",
                  TeamAInfo$Logo[1],
                  "\" style=\"height:",
                  paste0(80, "px"),
                  ";\" alt=\"User provided image\">")
    html(out)}) %>%
  cols_label_with(columns = TeamB2, fn = function(x) {
    out <- paste0("<img src=\"",
                  TeamBInfo$Logo[1],
                  "\" style=\"height:",
                  paste0(80, "px"),
                  ";\" alt=\"User provided image\">")
    html(out)}) %>%
  cols_hide(Points) %>%
  tab_style(style = list(cell_borders(sides = c("top"), color = "black", weight = px(10))),
            locations = list(cells_body(row = 17))) %>%
  tab_style(style = list(cell_borders(sides = c("top"), color = "pink", weight = px(0))),
            locations = list(cells_body(row = 1:16)))
}
GameRecapPlayers <- function(i) {
  
  TeamA <- Games$TeamA[i]
  TeamB <- Games$TeamB[i]
  GamePeriod <- Games$Period[i]
  GameYear <- Games$Year[i]
  TeamAInfo <- TeamInfo %>%
    filter(Team == TeamA)
  TeamBInfo <- TeamInfo %>%
    filter(Team == TeamB)
  Dates <- Schedule %>%
    filter(Year == GameYear) %>%
    filter(Period == GamePeriod) %>%
    select(-Period)

  TeamAResults <- ActivePlayers %>%
    filter(game_date %in% Dates$Date) %>%
    filter(Team %in% c(TeamA, TeamB)) %>%
    mutate(Team = factor(Team, levels = c(TeamA, TeamB)),
           PM = as.numeric(PM)) %>%
    arrange(Team, game_date, athlete_display_name) %>%
    mutate(game_date = format(game_date, "%b %d")) %>%
    group_by(Team)
  
  team_a_name <- TeamAInfo$Team[1]
  team_a_color <- TeamAInfo$Color4[1]
  team_b_name <- TeamBInfo$Team[1]
  team_b_color <- TeamBInfo$Color4[1]
  title_text <- glue::glue("
**<span style='color:{team_a_color};'>{team_a_name}</span>
<span style='color:black;'>at</span>
<span style='color:{team_b_color};'>{team_b_name}</span>**")
  
  gt(TeamAResults) %>%
    tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_body()) %>%
    cols_label(game_date = "Date",
               athlete_display_name = "Name",
               team_abbreviation = "Team",
               Location = "",
               opponent_team_abbreviation = "Opp") %>%
    gt_theme_538() %>%
    cols_align(columns = everything(), align = c('center')) %>%
    cols_align(columns = c(athlete_display_name), align = c('right')) %>%
    fmt_percent(columns = c("2P%", "3P%", "FT%", "TS%"), decimals = 2) %>%
    sub_missing(columns = everything(), missing_text = "") %>%
    tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_title(groups = c("title", "subtitle"))) %>%
    tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_source_notes()) %>%
    tab_style(style = list(cell_fill(color = TeamAInfo$Color1[1]), cell_text(color = TeamAInfo$Color3[1], align = "center")), locations = cells_row_groups(groups = TeamA)) %>%
    tab_style(style = list(cell_fill(color = TeamBInfo$Color1[1]), cell_text(color = TeamBInfo$Color3[1], align = "center")), locations = cells_row_groups(groups = TeamB)) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", weight = "bold")), locations = cells_column_labels(columns = everything())) %>%
    tab_header(title = md(title_text))
    
  
  
}
PlayerHeadshot <- function(Player) {
 A <-  GameData %>%
    filter(athlete_display_name == Player) %>%
    select(athlete_headshot_href) %>%
    distinct() %>%
    pull()
 
 ggplot() +
   geom_image(aes(x = 0, y = 0, image = A), size = 1.5) +
   theme_void()
  
}
CareerSeason <- function(Player, Input2) {
  
  PlayerData <- Careers %>%
    filter(PlayerName == Player) %>%
    filter(SeasonType == Input2) %>%
    left_join(PlayerNotes, by = c('PlayerName' = 'Winner', 'Year')) %>%
    select(-PlayerName, -SeasonType) %>%
    mutate(Team = ifelse(Team == "San Diego Wave", "San Diego Seals", Team),
           Color1 = ifelse(Team == "San Diego Seals", "#31439B", Color1),
           Color3 = ifelse(Team == "San Diego Seals", "white", Color3)) %>%
    select(2,1,3:22) %>%
    mutate(Year = paste0(Year-1,"-",Year-2000))
  
  NumberOfTeams <- length(unique(PlayerData$Team))
  Color1 <- ifelse(NumberOfTeams == 1, PlayerData$Color1[1], "black")
  Color3 <- ifelse(NumberOfTeams == 1, PlayerData$Color3[1], "white")
  
  gt_table <- gt(PlayerData) %>%
    tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_body()) %>%
    gt_theme_538() %>%
    cols_label(unique_icons = "Awards") %>%
    fmt_icon(columns = unique_icons) %>%
    cols_hide(columns = c(Color1, Color3)) %>%
    cols_align(columns = everything(), align = c('center')) %>%
    cols_align(columns = c(Team), align = c('right')) %>%
    cols_align(columns = unique_icons, align = c("left")) %>%
    fmt_percent(columns = c("2P%", "3P%", "FT%", "TS%"), decimals = 2) %>%
    sub_missing(columns = everything(), missing_text = "") %>%
    tab_header(title = md(paste0("**Career Summary: ", Player, "**"))) %>%
    tab_style(style = list(cell_fill(color = Color1), cell_text(color = Color3, weight = "bold")), locations = cells_column_labels(columns = everything())) %>%
    tab_style(style = list(cell_fill(color = Color1), cell_text(color = Color3, weight = "bold")), locations = cells_title())
  
    for (i in seq_len(nrow(PlayerData))) {
      gt_table <- gt_table %>%
        tab_style(style = list(cell_fill(color = PlayerData$Color1[i]), cell_text(color = PlayerData$Color3[i])), locations = cells_body(columns = Team:Year, rows = i))}
  
  gt_table %>%
    tab_style(
      style = list(cell_fill(color = "#AAAAAA"), cell_text(color = "#222222")),
      locations = cells_body(
        columns = setdiff(names(PlayerData), "Logo"),
        rows = Team == "Total"))  
  
  return(gt_table)
}
TeamSeason <- function(TeamA, YearA, Input2) {
  
  TeamData <- Careers %>%
    filter(Team == TeamA) %>%
    filter(Year == YearA) %>%
    filter(SeasonType == Input2) %>%
    select(-Year, -SeasonType) %>%
    mutate(Team = ifelse(Team == "San Diego Wave", "San Diego Seals", Team),
           Color1 = ifelse(Team == "San Diego Seals", "#31439B", Color1),
           Color3 = ifelse(Team == "San Diego Seals", "white", Color3)) %>%
    arrange(-GP) %>%
    select(Team, PlayerName, GP:PM, Color1, Color3)
  
  gt(TeamData) %>%
    gt_theme_538() %>%
    cols_hide(columns = c(Color1, Color3)) %>%
    cols_align(columns = everything(), align = c('center')) %>%
    cols_align(columns = c(Team, PlayerName), align = c('right')) %>%
    fmt_percent(columns = c("2P%", "3P%", "FT%", "TS%"), decimals = 2) %>%
    sub_missing(columns = everything(), missing_text = "") %>%
    tab_header(title = md(paste0("**Team Stats for the ", TeamA, " ",YearA-1,"-",YearA-2000, " Season**"))) %>%
    tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_body()) %>%
    tab_style(style = list(cell_fill(color = TeamData$Color1[1]), cell_text(color = TeamData$Color3[1])), locations = cells_body(columns = c(Team, PlayerName))) %>%
    tab_style(style = list(cell_fill(color = TeamData$Color1[1]), cell_text(color = TeamData$Color3[1], weight = "bold")), locations = cells_title(groups = "title")) %>%
    tab_style(style = list(cell_fill(color = TeamData$Color1[1]), cell_text(color = TeamData$Color3[1], weight = "bold")), locations = cells_column_labels(columns = everything())) %>%
    cols_label(PlayerName = "Player")
  
  }
TeamSchedule <- function(TeamAA, YearA) {
  
  TeamInfo2 <- TeamInfo %>%
    filter(Team == TeamAA)
  
  YearA <- as.numeric(YearA)
  
  Schedule2 <- Schedule %>%
    filter(Year == YearA) %>%
    group_by(Period) %>%
    summarize(SDate = min(Date),
              EDate = max(Date)) %>%
    ungroup() %>%
    mutate(SDate = format(as.Date(SDate), "%b %d"),
           EDate = format(as.Date(EDate), "%b %d"),
           Dates = paste0(SDate, "-", EDate)) %>%
    select(Period, Dates)
  
  TeamSchedule2 <- Games %>%
    mutate(ID = 1:n()) %>%
    filter(TeamA == TeamAA | TeamB == TeamAA) %>%
    filter(Year == YearA) %>%
    arrange(Period) %>%
    mutate(Location = ifelse(TeamB == TeamAA, "", "@"),
           Score = ifelse(TeamB == TeamAA, paste0(TeamBScore,"-",TeamAScore), paste0(TeamAScore,"-",TeamBScore)),
           Winner = ifelse(TeamBScore >= TeamAScore, TeamB, TeamA),
           Winner = ifelse(Winner == TeamAA, 1, 0),
           Team = TeamAA,
           Opponent = ifelse(TeamA == TeamAA, TeamB, TeamA)) %>%
    left_join(Schedule2, by = c('Period')) %>%
    select(Type, ID, Dates, Team, Location, Opponent, Score, Winner) %>%
    group_by(Type)
  
  gt(TeamSchedule2) %>%
    gt_theme_538() %>%
    gt_highlight_rows(rows = Winner == 1, fill = "#8CD47E") %>%
    gt_highlight_rows(rows = Winner == 0, fill = "#FF6961") %>%
    cols_align("center") %>%
    cols_hide(Winner) %>%
    tab_header(title = paste0(TeamAA, " Schedule for ", YearA - 1, "-", YearA - 2000, " Season")) %>%
    tab_style(style = list(cell_fill(color = TeamInfo2$Color1[1]), cell_text(color = TeamInfo2$Color3[1], weight = "bold", size = px(20))), locations = cells_title(groups = "title")) %>%
    tab_style(style = list(cell_fill(color = TeamInfo2$Color1[1]), cell_text(color = TeamInfo2$Color3[1], weight = "bold")), locations = cells_column_labels(columns = everything())) %>%
    cols_label(Location = "") %>%
    cols_align(columns = Opponent, "left") %>%
    cols_align(columns = Team, "right") %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", align = "center")), locations = cells_row_groups(groups = everything()))
    
    
}
AllTimeTeamLeader <- function(TeamA, Input2, Input3) {
  
  Rosters2 <- Rosters %>%
    filter(Team == TeamA) %>%
    left_join(Schedule, by = c("Year", "Period" = "Day")) %>%
    filter(is.na(Date) == F) %>%
    mutate(Date2 = Sys.Date()-Date,
           Date2 = abs(Date2),
           Date2 = as.numeric(Date2),
           MinDate = min(Date2)) %>%
    filter(Date2 == MinDate) %>%
    left_join(Players, by = c('PlayerID' = 'FantraxID')) %>%
    select(ESPNPlayer) %>%
    mutate(ActivePlayer = "fas fa-user")

  TeamInfo2 <- TeamInfo %>%
    filter(Team == TeamA)
  
 RosterLeader <- ActivePlayers %>%
    left_join(Players, by = c('athlete_display_name' = 'ESPNPlayer')) %>%
    left_join(Schedule, by = c('game_date' = 'Date')) %>%
    group_by(athlete_display_name, Season, Team) %>%
    summarize(GP = n(),
              MP = sum(MP),
              PTS = sum(PTS),
              OREB = sum(OREB),
              DREB = sum(DREB),
              AST = sum(AST),
              STL = sum(STL),
              BLK = sum(BLK),
              TOV = sum(TOV),
              PM = sum(as.numeric(PM)),
              FGM2 = sum(as.numeric(sapply(strsplit(`2P`, "/"), `[`, 1))),
              FGA2 = sum(as.numeric(sapply(strsplit(`2P`, "/"), `[`, 2))),
              FGM3 = sum(as.numeric(sapply(strsplit(`3P`, "/"), `[`, 1))),
              FGA3 = sum(as.numeric(sapply(strsplit(`3P`, "/"), `[`, 2))),
              FTM = sum(as.numeric(sapply(strsplit(`FT`, "/"), `[`, 1))),
              FTA = sum(as.numeric(sapply(strsplit(`FT`, "/"), `[`, 2))),
              `2P%` = ifelse(FGA2 > 0, FGM2 / FGA2, NaN),
              `3P%` = ifelse(FGA3 > 0, FGM3 / FGA3, NaN),
              `FT%` = ifelse(FTA > 0, FTM / FTA, NaN),
              `TS%` = ifelse((FGA2 + FGA3 + 0.44 * FTA) > 0, 
                             PTS / (2 * (FGA2 + FGA3 + 0.44 * FTA)), NaN)) %>%
    ungroup() %>%
    filter(Team == TeamA) %>%
    filter(Season == Input2) %>%
    left_join(Rosters2, by = c('athlete_display_name' = 'ESPNPlayer')) %>%
    mutate(`2P` = paste0(FGM2,"/",FGA2),
           `3P` = paste0(FGM3,"/",FGA3),
           FT = paste0(FTM,"/",FTA)) %>%
    select(ActivePlayer, athlete_display_name, GP, MP, `TS%`, `2P`, `2P%`, `3P`, `3P%`, FT, `FT%`, PTS, OREB, DREB, AST, STL, BLK, TOV, PM) %>%
    relocate(all_of(Input3), .after = athlete_display_name) %>%
    arrange(desc(.data[[Input3]]))
  
  gt(RosterLeader) %>%
    fmt_icon(columns = c(ActivePlayer)) %>%
    gt_theme_538() %>%
    tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_body()) %>%
    cols_align(columns = everything(), align = c('center')) %>%
    cols_align(columns = c(athlete_display_name), align = c('right')) %>%
    fmt_percent(columns = c("2P%", "3P%", "FT%", "TS%"), decimals = 2) %>%
    fmt_number(columns = c(GP, MP, PTS, OREB, DREB, AST, STL, BLK, TOV, PM), use_seps = TRUE, decimals = 0) %>%
    sub_missing(columns = everything(), missing_text = "") %>%
    cols_label(athlete_display_name = "",
               ActivePlayer = "") %>%
    tab_header(title = paste("All-Time Leaders for the", TeamA)) %>%
    tab_style(style = list(cell_fill(color = TeamInfo2$Color1[1]), cell_text(color = TeamInfo2$Color3[1], weight = "bold", size = px(20))), locations = cells_title(groups = "title")) %>%
    tab_style(style = list(cell_fill(color = TeamInfo2$Color1[1]), cell_text(color = TeamInfo2$Color3[1], weight = "bold")), locations = cells_column_labels(columns = everything()))
  
}
AllTimeLeaders <- function(Input2, Input3) {
  
  Rosters2 <- Rosters %>%
    left_join(Schedule, by = c("Year", "Period" = "Day")) %>%
    filter(is.na(Date) == F) %>%
    mutate(Date2 = Sys.Date()-Date,
           Date2 = abs(Date2),
           Date2 = as.numeric(Date2),
           MinDate = min(Date2)) %>%
    filter(Date2 == MinDate) %>%
    left_join(Players, by = c('PlayerID' = 'FantraxID')) %>%
    select(ESPNPlayer) %>%
    mutate(ActivePlayer = "fas fa-user")
  
  RosterLeader <- ActivePlayers %>%
    left_join(Players, by = c('athlete_display_name' = 'ESPNPlayer')) %>%
    left_join(Schedule, by = c('game_date' = 'Date')) %>%
    group_by(athlete_display_name, Season) %>%
    summarize(GP = n(),
              MP = sum(MP),
              PTS = sum(PTS),
              OREB = sum(OREB),
              DREB = sum(DREB),
              AST = sum(AST),
              STL = sum(STL),
              BLK = sum(BLK),
              TOV = sum(TOV),
              PM = sum(as.numeric(PM)),
              FGM2 = sum(as.numeric(sapply(strsplit(`2P`, "/"), `[`, 1))),
              FGA2 = sum(as.numeric(sapply(strsplit(`2P`, "/"), `[`, 2))),
              FGM3 = sum(as.numeric(sapply(strsplit(`3P`, "/"), `[`, 1))),
              FGA3 = sum(as.numeric(sapply(strsplit(`3P`, "/"), `[`, 2))),
              FTM = sum(as.numeric(sapply(strsplit(`FT`, "/"), `[`, 1))),
              FTA = sum(as.numeric(sapply(strsplit(`FT`, "/"), `[`, 2))),
              `2P%` = ifelse(FGA2 > 0, FGM2 / FGA2, NaN),
              `3P%` = ifelse(FGA3 > 0, FGM3 / FGA3, NaN),
              `FT%` = ifelse(FTA > 0, FTM / FTA, NaN),
              `TS%` = ifelse((FGA2 + FGA3 + 4/9 * FTA) > 0, 
                             PTS / (2 * (FGA2 + FGA3 + 4/9 * FTA)), NaN)) %>%
    ungroup() %>%
    filter(Season == Input2) %>%
    left_join(Rosters2, by = c('athlete_display_name' = 'ESPNPlayer')) %>%
    mutate(`2P` = paste0(FGM2,"/",FGA2),
           `3P` = paste0(FGM3,"/",FGA3),
           FT = paste0(FTM,"/",FTA)) %>%
    select(ActivePlayer, athlete_display_name, GP, MP, `TS%`, `2P`, `2P%`, `3P`, `3P%`, FT, `FT%`, PTS, OREB, DREB, AST, STL, BLK, TOV, PM) %>%
    select(ActivePlayer, athlete_display_name, GP, MP, `TS%`, `2P`, `2P%`, `3P`, `3P%`, FT, `FT%`, PTS, OREB, DREB, AST, STL, BLK, TOV, PM) %>%
    relocate(all_of(Input3), .after = athlete_display_name) %>%
    arrange(desc(.data[[Input3]]))
  
  
  gt(RosterLeader) %>%
    fmt_icon(columns = c(ActivePlayer)) %>%
    gt_theme_538() %>%
    tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_body()) %>%
    cols_align(columns = everything(), align = c('center')) %>%
    cols_align(columns = c(athlete_display_name), align = c('right')) %>%
    fmt_percent(columns = c("2P%", "3P%", "FT%", "TS%"), decimals = 2) %>%
    fmt_number(columns = c(GP, MP, PTS, OREB, DREB, AST, STL, BLK, TOV, PM), use_seps = TRUE, decimals = 0) %>%
    sub_missing(columns = everything(), missing_text = "") %>%
    cols_label(athlete_display_name = "",
               ActivePlayer = "") %>%
    tab_header(title = paste("All-Time Leaders for the SBCFBL")) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", weight = "bold")), locations = cells_title(groups = "title")) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", weight = "bold")), locations = cells_column_labels(columns = everything()))
  
  
}
MakeBracket <- function(YearA) {
  
  YearA <- as.numeric(YearA)
  
PlayoffBracket2 <- PlayoffBracket %>%
  left_join(TeamInfo, by = c('Team')) %>%
  filter(Year == YearA) %>%
  filter(Type == "Playoffs")

SquareSize <- 0.4
ggplot() +
  geom_segment(data = PlayoffLines, aes(x = X1, xend = X2, y = Y1, yend = Y2), color = PlayoffLines$Color) +
  geom_rect(data = PlayoffBracket2, aes(xmin = X-SquareSize, xmax = X+SquareSize, ymin = Y-SquareSize, ymax = Y+SquareSize), fill = PlayoffBracket2$Color1, color = PlayoffBracket2$Color2, linewidth = 1) +
  geom_text(data = PlayoffBracket2, aes(x = X, y = Y, label = Abb), color = PlayoffBracket2$Color3, size = 4) +
  coord_fixed() +
  theme_void() +
  labs(title = paste0(YearA," SBCFBL Playoffs")) +
  theme(plot.title = element_text(size = 30, hjust = 0.5, face = "bold", color = "black"))

}
GetStandings <- function(YearA, ConferenceA) {
  
  YearA <- as.numeric(YearA)
  
  TotalGames <- case_when(
    YearA == 2021 ~ 62,
    YearA %in% c(2022, 2023) ~ 76,
    YearA >= 2024 ~ 72)
  
  Standings <- Games %>%
    filter(Round == "Regular") %>%
    filter(Year == YearA) %>%
    mutate(Winner = ifelse(TeamAScore > TeamBScore, TeamA, TeamB)) %>%
    group_by(Winner) %>%
    summarize(Wins = n(),
              Losses = TotalGames - Wins) %>%
    left_join(TeamInfo, by = c('Winner' = 'Team')) %>%
    filter(Conference == ConferenceA) %>%
    arrange(-Wins) %>%
    mutate(Record = paste0(Wins,"-", Losses)) %>%
    select(City, Nickname, Record)
  
  Color1 <- ifelse(ConferenceA == "West", "#C8102E", "#1D428A")
  
  gt(Standings) %>%
    gt_theme_538() %>%
    gt_merge_stack(col1 = City, col2 = Nickname, palette = c("black", "black")) %>%
    cols_align(columns = everything(), align = c('center')) %>%
    gt_highlight_rows(rows = 1:6, fill = "#8CD47E") %>%
    gt_highlight_rows(rows = 7:10, fill = "#F8D66D") %>%
    gt_highlight_rows(rows = 11:15, fill = "#FF6961") %>%
    tab_source_note(source_note = "Tiebreakers might not be accurate") %>%
    tab_header(title = md(paste0(ConferenceA, "ern Conference")),
               subtitle = paste0(YearA-1, "-", YearA-2000, " Regular Season")) %>%
    cols_label(City = "Team") %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", weight = "bold")), locations = cells_column_labels(columns = everything())) %>%
    tab_style(style = list(cell_fill(color = Color1), cell_text(color = "white", weight = "bold")), locations = cells_title()) %>%
    tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_source_notes())
  
}
GetStandings2 <- function(YearA, ConferenceA) {
  
  YearA <- as.numeric(YearA)

  ISTStandings2 <- ISTStandings %>%
    filter(Year == YearA) %>%
    filter(Conf == ConferenceA) %>%
    left_join(TeamInfo, by = c('Team' = 'Team')) %>%
    select(City, Nickname, Group, IRecord, ILabel, Wildcard) %>%
    arrange(Group, ILabel) %>%
    group_by(Group)
  
  Color1 <- ifelse(ConferenceA == "West", "#C8102E", "#1D428A")
  
  gt(ISTStandings2) %>%
    gt_theme_538() %>%
    gt_merge_stack(col1 = City, col2 = Nickname, palette = c("black", "black")) %>%
    cols_align(columns = everything(), align = c('center')) %>%
    gt_highlight_rows(rows = everything(), fill = "#FF6961") %>%
    gt_highlight_rows(rows = ILabel == 1, fill = "#8CD47E") %>%
    gt_highlight_rows(rows = Wildcard == 1, fill = "#8CD47E") %>%
    tab_style(style = list(cell_fill(color = "Black"), cell_text(color = "White", align = "center")), locations = cells_row_groups()) %>%
    tab_header(title = md(paste0(ConferenceA, "ern Conference")),
               subtitle = paste0(YearA-1, " In-Season Tournament")) %>%
    cols_label(City = "Team",
               IRecord = "Record") %>%
    cols_hide(columns = c(ILabel, Wildcard)) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", weight = "bold")), locations = cells_column_labels(columns = everything())) %>%
    tab_style(style = list(cell_fill(color = Color1), cell_text(color = "white", weight = "bold")), locations = cells_title())
  
  
}
MakeBracket2 <- function(YearA) {
  
  YearA <- as.numeric(YearA)
  
  PlayoffBracket2 <- PlayoffBracket %>%
    left_join(TeamInfo, by = c('Team')) %>%
    filter(Year == YearA) %>%
    filter(Type == "In-Season")
  
  PlayoffLines2 <- PlayoffLines %>%
    filter(X1 >= -2 & X1 <= 2)
  
  SquareSize <- 0.4
  ggplot() +
    geom_segment(data = PlayoffLines2, aes(x = X1, xend = X2, y = Y1, yend = Y2), color = PlayoffLines2$Color) +
    geom_rect(data = PlayoffBracket2, aes(xmin = X-SquareSize, xmax = X+SquareSize, ymin = Y-SquareSize, ymax = Y+SquareSize), fill = PlayoffBracket2$Color1, color = PlayoffBracket2$Color2, linewidth = 3.5) +
    geom_text(data = PlayoffBracket2, aes(x = X, y = Y, label = Abb), color = PlayoffBracket2$Color3, size = 8) +
    theme_void() +
    labs(title = paste0(YearA-1," SBCFBL Cup")) +
    theme(plot.title = element_text(size = 30, hjust = 0.5, face = "bold", color = "black"))
  
}
TeamHistory <- function(TeamA) {
  
  TeamInfo2 <- TeamInfo %>%
    filter(Team == TeamA)
  
  Standings2 <- Standings %>%
    filter(Team == TeamA) %>%
    as.data.frame() %>%
    left_join(TeamHistoryNotes, by = c('Year', 'Team')) %>%
    select(Year, Team, LResult, YRecord, CRecord, DRecord, YLabel, CLabel, DLabel, IRecord, ILabel, CResult, Awards) %>%
    mutate(Year = paste0(Year-1,"-",Year-2000))

  gt(Standings2) %>%
    gt_theme_538() %>%
    tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_body()) %>%
    tab_style(style = list(cell_fill(color = TeamInfo2$Color1[1]), cell_text(color = TeamInfo2$Color3[1])), locations = cells_body(columns = "Team")) %>%
    tab_style(style = list(cell_fill(color = TeamInfo2$Color1[1]), cell_text(color = TeamInfo2$Color3[1])), locations = cells_body(columns = "Year")) %>%
    cols_align("center") %>%
    cols_align(columns = "Awards", align = "left") %>%
    cols_label(YRecord = "Overall",
               YLabel = "League",
               CLabel = "Conference",
               DLabel = "Division",
               CRecord = "Conference",
               DRecord = "Division",
               IRecord = "Record",
               ILabel = "Finish",
               LResult = "Playoffs",
               CResult = "Result") %>%
    tab_spanner(label = "Final Record", columns = c(YRecord, CRecord, DRecord)) %>%
    tab_spanner(label = "Finishing Position", columns = c(YLabel, CLabel, DLabel)) %>%
    tab_spanner(label = "In-Season Tournament", columns = c(IRecord, ILabel, CResult)) %>%
    fmt_icon(columns = Awards) %>%
    sub_missing(missing_text = "") %>%
    #tab_options(table.width = px(1500)) %>%
    tab_style(style = list(cell_fill(color = TeamInfo2$Color1[1]), cell_text(color = TeamInfo2$Color3[1], weight = "bold")), locations = cells_title(groups = "title")) %>%
    tab_style(style = list(cell_fill(color = TeamInfo2$Color1[1]), cell_text(color = TeamInfo2$Color3[1], weight = "bold")), locations = cells_column_labels(columns = everything())) %>%
    tab_style(style = list(cell_fill(color = TeamInfo2$Color1[1]), cell_text(color = TeamInfo2$Color3[1], weight = "bold")), locations = cells_column_spanners())
  
  
  
  }
TeamStatsHistory <- function(TeamA) {
  
  TeamInfo2 <- TeamInfo %>%
    filter(Team == TeamA)
  
  TeamTotalStats2 <- TeamTotalStats %>%
    filter(Team == TeamA) %>%
    select(Year, Team, GP, MP, PTS, OREB, DREB, AST, STL, BLK, TOV, PM, `2P`, `2P%`, `3P`, `3P%`, FT, `FT%`, `TS%`, Rk_GP, Rk_MP, Rk_PTS, Rk_OREB, Rk_DREB, Rk_AST, Rk_STL, Rk_BLK, Rk_TOV, Rk_PM, Rk_2P, Rk_2Ppct, Rk_3P, Rk_3Ppct, Rk_FT, Rk_FTpct, Rk_TSpct) %>%
    mutate(Year = paste0(Year-1,"-",Year-2000))
  
  gt(TeamTotalStats2) %>%
    gt_theme_538() %>%
    tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_body()) %>%
    tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_body()) %>%
    tab_style(style = list(cell_fill(color = TeamInfo2$Color1[1]), cell_text(color = TeamInfo2$Color3[1])), locations = cells_body(columns = "Team")) %>%
    tab_style(style = list(cell_fill(color = TeamInfo2$Color1[1]), cell_text(color = TeamInfo2$Color3[1])), locations = cells_body(columns = "Year")) %>%
    gt_merge_stack(col1 = GP, col2 = Rk_GP, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = PM, col2 = Rk_PM, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = AST, col2 = Rk_AST, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = BLK, col2 = Rk_BLK, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = DREB, col2 = Rk_DREB, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = MP, col2 = Rk_MP, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = OREB, col2 = Rk_OREB, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = PTS, col2 = Rk_PTS, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = STL, col2 = Rk_STL, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = TOV, col2 = Rk_TOV, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = `2P`, col2 = Rk_2P, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = `3P`, col2 = Rk_3P, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = FT, col2 = Rk_FT, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = `2P%`, col2 = Rk_2Ppct, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = `3P%`, col2 = Rk_3Ppct, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = `FT%`, col2 = Rk_FTpct, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = `TS%`, col2 = Rk_TSpct, palette = c("black", "black")) %>%
    fmt_percent(columns = c("2P%", "3P%", "FT%", "TS%"), decimals = 2) %>%
    fmt_number(columns = c(GP, MP, PTS, OREB, DREB, AST, STL, BLK, TOV, PM), use_seps = TRUE, decimals = 0) %>%
    cols_align("center") %>%
    tab_style(style = list(cell_fill(color = TeamInfo2$Color1[1]), cell_text(color = TeamInfo2$Color3[1], weight = "bold")), locations = cells_title(groups = "title")) %>%
    tab_style(style = list(cell_fill(color = TeamInfo2$Color1[1]), cell_text(color = TeamInfo2$Color3[1], weight = "bold")), locations = cells_column_labels(columns = everything()))

  
  
}
PeriodSchedule <- function(DateA, YearA) {
  
  YearA <- as.numeric(YearA)
  
  PeriodA <- ScheduleInput %>%
    filter(Year == YearA) %>%
    filter(Dates == DateA) %>%
    select(Period) %>%
    pull()
  
  Schedule2 <- Schedule %>%
    filter(Year == YearA) %>%
    group_by(Period) %>%
    summarize(SDate = min(Date),
              EDate = max(Date)) %>%
    ungroup() %>%
    mutate(SDate = format(as.Date(SDate), "%b %d"),
           EDate = format(as.Date(EDate), "%b %d"),
           Dates = paste0(SDate, "-", EDate)) %>%
    filter(Period == PeriodA) %>%
    select(Dates) %>%
    pull()
  
  TeamSchedule2 <- Games %>%
    mutate(ID = 1:n()) %>%
    filter(Period == PeriodA) %>%
    filter(Year == YearA) %>%
    arrange(Type,ID) %>%
    mutate(Location = "@",
           Score = paste0(TeamAScore,"-",TeamBScore),
           Winner = ifelse(TeamBScore >= TeamAScore, TeamB, TeamA)) %>%
    select(Type, ID, TeamA, Location, TeamB, Score, Winner, TeamAScore, TeamBScore) %>%
    group_by(Type)
  
  gt(TeamSchedule2) %>%
    gt_theme_538() %>%
    gt_highlight_rows(rows = 1:nrow(TeamSchedule2), fill = "#A9B2B1") %>%
    tab_style(style = cell_fill(color = "#8CD47E"), locations = cells_body(columns = TeamA, rows = TeamAScore > TeamBScore)) %>%
    tab_style(style = cell_fill(color = "#FF6961"), locations = cells_body(columns = c(TeamB,Location), rows = TeamAScore > TeamBScore)) %>%
    tab_style(style = cell_fill(color = "#8CD47E"), locations = cells_body(columns = c(Location,TeamB), rows = TeamAScore <= TeamBScore)) %>%
    tab_style(style = cell_fill(color = "#FF6961"), locations = cells_body(columns = TeamA, rows = TeamAScore <= TeamBScore)) %>%
    cols_align("center") %>%
    cols_hide(Winner) %>%
    cols_hide(TeamAScore) %>%
    cols_hide(TeamBScore) %>%
    tab_header(title = md(paste0("SBCFBL Schedule for ", Schedule2, ", ",YearA-1,"-",YearA-2000, " Season"))) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", weight = "bold")), locations = cells_title(groups = "title")) %>%
    tab_style(style = list(cell_fill(color = "#A9B2B1"), cell_text(color = "black", align = "center")), locations = cells_row_groups(groups = everything())) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", weight = "bold")), locations = cells_column_labels(columns = everything())) %>%
    cols_label(TeamA = "Away",
               Location = "",
               TeamB = "Home")
  
}
LeagueStatsHistory <- function(YearA, DateA, CategoryA) {
  
  PeriodA <- ScheduleInput %>%
    filter(Year == YearA) %>%
    filter(Dates == DateA) %>%
    select(Period) %>%
    pull()

  Schedule2 <- Schedule %>%
    filter(Year == YearA) %>%
    group_by(Period) %>%
    summarize(SDate = min(Date),
              EDate = max(Date)) %>%
    ungroup() %>%
    mutate(SDate = format(as.Date(SDate), "%b %d"),
           EDate = format(as.Date(EDate), "%b %d"),
           Dates = paste0(SDate, "-", EDate)) %>%
    filter(Period == PeriodA) %>%
    select(Dates) %>%
    pull()
  
  YearA <- as.numeric(YearA)
  
  ordinal <- function(n) {
    suffix <- ifelse(n %% 100 %in% 11:13, "th",
                     ifelse(n %% 10 == 1, "st",
                            ifelse(n %% 10 == 2, "nd",
                                   ifelse(n %% 10 == 3, "rd", "th"))))
    paste0(n, suffix)}
  
  TeamPeriodStats3 <- TeamPeriodStats %>%
    filter(Period == PeriodA) %>%
    filter(Year == YearA)
  
  TeamPeriodStats2 <- TeamInfo %>%
    filter(Team != "Total") %>%
    select(Team, Color1, Color3) %>%
    left_join(TeamPeriodStats3, by = c('Team')) %>%
    select(-Period, -Year) %>%
    mutate(TOV = ifelse(is.na(MP) == T, Inf, TOV),
           PM = ifelse(is.na(MP) == T, -Inf, PM))
  
  TeamPeriodStats2[is.na(TeamPeriodStats2)] <- 0
  
    
  TeamPeriodStats2 <- TeamPeriodStats2 %>%
    mutate(Rk_PM    = ordinal(rank(-PM, ties.method = "min")),
           Rk_FGM2  = ordinal(rank(-FGM2, ties.method = "min")),
           Rk_FGA2  = ordinal(rank(-FGA2, ties.method = "min")),
           Rk_FGM3  = ordinal(rank(-FGM3, ties.method = "min")),
           Rk_FGA3  = ordinal(rank(-FGA3, ties.method = "min")),
           Rk_AST   = ordinal(rank(-AST, ties.method = "min")),
           Rk_BLK   = ordinal(rank(-BLK, ties.method = "min")),
           Rk_DREB  = ordinal(rank(-DREB, ties.method = "min")),
           Rk_FTA   = ordinal(rank(-FTA, ties.method = "min")),
           Rk_FTM   = ordinal(rank(-FTM, ties.method = "min")),
           Rk_MP    = ordinal(rank(-MP, ties.method = "min")),
           Rk_OREB  = ordinal(rank(-OREB, ties.method = "min")),
           Rk_PTS   = ordinal(rank(-PTS, ties.method = "min")),
           Rk_STL   = ordinal(rank(-STL, ties.method = "min")),
           Rk_TOV   = ordinal(rank(TOV, ties.method = "min")),
           Rk_2Ppct = ordinal(rank(-FGp2, ties.method = "min")),
           Rk_3Ppct = ordinal(rank(-FGp3, ties.method = "min")),
           Rk_FTpct = ordinal(rank(-FTp, ties.method = "min")),
           Rk_TSpct = ordinal(rank(-TSp, ties.method = "min"))) %>%
    ungroup() %>%
    rename(`TS%` = TSp,
           `2P%` = FGp2,
           `3P%` = FGp3,
           `FT%` = FTp) %>%    
    arrange(desc(.data[[CategoryA]])) %>%
    mutate(`2P`   = paste(FGM2, FGA2, sep = "/"),
           `3P`   = paste(FGM3, FGA3, sep = "/"),
           FT     = paste(FTM,  FTA,  sep = "/"),
           Rk_2P = paste(Rk_FGM2, Rk_FGA2, sep = "/"),
           Rk_3P = paste(Rk_FGM3, Rk_FGA3, sep = "/"),
           Rk_FT  = paste(Rk_FTM,  Rk_FTA,  sep = "/")) %>%
    select(Team, Color1, Color3, MP, PTS, OREB, DREB, AST, STL, BLK, TOV, PM, `2P`, `2P%`, `3P`, `3P%`, FT, `FT%`, `TS%`, Rk_PTS, Rk_MP, Rk_OREB, Rk_DREB, Rk_AST, Rk_STL, Rk_BLK, Rk_TOV, Rk_PM, Rk_2P, Rk_2Ppct, Rk_3P, Rk_3Ppct, Rk_FT, Rk_FTpct, Rk_TSpct) %>%
    relocate(all_of(CategoryA), .after = Team)
    
  
  gt(TeamPeriodStats2) %>%
    gt_theme_538() %>%
    tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_body()) %>%
    gt_merge_stack(col1 = PM, col2 = Rk_PM, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = AST, col2 = Rk_AST, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = BLK, col2 = Rk_BLK, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = DREB, col2 = Rk_DREB, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = MP, col2 = Rk_MP, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = OREB, col2 = Rk_OREB, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = PTS, col2 = Rk_PTS, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = STL, col2 = Rk_STL, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = TOV, col2 = Rk_TOV, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = `2P`, col2 = Rk_2P, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = `3P`, col2 = Rk_3P, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = FT, col2 = Rk_FT, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = `2P%`, col2 = Rk_2Ppct, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = `3P%`, col2 = Rk_3Ppct, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = `FT%`, col2 = Rk_FTpct, palette = c("black", "black")) %>%
    gt_merge_stack(col1 = `TS%`, col2 = Rk_TSpct, palette = c("black", "black")) %>%
    fmt_percent(columns = c("2P%", "3P%", "FT%", "TS%"), decimals = 2) %>%
    fmt_number(columns = c(MP, PTS, OREB, DREB, AST, STL, BLK, TOV, PM), use_seps = TRUE, decimals = 0) %>%
    cols_align("center") %>%
    cols_align(columns = Team, align = "right") %>%
    #tab_options(heading.title.font.size = 24) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", weight = "bold")), locations = cells_column_labels(columns = everything())) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", weight = "bold")), locations = cells_title()) %>%
    tab_header(title = md(paste0("SBCFBL Stats for ", Schedule2, ", ",YearA-1,"-",YearA-2000, " Season"))) %>%
    cols_hide(Color1) %>%
    cols_hide(Color3) %>%
    {reduce(seq_len(nrow(TeamPeriodStats2)), function(tbl, i) {
      tab_style(tbl, style = list(cell_fill(color = TeamPeriodStats2$Color1[i]), cell_text(weight = "bold", color = TeamPeriodStats2$Color3[i])),
          locations = cells_body(columns = "Team", rows = i))}, .init = .)}

  
  }
GetTeamLogo1 <- function(TeamA) {
  TeamInfo2 <- TeamInfo %>%
    filter(Team == TeamA)
  ggplot(TeamInfo2) +
    geom_rect(aes(xmin = -1, xmax = 1, ymin = -1, ymax = 1), fill = TeamInfo2$Color2[1], color = TeamInfo2$Color1[1], linewidth = 3) +
    geom_image(aes(x = 0, y = 0, image = Logo), size = 0.9) +
    coord_fixed() +
    theme_void()}
GetTeamLogo2 <- function(TeamA) {
  TeamInfo2 <- TeamInfo %>%
    filter(Team == TeamA)
  ggplot(TeamInfo2) +
    geom_rect(aes(xmin = -1, xmax = 1, ymin = -1, ymax = 1), fill = TeamInfo2$Color1[1], color = TeamInfo2$Color2[1], linewidth = 3) +
    geom_image(aes(x = 0, y = 0, image = Logo), size = 0.9) +
    coord_fixed() +
    theme_void()}
GetTeamName <- function(TeamA) {

TeamInfo2 <- TeamInfo %>%
  left_join(team_fonts, by = c("Team")) %>%
  filter(Team == TeamA)

ggplot(TeamInfo2) +
  geom_rect(aes(xmin = -12, xmax = 12, ymin = -1, ymax = 1), fill = TeamInfo2$Color1[1], color = TeamInfo2$Color2[1], linewidth = 3) +
  geom_text(aes(x = 0, y = 0, label = Team, family = Wording), color = TeamInfo2$Color3, size = 22) +
  coord_fixed() +
  theme_void()
}
ResultsMatrix <- function() {
  
  TeamInfo2 <- TeamInfo %>%
    filter(Team != "Total") %>%
    select(City, Color1, Color3)

  RecordMatrix2 <- RecordMatrix %>%
    select(-Logo) %>%
    left_join(TeamInfo2, by = c('City')) %>%
    mutate(City = paste(City, Nickname)) %>%
    select(-Nickname)
  
  gt_table <- gt(RecordMatrix2) %>%
    cols_align(columns = everything(), align = c('center')) %>%
    cols_align(columns = c("City"), align = c('right')) %>%
    gt_theme_538() %>%
    sub_missing(columns = everything(), missing_text = "") %>%
    cols_label(City = "Team") %>%
    tab_spanner(columns = ALB:VBJ, label = "Opponent") %>%
    tab_spanner(columns = City, label = "") %>%
    tab_style(style = cell_borders(sides = "left", color = "#DDDDDD", weight = px(2)), locations = cells_body(columns = ALB:VBJ)) %>%
    cols_width(City ~ px(90)) %>%
    tab_style(style = cell_text(size = px(12)), locations = cells_body(columns = City:VBJ)) %>%
    tab_style(style = cell_fill(color = "#A9B2B1"), locations = cells_body()) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", weight = "bold")), locations = cells_column_spanners()) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")),
      locations = cells_column_labels(columns = City)) %>%
    tab_header(title = md(paste0("All-Time Regular Season Head-to-Head Record"))) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", weight = "bold", size = px(20))), locations = cells_title(groups = "title")) %>%
    cols_hide(Color1) %>%
    cols_hide(Color3)
    
    

      
  for (i in 1:30) {
      team_abbr <- TeamInfo$Abb[i]
      bg_color <- TeamInfo2$Color1[i]
      text_color <- TeamInfo2$Color3[i]
      
      gt_table <- gt_table %>%
        tab_style(style = list(cell_fill(color = bg_color), cell_text(color = text_color)), locations = cells_column_labels(columns = all_of(team_abbr))) %>%
        tab_style(style = list(cell_fill(color = bg_color), cell_text(color = text_color)), locations = cells_body(columns = City, rows = i))}
  
  gt_table
  
  return(gt_table)

}



sidebar_content <- list(
  tags$h4("Time Period", style = "margin-top: 10px; margin-bottom: 5px; color: #333;"),
  numericInput("Input5", "Year:", value = as.numeric(format(Sys.Date(), "%Y")), 
               min = 2021, max = as.numeric(format(Sys.Date(), "%Y")) + 1),
  selectInput(inputId = "Input3", label = "Season Type:", 
              choices = sort(unique(Schedule$Season)), 
              selected = sort(unique(Schedule$Season))[3], 
              multiple = FALSE),
  selectInput("Input7", "Dates:", 
              choices = NULL, 
              selected = NULL),
  tags$h4("Selection", style = "margin-top: 15px; margin-bottom: 5px; color: #333;"),
  selectInput(inputId = "Input4", label = "Team:", 
              choices = TeamInfo$Team[1:30], 
              selected = TeamInfo$Team[9], 
              multiple = FALSE),
  selectizeInput(inputId = "Input2", label = "Player:", 
                 choices = NULL, selected = NULL, 
                 multiple = FALSE, options = list(create = FALSE)),
  numericInput("Input1", "Matchup ID:", value = 5609, min = 1, max = nrow(Games)),
  tags$h4("Display", style = "margin-top: 15px; margin-bottom: 5px; color: #333;"),
  selectInput(inputId = "Input6", "Statistic:",
              choices = c("MP", "TS%", "2P%", "3P%", "FT%", "PTS", "OREB", "DREB", "AST", "STL", "BLK", "TOV", "PM"), 
              selected = "PTS"))

ui <- page_navbar(
  theme = bs_theme(bootswatch = "journal"),
  title = "SBCFBL-Reference",
  sidebar = sidebar(
    class = "bg-secondary",
    sidebar_content),
  navset_card_pill(
    nav_panel(
      title = "Period Stats",
      layout_columns(
        card(full_screen = TRUE, fill = TRUE, gt_output("table9")),
        card(full_screen = TRUE, fill = TRUE, gt_output("table10")),
        col_widths =  c(6,6),
        row_heights = c(1))),
    nav_panel(
      title = "Matchup Explorer",
      layout_columns(
        card(full_screen = TRUE, fill = TRUE, gt_output("table1")),
        card(full_screen = TRUE, fill = TRUE, gt_output("table2")),
        col_widths = c(4,8),
        row_heights = c(1))),
    nav_panel(
      title = "Team Rosters & Schedule",
      layout_columns(
        #card(full_screen = TRUE, fill = TRUE, plotOutput("plot2")),
        #card(full_screen = TRUE, fill = TRUE, plotOutput("plot5B")),
        #card(full_screen = TRUE, fill = TRUE, plotOutput("plot3")),
        card(full_screen = TRUE, fill = TRUE, gt_output("table7")),
        card(full_screen = TRUE, fill = TRUE, gt_output("table8")),
        col_widths =  c(7,5),
        row_heights = c(1))),
    nav_panel(
      title = "Player Stats",
      layout_columns(
        #value_box(title = "Player:", textOutput("text0"), showcase = bs_icon("person-fill")),
        #card(full_screen = TRUE, fill = TRUE, plotOutput("plot4")),
        card(full_screen = TRUE, fill = TRUE, gt_output("table3")),
        col_widths = c(12),
        row_heights = c(1))),
    nav_panel(
      title = "Playoff Bracket",
      layout_columns(
        card(full_screen = TRUE, fill = TRUE, gt_output("table28")),
        card(full_screen = TRUE, fill = TRUE, plotOutput("plot1")),
        card(full_screen = TRUE, fill = TRUE, gt_output("table17")),
        col_widths =  c(3,6,3),
        row_heights = c(1))),
    nav_panel(
      title = "Cup Tournament",
      layout_columns(
        card(full_screen = TRUE, fill = TRUE, gt_output("table28B")),
        card(full_screen = TRUE, fill = TRUE, plotOutput("plot1B")),
        card(full_screen = TRUE, fill = TRUE, gt_output("table17B")),
        col_widths =  c(3,6,3),
        row_heights = c(1))),
    nav_panel(
      title = "League Leaders",
      layout_columns(
        card(full_screen = TRUE, fill = TRUE, gt_output("table16")),
        col_widths = rep(12),
        row_heights = c(1))),
    nav_panel(
      title = "Team Leaders",
      layout_columns(
        card(full_screen = TRUE, fill = TRUE, gt_output("table4")),
        col_widths = rep(12),
        row_heights = c(1))),
    nav_panel(
      title = "Franchise History",
      layout_columns(
        #card(full_screen = TRUE, fill = TRUE, plotOutput("plot2")),
        #card(full_screen = TRUE, fill = TRUE, plotOutput("plot5")),
        #card(full_screen = TRUE, fill = TRUE, plotOutput("plot3")),
        card(full_screen = TRUE, fill = TRUE, gt_output("table5")),
        card(full_screen = TRUE, fill = TRUE, gt_output("table6")),
        col_widths =  c(12,12),
        row_heights = c(1,1))),
    nav_panel(
      title = "Head-to-Head",
       layout_columns(
        card(full_screen = TRUE, fill = TRUE, gt_output("table30")),
        col_widths =  c(12),
        row_heights = c(1)))
    ))
  
server <- function(input, output, session) {
  #thematic_shiny()
  observe({
    selected_year <- input$Input5
    
    # Filter dates based on selected year
    available_dates <- ScheduleInput$Dates[ScheduleInput$Year == selected_year]
    
    # Update Input7 choices
    updateSelectInput(session, "Input7",
                      choices = available_dates,
                      selected = if(length(available_dates) > 0) available_dates[1] else NULL)
  })
  
  updateSelectizeInput(session, inputId = "Input2", choices = sort(unique(Careers$PlayerName)), server = TRUE)
  #bs_themer()
  
  output$table1 <- render_gt({GameRecap(input$Input1)})
  output$table2 <- render_gt({GameRecapPlayers(input$Input1)}) 
  output$table3 <- render_gt({CareerSeason(input$Input2, input$Input3)})
  output$table4 <- render_gt({AllTimeTeamLeader(input$Input4, input$Input3, input$Input6)}) 
  
  output$table5 <- render_gt({TeamHistory(input$Input4)})
  output$table6 <- render_gt({TeamStatsHistory(input$Input4)})
  
  output$table7 <- render_gt({TeamSeason(input$Input4, input$Input5, input$Input3)})
  output$table8 <- render_gt({TeamSchedule(input$Input4, input$Input5)})
  
  output$table9 <- render_gt({LeagueStatsHistory(input$Input5, input$Input7, input$Input6)})
  output$table10 <- render_gt({PeriodSchedule(input$Input7, input$Input5)})

  output$table16 <- render_gt({AllTimeLeaders(input$Input3, input$Input6)}) 

  output$table28 <- render_gt({GetStandings(input$Input5, "West")}) 
  output$table17 <- render_gt({GetStandings(input$Input5, "East")}) 
  output$table28B <- render_gt({GetStandings2(input$Input5, "West")}) 
  output$table17B <- render_gt({GetStandings2(input$Input5, "East")}) 
  output$table30 <- render_gt({ResultsMatrix()}) 
  output$text0 <- renderText({print(input$Input2)})
  
  output$plot4 <- renderPlot({PlayerHeadshot(input$Input2)})
  output$plot1 <- renderPlot({MakeBracket(input$Input5)})
  output$plot1B <- renderPlot({MakeBracket2(input$Input5)})
  #output$plot2 <- renderPlot({GetTeamLogo1(input$Input4)})
  #output$plot3 <- renderPlot({GetTeamLogo2(input$Input4)})
  output$plot5 <- renderPlot({GetTeamName(input$Input4)})
  output$plot5B <- renderPlot({GetTeamName(input$Input4)})
}

shinyApp(ui, server)
