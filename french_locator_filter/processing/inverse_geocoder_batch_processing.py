from typing import Any, Dict, List, Optional

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFields,
    QgsGeocoderContext,
    QgsGeocoderInterface,
    QgsProcessingContext,
    QgsProcessingFeatureBasedAlgorithm,
    QgsProcessingFeedback,
    QgsProcessingParameterNumber,
    QgsProcessingUtils,
)
from qgis.PyQt.QtCore import QCoreApplication


class InverseGeocoderBatchProcessing(QgsProcessingFeatureBasedAlgorithm):
    NB_RESULT_BY_FEATURE = "NB_RESULT_BY_FEATURE"

    def __init__(self, geocoder: QgsGeocoderInterface):
        super().__init__()
        self.geocoder = geocoder
        self._nb_result_by_feature: int = 1
        self._additional_fields: List[str] = []
        self._input_crs = None

    def initParameters(self, configuration: Dict[str, Any] = {}) -> None:
        """Initializes any extra parameters added by the algorithm subclass.
        There is no need to declare the input source or output sink, as these are automatically created by QgsProcessingFeatureBasedAlgorithm.

        :param configuration: configuration, defaults to {}
        :type configuration: Dict[str, Any], optional
        """

        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.NB_RESULT_BY_FEATURE,
                description=self.tr("Nombre de résultat par ligne."),
                defaultValue=1,
                minValue=0,
                maxValue=10,
            )
        )

    def outputFields(self, inputFields: QgsFields) -> QgsFields:
        """Define output fields for sink creation

        :param inputFields: input fields
        :type inputFields: QgsFields
        :return: output fields
        :rtype: QgsFields
        """
        # append any additional fields created by the geocoder
        new_fields = self.geocoder.appendedFields()
        self._additional_fields = new_fields.names()

        return QgsProcessingUtils.combineFields(inputFields, new_fields)

    def outputWkbType(self, inputWkbType: Qgis.WkbType) -> Qgis.WkbType:
        """Define output WkbType, alway Point

        :param inputWkbType: input type
        :type inputWkbType: Qgis.WkbType
        :return: output type
        :rtype: Qgis.WkbType
        """
        return Qgis.WkbType.Point

    def outputLayerType(self) -> Qgis.ProcessingSourceType:
        """Define output layer type, always vector point

        :return: output layer type
        :rtype: Qgis.ProcessingSourceType
        """
        return Qgis.ProcessingSourceType.VectorPoint

    def prepareAlgorithm(
        self,
        parameters: Dict[str, Any],
        context: QgsProcessingContext,
        feedback: Optional[QgsProcessingFeedback],
    ) -> bool:
        """Prepares the algorithm to run using the specified parameters.

        :param parameters: input parameter
        :type parameters: Dict[str, Any]
        :param context: processing context
        :type context: QgsProcessingContext
        :param feedback: processing feedback
        :type feedback: Optional[QgsProcessingFeedback]
        :return: True if the parameter are valid, False otherwise
        :rtype: bool
        """
        self._nb_result_by_feature = self.parameterAsInt(
            parameters, self.NB_RESULT_BY_FEATURE, context
        )

        return True

    def processFeature(
        self,
        feature: QgsFeature,
        context: QgsProcessingContext,
        feedback: Optional[QgsProcessingFeedback],
    ) -> List[QgsFeature]:
        """Processes an individual input feature from the source

        :param feature: feature to process
        :type feature: QgsFeature
        :param context: processing context
        :type context: QgsProcessingContext
        :param feedback: processing feedback
        :type feedback: Optional[QgsProcessingFeedback]
        :return: list of created QgsFeature
        :rtype: List[QgsFeature]
        """

        # Check if geometry must be converted
        geometry = feature.geometry()
        transform = None
        if self._input_crs != QgsCoordinateReferenceSystem("EPSG:4326"):
            transform = QgsCoordinateTransform(
                self._input_crs,
                QgsCoordinateReferenceSystem("EPSG:4326"),
                context.transformContext(),
            )
            geometry.transform(transform)
            feature.setGeometry(geometry)

        geocode_context = QgsGeocoderContext(context.transformContext())
        results = self.geocoder.geocodeFeature(
            feature=feature, context=geocode_context, feedback=feedback
        )

        feature_list: List[QgsFeature] = []
        for res in results[0 : self._nb_result_by_feature]:
            f = QgsFeature(feature)
            attr = f.attributes()
            additional_attributes = res.additionalAttributes()
            for field in self._additional_fields:
                attr.append(additional_attributes[field])

            f.setAttributes(attr)

            # Apply inverse transformation if input data was converted
            g = res.geometry()
            if transform:
                g.transform(transform, direction=Qgis.TransformDirection.Reverse)

            f.setGeometry(g)
            feature_list.append(f)

        return feature_list

    def tr(self, message: str) -> str:
        """Get the translation for a string using Qt translation API.

        :param message: string to be translated.
        :type message: str

        :returns: Translated version of message.
        :rtype: str
        """
        return QCoreApplication.translate(self.__class__.__name__, message)

    def outputCrs(
        self, input_crs: QgsCoordinateReferenceSystem
    ) -> QgsCoordinateReferenceSystem:
        """Maps the input source coordinate reference system (inputCrs) to a corresponding output CRS generated by the algorithm.

        :param inputCrs: input crs
        :type inputCrs: QgsCoordinateReferenceSystem
        :return: output crs (alway input crs, conversion done after request if needed)
        :rtype: QgsCoordinateReferenceSystem
        """
        self._input_crs = input_crs
        return self._input_crs

    def outputName(self) -> str:
        """Output layer name

        :return: output layer name
        :rtype: str
        """
        return self.tr("Geocoding inversé")
