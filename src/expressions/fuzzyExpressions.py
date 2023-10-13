from qgis.core import qgsfunction
import math

def fuzzyPieceWise(x,a,b,c,d):
    if x < a:
        return 0
    elif x >= a and x <= b:
        return (x-a)/(b-a)
    elif x > b and x < c:
        return 1
    elif x >= c and x <= d:
        return (d-x)/(d-c)
    else:
        return 0

def fuzzyPieceWiseDecreasing(x,a,b):
    if x < a:
        return 1
    elif x >= a and x <= b:
        return (b-x)/(b-a)
    else:
        return 0
        
def fuzzyPieceWiseIncreasing(x,a,b):
    if x < a:
        return 0
    elif x >= a and x <= b:
        return (x-a)/(b-a)
    else:
        return 1
    
@qgsfunction(args='auto', group='AWD Fuzzy')
def fuzzifyFeature(flow, slope, error, minimumFlow, minmumSlope, osmIdIsPresent, feature, parent):
    if osmIdIsPresent:
        return 1
    
    flowGood  = fuzzyPieceWise(flow, minimumFlow, 10000, 200000, 1000000)
    slopeGood = fuzzyPieceWiseIncreasing(slope, minmumSlope, 25)
    errorGood = fuzzyPieceWiseDecreasing(error, 15, 50)
    
    good = max(
        min(errorGood, slopeGood, flowGood),
        min(errorGood**2, math.sqrt(slopeGood), flowGood**2),
        min(math.sqrt(errorGood), slopeGood**2, flowGood**2),
        min(errorGood**2, slopeGood**2, math.sqrt(flowGood)),
    )

    return good
