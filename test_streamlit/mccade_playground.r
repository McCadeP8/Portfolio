library(tidyverse)
library(rvest)

McCadeP8_theme_colors <- c(
  background = '#0D1117',   # dark slate gray (background)
  text       = '#F0F3F5',   # very light gray (text)
  panel      = '#1C1F26',   # near-black with blue hint (panel)
  border     = '#3E92CC',   # strong blue (border)
  strip_text = '#0D1117',   # matches background (strip text on light facet)
  lighter    = '#C3DDFD',   # baby blue
  light      = '#6FB1FC',   # sky blue
  medium     = '#326DA8',   # Jazz navy
  dark       = '#1D3557'    # deep indigo/navy
)

McCadeP8_palette <- c(
  '#C3DDFD', '#F94144', '#6A4C93', '#F9C74F', '#43AA8B',
  '#577590', '#F3722C', '#277DA1', '#264653'
)

## McCade Pearson
## theme_McCadeP8
## Date Created: June 10, 2025

# THEME COLOR PALETTE --------------------------------------

#' McCadeP8 Inspired Theme Color Palette
#'
#' @format character vector of hex code strings
#' @export
#' @concept McCadeP8
#'
McCadeP8_theme_colors <- c(
  background = '#0D1117',
  text       = '#F0F3F5',
  panel      = '#1C1F26',
  border     = '#3E92CC',
  strip_text = '#0D1117',
  lighter    = '#C3DDFD',
  light      = '#6FB1FC',
  medium     = '#326DA8',
  dark       = '#1D3557'
)

# DISCRETE COLOR PALETTE -----------------------------------

#' McCadeP8 Inspired Color Palette
#'
#' @format character vector of hex code strings
#' @export
#' @concept McCadeP8
#'
McCadeP8_palette <- c(
  '#C3DDFD', '#F94144', '#6A4C93', '#F9C74F', '#43AA8B',
  '#577590', '#F3722C', '#277DA1', '#264653'
)

# MAIN THEME ------------------------------------------------

#' McCadeP8 Inspired Theme
#'
#' @param McCadeP8_font should `theme_McCadeP8` use custom font? Default is `TRUE`.
#' @param ... additional parameters to pass to `ggplot2::theme()`
#'
#' @return a `ggplot2` `theme` object
#' @export
#' @concept McCadeP8
#'
theme_McCadeP8 <- function(McCadeP8_font = TRUE, ...) {

  # Load custom Google Font
  font_family <- ifelse(McCadeP8_font, "Barlow Semi Condensed", "sans")
  if (McCadeP8_font) {
  font_add_google(name = "Barlow Semi Condensed", family = "Barlow Semi Condensed")
  showtext_auto()
  }

  # Define the theme
  ggplot2::theme(
    plot.background = element_rect(fill = McCadeP8_theme_colors["background"], color = NA),
    panel.background = element_rect(fill = McCadeP8_theme_colors["panel"], color = NA),
    panel.border = element_rect(color = McCadeP8_theme_colors["border"], fill = NA, linewidth = 1.2),
    panel.grid.major = element_line(color = "#2D3748", size = 0.25),
    panel.grid.minor = element_blank(),
    
    text = element_text(color = McCadeP8_theme_colors["text"], family = font_family),
    title = element_text(size = 20, face = "bold", hjust = 0.5),
    axis.title = element_text(size = 17),
    axis.text = element_text(size = 13, color = McCadeP8_theme_colors["text"]),
    axis.ticks = element_line(color = McCadeP8_theme_colors["border"], linewidth = 1),
    
    legend.background = element_rect(fill = McCadeP8_theme_colors["panel"], color = NA),
    legend.text = element_text(size = 12),
    legend.title = element_text(size = 14, face = "bold"),
    
    strip.background = element_rect(fill = McCadeP8_theme_colors["lighter"], colour = McCadeP8_theme_colors["border"]),
    strip.text = element_text(colour = McCadeP8_theme_colors["strip_text"], size = 10)
  )
}

# COLOR SCALES ---------------------------------------------

#' McCadeP8 Inspired Color Scales
#'
#' @param ... Additional arguments to pass to `ggplot2::binned_scale` for `_b`,
#' `ggplot2::scale_[fill/color]_gradient` for `_c`, or `ggplot2::discrete_scale`
#' for `_d`
#'
#' @rdname scale_McCadeP8
#' @export
scale_color_McCadeP8_c <- function(...) {
  ggplot2::scale_color_gradient(..., low = McCadeP8_theme_colors["light"], high = McCadeP8_theme_colors["dark"])
}

#' @rdname scale_McCadeP8
#' @export
scale_fill_McCadeP8_c <- function(...) {
  ggplot2::scale_fill_gradient(..., low = McCadeP8_theme_colors["light"], high = McCadeP8_theme_colors["dark"])
}

#' @rdname scale_McCadeP8
#' @export
scale_color_McCadeP8_b <- function(...) {
  if (!requireNamespace('scales', quietly = TRUE)) {
    stop('This function requires the `scales` R package.')
  }
  ramp <- scales::colour_ramp(c(McCadeP8_theme_colors["light"], McCadeP8_theme_colors["dark"]))
  ggplot2::binned_scale('color', 'McCadeP8', palette = ramp, ...)
}

#' @rdname scale_McCadeP8
#' @export
scale_fill_McCadeP8_b <- function(...) {
  if (!requireNamespace('scales', quietly = TRUE)) {
    stop('This function requires the `scales` R package.')
  }
  ramp <- scales::colour_ramp(c(McCadeP8_theme_colors["light"], McCadeP8_theme_colors["dark"]))
  ggplot2::binned_scale('fill', 'McCadeP8', palette = ramp, ...)
}

#' @rdname scale_McCadeP8
#' @export
scale_color_McCadeP8_d <- function(...) {
  ggplot2::discrete_scale(aesthetics = 'color',
                          palette = rot_pal(McCadeP8_palette), ...)
}

#' @rdname scale_McCadeP8
#' @export
scale_fill_McCadeP8_d <- function(...) {
  ggplot2::discrete_scale(aesthetics = 'fill',
                          palette = rot_pal(McCadeP8_palette), ...)
}

# Aliases
#' @rdname scale_McCadeP8
#' @export
scale_colour_McCadeP8_d <- scale_color_McCadeP8_d
#' @rdname scale_McCadeP8
#' @export
scale_colour_McCadeP8_c <- scale_color_McCadeP8_c
#' @rdname scale_McCadeP8
#' @export
scale_colour_McCadeP8_b <- scale_color_McCadeP8_b


url <- "https://www.basketball-reference.com/leagues/NBA_2026_totals.html"
page <- read_html(url)
totals <- page %>%
  html_node("#totals_stats") %>%
  html_table(fill = TRUE) %>%
  select(Player, Team, MP, FTA, `3P`) %>%
  mutate(MP = as.numeric(MP),
         FTA = as.numeric(FTA),
         `3P` = as.numeric(`3P`))

url <- "https://www.basketball-reference.com/leagues/NBA_2026_shooting.html"
page <- read_html(url)
shooting <- page %>%
  html_node("#shooting") %>%
  html_table(fill = TRUE)
colnames(shooting) <- make.names(as.character(shooting[1, ]), unique = TRUE)
shooting <- shooting[-1, ] %>%
  mutate(Dunks = as.numeric(X.)) %>%
  select(Player, Team, Dunks) %>%
  left_join(totals, by = c("Player", "Team")) %>%
  mutate(DunksP36 = Dunks / MP * 36,
         FTAP36 = FTA / MP * 36,
         ThPMP36 = `3P` / MP * 36) %>%
  filter(MP >= 500) %>%
  mutate(AceBailey = ifelse(Player == "Ace Bailey", "#31006F", "#6FB1FC"))

ace <- shooting %>% 
  filter(Player == "Ace Bailey")

ggplot(shooting, aes(x = FTAP36, y = DunksP36)) +
  geom_point(color = shooting$AceBailey, size = 3) +
  geom_label_repel(
    data = ace,
    aes(label = paste0(
      "Ace Bailey\n",
      round(FTAP36,2), " FTA/36\n",
      round(DunksP36,2), " Dunks/36")),
    arrow = arrow(length = unit(0.02, "npc")),
    nudge_x = 1,
    nudge_y = 1) +
  scale_x_continuous(
    breaks = pretty_breaks(),
    labels = label_number(accuracy = 1)) +
  scale_y_continuous(
    breaks = pretty_breaks(),
    labels = label_number(accuracy = 1)) +
  labs(
    title = "Dunks and Frees",
    subtitle = "Players who dunk more often also tend to generate more trips to the line",
    caption = "@McCadeP8 | Data: basketball-reference.com",
    x = "Free Throw Attempts per 36 Minutes",
    y = "Dunks per 36 Minutes"
  ) +
  
  theme_McCadeP8() +
  theme(aspect.ratio = 0.616)








ggplot(shooting, aes(x = ThPMP36, y = DunksP36)) +
  geom_point(color = shooting$AceBailey, size = 3) +
  geom_label_repel(
    data = ace,
    aes(label = paste0(
      "Ace Bailey\n",
      round(ThPMP36,2), " 3PM/36\n",
      round(DunksP36,2), " Dunks/36")),
    arrow = arrow(length = unit(0.02, "npc")),
    nudge_x = 1,
    nudge_y = 1) +
  scale_x_continuous(
    breaks = pretty_breaks(),
    labels = label_number(accuracy = 1)) +
  scale_y_continuous(
    breaks = pretty_breaks(),
    labels = label_number(accuracy = 1)) +
  labs(
    title = "Dunks and Threes",
    subtitle = "Getting the most effecient shots all over the floor is a winning strategy",
    caption = "@McCadeP8 | Data: basketball-reference.com",
    x = "Three-Pointers Made per 36 Minutes",
    y = "Dunks per 36 Minutes"
  ) +
  
  theme_McCadeP8() +
  theme(aspect.ratio = 0.616)
library(httr)
library(jsonlite)
library(dplyr)
library(purrr)

### --------------------------------------------
### STEP 1. Pull schedule and game IDs
### --------------------------------------------

schedule_url <- "https://api-web.nhle.com/v1/schedule/2024-10-01"

schedule_data <- fromJSON(schedule_url, simplifyVector = FALSE)

games <- map_dfr(schedule_data$gameWeek, function(week){

  if(length(week$games) == 0) return(NULL)

  map_dfr(week$games, function(g){
    data.frame(
      id = g$id
    )
  })

})

game_ids <- unique(games$id)

### --------------------------------------------
### STEP 2. Function to get shots by period for one game
### --------------------------------------------

get_game_shots <- function(game_id){

  url <- paste0("https://api-web.nhle.com/v1/gamecenter/", game_id, "/boxscore")

  tryCatch({

    data <- fromJSON(url, simplifyVector = FALSE)

    home_team <- data$homeTeam$abbrev
    away_team <- data$awayTeam$abbrev

    home_shots <- data$homeTeam$sogByPeriod
    away_shots <- data$awayTeam$sogByPeriod

    game_date <- data$gameDate

    home_df <- data.frame(
      game_id = game_id,
      game_date = game_date,
      team = home_team,
      opponent = away_team,
      period = seq_along(home_shots),
      shots_on_goal = home_shots
    )

    away_df <- data.frame(
      game_id = game_id,
      game_date = game_date,
      team = away_team,
      opponent = home_team,
      period = seq_along(away_shots),
      shots_on_goal = away_shots
    )

    bind_rows(home_df, away_df)

  }, error = function(e){
    return(NULL)
  })
}

### --------------------------------------------
### STEP 3. Pull all games
### --------------------------------------------

shots_by_period <- map_dfr(game_ids, get_game_shots)

### --------------------------------------------
### STEP 4. Clean dataset
### --------------------------------------------

shots_by_period <- shots_by_period %>%
  filter(period <= 3) %>%   # remove overtime if you want only regulation
  arrange(team, game_date, period)

### --------------------------------------------
### OUTPUT
### --------------------------------------------

shots_by_period