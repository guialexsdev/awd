# AWD - Automatic Waterfalls Detector - A plugin for QGis

## Requirements and dependencies

- Minimum QGis version: 3.0

## Quick Tutorial

### Download plugin

Go to Plugin -> Manage and install plugins... -> Search for AWD and install it.

### Executing the algorithm

To use the plugin, go to Plugins -> AWD -> Detect Waterfalls or find it in the Processing Toolbox.

### Tutorial

This algorithm detects waterfalls using a fuzzy logic. All features of the resulting vector layer will contain an attribute called m_value, which varies between 0 and 1. The higher this value, the greater the certainty that the detection is correct. Detections with m_value below 0.3 should be discarded (but this can be controlled via the Alpha Cut field).

### Input parameters
#### DEM
It is recommended to use a raster with resolution of 30m or less. Copernicus 30m is a good choice.
#### Flow Accumulation
Raster containing drainages. Accumulation unit must be in Number of Cells. Recommended flow: Breaching Algorithm + Fill Sinks + Flow Accumulation (D8). The breaching algorithm implemented by John B. Lindsay is highly recommended and available in the WhiteBoxTools plugin.
#### Minimum Flow Accumulation
Minimum accumulation (in number of cells) that a drainage must have to be considered a river or stream eligible for analysis.
#### Minimum Slope
Minimum slope (in degrees) that a potential waterfall must have to be considered valid. Remember that several waterfalls can be considered small objects and therefore can contain significant errors in slope measurement. It is recommended to leave this value below 40, preferably between 10 and 20.
#### Alpha Cut
All detections with m_value below Alpha Cut will be discarded.
