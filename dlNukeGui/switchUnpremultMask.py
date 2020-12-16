################################################################################
# L ATELIER ANIMATION INC.
#
# [2012] - [2020] L ATELIER ANIMATION INC. All Rights Reserved.
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
'''dlNukeGui to switch unpremult Mask knob in gizmos, if input is connected.

@package dlNukeGui.switchUnpremultMask
@author Esteban Ortega <esteban.ortega@laterlieranimation.com>
'''

import ddQt

import ddNukeApi

__all__ = ( 'DLSwitchUnpremultMask' , )

class DLSwitchUnpremultMask( ddQt.QtWidgets.QDialog ):
    '''Dialog to select which gizmo to switch ON OFF unpremult Mask knob.
    '''

    ## Target Gizmos type names which can be modified.
    # type: tuple[str]
    DL_GIZMO_TYPE_NAMES = ( 'tbvContributionCc' ,
                            'tbvAlbedoCc'       ,
                            'tbvChannelCc'      ,
                            'tbvEyeCc'          ,
                            'tbvEyePolish'      ,
                            'tbvIncandescent'   ,
                            'tbvLightShadeCc'   ,
                            'tbvSpecularCc'     )

    def __init__( self       ,
                  *inArgs    ,
                  **inKWArgs ):
        '''Initialize the Dialog.

        @return (None):
        No return value.
        '''

        super( DLSwitchUnpremultMask , self ).__init__( *inArgs    ,
                                                        **inKWArgs )

        self.setWindowTitle( 'Switch Unpremult Mask' )

        mainLayout = ddQt.QtWidgets.QVBoxLayout()
        self.setLayout( mainLayout )
        self.setFixedSize( 250 ,
                           240 )

        ########################################################################
        # Create Check All box
        ########################################################################
        checkBoxAll = ddQt.QtWidgets.QRadioButton( text = 'Check All' )
        checkBoxAll.setChecked( True )

        mainLayout.addWidget( checkBoxAll )

        ########################################################################
        # Create a separator
        ########################################################################
        separatorQLabel = ddQt.QtWidgets.QLabel()
        separatorQLabel.setFrameStyle( ddQt.QtWidgets.QFrame.HLine  |
                                       ddQt.QtWidgets.QFrame.Sunken )
        mainLayout.addWidget( separatorQLabel )

        ########################################################################
        # Create Check boxes.
        ########################################################################
        self.__checkBoxLayout = ddQt.QtWidgets.QVBoxLayout()

        for gizmoClass in self.DL_GIZMO_TYPE_NAMES:

            checkBox = ddQt.QtWidgets.QRadioButton( text = gizmoClass )
            checkBox.setAutoExclusive( False )
            checkBox.setChecked( True )

            self.__checkBoxLayout.addWidget( checkBox )

        mainLayout.addLayout( self.__checkBoxLayout )

        ########################################################################
        # Create Button layout
        ########################################################################
        buttonBox = ddQt.QtWidgets.QDialogButtonBox(
            ddQt.QtWidgets.QDialogButtonBox.Ok     |
            ddQt.QtWidgets.QDialogButtonBox.Cancel )
        mainLayout.addWidget( buttonBox )

        ########################################################################
        # Connect signals
        ########################################################################
        buttonBox.accepted.connect( self.__onAccept )
        buttonBox.rejected.connect( self.close )
        checkBoxAll.toggled.connect( self.__onToggleCheckAll )

        return

    def __onAccept( self ):
        '''Execute when accept button is clicked.

        @return (None):
        No return value.
        '''

        root = ddNukeApi.DDRoot()

        nodesClassToSwitch = []

        for index in xrange( self.__checkBoxLayout.count() ):

            widget = self.__checkBoxLayout.itemAt( index ).widget()

            if widget.isChecked():

                nodesClassToSwitch.append( widget.text() )

        if not nodesClassToSwitch:

            self.close()

            return

        for node in root.findAll(
            ddNukeApi.filters.DDClassType( nodesClassToSwitch ) ):

            if node.input( 1 ) is not None:

                node.knob( 'unPremult' ).setValue( True )

        self.close()

        return

    def __onToggleCheckAll( self          ,
                            inCheckedBool ):
        '''Will toggle all widgets QRadioButtons in self.checkBoxLayout.

        @param (bool) inCheckedBool:
        Bool representing check or un check.

        @return (None):
        No return value.
        '''

        for index in range( self.__checkBoxLayout.count() ):

            widget = self.__checkBoxLayout.itemAt( index ).widget()
            widget.setChecked( inCheckedBool )

        return
