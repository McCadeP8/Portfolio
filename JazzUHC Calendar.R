library(tidyverse)
library(ggtext)

XStart <- rep(0:14,22)
XEnd <- XStart+1
YStart <- rep(21:0, each = 15)
YEnd <- YStart+1
Day <- 1:(15*22)

BaseCalender <- read.csv("C:/Users/mppac/Downloads/BaseCalender.csv")
UHTSchedule <- read.csv("C:/Users/mppac/Downloads/UHTSchedule.csv")

#UHTSchedule <- UHTSchedule %>%
#  filter(!grepl("^a", Game))

Data <- data.frame(XStart, XEnd, YStart, YEnd, Day)
Data2 <- BaseCalender %>%
  filter(is.na(Day) == F) %>%
  left_join(Data, by = c('Day')) %>%
  left_join(UHTSchedule, by = c('Date')) %>%
  separate(Date, into = c("Month", "DateOfMonth", "Year"), sep = "/")

NoGames <- Data2 %>%
  filter(is.na(Game) == T) %>%
  mutate(Color = "white", 
         Text = "black",
         Total = 0)

OneGame <- Data2 %>%
  filter(is.na(Game) == F) %>%
  group_by(Month, DateOfMonth, Year) %>%
  mutate(Total = n()) %>%
  filter(Total == 1) %>%
  mutate(Color = case_when(
    substr(Game, 1, 1) == "a" & League == "NHL" ~ "#964c18",
    substr(Game, 1, 1) == "a" & League == "NBA" ~ "black",
    substr(Game, 1, 1) != "a" & League == "NHL" ~ "#69B3E7",
    substr(Game, 1, 1) != "a" & League == "NBA" ~ "#4E008E")) %>%
  mutate(Text = case_when(
    substr(Game, 1, 1) == "a" ~ "white",
    substr(Game, 1, 1) != "a" & League == "NHL" ~ "white",
    substr(Game, 1, 1) != "a" & League == "NBA" ~ "white"))
  
TwoGames <- Data2 %>%
  filter(is.na(Game) == F) %>%
  group_by(Month, DateOfMonth, Year) %>%
  mutate(Total = n()) %>%
  filter(Total == 2) %>%
  mutate(YStart = ifelse(League == "NHL", YStart+0.5, YStart),
         YEnd = ifelse(League == "NBA", YEnd-0.5, YEnd)) %>%
  mutate(Color = case_when(
    substr(Game, 1, 1) == "a" & League == "NHL" ~ "#964c18",
    substr(Game, 1, 1) == "a" & League == "NBA" ~ "black",
    substr(Game, 1, 1) != "a" & League == "NHL" ~ "#69B3E7",
    substr(Game, 1, 1) != "a" & League == "NBA" ~ "#4E008E")) %>%
  mutate(Text = case_when(
    substr(Game, 1, 1) == "a" ~ "white",
    substr(Game, 1, 1) != "a" & League == "NHL" ~ "white",
    substr(Game, 1, 1) != "a" & League == "NBA" ~ "white")) %>%
  mutate(DateOfMonth = ifelse(League == "NHL", DateOfMonth, NA))

AllGames <- rbind(NoGames, OneGame, TwoGames)
  
  
Months <- c("October", "November", "December", "January", "February", "March", "April")
MonthX <- c(3.5,11.5,3.5,11.5,3.5,11.5,3.5)
MonthY <- c(21.5, 21.5, 15.5, 15.5, 9.5,9.5,3.5)
MonthData <- data.frame(Months, MonthX, MonthY)


ggplot(AllGames) +
  theme_void() +
  geom_rect(aes(xmin = XStart, xmax = XEnd, ymin = YStart, ymax = YEnd), color = "black", fill = AllGames$Color) +
  geom_text(aes(x = XStart+0.9, y = YStart+ifelse(Total == 2, 0.3, 0.8), label = DateOfMonth), size = 2.2, color = AllGames$Text, fontface = "bold") +
  geom_text(aes(x = XStart+0.5, y = YStart+ifelse(AllGames$Total == 2, 0.25,0.5), label = Game), size = 3, color = AllGames$Text, fontface = "bold") +
  geom_text(data = MonthData, aes(x = MonthX, y = MonthY, label = Months), size = 6) +
  geom_rect(aes(xmin = 8, xmax = 9.75, ymin = 0, ymax = 3), fill = "#964C18", color = "black") +
  geom_rect(aes(xmin = 9.75, xmax = 11.5, ymin = 0, ymax = 3), fill = "#69B3E7", color = "black") +
  geom_rect(aes(xmin = 11.5, xmax = 13.25, ymin = 0, ymax = 3), fill = "black", color = "black") +
  geom_rect(aes(xmin = 13.25, xmax = 15, ymin = 0, ymax = 3), fill = "#4E008E", color = "black") +
  geom_text(aes(x = 8.875, y = 1.5, label = "Mammoth\nAway"), color = "white", size = 4) +
  geom_text(aes(x = 10.625, y = 1.5, label = "Mammoth\nHome"), color = "white", size = 4) +
  geom_text(aes(x = 12.375, y = 1.5, label = "Jazz\nAway"), color = "white", size = 4) +
  geom_text(aes(x = 14.125, y = 1.5, label = "Jazz\nHome"), color = "white", size = 4) +
  labs(title = "2025-26 Utah  <span style='color:#4e008E;font-weight:bold'>Jazz</span> & <span style='color:#69b3e7;font-weight:bold'>Mammoth</span> Schedule") +
  theme(plot.title = element_markdown(hjust = 0.5, size = 24))

