import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import time, datetime
import math, numpy
import csv

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

    # Add tissue surrounding vein
    models = slicer.modules.createmodels.logic()
    tissue = models.CreateCube(1000, 1000, 1000)
    tissue.GetDisplayNode().SetColor(0.85, 0.75, 0.6)
    tissue.GetDisplayNode().SetOpacity(0.7)


    # Instantiate and connect widgets ...

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

    # Slope of cutter's trajectory 
    self.trajectorySlopeDescriptionLabel = qt.QLabel("Slope of Linear Trajectory:")
    self.trajectorySlopeDescriptionLabel.setVisible(False)
    self.trajectorySlopeValueLabel = qt.QLabel("0")
    self.trajectorySlopeValueLabel.setVisible(False)
    self.trajectorySlopeValueLabel.setAlignment(0x0002) # Align right
    evhTutorFormLayout.addRow(self.trajectorySlopeDescriptionLabel, self.trajectorySlopeValueLabel)

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

    # Button to save metrics of practice EVH run
    self.saveButton= qt.QPushButton("Save metrics")
    self.saveButton.toolTip = "Save performance metrics to CSV file."
    self.saveButton.setVisible(False)
    self.saveButton.enabled = True
    self.saveButton.connect('clicked(bool)', self.onSaveButton)
    evhTutorFormLayout.addRow(self.saveButton)

    # Add vertical spacing in EVH Tutor accordion 
    self.layout.addStretch(35)

    global logic 
    logic = VesselHarvestingTutorLogic()
    logic.loadTransforms()
    logic.loadModels()


  def onRunTutorButton(self):
    if not self.runTutor: # if tutor is not running, start it 
      logic.runTutor = True
      self.onStartTutorButton()
    else: # stop active tutor 
      logic.runTutor = False
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

      self.trajectorySlopeDescriptionLabel.setVisible(False)
      self.trajectorySlopeValueLabel.setVisible(False)

      self.procedureTimeDescriptionLabel.setVisible(False)
      self.procedureTimeValueLabel.setVisible(False)

      self.showPathButton.setVisible(False)
      self.saveButton.setVisible(False)

      self.startTime = time.time()
      logic.runTutor = True
  

  def onStopTutorButton(self):    
    self.runTutorButton.setText("Start Recording")
    self.runTutor = not self.runTutor
    
    logic.runTutor = False
    
    # Calculate total procedure time 
    stopTime = time.time() 
    timeTaken = logic.getTimestamp(self.startTime, stopTime)
    metrics = logic.getDistanceMetrics()

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

    self.trajectorySlopeDescriptionLabel.setVisible(True)
    self.trajectorySlopeValueLabel.setText(str(metrics['trajectorySlope']))
    self.trajectorySlopeValueLabel.setVisible(True)

    self.procedureTimeValueLabel.setText(timeTaken)
    self.procedureTimeDescriptionLabel.setVisible(True)
    self.procedureTimeValueLabel.setVisible(True)

    self.showPathButton.setVisible(True)
    self.saveButton.setVisible(True)


  def onShowPathButton(self):
    print 'Reconstructing retractor trajectory ...'
    fidNode = slicer.util.getNode('MarkupsFiducial_*')
    n = fidNode.GetNumberOfFiducials()
    for i in range(0, n):
      fidNode.SetNthFiducialVisibility(i, 1)  
    print 'Reconstruction complete'

  
  def onSaveButton(self):
    filename = "C:/Users/cyan/Documents/dev/VesselHarvestingTutor/Data/Evh-Metrics-" + str(datetime.date.today()) + '.csv'
    metrics = logic.getDistanceMetrics()
    with open(filename, 'w+') as f:  
      writer = csv.writer(f, delimiter=',')
      writer.writerow(['Metric', 'Value']) 
      for key, value in metrics.items():
        writer.writerow([key, value]) 


  def cleanup(self):
    pass


#
# VesselHarvestingTutorLogic
#

class VesselHarvestingTutorLogic(ScriptedLoadableModuleLogic):

  
  def __init__(self):
    self.resetMetrics()


  def resetMetrics(self):
    self.metrics = {
      'minDistance': 9999999999999999999999999999,
      'maxDistance': 0,
      'minAngle': 180,
      'maxAngle': 0,
      'trajectorySlope': 0
    }
    self.pathFiducialsX = []
    self.pathFiducialsY = []
    self.path = []
    self.lastTimestamp = time.time()
    self.runTutor = False

    self.fidNodes = {} # node number is key, value is list of fiducial points in node
    
    # remove existing fiducials
    fidNode = slicer.util.getNode('MarkupsFiducial_*')
    slicer.mrmlScene.RemoveNode(fidNode)


  def loadTransforms(self):
    moduleDir = os.path.dirname(slicer.modules.vesselharvestingtutor.path)

    vesselToRetractor = slicer.util.getNode('VesselToRetractor')
    if vesselToRetractor == None:
      vesselToRetractor = slicer.vtkMRMLLinearTransformNode()
      vesselToRetractor.SetName('vesselToRetractor')
      slicer.mrmlScene.AddNode(vesselToRetractor)

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

    #load vessel

    for i in range(13):
      modelFilename = 'Model_' + str(i) + '.vtk'
      fiducialFilename = 'Points_' + str(i) + '.fcsv'
      modelFilePath = os.path.join(moduleDir, os.pardir,'CadModels/vessel', modelFilename)
      fiducialFilePath = os.path.join(moduleDir, os.pardir,'CadModels/vessel', fiducialFilename)
      [success, tempNode] = slicer.util.loadModel(modelFilePath, returnNode=True)
      tempNode.GetDisplayNode().SetColor(1, 0, 0)
      slicer.util.loadMarkupsFiducialList(fiducialFilePath)
      if i == 0: 
        self.vesselModel = tempNode
    
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
    vesselToRetractor = slicer.util.getNode('vesselToRetractor')

    vesselID = self.vesselModelToVessel.GetID()
    for i in range(13): 
      branchName = 'Model_' + str(i)
      branchNode = slicer.util.getNode(branchName)
      branchNode.SetAndObserveTransformNodeID(vesselID)
    self.vesselModelToVessel.SetAndObserveTransformNodeID(vesselToRetractor.GetID())


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

    # current timestamp is time.time()
    # save fiducial point every 0.25 seconds 
    if self.runTutor and ( time.time() - self.lastTimestamp) > 0.25: 
      cutterTipWorld = [0,0,0,0]
      fiducial = slicer.util.getNode("F")
      fiducial.GetNthFiducialWorldCoordinates(0,cutterTipWorld) # z coordinate not important for linear slope calculation

      # add path fiducials to separate node
      self.pathFiducialsNode = slicer.util.getNode('MarkupsFiducial_*')
      if self.pathFiducialsNode == None:
        self.pathFiducialsNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMarkupsFiducialNode')
        slicer.mrmlScene.AddNode(self.pathFiducialsNode)
      slicer.modules.markups.logic().AddFiducial(cutterTipWorld[0], cutterTipWorld[1], cutterTipWorld[2])
      # set new fiducial's label and hide from 3D view
      n = self.pathFiducialsNode.GetNumberOfFiducials() - 1
      self.pathFiducialsNode.SetNthFiducialLabel(n, str(n))
      self.pathFiducialsNode.SetNthFiducialVisibility(n, 0)  

      self.pathFiducialsX.append(cutterTipWorld[0])
      self.pathFiducialsY.append(cutterTipWorld[1])
      self.path.append(cutterTipWorld[:-1])
      self.lastTimestamp = time.time()

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
    if len(self.pathFiducialsX) > 0:
      print self.pathFiducialsX, self.pathFiducialsY
      x = numpy.array(self.pathFiducialsX)
      y = numpy.array(self.pathFiducialsY)
      A = numpy.vstack([x, numpy.ones(len(x))]).T
      slope, _ = numpy.linalg.lstsq(A, y)[0]
      self.metrics['trajectorySlope'] = round(slope, 2)
      self.metrics['points'] = self.path
    return self.metrics


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

