# CryptoDaemon - cryptocurrency trading bot

Bot works with 3 exchanges: HitBtc, Poloniex, Exmo. The trading strategy is one. Its essence is as follows. Bot watches which currencies are now in a significant decline but have the potential for growth. To do this it uses data from coinmarketcap.com to assess the capitalization of each token. 

Coins are purchased in equal proportions for the part of the deposit specified in the strategy settings in the profile and immediately put up a sell order with a stop price higher by 10% (or as indicated in the settings). After the coins are sold, half of the profit is saved in the accumulative part of the balance, and the other is reinvested into the active deposit. 

In demo mode, the work of the exchange is emulated as close as possible to the real situation on the market.
