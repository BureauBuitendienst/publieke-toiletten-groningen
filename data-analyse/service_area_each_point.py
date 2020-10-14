from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFields,
                       QgsField,
                       QgsWkbTypes,
                       QgsFeature,
                       QgsFeatureSink,
                       QgsFeatureRequest,
                       QgsVectorFileWriter,
                       QgsProcessingAlgorithm,
                       QgsProcessingException,
                       QgsProcessingOutputNumber,
                       QgsProcessingFeedback,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFeatureSink)
from qgis import processing

class ServiceAreaEachPoint(QgsProcessingAlgorithm):
    """
    This algorithm runs the ServiceArea algorithm for each point in the input 
    layer and combines the results in one output layer.
    """
    
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        # Must return a new copy of your algorithm.
        return ServiceAreaEachPoint()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'service-area-each-point'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Service Area Each Point')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Antons scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs
        to.
        """
        return 'antons-scripts'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('Runs the algorithm "Service area (from point)" for each point in the input point layer. \
            Returns service area linestring geometry for each input point')
        

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and outputs of the algorithm.
        """
        # 'INPUT' is the recommended name for the main input
        # parameter.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT',
                self.tr('Input network vector layer'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT_POINTS',
                self.tr('Input point vector layer'),
                types=[QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(QgsProcessingParameterNumber(
            'BUFFER',
            self.tr("Buffer distance"),
            QgsProcessingParameterNumber.Integer,
            250.0))
        
        # 'OUTPUT' is the recommended name for the main output
        # parameter.
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                self.tr('Service areas per point')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        # First, we get the count of features from the INPUT layer.
        # This layer is defined as a QgsProcessingParameterFeatureSource
        # parameter, so it is retrieved by calling self.parameterAsSource.
        input_network = self.parameterAsVectorLayer(parameters,
                                                     'INPUT',
                                                     context)

        input_points = self.parameterAsVectorLayer(parameters,
                                                     'INPUT_POINTS',
                                                     context)
        buffer = self.parameterAsInt(parameters,'BUFFER',context)

        if feedback.isCanceled():
            return {}

        results = {}
        # inspect INPUT and OUTPUT parameters:
        # > processing.algorithmHelp("native:serviceareafrompoint")
        for point in input_points.getFeatures():
            # log messages to console with:
            # feedback.pushInfo(f"fid: {point.id()}")
            service_area_result = processing.run("native:serviceareafrompoint", {
                'INPUT': input_network,
                'STRATEGY': 0,
                'DEFAULT_DIRECTION': 2,
                'START_POINT': point.geometry(),
                'TRAVEL_COST': buffer,
                'OUTPUT_LINES': 'memory:',
                'OUTPUT': 'memory:'
            })            
            results[point.id()] = service_area_result
            if feedback.isCanceled():
                return {}
        
        fields = input_points.fields()
        (sink, dest_id) = self.parameterAsSink(parameters,'OUTPUT', context, fields,
            QgsWkbTypes.LineString, input_network.sourceCrs())
        
        for fid in results.keys():
            request = QgsFeatureRequest()
            request.setFilterFid(fid)
            point_features = input_points.getFeatures(request)
            # only feature expected to be returned...
            point_feature = QgsFeature() 
            point_features.nextFeature(point_feature) 
            for feature in results[fid]['OUTPUT_LINES'].getFeatures():
                attrs = point_feature.attributes()               
                feature.setAttributes(attrs)
                sink.addFeature(feature,  QgsFeatureSink.FastInsert)
                if feedback.isCanceled():
                    return {}

        results = {}
        results['OUTPUT'] = dest_id
        return results
