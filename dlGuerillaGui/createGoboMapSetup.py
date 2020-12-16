################################################################################
# L ATELIER ANIMATION INC.
#
# [2012] - [2019] L ATELIER ANIMATION INC. All Rights Reserved.
#
# NOTICE: All information contained herein is, and remains
#         the property of L Atelier Animation Inc. and its suppliers,
#         if any.  The intellectual and technical concepts contained
#         herein are proprietary to L Atelier Animation Inc. and its
#         suppliers and may be covered by Canadian, U.S. and/or
#         Foreign Patents, patents in process, and are protected
#         by trade secret or copyright law. Dissemination of this
#         information or reproduction of this material is strictly
#         forbidden unless prior written permission is obtained from
#         L ATELIER ANIMATION INC.
#
################################################################################
'''Guerilla tool UI to create gobo map setup / rig.

@package dlGuerillaGui.createGoboMapSetup
@author Esteban Ortega <esteban.ortega@latelieranimation.com>
'''

import dlGuerillaApi
import dlGuerillaTools

import ddPipeApi

import ddGuerillaApi

import ddGui

__all__ = ('DLCreateGoboMapSetup' , )

class DLCreateGoboMapSetup( ddGui.QtWidgets.QDialog ):
    '''Dialog to create GoboMap setup, shots can be specified to link all
    related renders graphs to the Gobo render pass created during process, gobo
    camera's field of view can also be specified.
    '''

    ## Define initial size of dialog Box.
    # type: QSize
    _DL_NORMAL_SIZE = ddGui.QtCore.QSize( 270 ,
                                          300 )

    ## Define initial size of dialog Box.
    # type: QSize
    _DL_EXPANDED_SIZE = ddGui.QtCore.QSize( 460 ,
                                            300 )

    def __init__( self ):
        '''Initialize the instance.
        '''

        ## Store gobo setup instance.
        # type: dlGuerillaTools.DLGoboMapSetup
        self.__goboSetup = None

        ## Current selection.
        # type: ddGuerillaApi.DDNode
        self.__currentSelection = None

        ## String representing the status for msg on accept.
        # type: str
        self.__statusMsg = 'Created'

        super( DLCreateGoboMapSetup , self ).__init__()

        self.setWindowTitle( 'Create GoboMap Setup' )
        self.setFixedSize( self._DL_NORMAL_SIZE )

        self.setWindowFlags( ddGui.QtCore.Qt.WindowStaysOnTopHint )

        ########################################################################
        # Create main layout
        ########################################################################
        mainLayout = ddGui.QtWidgets.QVBoxLayout()
        self.setLayout( mainLayout )

        ########################################################################
        # Create widget for camera Fov
        ########################################################################
        fovLayout = ddGui.QtWidgets.QHBoxLayout()
        self.fovQLabel = ddGui.QtWidgets.QLabel( 'Gobo camera Fov' )
        fovLayout.addWidget( self.fovQLabel )
        self.fovQSpinBox = ddGui.QtWidgets.QSpinBox()
        self.fovQSpinBox.setMaximum( 360 )
        self.fovQSpinBox.setValue( 50 )
        self.fovQSpinBox.setToolTip( 'Specify field of view in degrees for Gobo Camera.\n'
                                     'it also sets Frustum H and V Angle accordingly.' )

        fovLayout.addWidget( self.fovQSpinBox )

        ########################################################################
        # Create status Label widget
        ########################################################################
        self.statusQLabel = ddGui.QtWidgets.QLabel( 'Gobo setup exists!' )
        self.statusQLabel.setVisible( False )

        mainLayout.addWidget( self.statusQLabel )

        ########################################################################
        # Create widget for select parent for Camera
        ########################################################################
        self.parentQRadioButton = ddGui.QtWidgets.QRadioButton(
            'Use Parent to position Camera?'                  )
        self.parentQRadioButton.setVisible( False )

        self.groupParentQRadioButton = ddGui.QtWidgets.QButtonGroup( self )
        self.groupParentQRadioButton.addButton( self.parentQRadioButton ,
                                                1                       )
        self.groupParentQRadioButton.setExclusive( False )

        self.parentsQComboBox = ddGui.QtWidgets.QComboBox()
        self.parentsQComboBox.setVisible( False )

        ########################################################################
        # Create widget to select parent for selected light.
        ########################################################################
        self.newParentQRadioButton = ddGui.QtWidgets.QRadioButton(
            'Use Parent to position Camera?'                     )
        self.newParentQRadioButton.setVisible( False )

        self.groupNewParentRadioButton = ddGui.QtWidgets.QButtonGroup( self )
        self.groupNewParentRadioButton.addButton( self.newParentQRadioButton ,
                                                  1                          )
        self.groupNewParentRadioButton.setExclusive( False )

        self.newParentsQComboBox = ddGui.QtWidgets.QComboBox()
        self.newParentsQComboBox.setVisible( False )

        ########################################################################
        # Create widgets to list shot names
        ########################################################################
        self.selectShotsQLabel = ddGui.QtWidgets.QLabel( 'Select a shot' )
        self.listView = ddGui.QtWidgets.QListView()
        self.listView.setToolTip( 'Gets render graphs under selected shots\n'
                                  'and connects to Gobo render pass.'       )

        # Create an empty model for the list's data
        model = ddGui.QtGui.QStandardItemModel( self.listView )
        for entityName , entity in self.getShots():
            # create an item with a caption
            item = ddGui.QtGui.QStandardItem( entityName )
            item.setData( entity )
            # Add the item to the model
            model.appendRow( item )

        # Apply the model to the list view
        self.listView.setModel( model )
        self.listView.setSelectionMode(
            ddGui.QtWidgets.QAbstractItemView.SingleSelection )

        mainLayout.addWidget( self.selectShotsQLabel )
        mainLayout.addWidget( self.listView )
        mainLayout.addLayout( fovLayout )

        mainLayout.addWidget( self.parentQRadioButton )
        mainLayout.addWidget( self.parentsQComboBox   )

        mainLayout.addWidget( self.newParentQRadioButton )
        mainLayout.addWidget( self.newParentsQComboBox   )

        ########################################################################
        # Create button layout
        ########################################################################
        self.buttonBox = ddGui.QtWidgets.QDialogButtonBox(
            ddGui.QtWidgets.QDialogButtonBox.Cancel |
            ddGui.QtWidgets.QDialogButtonBox.Ok     )

        mainLayout.addWidget( self.buttonBox )

        ########################################################################
        # Connect signals
        ########################################################################
        self.buttonBox.accepted.connect( self.accept )
        self.buttonBox.rejected.connect( self.close  )
        self.parentQRadioButton.toggled.connect( self.populateParentsQComboBox )
        self.newParentQRadioButton.toggled.connect( self.populateNewParentsQComboBox )
        self.newParentsQComboBox.currentIndexChanged.connect( self.onNewParentsQComboBoxChange )
        self.parentsQComboBox.currentIndexChanged.connect( self.onParentsQComboBoxChange )

        return

    def accept( self ):
        '''Create gobo map setup on click Accept button.

        @return(None):
        No return value.
        '''

        fovAngle = None
        if self.fovQSpinBox.value():
            fovAngle = int( self.fovQSpinBox.value() )

        if not self.listView.selectedIndexes() and self.__statusMsg != 'Exists':
            warningMsg = ddGui.view.messageBox.DDMessageBox(
                ddGui.QtWidgets.QMessageBox.Warning        ,
                'Warning'                                  ,
                'You need to select a shot'                )
            warningMsg.exec_()

            return

        elif self.__statusMsg == 'Exists':

            self.close()

            return

        #Node to use for constraint camera
        if self.newParentQRadioButton.isChecked():
            lightNode = self.parentsQComboBox.itemData(
                    self.parentsQComboBox.currentIndex() )

            parentInstanceNode = self.newParentsQComboBox.itemData(
                self.newParentsQComboBox.currentIndex() )

            if parentInstanceNode is None:
                parentInstanceNode = lightNode

            self.__goboSetup.createGoboSetup( self.listView.selectedIndexes() ,
                                              fovAngle                        ,
                                              parentInstanceNode              ,
                                              inLightNode = lightNode         )

        else:
            parentInstanceNode = self.parentsQComboBox.itemData(
                self.parentsQComboBox.currentIndex() )

            self.__goboSetup.createGoboSetup( self.listView.selectedIndexes() ,
                                              fovAngle                        ,
                                              parentInstanceNode              )

        infoBox = ddGui.view.messageBox.DDMessageBox(
            ddGui.QtWidgets.QMessageBox.Information   ,
            'Information'                             ,
            'Gobo Setup {}!'.format( self.__statusMsg ) )
        infoBox.exec_()

        return super( DLCreateGoboMapSetup , self ).accept()

    @staticmethod
    def getShots():
        ''' Get shots in current scene file.

        @return(generator[ tuple( str, ddPipeApi.DDShot ) ] ):
        ('EntityName', entity):
        '''

        scene = dlGuerillaApi.DLScene()
        entitiesList = scene.entities

        for entityName , entity in sorted(
                ( entity.name ,
                  entity      ) for entity in entitiesList ):
            if ( isinstance( entity , ddPipeApi.DDShot ) and not entity.isOmitted() ):
                yield entityName , entity

        return

    def showEvent( self     ,
                   inQEvent ):
        '''Refresh at show.

        @param (ddGui.QtCore.QEvent) inQEvent:
        QEvent.

        @return (None):
        No return value.
        '''

        self.__currentSelection = list(
            ddGuerillaApi.DDScene.getSelection() )[ 0 ]

        self.__goboSetup = dlGuerillaTools.DLGoboMapSetup(
            self.__currentSelection                      )

        if self.__goboSetup._isLightAttributes:
            self.parentQRadioButton.setText( 'Select Light to Override' )

        if self.__goboSetup.existsGoboRenderGraph():
            self.__statusMsg = 'Exists'
            self.updateUI()

            super( DLCreateGoboMapSetup , self ).showEvent( inQEvent )

            return

        if self.__goboSetup._isSelectionConnected:
            self.parentQRadioButton.setVisible( True )

        if self.__goboSetup.getFalloffHAngle():
            self.fovQSpinBox.setValue(
                round( self.__goboSetup.getFalloffHAngle() * 2 ) )

        super( DLCreateGoboMapSetup , self ).showEvent( inQEvent )

        return

    def onNewParentsQComboBoxChange( self        ,
                                     inSignalInt ):
        '''Change selection in guerilla based on selection in newParentsQComboBox.

        @param(int) inSignalInt:
        Integer representing index of selection in comboBox.

        @return(None):
        No return value.
        '''

        elementObject = self.newParentsQComboBox.itemData( inSignalInt )

        elementObject.select()

        return

    def onParentsQComboBoxChange( self        ,
                                  inSignalInt ):
        '''Change selection in guerilla based on selection in ParentsQComboBox.

        @param(int) inSignalInt:
        Integer representing index of selection in comboBox.

        @return(None):
        No return value.
        '''

        elementObject = self.parentsQComboBox.itemData( inSignalInt )

        elementObject.select()

        return

    def populateParentsQComboBox( self         ,
                                  inSignalBool ):
        '''Shows combo box with elements to select for constraining the camera.

        @param( bool ) inSignalBool.
        Widget signal.

        @return(None):
        No return value.
        '''

        if inSignalBool:
            if not self.listView.selectedIndexes():
                warningMsg = ddGui.view.messageBox.DDMessageBox(
                        ddGui.QtWidgets.QMessageBox.Warning ,
                        'Warning' ,
                        'You need to select at least one shot' )
                warningMsg.exec_()

                self.parentQRadioButton.setChecked( False )

                return

            else:
                self.parentsQComboBox.clear()

                parentNodes = self.__goboSetup.getParentInstancesNodes(
                    self.__currentSelection                           )

                elements = self.__goboSetup.getSelectedParentInstances(
                    self.listView.selectedIndexes()                   ,
                    parentNodes                                       )

                for element in elements:
                    self.parentsQComboBox.addItem( element.name , element )

                self.setFixedSize( self._DL_EXPANDED_SIZE )
                self.parentsQComboBox.setVisible( True )

                if self.__goboSetup._isLightAttributes:
                    self.newParentQRadioButton.setVisible( True )

        else:
            self.newParentQRadioButton.setVisible( False )

            self.parentsQComboBox.clear()
            self.parentsQComboBox.setVisible( False )
            self.setFixedSize( self._DL_NORMAL_SIZE )

        return

    def populateNewParentsQComboBox( self         ,
                                     inSignalBool ):
        '''Shows combo box with elements to select for constraining the camera.

        @param( bool ) inSignalBool.
        Widget signal.

        @return(None):
        No return value.
        '''

        if inSignalBool:
            if not self.listView.selectedIndexes():
                warningMsg = ddGui.view.messageBox.DDMessageBox(
                        ddGui.QtWidgets.QMessageBox.Warning ,
                        'Warning' ,
                        'You need to select at least one shot' )
                warningMsg.exec_()

                self.newParentQRadioButton.setChecked( False )

                return

            else:
                #Disabling parentQRadioButton and related comboBox.
                self.parentQRadioButton.setEnabled( False )
                self.parentsQComboBox.setEnabled( False )

                self.newParentsQComboBox.clear()

                lightNode = self.parentsQComboBox.itemData(
                    self.parentsQComboBox.currentIndex()  )

                parentNodes = self.__goboSetup.getParentInstancesNodes(
                    lightNode                                         )

                elements = self.__goboSetup.getSelectedLightParentInstances(
                    self.listView.selectedIndexes()                        ,
                    parentNodes                                            )

                for element in elements:
                    self.newParentsQComboBox.addItem( element.name , element )

                self.setFixedSize( self._DL_EXPANDED_SIZE )

                self.newParentsQComboBox.setVisible( True )
        else:

            self.parentQRadioButton.setEnabled( True )
            self.parentsQComboBox.setEnabled( True )

            self.newParentsQComboBox.clear()
            self.newParentsQComboBox.setVisible( False )

        return

    def updateUI( self ):
        '''Updates UI if gobo setup already exists.

        @return (None):
        No return value.
        '''
        self.setWindowTitle( 'GoboMap setup exists!' )

        self.setFixedSize( 220 ,
                           100 )

        self.selectShotsQLabel.setVisible( False )
        self.listView.clearSelection()
        self.listView.setVisible( False )

        self.fovQLabel.setVisible( False )
        self.fovQSpinBox.setVisible( False )

        self.parentQRadioButton.setVisible( False )
        self.parentsQComboBox.setVisible( False )

        self.newParentQRadioButton.setVisible( False )
        self.newParentsQComboBox.setVisible( False )

        self.statusQLabel.setVisible( True )

        self.buttonBox.button(
            ddGui.QtWidgets.QDialogButtonBox.Cancel ).setVisible( False )

        return
