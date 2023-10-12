import processing
from qgis.core import QgsProcessing, QgsProcessingParameterNumber, QgsProcessingParameterDefinition
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterRasterLayer
from .awdPostProcessing import AWDPostProcessing

class AWDAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('DEM', 'DEM', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('FLOW_ACCUMULATION', 'Flow Accumulation', defaultValue=None))
        param = QgsProcessingParameterNumber('MINIMUM_FLOW_ACCUMULATION', 'Minimum Flow Accumulation', type=QgsProcessingParameterNumber.Integer, minValue=1000, maxValue=10000, defaultValue=5000)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber('MINIMUM_SLOPE', 'Minimum Slope', type=QgsProcessingParameterNumber.Integer, minValue=5, maxValue=90, defaultValue=12)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber('ALPHA_CUT', 'Alpha Cut', type=QgsProcessingParameterNumber.Double, minValue=0.2, maxValue=1, defaultValue=0.5)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        self.addParameter(QgsProcessingParameterFeatureSink('OUTPUT', 'AWD Detections', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='TEMPORARY_OUTPUT'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(27, model_feedback)
        results = {}
        outputs = {}

        # Build query inside an extent
        alg_params = {
            'EXTENT': parameters['DEM'],
            'KEY': 'waterway',
            'SERVER': 'https://overpass-api.de/api/interpreter',
            'TIMEOUT': 25,
            'VALUE': 'waterfall'
        }
        outputs['BuildQueryInsideAnExtent'] = processing.run('quickosm:buildqueryextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Slope
        alg_params = {
            'AS_PERCENT': False,
            'BAND': 1,
            'COMPUTE_EDGES': False,
            'EXTRA': '',
            'INPUT': parameters['DEM'],
            'OPTIONS': '',
            'SCALE': 1,
            'ZEVENBERGEN': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Slope'] = processing.run('gdal:slope', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Download file
        alg_params = {
            'DATA': '',
            'METHOD': 0,  # GET
            'URL': outputs['BuildQueryInsideAnExtent']['OUTPUT_URL'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DownloadFile'] = processing.run('native:filedownloader', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # r.neighbors (error_control)
        alg_params = {
            '-a': False,
            '-c': False,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'gauss': None,
            'input': outputs['Slope']['OUTPUT'],
            'method': 9,  # variance
            'quantile': '',
            'selection': None,
            'size': 3,
            'weight': '',
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RneighborsError_control'] = processing.run('grass7:r.neighbors', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # String concatenation
        alg_params = {
            'INPUT_1': outputs['DownloadFile']['OUTPUT'],
            'INPUT_2': '|layername=points'
        }
        outputs['StringConcatenation'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # OSM Data
        alg_params = {
            'INPUT': outputs['StringConcatenation']['CONCATENATION'],
            'OPERATION': '',
            'TARGET_CRS': parameters['DEM'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['OsmData'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Raster calculator
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': None,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': f"logical_and(A > {parameters['MINIMUM_SLOPE']}, B > {parameters['MINIMUM_FLOW_ACCUMULATION']})",
            'INPUT_A': outputs['Slope']['OUTPUT'],
            'INPUT_B': parameters['FLOW_ACCUMULATION'],
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'PROJWIN': None,
            'RTYPE': 5,  # Float32
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterCalculator'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Buffered OSM Data
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 500,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['OsmData']['OUTPUT'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BufferedOsmData'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Translate (convert format)
        alg_params = {
            'COPY_SUBDATASETS': False,
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': outputs['RasterCalculator']['OUTPUT'],
            'NODATA': 0,
            'OPTIONS': '',
            'TARGET_CRS': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['TranslateConvertFormat'] = processing.run('gdal:translate', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Raster pixels to points
        alg_params = {
            'FIELD_NAME': 'toRemove',
            'INPUT_RASTER': outputs['TranslateConvertFormat']['OUTPUT'],
            'RASTER_BAND': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterPixelsToPoints'] = processing.run('native:pixelstopoints', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # OSM Data Indexed
        alg_params = {
            'INPUT': outputs['BufferedOsmData']['OUTPUT']
        }
        outputs['OsmDataIndexed'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Sample raster values (slope)
        alg_params = {
            'COLUMN_PREFIX': 'slope',
            'INPUT': outputs['RasterPixelsToPoints']['OUTPUT'],
            'RASTERCOPY': outputs['Slope']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SampleRasterValuesSlope'] = processing.run('native:rastersampling', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Sample raster values (error)
        alg_params = {
            'COLUMN_PREFIX': 'error',
            'INPUT': outputs['SampleRasterValuesSlope']['OUTPUT'],
            'RASTERCOPY': outputs['RneighborsError_control']['output'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SampleRasterValuesError'] = processing.run('native:rastersampling', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Sample raster values (flow)
        alg_params = {
            'COLUMN_PREFIX': 'flowacc',
            'INPUT': outputs['SampleRasterValuesError']['OUTPUT'],
            'RASTERCOPY': parameters['FLOW_ACCUMULATION'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SampleRasterValuesFlow'] = processing.run('native:rastersampling', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"slope1"','length': 0,'name': 'slope','precision': 0,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"flowacc1"','length': 0,'name': 'flowacc','precision': 0,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"error1"','length': 0,'name': 'error','precision': 0,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'INPUT': outputs['SampleRasterValuesFlow']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RefactorFields'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Drop field(s)
        alg_params = {
            'COLUMN': ['toRemove'],
            'INPUT': outputs['RefactorFields']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DropFields'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Detections
        alg_params = {
            'EXPRESSION': '"slope" IS NOT NULL and "flowacc" > 1000',
            'INPUT': outputs['DropFields']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Detections'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Detections Indexed
        alg_params = {
            'INPUT': outputs['Detections']['OUTPUT']
        }
        outputs['DetectionsIndexed'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 30,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['Detections']['OUTPUT'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # Dissolve
        alg_params = {
            'FIELD': [''],
            'INPUT': outputs['Buffer']['OUTPUT'],
            'SEPARATE_DISJOINT': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dissolve'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # Add groupId
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '$id','length': 0,'name': 'groupId','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'}],
            'INPUT': outputs['Dissolve']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AddGroupid'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # Groups Indexed
        alg_params = {
            'INPUT': outputs['AddGroupid']['OUTPUT']
        }
        outputs['GroupsIndexed'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # Add groupId to each detection
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['DetectionsIndexed']['OUTPUT'],
            'JOIN': outputs['GroupsIndexed']['OUTPUT'],
            'JOIN_FIELDS': ['groupId'],
            'METHOD': 0,  # Create separate feature for each matching feature (one-to-many)
            'PREDICATE': [5],  # are within
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AddGroupidToEachDetection'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        # Add OSM id
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['AddGroupidToEachDetection']['OUTPUT'],
            'JOIN': outputs['OsmDataIndexed']['OUTPUT'],
            'JOIN_FIELDS': ['osm_id'],
            'METHOD': 0,  # Create separate feature for each matching feature (one-to-many)
            'PREDICATE': [5],  # are within
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AddOsmId'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(24)
        if feedback.isCanceled():
            return {}

        # Field calculator
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'm_value',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimal (double)
            'FORMULA': 'fuzzifyFeature("flowacc", "slope", "error", "osm_id" IS NOT NULL)',
            'INPUT': outputs['AddOsmId']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FieldCalculator'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(25)
        if feedback.isCanceled():
            return {}
        results['OUTPUT'] = outputs['FieldCalculator']['OUTPUT']
        
        # Alpha Cut
        alg_params = {
            'EXPRESSION': f"\"m_value\" >= {parameters['ALPHA_CUT']}",
            'INPUT': outputs['FieldCalculator']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AlphaCut'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(26)
        if feedback.isCanceled():
            return {}

        # Extract by expression
        alg_params = {
            'EXPRESSION': '"m_value" = maximum("m_value", "groupId")',
            'INPUT': outputs['AlphaCut']['OUTPUT'],
            'OUTPUT': parameters['OUTPUT']
        }
        outputs['ExtractByExpression'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['OUTPUT'] = outputs['ExtractByExpression']['OUTPUT']

        global renamer
        renamer = AWDPostProcessing('AWD Detections')
        context.layerToLoadOnCompletionDetails(results['OUTPUT']).setPostProcessor(renamer)
        
        return results    
    
    def name(self):
        return 'awd_algorithm'

    def displayName(self):
        return 'Detect Waterfalls'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return AWDAlgorithm()

    def shortHelpString(self):
        return """
        This algorithm detects waterfalls using a fuzzy approach. All detections of the resulting vector layer will contain an attribute called <b>m_value</b> ranging from 0 to 1. The higher this value, the greater the certainty that the detection is correct. Detections with m_value below 0.3 in general should be discarded (but this can be controlled via the Alpha Cut field).
        <h2>Input parameters</h2>
        <h3>DEM</h3>
        It is recommended to use a raster with resolution of 30m or less. Copernicus 30m is a good choice.
        <h3>Flow Accumulation</h3>
        Raster containing drainages. <b>Accumulation unit must be in Number of Cells</b>. Recommended flow: Breaching Algorithm + Fill Sinks + Flow Accumulation (D8). The breaching algorithm implemented by John B. Lindsay is highly recommended and available in the WhiteBoxTools plugin.
        <h3>Minimum Flow Accumulation</h3>
        Minimum accumulation (in number of cells) that a drainage must have to be considered a river or stream eligible for analysis.
        <h3>Minimum Slope</h3>
        Minimum slope (in degrees) that a potential waterfall must have to be considered valid. Remember that several waterfalls can be considered small objects and therefore can contain significant errors in slope measurement. It is recommended to leave this value below 40, preferably between 10 and 20.
        <h3>Alpha Cut</h3>
        All detections with <b>m_value</b> below <b>Alpha Cut</b> will be discarded.
        <br />
        Visit <a href="https://github.com/guialexsdev/awd">https://github.com/guialexsdev/awd</a> to learn more!
        """
    