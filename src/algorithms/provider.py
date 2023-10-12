from qgis.core import QgsProcessingProvider
from .awdAlgorithm import AWDAlgorithm

class Provider(QgsProcessingProvider):
    """Processing AWD provider."""

    def id(self, *args, **kwargs):
        """Return the id."""
        return 'awd'

    def name(self, *args, **kwargs):
        """Return the name."""
        return 'AWD - Automatic Waterfall Detector'

    def icon(self):
        """Return the icon."""
        return QgsProcessingProvider.icon(self)

    def loadAlgorithms(self, *args, **kwargs):
        """Load the algorithms"""
        self.addAlgorithm(AWDAlgorithm())
