# UBS_Challenge

ir_vegas.csv: 
    This file contains timeseries of TV and IR Vega of each trade, specifically:
    1. Value Date: the date on which we compute the TV and Vega risks
    2. Trade Name: trade identity
    3. Trade Currency: currency of the trade
    4. Zero Rate Shock: shock value in bps of the parallel yield curve zero rate shock
    5. TV: total value of the trade in its trade currency
    6. Expiry Bucket: expiry of the swaption
    7. Expiry Date: expiry date of the swaption
    8. Tenor Bucket: tenor of the swap to be entered by the swaption
    9. Vega: trade's sensitivity in cash towards market swaption implied Normal volatility
    For example, the row item
        (2023-05-23, dummyTrade1, USD, -50, -158091.52, 5y, 2028-05-23, 4y, -32.53)
    indicates that:
        Market Condition: USD zero rates moves in parallel by -50 basis points on 2023-05-23
        dummyTrade1’s TV under the Market Condition is -158,091.52 in USD
        dummyTrade1’s sensitivity towards USD 5y swaption (underlying 4y IRS) market implied Normal volatility is -32.53 in USD
swap_rates.csv:
    This file contains timeseries of swap rates, specifically:
    1. Date： quote date
    2. Start Date: start date of swap
    3. Tenor: swap tenor
    4. Swap Rate: market swap rate value （in percentage)
    For example, the row item
        (1/13/2021, 1/13/2022, 10y, 1.0813328677467247)
    indicates that the swap rate for a 10y swap starting from 1/13/2022 quoted on 1/13/2021 is 1.0813328677467247%		
rates_vols.csv:
    This file contains time series of swap implied normal vols, specifically:
    1. Date: quote date
    2. Expiry: expiry of the swaption
    3. Tenor: tenor of the swap to be entered by the swaption
    4. Strike: rate spread to ATM value
    5. Vols: market implied normal volatility (in percentage)
    For example, the row item
        (1/13/2021, 10y, 10y, atm-1.0%, 0.17055186526449959)
    indicates that on 1/13/2021, the implied normal volatility for a 10y swap starting in 10 years with strike being 0.99*swap rate is 0.17055186526449959%		
portfolio_information.csv:
    This file contains information of the portfolio used in IR Vega calculation. For example, the 1st trade is a 5Y range accrual with 2y CMS rate as the underlying, coupon is paid every 6M with lower bound = 0.0042 and upper bound = 0.0379.
