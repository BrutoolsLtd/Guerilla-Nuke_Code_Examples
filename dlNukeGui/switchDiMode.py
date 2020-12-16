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
'''dlNukeGui to switch all tbvDiCreate and tbvDiOutput
nuke gizmo nodes between Compositing and DI.

@package dlNukeGui.switchDiMode
@author Esteban Ortega <esteban.ortega@laterlieranimation.com>
'''

import ddNukeApi

import ddGui

__all__ = ( )

class DLSwitchDiModeDialog( ddGui.QtWidgets.QDialog ):
    '''Dialog to switch between (compositing and DI) all tbvDiCreate
    and tbvDiOutput nuke gizmos in the current script.
    '''

    ## Stores modes for gizmo node
    # type: []

    _DL_MODES = ( 'Compositing' ,
                  'DI'          )

    def __init__( self       ,
                  *inArgs    ,
                  **inKWArgs ):
        '''Initialize the Dialog.

        return(None):
        No return value.
        '''

        super( DLSwitchDiModeDialog , self ).__init__( *inArgs    ,
                                                       **inKWArgs )

        self.setWindowTitle( 'Switch DiMode' )

        mainLayout = ddGui.QtWidgets.QVBoxLayout()
        self.setLayout( mainLayout )
        self.setFixedSize( 180 ,
                           100 )

        ########################################################################
        # Create ComboBox
        ########################################################################
        self.diModeQComboBox = ddGui.QtWidgets.QComboBox()
        self.diModeQComboBox.addItems( self._DL_MODES )

        mainLayout.addWidget( self.diModeQComboBox )

        ########################################################################
        # Create Button layout
        ########################################################################
        self.buttonBox = ddGui.QtWidgets.QDialogButtonBox(
            ddGui.QtWidgets.QDialogButtonBox.Ok     |
            ddGui.QtWidgets.QDialogButtonBox.Cancel )
        mainLayout.addWidget( self.buttonBox )

        ########################################################################
        # Connect Signals
        ########################################################################
        self.buttonBox.accepted.connect( self.onAccept )
        self.buttonBox.rejected.connect( self.close )

    def onAccept( self ):
        '''Execute when accept button is clicked.

        @return(None):
        No return value.
        '''

        diMode           = self.diModeQComboBox.currentIndex()
        classTargetNodes = [ 'tbvDiOutput' ,
                             'tbvDiCreate' ]

        for node in ddNukeApi.DDRoot().findAll():
            if node.Class() in classTargetNodes:
                node.knob( 'mode' ).setValue( diMode )

        self.close()

        return
