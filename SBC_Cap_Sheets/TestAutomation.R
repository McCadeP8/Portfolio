library(httr)
library(tidyverse)

Games <- readRDS("SBC_Cap_Sheets/SBC_Bref/games.rds")
Schedule <- readRDS("SBC_Cap_Sheets/SBC_Bref/schedule.rds")

Schedule2 <- Schedule %>%
  filter(Year == 2025) %>%
  group_by(Period) %>%
  mutate(MaxDay = max(Day)) %>%
  filter(Day == MaxDay) %>%
  ungroup() %>%
  select(Date) %>%
  mutate(Date = Date+1) %>%
  pull()



Today <- Sys.Date()-336

if (Today %in% Schedule2) {
  
PeriodA <- Schedule %>%
  filter(Year == 2025) %>%
  filter(Date == Today) %>%
  select(Period) %>%
  pull()

Games2 <- Games %>%
  filter(Year == 2025) %>%
  filter(Period == PeriodA) %>%
  mutate(text = do.call(paste, c(across(everything()), sep = " "))) %>%
  select(text) %>%
  pull()

for(i in 1:length(Games2)) {
POST(url = discord_webhook, body = list(content = paste(i, " Posted at", Sys.time(), Games2[i])))
  Sys.sleep(30)}

} else {
  
Schedule3 <- Schedule %>%
  filter(Year == 2025) %>%
  filter(Date == Today) %>%
  select(Period) %>%
  pull()

Schedule4 <- Schedule %>%
  filter(Year == 2025) %>%
  filter(Period == Schedule3) %>%
  arrange(desc(Date)) %>%
  select(Date) %>%
  head(1) %>%
  pull()
  
POST(url = discord_webhook, body = list(content = paste0("The Matchups from Period ",Schedule3, " are still going and will end on ", Schedule4)))

}

     
