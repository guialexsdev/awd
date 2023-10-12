from qgis.core import QgsMessageLog, Qgis

def info(msg, tabName = 'AWD'):
    QgsMessageLog.logMessage(msg, tabName, Qgis.MessageLevel.Info)

def warning(msg, tabName = 'AWD'):
    QgsMessageLog.logMessage(msg, tabName, Qgis.MessageLevel.Warning)

def error(msg, tabName = 'AWD'):
    QgsMessageLog.logMessage(msg, tabName, Qgis.MessageLevel.Critical)