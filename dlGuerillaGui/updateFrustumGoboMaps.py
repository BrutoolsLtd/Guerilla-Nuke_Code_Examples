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
'''Guerilla tool UI to update Frustum GoboMaps with published goboMaps if any.

@package dlGuerillaGui.updateFrustumGoboMaps
@author Esteban Ortega <esteban.ortega@latelieranimation.com>
'''

import os
import re

import guerilla

import dlAction
import dlConstants
import dlGuerillaTools

import ddConstants.guerilla
import ddGuerillaApi
import ddGui
import ddPath

__all__ = ( 'DLUpdateFrustumGoboMapsDialog' , )

class DLUpdateFrustumGoboMapsDialog( ddGui.QtWidgets.QDialog ):
    '''Dialog to update and report gobo frustum maps status.
    '''

    ## Define color for QtreeWidgetItem when updated (green).
    # type: QColor
    _DL_UPDATE_COLOR = ddGui.QtGui.QColor( 120 ,
                                           255 ,
                                           160 )

    ## Define color for QtreeWidgetItem when there is a publish file
    # will update.
    # type: QColor
    _DL_WILL_UPDATE_COLOR = ddGui.QtGui.QColor( 240 ,
                                                160 ,
                                                255 )

    ## Define status for gobo map.
    # type: tuple
    _DL_STATUS = ( 'Published'               ,
                   'Updated'                 ,
                   'Will update'             ,
                   'Offpipe / Not Published' ,
                   'Empty File Path'         )

    ## Define pattern to find path str.
    # type: sre.SRE_Pattern
    DL_GROUP_PATTERN = re.compile( '\'(?P<path>.*)\'' )

    def __init__( self ):
        super( DLUpdateFrustumGoboMapsDialog , self ).__init__()

        self.setWindowTitle( 'Update frustum\'s gobo map' )
        self.setMinimumSize( 1000 ,
                             200  )

        self.setWindowFlags( ddGui.QtCore.Qt.WindowStaysOnTopHint )

        mainLayout = ddGui.QtWidgets.QVBoxLayout()

        self.setLayout( mainLayout )

        ########################################################################
        # Create text labels
        ########################################################################
        self.msgQLabel = ddGui.QtWidgets.QLabel(
            'There is No Gobo Frustum to update!' )
        self.msgQLabel.setStyleSheet( 'color: Chocolate' )
        self.msgQLabel.setVisible( False )

        ########################################################################
        # Create QTreeWidget
        ########################################################################
        self.treeWidget = ddGui.QtWidgets.QTreeWidget()
        self.treeWidget.setContextMenuPolicy( ddGui.QtGui.Qt.CustomContextMenu )
        self.treeWidget.setToolTip(
            '- Ctrl + click to select non consecutive elements.\n'
            '- Shift + click to select consecutive elements.\n'
            '- Click + drag to select consecutive elements.\n'
            '- Ctrl + click on selected element will deselect it.\n'
            '- To deselect all, select only one element (click)\n'
            '  then Ctrl + click in same element.'                 )

        self.treeWidget.setSortingEnabled( True )
        self.treeWidget.setSelectionMode(
            ddGui.QtWidgets.QAbstractItemView.ExtendedSelection )
        self.treeWidget.setSelectionBehavior(
            ddGui.QtWidgets.QAbstractItemView.SelectItems )
        self.treeWidget.setAlternatingRowColors( True )

        self.treeWidget.setColumnCount( 6 )
        self.treeWidget.resizeColumnToContents( 0 )
        self.treeWidget.setColumnWidth( 0   ,
                                        100 )
        self.treeWidget.setColumnWidth( 1   ,
                                        200 )

        self.treeWidget.setHeaderLabels( [ 'Light Name'        ,
                                           'Frustum Full Name' ,
                                           'Status'            ,
                                           'File Path'         ,
                                           'Version'           ,
                                           'Nuke script'       ] )

        ########################################################################
        # Create progress bar
        ########################################################################
        self.progressQProgressBar = ddGui.QtWidgets.QProgressBar()
        self.progressQProgressBar.setVisible( False )
        self.progressQProgressBar.setFormat( '%p% / %m Frustum Nodes' )

        ########################################################################
        # Create button layout
        ########################################################################
        self.buttonBox = ddGui.QtWidgets.QDialogButtonBox(
            ddGui.QtWidgets.QDialogButtonBox.Cancel      |
            ddGui.QtWidgets.QDialogButtonBox.Ok          )

        self.buttonBox.button( ddGui.QtWidgets.QDialogButtonBox.Ok ).setText(
            'Update All'                                                    )

        ########################################################################
        # Add widgets to layout
        ########################################################################
        mainLayout.addWidget( self.treeWidget )
        mainLayout.addWidget( self.progressQProgressBar )
        mainLayout.addWidget( self.msgQLabel )
        mainLayout.addWidget( self.buttonBox )

        ########################################################################
        # Msgbox when all frustum goboMaps are target to update.
        ########################################################################
        self.msgBox = ddGui.QtWidgets.QMessageBox( parent = self )
        self.msgBox.setText( "This will update all frustum's gobo maps nodes" )
        self.msgBox.setInformativeText( "Do you want to proceed?" )
        self.msgBox.setStandardButtons(
            ddGui.QtWidgets.QMessageBox.Cancel |
            ddGui.QtWidgets.QMessageBox.Ok     )

        ########################################################################
        # Context menu and actions
        ########################################################################
        self.rightClickMenu = ddGui.QtGui.QMenu( 'ContextMenu' )

        self.actionMenuOpenNuke  = ddGui.QtGui.QAction( 'Open Nuke Script' )
        self.actionMenuFindLight = ddGui.QtGui.QAction( 'Go to Light Location' )

        ########################################################################
        # Connect signals
        ########################################################################
        self.buttonBox.accepted.connect( self.updateGoboMaps )
        self.buttonBox.rejected.connect( self.close )
        self.treeWidget.itemSelectionChanged.connect( self.onSelectionChange )
        self.treeWidget.customContextMenuRequested.connect( self.onRightClick )

    def browseLocation( self ):
        '''Will update browser window with selected light location.

        @return (None):
        No return value.
        '''

        items = self.treeWidget.selectedItems()

        frustumNode = ddGuerillaApi.DDNode( items[ 0 ].text( 1 ) )
        lightNode = frustumNode.parent

        guerilla.ui.focusview( 'Browser' )
        browserWindows = guerilla.ui.getactiveview()

        lightNode.select()

        guerilla.ui.editnode( lightNode.parent  ,
                              lightNode         ,
                              browserWindows    )

        return

    def checkForUpdates( self ):
        '''Checks if there is gobo maps published to update.

        @return(bool):
        Returns True if there is something to update, False otherwise.
        '''

        updates = []

        for index in range( self.treeWidget.topLevelItemCount() ):

            item = self.treeWidget.topLevelItem( index )
            status = item.text( 2 )

            if status == self._DL_STATUS[ 2 ]:
                updates.append( index )

        return updates

    @staticmethod
    def getGoboFrustums():
        '''Gets all light's shader frustums

        @return(list):
        List of ddGuerillaApi.DDNode nodes.
        '''

        scene = ddGuerillaApi.DDScene()
        frustumNodes = []

        nodeTypeFilter = ddGuerillaApi.filters.DDExactTypeName(
            ( ddConstants.guerilla.nodeType.DD_RGN_LIGHT            ,
              ddConstants.guerilla.nodeType.DD_RGN_LIGHT_ATTRIBUTES ) )

        for nodeLight in scene.findAll( nodeTypeFilter         ,
                                        inRecursiveBool = True ):

            frustumNode = nodeLight.findChild(
                dlConstants.guerilla.goboLightShaderName.DL_GOBO_FRUSTUM_SHADER_NAME )

            oldFrustumNode = nodeLight.findChild( 'Frustum' )

            if frustumNode:
                frustumNodes.append( frustumNode )

            elif oldFrustumNode is not None:
                frustumNodes.append( oldFrustumNode )

        return frustumNodes

    def getLinkedPublishedFile( self      ,
                                inPathStr ):
        '''Gets published file based on passed path str from frustum node
        if any and returns a published.

        @param(str) inPathStr:
        String representing path to image gobo map.

        @return(DDPublishFile):
        Return ddPipeApi.DDPublishFile if any, None otherwise.
        '''

        pathNode      = ddPath.DDFile( inPathStr )
        publishedFile = pathNode.getPublishedFile()

        if publishedFile:
            return publishedFile

        sequence      = pathNode.getSequence()
        if sequence is not None:
            try:
                firstFrame    = sequence.getFile( sequence.getFirstFrame() )
            except ValueError:
                return publishedFile
        else:
            return publishedFile

        if sequence.isSingleFrame():

            newFilePath = ( firstFrame.sequencePrefix[ :-1 ]                  +
                            str( ddConstants.fileExtensions.DD_FILE_EXT_TEX ) )

            newPath = ddPath.DDFile( newFilePath )
            if newPath.isLink():
                linkedFile = newPath.getLink()
                return linkedFile.getPublishedFile()

            else:
                return publishedFile
        else:

            linkedFile = firstFrame.getLink()
            if linkedFile:
                return linkedFile.getPublishedFile()

            else:
                return publishedFile

    def getNukeScriptPath( self      ,
                           inPathStr ):
        '''Gets nuke script path based on passed exr image path string.

        @param(str) inPathStr:
        String representing the path to tex file.

        @return(str):
        Path to Nuke script file which was used to render the file.
        '''

        pathNode = ddPath.DDFile( inPathStr )

        if pathNode.lexists():
            sequence = pathNode.getSequence()

            if sequence is None:
                return None

            else:
                try:
                    firstFrame = sequence.getFile( sequence.getFirstFrame() )

                except ValueError:
                    return None

            if sequence.isSingleFrame():
                newFilePath = (
                    firstFrame.changeExtension(
                        ddConstants.fileExtensions.DD_FILE_EXT_EXR ) )

                nukeFilePath = os.popen(
                    'exiftool -UpstreamFiles {}'.format( newFilePath ) )

                nukeFileStr = nukeFilePath.read()

                matches = self.DL_GROUP_PATTERN.search( nukeFileStr )

                if matches:
                    return matches.group( 'path' )

                else:
                    return None

        else:
            return None

    def onSelectionChange( self ):
        '''Executes when selection is changed in QTreeWidget.

        @return(None):
        No return value.
        '''

        if self.treeWidget.selectedItems():
            self.buttonBox.button(
                ddGui.QtWidgets.QDialogButtonBox.Ok ).setText( 'Update Selected' )
        else:
            self.buttonBox.button(
                ddGui.QtWidgets.QDialogButtonBox.Ok ).setText( 'Update All' )

        return

    def openPublishedNukeScript( self ):
        '''Will launch nuke and open nuke script.

        @return (None):
        No return value.
        '''

        items = self.treeWidget.selectedItems()

        ddPathNukeFile = ddPath.DDFile( items[ 0 ].text( 5 ) )
        nukePublishedFile = ddPathNukeFile.getPublishedFile()

        context = nukePublishedFile.getContext()
        projectShortName = context.project.shortName.lower()

        graph = dlAction.guerilla.DLOpenNukeScript(
            inLabelStr = 'Open Gobo Nuke script'        ,
            context    = context                        ,
            filePath   = nukePublishedFile.localPath    )

        dlGuerillaTools.launchNukeGraph( graph            ,
                                         projectShortName )

    def onRightClick( self     ,
                      inSignal ):
        '''Will execute when right click on QtreeWidget.

        @param (QtCore.QPoint) inSignal:
        QPoint object storing position of the right click.

        return (None):
        No return value.
        '''

        items = self.treeWidget.selectedItems()

        if len( items ) != 1:

            return

        self.rightClickMenu.clear()

        currentColumn = self.treeWidget.currentColumn()

        if currentColumn == 5:

            ddPathNukeFile = ddPath.DDFile( items[ 0 ].text( 5 ) )
            nukePublishedFile = ddPathNukeFile.getPublishedFile()

            if nukePublishedFile:

                self.rightClickMenu.addAction( self.actionMenuOpenNuke )
                self.actionMenuOpenNuke.triggered.connect(
                    self.openPublishedNukeScript         )

                self.rightClickMenu.exec_(
                    self.treeWidget.viewport().mapToGlobal( inSignal ) )

        elif currentColumn == 1 or currentColumn == 0:

            self.rightClickMenu.addAction( self.actionMenuFindLight )
            self.actionMenuFindLight.triggered.connect( self.browseLocation )

            self.rightClickMenu.exec_(
                self.treeWidget.viewport().mapToGlobal( inSignal ) )

        else:

            self.rightClickMenu.clear()

            return

        return

    def populateTreeWidget( self ):
        '''Gets goboMaps file status / data and populate treeWidget.

        @return(None):
        No return value.
        '''

        self.treeWidget.clear()

        frustums = self.getGoboFrustums()
        progress = 0

        if not frustums:
            self.msgQLabel.setVisible( True )

            return

        self.progressQProgressBar.setVisible( True )
        self.progressQProgressBar.setMaximum( len( frustums ) )

        for frustum in frustums:

            path       = frustum.Input5.Value.get()
            status     = self._DL_STATUS[ 4 ]
            version    = None
            nukeScript = None

            if path:

                publishedFile = self.getLinkedPublishedFile( path )
                if publishedFile:
                    # Check for a sequence and change padding
                    publishedFilePath = publishedFile.localPath

                    if isinstance( publishedFilePath , ddPath.sequence.DDSequence ):
                        if '%06d' == publishedFilePath.patternFrame:
                            publishedFilePath = (
                                publishedFilePath.convertToPattern(
                                    inPatternStr = ddPath.constant.DD_PATTERN_DOLLAR_FRAME ) )

                    if path == publishedFilePath:

                        status = self._DL_STATUS[ 0 ]
                        version    = publishedFile.versionNumber
                        nukeScript = publishedFile.work.name

                    else:
                        status = self._DL_STATUS[ 2 ]
                        nukeScript = self.getNukeScriptPath( path )
                        pathNode = ddPath.DDFile( path )
                        version = pathNode.getVersion()

                else:
                    status     = self._DL_STATUS[ 3 ]
                    nukeScript = self.getNukeScriptPath( path )
                    pathNode = ddPath.DDFile( path )
                    version = pathNode.getVersion()

            item = ddGui.QtWidgets.QTreeWidgetItem( [ frustum.parent.name     ,
                                                      frustum.fullName        ,
                                                      status                  ,
                                                      str( path )             ,
                                                      str( version )          ,
                                                      str( nukeScript )       ] )

            item.setTextAlignment( 4                            ,
                                   ddGui.QtCore.Qt.AlignHCenter )
            self.treeWidget.addTopLevelItem( item )

            if status == self._DL_STATUS[ 2 ]:
                for column in range( self.treeWidget.columnCount() ):
                    item.setBackgroundColor( column                     ,
                                             self._DL_WILL_UPDATE_COLOR )

            if status == self._DL_STATUS[ 0 ]:
                for column in range( self.treeWidget.columnCount() ):
                    item.setBackgroundColor( column                ,
                                             self._DL_UPDATE_COLOR )

            progress += 1

            self.progressQProgressBar.setValue( progress )

        self.treeWidget.resizeColumnToContents( 0 )
        self.treeWidget.setColumnWidth( 1   ,
                                        200 )

        #check if there is something to update
        if not self.checkForUpdates():
            self.updateMsgQLabel()

        return

    def showEvent( self     ,
                   inQEvent ):
        '''Executes when UI is shown.

        @param (ddGui.QtCore.QEvent) inQEvent:
        QEvent.

        @return (None):
        No return value.
        '''

        self.populateTreeWidget()

        return

    def updateGoboMaps( self ):
        '''Updates goboMap file's path with published file path if any.

        @return(None):
        No return value.
        '''

        if not self.checkForUpdates():
            self.updateMsgQLabel()

            return

        if self.buttonBox.button(
            ddGui.QtWidgets.QDialogButtonBox.Ok ).text() == 'Update All':

            if self.msgBox.exec_() == self.msgBox.Cancel :

                return

        self.progressQProgressBar.reset()

        progress    = 0
        version     = None
        nukeScript  = None
        widgetItems = []

        if self.treeWidget.selectedItems():

            widgetItems = self.treeWidget.selectedItems()
            self.progressQProgressBar.setMaximum( len( widgetItems ) )

        else:

            for index in range( self.treeWidget.topLevelItemCount() ):

                item = self.treeWidget.topLevelItem( index )

                if item.text( 2 ) == self._DL_STATUS[ 2 ]:
                    widgetItems.append( self.treeWidget.topLevelItem( index ) )

            self.progressQProgressBar.setMaximum( len( widgetItems ) )

        with ddGuerillaApi.DDModifier() as mod:

            for widgetItem in widgetItems:

                path            = widgetItem.text( 3 )
                frustumFullName = widgetItem.text( 1 )
                frustumNode     = ddGuerillaApi.DDNode( frustumFullName )
                status          = widgetItem.text( 2 )

                if status == self._DL_STATUS[ 0 ] or status == self._DL_STATUS[ 4 ]:

                    progress += 1
                    self.progressQProgressBar.setValue( progress )

                    continue

                if path:
                    # This can be in another definition to update
                    publishedFile = self.getLinkedPublishedFile( path )

                    if publishedFile:
                        # Check for a sequence and change padding
                        publishedFilePath = publishedFile.localPath

                        if isinstance( publishedFilePath          ,
                                       ddPath.sequence.DDSequence ):
                            if '%06d' == publishedFilePath.patternFrame:
                                publishedFilePath = (
                                    publishedFilePath.convertToPattern(
                                        inPatternStr = ddPath.constant.DD_PATTERN_DOLLAR_FRAME ) )


                        frustumNode.Input5.Value.set( publishedFilePath )

                        path       = publishedFilePath
                        status     = self._DL_STATUS[ 1 ]
                        version    = publishedFile.versionNumber
                        nukeScript = publishedFile.work.name

                    else:
                        nukeScript = self.getNukeScriptPath( path )
                        pathNode   = ddPath.DDFile( path )
                        version    = pathNode.getVersion()
                        status     = self._DL_STATUS[ 3 ]


                if status == self._DL_STATUS[ 1 ]:
                    for column in range( self.treeWidget.columnCount() ):
                        widgetItem.setBackgroundColor( column                ,
                                                       self._DL_UPDATE_COLOR )

                widgetItem.setText( 2      ,
                                    status )
                widgetItem.setText( 3           ,
                                    str( path ) )
                widgetItem.setText( 4              ,
                                    str( version ) )
                widgetItem.setText( 5                 ,
                                    str( nukeScript ) )

                progress += 1

                self.progressQProgressBar.setValue( progress )

        return

    def updateMsgQLabel( self ):
        '''Updates msgQLabel based on status of gobo maps.

        @return(None):
        No return type
        '''

        self.msgQLabel.setText( 'Frustum\'s gobo maps already updated!' )
        self.msgQLabel.setVisible( True )
        self.buttonBox.button(
            ddGui.QtWidgets.QDialogButtonBox.Ok ).setEnabled( False )

        return
