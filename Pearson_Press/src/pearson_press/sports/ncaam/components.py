"""College basketball components built on the shared basketball layout."""

from pearson_press.sports.nba.components import (
    PlayerLine as CollegeBasketballPlayerLine,
)
from pearson_press.sports.nba.components import (
    SimpleBoxScore as CollegeBasketballSimpleBoxScore,
)
from pearson_press.sports.nba.components import (
    TeamBox as CollegeBasketballTeamBox,
)
from pearson_press.sports.nba.components import (
    draw_simple_box_score as draw_college_basketball_simple_box_score,
)

__all__ = (
    "CollegeBasketballPlayerLine",
    "CollegeBasketballSimpleBoxScore",
    "CollegeBasketballTeamBox",
    "draw_college_basketball_simple_box_score",
)
