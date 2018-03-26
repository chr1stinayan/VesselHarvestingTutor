import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# VesselHarvestingTutor
#

class VesselHarvestingTutor(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "VesselHarvestingTutor" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
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

    # Add vertical spacer
    self.layout.addStretch(1)

    logic = VesselHarvestingTutorLogic()
    logic.loadTransforms()
    logic.loadModels()
    
    # Refresh Apply button state
    #self.onSelect()
    

  def cleanup(self):
    pass


#
# VesselHarvestingTutorLogic
#

class VesselHarvestingTutorLogic(ScriptedLoadableModuleLogic):

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
  
  
  def updateTransforms(self, event, caller):
    
    triggerToCutter = slicer.mrmlScene.GetFirstNodeByName('TriggerToCutter')
    
    if triggerToCutter == None:
      logging.error('Could not found TriggerToCutter!')
      #return
    
    triggerToCutterTransform = triggerToCutter.GetTransformToParent()
    
    angles = triggerToCutterTransform.GetOrientation()
    
    # Todo: Implement cutter angle computation as outlined below
    
    shaftDirection_Cutter = [0,1,0]
    triggerDirection_Trigger = [1,0,0]
    triggerDirection_Cutter = triggerToCutterTransform.TransformFloatVector(triggerDirection_Trigger)
    
    triggerAngle_Rad = vtk.vtkMath().AngleBetweenVectors(triggerDirection_Cutter, shaftDirection_Cutter)
    triggerAngle_Deg = vtk.vtkMath().DegreesFromRadians(triggerAngle_Rad)
    
    print "triggerAngle_Deg: " + str(triggerAngle_Deg)
    
    if triggerAngle_Deg < 86.0:
      triggerAngle_Deg = 86.0
    if triggerAngle_Deg > 102.0:
      triggerAngle_Deg = 102.0
    
    openAngle = (triggerAngle_Deg - 86.0) * -2.2
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

    