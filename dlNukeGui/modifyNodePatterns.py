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
'''dlNukeGui to modify default DeepOpenEXRId patterns knob.

@package dlNukeGui.modifyNodePatterns
@author Esteban Ortega <esteban.ortega@laterlieranimation.com>
'''

import nuke

import ddGui

import dlNukeApi

__all_ = ( 'DLModifyNodePatterns' , )

class DLModifyNodePatterns( ddGui.QtWidgets.QDialog ):
    '''Dialog to select how DeepOpenEXRId's  knob patterns will be processed.
    '''

    def __init__( self       ,
                  *inArgs    ,
                  **inKWArgs ):
        '''Initialize the Dialog.

        return(None):
        No return value.
        '''

        ## Stores DeepOpenEXRId nodes.
        # type: []
        self.__nodes = []

        super( DLModifyNodePatterns , self ).__init__( *inArgs    ,
                                                       **inKWArgs )

        self.setWindowTitle( 'Patterns to object name' )

        mainLayout = ddGui.QtWidgets.QVBoxLayout()
        self.setLayout( mainLayout )
        self.setFixedSize( 250 ,
                           120 )

        ########################################################################
        # Create Check boxes.
        ########################################################################
        checkBoxesLayout = ddGui.QtWidgets.QVBoxLayout()

        toTagOnlyQRadioButton = ddGui.QtWidgets.QRadioButton(
            text = 'Tags Only'                              )
        toTagOnlyQRadioButton.setChecked( True )

        toAbsolutePathQRadioButton = ddGui.QtWidgets.QRadioButton(
            text = 'Absolute Path'                               )

        toObjectNameQRadioButton = ddGui.QtWidgets.QRadioButton(
            text = 'Object Name'                               )

        self.checkBoxGrp = ddGui.QtWidgets.QButtonGroup( self )
        self.checkBoxGrp.addButton( toTagOnlyQRadioButton ,
                                    1                     )
        self.checkBoxGrp.addButton( toAbsolutePathQRadioButton ,
                                    2                          )
        self.checkBoxGrp.addButton( toObjectNameQRadioButton ,
                                    3                        )

        checkBoxesLayout.addWidget( toTagOnlyQRadioButton )
        checkBoxesLayout.addWidget( toAbsolutePathQRadioButton )
        checkBoxesLayout.addWidget( toObjectNameQRadioButton )

        mainLayout.addLayout( checkBoxesLayout )

        ########################################################################
        # Create Button layout
        ########################################################################
        buttonBox = ddGui.QtWidgets.QDialogButtonBox(
            ddGui.QtWidgets.QDialogButtonBox.Ok     |
            ddGui.QtWidgets.QDialogButtonBox.Cancel )
        mainLayout.addWidget( buttonBox )

        ########################################################################
        # Connect signals
        ########################################################################
        buttonBox.accepted.connect( self.onAccept )
        buttonBox.rejected.connect( self.close )

        return

    def onAccept( self ):
        '''Execute when accept button is clicked.

        @return(None):
        No return value.
        '''

        id = self.checkBoxGrp.checkedId()

        for node in self.__nodes:
            dlDeepNode = dlNukeApi.DLDeepOpenExrId( node )

            if id == 1:
                dlDeepNode.setPatternToTagsOnly()

            elif id == 2:
                dlDeepNode.setPatternToNoShapeName()

            elif id == 3:
                dlDeepNode.setPatternToObjectName()

        self.close()

        return

    def showEvent( self     ,
                   inQEvent ):
        '''Refresh on show.

        @param (ddGui.QtCore.QEvent) inQEvent:
        QEvent.

        @return (None):
        No return value.
        '''

        self.__nodes = [ node for node in nuke.selectedNodes() if
                         node.Class() == 'DeepOpenEXRId'        ]

        super( DLModifyNodePatterns , self ).showEvent( inQEvent )

        return
