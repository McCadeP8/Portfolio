Number <- 126714599
Repeater <- T

TaxAmount <- function(Number,Repeater) {
  TaxNumber <- rep(Number,100)
  Repeater2 <- rep(Repeater,100)
  Slot <- 1:100
  Group <- rep(1,100)
  Penalty1 <- c(1.00,0.25,2.25,1.25,rep(0.5,96))
  Penalty2 <- c(3.00,0.25,2.25,1.25,rep(0.5,96))
  TaxNumber <- data.frame(Group,Slot,TaxNumber,Repeater,Penalty1,Penalty2)
  TaxNumber <- TaxNumber %>%
    mutate(TaxNumber = TaxNumber-(5168000*(Slot-1))) %>%
    filter(TaxNumber >= 0) %>%
    mutate(Penalty3 = ifelse(Repeater == TRUE, Penalty2, Penalty1),
           TaxCost = TaxNumber*Penalty3) %>%
    group_by(Group) %>%
    summarize(TaxCost = sum(TaxCost)) %>%
    select(TaxCost) %>%
    pull()
  TaxNumber <- ifelse(length(TaxNumber) == 0, 0, TaxNumber)
  return(TaxNumber)}

A <- Players %>%
  mutate(Type2026 = ifelse(Type2026 %in% c('Non-Guaranteed', 'Guaranteed', 'Dead'), 'Salary', Type2026)) %>%
  group_by(Team, Type2026) %>%
  summarize(Total = sum(Y2026)) %>%
  pivot_wider(names_from = Type2026, values_from = Total) %>%
  select(Team, Salary, Unrestricted, Restricted) %>%
  mutate(Tier = case_when(Salary <= 154600000 ~ "Tier 1",
                          Salary <= 195900000 ~ "Tier 2",
                          Salary <= 207800000 ~ "Tier 3",
                          Salary > 207800000 ~ "Tier 4")) %>%
  ungroup() %>%
  mutate(CurrentCost = Salary / 3000000) %>%
  rowwise() %>%
  mutate(TaxY = TaxAmount(Salary - 187895000, TRUE),
         TaxN = TaxAmount(Salary - 187895000, FALSE),
         TaxY = TaxY/3000000,
         TaxN = TaxN/3000000) %>%
  ungroup() %>%
  arrange(-Salary) %>%
  group_by(Tier) %>%
  gt() %>%
  gt_theme_espn() %>%
  cols_align(align = "center") %>%
  tab_spanner(label = "Team Cost", columns = c(Salary, Unrestricted, Restricted)) %>%
  tab_spanner(label = "Entry Fee Costs", columns = c(CurrentCost, TaxY, TaxN)) %>%
  tab_header(title = "Quick Outlook on Free Agency", subtitle = "If every team renounces all free agents — which obviously won't happen. So most teams will likely be a tier higher than it shows.") %>%
  tab_source_note(source_note = "Entry fees will be raised to 90% of the salary cap and a $3 In-Season tournament fee is also added")

gtsave(A, "GT.png")
