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
    # threshold value
    #
    self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
    self.imageThresholdSliderWidget.singleStep = 0.1
    self.imageThresholdSliderWidget.minimum = -100
    self.imageThresholdSliderWidget.maximum = 100
    self.imageThresholdSliderWidget.value = 0.5
    self.imageThresholdSliderWidget.setToolTip("Set threshold value for computing the output image. Voxels that have intensities lower than this value will set to zero.")
    parametersFormLayout.addRow("Image threshold", self.imageThresholdSliderWidget)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = 0
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)

    #
    # Apply Button
    #
    self.addToolsButton = qt.QPushButton("Add Tools")
    self.addToolsButton.toolTip = "Add Tools to Scene."
    self.addToolsButton.enabled = True
    parametersFormLayout.addRow(self.addToolsButton)

    # connections
    self.addToolsButton.connect('clicked(bool)', self.onAddToolsButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    logic = VesselHarvestingTutorLogic()
    logic.loadTransforms()
    logic.loadModels()
    
    # Refresh Apply button state
    #self.onSelect()
    

  def cleanup(self):
    pass

  def onSelect(self):
    self.addToolsButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()

  def onAddToolsButton(self):
    logic = VesselHarvestingTutorLogic()
    logic.run()

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

  def run(self):
    return True
  
  
  def updateTransforms(self, event, caller):
    
    triggerToCutter = slicer.util.getNode('TriggerToCutter')
    if triggerToCutter == None:
      logging.error('Could not found TriggerToCutter!')
      return
    
    triggerToCutterTransform = triggerToCutter.GetTransformToParent()
    
    angles = triggerToCutterTransform.GetOrientation()
    
    # Todo: Implement cutter angle computation as outlined below
    
    # Compute the long axis of the cutter tool
    
    # Find direction of the trigger sensor (where the cable points at)
    
    # Compute angle between cutter long axis and trigger sensor
    
    # Find and compute mapping from trigger angle to cutter angle
    
    cutterMovingToTipTransform = vtk.vtkTransform()
    
    # By default transformations occur in reverse order compared to code. So this part needs to be read from last to first.
    # Translate center of rotation back to the original position
    cutterMovingToTipTransform.Translate(0,0,20)
    # Rotate cutter moving part
    cutterMovingToTipTransform.RotateY(angles[1]*-3)
    # Translate center of rotation of the moving part to origin
    cutterMovingToTipTransform.Translate(0,0,-20)
    
    cutterMovingToTip = slicer.util.getNode('CutterMovingToCutterTip')
    cutterMovingToTip.SetAndObserveTransformToParent(cutterMovingToTipTransform)


class VesselHarvestingTutorTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_VesselHarvestingTutor1()
    

  def test_VesselHarvestingTutor1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    logic = VesselHarvestingTutorLogic()
    logic.loadTransforms()
    logic.loadModels()

    