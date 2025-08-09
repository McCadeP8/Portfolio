library(tidyverse)
library(gt)
library(gtExtras)
library(readxl)
library(shiny)
library(googlesheets4)
library(ggimage)
library(conflicted)
library(svglite)
library(htmltools)
library(ggpath)
library(ggdark)
library(bslib)
library(bsicons)
library(thematic)
library(sysfonts)
library(showtext)

conflict_prefer("filter", "dplyr")
gs4_deauth()
options(scipen = 99)

# OPTIMIZATION 1: Cache data loading with error handling
sheet_key <- "11YuW1DTPVid5OUcludvPE4-EqU751qp5l21lDK6V7PE"

# Function to safely load data with caching
load_sheet_data <- function() {
  tryCatch({
    list(
      Players = range_read(sheet_key, sheet = "Players"),
      TotalCapBase = range_read(sheet_key, sheet = "BaseCap"),
      Cap = range_read(sheet_key, sheet = "Cap"),
      Exceptions = range_read(sheet_key, sheet = "Exceptions2"),
      SBC = range_read(sheet_key, sheet = "SBCLogos"),
      Pictures = range_read(sheet_key, sheet = "Pictures"),
      FA = range_read(sheet_key, sheet = "FreeAgencyCode"),
      DraftPicks = range_read(sheet_key, sheet = "Draft Picks2"),
      Schedule = range_read(sheet_key, sheet = "2024 Schedule"),
      TeamStats3 = range_read(sheet_key, sheet = "Matchup Stats"),
      InSeason = range_read(sheet_key, sheet = "InSeason"),
      Draft = range_read(sheet_key, sheet = "Draft"),
      FAOrder = range_read(sheet_key, sheet = "FreeAgencyOrder"),
      InSeason2 = range_read(sheet_key, sheet = "InSeason2")
    )
  }, error = function(e) {
    showNotification("Error loading data from Google Sheets", type = "error")
    return(NULL)
  })
}

# Load data once at startup
cat("Loading data from Google Sheets...\n")
app_data <- load_sheet_data()

# Check if data loaded successfully
if (is.null(app_data)) {
  stop("Failed to load data from Google Sheets")
}

# Extract data objects for compatibility with existing code
Players <- app_data$Players
TotalCapBase <- app_data$TotalCapBase
Cap <- app_data$Cap
Exceptions <- app_data$Exceptions
SBC <- app_data$SBC
Pictures <- app_data$Pictures
DraftPicks <- app_data$DraftPicks
Schedule <- app_data$Schedule
FA = app_data$FA
TeamStats3 <- app_data$TeamStats3
InSeason <- app_data$InSeason
Draft <- app_data$Draft
FAOrder <- app_data$FAOrder
InSeason2 <- app_data$InSeason2

cat("Data loaded successfully!\n")

Players <- Players %>%
  select(-Type2023,-Y2023, -Y2024, -Type2024,-Type2025,-Y2025) %>%
  filter(is.na(Y2026) == F | BirdRights == "Draft Rights") %>%
  mutate(Type = as.character(Type),
         Team = as.character(Team),
         Player = as.character(Player),
         BirdRights = as.character(BirdRights),
         Type2026 = as.character(Type2026),
         Type2027 = as.character(Type2027),
         Type2028 = as.character(Type2028),
         Type2029 = as.character(Type2029),
         Type2030 = as.character(Type2030),
         Type2031 = as.character(Type2031),
         Type2032 = as.character(Type2032),
         Trade.Restriction = as.character(Trade.Restriction),
         Y2026 = as.numeric(Y2026),
         Y2027 = as.numeric(Y2027),
         Y2028 = as.numeric(Y2028),
         Y2029 = as.numeric(Y2029),
         Y2030 = as.numeric(Y2030),
         Y2031 = as.numeric(Y2031),
         Y2032 = as.numeric(Y2032)) %>%
  arrange(Team)
Cap <- Cap %>%
  mutate(Type = as.character(Type),
         Team = as.character(Team),
         Player = as.character(Player),
         BirdRights = as.character(BirdRights),
         Type2026 = as.character(Type2026),
         Type2027 = as.character(Type2027),
         Type2028 = as.character(Type2028),
         Type2029 = as.character(Type2029),
         Type2030 = as.character(Type2030),
         Type2031 = as.character(Type2031),
         Type2032 = as.character(Type2032),
         Trade.Restriction = as.character(Trade.Restriction),
         Y2026 = as.numeric(Y2026),
         Y2027 = as.numeric(Y2027),
         Y2028 = as.numeric(Y2028),
         Y2029 = as.numeric(Y2029),
         Y2030 = as.numeric(Y2030),
         Y2031 = as.numeric(Y2031),
         Y2032 = as.numeric(Y2032))
Exceptions <- Exceptions %>%
  mutate(Type = as.character(Type),
         Team = as.character(Team),
         Player = as.character(Player),
         BirdRights = as.character(BirdRights),
         Type2026 = as.character(Type2026),
         Type2027 = as.character(Type2027),
         Type2028 = as.character(Type2028),
         Type2029 = as.character(Type2029),
         Type2030 = as.character(Type2030),
         Type2031 = as.character(Type2031),
         Type2032 = as.character(Type2032),
         Trade.Restriction = as.character(Trade.Restriction),
         Y2026 = as.numeric(Y2026),
         Y2027 = as.numeric(Y2027),
         Y2028 = as.numeric(Y2028),
         Y2029 = as.numeric(Y2029),
         Y2030 = as.numeric(Y2030),
         Y2031 = as.numeric(Y2031),
         Y2032 = as.numeric(Y2032))



CapSheet <- function(TeamName) {
  Players2 <- Players %>%
    filter(Team == TeamName) %>%
    arrange(Type,desc(Y2026))
  Players3 <- Players2 %>%
    mutate(Y2026 = ifelse(Type2026 %in% c("Restricted","Unrestricted"),NA,Y2026),
           Y2027 = ifelse(Type2027 %in% c("Restricted","Unrestricted"),NA,Y2027),
           Y2028 = ifelse(Type2028 %in% c("Restricted","Unrestricted"),NA,Y2028),
           Y2029 = ifelse(Type2029 %in% c("Restricted","Unrestricted"),NA,Y2029),
           Y2030 = ifelse(Type2030 %in% c("Restricted","Unrestricted"),NA,Y2030),
           Y2031 = ifelse(Type2031 %in% c("Restricted","Unrestricted"),NA,Y2031),
           Y2032 = ifelse(Type2032 %in% c("Restricted","Unrestricted"),NA,Y2032))
  Players4 <- Players2 %>%
    mutate(Y2026 = ifelse(Type2026 %in% c("Restricted","Unrestricted","Dead"),NA,Y2026),
           Y2027 = ifelse(Type2027 %in% c("Restricted","Unrestricted","Dead"),NA,Y2027),
           Y2028 = ifelse(Type2028 %in% c("Restricted","Unrestricted","Dead"),NA,Y2028),
           Y2029 = ifelse(Type2029 %in% c("Restricted","Unrestricted","Dead"),NA,Y2029),
           Y2030 = ifelse(Type2030 %in% c("Restricted","Unrestricted","Dead"),NA,Y2030),
           Y2031 = ifelse(Type2031 %in% c("Restricted","Unrestricted","Dead"),NA,Y2031),
           Y2032 = ifelse(Type2032 %in% c("Restricted","Unrestricted","Dead"),NA,Y2032))
  Exceptions2 <- Exceptions %>%
    filter(Team %in% c("All",TeamName))
  Team <- SBC %>%
    filter(City == TeamName)
  Logo <- Team$Logo
  
  
  Min2026Hold <- Exceptions2$Y2026[1]*(12-sum(Players2$Y2026 > 0, na.rm = T))
  Exceptions2$Y2026[1] <- ifelse(Min2026Hold <= 0, 0, Min2026Hold)
  Min2027Hold <- Exceptions2$Y2027[1]*(12-sum(Players2$Y2027 > 0, na.rm = T))
  Exceptions2$Y2027[1] <- ifelse(Min2027Hold <= 0, 0, Min2027Hold)
  Min2028Hold <- Exceptions2$Y2028[1]*(12-sum(Players2$Y2028 > 0, na.rm = T))
  Exceptions2$Y2028[1] <- ifelse(Min2028Hold <= 0, 0, Min2028Hold)
  Min2029Hold <- Exceptions2$Y2029[1]*(12-sum(Players2$Y2029 > 0, na.rm = T))
  Exceptions2$Y2029[1] <- ifelse(Min2029Hold <= 0, 0, Min2029Hold)
  Min2030Hold <- Exceptions2$Y2030[1]*(12-sum(Players2$Y2030 > 0, na.rm = T))
  Exceptions2$Y2030[1] <- ifelse(Min2030Hold <= 0, 0, Min2030Hold)
  Min2031Hold <- Exceptions2$Y2031[1]*(12-sum(Players2$Y2031 > 0, na.rm = T))
  Exceptions2$Y2031[1] <- ifelse(Min2031Hold <= 0, 0, Min2031Hold)
  Min2032Hold <- Exceptions2$Y2032[1]*(12-sum(Players2$Y2032 > 0, na.rm = T))
  Exceptions2$Y2032[1] <- ifelse(Min2032Hold <= 0, 0, Min2032Hold)
  
  
  CapHit <- rbind(Players2,Exceptions2)
  CapHit <- CapHit %>%
    mutate(Y2026 = ifelse(Player == "Room Mid-Level", 0, Y2026)) %>%
    summarize(Y2026 = sum(Y2026, na.rm = T),
              Y2027 = sum(Y2027, na.rm = T),
              Y2028 = sum(Y2028, na.rm = T),
              Y2029 = sum(Y2029, na.rm = T),
              Y2030 = sum(Y2030, na.rm = T),
              Y2031 = sum(Y2031, na.rm = T),
              Y2032 = sum(Y2032, na.rm = T)) %>%
    mutate(Type = "Cap Hits",
           Team = "",
           Player = "Salary Cap Hit",
           BirdRights = "",
           Type2026 = "",
           Type2027 = "",
           Type2028 = "",
           Type2029 = "",
           Type2030 = "",
           Type2031 = "",
           Type2032 = "",
           Trade.Restriction = "",
           Type = as.character(Type),
           Team = as.character(Team),
           Player = as.character(Player),
           BirdRights = as.character(BirdRights),
           Type2026 = as.character(Type2026),
           Type2027 = as.character(Type2027),
           Type2028 = as.character(Type2028),
           Type2029 = as.character(Type2029),
           Type2030 = as.character(Type2030),
           Type2031 = as.character(Type2031),
           Type2032 = as.character(Type2032),
           Trade.Restriction = as.character(Trade.Restriction),
           Y2026 = as.numeric(Y2026),
           Y2027 = as.numeric(Y2027),
           Y2028 = as.numeric(Y2028),
           Y2029 = as.numeric(Y2029),
           Y2030 = as.numeric(Y2030),
           Y2031 = as.numeric(Y2031),
           Y2032 = as.numeric(Y2032))
  CapDiff <- rbind(Cap,CapHit)
  CapDiff <- CapDiff %>%
    filter(Player == "Salary Cap" | Player == "Salary Cap Hit")
  CapDiff <- rbind(CapDiff, rep(NA, ncol(CapDiff)))
  CapDiff$Type[3] <- "Cap Space"
  CapDiff$Y2026[3] <- CapDiff$Y2026[1]-CapDiff$Y2026[2]
  CapDiff$Y2027[3] <- CapDiff$Y2027[1]-CapDiff$Y2027[2]
  CapDiff$Y2028[3] <- CapDiff$Y2028[1]-CapDiff$Y2028[2]
  CapDiff$Y2029[3] <- CapDiff$Y2029[1]-CapDiff$Y2029[2]
  CapDiff$Y2030[3] <- CapDiff$Y2030[1]-CapDiff$Y2030[2]
  CapDiff$Y2031[3] <- CapDiff$Y2031[1]-CapDiff$Y2031[2]
  CapDiff$Y2032[3] <- CapDiff$Y2032[1]-CapDiff$Y2032[2]
  CapDiff$BirdRights <- ""
  CapDiff$Trade.Restriction <- ""
  CapDiff$Team <- ""
  CapDiff$Player <- "Cap Space"
  CapDiff <- CapDiff %>%
    filter(Type == "Cap Space")
  
  Exceptions3 <- Exceptions %>%
    filter(Team %in% c("All",TeamName))
  Min2026Hold <- Exceptions3$Y2026[1]*(12-sum(Players4$Y2026 > 0, na.rm = T))
  Exceptions3$Y2026[1] <- ifelse(Min2026Hold <= 0, 0, Min2026Hold)
  Min2027Hold <- Exceptions3$Y2027[1]*(12-sum(Players4$Y2027 > 0, na.rm = T))
  Exceptions3$Y2027[1] <- ifelse(Min2027Hold <= 0, 0, Min2027Hold)
  Min2028Hold <- Exceptions3$Y2028[1]*(12-sum(Players4$Y2028 > 0, na.rm = T))
  Exceptions3$Y2028[1] <- ifelse(Min2028Hold <= 0, 0, Min2028Hold)
  Min2029Hold <- Exceptions3$Y2029[1]*(12-sum(Players4$Y2029 > 0, na.rm = T))
  Exceptions3$Y2029[1] <- ifelse(Min2029Hold <= 0, 0, Min2029Hold)
  Min2030Hold <- Exceptions3$Y2030[1]*(12-sum(Players4$Y2030 > 0, na.rm = T))
  Exceptions3$Y2030[1] <- ifelse(Min2030Hold <= 0, 0, Min2030Hold)
  Min2031Hold <- Exceptions3$Y2031[1]*(12-sum(Players4$Y2031 > 0, na.rm = T))
  Exceptions3$Y2031[1] <- ifelse(Min2031Hold <= 0, 0, Min2031Hold)
  Min2032Hold <- Exceptions3$Y2032[1]*(12-sum(Players4$Y2032 > 0, na.rm = T))
  Exceptions3$Y2032[1] <- ifelse(Min2032Hold <= 0, 0, Min2032Hold)
  
  Exceptions3 <- Exceptions3 %>%
    filter(Player == "Minimum")
  ApronHit <- rbind(Players3,Exceptions3)
  ApronHit <- ApronHit %>%
    summarize(Y2026 = sum(Y2026, na.rm = T),
              Y2027 = sum(Y2027, na.rm = T),
              Y2028 = sum(Y2028, na.rm = T),
              Y2029 = sum(Y2029, na.rm = T),
              Y2030 = sum(Y2030, na.rm = T),
              Y2031 = sum(Y2031, na.rm = T),
              Y2032 = sum(Y2032, na.rm = T)) %>%
    mutate(Type = "Cap Hits",
           Team = "",
           Player = "Tax Hit",
           BirdRights = "",
           Type2026 = "",
           Type2027 = "",
           Type2028 = "",
           Type2029 = "",
           Type2030 = "",
           Type2031 = "",
           Type2032 = "",
           Trade.Restriction = "",
           Type = as.character(Type),
           Team = as.character(Team),
           Player = as.character(Player),
           BirdRights = as.character(BirdRights),
           Type2026 = as.character(Type2026),
           Type2027 = as.character(Type2027),
           Type2028 = as.character(Type2028),
           Type2029 = as.character(Type2029),
           Type2030 = as.character(Type2030),
           Type2031 = as.character(Type2031),
           Type2032 = as.character(Type2032),
           Trade.Restriction = as.character(Trade.Restriction),
           Y2026 = as.numeric(Y2026),
           Y2027 = as.numeric(Y2027),
           Y2028 = as.numeric(Y2028),
           Y2029 = as.numeric(Y2029),
           Y2030 = as.numeric(Y2030),
           Y2031 = as.numeric(Y2031),
           Y2032 = as.numeric(Y2032))
  
  TaxDiff <- rbind(Cap,ApronHit)
  TaxDiff <- TaxDiff %>%
    filter(Player == "Luxury Tax" | Player == "Tax Hit")
  TaxDiff <- rbind(TaxDiff, rep(NA, ncol(TaxDiff)))
  TaxDiff$Type[3] <- "Cap Space"
  TaxDiff$Y2026[3] <- TaxDiff$Y2026[1]-TaxDiff$Y2026[2]
  TaxDiff$Y2027[3] <- TaxDiff$Y2027[1]-TaxDiff$Y2027[2]
  TaxDiff$Y2028[3] <- TaxDiff$Y2028[1]-TaxDiff$Y2028[2]
  TaxDiff$Y2029[3] <- TaxDiff$Y2029[1]-TaxDiff$Y2029[2]
  TaxDiff$Y2030[3] <- TaxDiff$Y2030[1]-TaxDiff$Y2030[2]
  TaxDiff$Y2031[3] <- TaxDiff$Y2031[1]-TaxDiff$Y2031[2]
  TaxDiff$Y2032[3] <- TaxDiff$Y2032[1]-TaxDiff$Y2032[2]
  TaxDiff$BirdRights <- ""
  TaxDiff$Trade.Restriction <- ""
  TaxDiff$Team <- ""
  TaxDiff$Player <- "Tax Space"
  TaxDiff <- TaxDiff %>%
    filter(Type == "Cap Space")
  
  Apron1Diff <- rbind(Cap,ApronHit)
  Apron1Diff <- Apron1Diff %>%
    filter(Player == "Apron #1" | Player == "Tax Hit")
  Apron1Diff <- rbind(Apron1Diff, rep(NA, ncol(Apron1Diff)))
  Apron1Diff$Type[3] <- "Cap Space"
  Apron1Diff$Y2026[3] <- Apron1Diff$Y2026[1]-Apron1Diff$Y2026[2]
  Apron1Diff$Y2027[3] <- Apron1Diff$Y2027[1]-Apron1Diff$Y2027[2]
  Apron1Diff$Y2028[3] <- Apron1Diff$Y2028[1]-Apron1Diff$Y2028[2]
  Apron1Diff$Y2029[3] <- Apron1Diff$Y2029[1]-Apron1Diff$Y2029[2]
  Apron1Diff$Y2030[3] <- Apron1Diff$Y2030[1]-Apron1Diff$Y2030[2]
  Apron1Diff$Y2031[3] <- Apron1Diff$Y2031[1]-Apron1Diff$Y2031[2]
  Apron1Diff$Y2032[3] <- Apron1Diff$Y2032[1]-Apron1Diff$Y2032[2]
  Apron1Diff$BirdRights <- ""
  Apron1Diff$Trade.Restriction <- ""
  Apron1Diff$Team <- ""
  Apron1Diff$Player <- "Apron 1 Space"
  Apron1Diff <- Apron1Diff %>%
    filter(Type == "Cap Space")
  
  
  Apron2Diff <- rbind(Cap,ApronHit)
  Apron2Diff <- Apron2Diff %>%
    filter(Player == "Apron #2" | Player == "Tax Hit")
  Apron2Diff <- rbind(Apron2Diff, rep(NA, ncol(Apron2Diff)))
  Apron2Diff$Type[3] <- "Cap Space"
  Apron2Diff$Y2026[3] <- Apron2Diff$Y2026[1]-Apron2Diff$Y2026[2]
  Apron2Diff$Y2027[3] <- Apron2Diff$Y2027[1]-Apron2Diff$Y2027[2]
  Apron2Diff$Y2028[3] <- Apron2Diff$Y2028[1]-Apron2Diff$Y2028[2]
  Apron2Diff$Y2029[3] <- Apron2Diff$Y2029[1]-Apron2Diff$Y2029[2]
  Apron2Diff$Y2030[3] <- Apron2Diff$Y2030[1]-Apron2Diff$Y2030[2]
  Apron2Diff$Y2031[3] <- Apron2Diff$Y2031[1]-Apron2Diff$Y2031[2]
  Apron2Diff$Y2032[3] <- Apron2Diff$Y2032[1]-Apron2Diff$Y2032[2]
  Apron2Diff$BirdRights <- ""
  Apron2Diff$Trade.Restriction <- ""
  Apron2Diff$Team <- ""
  Apron2Diff$Player <- "Apron 2 Space"
  Apron2Diff <- Apron2Diff %>%
    filter(Type == "Cap Space")
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  Table <- rbind(Cap,Players2,Exceptions2,CapHit,ApronHit,CapDiff,TaxDiff,Apron1Diff,Apron2Diff)
  Table <- Table %>%
    filter(is.na(Player) == F) %>%
    left_join(Pictures, by = c('Player')) %>%
    select(20,1:19) %>%
    mutate(Picture = ifelse(is.na(Picture) == T, Logo, Picture)) %>%
    group_by(Type)
  
  A <- gt(Table) %>%
    gt_theme_espn() %>%
    tab_header(title = md(
      paste0(
        "<div style='text-align: center; font-weight: bold; font-size: 1.1em;'>",
        "<span style='color:#d29d69'>Guaranteed</span>",
        "<span style='color:#000000'> | </span>",
        "<span style='color:#c17272'>Non-Guaranteed</span>",
        "<span style='color:#000000'> | </span>",
        "<span style='color:#7fa1c5'>Team Option</span>",
        "<span style='color:#000000'> | </span>",
        "<span style='color:#9d93b3'>Unrestricted Free Agent</span>",
        "<span style='color:#000000'> | </span>",
        "<span style='color:#93b3b3'>Restricted Free Agent</span>",
        "<span style='color:#000000'> | </span>",
        "<span style='color:#a6a6a6'>Dead</span>",
        "</div>"))) %>%
    #text_transform(locations = cells_body(columns = Picture),
    #    fn = function(x) {map_chr(x, function(path) {
    #                if (file.exists(path)) {local_image(filename = path, height = 40)} 
    #                else {paste("Missing:", basename(path))}})}) %>%
    cols_hide(columns = c(Type2026,Type2027,Type2028,Type2029,Type2030,Type2031,Type2032,Team, Picture)) %>%
    cols_align(columns = everything(), align = "center") %>%
    cols_align(columns = Player, align = "left") %>%
    fmt_currency(columns = c(Y2026,Y2027,Y2028,Y2029,Y2030,Y2031,Y2032), currency = "USD", decimals = 0) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2026, rows = Type2026 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2027, rows = Type2027 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2028, rows = Type2028 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2029, rows = Type2029 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2030, rows = Type2030 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2031, rows = Type2031 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2032, rows = Type2032 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2026, rows = Type2026 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2027, rows = Type2027 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2028, rows = Type2028 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2029, rows = Type2029 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2030, rows = Type2030 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2031, rows = Type2031 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2032, rows = Type2032 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2026, rows = Type2026 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2027, rows = Type2027 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2028, rows = Type2028 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2029, rows = Type2029 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2030, rows = Type2030 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2031, rows = Type2031 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2032, rows = Type2032 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2026, rows = Type2026 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2027, rows = Type2027 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2028, rows = Type2028 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2029, rows = Type2029 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2030, rows = Type2030 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2031, rows = Type2031 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2032, rows = Type2032 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2026, rows = Type2026 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2027, rows = Type2027 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2028, rows = Type2028 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2029, rows = Type2029 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2030, rows = Type2030 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2031, rows = Type2031 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2032, rows = Type2032 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2026, rows = Type2026 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2027, rows = Type2027 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2028, rows = Type2028 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2029, rows = Type2029 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2030, rows = Type2030 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2031, rows = Type2031 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2032, rows = Type2032 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = Team$Color1), cell_text(color = Team$Color3[1], align = "center")), locations = cells_row_groups()) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_body(columns = everything(), rows = Player == "Salary Cap")) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_body(columns = everything(), rows = Player == "Luxury Tax")) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_body(columns = everything(), rows = Player == "Total Cap Hit")) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_body(columns = everything(), rows = Player == "Total Salary")) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_body(columns = everything(), rows = Player == "Salary Cap Hit")) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_body(columns = everything(), rows = Player == "Tax Hit")) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_body(columns = everything(), rows = Player == "Apron #1")) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_body(columns = everything(), rows = Player == "Apron #2")) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2026, rows = Type == "Cap Space" & Y2026 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2027, rows = Type == "Cap Space" & Y2027 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2028, rows = Type == "Cap Space" & Y2028 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2029, rows = Type == "Cap Space" & Y2029 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2030, rows = Type == "Cap Space" & Y2030 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2031, rows = Type == "Cap Space" & Y2031 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2032, rows = Type == "Cap Space" & Y2032 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2026, rows = Type == "Cap Space" & Y2026 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2027, rows = Type == "Cap Space" & Y2027 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2028, rows = Type == "Cap Space" & Y2028 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2029, rows = Type == "Cap Space" & Y2029 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2030, rows = Type == "Cap Space" & Y2030 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2031, rows = Type == "Cap Space" & Y2031 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2032, rows = Type == "Cap Space" & Y2032 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#EAD1DC"), cell_text(color = "black")), locations = cells_body(columns = c(Y2026,Y2027,Y2028,Y2029,Y2030,Y2031,Y2032), rows = Player == "Minimum")) %>%
    tab_style(style = list(cell_fill(color = "#EAD1DC"), cell_text(color = "black")), locations = cells_body(columns = c(Y2026,Y2027,Y2028,Y2029,Y2030,Y2031,Y2032), rows = Player == "Bi-Annual")) %>%
    tab_style(style = list(cell_fill(color = "#EAD1DC"), cell_text(color = "black")), locations = cells_body(columns = c(Y2026,Y2027,Y2028,Y2029,Y2030,Y2031,Y2032), rows = Player == "Disabled-Player")) %>%
    tab_style(style = list(cell_fill(color = "#EAD1DC"), cell_text(color = "black")), locations = cells_body(columns = c(Y2026,Y2027,Y2028,Y2029,Y2030,Y2031,Y2032), rows = Player %in% c("Full Mid-Level", "Room Mid-Level","No Mid-Level", "Taxpayer Mid-Level"))) %>%
    tab_style(style = list(cell_fill(color = "#EAD1DC"), cell_text(color = "black")), locations = cells_body(columns = c(Y2026,Y2027,Y2028,Y2029,Y2030,Y2031,Y2032), rows = Player == "Traded-Player")) %>%
    sub_missing(missing_text = "") %>%
    cols_label(
      Y2026 = "2025-26",
      Y2027 = "2026-27",
      Y2028 = "2027-28",
      Y2029 = "2028-29",
      Y2030 = "2029-30",
      Y2031 = "2030-31",
      Y2032 = "2031-32",
      BirdRights = "Bird Rights",
      Trade.Restriction = "Trade Restriction",
      Picture = "")
  return(A)}
Picks <- function(TeamName) {
  
  Team <- SBC %>%
    filter(City == TeamName)
  DraftPicksTeam <- DraftPicks %>%
    filter(OGTeam == TeamName | CurrentTeam == TeamName | grepl(TeamName, TeamTouched) == T) %>%
    filter(Year != 2023) %>%
    filter(Year != 2024) %>%
    filter(Year != 2025) %>%
    arrange(Year, Round, OGTeam) %>%
    left_join(SBC, by = c('OGTeam' = 'City')) %>%
    mutate(OGTeam2 = Logo) %>%
    select(1:2,OGTeam2,4:6,OGTeam) %>%
    left_join(SBC, by = c('CurrentTeam' = 'City')) %>%
    mutate(CurrentTeam2 = Logo) %>%
    select(1:4,CurrentTeam2,Notes,OGTeam,CurrentTeam) %>%
    mutate(Type = ifelse(CurrentTeam == Team$City[1], "Current Picks", ifelse(OGTeam == Team$City[1], "Original Picks", "Touched Previously")),
           Type2 = ifelse(Type == "Current Picks", 1, ifelse(Type == "Original Picks", 2, 3))) %>%
    arrange(Type2, Round,Year, OGTeam) %>%
    select(Type, OGTeam2, CurrentTeam2, Year, Round, OGTeam, TeamTouched, CurrentTeam, Notes) %>%
    group_by(Type)
  
  A <- gt(DraftPicksTeam) %>%
    gt_theme_espn() %>%
    cols_hide(columns = c(OGTeam2, CurrentTeam2)) %>%
    cols_label(OGTeam = "Original",
               TeamTouched = "Middle",
               CurrentTeam = "Current") %>%
    #text_transform(locations = cells_body(columns = OGTeam2),
    #               fn = function(x) {map_chr(x, function(path) {
    #                 if (file.exists(path)) {local_image(filename = path, height = 40)} 
    #                 else {paste("Missing:", basename(path))}})}) %>%
    #text_transform(locations = cells_body(columns = CurrentTeam2),
    #               fn = function(x) {map_chr(x, function(path) {
    #                 if (file.exists(path)) {local_image(filename = path, height = 40)} 
    #                 else {paste("Missing:", basename(path))}})}) %>%
    tab_style(style = list(cell_fill(color = Team$Color1), cell_text(color = Team$Color3[1], align = "center")), locations = cells_row_groups()) %>%
    sub_missing(missing_text = "") %>%
    tab_style(style = list(cell_fill(color = "white"), cell_text(color = "black")), locations = cells_body(columns = everything())) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC"), cell_text(color = "black")), locations = cells_body(columns = everything(), rows = OGTeam == Team$City[1])) %>%
    tab_style(style = list(cell_fill(color = "#B7E1CD"), cell_text(color = "black")), locations = cells_body(columns = everything(), rows = CurrentTeam == Team$City[1])) %>%
    cols_align(columns = everything(), align = "center") %>%
    tab_style(style = list(cell_text(size = 100)), locations = cells_body(columns = everything()))
  return(A)}
AllPlayers <- function() {
  Order1 <- 1:7
  Type2026 <- c("Guaranteed","Non-Guaranteed","Unrestricted","Restricted","Draft Rights","Dead","Dead Coming Off")
  TotalPlayers <- data.frame(Order1,Type2026)
  TotalPlayers <- Players %>%
    left_join(Pictures, by = c('Player')) %>%
    select(20, 1:19) %>%
    left_join(SBC, by = c('Team' = 'City')) %>%
    dplyr::select(32,1:20) %>%
    left_join(TotalPlayers, by = c('Type2026')) %>%
    group_by(Type2026) %>%
    arrange(Order1,-Y2026,Team)
  gt(TotalPlayers) %>%
    gt_theme_espn() %>%
    tab_header(title = md(
      paste0(
        "<div style='text-align: center; font-weight: bold; font-size: 1.1em;'>",
        "<span style='color:#d29d69'>Guaranteed</span>",
        "<span style='color:#000000'> | </span>",
        "<span style='color:#c17272'>Non-Guaranteed</span>",
        "<span style='color:#000000'> | </span>",
        "<span style='color:#7fa1c5'>Team Option</span>",
        "<span style='color:#000000'> | </span>",
        "<span style='color:#9d93b3'>Unrestricted Free Agent</span>",
        "<span style='color:#000000'> | </span>",
        "<span style='color:#93b3b3'>Restricted Free Agent</span>",
        "<span style='color:#000000'> | </span>",
        "<span style='color:#a6a6a6'>Dead</span>",
        "</div>"))) %>%
    #text_transform(locations = cells_body(columns = Picture),
    #               fn = function(x) {map_chr(x, function(path) {
    #                 if (file.exists(path)) {local_image(filename = path, height = 40)} 
    #                 else {paste("Missing:", basename(path))}})}) %>%
    #text_transform(locations = cells_body(columns = Logo),
    #               fn = function(x) {map_chr(x, function(path) {
    #                 if (file.exists(path)) {local_image(filename = path, height = 40)} 
    #                 else {paste("Missing:", basename(path))}})}) %>%
    cols_hide(columns = c(Type2026,Type2027,Type2028,Type2029,Type2030,Type2031,Type2032,Type,Picture,Order1,Logo)) %>%
    cols_align(columns = everything(), align = "center") %>%
    cols_align(columns = Player, align = "left") %>%
    cols_align(columns = Team, align = "right") %>%
    fmt_currency(columns = c(Y2026,Y2027,Y2028,Y2029,Y2030,Y2031,Y2032), currency = "USD", decimals = 0) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2026, rows = Type2026 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2027, rows = Type2027 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2028, rows = Type2028 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2029, rows = Type2029 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2030, rows = Type2030 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2031, rows = Type2031 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD")), locations = cells_body(columns = Y2032, rows = Type2032 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2026, rows = Type2026 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2027, rows = Type2027 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2028, rows = Type2028 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2029, rows = Type2029 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2030, rows = Type2030 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2031, rows = Type2031 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC")), locations = cells_body(columns = Y2032, rows = Type2032 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2026, rows = Type2026 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2027, rows = Type2027 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2028, rows = Type2028 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2029, rows = Type2029 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2030, rows = Type2030 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2031, rows = Type2031 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3")), locations = cells_body(columns = Y2032, rows = Type2032 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2026, rows = Type2026 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2027, rows = Type2027 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2028, rows = Type2028 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2029, rows = Type2029 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2030, rows = Type2030 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2031, rows = Type2031 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9")), locations = cells_body(columns = Y2032, rows = Type2032 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2026, rows = Type2026 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2027, rows = Type2027 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2028, rows = Type2028 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2029, rows = Type2029 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2030, rows = Type2030 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2031, rows = Type2031 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = Y2032, rows = Type2032 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2026, rows = Type2026 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2027, rows = Type2027 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2028, rows = Type2028 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2029, rows = Type2029 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2030, rows = Type2030 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2031, rows = Type2031 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = Y2032, rows = Type2032 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "Black"), cell_text(color = "White", align = "center")), locations = cells_row_groups()) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_body(columns = everything(), rows = Player == "Salary Cap")) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_body(columns = everything(), rows = Player == "Luxury Tax")) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_body(columns = everything(), rows = Player == "Total Cap Hit")) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white")), locations = cells_body(columns = everything(), rows = Player == "Total Salary")) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2026, rows = Type == "Cap Space" & Y2026 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2027, rows = Type == "Cap Space" & Y2027 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2028, rows = Type == "Cap Space" & Y2028 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2029, rows = Type == "Cap Space" & Y2029 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2030, rows = Type == "Cap Space" & Y2030 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2031, rows = Type == "Cap Space" & Y2031 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Y2032, rows = Type == "Cap Space" & Y2032 <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2026, rows = Type == "Cap Space" & Y2026 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2027, rows = Type == "Cap Space" & Y2027 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2028, rows = Type == "Cap Space" & Y2028 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2029, rows = Type == "Cap Space" & Y2029 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2030, rows = Type == "Cap Space" & Y2030 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2031, rows = Type == "Cap Space" & Y2031 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = Y2032, rows = Type == "Cap Space" & Y2032 > 0)) %>%
    tab_style(style = list(cell_fill(color = "#EAD1DC"), cell_text(color = "black")), locations = cells_body(columns = c(Y2026,Y2027,Y2028,Y2029,Y2030,Y2031,Y2032), rows = Player == "Minimum")) %>%
    tab_style(style = list(cell_fill(color = "#EAD1DC"), cell_text(color = "black")), locations = cells_body(columns = c(Y2026,Y2027,Y2028,Y2029,Y2030,Y2031,Y2032), rows = Player == "Bi-Annual")) %>%
    tab_style(style = list(cell_fill(color = "#EAD1DC"), cell_text(color = "black")), locations = cells_body(columns = c(Y2026,Y2027,Y2028,Y2029,Y2030,Y2031,Y2032), rows = Player == "Mid-Level")) %>%
    tab_style(style = list(cell_fill(color = "#EAD1DC"), cell_text(color = "black")), locations = cells_body(columns = c(Y2026,Y2027,Y2028,Y2029,Y2030,Y2031,Y2032), rows = Player == "Traded-Player")) %>%
    sub_missing(missing_text = "") %>%
    cols_label(
      Y2026 = "2025-26",
      Y2027 = "2026-27",
      Y2028 = "2027-28",
      Y2029 = "2028-29",
      Y2030 = "2029-30",
      Y2031 = "2030-31",
      Y2032 = "2031-32",
      BirdRights = "Bird Rights",
      Trade.Restriction = "Trade Restriction",
      Picture = "")
  
}
AllPicks <- function() {
  
  DraftPicksTotal <- DraftPicks %>%
    filter(Year != 2023) %>%
    filter(Year != 2024) %>%
    filter(Year != 2025) %>%
    arrange(Year, Round, OGTeam) %>%
    left_join(SBC, by = c('OGTeam' = 'City')) %>%
    mutate(OGTeam2 = Logo) %>%
    select(1:2,OGTeam2,4:6,OGTeam) %>%
    left_join(SBC, by = c('CurrentTeam' = 'City')) %>%
    mutate(CurrentTeam2 = Logo) %>%
    select(Year, Round, OGTeam, TeamTouched, CurrentTeam, Notes, OGTeam2, CurrentTeam2) %>%
    group_by(Year,Round)
  
  A <- gt(DraftPicksTotal) %>%
    gt_theme_espn() %>%
    cols_hide(columns = c(OGTeam2, CurrentTeam2)) %>%
    cols_label(OGTeam = "Original",
               TeamTouched = "Middle",
               CurrentTeam = "Current") %>%
    #text_transform(locations = cells_body(columns = OGTeam2),
    #               fn = function(x) {map_chr(x, function(path) {
    #                 if (file.exists(path)) {local_image(filename = path, height = 40)} 
    #                 else {paste("Missing:", basename(path))}})}) %>%
    #text_transform(locations = cells_body(columns = CurrentTeam2),
    #               fn = function(x) {map_chr(x, function(path) {
    #                 if (file.exists(path)) {local_image(filename = path, height = 40)} 
    #                 else {paste("Missing:", basename(path))}})}) %>%
    sub_missing(missing_text = "") %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", align = "center")), locations = cells_row_groups()) %>%
    tab_style(style = list(cell_fill(color = "white"), cell_text(color = "black")), locations = cells_body(columns = everything())) %>%
    cols_align(columns = everything(), align = "center") %>%
    tab_style(style = list(cell_text(size = 100)), locations = cells_body(columns = everything()))
  return(A)}
CapHits <- function(TeamName) {
  Players2 <- Players %>%
    filter(Team == TeamName) %>%
    arrange(Type,desc(Y2026))
  Players3 <- Players2 %>%
    mutate(Y2026 = ifelse(Type2026 %in% c("Restricted","Unrestricted"),NA,Y2026),
           Y2027 = ifelse(Type2027 %in% c("Restricted","Unrestricted"),NA,Y2027),
           Y2028 = ifelse(Type2028 %in% c("Restricted","Unrestricted"),NA,Y2028),
           Y2029 = ifelse(Type2029 %in% c("Restricted","Unrestricted"),NA,Y2029),
           Y2030 = ifelse(Type2030 %in% c("Restricted","Unrestricted"),NA,Y2030),
           Y2031 = ifelse(Type2031 %in% c("Restricted","Unrestricted"),NA,Y2031),
           Y2032 = ifelse(Type2032 %in% c("Restricted","Unrestricted"),NA,Y2032))
  Players4 <- Players2 %>%
    mutate(Y2026 = ifelse(Type2026 %in% c("Restricted","Unrestricted","Dead"),NA,Y2026),
           Y2027 = ifelse(Type2027 %in% c("Restricted","Unrestricted","Dead"),NA,Y2027),
           Y2028 = ifelse(Type2028 %in% c("Restricted","Unrestricted","Dead"),NA,Y2028),
           Y2029 = ifelse(Type2029 %in% c("Restricted","Unrestricted","Dead"),NA,Y2029),
           Y2030 = ifelse(Type2030 %in% c("Restricted","Unrestricted","Dead"),NA,Y2030),
           Y2031 = ifelse(Type2031 %in% c("Restricted","Unrestricted","Dead"),NA,Y2031),
           Y2032 = ifelse(Type2032 %in% c("Restricted","Unrestricted","Dead"),NA,Y2032))
  Exceptions2 <- Exceptions %>%
    filter(Team %in% c("All",TeamName))
  Team <- SBC %>%
    filter(City == TeamName)
  Logo <- Team$Logo
  
  Salary <- Players3 %>%
    group_by(Team) %>%
    summarize(Total = sum(Y2026, na.rm = T)) %>%
    select(Total) %>%
    pull()
  
  Min2026Hold <- Exceptions2$Y2026[1]*(12-sum(Players2$Y2026 > 0, na.rm = T))
  Exceptions2$Y2026[1] <- ifelse(Min2026Hold <= 0, 0, Min2026Hold)
  Min2027Hold <- Exceptions2$Y2027[1]*(12-sum(Players2$Y2027 > 0, na.rm = T))
  Exceptions2$Y2027[1] <- ifelse(Min2027Hold <= 0, 0, Min2027Hold)
  Min2028Hold <- Exceptions2$Y2028[1]*(12-sum(Players2$Y2028 > 0, na.rm = T))
  Exceptions2$Y2028[1] <- ifelse(Min2028Hold <= 0, 0, Min2028Hold)
  Min2029Hold <- Exceptions2$Y2029[1]*(12-sum(Players2$Y2029 > 0, na.rm = T))
  Exceptions2$Y2029[1] <- ifelse(Min2029Hold <= 0, 0, Min2029Hold)
  Min2030Hold <- Exceptions2$Y2030[1]*(12-sum(Players2$Y2030 > 0, na.rm = T))
  Exceptions2$Y2030[1] <- ifelse(Min2030Hold <= 0, 0, Min2030Hold)
  Min2031Hold <- Exceptions2$Y2031[1]*(12-sum(Players2$Y2031 > 0, na.rm = T))
  Exceptions2$Y2031[1] <- ifelse(Min2031Hold <= 0, 0, Min2031Hold)
  Min2032Hold <- Exceptions2$Y2032[1]*(12-sum(Players2$Y2032 > 0, na.rm = T))
  Exceptions2$Y2032[1] <- ifelse(Min2032Hold <= 0, 0, Min2032Hold)
  
  
  CapHit <- rbind(Players2,Exceptions2)
  CapHit <- CapHit %>%
    mutate(Y2026 = ifelse(Player == "Room Mid-Level", 0, Y2026)) %>%
    summarize(Y2026 = sum(Y2026, na.rm = T),
              Y2027 = sum(Y2027, na.rm = T),
              Y2028 = sum(Y2028, na.rm = T),
              Y2029 = sum(Y2029, na.rm = T),
              Y2030 = sum(Y2030, na.rm = T),
              Y2031 = sum(Y2031, na.rm = T),
              Y2032 = sum(Y2032, na.rm = T)) %>%
    mutate(Type = "Cap Hits",
           Team = "",
           Player = "Salary Cap Hit",
           BirdRights = "",
           Type2026 = "",
           Type2027 = "",
           Type2028 = "",
           Type2029 = "",
           Type2030 = "",
           Type2031 = "",
           Type2032 = "",
           Trade.Restriction = "",
           Type = as.character(Type),
           Team = as.character(Team),
           Player = as.character(Player),
           BirdRights = as.character(BirdRights),
           Type2026 = as.character(Type2026),
           Type2027 = as.character(Type2027),
           Type2028 = as.character(Type2028),
           Type2029 = as.character(Type2029),
           Type2030 = as.character(Type2030),
           Type2031 = as.character(Type2031),
           Type2032 = as.character(Type2032),
           Trade.Restriction = as.character(Trade.Restriction),
           Y2026 = as.numeric(Y2026),
           Y2027 = as.numeric(Y2027),
           Y2028 = as.numeric(Y2028),
           Y2029 = as.numeric(Y2029),
           Y2030 = as.numeric(Y2030),
           Y2031 = as.numeric(Y2031),
           Y2032 = as.numeric(Y2032))
  CapDiff <- rbind(Cap,CapHit)
  CapDiff <- CapDiff %>%
    filter(Player == "Salary Cap" | Player == "Salary Cap Hit")
  CapDiff <- rbind(CapDiff, rep(NA, ncol(CapDiff)))
  CapDiff$Type[3] <- "Cap Space"
  CapDiff$Y2026[3] <- CapDiff$Y2026[1]-CapDiff$Y2026[2]
  CapDiff$Y2027[3] <- CapDiff$Y2027[1]-CapDiff$Y2027[2]
  CapDiff$Y2028[3] <- CapDiff$Y2028[1]-CapDiff$Y2028[2]
  CapDiff$Y2029[3] <- CapDiff$Y2029[1]-CapDiff$Y2029[2]
  CapDiff$Y2030[3] <- CapDiff$Y2030[1]-CapDiff$Y2030[2]
  CapDiff$Y2031[3] <- CapDiff$Y2031[1]-CapDiff$Y2031[2]
  CapDiff$Y2032[3] <- CapDiff$Y2032[1]-CapDiff$Y2032[2]
  CapDiff$BirdRights <- ""
  CapDiff$Trade.Restriction <- ""
  CapDiff$Team <- ""
  CapDiff$Player <- "Cap Space2"
  CapDiff <- CapDiff %>%
    filter(Type == "Cap Space")
  
  Exceptions3 <- Exceptions %>%
    filter(Team %in% c("All",TeamName))
  Min2026Hold <- Exceptions3$Y2026[1]*(12-sum(Players4$Y2026 > 0, na.rm = T))
  Exceptions3$Y2026[1] <- ifelse(Min2026Hold <= 0, 0, Min2026Hold)
  Min2027Hold <- Exceptions3$Y2027[1]*(12-sum(Players4$Y2027 > 0, na.rm = T))
  Exceptions3$Y2027[1] <- ifelse(Min2027Hold <= 0, 0, Min2027Hold)
  Min2028Hold <- Exceptions3$Y2028[1]*(12-sum(Players4$Y2028 > 0, na.rm = T))
  Exceptions3$Y2028[1] <- ifelse(Min2028Hold <= 0, 0, Min2028Hold)
  Min2029Hold <- Exceptions3$Y2029[1]*(12-sum(Players4$Y2029 > 0, na.rm = T))
  Exceptions3$Y2029[1] <- ifelse(Min2029Hold <= 0, 0, Min2029Hold)
  Min2030Hold <- Exceptions3$Y2030[1]*(12-sum(Players4$Y2030 > 0, na.rm = T))
  Exceptions3$Y2030[1] <- ifelse(Min2030Hold <= 0, 0, Min2030Hold)
  Min2031Hold <- Exceptions3$Y2031[1]*(12-sum(Players4$Y2031 > 0, na.rm = T))
  Exceptions3$Y2031[1] <- ifelse(Min2031Hold <= 0, 0, Min2031Hold)
  Min2032Hold <- Exceptions3$Y2032[1]*(12-sum(Players4$Y2032 > 0, na.rm = T))
  Exceptions3$Y2032[1] <- ifelse(Min2032Hold <= 0, 0, Min2032Hold)
  
  Exceptions3 <- Exceptions3 %>%
    filter(Player == "Minimum")
  ApronHit <- rbind(Players3,Exceptions3)
  ApronHit <- ApronHit %>%
    summarize(Y2026 = sum(Y2026, na.rm = T),
              Y2027 = sum(Y2027, na.rm = T),
              Y2028 = sum(Y2028, na.rm = T),
              Y2029 = sum(Y2029, na.rm = T),
              Y2030 = sum(Y2030, na.rm = T),
              Y2031 = sum(Y2031, na.rm = T),
              Y2032 = sum(Y2032, na.rm = T)) %>%
    mutate(Type = "Cap Hits",
           Team = "",
           Player = "Tax Hit",
           BirdRights = "",
           Type2026 = "",
           Type2027 = "",
           Type2028 = "",
           Type2029 = "",
           Type2030 = "",
           Type2031 = "",
           Type2032 = "",
           Trade.Restriction = "",
           Type = as.character(Type),
           Team = as.character(Team),
           Player = as.character(Player),
           BirdRights = as.character(BirdRights),
           Type2026 = as.character(Type2026),
           Type2027 = as.character(Type2027),
           Type2028 = as.character(Type2028),
           Type2029 = as.character(Type2029),
           Type2030 = as.character(Type2030),
           Type2031 = as.character(Type2031),
           Type2032 = as.character(Type2032),
           Trade.Restriction = as.character(Trade.Restriction),
           Y2026 = as.numeric(Y2026),
           Y2027 = as.numeric(Y2027),
           Y2028 = as.numeric(Y2028),
           Y2029 = as.numeric(Y2029),
           Y2030 = as.numeric(Y2030),
           Y2031 = as.numeric(Y2031),
           Y2032 = as.numeric(Y2032))
  
  TaxDiff <- rbind(Cap,ApronHit)
  TaxDiff <- TaxDiff %>%
    filter(Player == "Luxury Tax" | Player == "Tax Hit")
  TaxDiff <- rbind(TaxDiff, rep(NA, ncol(TaxDiff)))
  TaxDiff$Type[3] <- "Cap Space"
  TaxDiff$Y2026[3] <- TaxDiff$Y2026[1]-TaxDiff$Y2026[2]
  TaxDiff$Y2027[3] <- TaxDiff$Y2027[1]-TaxDiff$Y2027[2]
  TaxDiff$Y2028[3] <- TaxDiff$Y2028[1]-TaxDiff$Y2028[2]
  TaxDiff$Y2029[3] <- TaxDiff$Y2029[1]-TaxDiff$Y2029[2]
  TaxDiff$Y2030[3] <- TaxDiff$Y2030[1]-TaxDiff$Y2030[2]
  TaxDiff$Y2031[3] <- TaxDiff$Y2031[1]-TaxDiff$Y2031[2]
  TaxDiff$Y2032[3] <- TaxDiff$Y2032[1]-TaxDiff$Y2032[2]
  TaxDiff$BirdRights <- ""
  TaxDiff$Trade.Restriction <- ""
  TaxDiff$Team <- ""
  TaxDiff$Player <- "Tax Space"
  TaxDiff <- TaxDiff %>%
    filter(Type == "Cap Space")
  
  Apron1Diff <- rbind(Cap,ApronHit)
  Apron1Diff <- Apron1Diff %>%
    filter(Player == "Apron #1" | Player == "Tax Hit")
  Apron1Diff <- rbind(Apron1Diff, rep(NA, ncol(Apron1Diff)))
  Apron1Diff$Type[3] <- "Cap Space"
  Apron1Diff$Y2026[3] <- Apron1Diff$Y2026[1]-Apron1Diff$Y2026[2]
  Apron1Diff$Y2027[3] <- Apron1Diff$Y2027[1]-Apron1Diff$Y2027[2]
  Apron1Diff$Y2028[3] <- Apron1Diff$Y2028[1]-Apron1Diff$Y2028[2]
  Apron1Diff$Y2029[3] <- Apron1Diff$Y2029[1]-Apron1Diff$Y2029[2]
  Apron1Diff$Y2030[3] <- Apron1Diff$Y2030[1]-Apron1Diff$Y2030[2]
  Apron1Diff$Y2031[3] <- Apron1Diff$Y2031[1]-Apron1Diff$Y2031[2]
  Apron1Diff$Y2032[3] <- Apron1Diff$Y2032[1]-Apron1Diff$Y2032[2]
  Apron1Diff$BirdRights <- ""
  Apron1Diff$Trade.Restriction <- ""
  Apron1Diff$Team <- ""
  Apron1Diff$Player <- "Apron 1 Space"
  Apron1Diff <- Apron1Diff %>%
    filter(Type == "Cap Space")
  
  
  Apron2Diff <- rbind(Cap,ApronHit)
  Apron2Diff <- Apron2Diff %>%
    filter(Player == "Apron #2" | Player == "Tax Hit")
  Apron2Diff <- rbind(Apron2Diff, rep(NA, ncol(Apron2Diff)))
  Apron2Diff$Type[3] <- "Cap Space"
  Apron2Diff$Y2026[3] <- Apron2Diff$Y2026[1]-Apron2Diff$Y2026[2]
  Apron2Diff$Y2027[3] <- Apron2Diff$Y2027[1]-Apron2Diff$Y2027[2]
  Apron2Diff$Y2028[3] <- Apron2Diff$Y2028[1]-Apron2Diff$Y2028[2]
  Apron2Diff$Y2029[3] <- Apron2Diff$Y2029[1]-Apron2Diff$Y2029[2]
  Apron2Diff$Y2030[3] <- Apron2Diff$Y2030[1]-Apron2Diff$Y2030[2]
  Apron2Diff$Y2031[3] <- Apron2Diff$Y2031[1]-Apron2Diff$Y2031[2]
  Apron2Diff$Y2032[3] <- Apron2Diff$Y2032[1]-Apron2Diff$Y2032[2]
  Apron2Diff$BirdRights <- ""
  Apron2Diff$Trade.Restriction <- ""
  Apron2Diff$Team <- ""
  Apron2Diff$Player <- "Apron 2 Space"
  Apron2Diff <- Apron2Diff %>%
    filter(Type == "Cap Space")
  Table <- rbind(CapHit,ApronHit,CapDiff,TaxDiff,Apron1Diff,Apron2Diff) %>%
    select(Y2026,Player) %>%
    pivot_wider(names_from = Player, values_from = Y2026) %>%
    mutate(Team = TeamName) %>%
    mutate(Salary = Salary) %>%
    select(7:8, 1:6)
  colnames(Table)[3] <- "SalaryCapHit"
  colnames(Table)[4] <- "TaxHit"
  colnames(Table)[5] <- "CapSpace"
  colnames(Table)[6] <- "TaxSpace"
  colnames(Table)[7] <- "Apron1"
  colnames(Table)[8] <- "Apron2"
  return(Table)}
TaxAmountCalc <- function(Number,Repeater) {
  TaxNumber <- rep(Number,100)
  Repeater2 <- rep(Repeater,100)
  Slot <- 1:100
  Group <- rep(1,100)
  Penalty1 <- c(1.0,0.25,2.25,1.25,rep(0.5,96))
  Penalty2 <- c(3.0,0.25,2.25,1.25,rep(0.5,96))
  TaxNumber <- data.frame(Group,Slot,TaxNumber,Repeater,Penalty1,Penalty2)
  TaxNumber <- TaxNumber %>%
    mutate(TaxNumber = TaxNumber-(5685000*(Slot-1))) %>%
    filter(TaxNumber >= 0) %>%
    mutate(Penalty3 = ifelse(Repeater == TRUE, Penalty2, Penalty1),
           TaxCost = TaxNumber*Penalty3) %>%
    group_by(Group) %>%
    summarize(TaxCost = sum(TaxCost)) %>%
    select(TaxCost) %>%
    pull()
  TaxNumber <- ifelse(length(TaxNumber) == 0, 0, TaxNumber)
  return(TaxNumber)}
CapSideBySide <- function(TeamName) {
  Players2 <- Players %>%
    filter(Team == TeamName) %>%
    arrange(Type,desc(Y2026))
  Players3 <- Players2 %>%
    mutate(Y2026 = ifelse(Type2026 %in% c("Restricted","Unrestricted"),NA,Y2026),
           Y2027 = ifelse(Type2027 %in% c("Restricted","Unrestricted"),NA,Y2027),
           Y2028 = ifelse(Type2028 %in% c("Restricted","Unrestricted"),NA,Y2028),
           Y2029 = ifelse(Type2029 %in% c("Restricted","Unrestricted"),NA,Y2029),
           Y2030 = ifelse(Type2030 %in% c("Restricted","Unrestricted"),NA,Y2030),
           Y2031 = ifelse(Type2031 %in% c("Restricted","Unrestricted"),NA,Y2031),
           Y2032 = ifelse(Type2032 %in% c("Restricted","Unrestricted"),NA,Y2032))
  Players4 <- Players2 %>%
    mutate(Y2026 = ifelse(Type2026 %in% c("Restricted","Unrestricted","Dead"),NA,Y2026),
           Y2027 = ifelse(Type2027 %in% c("Restricted","Unrestricted","Dead"),NA,Y2027),
           Y2028 = ifelse(Type2028 %in% c("Restricted","Unrestricted","Dead"),NA,Y2028),
           Y2029 = ifelse(Type2029 %in% c("Restricted","Unrestricted","Dead"),NA,Y2029),
           Y2030 = ifelse(Type2030 %in% c("Restricted","Unrestricted","Dead"),NA,Y2030),
           Y2031 = ifelse(Type2031 %in% c("Restricted","Unrestricted","Dead"),NA,Y2031),
           Y2032 = ifelse(Type2032 %in% c("Restricted","Unrestricted","Dead"),NA,Y2032))
  Exceptions2 <- Exceptions %>%
    filter(Team %in% c("All",TeamName))
  Team <- SBC %>%
    filter(City == TeamName)
  Logo <- Team$Logo
  
  
  Min2026Hold <- Exceptions2$Y2026[1]*(12-sum(Players2$Y2026 > 0, na.rm = T))
  Exceptions2$Y2026[1] <- ifelse(Min2026Hold <= 0, 0, Min2026Hold)
  Min2027Hold <- Exceptions2$Y2027[1]*(12-sum(Players2$Y2027 > 0, na.rm = T))
  Exceptions2$Y2027[1] <- ifelse(Min2027Hold <= 0, 0, Min2027Hold)
  Min2028Hold <- Exceptions2$Y2028[1]*(12-sum(Players2$Y2028 > 0, na.rm = T))
  Exceptions2$Y2028[1] <- ifelse(Min2028Hold <= 0, 0, Min2028Hold)
  Min2029Hold <- Exceptions2$Y2029[1]*(12-sum(Players2$Y2029 > 0, na.rm = T))
  Exceptions2$Y2029[1] <- ifelse(Min2029Hold <= 0, 0, Min2029Hold)
  Min2030Hold <- Exceptions2$Y2030[1]*(12-sum(Players2$Y2030 > 0, na.rm = T))
  Exceptions2$Y2030[1] <- ifelse(Min2030Hold <= 0, 0, Min2030Hold)
  Min2031Hold <- Exceptions2$Y2031[1]*(12-sum(Players2$Y2031 > 0, na.rm = T))
  Exceptions2$Y2031[1] <- ifelse(Min2031Hold <= 0, 0, Min2031Hold)
  Min2032Hold <- Exceptions2$Y2032[1]*(12-sum(Players2$Y2032 > 0, na.rm = T))
  Exceptions2$Y2032[1] <- ifelse(Min2032Hold <= 0, 0, Min2032Hold)
  
  
  CapHit <- rbind(Players2,Exceptions2)
  CapHit <- CapHit %>%
    mutate(Y2026 = ifelse(Player == "Room Mid-Level", 0, Y2026)) %>%
    summarize(Y2026 = sum(Y2026, na.rm = T),
              Y2027 = sum(Y2027, na.rm = T),
              Y2028 = sum(Y2028, na.rm = T),
              Y2029 = sum(Y2029, na.rm = T),
              Y2030 = sum(Y2030, na.rm = T),
              Y2031 = sum(Y2031, na.rm = T),
              Y2032 = sum(Y2032, na.rm = T)) %>%
    mutate(Type = "Cap Hits",
           Team = "",
           Player = "Salary Cap Hit",
           BirdRights = "",
           Type2026 = "",
           Type2027 = "",
           Type2028 = "",
           Type2029 = "",
           Type2030 = "",
           Type2031 = "",
           Type2032 = "",
           Trade.Restriction = "",
           Type = as.character(Type),
           Team = as.character(Team),
           Player = as.character(Player),
           BirdRights = as.character(BirdRights),
           Type2026 = as.character(Type2026),
           Type2027 = as.character(Type2027),
           Type2028 = as.character(Type2028),
           Type2029 = as.character(Type2029),
           Type2030 = as.character(Type2030),
           Type2031 = as.character(Type2031),
           Type2032 = as.character(Type2032),
           Trade.Restriction = as.character(Trade.Restriction),
           Y2026 = as.numeric(Y2026),
           Y2027 = as.numeric(Y2027),
           Y2028 = as.numeric(Y2028),
           Y2029 = as.numeric(Y2029),
           Y2030 = as.numeric(Y2030),
           Y2031 = as.numeric(Y2031),
           Y2032 = as.numeric(Y2032))
  CapDiff <- rbind(Cap,CapHit)
  CapDiff <- CapDiff %>%
    filter(Player == "Salary Cap" | Player == "Salary Cap Hit")
  CapDiff <- rbind(CapDiff, rep(NA, ncol(CapDiff)))
  CapDiff$Type[3] <- "Cap Space"
  CapDiff$Y2026[3] <- CapDiff$Y2026[1]-CapDiff$Y2026[2]
  CapDiff$Y2027[3] <- CapDiff$Y2027[1]-CapDiff$Y2027[2]
  CapDiff$Y2028[3] <- CapDiff$Y2028[1]-CapDiff$Y2028[2]
  CapDiff$Y2029[3] <- CapDiff$Y2029[1]-CapDiff$Y2029[2]
  CapDiff$Y2030[3] <- CapDiff$Y2030[1]-CapDiff$Y2030[2]
  CapDiff$Y2031[3] <- CapDiff$Y2031[1]-CapDiff$Y2031[2]
  CapDiff$Y2032[3] <- CapDiff$Y2032[1]-CapDiff$Y2032[2]
  CapDiff$BirdRights <- ""
  CapDiff$Trade.Restriction <- ""
  CapDiff$Team <- ""
  CapDiff$Player <- "Cap Space"
  CapDiff <- CapDiff %>%
    filter(Type == "Cap Space")
  
  Exceptions3 <- Exceptions %>%
    filter(Team %in% c("All",TeamName))
  Min2026Hold <- Exceptions3$Y2026[1]*(12-sum(Players4$Y2026 > 0, na.rm = T))
  Exceptions3$Y2026[1] <- ifelse(Min2026Hold <= 0, 0, Min2026Hold)
  Min2027Hold <- Exceptions3$Y2027[1]*(12-sum(Players4$Y2027 > 0, na.rm = T))
  Exceptions3$Y2027[1] <- ifelse(Min2027Hold <= 0, 0, Min2027Hold)
  Min2028Hold <- Exceptions3$Y2028[1]*(12-sum(Players4$Y2028 > 0, na.rm = T))
  Exceptions3$Y2028[1] <- ifelse(Min2028Hold <= 0, 0, Min2028Hold)
  Min2029Hold <- Exceptions3$Y2029[1]*(12-sum(Players4$Y2029 > 0, na.rm = T))
  Exceptions3$Y2029[1] <- ifelse(Min2029Hold <= 0, 0, Min2029Hold)
  Min2030Hold <- Exceptions3$Y2030[1]*(12-sum(Players4$Y2030 > 0, na.rm = T))
  Exceptions3$Y2030[1] <- ifelse(Min2030Hold <= 0, 0, Min2030Hold)
  Min2031Hold <- Exceptions3$Y2031[1]*(12-sum(Players4$Y2031 > 0, na.rm = T))
  Exceptions3$Y2031[1] <- ifelse(Min2031Hold <= 0, 0, Min2031Hold)
  Min2032Hold <- Exceptions3$Y2032[1]*(12-sum(Players4$Y2032 > 0, na.rm = T))
  Exceptions3$Y2032[1] <- ifelse(Min2032Hold <= 0, 0, Min2032Hold)
  
  Exceptions3 <- Exceptions3 %>%
    filter(Player == "Minimum")
  ApronHit <- rbind(Players3,Exceptions3)
  ApronHit <- ApronHit %>%
    summarize(Y2026 = sum(Y2026, na.rm = T),
              Y2027 = sum(Y2027, na.rm = T),
              Y2028 = sum(Y2028, na.rm = T),
              Y2029 = sum(Y2029, na.rm = T),
              Y2030 = sum(Y2030, na.rm = T),
              Y2031 = sum(Y2031, na.rm = T),
              Y2032 = sum(Y2032, na.rm = T)) %>%
    mutate(Type = "Cap Hits",
           Team = "",
           Player = "Tax Hit",
           BirdRights = "",
           Type2026 = "",
           Type2027 = "",
           Type2028 = "",
           Type2029 = "",
           Type2030 = "",
           Type2031 = "",
           Type2032 = "",
           Trade.Restriction = "",
           Type = as.character(Type),
           Team = as.character(Team),
           Player = as.character(Player),
           BirdRights = as.character(BirdRights),
           Type2026 = as.character(Type2026),
           Type2027 = as.character(Type2027),
           Type2028 = as.character(Type2028),
           Type2029 = as.character(Type2029),
           Type2030 = as.character(Type2030),
           Type2031 = as.character(Type2031),
           Type2032 = as.character(Type2032),
           Trade.Restriction = as.character(Trade.Restriction),
           Y2026 = as.numeric(Y2026),
           Y2027 = as.numeric(Y2027),
           Y2028 = as.numeric(Y2028),
           Y2029 = as.numeric(Y2029),
           Y2030 = as.numeric(Y2030),
           Y2031 = as.numeric(Y2031),
           Y2032 = as.numeric(Y2032))
  
  TaxDiff <- rbind(Cap,ApronHit)
  TaxDiff <- TaxDiff %>%
    filter(Player == "Luxury Tax" | Player == "Tax Hit")
  TaxDiff <- rbind(TaxDiff, rep(NA, ncol(TaxDiff)))
  TaxDiff$Type[3] <- "Cap Space"
  TaxDiff$Y2026[3] <- TaxDiff$Y2026[1]-TaxDiff$Y2026[2]
  TaxDiff$Y2027[3] <- TaxDiff$Y2027[1]-TaxDiff$Y2027[2]
  TaxDiff$Y2028[3] <- TaxDiff$Y2028[1]-TaxDiff$Y2028[2]
  TaxDiff$Y2029[3] <- TaxDiff$Y2029[1]-TaxDiff$Y2029[2]
  TaxDiff$Y2030[3] <- TaxDiff$Y2030[1]-TaxDiff$Y2030[2]
  TaxDiff$Y2031[3] <- TaxDiff$Y2031[1]-TaxDiff$Y2031[2]
  TaxDiff$Y2032[3] <- TaxDiff$Y2032[1]-TaxDiff$Y2032[2]
  TaxDiff$BirdRights <- ""
  TaxDiff$Trade.Restriction <- ""
  TaxDiff$Team <- ""
  TaxDiff$Player <- "Tax Space"
  TaxDiff <- TaxDiff %>%
    filter(Type == "Cap Space")
  
  Apron1Diff <- rbind(Cap,ApronHit)
  Apron1Diff <- Apron1Diff %>%
    filter(Player == "Apron #1" | Player == "Tax Hit")
  Apron1Diff <- rbind(Apron1Diff, rep(NA, ncol(Apron1Diff)))
  Apron1Diff$Type[3] <- "Cap Space"
  Apron1Diff$Y2026[3] <- Apron1Diff$Y2026[1]-Apron1Diff$Y2026[2]
  Apron1Diff$Y2027[3] <- Apron1Diff$Y2027[1]-Apron1Diff$Y2027[2]
  Apron1Diff$Y2028[3] <- Apron1Diff$Y2028[1]-Apron1Diff$Y2028[2]
  Apron1Diff$Y2029[3] <- Apron1Diff$Y2029[1]-Apron1Diff$Y2029[2]
  Apron1Diff$Y2030[3] <- Apron1Diff$Y2030[1]-Apron1Diff$Y2030[2]
  Apron1Diff$Y2031[3] <- Apron1Diff$Y2031[1]-Apron1Diff$Y2031[2]
  Apron1Diff$Y2032[3] <- Apron1Diff$Y2032[1]-Apron1Diff$Y2032[2]
  Apron1Diff$BirdRights <- ""
  Apron1Diff$Trade.Restriction <- ""
  Apron1Diff$Team <- ""
  Apron1Diff$Player <- "Apron 1 Space"
  Apron1Diff <- Apron1Diff %>%
    filter(Type == "Cap Space")
  
  
  Apron2Diff <- rbind(Cap,ApronHit)
  Apron2Diff <- Apron2Diff %>%
    filter(Player == "Apron #2" | Player == "Tax Hit")
  Apron2Diff <- rbind(Apron2Diff, rep(NA, ncol(Apron2Diff)))
  Apron2Diff$Type[3] <- "Cap Space"
  Apron2Diff$Y2026[3] <- Apron2Diff$Y2026[1]-Apron2Diff$Y2026[2]
  Apron2Diff$Y2027[3] <- Apron2Diff$Y2027[1]-Apron2Diff$Y2027[2]
  Apron2Diff$Y2028[3] <- Apron2Diff$Y2028[1]-Apron2Diff$Y2028[2]
  Apron2Diff$Y2029[3] <- Apron2Diff$Y2029[1]-Apron2Diff$Y2029[2]
  Apron2Diff$Y2030[3] <- Apron2Diff$Y2030[1]-Apron2Diff$Y2030[2]
  Apron2Diff$Y2031[3] <- Apron2Diff$Y2031[1]-Apron2Diff$Y2031[2]
  Apron2Diff$Y2032[3] <- Apron2Diff$Y2032[1]-Apron2Diff$Y2032[2]
  Apron2Diff$BirdRights <- ""
  Apron2Diff$Trade.Restriction <- ""
  Apron2Diff$Team <- ""
  Apron2Diff$Player <- "Apron 2 Space"
  Apron2Diff <- Apron2Diff %>%
    filter(Type == "Cap Space")
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  Table <- rbind(Cap,Players2,Exceptions2,CapHit,ApronHit,CapDiff,TaxDiff,Apron1Diff,Apron2Diff)
  Table <- Table %>%
    filter(is.na(Player) == F) %>%
    left_join(Pictures, by = c('Player')) %>%
    select(20,1:19) %>%
    mutate(Picture = ifelse(is.na(Picture) == T, Logo, Picture)) %>%
    select(Picture, Type, Team, Player, Y2026, BirdRights, Type2026, Trade.Restriction) %>%
    group_by(Type) 
  return(Table)}
SideBySide <- function(TeamName1,TeamName2) {
  TeamAInfo <- SBC %>%
    filter(City == TeamName1)
  TeamBInfo <- SBC %>%
    filter(City == TeamName2)
  TeamA <- CapSideBySide(TeamName1)
  TeamB <- CapSideBySide(TeamName2)
  TeamA <- TeamA %>%
    group_by(Type) %>%
    mutate(Number = 1:n(),
           Number = paste0(Type,Number))
  TeamB <- TeamB %>%
    group_by(Type) %>%
    mutate(Number = 1:n(),
           Number = paste0(Type,Number)) %>%
    rename(Picture2 = Picture,
           Type2 = Type, 
           Team2 = Team,
           Player2 = Player,
           Y20262 = Y2026,
           BirdRights2 = BirdRights,
           Type20262 = Type2026,
           Trade.Restriction2 = Trade.Restriction)
  Total <- full_join(TeamA, TeamB, by = "Number")
  Total <- Total %>%
    ungroup() %>%
    select(-Type, -Type2, -Team, -Team2) %>%
    mutate(Number = gsub("\\d+$", "", Number)) %>%
    mutate(Order = case_when(
      Number == "Cap Amounts" ~ 6,
      Number == "Active Players" ~ 5,
      Number == "Free Agent" ~ 4,
      Number == "Non-Active Players" ~ 3,
      Number == "Exceptions" ~ 2,
      Number == "Cap Hits" ~ 1,
      Number == "Cap Space" ~ 0,
      TRUE ~ -1)) %>%
    group_by(Number) %>%
    arrange(-Order) %>%
    select(-Order)
  
  gt(Total) %>%
    gt_theme_espn() %>%
    tab_style(style = list(cell_fill(color = TeamBInfo$Color1), cell_text(color = TeamBInfo$Color3)), locations = cells_body(columns = c(Picture2,Player2,Y20262,BirdRights2,Trade.Restriction2))) %>%
    tab_style(style = list(cell_fill(color = TeamAInfo$Color1), cell_text(color = TeamAInfo$Color3)), locations = cells_body(columns = c(Picture,Player,Y2026,BirdRights,Trade.Restriction))) %>%
    cols_hide(columns = c(Type2026,Type20262,Picture,Picture2)) %>%
    #text_transform(locations = cells_body(columns = Picture),
    #               fn = function(x) {map_chr(x, function(path) {
    #                 if (file.exists(path)) {local_image(filename = path, height = 40)} 
    #                 else {paste("Missing:", basename(path))}})}) %>%
    #text_transform(locations = cells_body(columns = Picture2),
    #               fn = function(x) {map_chr(x, function(path) {
    #                 if (file.exists(path)) {local_image(filename = path, height = 40)} 
    #                 else {paste("Missing:", basename(path))}})}) %>%
    cols_align(columns = everything(), align = "center") %>%
    cols_align(columns = Player, align = "left") %>%
    cols_align(columns = Player2, align = "left") %>%
    fmt_currency(columns = c(Y2026,Y20262), currency = "USD", decimals = 0) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD"), cell_text(color = "black")), locations = cells_body(columns = Y2026, rows = Type2026 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC"), cell_text(color = "black")), locations = cells_body(columns = Y2026, rows = Type2026 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3"), cell_text(color = "black")), locations = cells_body(columns = Y2026, rows = Type2026 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9"), cell_text(color = "black")), locations = cells_body(columns = Y2026, rows = Type2026 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9"), cell_text(color = "black")), locations = cells_body(columns = Y2026, rows = Type2026 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF"), cell_text(color = "black")), locations = cells_body(columns = Y2026, rows = Type2026 == "Restricted")) %>%
    tab_style(style = list(cell_fill(color = "#FCE5CD"), cell_text(color = "black")), locations = cells_body(columns = Y20262, rows = Type20262 == "Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#F4CCCC"), cell_text(color = "black")), locations = cells_body(columns = Y20262, rows = Type20262 == "Non-Guaranteed")) %>%
    tab_style(style = list(cell_fill(color = "#CFE2F3"), cell_text(color = "black")), locations = cells_body(columns = Y20262, rows = Type20262 == "Team")) %>%
    tab_style(style = list(cell_fill(color = "#D9D9D9"), cell_text(color = "black")), locations = cells_body(columns = Y20262, rows = Type20262 == "Dead")) %>%
    tab_style(style = list(cell_fill(color = "#D9D2E9"), cell_text(color = "black")), locations = cells_body(columns = Y20262, rows = Type20262 == "Unrestricted")) %>%
    tab_style(style = list(cell_fill(color = "#CFFFFF"), cell_text(color = "black")), locations = cells_body(columns = Y20262, rows = Type20262 == "Restricted")) %>%
    sub_missing(missing_text = "") %>%
    tab_style(style = list(cell_fill(color = "Black"), cell_text(color = "White", align = "center")), locations = cells_row_groups()) %>%
    tab_spanner(label = md(TeamAInfo$Team), columns = c(Picture, Player, Y2026, BirdRights, Trade.Restriction)) %>%
    tab_spanner(label = md(TeamBInfo$Team), columns = c(Picture2, Player2, Y20262, BirdRights2, Trade.Restriction2)) %>%
    cols_label(
      Y2026 = "2025-26",
      BirdRights = "Bird Rights",
      Trade.Restriction = "Trade Restriction",
      Picture = "",
      Y20262 = "2025-26",
      BirdRights2 = "Bird Rights",
      Trade.Restriction2 = "Trade Restriction",
      Picture2 = "",
      Player2 = "Player")
    
    
}
GetFreeAgents <- function() {

FA %>%
  group_by(Tier) %>%
  gt() %>%
  gt_theme_espn() %>%
  tab_header(title = md(
    paste0(
      "<div style='text-align: center; font-weight: bold; font-size: 1.1m;'>",
      "2025 Free Agency",
      "</div>"))) %>%
  #text_transform(locations = cells_body(columns = Picture),
  #               fn = function(x) {map_chr(x, function(path) {
  #                 if (file.exists(path)) {local_image(filename = path, height = 40)} 
  #                 else {paste("Missing:", basename(path))}})}) %>%
  cols_align(columns = everything(), align = "center") %>%
  cols_align(columns = Team, align = "right") %>%
  cols_align(columns = Player, align = "left") %>%
  fmt_currency(columns = c(CapHold,MaxBid), currency = "USD", decimals = 0) %>%
  tab_style(style = list(cell_fill(color = "#D9D2E9")), locations = cells_body(columns = CapHold, rows = Type2026 == "Unrestricted")) %>%
  tab_style(style = list(cell_fill(color = "#CFFFFF")), locations = cells_body(columns = CapHold, rows = Type2026 == "Restricted")) %>%
  cols_label(BirdRights = "Bird Rights",
             CapHold = "Cap Hold",
             SignDate = "Sign Date") %>%
  cols_hide(columns = c(Type2026, Score)) %>%
  tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", align = "center")), locations = cells_row_groups()) %>%
  sub_missing(missing_text = "")
  
  
  
  
  }
OverallCapSheet <- function() {
  
  Players2 <- Players %>%
    filter(Type2026 %in% c("Guaranteed", "Non-Guaranteed")) %>%
    group_by(Type, Team) %>%
    summarize(Total = n()) %>%
    ungroup() %>%
    pivot_wider(names_from = Type, values_from = Total, values_fill = 0)
  
  Value2 <- Players %>%
    filter(Type2026 %in% c("Guaranteed", "Non-Guaranteed", "Dead")) %>%
    group_by(Team) %>%
    summarize(Salary = sum(Y2026)) %>%
    ungroup() %>%
    mutate(TaxAmount = (Salary-187895000),
           Tax2026 = ifelse(TaxAmount > 0, 1, 0),
           TaxAmount = ifelse(TaxAmount > 0, TaxAmount, NA))
  
  TotalCapBase2 <- TotalCapBase %>%
    left_join(Value2, by = 'Team') %>%
    select(-TaxAmount, -Salary) %>%
    mutate(TaxRepeater = Tax2022+Tax2023+Tax2024+Tax2025+Tax2026,
           TaxRepeater = ifelse(TaxRepeater >= 4, T, F)) %>%
    pivot_longer(cols = starts_with("Tax20"), names_to = "Year", values_to = "TaxValue") %>%
    group_by(across(-c(Year, TaxValue))) %>%
    summarise(Tax = list(TaxValue), .groups = "drop")
  
  
  Total <- TotalCapBase2 %>%
    left_join(Players2, by = c("Team")) %>%
    left_join(Value2, by = c('Team')) %>%
    mutate(FeesOwed = Salary/3000000,
           FeesOwed = ifelse(FeesOwed <= 154647000*0.9/3000000, 46.39, FeesOwed),
           FeesOwed = FeesOwed+3,
           FeesOwed = FeesOwed,
           FeesOwed = FeesOwed*Rate,
           FeesOwed2 = FeesOwed*(1-Rate),
           `Non-Active Players` = paste0("(",`Non-Active Players`,")")) %>%
    rowwise() %>%
    mutate(TaxesOwed = TaxAmountCalc(TaxAmount, TaxRepeater),
           TaxesOwed = TaxesOwed/3000000,
           TaxesOwed = TaxesOwed*Rate)
  
  
  Total$TaxDist <- ifelse(Total$Tax2026 == 1, 0, Total$Rate / sum(Total$Rate[Total$Tax2026 == 0]))
           

  
  TotalTax <- sum(Total$TaxesOwed)
  TotalTax <- TotalTax-229.95-sum(Total$FeesOwed2)
  TotalTax <- TotalTax/2
  
  Payouts <- sum(Total$FeesOwed)+sum(Total$FeesOwed2)-90

  
  CharityAmount <- round(TotalTax,2)
  Champ <- Payouts*12/24
  RunnerUp <- Payouts*4/24
  ConfFinal <- Payouts*2/24
  ConfSemi <- Payouts*1/24

  Total$TaxesOwed <- ifelse(Total$TaxesOwed == 0, -Total$TaxDist*TotalTax, Total$TaxesOwed)
  
  Total <- Total %>%
    mutate(TaxesOwed = ifelse(TaxesOwed == 0, -TaxDist, TaxesOwed),
           TaxesOwed = round(TaxesOwed,2),
           NetBalance = FeesOwed+TaxesOwed-MoneyPaid,
           TaxesOwed = paste0("$",TaxesOwed)) %>%
    mutate(DistanceFromCap = case_when(
                               HardCap == "Second Apron" ~ 207824000,
                               HardCap == "First Apron" ~ 195945000,
                               TRUE ~ NA_real_),
           DistanceFromCap = DistanceFromCap-Salary) %>%
    mutate(Tier = factor(Tier, levels = c("Second Apron", "First Apron", "Over Cap", "Cap Space"))) %>%
    arrange(Tier, -Salary) %>%
    group_by(Tier) %>%
    select(Team, `Active Players`, Salary, TaxAmount, DistanceFromCap, Tax, FeesOwed, TaxesOwed, NetBalance, HardCap, MoneyPaid, TaxRepeater, `Non-Active Players`, Tier)
  
  A <- gt(Total) %>%
    gt_theme_espn() %>%
    cols_hide(columns = c(HardCap, MoneyPaid, TaxRepeater)) %>%
    gt_merge_stack(col1 = `Active Players`, col2 = `Non-Active Players`) %>%
    gt_merge_stack(col1 = FeesOwed, col2 = TaxesOwed) %>%
    fmt_currency(columns = c(Salary, TaxAmount, DistanceFromCap), decimals = 0) %>%
    fmt_currency(columns = c(TaxesOwed, FeesOwed, NetBalance), decimals = 2) %>%
    gt_plt_winloss(column = Tax, palette = c("black", "gray", "gray"), type = "pill") %>%
    cols_align(align = "center", columns = everything()) %>%
    cols_align(align = "right", columns = Team) %>%
    sub_missing(everything(), missing_text = "") %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = `Active Players`, rows = `Active Players` < 12 | `Active Players` > 17)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = NetBalance, rows = NetBalance > 0)) %>%
    tab_style(style = list(cell_fill(color = "#309143"), cell_text(color = "white")), locations = cells_body(columns = NetBalance, rows = NetBalance <= 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = DistanceFromCap, rows = DistanceFromCap < 0)) %>%
    tab_style(style = list(cell_fill(color = "#B61A1C"), cell_text(color = "white")), locations = cells_body(columns = Tax, rows = TaxRepeater == T)) %>%
    tab_style(style = list(cell_fill(color = "black"), cell_text(color = "white", align = "center")), locations = cells_row_groups()) %>%
    cols_label(Team = "",
               `Active Players` = "Players",
               TaxAmount = "Taxable",
               DistanceFromCap = "Hard Cap",
               Tax = "Tax History",
               FeesOwed = "Owed",
               NetBalance = "Balance") %>%
    cols_align(align = "center", columns = Tax) %>%
    tab_source_note(paste0("PLAYOFF PAYOUT BREAKDOWN: ")) %>%
    tab_source_note(paste0("Champion: $", formatC(Champ, format = "f", digits = 2), " (plus $", formatC(CharityAmount, format = "f", digits = 2), " to charity of choosing);")) %>%
    tab_source_note(paste0("Runner-Up: $", formatC(RunnerUp, format = "f", digits = 2), "; ")) %>%
    tab_source_note(paste0("Conference Finalists (2): $", formatC(ConfFinal, format = "f", digits = 2), " each; ")) %>%
    tab_source_note(paste0("Conference Semifinalists (4): $", formatC(ConfSemi, format = "f", digits = 2), " each.")) %>%
    tab_source_note(paste0("IST PAYOUT BREAKDOWN: ")) %>%
    tab_source_note(paste0("Champion: $75.00")) %>%
    tab_source_note(paste0("Runner-Up: $15.00"))
    
  
  return(A)}



team_fonts <- data.frame(
  Team = c("Albuquerque Armadillos", "Anaheim Mice", "Anchorage Killer Whales","Austin Bats", "Baltimore Blue Crabs", "Birmingham Bandits","Boise Spuds", "Buffalo Daredevils", "Cincinnati Chili","Columbus Arches", "Des Moines Racoons", "El Paso Vipers","Honolulu Diamonds", "Jacksonville Manatees", "Kentucky Thoroughbreds","Lansing Lagoon", "Lincoln Bully", "Little Rock Big Foot","Manchester Trout", "Nashville Strings", "Pittsburgh Bridge","Providence Pilgrims", "San Diego Wave", "San Jose Seagulls","Seattle Brew", "St. Louis 66ers", "Tampa Bay Flamingos","Tulsa Tornado", "Vancouver Forest", "Vegas Blackjack"),
  Wording = c("amatic", "baloo", "fjalla","creepster", "lobster", "rye","neucha", "teko", "satisfy","arvo", "cabin_sketch", "pathway","dancing", "pacifico", "playfair","ubuntu", "bebas", "alfa","quicksand", "tangerine", "roboto_slab","fell_english", "comfortaa", "indie_flower","poppins", "oswald", "parisienne","permanent_marker", "shadows", "audiowide"))

font_add_google("Amatic SC", "amatic")
font_add_google("Baloo 2", "baloo")
font_add_google("Fjalla One", "fjalla")
font_add_google("Creepster", "creepster")
font_add_google("Lobster", "lobster")
font_add_google("Rye", "rye")
font_add_google("Neucha", "neucha")
font_add_google("Teko", "teko")
font_add_google("Satisfy", "satisfy")
font_add_google("Arvo", "arvo")
font_add_google("Cabin Sketch", "cabin_sketch")
font_add_google("Pathway Gothic One", "pathway")
font_add_google("Dancing Script", "dancing")
font_add_google("Pacifico", "pacifico")
font_add_google("Playfair Display", "playfair")
font_add_google("Ubuntu", "ubuntu")
font_add_google("Bebas Neue", "bebas")
font_add_google("Alfa Slab One", "alfa")
font_add_google("Quicksand", "quicksand")
font_add_google("Tangerine", "tangerine")
font_add_google("Roboto Slab", "roboto_slab")
font_add_google("IM Fell English", "fell_english")
font_add_google("Comfortaa", "comfortaa")
font_add_google("Indie Flower", "indie_flower")
font_add_google("Poppins", "poppins")
font_add_google("Oswald", "oswald")
font_add_google("Parisienne", "parisienne")
font_add_google("Permanent Marker", "permanent_marker")
font_add_google("Shadows Into Light Two", "shadows")
font_add_google("Audiowide", "audiowide")
showtext_auto()

GetTeamLogo1 <- function(TeamA) {
  TeamInfo2 <- SBC %>%
    filter(City == TeamA)
  ggplot(TeamInfo2) +
    geom_rect(aes(xmin = -1, xmax = 1, ymin = -1, ymax = 1), fill = TeamInfo2$Color2[1], color = TeamInfo2$Color1[1], linewidth = 3) +
    geom_image(aes(x = 0, y = 0, image = Logo), size = 0.9) +
    coord_fixed() +
    theme_void()}
GetTeamLogo2 <- function(TeamA) {
  TeamInfo2 <- SBC %>%
    filter(City == TeamA)
  ggplot(TeamInfo2) +
    geom_rect(aes(xmin = -1, xmax = 1, ymin = -1, ymax = 1), fill = TeamInfo2$Color1[1], color = TeamInfo2$Color2[1], linewidth = 3) +
    geom_image(aes(x = 0, y = 0, image = Logo), size = 0.9) +
    coord_fixed() +
    theme_void()}
GetTeamName <- function(TeamA) {
  TeamInfo2 <- SBC %>%
    left_join(team_fonts, by = c("Team")) %>%
    filter(City == TeamA)
  
  ggplot(TeamInfo2) +
    geom_rect(aes(xmin = -12, xmax = 12, ymin = -1, ymax = 1), fill = TeamInfo2$Color1[1], color = TeamInfo2$Color2[1], linewidth = 3) +
    geom_text(aes(x = 0, y = 0, label = Team, family = Wording), color = TeamInfo2$Color3, size = 18) +
    coord_fixed() +
    theme_void()
}
GetDraft <- function() {
  
  Draft <- Draft %>%
    left_join(SBC, by = c("TeamA" = "Team")) %>%
    left_join(SBC, by = c("TeamB" = "Team")) %>%
    select(1:8, Color1.x, Color3.x, Color1.y, Color3.y)
  
  gt_table <- gt(Draft) %>%
    gt_theme_espn() %>%
    tab_spanner(label = "1st Round, Saturday, June 28th", columns = c(PickA, TeamA, PlayerA, TimeA)) %>%
    tab_spanner(label = "2nd Round, Sunday, June 29th", columns = c(PickB, TeamB, PlayerB, TimeB)) %>%
    cols_label(PickA = "#",
               TeamA = "Team",
               PlayerA = "Pick",
               TimeA = "Due (ET)",
               PickB = "#",
               TeamB = "Team",
               PlayerB = "Pick",
               TimeB = "Due (ET)") %>%
    tab_header(title = md(
      paste0(
        "<div style='text-align: center; font-weight: bold; font-size: 1.1em;'>",
        "2025 Sports Business Classroom Fantasy Draft",
        "</div>"))) %>%
    sub_missing(missing_text = "") %>%
    cols_hide(columns = c(Color1.x, Color3.x, Color1.y, Color3.y)) %>%
    cols_align(columns = c(PickA, PickB, TimeA, TimeB), align = "center") %>%
    cols_align(columns = c(TeamA, TeamB), align = "right") %>%
    cols_align(columns = c(PlayerA, PlayerB), align = "left")

  for(i in 1:nrow(Draft)) {
    if(!is.na(Draft$Color1.x[i])) {
      gt_table <- gt_table %>%
        tab_style(style = list(cell_fill(color = Draft$Color1.x[i]),
                               cell_text(color = Draft$Color3.x[i])),
                  locations = cells_body(columns = c(PickA, TeamA, PlayerA, TimeA), rows = i))}
    
    if(!is.na(Draft$Color1.y[i])) {
      gt_table <- gt_table %>%
        tab_style(style = list(cell_fill(color = Draft$Color1.y[i]),
                               cell_text(color = Draft$Color3.y[i])),
                  locations = cells_body(columns = c(PickB, TeamB, PlayerB, TimeB), rows = i))}}
    
    gt_table
    
    }

ui <- page_navbar(
  
  theme = bs_theme(bootswatch = "slate",
                   version = 5,
                   primary = "blue", `enable-gradients` = TRUE, font_scale = 0.8, "form-text-color" = "white"),
  
  title = "SBC Cap Sheets",
  sidebar = sidebar(
    class = "bg-secondary",
    selectInput(inputId = "team", label = "Primary Team:", choices = unique(Players$Team), selected = "Vegas"),
    selectInput(inputId = "team2", label = "Secondary Team:", choices = unique(Players$Team), selected = "Anaheim")),
  navset_card_pill(
    nav_panel(
      title = "Team Cap Sheet",
      layout_columns(
        card(full_screen = TRUE, fill = TRUE, plotOutput("plot3")),
        card(full_screen = TRUE, fill = TRUE, gt_output("table1")),
        col_widths = c(12,12),
        row_heights = c(1,4))),
    nav_panel(
      title = "Team Draft Picks",
      layout_columns(
        card(full_screen = TRUE, fill = TRUE, plotOutput("plot6")),
        card(full_screen = TRUE, fill = TRUE, gt_output("table2")),
        col_widths = c(12,12),
        row_heights = c(1,4))),
    nav_panel(
      title = "Two-Team Comparison",
      layout_columns(
        card(full_screen = TRUE, fill = TRUE, gt_output("table6")),
        col_widths = c(12),
        row_heights = c(1))),
    nav_panel(
      title = "All Players",
      layout_columns(
        card(full_screen = TRUE, fill = TRUE, gt_output("table3")),
        col_widths = c(12),
        row_heights = c(1))),
    nav_panel(
      title = "All Picks",
      layout_columns(
        card(full_screen = TRUE, fill = TRUE, gt_output("table4")),
        col_widths = c(12),
        row_heights = c(1))),
    nav_panel(
      title = "Overall Cap Sheet",
      layout_columns(
        card(full_screen = TRUE, fill = TRUE, gt_output("table8")),
        col_widths = c(12),
        row_heights = c(1))),
    nav_panel(
      title = "2025 Draft",
      layout_columns(
        card(full_screen = TRUE, fill = TRUE, gt_output("table7")),
        col_widths = c(12),
        row_heights = c(1)))))

server <- function(input, output, session) {
  #bs_themer()
  thematic_shiny()
  

  output$table1 <- render_gt({CapSheet(input$team)})
  output$table2 <- render_gt({Picks(input$team)})
  output$table3 <- render_gt({AllPlayers()})
  output$table4 <- render_gt({AllPicks()})
  output$table5A <- render_gt({BasicTable(input$team)})
  output$table5B <- render_gt({GameRecap(input$GameID)})
  output$table6 <- render_gt({SideBySide(input$team, input$team2)})
  output$table7 <- render_gt({GetDraft()})
  output$table8 <- render_gt({OverallCapSheet()})
  
  
  output$plot3 <- renderPlot({GetTeamName(input$team)})
  output$plot6 <- renderPlot({GetTeamName(input$team)})
  
  
}

shinyApp(ui, server)
