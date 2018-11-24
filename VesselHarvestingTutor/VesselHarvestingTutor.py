import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import time
import math, numpy

#
# VesselHarvestingTutor
#

class VesselHarvestingTutor(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Vessel Harvesting Tutor" 
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Perk Lab"] 
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# VesselHarvestingTutorWidget
#

class VesselHarvestingTutorWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    self.runTutor = False
    self.cutterFiducial = slicer.modules.markups.logic().AddFiducial()

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)

    #
    # output volume selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = True
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Volume: ", self.outputSelector)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = 0
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)


    #
    # EVH Tutor Accordion
    #
    evhTutorCollapsibleButton = ctk.ctkCollapsibleButton()
    evhTutorCollapsibleButton.text = "Endovein Harvesting Tutor"
    self.layout.addWidget(evhTutorCollapsibleButton)
    evhTutorFormLayout = qt.QFormLayout(evhTutorCollapsibleButton)

    # Button to start recording with EVH tutor
    self.runTutorButton = qt.QPushButton("Start Recording")
    self.runTutorButton.toolTip = "Starts EVH tutor and recording practice procedure."
    self.runTutorButton.enabled = True
    self.runTutorButton.connect('clicked(bool)', self.onRunTutorButton)
    evhTutorFormLayout.addRow(self.runTutorButton)

    # Smallest angle between retractor and vessel axis
    self.minAngleDescriptionLabel = qt.QLabel("Smallest Angle Between Retractor and Vessel:")
    self.minAngleDescriptionLabel.setVisible(False)
    self.minAngleValueLabel = qt.QLabel("0")
    self.minAngleValueLabel.setVisible(False)
    self.minAngleValueLabel.setAlignment(0x0002) # Align right
    evhTutorFormLayout.addRow(self.minAngleDescriptionLabel, self.minAngleValueLabel)

    # Maximum angle between retractor and vessel axis
    self.maxAngleDescriptionLabel = qt.QLabel("Largest Angle Between Retractor and Vessel:")
    self.maxAngleDescriptionLabel.setVisible(False)
    self.maxAngleValueLabel = qt.QLabel("0")
    self.maxAngleValueLabel.setVisible(False)
    self.maxAngleValueLabel.setAlignment(0x0002) # Align right
    evhTutorFormLayout.addRow(self.maxAngleDescriptionLabel, self.maxAngleValueLabel)

    # Minimum distance from vessel
    self.minDistanceDescriptionLabel = qt.QLabel("Shortest Distance Cut from Dissected Vein:")
    self.minDistanceDescriptionLabel.setVisible(False)
    self.minDistanceValueLabel = qt.QLabel("0")
    self.minDistanceValueLabel.setVisible(False)
    self.minDistanceValueLabel.setAlignment(0x0002) # Align right
    evhTutorFormLayout.addRow(self.minDistanceDescriptionLabel, self.minDistanceValueLabel)

    # Maximum distance from vessel
    self.maxDistanceDescriptionLabel = qt.QLabel("Largest Distance Cut from Dissected vein:")
    self.maxDistanceDescriptionLabel.setVisible(False)
    self.maxDistanceValueLabel = qt.QLabel("0")
    self.maxDistanceValueLabel.setVisible(False)
    self.maxDistanceValueLabel.setAlignment(0x0002) # Align right
    evhTutorFormLayout.addRow(self.maxDistanceDescriptionLabel, self.maxDistanceValueLabel)

    # Number of cutter rotations 
    self.numRotationsDescriptionLabel = qt.QLabel("Total Number of Tool Rotations:")
    self.numRotationsDescriptionLabel.setVisible(False)
    self.numRotationsValueLabel = qt.QLabel("0")
    self.numRotationsValueLabel.setVisible(False)
    self.numRotationsValueLabel.setAlignment(0x0002) # Align right
    evhTutorFormLayout.addRow(self.numRotationsDescriptionLabel, self.numRotationsValueLabel)

    # Time label of practice procedure
    self.procedureTimeDescriptionLabel = qt.QLabel("Total Procedure Time:")
    self.procedureTimeDescriptionLabel.setVisible(False)
    self.procedureTimeValueLabel = qt.QLabel("")
    self.procedureTimeValueLabel.setVisible(False)
    self.procedureTimeValueLabel.setAlignment(0x0002) # Align right
    evhTutorFormLayout.addRow(self.procedureTimeDescriptionLabel, self.procedureTimeValueLabel)

    # Button to display retractor trajectory 
    self.showPathButton = qt.QPushButton("Reconstruct retractor trajectory")
    self.showPathButton.toolTip = "Visualize retractor trajectory overlayed on vessel model."
    self.showPathButton.setVisible(False)
    self.showPathButton.enabled = True
    self.showPathButton.connect('clicked(bool)', self.onShowPathButton)
    evhTutorFormLayout.addRow(self.showPathButton)

    # Add vertical spacing in EVH Tutor accordion 
    self.layout.addStretch(35)

    global logic 
    logic = VesselHarvestingTutorLogic()
    logic.loadTransforms()
    logic.loadModels()
    
    # Refresh Apply button state
    #self.onSelect()


  def onRunTutorButton(self):
    if not self.runTutor: # if tutor is not running, start it 
      self.onStartTutorButton()
    else: # stop active tutor 
      self.onStopTutorButton()


  def onStartTutorButton(self):
      logic.resetMetrics()
      self.runTutorButton.setText("Stop Recording")
      self.runTutorButton.toolTip = "Stops EVH tutor and recording practice procedure."
      self.runTutor = not self.runTutor

      self.minAngleDescriptionLabel.setVisible(False)
      self.minAngleValueLabel.setVisible(False)

      self.maxAngleDescriptionLabel.setVisible(False)
      self.maxAngleValueLabel.setVisible(False)

      self.minDistanceDescriptionLabel.setVisible(False)
      self.minDistanceValueLabel.setVisible(False)

      self.maxDistanceDescriptionLabel.setVisible(False)
      self.maxDistanceValueLabel.setVisible(False)

      self.numRotationsDescriptionLabel.setVisible(False)
      self.numRotationsValueLabel.setVisible(False)

      self.procedureTimeDescriptionLabel.setVisible(False)
      self.procedureTimeValueLabel.setVisible(False)

      self.showPathButton.setVisible(False)

      self.startTime = time.time()
      logic.runTutor()
  

  def onStopTutorButton(self):    
    self.runTutorButton.setText("Start Recording")
    self.runTutor = not self.runTutor
    
    # Calculate total procedure time 
    stopTime = time.time() 
    timeTaken = logic.getTimestamp(self.startTime, stopTime)
    logic.stopTutor()
    metrics = logic.getDistanceMetrics()
    print metrics

    self.minAngleDescriptionLabel.setVisible(True)
    self.minAngleValueLabel.setText(str(metrics['minAngle']) + ' degrees')
    self.minAngleValueLabel.setVisible(True)

    self.maxAngleDescriptionLabel.setVisible(True)
    self.maxAngleValueLabel.setText(str(metrics['maxAngle']) + ' degrees')
    self.maxAngleValueLabel.setVisible(True)

    self.minDistanceDescriptionLabel.setVisible(True)
    self.minDistanceValueLabel.setText(str(metrics['minDistance']))
    self.minDistanceValueLabel.setVisible(True)

    self.maxDistanceDescriptionLabel.setVisible(True)
    self.maxDistanceValueLabel.setText(str(metrics['maxDistance']))
    self.maxDistanceValueLabel.setVisible(True)

    self.numRotationsDescriptionLabel.setVisible(True)
    self.numRotationsValueLabel.setVisible(True)

    self.procedureTimeValueLabel.setText(timeTaken)
    self.procedureTimeDescriptionLabel.setVisible(True)
    self.procedureTimeValueLabel.setVisible(True)

    self.showPathButton.setVisible(True)


  def onShowPathButton(self):
    print 'Reconstructing retractor trajectory ...'
    # TODO implement path reconstruction
    pass


  def cleanup(self):
    pass


#
# VesselHarvestingTutorLogic
#

class VesselHarvestingTutorLogic(ScriptedLoadableModuleLogic):

  
  def __init__(self):
    self.metrics = {
      'minDistance': 9999999999999999999999999999,
      'maxDistance': 0,
      'minAngle': 180,
      'maxAngle': 0,
      'numRotations': 0
    }


  def resetMetrics(self):
    self.metrics = {
      'minDistance': 9999999999999999999999999999,
      'maxDistance': 0,
      'minAngle': 180,
      'maxAngle': 0,
      'numRotations': 0
    }


  def loadTransforms(self):
    moduleDir = os.path.dirname(slicer.modules.vesselharvestingtutor.path)

    self.vesselToRetractor = slicer.util.getNode('VesselToRetractor')
    triggerToCutter = slicer.util.getNode('TriggerToCutter')
    if triggerToCutter == None:
      triggerToCutter = slicer.vtkMRMLLinearTransformNode()
      triggerToCutter.SetName('TriggerToCutter')
      slicer.mrmlScene.AddNode(triggerToCutter)
    
    cutterToRetractor = slicer.util.getNode('CutterToRetractor')
    if cutterToRetractor == None:
      cutterToRetractor = slicer.vtkMRMLLinearTransformNode()
      cutterToRetractor.SetName('CutterToRetractor')
      slicer.mrmlScene.AddNode(cutterToRetractor)
    
    cutterMovingToTip = slicer.util.getNode('CutterMovingToCutterTip')
    if cutterMovingToTip == None:
      cutterMovingToTip = slicer.vtkMRMLLinearTransformNode()
      cutterMovingToTip.SetName('CutterMovingToCutterTip')
      slicer.mrmlScene.AddNode(cutterMovingToTip)
    
    cutterTipToCutter = slicer.util.getNode('CutterTipToCutter')
    if cutterTipToCutter == None:
      filePath = os.path.join(moduleDir, os.pardir, 'Transforms', 'CutterTipToCutter.h5')
      [success, cutterTipToCutter] = slicer.util.loadTransform(filePath, returnNode=True)
      cutterTipToCutter.SetName('CutterTipToCutter')

    # Create and set fiducial point on the cutter tip, used to calculate distance metrics
    # TODO make fiducial invisible
    fidNode = slicer.util.getNode("F")
    fidNode.SetAndObserveTransformNodeID(cutterTipToCutter.GetID())
    cutterTipToCutter.SetAndObserveTransformNodeID(cutterToRetractor.GetID())
    cutterMovingToTip.SetAndObserveTransformNodeID(cutterTipToCutter.GetID())
    triggerToCutter.AddObserver(slicer.vtkMRMLLinearTransformNode.TransformModifiedEvent, self.updateTransforms)


  def loadModels(self):
    moduleDir = os.path.dirname(slicer.modules.vesselharvestingtutor.path)
    
    self.retractorModel= slicer.util.getNode('RetractorModel')
    if not self.retractorModel:
      modelFilePath = os.path.join(moduleDir, os.pardir,'CadModels', 'VesselRetractorHead.stl')
      [success, self.retractorModel] = slicer.util.loadModel(modelFilePath, returnNode=True)
      self.retractorModel.SetName('RetractorModel')
      self.retractorModel.GetDisplayNode().SetColor(0.9, 0.9, 0.9)
    
    self.cutterBaseModel = slicer.util.getNode('CutterBaseModel')
    if self.cutterBaseModel == None:
      modelFilePath = os.path.join(moduleDir, os.pardir, 'CadModels', 'CutterBaseModel.stl')
      [success, self.cutterBaseModel] = slicer.util.loadModel(modelFilePath, returnNode=True)
      self.cutterBaseModel.SetName('CutterBaseModel')
      self.cutterBaseModel.GetDisplayNode().SetColor(0.8, 0.9, 1.0)
	  
    self.vesselModel= slicer.util.getNode('VesselModel')
    if not self.vesselModel:
      modelFilePath = os.path.join(moduleDir, os.pardir,'CadModels', 'VesselModel.vtk')
      [success, self.vesselModel] = slicer.util.loadModel(modelFilePath, returnNode=True)
      self.vesselModel.SetName('VesselModel')
      self.vesselModel.GetDisplayNode().SetColor(1, 0, 0)

    cutterTipToCutter = slicer.util.getNode('CutterTipToCutter')
    if cutterTipToCutter == None:
      logging.error('Load transforms before models!')
      return
    self.cutterBaseModel.SetAndObserveTransformNodeID(cutterTipToCutter.GetID())
    
    self.cutterMovingModel = slicer.util.getNode('CutterMovingModel')
    if self.cutterMovingModel == None:
      modelFilePath = os.path.join(moduleDir, os.pardir, 'CadModels', 'CutterMovingModel.stl')
      [success, self.cutterMovingModel] = slicer.util.loadModel(modelFilePath, returnNode=True)
      self.cutterMovingModel.SetName('CutterMovingModel')
      self.cutterMovingModel.GetDisplayNode().SetColor(0.8, 0.9, 1.0)

    cutterMovingToTip = slicer.util.getNode('CutterMovingToCutterTip')
    if cutterMovingToTip == None:
      logging.error('Load transforms before models!')
      return
    self.cutterMovingModel.SetAndObserveTransformNodeID(cutterMovingToTip.GetID())
	
    self.vesselModelToVessel = slicer.util.getNode('VesselModelToVessel')
    if not self.vesselModelToVessel:
      transformFilePath = os.path.join(moduleDir, os.pardir,'Transforms', 'VesselModelToVessel.h5')
      [success, self.vesselModelToVessel] = slicer.util.loadTransform(transformFilePath, returnNode=True)
      if success == False:
        logging.error('Could not read needle tip to needle transform!')
      else:
        self.vesselModelToVessel.SetName("VesselModelToVessel")
    self.vesselModel.SetAndObserveTransformNodeID(self.vesselModelToVessel.GetID())


  def run(self):
    return True


  def distance(self, a, b):
    dist = 0
    length = len(b)
    for i in range(length):
      dist += (a[i] - b[i]) ** 2
    return math.sqrt(dist)

  
  def calculateVesselToRetractorAngle(self, vesselVector, retractorVector):
    angleRadians = vtk.vtkMath.AngleBetweenVectors(vesselVector[0:3], retractorVector[0:3])
    angleDegrees = round(vtk.vtkMath.DegreesFromRadians(angleRadians), 2)
    if self.metrics['maxAngle'] < angleDegrees:
      self.metrics['maxAngle'] = angleDegrees
    elif self.metrics['minAngle'] > angleDegrees:
      self.metrics['minAngle'] = angleDegrees
  
  
  def updateTransforms(self, event, caller):
    
    triggerToCutter = slicer.mrmlScene.GetFirstNodeByName('TriggerToCutter')    
    if triggerToCutter == None:
      logging.error('Could not found TriggerToCutter!')

    triggerToCutterTransform = triggerToCutter.GetTransformToParent()    
    angles = triggerToCutterTransform.GetOrientation()    
    # Todo: Implement cutter angle computation as outlined below    
    shaftDirection_Cutter = [0,1,0]
    triggerDirection_Trigger = [1,0,0]
    triggerDirection_Cutter = triggerToCutterTransform.TransformFloatVector(triggerDirection_Trigger)    

    triggerAngle_Rad = vtk.vtkMath().AngleBetweenVectors(triggerDirection_Cutter, shaftDirection_Cutter)
    triggerAngle_Deg = vtk.vtkMath().DegreesFromRadians(triggerAngle_Rad)
    
    # adjusting values for openAngle calculation 
    if triggerAngle_Deg < 90.0:
      triggerAngle_Deg = 90.0
    if triggerAngle_Deg > 102.0:
      triggerAngle_Deg = 102.0

    openAngle = (triggerAngle_Deg - 90.0) * -2.2 # angle of cutter tip to shaft 
    #print "triggerAngle_Deg: " + str(triggerAngle_Deg), "open ", openAngle #DEBUG

    cutterMovingToTipTransform = vtk.vtkTransform()
    # By default transformations occur in reverse order compared to source code line order.
    # Translate center of rotation back to the original position
    cutterMovingToTipTransform.Translate(0,0,-20)
    # Rotate cutter moving part
    cutterMovingToTipTransform.RotateY(openAngle)
    # Translate center of rotation of the moving part to origin
    cutterMovingToTipTransform.Translate(0,0,20)
    
    cutterMovingToTip = slicer.mrmlScene.GetFirstNodeByName('CutterMovingToCutterTip')
    cutterMovingToTip.SetAndObserveTransformToParent(cutterMovingToTipTransform)   

    self.updateAngleMetrics()

    if math.fabs(openAngle) < 0.5:
      return self.updateDistanceMetrics()


  def npArrayFromVtkMatrix(self, vtkMatrix):
    npArray = numpy.zeros((4,4))
    for row in range(4):
      for column in range(4):
          npArray[row][column] = vtkMatrix.GetElement(row,column)
    return npArray

    
  def updateAngleMetrics(self):
    vesselModelToVessel = slicer.mrmlScene.GetFirstNodeByName('VesselModelToVessel')  
    vesselToRas = vtk.vtkMatrix4x4()
    vesselModelToVessel.GetMatrixTransformToWorld(vesselToRas)
    vesselDirection = numpy.dot(self.npArrayFromVtkMatrix(vesselToRas), numpy.array([ 0, 0, 1, 0]))

    cutterTipToCutter = slicer.mrmlScene.GetFirstNodeByName('CutterTipToCutter')  
    cutterToRas = vtk.vtkMatrix4x4()
    cutterTipToCutter.GetMatrixTransformToWorld(cutterToRas)
    cutterDirection = numpy.dot(self.npArrayFromVtkMatrix(cutterToRas), numpy.array([ 0, 0, 1, 0]))

    self.calculateVesselToRetractorAngle(vesselDirection, cutterDirection)
    

  def updateDistanceMetrics(self):
    cutterTipWorld = [0,0,0,0]
    fiducial = slicer.util.getNode("F")
    fiducial.GetNthFiducialWorldCoordinates(0,cutterTipWorld) # cutterTipWorld now holds the coordinates of 
    self.vesselModel = slicer.util.getNode('VesselModel') 
    polydata = self.vesselModel.GetPolyData()
    numVesselPoints = polydata.GetNumberOfPoints()
    vesselPoints = [ self.distance(cutterTipWorld, polydata.GetPoint(i)) for i in range(numVesselPoints)]
    cutDistance = min(vesselPoints)
    if self.metrics['maxDistance'] < cutDistance:
      self.metrics['maxDistance'] = round(cutDistance, 2)
    if self.metrics['minDistance'] > cutDistance:
      self.metrics['minDistance'] = round(cutDistance, 2)
    # TODO average cut distance logic 
    
  
  def getDistanceMetrics(self):
    return self.metrics

  
  def runTutor(self):
    print "Starting EVH Tutor"

  
  def stopTutor(self):
    print "Stopping EVH Tutor"


  def getTimestamp(self, start, stop):
    elapsed = stop - start 
    formattedTime = time.strftime('%H:%M:%S', time.gmtime(elapsed)) # convert seconds to HH:MM:SS timestamp
    return formattedTime
    

class VesselHarvestingTutorTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_VesselHarvestingTutor1()


  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)


  def test_VesselHarvestingTutor1(self):
    logic = VesselHarvestingTutorLogic()
    logic.loadTransforms()
    logic.loadModels()

