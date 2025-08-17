print(getwd())
print(list.files("SBC_Cap_Sheets/SBC_Bref"))

library(httr)
library(tidyverse)

Games <- readRDS("SBC_Cap_Sheets/SBC_Bref/games.rds")

discord_webhook <- "https://discord.com/api/webhooks/1396720354034057326/IBOVLxOQ4xKmk2VEAX6fBgWRrsc6SZJSlMlcQVF0LovCM9wpqeivQqBMdTf4kNZHYmyv"

PeriodA <- as.integer(Sys.Date() - as.Date("2025-08-07"))

Games2 <- Games %>%
  filter(Year == 2025) %>%
  filter(Period == PeriodA) %>%
  mutate(text = do.call(paste, c(across(everything()), sep = " "))) %>%
  select(text) %>%
  pull()

for(i in 1:length(Games2)) {
  sys.sleep(1)
POST(url = discord_webhook, body = list(content = paste("Posted at", Sys.time(), Games2[i])))}

     
