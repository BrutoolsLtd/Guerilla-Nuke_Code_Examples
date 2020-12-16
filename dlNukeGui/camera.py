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
'''dlNukeGui to split camera and chose amount of over scan.

@package dlNukeGui.setCameraMain
@author Esteban Ortega <esteban.ortega@laterlieranimation.com>
'''

import nuke

import ddGui

import dlNukePipe.camera

__all_ = ( 'DLCameraMainDialog' , )

class DLCameraMainDialog( ddGui.QtWidgets.QDialog ):
    '''Dialog to set main camera (CamMain) select amount of over scan
     and split stereo camera.
    '''

    def __init__( self       ,
                  *inArgs    ,
                  **inKWArgs ):
        '''Initialize the Dialog.

        return(None):
        No return value.
        '''

        ## Stores current selection.
        # type: []
        self.cameraNodes = []

        ## String representing the status for msg on accept.
        # type: str
        self.__statusMsg = ''

        super( DLCameraMainDialog , self ).__init__( *inArgs    ,
                                                     **inKWArgs )

        self.setWindowTitle( 'Set Main Camera' )

        mainLayout = ddGui.QtWidgets.QVBoxLayout()
        self.setLayout( mainLayout )
        self.setFixedSize( 250 ,
                           150 )

        ########################################################################
        # Create Check boxes.
        ########################################################################
        self.infoLabel = ddGui.QtWidgets.QLabel( 'Select Overscan %' )
        self.infoLabel.setAlignment( ddGui.QtCore.Qt.AlignCenter )
        checkBoxesLayout = ddGui.QtWidgets.QHBoxLayout()

        self.overscan0QRadioButton = ddGui.QtWidgets.QRadioButton(
            text = '0%'                                         )
        self.overscan0QRadioButton.setChecked( True )

        self.overscan1QRadioButton = ddGui.QtWidgets.QRadioButton(
            text = '1%'                                          )

        self.overscan4QRadioButton = ddGui.QtWidgets.QRadioButton(
            text = '4%'                                          )

        self.checkBoxGrp = ddGui.QtWidgets.QButtonGroup( self )
        self.checkBoxGrp.addButton( self.overscan0QRadioButton ,
                                    1 )
        self.checkBoxGrp.addButton( self.overscan1QRadioButton ,
                                    2                          )
        self.checkBoxGrp.addButton( self.overscan4QRadioButton ,
                                    3                          )

        checkBoxesLayout.addWidget( self.overscan0QRadioButton )
        checkBoxesLayout.addWidget( self.overscan1QRadioButton )
        checkBoxesLayout.addWidget( self.overscan4QRadioButton )

        mainLayout.addWidget( self.infoLabel   )
        mainLayout.addLayout( checkBoxesLayout )

        ########################################################################
        # Create a separator
        ########################################################################
        self.separatorQLabel = ddGui.QtWidgets.QLabel()
        self.separatorQLabel.setFrameStyle( ddGui.QtWidgets.QFrame.HLine  |
                                            ddGui.QtWidgets.QFrame.Sunken )
        mainLayout.addWidget( self.separatorQLabel )

        ########################################################################
        # Create a radio button for split stereo camera.
        ########################################################################
        self.splitStereoCamQRadioButton = ddGui.QtWidgets.QRadioButton(
            text = 'Split Stereo Camera L/R'                          )
        mainLayout.addWidget( self.splitStereoCamQRadioButton )

        ########################################################################
        # Create Button layout
        ########################################################################
        self.buttonBox = ddGui.QtWidgets.QDialogButtonBox(
            ddGui.QtWidgets.QDialogButtonBox.Ok     |
            ddGui.QtWidgets.QDialogButtonBox.Cancel )
        mainLayout.addWidget( self.buttonBox )

        ########################################################################
        # Connect signals
        ########################################################################
        self.buttonBox.accepted.connect( self.onAccept )
        self.buttonBox.rejected.connect( self.close )

        return

    def onAccept( self ):
        '''Execute when accept button is clicked.

        @return(None):
        No return value.
        '''

        id = self.checkBoxGrp.checkedId()
        splitStereoCam = self.splitStereoCamQRadioButton.isChecked()

        if self.__statusMsg == 'Empty':

            self.close()

            return

        if self.__statusMsg == 'Exists':
            renameNodeBool = False
        else:
            renameNodeBool = True

        overscan = None

        if id == 1:
            overscan = 1.0

        elif id == 2:
            overscan = 1.01

        elif id == 3:
            overscan = 1.04

        for cameraNode in self.cameraNodes:
            selectedNode = nuke.toNode( cameraNode.name() )
            mainCamera = dlNukePipe.camera.DLCamera()
            mainCamera.setCamera( selectedNode   ,
                                  overscan       ,
                                  renameNodeBool ,
                                  splitStereoCam )

        self.close()

        return

    def checkCameras( self ):
        '''Check if cameras already exists.

        @return(bool):
        Return True y camera exist False otherwise
        '''

        camExceptList = [ 'CamMain'       ,
                          'CamMainL'      ,
                          'CamMainR'      ,
                          'CamMainStereo' ]

        allCameras     = nuke.allNodes('Camera2')
        allCameraNames = [ cam.name() for cam in allCameras ]

        if any( cameraName in allCameraNames for cameraName in camExceptList ):
                return True

        return False

    def showEvent( self     ,
                   inQEvent ):
        '''Refresh on show.

        @param (ddGui.QtCore.QEvent) inQEvent:
        QEvent.

        @return (None):
        No return value.
        '''

        self.cameraNodes = [ node for node in nuke.selectedNodes() if
                             node.Class() == 'Camera2'              ]

        if not self.cameraNodes:
            self.__statusMsg = 'Empty'

            self.updateUiNoSelection()

            super( DLCameraMainDialog , self ).showEvent( inQEvent )

            return

        if self.checkCameras():
            self.__statusMsg = 'Exists'

            self.updateUiCameraExists()

            super( DLCameraMainDialog , self ).showEvent( inQEvent )

        super( DLCameraMainDialog , self ).showEvent( inQEvent )

        return

    def updateUiNoSelection( self ):
        '''updates UI

        @return (None):
        No return value.
        '''

        self.setFixedSize( 250 ,
                           80  )

        self.infoLabel.setText( 'Select a camera node' )

        self.overscan0QRadioButton.setVisible( False )
        self.overscan1QRadioButton.setVisible( False )
        self.overscan4QRadioButton.setVisible( False )
        self.splitStereoCamQRadioButton.setVisible( False )
        self.separatorQLabel.setVisible( False )
        self.buttonBox.button(
            ddGui.QtWidgets.QDialogButtonBox.Cancel ).setVisible( False )

        return

    def updateUiCameraExists( self ):
        '''Update UI when camera already exists.

        @return (None):
        No return value.
        '''

        self.setFixedSize( 250 ,
                           180 )

        self.infoLabel.setText( 'CamMain Component already Exist!\n'
                                'Create Generic Stereo Camera?\n\n'
                                'Select Overscan %'                )

        return
