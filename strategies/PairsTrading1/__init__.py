from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils


class PairsTrading1(Strategy):
    @property
    def c1(self):
        return utils.prices_to_returns(self.get_candles(self.exchange, self.routes[0].symbol, self.timeframe)[:, 2][-200:])
    
    @property
    def c2(self):
        return utils.prices_to_returns(self.get_candles(self.exchange, self.routes[1].symbol, self.timeframe)[:, 2][-200:])
    
    @property
    def z_score(self):
        spread = self.c1[1:] - self.c2[1:]
        z_score = utils.z_score(spread)
        return z_score[-1]


    def before(self) -> None:
        if self.index == 0:
            self.shared_vars["s1-position"] = 0
            self.shared_vars["s2-position"] = 0

        if self.index == 0 or self.index % (24 * 60 / utils.timeframe_to_one_minutes(self.timeframe)) == 0:
            # 24 * 60 / 15 can be hard coded
            is_cointegrated = utils.are_cointegrated(self.c1[1:], self.c2[1:])
            if not is_cointegrated: # close positions
                self.shared_vars["s1-position"] = 0
                self.shared_vars["s2-position"] = 0

        z_score = self.z_score

        if self.is_close and z_score < -1.2: # threshold
            # z_score negative -1.2, s2 return is greater than s1
            # thus, should short s2 and long s1
            self.shared_vars["s1-position"] = 1 
            self.shared_vars["s2-position"] = -1
            self._set_proper_margin_per_route()

        elif self.is_long and z_score > 0: # point where two return does not defer
            self.shared_vars["s1-position"] = 0
            self.shared_vars["s2-position"] = 0
        elif self.is_short and z_score < 0:
            self.shared_vars["s1-position"] = 0
            self.shared_vars["s2-position"] = 0

        elif self.is_close and z_score > 1.2:
            self.shared_vars["s1-position"] = -1
            self.shared_vars["s2-position"] = 1
            self._set_proper_margin_per_route()
        
    def _set_proper_margin_per_route(self):
        alpha, beta = utils.calculate_alpha_beta(self.c1[1:], self.c2[1:])
        # price relationship: price1 = a + (b * price2)
        # beta (hedge ratio) represents the amount of asset2 we need to buy single asset1

        self.shared_vars["margin1"] = self.available_margin * (1 / (1 + beta))
        self.shared_vars["margin2"] = self.available_margin * (beta / (1+ beta))
        # (1 / (1 + beta)) + (beta / (1+ beta)) = 1
        # margin2 = beta * margin1
 

    def should_long(self) -> bool:
        return self.shared_vars["s1-position"] == 1

    def should_short(self) -> bool:
        # For futures trading only
        return self.shared_vars["s1-position"] == -1
        
    def go_long(self):
        qty = utils.size_to_qty(self.shared_vars["margin1"], self.price, fee_rate=self.fee_rate)
        # position size represents the amount of capital allocated to a single trade
        self.buy = qty, self.price

    def go_short(self):
        qty = utils.size_to_qty(self.shared_vars["margin1"], self.price, fee_rate=self.fee_rate)
        self.sell = qty, self.price

    def update_position(self):
        if self.shared_vars["s1-position"] == 0:
            self.liquidate()
        
