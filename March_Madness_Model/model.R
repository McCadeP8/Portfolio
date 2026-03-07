#setwd("March_Madness_Model")

options(scipen = 99)
library(tidyverse)
library(gt)
library(gtExtras)
library(ggrepel)
library(combinat)
AssignCluster <- function(Data, Centers) {
  apply(Data, 1, function(x) {
    which.min(colSums((t(Centers)-x)^2))})}

MGameCities <- read.csv("MGameCities.csv")
MConferenceTourneyGames <- read.csv("MConferenceTourneyGames.csv")
Conferences <- read.csv("Conferences.csv")
Cities <- read.csv("Cities.csv")
MNCAATourneySeeds <- read.csv("MNCAATourneySeeds.csv")
MNCAATourneySeedRoundSlots <- read.csv("MNCAATourneySeedRoundSlots.csv")
MNCAATourneyDetailedResults <- read.csv("MNCAATourneyDetailedResults.csv")
MNCAATourneyCompactResults <- read.csv("MNCAATourneyCompactResults.csv")
MMasseyOrdinals <- read.csv("MMasseyOrdinals.csv")
MTeamSpellings <- read.csv("MTeamSpellings.csv")
MTeams <- read.csv("MTeams.csv")
MTeamConferences <- read.csv("MTeamConferences.csv")
MTeamCoaches <- read.csv("MTeamCoaches.csv")
MSecondaryTourneyTeams <- read.csv("MSecondaryTourneyTeams.csv")
MSecondaryTourneyCompactResults <- read.csv("MSecondaryTourneyCompactResults.csv")
MSeasons <- read.csv("MSeasons.csv")
MRegularSeasonDetailedResults <- read.csv("MRegularSeasonDetailedResults.csv")
MRegularSeasonCompactResults <- read.csv("MRegularSeasonCompactResults.csv")
MNCAATourneySlots <- read.csv("MNCAATourneySlots.csv")
WGameCities <- read.csv("WGameCities.csv")
WConferenceTourneyGames <- read.csv("WConferenceTourneyGames.csv")
WNCAATourneySeeds <- read.csv("WNCAATourneySeeds.csv")
WNCAATourneyDetailedResults <- read.csv("WNCAATourneyDetailedResults.csv")
WNCAATourneyCompactResults <- read.csv("WNCAATourneyCompactResults.csv")
WTeamSpellings <- read.csv("WTeamSpellings.csv")
WTeams <- read.csv("WTeams.csv")
WTeamConferences <- read.csv("WTeamConferences.csv")
WSecondaryTourneyTeams <- read.csv("WSecondaryTourneyTeams.csv")
WSecondaryTourneyCompactResults <- read.csv("WSecondaryTourneyCompactResults.csv")
WSeasons <- read.csv("WSeasons.csv")
WRegularSeasonDetailedResults <- read.csv("WRegularSeasonDetailedResults.csv")
WRegularSeasonCompactResults <- read.csv("WRegularSeasonCompactResults.csv")
WNCAATourneySlots <- read.csv("WNCAATourneySlots.csv")

MRegularSeasonDetailedResults <- MRegularSeasonDetailedResults %>%
  mutate(Type = "Regular")
MNCAATourneyDetailedResults <- MNCAATourneyDetailedResults %>%
  mutate(Type = "NCAA")
MensGames <- rbind(MRegularSeasonDetailedResults, MNCAATourneyDetailedResults)
remove(MRegularSeasonCompactResults)
remove(MRegularSeasonDetailedResults) 
remove(MNCAATourneyCompactResults)
remove(MNCAATourneyDetailedResults)
remove(MNCAATourneySeedRoundSlots)
remove(MSecondaryTourneyCompactResults)
remove(MSecondaryTourneyTeams)
remove(MTeamSpellings)
MTeams <- MTeams %>%
  select(TeamID, TeamName)
MensGames <- MensGames %>%
  left_join(MTeams, by = c('WTeamID' = 'TeamID')) %>%
  mutate(WTeamName = TeamName) %>%
  select(-TeamName) %>%
  left_join(MTeams, by = c('LTeamID' = 'TeamID')) %>%
  mutate(LTeamName = TeamName) %>%
  select(-TeamName)
remove(MGameCities)
remove(MTeamCoaches)
remove(MTeams)
remove(MMasseyOrdinals)
MConferenceTourneyGames <- MConferenceTourneyGames %>%
  mutate(Type2 = "Conf Tourney") %>%
  select(-ConfAbbrev)
MensGames <- MensGames %>%
  left_join(MConferenceTourneyGames, by = c('Season','DayNum','WTeamID','LTeamID')) %>%
  mutate(Type = ifelse(is.na(Type2) == T, Type, Type2)) %>%
  left_join(MTeamConferences, by = c('WTeamID' = 'TeamID', 'Season')) %>%
  mutate(WTeamConf = ConfAbbrev) %>%
  select(-ConfAbbrev) %>%
  left_join(MTeamConferences, by = c('LTeamID' = 'TeamID', 'Season')) %>%
  mutate(LTeamConf = ConfAbbrev) %>%
  select(-ConfAbbrev, -Type2)
remove(MTeamConferences)
remove(MConferenceTourneyGames)
remove(MNCAATourneySlots)
remove(MNCAATourneySeeds)
remove(Cities)
remove(Conferences)
MSeasons <- MSeasons %>%
  mutate(DayZero = as.Date(DayZero, format = "%m/%d/%Y")) %>%
  uncount(155) %>%
  group_by(Season) %>%
  mutate(DayNum = 0:154,  
         DayZero = DayZero + DayNum) %>%
  ungroup() %>%
  select(-RegionW, -RegionX, -RegionY, -RegionZ)
MensGames <- MensGames %>%
  left_join(MSeasons, by = c('Season', 'DayNum')) %>%
  mutate(WPace = ((WFGA+WTO+(WFTA*(4/9))-WOR)/(NumOT*5+40))*40,
         WORtg = WScore/WPace*100,
         WORebPct = WOR/(WOR+LDR)*100,
         WTSPct = WScore/(WFGA+(WFTA*(4/9)*2))*100,
         WTovPct = WTO/(WFGA+WTO+(WFTA*(4/9)))*100,
         WEffPct = ((WFGM+(0.5*WFGM3))/WFGA)*100,
         WFTr = WFTA/WFGA,
         WFGPct = WFGM/WFGA*100,
         WFG3Pct = WFGM3/WFGA3*100,
         WFG2Pct = (WFGM-WFGM3)/(WFGA-WFGA3)*100,
         WFTPct = WFTM/WFTA*100,
         LPace = ((LFGA+LTO+(LFTA*(4/9))-LOR)/(NumOT*5+40))*40,
         LORtg = LScore/LPace*100,
         LORebPct = LOR/(LOR+WDR)*100,
         LTSPct = LScore/(LFGA+(LFTA*(4/9)*2))*100,
         LTovPct = LTO/(LFGA+LTO+(LFTA*(4/9)))*100,
         LEffPct = (LFGM+(0.5*LFGM3))/LFGA*100,
         LFTr = LFTA/LFGA,
         LFGPct = LFGM/LFGA*100,
         LFG3Pct = LFGM3/LFGA3*100,
         LFG2Pct = (LFGM-LFGM3)/(LFGA-LFGA3)*100,
         LFTPct = LFTM/LFTA*100) %>%
  mutate(ConfGame = ifelse(WTeamConf == LTeamConf, "Conf", "Non-Conf")) %>%
  select(Season, DayZero, WTeamName, WTeamID, WTeamConf, LTeamName, LTeamID, LTeamConf, ConfGame, WScore, LScore, WLoc, NumOT, Type, WFGM, WFGA, WFGM3, WFGA3, WFTM, WFTA, WOR, WDR, WAst, WTO, WStl, WBlk, WPF, WPace, WORtg, WORebPct, WTSPct, WTovPct, WEffPct, WFTr, WFGPct, WFG3Pct, WFG2Pct, WFTPct, LFGM, LFGA, LFGM3, LFGA3, LFTM, LFTA, LOR, LDR, LAst, LTO, LStl, LBlk, LPF, LPace, LORtg, LORebPct, LTSPct, LTovPct, LEffPct, LFTr, LFGPct, LFG3Pct, LFG2Pct, LFTPct) %>%
  mutate(Gender = "Male")
remove(MSeasons)

WRegularSeasonDetailedResults <- WRegularSeasonDetailedResults %>%
  mutate(Type = "Regular")
WNCAATourneyDetailedResults <- WNCAATourneyDetailedResults %>%
  mutate(Type = "NCAA")
WomensGames <- rbind(WRegularSeasonDetailedResults, WNCAATourneyDetailedResults)
remove(WRegularSeasonCompactResults)
remove(WRegularSeasonDetailedResults) 
remove(WNCAATourneyCompactResults)
remove(WNCAATourneyDetailedResults)
remove(WNCAATourneySeedRoundSlots)
remove(WSecondaryTourneyCompactResults)
remove(WSecondaryTourneyTeams)
remove(WTeamSpellings)
WTeams <- WTeams %>%
  select(TeamID, TeamName)
WomensGames <- WomensGames %>%
  left_join(WTeams, by = c('WTeamID' = 'TeamID')) %>%
  mutate(WTeamName = TeamName) %>%
  select(-TeamName) %>%
  left_join(WTeams, by = c('LTeamID' = 'TeamID')) %>%
  mutate(LTeamName = TeamName) %>%
  select(-TeamName)
remove(WGameCities)
remove(WTeamCoaches)
remove(WTeams)
remove(WMasseyOrdinals)
WConferenceTourneyGames <- WConferenceTourneyGames %>%
  mutate(Type2 = "Conf Tourney") %>%
  select(-ConfAbbrev)
WomensGames <- WomensGames %>%
  left_join(WConferenceTourneyGames, by = c('Season','DayNum','WTeamID','LTeamID')) %>%
  mutate(Type = ifelse(is.na(Type2) == T, Type, Type2)) %>%
  left_join(WTeamConferences, by = c('WTeamID' = 'TeamID', 'Season')) %>%
  mutate(WTeamConf = ConfAbbrev) %>%
  select(-ConfAbbrev) %>%
  left_join(WTeamConferences, by = c('LTeamID' = 'TeamID', 'Season')) %>%
  mutate(LTeamConf = ConfAbbrev) %>%
  select(-ConfAbbrev, -Type2)
remove(WTeamConferences)
remove(WConferenceTourneyGames)
remove(WNCAATourneySlots)
remove(WNCAATourneySeeds)
remove(Cities)
remove(Conferences)
WSeasons <- WSeasons %>%
  mutate(DayZero = as.Date(DayZero, format = "%m/%d/%Y")) %>%
  uncount(155) %>%
  group_by(Season) %>%
  mutate(DayNum = 0:154,  
         DayZero = DayZero + DayNum) %>%
  ungroup() %>%
  select(-RegionW, -RegionX, -RegionY, -RegionZ)
WomensGames <- WomensGames %>%
  left_join(WSeasons, by = c('Season', 'DayNum')) %>%
  mutate(WPace = ((WFGA+WTO+(WFTA*(4/9))-WOR)/(NumOT*5+40))*40,
         WORtg = WScore/WPace*100,
         WORebPct = WOR/(WOR+LDR)*100,
         WTSPct = WScore/(WFGA+(WFTA*(4/9)*2))*100,
         WTovPct = WTO/(WFGA+WTO+(WFTA*(4/9)))*100,
         WEffPct = (WFGM+(0.5*WFGM3))/WFGA*100,
         WFTr = WFTA/WFGA,
         WFGPct = WFGM/WFGA*100,
         WFG3Pct = WFGM3/WFGA3*100,
         WFG2Pct = (WFGM-WFGM3)/(WFGA-WFGA3)*100,
         WFTPct = WFTM/WFTA*100,
         LPace = ((LFGA+LTO+(LFTA*(4/9))-LOR)/(NumOT*5+40))*40,
         LORtg = LScore/LPace*100,
         LORebPct = LOR/(LOR+WDR)*100,
         LTSPct = LScore/(LFGA+(LFTA*(4/9)*2))*100,
         LTovPct = LTO/(LFGA+LTO+(LFTA*(4/9)))*100,
         LEffPct = (LFGM+(0.5*LFGM3))/LFGA*100,
         LFTr = LFTA/LFGA,
         LFGPct = LFGM/LFGA*100,
         LFG3Pct = LFGM3/LFGA3*100,
         LFG2Pct = (LFGM-LFGM3)/(LFGA-LFGA3)*100,
         LFTPct = LFTM/LFTA*100) %>%
  mutate(ConfGame = ifelse(WTeamConf == LTeamConf, "Conf", "Non-Conf")) %>%
  select(Season, DayZero, WTeamName, WTeamID, WTeamConf, LTeamName, LTeamID, LTeamConf, ConfGame, WScore, LScore, WLoc, NumOT, Type, WFGM, WFGA, WFGM3, WFGA3, WFTM, WFTA, WOR, WDR, WAst, WTO, WStl, WBlk, WPF, WPace, WORtg, WORebPct, WTSPct, WTovPct, WEffPct, WFTr, WFGPct, WFG3Pct, WFG2Pct, WFTPct, LFGM, LFGA, LFGM3, LFGA3, LFTM, LFTA, LOR, LDR, LAst, LTO, LStl, LBlk, LPF, LPace, LORtg, LORebPct, LTSPct, LTovPct, LEffPct, LFTr, LFGPct, LFG3Pct, LFG2Pct, LFTPct) %>%
  mutate(Gender = "Female")
remove(WSeasons)
Games <- rbind(MensGames, WomensGames)
remove(MensGames, WomensGames)
colnames(Games) <- c(
  "Season", "DayZero", "Win_TeamName", "Win_TeamID", "Win_TeamConf", "Lose_TeamName", "Lose_TeamID", "Lose_TeamConf", "ConfGame", "Win_Score", "Lose_Score", "Loc", "NumOT", "Type", "Win_FGM", "Win_FGA", "Win_FGM3", "Win_FGA3", "Win_FTM", "Win_FTA", "Win_OR", "Win_DR", "Win_Ast", "Win_TO", "Win_Stl", "Win_Blk", "Win_PF", "Win_Pace", "Win_ORtg", "Win_ORebPct", "Win_TSPct", "Win_TovPct", "Win_EffPct", "Win_FTr", "Win_FGPct", "Win_FG3Pct", "Win_FG2Pct", "Win_FTPct", "Lose_FGM", "Lose_FGA", "Lose_FGM3", "Lose_FGA3", "Lose_FTM", "Lose_FTA", "Lose_OR", "Lose_DR", "Lose_Ast", "Lose_TO", "Lose_Stl", "Lose_Blk", "Lose_PF", "Lose_Pace", "Lose_ORtg", "Lose_ORebPct", "Lose_TSPct", "Lose_TovPct", "Lose_EffPct", "Lose_FTr", "Lose_FGPct", "Lose_FG3Pct", "Lose_FG2Pct", "Lose_FTPct", "Gender")

Games2 <- Games
colnames(Games2) <- c(
  "Season", "DayZero", "TeamName", "TeamID", "TeamConf", "Opp_TeamName", "Opp_TeamID", "Opp_TeamConf", "ConfGame", "Team_Score", "Opp_Score", "Loc", "NumOT", "Type", "Team_FGM", "Team_FGA", "Team_FGM3", "Team_FGA3", "Team_FTM", "Team_FTA", "Team_OR", "Team_DR", "Team_Ast", "Team_TO", "Team_Stl", "Team_Blk", "Team_PF", "Team_Pace", "Team_ORtg", "Team_ORebPct", "Team_TSPct", "Team_TovPct", "Team_EffPct", "Team_FTr", "Team_FGPct", "Team_FG3Pct", "Team_FG2Pct", "Team_FTPct", "Opp_FGM", "Opp_FGA", "Opp_FGM3", "Opp_FGA3", "Opp_FTM", "Opp_FTA", "Opp_OR", "Opp_DR", "Opp_Ast", "Opp_TO", "Opp_Stl", "Opp_Blk", "Opp_PF", "Opp_Pace", "Opp_ORtg", "Opp_ORebPct", "Opp_TSPct", "Opp_TovPct", "Opp_EffPct", "Opp_FTr", "Opp_FGPct", "Opp_FG3Pct", "Opp_FG2Pct", "Opp_FTPct", "Gender")
Games3 <- Games
colnames(Games3) <- c(
  "Season", "DayZero", "Opp_TeamName", "Opp_TeamID", "Opp_TeamConf", "TeamName", "TeamID", "TeamConf", "ConfGame", "Opp_Score", "Team_Score", "Loc", "NumOT", "Type", "Opp_FGM", "Opp_FGA", "Opp_FGM3", "Opp_FGA3", "Opp_FTM", "Opp_FTA", "Opp_OR", "Opp_DR", "Opp_Ast", "Opp_TO", "Opp_Stl", "Opp_Blk", "Opp_PF", "Opp_Pace", "Opp_ORtg", "Opp_ORebPct", "Opp_TSPct", "Opp_TovPct","Opp_EffPct", "Opp_FTr", "Opp_FGPct", "Opp_FG3Pct", "Opp_FG2Pct", "Opp_FTPct", "Team_FGM", "Team_FGA", "Team_FGM3", "Team_FGA3", "Team_FTM", "Team_FTA", "Team_OR", "Team_DR", "Team_Ast", "Team_TO", "Team_Stl", "Team_Blk", "Team_PF", "Team_Pace", "Team_ORtg", "Team_ORebPct", "Team_TSPct", "Team_TovPct","Team_EffPct", "Team_FTr", "Team_FGPct", "Team_FG3Pct", "Team_FG2Pct", "Team_FTPct", "Gender")
Games2 <- Games2 %>%
  select(-Opp_TeamName, -Opp_TeamConf)
Games3 <- Games3 %>%
  select(-Opp_TeamName, -Opp_TeamConf)
TeamAverages <- rbind(Games2,Games3)
TeamAverages <- TeamAverages %>%
  group_by(Season, TeamName, TeamID, Gender) %>%
  summarize(GP = n(),
            W = sum(Team_Score>Opp_Score),
            L = GP-W,
            WPct = W/GP*100,
            Team_Score = mean(Team_Score),
            Team_FGM = mean(Team_FGM),
            Team_FGA = mean(Team_FGA),
            Team_FGM3 = mean(Team_FGM3),
            Team_FGA3 = mean(Team_FGA3),
            Team_FTM = mean(Team_FTM),
            Team_FTA = mean(Team_FTA),
            Team_OR = mean(Team_OR),
            Team_DR = mean(Team_DR),
            Team_Ast = mean(Team_Ast),
            Team_TO = mean(Team_TO),
            Team_STL = mean(Team_Stl),
            Team_Blk = mean(Team_Blk),
            Team_PF = mean(Team_PF),
            Opp_Score = mean(Opp_Score),
            Opp_FGM = mean(Opp_FGM),
            Opp_FGA = mean(Opp_FGA),
            Opp_FGM3 = mean(Opp_FGM3),
            Opp_FGA3 = mean(Opp_FGA3),
            Opp_FTM = mean(Opp_FTM),
            Opp_FTA = mean(Opp_FTA),
            Opp_OR = mean(Opp_OR),
            Opp_DR = mean(Opp_DR),
            Opp_Ast = mean(Opp_Ast),
            Opp_TO = mean(Opp_TO),
            Opp_STL = mean(Opp_Stl),
            Opp_Blk = mean(Opp_Blk),
            Opp_PF = mean(Opp_PF),
            OTPlayed = sum(NumOT)/GP) %>%
  ungroup() %>%
  mutate(Team_Pace = ((Team_FGA+Team_TO+(Team_FTA*(4/9))-Team_OR)/(OTPlayed*5+40))*40,
         Team_ORtg = Team_Score/Team_Pace*100,  
         Team_ORebPct = Team_OR/(Team_OR+Opp_DR)*100,  
         Team_TSPct = Team_Score/(Team_FGA+(Team_FTA*(4/9)*2))*100,  
         Team_TovPct = Team_TO/(Team_FGA+Team_TO+(Team_FTA*(4/9)))*100,  
         Team_EffPct = (Team_FGM+(0.5*Team_FGM3))/Team_FGA*100,  
         Team_FTr = Team_FTA/Team_FGA,  
         Team_FGPct = Team_FGM/Team_FGA*100,  
         Team_FG3Pct = Team_FGM3/Team_FGA3*100,  
         Team_FG2Pct = (Team_FGM-Team_FGM3)/(Team_FGA-Team_FGA3)*100,  
         Team_FTPct = Team_FTM/Team_FTA*100,  
         Opp_Pace = ((Opp_FGA+Opp_TO+(Opp_FTA*(4/9))-Opp_OR)/(OTPlayed*5+40))*40,  
         Opp_ORtg = Opp_Score/Opp_Pace*100,  
         Opp_ORebPct = Opp_OR/(Opp_OR + Team_DR)*100,  
         Opp_TSPct = Opp_Score/(Opp_FGA+(Opp_FTA*(4/9)*2))*100,  
         Opp_TovPct = Opp_TO/(Opp_FGA+Opp_TO+(Opp_FTA*(4/9)))*100,  
         Opp_EffPct = (Opp_FGM+(0.5*Opp_FGM3))/Opp_FGA*100,  
         Opp_FTr = Opp_FTA/Opp_FGA,  
         Opp_FGPct = Opp_FGM/Opp_FGA*100,  
         Opp_FG3Pct = Opp_FGM3/Opp_FGA3*100,  
         Opp_FG2Pct = (Opp_FGM-Opp_FGM3)/(Opp_FGA-Opp_FGA3)*100,  
         Opp_FTPct = Opp_FTM/Opp_FTA*100,
         Net_Score = Team_Score-Opp_Score,
         Net_FGM = Team_FGM-Opp_FGM,
         Net_FGA = Team_FGA-Opp_FGA,
         Net_FGM3 = Team_FGM3-Opp_FGM3,
         Net_FGA3 = Team_FGA3-Opp_FGA3,
         Net_FTM = Team_FTM-Opp_FTM,
         Net_FTA = Team_FTA-Opp_FTA,
         Net_OR = Team_OR-Opp_OR,
         Net_DR = Team_DR-Opp_DR,
         Net_Ast = Team_Ast-Opp_Ast,
         Net_TO = Team_TO-Opp_TO,
         Net_STL = Team_STL-Opp_STL,
         Net_Blk = Team_Blk-Opp_Blk,
         Net_PF = Team_PF-Opp_PF,
         Net_ORtg = Team_ORtg-Opp_ORtg,
         Net_ORebPct = Team_ORebPct-Opp_ORebPct,
         Net_TSPct = Team_TSPct-Opp_TSPct,
         Net_TovPct = Team_TovPct-Opp_TovPct,
         Net_EffPct = Team_EffPct-Opp_EffPct,
         Net_FTr = Team_FTr-Opp_FTr,
         Net_FGPct = Team_FGPct-Opp_FGPct,
         Net_FG3Pct = Team_FG3Pct-Opp_FG3Pct,
         Net_FG2Pct = Team_FG2Pct-Opp_FG2Pct,
         Net_FTPct = Team_FTPct-Opp_FTPct)

Y2026 <- TeamAverages %>%
  filter(Season == 2026)
TeamAverages <- TeamAverages %>%
  filter(Season != 2026)
remove(Games2, Games3)

LeagueAverages <- Games
  colnames(LeagueAverages) <- c(
  "Season", "DayZero", "Opp_TeamName", "Opp_TeamID", "Opp_TeamConf", "TeamName", "TeamID", "TeamConf", "ConfGame", "Opp_Score", "Team_Score", "Loc", "NumOT", "Type", "Opp_FGM", "Opp_FGA", "Opp_FGM3", "Opp_FGA3", "Opp_FTM", "Opp_FTA", "Opp_OR", "Opp_DR", "Opp_Ast", "Opp_TO", "Opp_Stl", "Opp_Blk", "Opp_PF", "Opp_Pace", "Opp_ORtg", "Opp_ORebPct", "Opp_TSPct", "Opp_TovPct","Opp_EffPct", "Opp_FTr", "Opp_FGPct", "Opp_FG3Pct", "Opp_FG2Pct", "Opp_FTPct", "Team_FGM", "Team_FGA", "Team_FGM3", "Team_FGA3", "Team_FTM", "Team_FTA", "Team_OR", "Team_DR", "Team_Ast", "Team_TO", "Team_Stl", "Team_Blk", "Team_PF", "Team_Pace", "Team_ORtg", "Team_ORebPct", "Team_TSPct", "Team_TovPct","Team_EffPct", "Team_FTr", "Team_FGPct", "Team_FG3Pct", "Team_FG2Pct", "Team_FTPct", "Gender")
LeagueAverages2 <- Games
  colnames(LeagueAverages2) <- c(
  "Season", "DayZero", "TeamName", "TeamID", "TeamConf", "Opp_TeamName", "Opp_TeamID", "Opp_TeamConf", "ConfGame", "Team_Score", "Opp_Score", "Loc", "NumOT", "Type", "Team_FGM", "Team_FGA", "Team_FGM3", "Team_FGA3", "Team_FTM", "Team_FTA", "Team_OR", "Team_DR", "Team_Ast", "Team_TO", "Team_Stl", "Team_Blk", "Team_PF", "Team_Pace", "Team_ORtg", "Team_ORebPct", "Team_TSPct", "Team_TovPct", "Team_EffPct", "Team_FTr", "Team_FGPct", "Team_FG3Pct", "Team_FG2Pct", "Team_FTPct", "Opp_FGM", "Opp_FGA", "Opp_FGM3", "Opp_FGA3", "Opp_FTM", "Opp_FTA", "Opp_OR", "Opp_DR", "Opp_Ast", "Opp_TO", "Opp_Stl", "Opp_Blk", "Opp_PF", "Opp_Pace", "Opp_ORtg", "Opp_ORebPct", "Opp_TSPct", "Opp_TovPct", "Opp_EffPct", "Opp_FTr", "Opp_FGPct", "Opp_FG3Pct", "Opp_FG2Pct", "Opp_FTPct", "Gender")
LeagueAverages <- rbind(LeagueAverages,LeagueAverages2)
LeagueAverages <- LeagueAverages %>%
  group_by(Season, Gender) %>%
  summarize(GP = n(),
            W = sum(Team_Score>Opp_Score),
            L = GP-W,
            WPct = W/GP*100,
            Team_Score = mean(Team_Score),
            Team_FGM = mean(Team_FGM),
            Team_FGA = mean(Team_FGA),
            Team_FGM3 = mean(Team_FGM3),
            Team_FGA3 = mean(Team_FGA3),
            Team_FTM = mean(Team_FTM),
            Team_FTA = mean(Team_FTA),
            Team_OR = mean(Team_OR),
            Team_DR = mean(Team_DR),
            Team_Ast = mean(Team_Ast),
            Team_TO = mean(Team_TO),
            Team_STL = mean(Team_Stl),
            Team_Blk = mean(Team_Blk),
            Team_PF = mean(Team_PF),
            OTPlayed = sum(NumOT)/GP) %>%
  ungroup() %>%
  mutate(Team_Pace = ((Team_FGA+Team_TO+(Team_FTA*(4/9))-Team_OR)/(OTPlayed*5+40))*40,
         Team_ORtg = Team_Score/Team_Pace*100,  
         Team_ORebPct = Team_OR/(Team_OR+Team_DR)*100,  
         Team_TSPct = Team_Score/(Team_FGA+(Team_FTA*(4/9)*2))*100,  
         Team_TovPct = Team_TO/(Team_FGA+Team_TO+(Team_FTA*(4/9)))*100,  
         Team_EffPct = (Team_FGM+(0.5*Team_FGM3))/Team_FGA*100,  
         Team_FTr = Team_FTA/Team_FGA,  
         Team_FGPct = Team_FGM/Team_FGA*100,  
         Team_FG3Pct = Team_FGM3/Team_FGA3*100,  
         Team_FG2Pct = (Team_FGM-Team_FGM3)/(Team_FGA-Team_FGA3)*100,  
         Team_FTPct = Team_FTM/Team_FTA*100)

TeamAverages <- TeamAverages %>%
    left_join(LeagueAverages, by = c("Season", "Gender"), suffix = c("", "_League")) %>%
  mutate(
    R_Team_Score = Team_Score-Team_Score_League,
    R_Team_FGM = Team_FGM-Team_FGM_League,
    R_Team_FGA = Team_FGA-Team_FGA_League,
    R_Team_FGPct = Team_FGPct-Team_FGPct_League,
    R_Team_FGM3 = Team_FGM3-Team_FGM3_League,
    R_Team_FGA3 = Team_FGA3-Team_FGA3_League,
    R_Team_FG3Pct = Team_FG3Pct-Team_FG3Pct_League,
    R_Team_FG2Pct = Team_FG2Pct-Team_FG2Pct_League,
    R_Team_FTM = Team_FTM-Team_FTM_League,
    R_Team_FTA = Team_FTA-Team_FTA_League,
    R_Team_FTPct = Team_FTPct-Team_FTPct_League,
    R_Team_FTr = Team_FTr-Team_FTr_League,
    R_Team_OR = Team_OR-Team_OR_League,
    R_Team_DR = Team_DR-Team_DR_League,
    R_Team_ORebPct = Team_ORebPct-Team_ORebPct_League,
    R_Team_Ast = Team_Ast-Team_Ast_League,
    R_Team_TO = Team_TO-Team_TO_League,
    R_Team_STL = Team_STL-Team_STL_League,
    R_Team_Blk = Team_Blk-Team_Blk_League,
    R_Team_PF = Team_PF-Team_PF_League,
    R_Team_Pace = Team_Pace-Team_Pace_League,
    R_Team_ORtg = Team_ORtg-Team_ORtg_League,
    R_Team_TSPct = Team_TSPct-Team_TSPct_League,
    R_Team_TovPct = Team_TovPct-Team_TovPct_League,
    R_Team_EffPct = Team_EffPct-Team_EffPct_League,
    R_Opp_Score = Opp_Score-Team_Score_League,
    R_Opp_FGM = Opp_FGM-Team_FGM_League,
    R_Opp_FGA = Opp_FGA-Team_FGA_League,
    R_Opp_FGPct = Opp_FGPct-Team_FGPct_League,
    R_Opp_FGM3 = Opp_FGM3-Team_FGM3_League,
    R_Opp_FGA3 = Opp_FGA3-Team_FGA3_League,
    R_Opp_FG3Pct = Opp_FG3Pct-Team_FG3Pct_League,
    R_Opp_FG2Pct = Opp_FG2Pct-Team_FG2Pct_League,
    R_Opp_FTM = Opp_FTM-Team_FTM_League,
    R_Opp_FTA = Opp_FTA-Team_FTA_League,
    R_Opp_FTPct = Opp_FTPct-Team_FTPct_League,
    R_Opp_FTr = Opp_FTr-Team_FTr_League,
    R_Opp_OR = Opp_OR-Team_OR_League,
    R_Opp_DR = Opp_DR-Team_DR_League,
    R_Opp_ORebPct = Opp_ORebPct-Team_ORebPct_League,
    R_Opp_Ast = Opp_Ast-Team_Ast_League,
    R_Opp_TO = Opp_TO-Team_TO_League,
    R_Opp_STL = Opp_STL-Team_STL_League,
    R_Opp_Blk = Opp_Blk-Team_Blk_League,
    R_Opp_PF = Opp_PF-Team_PF_League,
    R_Opp_Pace = Opp_Pace-Team_Pace_League,
    R_Opp_ORtg = Opp_ORtg-Team_ORtg_League,
    R_Opp_TSPct = Opp_TSPct-Team_TSPct_League,
    R_Opp_TovPct = Opp_TovPct-Team_TovPct_League,
    R_Opp_EffPct = Opp_EffPct-Team_EffPct_League) %>%
  select(-ends_with("_League")) %>%
  ungroup()

MensTeams <- TeamAverages %>%
  filter(Gender == "Male")
WomensTeams <- TeamAverages %>%
  filter(Gender == "Female")

NClusters <- 7
ClusterData <- MensTeams %>% 
  select(Net_ORtg, Net_OR, Net_DR, Net_TO)
KMeans <- kmeans(ClusterData, centers = NClusters, nstart = 15)
MensTeams <- MensTeams %>%
  mutate(Cluster = KMeans$cluster)
KMeansCenter <- KMeans$centers
Y2026Men <- Y2026 %>%
  filter(Gender == "Male")
Y2026Men2 <- Y2026Men %>%
  select(Net_ORtg, Net_OR, Net_DR, Net_TO)
Y2026Men$Cluster <- AssignCluster(Y2026Men2, KMeansCenter)

ClusterData <- WomensTeams %>% 
  select(Net_ORtg, Net_OR, Net_DR, Net_TO)
KMeans <- kmeans(ClusterData, centers = NClusters, nstart = 15)
WomensTeams <- WomensTeams %>%
  mutate(Cluster = KMeans$cluster)
KMeansCenter <- KMeans$centers
Y2026Women <- Y2026 %>%
  filter(Gender == "Female")
Y2026Women2 <- Y2026Women %>%
  select(Net_ORtg, Net_OR, Net_DR, Net_TO)
Y2026Women$Cluster <- AssignCluster(Y2026Women2, KMeansCenter)

Y2026 <- rbind(Y2026Men, Y2026Women)
TeamAverages <- rbind(MensTeams, WomensTeams)
remove(MensTeams, WomensTeams, KMeans, ClusterData, KMeansCenter, Y2026Men, Y2026Women, Y2026Men2, Y2026Women2)

Combinations <- data.frame(t(combn(NClusters,2)))
X1 <- 1:NClusters
X2 <- 1:NClusters
Combinations2 <- data.frame(X1,X2)
Combinations <- rbind(Combinations, Combinations2)
Combinations <- rbind(Combinations,Combinations)
Combinations <- Combinations %>%
  mutate(Gender = c(rep("Male",nrow(Combinations)/2),rep("Female",nrow(Combinations)/2)))
remove(X1,X2,Combinations2)

GamesTeamAverages <- Games %>%
  filter(Season <= 2024) %>%
  select(Season, DayZero, Gender, Win_TeamName, Win_Score, Lose_TeamName, Lose_Score) %>%
  left_join(TeamAverages, by = c('Win_TeamName' = 'TeamName', 'Season', 'Gender')) %>%
  left_join(TeamAverages, by = c('Lose_TeamName' = 'TeamName', 'Season', 'Gender'))

GamesTeamAverages2 <- GamesTeamAverages %>%
  filter(TeamID.x < TeamID.y) %>%
    rename(TeamName.x = Win_TeamName,
           TeamName.y = Lose_TeamName,
           TeamScore.x = Win_Score,
           TeamScore.y = Lose_Score)

GamesTeamAverages3 <- GamesTeamAverages %>%
  filter(TeamID.x > TeamID.y)

colnames(GamesTeamAverages3) <- c(
"Season", "DayZero", "Gender", "TeamName.y", "TeamScore.y", "TeamName.x", "TeamScore.x", "TeamID.y", "GP.y", "W.y", 
"L.y", "WPct.y", "Team_Score.y", "Team_FGM.y", "Team_FGA.y", "Team_FGM3.y", "Team_FGA3.y", "Team_FTM.y", "Team_FTA.y", "Team_OR.y", 
"Team_DR.y", "Team_Ast.y", "Team_TO.y", "Team_STL.y", "Team_Blk.y", "Team_PF.y", "Opp_Score.y", "Opp_FGM.y", "Opp_FGA.y", "Opp_FGM3.y", 
"Opp_FGA3.y", "Opp_FTM.y", "Opp_FTA.y", "Opp_OR.y", "Opp_DR.y", "Opp_Ast.y", "Opp_TO.y", "Opp_STL.y", "Opp_Blk.y", "Opp_PF.y", 
"OTPlayed.y", "Team_Pace.y", "Team_ORtg.y", "Team_ORebPct.y", "Team_TSPct.y", "Team_TovPct.y", "Team_EffPct.y", "Team_FTr.y", "Team_FGPct.y", "Team_FG3Pct.y", 
"Team_FG2Pct.y", "Team_FTPct.y", "Opp_Pace.y", "Opp_ORtg.y", "Opp_ORebPct.y", "Opp_TSPct.y", "Opp_TovPct.y", "Opp_EffPct.y", "Opp_FTr.y", "Opp_FGPct.y", 
"Opp_FG3Pct.y", "Opp_FG2Pct.y", "Opp_FTPct.y", "Net_Score.y", "Net_FGM.y", "Net_FGA.y", "Net_FGM3.y", "Net_FGA3.y", "Net_FTM.y", "Net_FTA.y", 
"Net_OR.y", "Net_DR.y", "Net_Ast.y", "Net_TO.y", "Net_STL.y", "Net_Blk.y", "Net_PF.y", "Net_ORtg.y", "Net_ORebPct.y", "Net_TSPct.y", 
"Net_TovPct.y", "Net_EffPct.y", "Net_FTr.y", "Net_FGPct.y", "Net_FG3Pct.y", "Net_FG2Pct.y", "Net_FTPct.y", "R_Team_Score.y", "R_Team_FGM.y", "R_Team_FGA.y", 
"R_Team_FGPct.y", "R_Team_FGM3.y", "R_Team_FGA3.y", "R_Team_FG3Pct.y", "R_Team_FG2Pct.y", "R_Team_FTM.y", "R_Team_FTA.y", "R_Team_FTPct.y", "R_Team_FTr.y", "R_Team_OR.y", 
"R_Team_DR.y", "R_Team_ORebPct.y", "R_Team_Ast.y", "R_Team_TO.y", "R_Team_STL.y", "R_Team_Blk.y", "R_Team_PF.y", "R_Team_Pace.y", "R_Team_ORtg.y", "R_Team_TSPct.y", 
"R_Team_TovPct.y", "R_Team_EffPct.y", "R_Opp_Score.y", "R_Opp_FGM.y", "R_Opp_FGA.y", "R_Opp_FGPct.y", "R_Opp_FGM3.y", "R_Opp_FGA3.y", "R_Opp_FG3Pct.y", "R_Opp_FG2Pct.y", 
"R_Opp_FTM.y", "R_Opp_FTA.y", "R_Opp_FTPct.y", "R_Opp_FTr.y", "R_Opp_OR.y", "R_Opp_DR.y", "R_Opp_ORebPct.y", "R_Opp_Ast.y", "R_Opp_TO.y", "R_Opp_STL.y", 
"R_Opp_Blk.y", "R_Opp_PF.y", "R_Opp_Pace.y", "R_Opp_ORtg.y", "R_Opp_TSPct.y", "R_Opp_TovPct.y", "R_Opp_EffPct.y", "Cluster.y", "TeamID.x", "GP.x", 
"W.x", "L.x", "WPct.x", "Team_Score.x", "Team_FGM.x", "Team_FGA.x", "Team_FGM3.x", "Team_FGA3.x", "Team_FTM.x", "Team_FTA.x", 
"Team_OR.x", "Team_DR.x", "Team_Ast.x", "Team_TO.x", "Team_STL.x", "Team_Blk.x", "Team_PF.x", "Opp_Score.x", "Opp_FGM.x", "Opp_FGA.x", 
"Opp_FGM3.x", "Opp_FGA3.x", "Opp_FTM.x", "Opp_FTA.x", "Opp_OR.x", "Opp_DR.x", "Opp_Ast.x", "Opp_TO.x", "Opp_STL.x", "Opp_Blk.x", 
"Opp_PF.x", "OTPlayed.x", "Team_Pace.x", "Team_ORtg.x", "Team_ORebPct.x", "Team_TSPct.x", "Team_TovPct.x", "Team_EffPct.x", "Team_FTr.x", "Team_FGPct.x", 
"Team_FG3Pct.x", "Team_FG2Pct.x", "Team_FTPct.x", "Opp_Pace.x", "Opp_ORtg.x", "Opp_ORebPct.x", "Opp_TSPct.x", "Opp_TovPct.x", "Opp_EffPct.x", "Opp_FTr.x", 
"Opp_FGPct.x", "Opp_FG3Pct.x", "Opp_FG2Pct.x", "Opp_FTPct.x", "Net_Score.x", "Net_FGM.x", "Net_FGA.x", "Net_FGM3.x", "Net_FGA3.x", "Net_FTM.x", 
"Net_FTA.x", "Net_OR.x", "Net_DR.x", "Net_Ast.x", "Net_TO.x", "Net_STL.x", "Net_Blk.x", "Net_PF.x", "Net_ORtg.x", "Net_ORebPct.x", 
"Net_TSPct.x", "Net_TovPct.x", "Net_EffPct.x", "Net_FTr.x", "Net_FGPct.x", "Net_FG3Pct.x", "Net_FG2Pct.x", "Net_FTPct.x", "R_Team_Score.x", "R_Team_FGM.x", 
"R_Team_FGA.x", "R_Team_FGPct.x", "R_Team_FGM3.x", "R_Team_FGA3.x", "R_Team_FG3Pct.x", "R_Team_FG2Pct.x", "R_Team_FTM.x", "R_Team_FTA.x", "R_Team_FTPct.x", "R_Team_FTr.x", 
"R_Team_OR.x", "R_Team_DR.x", "R_Team_ORebPct.x", "R_Team_Ast.x", "R_Team_TO.x", "R_Team_STL.x", "R_Team_Blk.x", "R_Team_PF.x", "R_Team_Pace.x", "R_Team_ORtg.x", 
"R_Team_TSPct.x", "R_Team_TovPct.x", "R_Team_EffPct.x", "R_Opp_Score.x", "R_Opp_FGM.x", "R_Opp_FGA.x", "R_Opp_FGPct.x", "R_Opp_FGM3.x", "R_Opp_FGA3.x", "R_Opp_FG3Pct.x", 
"R_Opp_FG2Pct.x", "R_Opp_FTM.x", "R_Opp_FTA.x", "R_Opp_FTPct.x", "R_Opp_FTr.x", "R_Opp_OR.x", "R_Opp_DR.x", "R_Opp_ORebPct.x", "R_Opp_Ast.x", "R_Opp_TO.x", 
"R_Opp_STL.x", "R_Opp_Blk.x", "R_Opp_PF.x", "R_Opp_Pace.x", "R_Opp_ORtg.x", "R_Opp_TSPct.x", "R_Opp_TovPct.x", "R_Opp_EffPct.x", "Cluster.x")

GamesTeamAverages <- rbind(GamesTeamAverages2,GamesTeamAverages3)

GamesTeamAverages <- GamesTeamAverages %>%
  mutate(Result = ifelse(TeamScore.x <= TeamScore.y, 0, 1))

GroupGamesList <- list()

for(i in 1:nrow(Combinations)) {
  Cluster1 <- Combinations$X1[i]
  Cluster2 <- Combinations$X2[i]
  Gender1 <- Combinations$Gender[i]
  ClusterName <- paste0("Cluster_",Cluster1,"_",Cluster2,"_",Gender1)
  TempTable1 <- GamesTeamAverages %>%
    filter(Cluster.x == Cluster1) %>%
    filter(Cluster.y == Cluster2) %>%
    filter(Gender == Gender1)
  TempTable2 <- GamesTeamAverages %>%
    filter(Cluster.x == Cluster2) %>%
    filter(Cluster.y == Cluster1) %>%
    filter(Gender == Gender1)
  TempTable3 <- rbind(TempTable1,TempTable2)
  TempTable3 <- TempTable3 %>%
    distinct()
  GroupGamesList[[ClusterName]] <- TempTable3
  print(i)}

remove(Combinations, TempTable1, TempTable2, TempTable3, Cluster1, Cluster2, ClusterName, i, GamesTeamAverages2, GamesTeamAverages3, Gender1)

ModelGamesList <- list()

for (i in 1:length(GroupGamesList)) {
  DataFrameName <- names(GroupGamesList)[i]
  ModelName <- sub("Cluster", "Model", DataFrameName)
  ModelGamesList[[ModelName]] <- glm(Result ~ Net_Score.x + Net_Score.y, data = GroupGamesList[[i]], family = binomial)}

FinalProduct <- read.csv("SampleSubmissionStage2.csv")
FinalProduct <- FinalProduct %>%
  separate(ID, into = c('Year', 'Lower', 'Upper'), sep = "_", remove = FALSE) %>%
  mutate(Year = as.numeric(Year),
         Lower = as.numeric(Lower),
         Upper = as.numeric(Upper),
         Gender = ifelse(Lower <= 2500, "Male", "Female")) %>%
  left_join(Y2026, by = c('Year' = 'Season', 'Lower' = 'TeamID', 'Gender')) %>%
  left_join(Y2026, by = c('Year' = 'Season', 'Upper' = 'TeamID', 'Gender'))

Combinations <- data.frame(t(combn(NClusters,2)))
X1 <- 1:NClusters
X2 <- 1:NClusters
Combinations2 <- data.frame(X1,X2)
Combinations <- rbind(Combinations, Combinations2)
Combinations <- rbind(Combinations,Combinations)
Combinations <- Combinations %>%
  mutate(Gender = c(rep("Male",nrow(Combinations)/2),rep("Female",nrow(Combinations)/2)))
remove(X1,X2,Combinations2)

PredictionsGamesList <- list()

for(i in 1:nrow(Combinations)) {
  Cluster1 <- Combinations$X1[i]
  Cluster2 <- Combinations$X2[i]
  Gender1 <- Combinations$Gender[i]
  ClusterName <- paste0("Cluster_",Cluster1,"_",Cluster2,"_",Gender1)
  TempTable1 <- FinalProduct %>%
    filter(Cluster.x == Cluster1) %>%
    filter(Cluster.y == Cluster2) %>%
    filter(Gender == Gender1)
  TempTable2 <- FinalProduct %>%
    filter(Cluster.x == Cluster2) %>%
    filter(Cluster.y == Cluster1) %>%
    filter(Gender == Gender1)
  TempTable3 <- rbind(TempTable1,TempTable2)
  TempTable3 <- TempTable3 %>%
    distinct()
  PredictionsGamesList[[ClusterName]] <- TempTable3
  print(i)}

for (i in 1:length(ModelGamesList)) {
  PredictionsGamesList[[i]]$Pred <- predict(ModelGamesList[[i]], PredictionsGamesList[[i]], type = "response")}

remove(Combinations, TempTable1, TempTable2, TempTable3, Cluster1, Cluster2, ClusterName, DataFrameName, Gender1, i, ModelName)

FinalProduct <- do.call(rbind, PredictionsGamesList)
FinalProduct <- FinalProduct %>%
  select(ID, Pred)

AllTeams <- TeamAverages %>%
  select(TeamName, Gender, TeamID) %>%
  distinct() %>%
  group_by(TeamName) %>%
  mutate(Total = n()) %>%
  filter(Total == 2) %>%
  select(-Total) %>%
  ungroup()

Round <- c(rep("First Four",4), rep("1st Round",32),rep("2nd Round", 16),rep("Sweet Sixteen", 8), rep("Elite Eight", 4), rep("Final Four", 2), rep("Championship", 1))

A <- sample(unique(AllTeams$TeamName), 68)
TeamA <- A[1:34]
TeamB <- A[35:68]
TeamA <- c(TeamA, rep(NA,33))
TeamB <- c(TeamB, rep(NA,33))

Bracket <- data.frame(Round, TeamA, TeamB)
Bracket <- rbind(Bracket,Bracket)
Bracket <- Bracket %>%
  mutate(Gender = c(rep("Male",67), rep("Female", 67)),
         Matchup = 1:134)
SimGame <- function(Bracket2,GameID) {
  Game <- Bracket2 %>%
    filter(Matchup == GameID) %>%
    left_join(AllTeams, by = c('TeamA' = 'TeamName', 'Gender')) %>%
    left_join(AllTeams, by = c('TeamB' = 'TeamName', 'Gender')) %>%
    mutate(Lower = ifelse(TeamID.x <= TeamID.y, TeamID.x, TeamID.y),
           Upper = ifelse(TeamID.x <= TeamID.y, TeamID.y, TeamID.x),
           LowerT = ifelse(TeamID.x <= TeamID.y, TeamA, TeamB),
           UpperT = ifelse(TeamID.x <= TeamID.y, TeamB, TeamA),
           ID = paste0("2026_",Lower,"_",Upper)) %>%
    left_join(FinalProduct, by = c('ID')) %>%
    mutate(Result = runif(1,0,1),
           Result = ifelse(Result <= Pred, LowerT, UpperT),
           Result = ifelse(is.na(Result) == T, LowerT, Result)) %>%
    select(Result) %>%
    pull()
  return(Game)}
SimTourney <- function(Bracket2, SimNumber) {
  Bracket3 <- Bracket2
  Bracket3$TeamA[35] <- SimGame(Bracket3, 1)
  Bracket3$TeamB[35] <- SimGame(Bracket3, 2)
  Bracket3$TeamA[36] <- SimGame(Bracket3, 3)
  Bracket3$TeamB[36] <- SimGame(Bracket3, 4)
  Bracket3$TeamA[37] <- SimGame(Bracket3, 5)
  Bracket3$TeamB[37] <- SimGame(Bracket3, 6)
  Bracket3$TeamA[38] <- SimGame(Bracket3, 7)
  Bracket3$TeamB[38] <- SimGame(Bracket3, 8)
  Bracket3$TeamA[39] <- SimGame(Bracket3, 9)
  Bracket3$TeamB[39] <- SimGame(Bracket3, 10)
  Bracket3$TeamA[40] <- SimGame(Bracket3, 11)
  Bracket3$TeamB[40] <- SimGame(Bracket3, 12)
  Bracket3$TeamA[41] <- SimGame(Bracket3, 13)
  Bracket3$TeamB[41] <- SimGame(Bracket3, 14)
  Bracket3$TeamA[42] <- SimGame(Bracket3, 15)
  Bracket3$TeamB[42] <- SimGame(Bracket3, 16)
  Bracket3$TeamA[43] <- SimGame(Bracket3, 17)
  Bracket3$TeamB[43] <- SimGame(Bracket3, 18)
  Bracket3$TeamA[44] <- SimGame(Bracket3, 19)
  Bracket3$TeamB[44] <- SimGame(Bracket3, 20)
  Bracket3$TeamA[45] <- SimGame(Bracket3, 21)
  Bracket3$TeamB[45] <- SimGame(Bracket3, 22)
  Bracket3$TeamA[46] <- SimGame(Bracket3, 23)
  Bracket3$TeamB[46] <- SimGame(Bracket3, 24)
  Bracket3$TeamA[47] <- SimGame(Bracket3, 25)
  Bracket3$TeamB[47] <- SimGame(Bracket3, 26)
  Bracket3$TeamA[48] <- SimGame(Bracket3, 27)
  Bracket3$TeamB[48] <- SimGame(Bracket3, 28)
  Bracket3$TeamA[49] <- SimGame(Bracket3, 29)
  Bracket3$TeamB[49] <- SimGame(Bracket3, 30)
  Bracket3$TeamA[50] <- SimGame(Bracket3, 31)
  Bracket3$TeamB[50] <- SimGame(Bracket3, 32)
  Bracket3$TeamA[51] <- SimGame(Bracket3, 33)
  Bracket3$TeamB[51] <- SimGame(Bracket3, 34)
  Bracket3$TeamA[52] <- SimGame(Bracket3, 35)
  Bracket3$TeamB[52] <- SimGame(Bracket3, 36)
  Bracket3$TeamA[53] <- SimGame(Bracket3, 37)
  Bracket3$TeamB[53] <- SimGame(Bracket3, 38)
  Bracket3$TeamA[54] <- SimGame(Bracket3, 39)
  Bracket3$TeamB[54] <- SimGame(Bracket3, 40)
  Bracket3$TeamA[55] <- SimGame(Bracket3, 41)
  Bracket3$TeamB[55] <- SimGame(Bracket3, 42)
  Bracket3$TeamA[56] <- SimGame(Bracket3, 43)
  Bracket3$TeamB[56] <- SimGame(Bracket3, 44)
  Bracket3$TeamA[57] <- SimGame(Bracket3, 45)
  Bracket3$TeamB[57] <- SimGame(Bracket3, 46)
  Bracket3$TeamA[58] <- SimGame(Bracket3, 47)
  Bracket3$TeamB[58] <- SimGame(Bracket3, 48)
  Bracket3$TeamA[59] <- SimGame(Bracket3, 49)
  Bracket3$TeamB[59] <- SimGame(Bracket3, 50)
  Bracket3$TeamA[60] <- SimGame(Bracket3, 51)
  Bracket3$TeamB[60] <- SimGame(Bracket3, 52)
  Bracket3$TeamA[61] <- SimGame(Bracket3, 53)
  Bracket3$TeamB[61] <- SimGame(Bracket3, 54)
  Bracket3$TeamA[62] <- SimGame(Bracket3, 55)
  Bracket3$TeamB[62] <- SimGame(Bracket3, 56)
  Bracket3$TeamA[63] <- SimGame(Bracket3, 57)
  Bracket3$TeamB[63] <- SimGame(Bracket3, 58)
  Bracket3$TeamA[64] <- SimGame(Bracket3, 59)
  Bracket3$TeamB[64] <- SimGame(Bracket3, 60)
  Bracket3$TeamA[65] <- SimGame(Bracket3, 61)
  Bracket3$TeamB[65] <- SimGame(Bracket3, 62)
  Bracket3$TeamA[66] <- SimGame(Bracket3, 63)
  Bracket3$TeamB[66] <- SimGame(Bracket3, 64)
  Bracket3$TeamA[67] <- SimGame(Bracket3, 65)
  Bracket3$TeamB[67] <- SimGame(Bracket3, 66)
  Bracket3$TeamA[102] <- SimGame(Bracket3, 68)
  Bracket3$TeamB[102] <- SimGame(Bracket3, 69)
  Bracket3$TeamA[103] <- SimGame(Bracket3, 70)
  Bracket3$TeamB[103] <- SimGame(Bracket3, 71)
  Bracket3$TeamA[104] <- SimGame(Bracket3, 72)
  Bracket3$TeamB[104] <- SimGame(Bracket3, 73)
  Bracket3$TeamA[105] <- SimGame(Bracket3, 74)
  Bracket3$TeamB[105] <- SimGame(Bracket3, 75)
  Bracket3$TeamA[106] <- SimGame(Bracket3, 76)
  Bracket3$TeamB[106] <- SimGame(Bracket3, 77)
  Bracket3$TeamA[107] <- SimGame(Bracket3, 78)
  Bracket3$TeamB[107] <- SimGame(Bracket3, 79)
  Bracket3$TeamA[108] <- SimGame(Bracket3, 80) 
  Bracket3$TeamB[108] <- SimGame(Bracket3, 81)
  Bracket3$TeamA[109] <- SimGame(Bracket3, 82) 
  Bracket3$TeamB[109] <- SimGame(Bracket3, 83)
  Bracket3$TeamA[110] <- SimGame(Bracket3, 84)
  Bracket3$TeamB[110] <- SimGame(Bracket3, 85)
  Bracket3$TeamA[111] <- SimGame(Bracket3, 86)
  Bracket3$TeamB[111] <- SimGame(Bracket3, 87)
  Bracket3$TeamA[112] <- SimGame(Bracket3, 88)
  Bracket3$TeamB[112] <- SimGame(Bracket3, 89) 
  Bracket3$TeamA[113] <- SimGame(Bracket3, 90)
  Bracket3$TeamB[113] <- SimGame(Bracket3, 91)
  Bracket3$TeamA[114] <- SimGame(Bracket3, 92)
  Bracket3$TeamB[114] <- SimGame(Bracket3, 93)
  Bracket3$TeamA[115] <- SimGame(Bracket3, 94)
  Bracket3$TeamB[115] <- SimGame(Bracket3, 95)
  Bracket3$TeamA[116] <- SimGame(Bracket3, 96)
  Bracket3$TeamB[116] <- SimGame(Bracket3, 97)
  Bracket3$TeamA[117] <- SimGame(Bracket3, 98)
  Bracket3$TeamB[117] <- SimGame(Bracket3, 99)
  Bracket3$TeamA[118] <- SimGame(Bracket3, 100)
  Bracket3$TeamB[118] <- SimGame(Bracket3, 101)
  Bracket3$TeamA[119] <- SimGame(Bracket3, 102)
  Bracket3$TeamB[119] <- SimGame(Bracket3, 103)
  Bracket3$TeamA[120] <- SimGame(Bracket3, 104)
  Bracket3$TeamB[120] <- SimGame(Bracket3, 105)
  Bracket3$TeamA[121] <- SimGame(Bracket3, 106)
  Bracket3$TeamB[121] <- SimGame(Bracket3, 107)
  Bracket3$TeamA[122] <- SimGame(Bracket3, 108)
  Bracket3$TeamB[122] <- SimGame(Bracket3, 109)
  Bracket3$TeamA[123] <- SimGame(Bracket3, 110)
  Bracket3$TeamB[123] <- SimGame(Bracket3, 111)
  Bracket3$TeamA[124] <- SimGame(Bracket3, 112)
  Bracket3$TeamB[124] <- SimGame(Bracket3, 113)
  Bracket3$TeamA[125] <- SimGame(Bracket3, 114)
  Bracket3$TeamB[125] <- SimGame(Bracket3, 115)
  Bracket3$TeamA[126] <- SimGame(Bracket3, 116)
  Bracket3$TeamB[126] <- SimGame(Bracket3, 117)
  Bracket3$TeamA[127] <- SimGame(Bracket3, 118)
  Bracket3$TeamB[127] <- SimGame(Bracket3, 119)
  Bracket3$TeamA[128] <- SimGame(Bracket3, 120)
  Bracket3$TeamB[128] <- SimGame(Bracket3, 121)
  Bracket3$TeamA[129] <- SimGame(Bracket3, 122)
  Bracket3$TeamB[129] <- SimGame(Bracket3, 123)
  Bracket3$TeamA[130] <- SimGame(Bracket3, 124)
  Bracket3$TeamB[130] <- SimGame(Bracket3, 125)
  Bracket3$TeamA[131] <- SimGame(Bracket3, 126)
  Bracket3$TeamB[131] <- SimGame(Bracket3, 127)
  Bracket3$TeamA[132] <- SimGame(Bracket3, 128)
  Bracket3$TeamB[132] <- SimGame(Bracket3, 129)
  Bracket3$TeamA[133] <- SimGame(Bracket3, 130)
  Bracket3$TeamB[133] <- SimGame(Bracket3, 131)
  Bracket3$TeamA[134] <- SimGame(Bracket3, 132)
  Bracket3$TeamB[134] <- SimGame(Bracket3, 133)
  Sim <- SimNumber
  Results <- data.frame(Sim)
  Results <- Results %>%
    mutate(M_PI_1 = Bracket3$TeamA[35],
           M_PI_2 = Bracket3$TeamB[35],
           M_PI_3 = Bracket3$TeamA[36],
           M_PI_4 = Bracket3$TeamB[36],
           M_R32_1 = Bracket3$TeamA[37],
           M_R32_2 = Bracket3$TeamB[37],
           M_R32_3 = Bracket3$TeamA[38],
           M_R32_4 = Bracket3$TeamB[38],
           M_R32_5 = Bracket3$TeamA[39],
           M_R32_6 = Bracket3$TeamB[39],
           M_R32_7 = Bracket3$TeamA[40],
           M_R32_8 = Bracket3$TeamB[40],
           M_R32_9 = Bracket3$TeamA[41],
           M_R32_10 = Bracket3$TeamB[41],
           M_R32_11 = Bracket3$TeamA[42],
           M_R32_12 = Bracket3$TeamB[42],
           M_R32_13 = Bracket3$TeamA[43],
           M_R32_14 = Bracket3$TeamB[43],
           M_R32_15 = Bracket3$TeamA[44],
           M_R32_16 = Bracket3$TeamB[44],
           M_R32_17 = Bracket3$TeamA[45],
           M_R32_18 = Bracket3$TeamB[45],
           M_R32_19 = Bracket3$TeamA[46],
           M_R32_20 = Bracket3$TeamB[46],
           M_R32_21 = Bracket3$TeamA[47],
           M_R32_22 = Bracket3$TeamB[47],
           M_R32_23 = Bracket3$TeamA[48],
           M_R32_24 = Bracket3$TeamB[48],
           M_R32_25 = Bracket3$TeamA[49],
           M_R32_26 = Bracket3$TeamB[49],
           M_R32_27 = Bracket3$TeamA[50],
           M_R32_28 = Bracket3$TeamB[50],
           M_R32_29 = Bracket3$TeamA[51],
           M_R32_30 = Bracket3$TeamB[51],
           M_R32_31 = Bracket3$TeamA[52],
           M_R32_32 = Bracket3$TeamB[52],
           M_S16_1 = Bracket3$TeamA[53],
           M_S16_2 = Bracket3$TeamB[53],
           M_S16_3 = Bracket3$TeamA[54],
           M_S16_4 = Bracket3$TeamB[54],
           M_S16_5 = Bracket3$TeamA[55],
           M_S16_6 = Bracket3$TeamB[55],
           M_S16_7 = Bracket3$TeamA[56],
           M_S16_8 = Bracket3$TeamB[56],
           M_S16_9 = Bracket3$TeamA[57],
           M_S16_10 = Bracket3$TeamB[57],
           M_S16_11 = Bracket3$TeamA[58],
           M_S16_12 = Bracket3$TeamB[58],
           M_S16_13 = Bracket3$TeamA[59],
           M_S16_14 = Bracket3$TeamB[59],
           M_S16_15 = Bracket3$TeamA[60],
           M_S16_16 = Bracket3$TeamB[60],
           M_E8_1 = Bracket3$TeamA[61],
           M_E8_2 = Bracket3$TeamB[61],
           M_E8_3 = Bracket3$TeamA[62],
           M_E8_4 = Bracket3$TeamB[62],
           M_E8_5 = Bracket3$TeamA[63],
           M_E8_6 = Bracket3$TeamB[63],
           M_E8_7 = Bracket3$TeamA[64],
           M_E8_8 = Bracket3$TeamB[64],
           M_F4_1 = Bracket3$TeamA[65],
           M_F4_2 = Bracket3$TeamB[65],
           M_F4_3 = Bracket3$TeamA[66],
           M_F4_4 = Bracket3$TeamB[66],
           M_C2_1 = Bracket3$TeamA[67],
           M_C2_2 = Bracket3$TeamB[67],
           M_Champ = SimGame(Bracket3, 67),
           W_PI_1 = Bracket3$TeamA[102],
           W_PI_2 = Bracket3$TeamB[102],
       W_PI_3 = Bracket3$TeamA[103],
       W_PI_4 = Bracket3$TeamB[103],
       W_R32_1 = Bracket3$TeamA[104],
       W_R32_2 = Bracket3$TeamB[104],
       W_R32_3 = Bracket3$TeamA[105],
       W_R32_4 = Bracket3$TeamB[105],
       W_R32_5 = Bracket3$TeamA[106],
       W_R32_6 = Bracket3$TeamB[106],
       W_R32_7 = Bracket3$TeamA[107],
       W_R32_8 = Bracket3$TeamB[107],
       W_R32_9 = Bracket3$TeamA[108],
       W_R32_10 = Bracket3$TeamB[108],
       W_R32_11 = Bracket3$TeamA[109],
       W_R32_12 = Bracket3$TeamB[109],
       W_R32_13 = Bracket3$TeamA[110],
       W_R32_14 = Bracket3$TeamB[110],
       W_R32_15 = Bracket3$TeamA[111],
       W_R32_16 = Bracket3$TeamB[111],
       W_R32_17 = Bracket3$TeamA[112],
       W_R32_18 = Bracket3$TeamB[112],
       W_R32_19 = Bracket3$TeamA[113],
       W_R32_20 = Bracket3$TeamB[113],
       W_R32_21 = Bracket3$TeamA[114],
       W_R32_22 = Bracket3$TeamB[114],
       W_R32_23 = Bracket3$TeamA[115],
       W_R32_24 = Bracket3$TeamB[115],
       W_R32_25 = Bracket3$TeamA[116],
       W_R32_26 = Bracket3$TeamB[116],
       W_R32_27 = Bracket3$TeamA[117],
       W_R32_28 = Bracket3$TeamB[117],
       W_R32_29 = Bracket3$TeamA[118],
       W_R32_30 = Bracket3$TeamB[118],
       W_R32_31 = Bracket3$TeamA[119],
       W_R32_32 = Bracket3$TeamB[119],
       W_S16_1 = Bracket3$TeamA[120],
       W_S16_2 = Bracket3$TeamB[120],
       W_S16_3 = Bracket3$TeamA[121],
       W_S16_4 = Bracket3$TeamB[121],
       W_S16_5 = Bracket3$TeamA[122],
       W_S16_6 = Bracket3$TeamB[122],
       W_S16_7 = Bracket3$TeamA[123],
       W_S16_8 = Bracket3$TeamB[123],
       W_S16_9 = Bracket3$TeamA[124],
       W_S16_10 = Bracket3$TeamB[124],
       W_S16_11 = Bracket3$TeamA[125],
       W_S16_12 = Bracket3$TeamB[125],
       W_S16_13 = Bracket3$TeamA[126],
       W_S16_14 = Bracket3$TeamB[126],
       W_S16_15 = Bracket3$TeamA[127],
       W_S16_16 = Bracket3$TeamB[127],
       W_E8_1 = Bracket3$TeamA[128],
       W_E8_2 = Bracket3$TeamB[128],
       W_E8_3 = Bracket3$TeamA[129],
       W_E8_4 = Bracket3$TeamB[129],
       W_E8_5 = Bracket3$TeamA[130],
       W_E8_6 = Bracket3$TeamB[130],
       W_E8_7 = Bracket3$TeamA[131],
       W_E8_8 = Bracket3$TeamB[131],
       W_F4_1 = Bracket3$TeamA[132],
       W_F4_2 = Bracket3$TeamB[132],
       W_F4_3 = Bracket3$TeamA[133],
       W_F4_4 = Bracket3$TeamB[133],
       W_C2_1 = Bracket3$TeamA[134],
       W_C2_2 = Bracket3$TeamB[134],
       W_Champ = SimGame(Bracket3, 134))

  
  return(Results)}

AllResults <- data.frame()
for(i in 1:100) {
  Simulation <- SimTourney(Bracket, i)
  AllResults <- rbind(AllResults,Simulation)
  print(i)}

Games <- Games %>%
  mutate(Net_Score = Win_Score-Lose_Score,
         Net_FGM = Win_FGM-Lose_FGM,
         Net_FGA = Win_FGA-Lose_FGA,
         Net_FGM3 = Win_FGM3-Lose_FGM3,
         Net_FGA3 = Win_FGA3-Lose_FGA3,
         Net_FTM = Win_FTM-Lose_FTM,
         Net_FTA = Win_FTA-Lose_FTA,
         Net_OR = Win_OR-Lose_OR,
         Net_DR = Win_DR-Lose_DR,
         Net_Ast = Win_Ast-Lose_Ast,
         Net_TO = Win_TO-Lose_TO,
         Net_STL = Win_Stl-Lose_Stl,
         Net_Blk = Win_Blk-Lose_Blk,
         Net_PF = Win_PF-Lose_PF,
         Net_ORtg = Win_ORtg-Lose_ORtg,
         Net_ORebPct = Win_ORebPct-Lose_ORebPct,
         Net_TSPct = Win_TSPct-Lose_TSPct,
         Net_TovPct = Win_TovPct-Lose_TovPct,
         Net_EffPct = Win_EffPct-Lose_EffPct,
         Net_FTr = Win_FTr-Lose_FTr,
         Net_FGPct = Win_FGPct-Lose_FGPct,
         Net_FG3Pct = Win_FG3Pct-Lose_FG3Pct,
         Net_FG2Pct = Win_FG2Pct-Lose_FG2Pct,
         Net_FTPct = Win_FTPct-Lose_FTPct)

TeamAverages2 <- rbind(TeamAverages,Y2026)

write.csv(Games, "C:/Users/mppac/Downloads/AllGames.csv", row.names = FALSE)
write.csv(TeamAverages2, "C:/Users/mppac/Downloads/TeamAverages.csv", row.names = FALSE)