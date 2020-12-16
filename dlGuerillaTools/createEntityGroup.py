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
'''Guerilla tool to create an entity group or use and existing one along with
its new or existing RenderGraph to share between shots.

@package dlGuerillaCommands.createEntityGroup
@author Esteban Ortega <esteban.ortega@latelieranimation.com>
'''

import string

import dlGuerillaApi

import ddAction
import ddConstants.guerilla
import ddBuilder
import ddGui
import ddGui.helper
import ddGui.view.entityGroupCreateDialog
import ddGui.widget
import ddGui.widget.commentBox
import ddLogger
import ddPipeApi
import ddType

import ddGuerillaApi
import ddGuerillaCommands.nodePublisher

__all__ = ( 'DLCreateEntityGroup' , )

class DLCreateEntityGroup( ddGui.QtWidgets.QDialog ):
    '''Dialog to create or use and existing entity group and associate shot
    with it.
    '''

    __metaclass__ = ddGui.helper.DDGuiSingleton

    ## List of string for the accept button text.
    # type: []
    _DL_BUTTON_LABELS = ( 'Assign'        ,
                          'Create/Assign' )

    ## New str for comboBox.
    # type: str
    _DL_LABEL_NEW = 'New...'

    ## Select an Entity Group str for comboBox.
    # type: str
    _DL_LABEL_SELECT = 'Select an Entity Group'

    def __init__( self       ,
                  *inArgs    ,
                  **inKWArgs ):
        '''Initialize the main window.
        '''

        super( DLCreateEntityGroup , self ).__init__( *inArgs    ,
                                                      **inKWArgs )

        self.setWindowTitle( 'Entity Group Association' )
        self.setWindowModality( ddGui.QtCore.Qt.WindowModal )
        self.setFixedSize( 550 ,
                           380 )

        ########################################################################
        # Create Main widget and set Layout.
        ########################################################################
        mainWidget = ddGui.QtWidgets.QWidget( parent = self )
        mainLayout = ddGui.QtWidgets.QVBoxLayout()
        mainWidget.setLayout( mainLayout )
        mainWidget.resize( 550 ,
                           380 )

        ########################################################################
        # Create widgets
        ########################################################################
        self.createEntityBoxWidget = (
            ddGui.view.entityGroupCreateDialog.DDEntityGroupCreateDialog(
                parent = self )                                           )
        self.createEntityBoxWidget.seqLineEdit.setEnabled( False )
        self.createEntityBoxWidget.create.hide()
        self.createEntityBoxWidget.abort.hide()
        self.createEntityBoxWidget.setVisible( False )

        self.infoEntityGrpLabel = ddGui.QtWidgets.QLabel( '' )
        self.infoEntityGrpLabel.setStyleSheet( 'color: Chocolate' )
        self.infoRenderGraphLabel = ddGui.QtWidgets.QLabel( '' )
        self.infoRenderGraphLabel.setStyleSheet( 'color: Chocolate' )
        self.entityListComboBox = ddGui.QtWidgets.QComboBox( self )

        self._commentBoxWidget = ddGui.widget.commentBox.DDCommentBox(
            inParentWidget = self                                    ,
            inConfigName   = 'guerillaNodePublish'                   )

        ########################################################################
        # Create CheckBoxes Layout and add to widgets
        ########################################################################
        checkBoxesLayout = ddGui.QtWidgets.QHBoxLayout()

        publishRenderGraphLayout = ddGui.QtWidgets.QVBoxLayout()

        publishRenderGraphLayout.addWidget( self.entityListComboBox )

        ########################################################################
        # Create main buttons with layout for MainWidget
        ########################################################################
        self.acceptButton = ddGui.QtWidgets.QPushButton( 'Accept'      ,
                                                         parent = self )
        self.acceptButton.setEnabled( False )

        cancelButton = ddGui.QtWidgets.QPushButton( 'Cancel'      ,
                                                    parent = self )

        buttonLayout = ddGui.QtWidgets.QHBoxLayout()

        buttonLayout.addWidget( cancelButton )
        buttonLayout.addWidget( self.acceptButton )

        ########################################################################
        # Create completer for comboBox widget.
        ########################################################################
        self.entityListComboBox.setEditable( True )
        self.entityListComboBox.addItems( [] )
        self.entityListCompleter = ddGui.QtWidgets.QCompleter( [] )
        self.entityListComboBox.setCompleter( self.entityListCompleter )

        ########################################################################
        # Add widgets / Construct MainLayout
        ########################################################################
        mainLayout.addLayout( publishRenderGraphLayout )
        mainLayout.addLayout( checkBoxesLayout )
        mainLayout.addWidget( self._commentBoxWidget )
        mainLayout.addWidget( self.createEntityBoxWidget )
        mainLayout.addWidget( self.infoEntityGrpLabel )
        mainLayout.addWidget( self.infoRenderGraphLabel )
        mainLayout.addLayout( buttonLayout )

        ########################################################################
        # Connect signals
        ########################################################################
        cancelButton.clicked.connect( self.close )
        self.acceptButton.clicked.connect( self.onAccept )
        self.entityListComboBox.currentIndexChanged.connect(
            self.__onEntityListComboBoxChange )

        self.createEntityBoxWidget._subNomComboBox.currentIndexChanged.connect(
            self.__updateLetterComboBox                                       )

    def __associateShotToEntityGroup( self              ,
                                      inEntityGroupDict ,
                                      inEntityShot      ):
        '''Associate selected shot to an entity group.

        @param ( ddPipeApi.DDEntityGroup ) inEntityGroupDict:
        DDEntityGroup obj.

        @param ( ddPipeApi.DDEntityShot ) inEntityShot:
        DDEntityShot obj.

        @return (None):
        No return value.
        '''

        shots = inEntityGroupDict.shots

        shots.append( inEntityShot )## need the entity

        inEntityGroupDict.shots = shots

        return

    def __cleanWidgets( self ):
        '''Cleans content of widgets.

        @return (None):
        No return value.
        '''

        self.entityListComboBox.clear()
        self.createEntityBoxWidget.seqLineEdit.clear()

        return

    def closeEvent( self     ,
                    inQEvent ):
        '''Unregister or disconnect events on close, save config.

        @param (ddGui.QtCore.QEvent) inQEvent:
        QEvent.

        @return (None):
        No return value.
        '''

        self.__cleanWidgets()

        super( DLCreateEntityGroup , self ).closeEvent( inQEvent )

        return

    def __connectToRenderPass( self          ,
                               inRenderGraph ,
                               inEntityShot  ):
        '''Connects the render passes under entity shot to the
        passed render graph.

        @param ( dlGuerillaApi.DLRenderGraph ) inRenderGraph:
        Created / existing Render graph.

        @param ( ddPipeApi.DDEntityShot ) inEntityShot:
        DDEntityShot obj.

        @return(None):
        No return value.
        '''

        scene = dlGuerillaApi.DLScene()
        entityMetadataNode = scene.createEntityMetadataNode( inEntityShot )

        for renderPass in entityMetadataNode.renderPasses:
            renderPass['RenderGraph'].adddependency( inRenderGraph.RenderGraph )

        return

    def __createEntityHierarchy( self     ,
                                 inEntity ):
        '''Creates inside Guerilla the node hierarchy for the created or
        related / existing entity group.

        @param ( ddPipeApi.DDEntityGroup ) inEntity:
        Created or Existing entity group.

        @return ( ddGuerillaApi.DDBuilderType )
        Builder type node.
        '''

        scene = dlGuerillaApi.DLScene()

        builderType = None

        if ( inEntity.subNomenclature.id ==
            ddPipeApi.nomenclature.DD_ID_ENVIRONMENT ):
            builderType = ddType.builder.DD_LIGHTING_ENV

        elif ( inEntity.subNomenclature.id ==
            ddPipeApi.nomenclature.DD_ID_POV ):
            builderType = ddType.builder.DD_LIGHTING_POV

        entityMetadataNode = scene.createEntityMetadataNode( inEntity )
        newEntityMetadataNode = dlGuerillaApi.entityGroup.DLEntityGroup(
            entityMetadataNode                                         )
        builderTypeNode = newEntityMetadataNode.getBuilderTypeNode(
            inTypeNode = builderType                              )

        return builderTypeNode

    def __disconnectRenderPass( self          ,
                                inEntityShot  ,
                                inEntityGrp   ,
                                inRenderGraph ):
        '''Disconnect render passes from render graph, if there is already
        a render graph associated with shot.

        @param (ddPipeApi.DDEntityShot) inEntityShot:
        DDEntityShot obj.

        @param (ddPipeApi.DDEntityGroup) inEntityGrp:
        Created or existing EntityGroup, as a reference to find it's
        subNomenclature entity group associated with shot if any.

        @param (ddGuerillaApi.DDRenderGraph) inRenderGraph:
        DDRenderGraph obj.

        @return(None):
        No return value.
        '''

        if inEntityGrp is None:
            return

        scene = dlGuerillaApi.DLScene()
        entityMetadataNode = scene.createEntityMetadataNode( inEntityShot )

        if inRenderGraph is not None:
            for renderPass in entityMetadataNode.renderPasses:
                renderPass[ 'RenderGraph' ].removedependency(
                    inRenderGraph.RenderGraph               )

        return

    def __getCurrentShotEntityGrpAndRenderGraph( self               ,
                                                 inEntityGrp        ,
                                                 inShotEntityGroups ):
        '''Get the current render graph associated with selected shot, if any
        None otherwise.

        @param (ddPipeApi.DDEntityGroup) inEntityGrp:
        Created or Existing entity group, as a reference to find the current
        subNomenclature entity group if any.

        @return(tuple):
        Return a tuple with entity group and render graph if any, ( None, None )
        otherwise.
        ( ddPipeApi.DDEntityGroup     ,
          ddGuerillaApi.DDRenderGraph )
        '''

        scene = dlGuerillaApi.DLScene()

        targetSubNomEntity = None
        for shotEntityGrp in inShotEntityGroups:
            if inEntityGrp.subNomenclature.id == shotEntityGrp.subNomenclature.id:
                targetSubNomEntity = shotEntityGrp

        if targetSubNomEntity is None:
            return ( None ,
                     None )

        targetEntityGrp = None
        for sceneEntity in scene.findAllEntityNodes():
            if sceneEntity.name == targetSubNomEntity.name:
                targetEntityGrp = sceneEntity

        if targetEntityGrp is None:
            return ( None ,
                     None )

        targetRenderGraph = targetEntityGrp.findFirst(
            inNodeTypeStr = ddConstants.guerilla.nodeType.DD_RENDER_GRAPH )

        if targetRenderGraph is None:
            return ( None ,
                     None )

        return ( targetEntityGrp   ,
                 targetRenderGraph )

    def __getSelectedShots( self ):
        '''Gets the current selected DDEntityShot objects.

        @return (list):
        A list of ddGuerillaApi.DDEntityShot objects.
        '''

        selectedShots = []
        for selection in ddGuerillaApi.DDScene().getSelection():

            if isinstance( selection , ddGuerillaApi.DDEntityShot ):
                selectedShots.append( selection.entity )

        return selectedShots

    def __getPublishedRenderGraph( self            ,
                                   inEntityGrpDict ,
                                   inEntityShot    ):
        '''Gets the latest version of the RenderGraph published under the given
        entity group, if there is nothing under entityGroup will return the
        render graph published for project.

        @param (ddPipeApi.DDEntityGroup) inEntityGrpDict:
        DDEntityGrp obj.

        @param (ddPipeApi.DDEntityShot) inEntityShot:
        DDEntityShot obj.

        @return (ddPipeApi.DDPublishedFile):
        Returns ddPipeApi.DDPublishedFile published File Obj.
        '''

        renderGraphObj = None

        if not inEntityGrpDict:
            return renderGraphObj

        bridgeTypeObj = None
        subNom = None

        if ( inEntityGrpDict.subNomenclature.id ==
             ddPipeApi.nomenclature.DD_ID_POV    ):

            bridgeTypeObj = ddBuilder.type.DD_LIGHTING_POV
            subNom = ddPipeApi.nomenclature.DD_ID_POV

        elif ( inEntityGrpDict.subNomenclature.id      ==
               ddPipeApi.nomenclature.DD_ID_ENVIRONMENT ):

            bridgeTypeObj = ddBuilder.type.DD_LIGHTING_ENV
            subNom = ddPipeApi.nomenclature.DD_ID_ENVIRONMENT

        else:

            raise TypeError( 'Entity {} not of context type Pov or '
                             'Env'.format( inEntityGrpDict.name ) )

        bridge = ddBuilder.DDBridge()

        bridge.addImporter( ddBuilder.DDImporter(
            inTypeInt               = bridgeTypeObj                           ,
            inMainNomenclatureList  = ( ddPipeApi.nomenclature.DD_ID_LIGHTING ,
                                                                              ) ,
            inSubNomenclatureList   = ( subNom                                , ) ,
            inPublishedFileTypeList = (
                ddPipeApi.publishedFileType.DD_ID_GUERILLA_RENDER_GRAPH       , ) ) )

        builder = ddBuilder.DDBuilder(
            inEntityDict = inEntityShot ,
            inBridgeObj  = bridge       )

        preset = builder.preset
        preset.subAssetRestriction = ()

        builder.preset = preset

        version = builder.getFirstVersion( inRecursiveBool = False )

        renderGraphPubFile = version.current

        msg = 'Fetching {}, version: {}'.format(
            renderGraphPubFile.name            ,
            renderGraphPubFile.versionNumber   )
        ddLogger.DD_GUERILLA.info( msg )

        return renderGraphPubFile

    def __getSeqEntityGroups( self ):
        '''Creates a list of entity groups for the current sequence.

        @return(list):
        Return a list of DDEntityGroups.
        '''

        seqEntityGroups = []
        sequence = ddPipeApi.getCurrentContext().sequence

        for entityGrp in self.__getProjectEntityGroups():
            if entityGrp.name.startswith( sequence.name ):
                seqEntityGroups.append( entityGrp )

        return sorted( seqEntityGroups )

    def __getShotEntityGroup( self ):
        '''Get entity groups related to current selected shot.

        @return (dict):
        Return a dict with DDEntityShot as a key and a list of
        DDEntityGroup object if shot is related to any, None otherwise.
        { DDEntityShot: [ DDEntityGroup , ] }
        '''

        shotsEntityGroups = {}

        for selectedShot in self.__getSelectedShots():

            shotEntityGroups = []

            for entity in self.__getAllProjectEntityGroups():

                for shot in entity.shots:

                    if shot == selectedShot:

                        shotEntityGroups.append( entity )

            shotsEntityGroups[ selectedShot ] = shotEntityGroups

        return shotsEntityGroups

    def __getAllProjectEntityGroups( self ):
        '''Get entity groups related to current project.

        @return(list):
        Returns a list of DDEntityGroups
        '''

        project = ddPipeApi.getCurrentProject()

        light = ddPipeApi.DDNomenclature( ddPipeApi.nomenclature.DD_ID_LIGHTING )

        filters = [
            ddPipeApi.DDEntityGroup.project          == project ,
            ddPipeApi.DDEntityGroup.mainNomenclature == light   ]

        fields = [ ddPipeApi.DDEntityGroup.shots ,
                   ddPipeApi.DDEntityGroup.name  ,
                   ddPipeApi.DDEntityGroup.id    ]

        ####################################################################
        # EntityGroup lookup
        ####################################################################

        entityGrps = ddPipeApi.DDEntityGroup.getAll(
            inFilters = filters                    ,
            inFields  = fields                     )

        return entityGrps

    def __getProjectEntityGroups( self ):
        '''Gets all entity groups from project except the ones currently
        owning the selected shot.

        @return(list):
        Returns a list of DDEntityGroups
        '''

        entityGroups = self.__getAllProjectEntityGroups()

        for entityList in self.__getShotEntityGroup().values():

            for entity in entityList:

                if entity in entityGroups:

                    entityGroups.remove( entity )

        return sorted( entityGroups )

    def __hasValidPublishContext( self          ,
                                  inRenderGraph ):
        '''
        Check the validity of the publish context.

        @param (ddPipeApi.DdPublishedFile) inRenderGraph:
        Published rendergraph obj.

        @return (bool):
        Returns True if the publish context is valid.
        Returns False otherwise.
        '''

        ########################################################################
        # Doing multiple check before publishing the node.
        ########################################################################
        toPublishNode = ddGuerillaApi.DDNode( inRenderGraph )

        path = ddGuerillaApi.DDScene().filePath

        if path is None:

            ddGui.QtWidgets.QMessageBox.warning(
                None                                                  ,
                'Scene not saved!'                                    ,
                'Please save your scene before publishing this node.' )

            return False

        elif path and not path.getPublishedFile():

            ddGui.QtWidgets.QMessageBox.warning(
                None                                                 ,
                'Invalid Scene!'                                     ,
                'Please save a minor or major (publish) version of '
                'the current scene.'                                 )

            return False

        publishContext = toPublishNode.getPublishContext()

        if publishContext is None:

            ddGui.QtWidgets.QMessageBox.warning(
                None                                                 ,
                'No publish context found!'                          ,
                'Expected a ddPipeApi.DDContext instance, got None.' )

            return False

        return True

    def __getEntityGrpFromComboBox( self ):
        '''Gets the entity group Object based on comboBox Selection.

        @return (DDEntityGroup):
        Returns Entity Group obj.

        @return (str):
        Returns "New..." string if index does not have data (entity obj).
        '''

        index = self.entityListComboBox.currentIndex()
        entityId = self.entityListComboBox.itemData( index )

        if entityId is None:

            return self._DL_LABEL_NEW

        return ddPipeApi.DDEntityGroup( entityId )

    def onAccept( self ):
        '''Slot for when the button accept is clicked.

        @return (None):
        No return value.
        '''

        targetEntityGroup = self.__getEntityGrpFromComboBox()

        if targetEntityGroup == self._DL_LABEL_NEW:

            self._commentBoxWidget.saveComment(
                inCommentStr = self._commentBoxWidget.toPlainText() )

            newEntityGroup = self.createEntityBoxWidget.onCreateClicked()
            newEntityGroup.description = self._commentBoxWidget.value

            builderTypeNode = self.__createEntityHierarchy( newEntityGroup )

            for entityShot , entityGrpList in self.__getShotEntityGroup().iteritems():

                renderGraph = builderTypeNode.findFirst(
                    inNodeTypeStr=ddConstants.guerilla.nodeType.DD_RENDER_GRAPH )

                ddEntityGrp , ddRenderGraph = self.__getCurrentShotEntityGrpAndRenderGraph(
                    newEntityGroup                                                        ,
                    entityGrpList                                                         )

                self.__disconnectRenderPass( entityShot    ,
                                             ddEntityGrp   ,
                                             ddRenderGraph )

                self.__removePreviousEntityGroup( ddEntityGrp   ,
                                                  ddRenderGraph )

                for entityGrp in entityGrpList:

                    if newEntityGroup.subNomenclature.id == entityGrp.subNomenclature.id:

                        self.__removeShotFromEntityGroup( entityGrp  ,
                                                          entityShot )

                self.__associateShotToEntityGroup( newEntityGroup ,
                                                   entityShot     )

                if renderGraph is None:

                    publishedRenderGraph = self.__getPublishedRenderGraph(
                        newEntityGroup                                   ,
                        entityShot                                       )

                    loadedRenderGraph = builderTypeNode.loadfile(
                        publishedRenderGraph.localPath          )[ 0 ]

                    renderGraph = dlGuerillaApi.DLRenderGraph( loadedRenderGraph )

                    # Publish render graph if its entity parent is the project.
                    if ( isinstance( publishedRenderGraph.entity , ddPipeApi.DDProject ) and
                         self.__hasValidPublishContext( loadedRenderGraph )                ):

                        self.__publishRenderGraph( renderGraph )

                self.__connectToRenderPass(
                    dlGuerillaApi.DLRenderGraph( renderGraph ) ,
                    entityShot                                 )

            self.close()

        elif isinstance( targetEntityGroup, ddPipeApi.DDEntityGroup ):

            builderTypeNode = self.__createEntityHierarchy( targetEntityGroup )
            renderGraph = builderTypeNode.findFirst(
                inNodeTypeStr=ddConstants.guerilla.nodeType.DD_RENDER_GRAPH )

            for entityShot , entityGrpList in self.__getShotEntityGroup().iteritems():

                ddEntityGrp, ddRenderGraph = self.__getCurrentShotEntityGrpAndRenderGraph(
                    targetEntityGroup                                                    ,
                    entityGrpList                                                        )

                self.__disconnectRenderPass( entityShot    ,
                                             ddEntityGrp   ,
                                             ddRenderGraph )

                self.__removePreviousEntityGroup( ddEntityGrp   ,
                                                  ddRenderGraph )

                for entityGrp in entityGrpList:

                    if targetEntityGroup.subNomenclature.id == entityGrp.subNomenclature.id:
                        self.__removeShotFromEntityGroup( entityGrp  ,
                                                          entityShot )

                self.__associateShotToEntityGroup( targetEntityGroup ,
                                                   entityShot        )


                if renderGraph is None:

                    publishedRenderGraph = self.__getPublishedRenderGraph(
                        targetEntityGroup                                ,
                        entityShot                                       )

                    loadedRenderGraph = builderTypeNode.loadfile(
                        publishedRenderGraph.localPath          )[ 0 ]

                    renderGraph = dlGuerillaApi.DLRenderGraph( loadedRenderGraph )

                    # Publish render graph if its entity parent is the project.
                    if ( isinstance( publishedRenderGraph.entity , ddPipeApi.DDProject ) and
                         self.__hasValidPublishContext( loadedRenderGraph )                ):

                        self.__publishRenderGraph( renderGraph )

                self.__connectToRenderPass(
                    dlGuerillaApi.DLRenderGraph( renderGraph ) ,
                    entityShot                                 )

            self.close()

        else:

            ddGui.view.messageBox.DDMessageBox.warning(
                self                      ,
                'Warning'                 ,
                'No entity group defined' )

        return

    def __onEntityListComboBoxChange( self       ,
                                      inIndexInt ):
        '''Execute when entityListComboBox changes, this change the
        text of accept button and the visibility of createEntityBoxWidget.

        @param (int) inIndexInt:
        Widget ComboBox signal.

        @return (None):
        No return value.
        '''

        if self.entityListComboBox.itemText( inIndexInt ) == self._DL_LABEL_NEW:
            self.acceptButton.setText( self._DL_BUTTON_LABELS[ 1 ] )
            self._commentBoxWidget.setEnabled( True )

            self.createEntityBoxWidget.setVisible( True )
            self.__updateCreateWidgetWithSequenceName()
        else:
            self.acceptButton.setText( self._DL_BUTTON_LABELS[ 0 ] )
            self._commentBoxWidget.clear()
            self._commentBoxWidget.setEnabled( False )

            self.createEntityBoxWidget.setVisible( False )

        return

    def __publishRenderGraph( self          ,
                              inRenderGraph ):
        '''Publish the render graph brought from project, under Entity group.

        @note: The only publishable nodes are under the DDWork node.

        @return (bool):
        Returns True if the publish action is correctly done.

        @return (None):
        Returns None if something went wrong during the publish process.

        @rtype: bool|None
        '''

        comment = 'Initial render graph from project'

        publishContext = inRenderGraph.getPublishContext()

        path = ddGuerillaApi.DDScene().filePath

        versionNode = ddAction.guerilla.publish.DDVersionNode(
            inLabelStr = 'Publish {0}'.format( inRenderGraph.name ) ,
            node       = inRenderGraph                              ,
            comment    = comment                                    ,
            context    = publishContext                             ,
            work       = path.getPublishedFile()                    )

        versionNode()

        return True

    def __updateLetterComboBox( self ):
        '''Removes letters / version of the existing entity groups in the
        letter drop down menu.

        @return (None):
        No return value.
        '''

        existsLetter = []
        self.createEntityBoxWidget._letterComboBox.clear()
        self.createEntityBoxWidget._letterComboBox.addItems(
            string.ascii_uppercase                         )

        index  = self.createEntityBoxWidget._subNomComboBox.currentIndex()
        subNom = self.createEntityBoxWidget._subNomComboBox.itemData( index )

        sequenceGroups = []
        sequence       = ddPipeApi.getCurrentContext().sequence

        for entityGrp in self.__getAllProjectEntityGroups():
            if ( entityGrp.name.startswith( sequence.name ) and
                entityGrp.subNomenclature.id == subNom        ):
                sequenceGroups.append( entityGrp )

        for entity in sequenceGroups:
            existsLetter.append( entity.name[-1] )

        for letter in existsLetter:
            index = self.createEntityBoxWidget._letterComboBox.findText( letter )
            self.createEntityBoxWidget._letterComboBox.removeItem( index )

        return

    def __removePreviousEntityGroup( self          ,
                                     inEntityGroup ,
                                     inRenderGraph ):
        '''Removes previous entity group related to shot if it's render graph is
        not connected to any render pass.

        @param (ddPipeApi.DDEntityGroup) inEntityGroup:
        Entity group created or existing that shot will be assigned.

        @param (ddGuerillaApi.DDRenderGraph) inRenderGraph:
        DDRenderGraph obj.

        @return(None):
        No return value.
        '''

        if inRenderGraph is None:
            return

        elif 'RenderGraph' not in [
            dependency.name for dependency               in
            inRenderGraph.RenderGraph.getbackdependencies() ]:

            inEntityGroup.delete()

        return

    def __removeShotFromEntityGroup( self            ,
                                     inDDEntityGrp   ,
                                     inDDEntityShot  ):
        '''Removes a shot from The given EntityGroup.

        @param (DDEntityGroup) inDDEntityGrp:

        @param (DDEntityShot) inDDEntityShot:

        @return (None):
        No return value.
        '''

        try:
            shots = inDDEntityGrp.shots
            shots.remove( inDDEntityShot )

            inDDEntityGrp.shots = shots
        except Exception, error:
            warningMsg = ('Selected shot is not assigned to any Entity Group,'
                          ' error {}'.format( str( error ) ) )
            ddLogger.DD_GUERILLA.warning( warningMsg )

            pass

        return

    def __setComboBoxCompleter( self ):
        '''This add project entity group to completer for entity group
        combo box.

        @return (None):
        No return value.
        '''

        comboBoxCompleterList = []
        comboBoxCompleterList.append( self._DL_LABEL_NEW )

        for entity in self.__getProjectEntityGroups():
            comboBoxCompleterList.append( entity.name )

        entityListCompleter = ddGui.QtWidgets.QCompleter( comboBoxCompleterList )

        self.entityListComboBox.setCompleter( entityListCompleter )
        entityListCompleter.setFilterMode( ddGui.QtCore.Qt.MatchContains )

        return

    def __updateEntityGrpComboBox( self ):
        '''Adds the current sequence entity groups.

        @return (None):
        No return value.
        '''

        self.entityListComboBox.clear()
        self.entityListComboBox.addItem( self._DL_LABEL_SELECT )
        self.entityListComboBox.addItem( self._DL_LABEL_NEW )

        sequenceEntityGroups = self.__getSeqEntityGroups()

        shotEntityGroup = []

        for entityGrpList in self.__getShotEntityGroup().values():

            for entityGrp in entityGrpList:

                if entityGrp not in shotEntityGroup:

                    shotEntityGroup.append( entityGrp )

        projectEntityGroups  = self.__getProjectEntityGroups()

        entityGroupsWithoutSequence = list(
            set( projectEntityGroups ) - set( sequenceEntityGroups ) )


        if not sequenceEntityGroups and not shotEntityGroup:
            self.entityListComboBox.setCurrentIndex( 1 )
            self._commentBoxWidget.setEnabled( True )

        elif sequenceEntityGroups and not shotEntityGroup:
            for entity in sequenceEntityGroups:
                self.entityListComboBox.addItem( entity.name ,
                                                 entity.id   )

            for entity in entityGroupsWithoutSequence:
                self.entityListComboBox.addItem( entity.name ,
                                                 entity.id   )

            self.entityListComboBox.setCurrentIndex( 0 )
            self._commentBoxWidget.setEnabled( False )

        else:
            for entity in sequenceEntityGroups:
                self.entityListComboBox.addItem( entity.name ,
                                                 entity.id   )

            for entity in entityGroupsWithoutSequence:
                self.entityListComboBox.addItem( entity.name ,
                                                 entity.id   )

            for entity in shotEntityGroup:
                index = self.entityListComboBox.findData( entity.id )
                self.entityListComboBox.removeItem( index )

                self.entityListComboBox.setCurrentIndex( 0 )
                self._commentBoxWidget.setEnabled( False )

        return

    def __updateCreateWidgetWithSequenceName( self ):
        '''Update the lineEdit field for creating entity group, with
        with sequence name.

        @return (None):
        No return value.
        '''

        currentSequence = ddPipeApi.getCurrentContext().sequence

        if currentSequence is None:
            self.createEntityBoxWidget.seqLineEdit.setText( '' )
        else:
            self.createEntityBoxWidget.seqLineEdit.setText( currentSequence.name )

        return

    def __populateMainNomComboBox( self ):
        '''Populates the main nomenclature based / cross checked
        with artist department and pre-defined Nomenclatures.

        @return (None):
        No return value.
        '''

        mainNom = None

        currentContext = ddPipeApi.getCurrentContext()

        if ( currentContext.mainNomenclature                       in
             self.createEntityBoxWidget.DD_VALID_MAIN_NOMENCLATURES ):
            mainNom = currentContext.mainNomenclature

        self.createEntityBoxWidget._mainNomComboBox.clear()

        if mainNom:
            self.createEntityBoxWidget._mainNomComboBox.addItem( mainNom.name ,
                                                                 mainNom.id   )
        else:
            self.createEntityBoxWidget._mainNomComboBox.addItem(
                'Not supported' )

        return

    def __updateMainWindow( self ):
        '''Update main UI widgets based on selection.

        @return (None):
        No return value.
        '''

        self.__updateEntityGrpComboBox()
        self.__setComboBoxCompleter()

        self._commentBoxWidget.setVisible( True )
        self.acceptButton.setEnabled( True )

        if self.__getShotEntityGroup():
            self.acceptButton.setText( self._DL_BUTTON_LABELS[ 0 ] )
            self.acceptButton.setEnabled( True )

        return

    def __updateInfoRenderGraphLabel( self ):
        '''Updates infoRenderGraphLabel which shows information of
        the entity group and render graph of the selected shot if any.

        @return (None):
        No return value.
        '''

        if len( self.__getShotEntityGroup().keys() ) > 1:

            entityGrpLabelMsg = ''

            for entityShot , entityGrpList in self.__getShotEntityGroup().iteritems():

                entityGrps = [ entityGrp.name for entityGrp in entityGrpList ]

                entityGrpLabelMsg += '{} assigned to: {}\n'.format(
                    entityShot.name , entityGrps if entityGrps else 'NOT assigned' )


            self.infoRenderGraphLabel.setText( 'Multiple DDShot selected!' )
            self.infoRenderGraphLabel.setVisible( True )

            self.infoEntityGrpLabel.setText( entityGrpLabelMsg )
            self.infoEntityGrpLabel.setVisible( True )

            return

        elif len( self.__getShotEntityGroup().keys() ) == 1:

            entityShot   = self.__getShotEntityGroup().keys()[ 0 ]
            entityGroups = self.__getShotEntityGroup().values()[ 0 ]

            if not entityGroups:

                self.infoEntityGrpLabel.setText( 'Shot is NOT assigned!' )
                self.infoEntityGrpLabel.setVisible( True )
                self.infoRenderGraphLabel.setVisible( False )

                return

            else:

                entityGrps = [ entity.name for entity in entityGroups ]

                self.infoEntityGrpLabel.setText( 'Shot is already assigned to: %s' %
                    entityGrps                                                     )
                self.infoEntityGrpLabel.setVisible( True )

                renderGraphPubFiles = []
                for entity in entityGroups:

                    publishedFile = self.__getPublishedRenderGraph( entity     ,
                                                                    entityShot )

                    if isinstance( publishedFile.entity , ddPipeApi.DDEntityGroup ):

                        renderGraphPubFiles.append( publishedFile )

                if renderGraphPubFiles:

                    renderGraphInfo = 'Existing render graphs:\n'

                    for renderGraph in renderGraphPubFiles:

                        renderGraphInfo += (
                                'RenderGraph: %s\n'
                                'Description:    %s\n'
                                'Updated:        %s\n\n' %
                                (renderGraph.name,
                                 renderGraph.description,
                                 renderGraph.updatedAt))

                    self.infoRenderGraphLabel.setText( renderGraphInfo )
                    self.infoRenderGraphLabel.setVisible( True )

                return

    def showEvent( self     ,
                   inQEvent ):
        '''Refresh on show

        @param (ddGui.QtCore.QEvent) inQEvent:
        QEvent.

        @return (None):
        No return value.
        '''

        if not self.__getSelectedShots():

            msg = 'Select at least one DDShot'

            self.entityListComboBox.clear()
            self.entityListComboBox.addItem( msg )

            self.infoEntityGrpLabel.setText( msg )
            self.infoEntityGrpLabel.setVisible( True )

            self.infoRenderGraphLabel.setVisible( False )

            self.acceptButton.setEnabled( False )

            super( DLCreateEntityGroup , self ).showEvent( inQEvent )

            return

        self.__updateMainWindow()
        self.__populateMainNomComboBox()
        self.__updateLetterComboBox()
        self.__updateInfoRenderGraphLabel()

        super( DLCreateEntityGroup , self ).showEvent( inQEvent )

        return
