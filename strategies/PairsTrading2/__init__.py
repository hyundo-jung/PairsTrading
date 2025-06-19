from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils


class PairsTrading2(Strategy):
    def should_long(self) -> bool:
        return self.shared_vars["s2-position"] == 1

    def should_short(self) -> bool:
        # For futures trading only
        return self.shared_vars["s2-position"] == -1
        
    def go_long(self):
        pass

    def go_short(self):
        # For futures trading only
        pass

    def update_position(self):
        if self.shared_vars["s2-position"] == 0:
            self.liquidate()
