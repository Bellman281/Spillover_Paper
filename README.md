# Spillover_Paper

This repo includes data, python codes & notebooks and RATS codes for our joint paper on "The interactions between OPEC oil price and sectoral stock returns: Evidence from China, Physica A: Statistical Mechanics and its Applications, Berna Kirkulak-Uludag, Omid Safarzadeh." and similar paper which will be published soon.

Please look at these files:

1. wti_oil.py (or Colab :    https://colab.research.google.com/drive/1oDcwPDOQsUi2uqn-0PrqAXe5nizaCZRo ) 
this file rearranges the data from several stock indices and WTI (OPEC will be similar), prepares descriptive statistics and statistics tests reported in the paper.

2. *.RPF files : provide RATS codes for multivariate GARCH models including BEKK, DCC and VARMA GARCH to capture spillover effect of oil prices on several markets. 

3. Varma-Garch model provides Dynamic Covariance (*_H-matrix.xlsx files) matrix from which one can estimate hedging ratios against volatility of oil prices for each market. 

(please read the paper for more details )
