"""College football components built on the shared football box-score layout."""

from pearson_press.sports.nfl.components import (
    NFLPlayerLine as CollegeFootballPlayerLine,
)
from pearson_press.sports.nfl.components import (
    NFLSimpleBoxScore as CollegeFootballSimpleBoxScore,
)
from pearson_press.sports.nfl.components import (
    NFLTeamBox as CollegeFootballTeamBox,
)
from pearson_press.sports.nfl.components import (
    draw_nfl_simple_box_score as draw_college_football_simple_box_score,
)

__all__ = (
    "CollegeFootballPlayerLine",
    "CollegeFootballSimpleBoxScore",
    "CollegeFootballTeamBox",
    "draw_college_football_simple_box_score",
)
