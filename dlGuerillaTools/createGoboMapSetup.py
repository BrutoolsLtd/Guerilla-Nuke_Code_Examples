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
'''Guerilla tool to create gobo map setup / rig.

@package dlGuerillaTools.createGoboMapSetup
@author Esteban Ortega <esteban.ortega@latelieranimation.com>
@author Camelia Slimani <camelia.slimani@latelieranimation.com>
'''

import math
import re

import dlConstants
import dlGuerillaApi

import ddBuilder
import ddConstants.guerilla
import ddConstants.renderToken
import ddPipeApi
import ddType.builder


import ddGuerillaApi

__all__ = ( 'DLGoboMapSetup' , )

class DLGoboMapSetup( object ):
    '''Creates a gobo map setup based on current selection, light or
    lightAttributes node within Guerilla.
    '''

    ## Gobo render pass resolution.
    # type: int
    __DL_GOBO_RENDERPASS_RESOLUTION = 2048

    ## Store edge upstream node in the selected node tree.
    # type: []
    __DL_EDGE_NODES = []

    ## Store downstream connected scene graph nodes.
    # type: []
    __DL_SCENEGRAPH_NODES = []

    def __init__( self           ,
                  inSelectedNode ):
        '''Initialize class.

        @param(ddGuerillaApi.DDNode) inSelectedNode:
        Node representing the current selected light or lightAttributes node.

        @return(None)
        No return value.
        '''

        ## Current selection.
        # type: ddGuerillaApi.DDNode
        self.__selectedNode = inSelectedNode

        ## Stores a boolen, True if current selection is a lightAttributes,
        # False otherwise.
        # type: bool
        if ( self.__selectedNode.guerillaType ==
             ddConstants.guerilla.nodeType.DD_RGN_LIGHT_ATTRIBUTES ):
            self._isLightAttributes = True

        else:
            self._isLightAttributes = False

        ## Stores a boolen, True if current selection has a
        # upstream / parent connection, False otherwise.
        # type: bool
        inputNode = self.__selectedNode.getinputs()[ 0 ]
        if inputNode.getconnected():
            self._isSelectionConnected = True

        else:
            self._isSelectionConnected = False

        return

    def __createFrustum( self ):
        '''Creates Frustum light shader under the selected light.

        @return (ddGuerillaApi.DDNode):
        Falloff node.
        '''

        newName = dlConstants.guerilla.goboLightShaderName.DL_GOBO_FRUSTUM_SHADER_NAME

        frustumNode = self.__selectedNode.findChild( newName )

        oldFrustumNode = self.__selectedNode.findChild( 'Frustum' )

        if frustumNode is None and oldFrustumNode is None:
            frustumNode = ddGuerillaApi.DDNode(
                self.__selectedNode.loadfile(
                    "$(LIBRARY)/lights/frustum.gnode" )[ 0 ] )

            frustumNode.rename( newName )

            fallOffNode = frustumNode.findFirst(
                ddGuerillaApi.filters.DDName( 'Falloff' ) ,
                inNodeTypeStr = 'ShaderNodeSL'            )

            for node in fallOffNode.findAll( inNodeTypeStr = 'ShaderNodeIn' ):
                plugName = node.PlugName.get()

                if plugName in ( 'VDelta' , 'HDelta' ):
                    node.Value.set( 0 )

            return fallOffNode

        elif frustumNode is None and oldFrustumNode is not None:
            frustumNode = oldFrustumNode
            frustumNode.rename( newName )

        fallOffNode = frustumNode.findFirst(
            ddGuerillaApi.filters.DDName( 'Falloff' ) ,
            inNodeTypeStr = 'ShaderNodeSL'            )

        return fallOffNode

    @staticmethod
    def __getFovAndFrameRatio( inLightNode ):
        '''Gets the FOV and Frame ratio from existing frustum to be override
        as starting point.

        @param (ddGuerillaApi.DDNode) inLightNode:
        Source node to copy get settings from.

        @return (tuple):
        ( int representing the Fov    ,
          int representing FrameRatio )
        '''

        VAngle     = None
        frameRatio = 1

        newName = dlConstants.guerilla.goboLightShaderName.DL_GOBO_FRUSTUM_SHADER_NAME

        frustumNode    = inLightNode.findChild( newName   )
        oldFrustumNode = inLightNode.findChild( 'Frustum' )

        if frustumNode is None and oldFrustumNode is None:
            return ( VAngle     ,
                     frameRatio )

        elif frustumNode is None and oldFrustumNode is not None:
            frustumNode = oldFrustumNode
            frustumNode.rename( newName )

        expressions = list( inLightNode.findAll(
            inNodeTypeStr = ddConstants.guerilla.nodeType.DD_EXPRESSION ) )

        if expressions:
            for expression in expressions:
                if expression.name == 'Expression_VAngle_FOVCamera':
                    VAngle = expression.VAngle.get()
                    frameRatio = expression.FrameRatio.get()

            return ( VAngle     ,
                     frameRatio )

        else:
            for node in inLightNode.parent.findAll(
                inNodeTypeStr = 'ShaderNodeIn'     ):

                if node.PlugName.get() == 'VAngle':
                    VAngle = node.Value.get()

            return( VAngle     ,
                    frameRatio )

    def createGoboSetup( self                 ,
                         inShotList           ,
                         inAngleInt           ,
                         inParentInstanceNode ,
                         inLightNode = None   ):
        '''Creates a camera constrained to selected light.

        @param(list) inShotList:
        List of PySide2.QtCore.QModelIndex Object which store name of shot.

        @param(int) inAngleInt:
        Integer representing the angle for camera Fov.

        @param(ddGuerillaApi.DDNode) inParentInstanceNode:
        Node representing the instance node used for locating the light.

        @param(ddGuerillaApi.DDNode) inLightNode:
        Node representing the light node.

        return(None):
        No return value.
        '''

        with ddGuerillaApi.DDModifier() as mod:

            goboName = '{}_{}'.format(
                dlConstants.guerilla.renderPass.DL_GOBOMAP_PREFIX ,
                self.__selectedNode.name                          )

            ####################################################################
            # Create nodes for Gobo setup.
            ####################################################################
            fallOffNode = self.__createFrustum()

            parentEntity = self.__selectedNode.findParent(
                inTypeStr = ddConstants.guerilla.plugIn.DD_ENTITY_METADATA )

            if parentEntity is None:
                raise AttributeError(
                    'Selection "{}" not under a valid entityMetadataNode!'.format(
                        self.__selectedNode.name                                 ) )

            mainNom = ddPipeApi.getCurrentContext().mainNomenclature
            nodePath = '{}|{}|{}'.format( mainNom.name.capitalize() ,
                                          parentEntity.entity.name  ,
                                          goboName                  )

            if ddGuerillaApi.DDScene.nodeExists( nodePath ):
                raise AttributeError( '"{}" already exist!'.format( nodePath ) )

            # Create EntityMetadata if it does not exist, render pass and layer.
            scene = dlGuerillaApi.DLScene()

            entityMetadataNode = scene.createEntityMetadataNode(
                parentEntity.entity                               ,
                inMainNomenclatureStr = ddPipeApi.DDNomenclature(
                    ddPipeApi.nomenclature.DD_ID_GOBOMAP        ) )

            renderPass = entityMetadataNode.createRenderPass( goboName )
            renderPass[ 'Height' ].value = self.__DL_GOBO_RENDERPASS_RESOLUTION
            renderPass[ 'Width'  ].value = self.__DL_GOBO_RENDERPASS_RESOLUTION
            renderPass.BrdfSamples.set( 64 )
            renderPass.AdaptiveThreshold.set( 0.1 )
            renderPass.AdaptiveMinSamples.set( 2 )

            layer = renderPass.createRenderLayer( 'B10_{}'.format( goboName ) )
            layer.createLayerOut(
                ddConstants.renderToken.DD_RENDER_AOV_BEAUTY_STR.capitalize() )
            layer.createLayerOut( 'Albedo' )

            for shot in inShotList:
                for renderGraph in self.__getRenderGraph( shot ):
                    renderGraph.connectToRenderPass( renderPass )

                goboRenderGraphOrder = self.__getGoboRenderGraphOrder( shot )

            renderGraph = entityMetadataNode.findFirst(
                ddGuerillaApi.filters.DDName( goboName )                      ,
                inNodeTypeStr = ddConstants.guerilla.nodeType.DD_RENDER_GRAPH )

            if renderGraph is not None:
                goboCamera = entityMetadataNode.findFirst(
                    ddGuerillaApi.filters.DDName( 'Camera_{}'.format( goboName ) ) ,
                    inNodeTypeStr = ddConstants.guerilla.nodeType.DD_CAMERA        )
            else:
                builderTypeNode = entityMetadataNode.getBuilderTypeNode(
                    inTypeNode = ddType.builder.DD_RENDER_SETTING_GRAPH )
                renderGraph = renderPass.createDependentRenderGraph(
                    inParentNode = builderTypeNode                 )

                renderGraph.connectToRenderPass( renderPass )

                goboCamera = self.__createNodesForGoboCamera( goboName    ,
                                                              renderGraph )
                renderPass.connectCamera( goboCamera )

                # Create euler transform to offset the scene graph with camera.
                cameraEulerTransform = ddGuerillaApi.DDTransformEuler.create(
                    inNameStr    = 'Offset_EulerTransform'                  ,
                    inParentNode = goboCamera.parent                        )

                # Set transforms based on inDDNode
                self.__setTransformsForSceneGraph( cameraEulerTransform ,
                                                   inParentInstanceNode ,
                                                   inLightNode          ,
                                                   goboCamera.parent    )

                # Constraint camera to light's shader Frustum.
                cameraConstraint = ddGuerillaApi.DDTransformConstraint.create(
                    inNameStr    = 'Constraint_{}'.format( fallOffNode.parent.name ) ,
                    inParentNode = goboCamera.parent                                 )

                cameraConstraint.addObject( fallOffNode.parent )

            # Get Fov and FrameRatio from selected Light's Frustum.
            if inLightNode:
                fov , frameRatio = self.__getFovAndFrameRatio( inLightNode )

                if fov is not None:
                    goboCamera[ 'Fov' ].value = fov
                    goboCamera[ 'FrameRatio' ].value = frameRatio
            else:
                goboCamera[ 'Fov' ].value = inAngleInt

            goboCamera.FreezeTransform.set( True )

            self.__linkFrustumAnglesToCameraFov( goboCamera         ,
                                                 fallOffNode.parent )

            self.__linkPassHeightToCameraFrameRatio( renderPass ,
                                                     goboCamera )

            renderGraph.Order.set( goboRenderGraphOrder )
            renderGraph.connectToRenderPass( renderPass )
            renderPass.connectCamera( goboCamera )

            # Create isolate gobo setup.
            self.createGoboIsolateSetup( self.__selectedNode.name ,
                                         renderGraph              )

        return

    def createGoboIsolateSetup( self                  ,
                                inLightNameStr        ,
                                inGoboRenderGraphNode ):
        '''Creates node setup to isolate gobo light setup.

        @param(str) inLightNameStr:
        Name of the light to isolate.

        @param(ddGuerillaApi.DDNode) inGoboRenderGraphNode:
        Node which will contain setup.

        @return(None):
        No return value.
        '''

        ########################################################################
        # Create nodes.
        ########################################################################
        tagAllNode = inGoboRenderGraphNode.findFirst(
            ddGuerillaApi.filters.DDName( 'All' )   )

        if tagAllNode is None:
            return

        newTagNode = inGoboRenderGraphNode.createChild(
            inNameStr = 'All'                                        ,
            inNodeTypeStr = ddConstants.guerilla.nodeType.DD_RGN_TAG )
        newTagNode.SceneGraphNodes.set( False )
        newTagNode.Primitives.set( False )
        newTagNode.Lights.set( True )
        newTagNode.Tag.set( 'All' )

        attributesNode = inGoboRenderGraphNode.createChild(
            inNameStr     = 'Attributes'                                    ,
            inNodeTypeStr = ddConstants.guerilla.nodeType.DD_RGN_ATTRIBUTES )
        attributesNode.overrideAttribute( 'Hidden' , True )

        mergeNode = inGoboRenderGraphNode.createChild(
            inNameStr     = 'merge'                                    ,
            inNodeTypeStr = ddConstants.guerilla.nodeType.DD_RGN_BINOP )
        mergeNode.State.set( 'bypass' )

        subtractNode = inGoboRenderGraphNode.createChild(
            inNameStr     = 'subtract'                                 ,
            inNodeTypeStr = ddConstants.guerilla.nodeType.DD_RGN_BINOP )
        subtractNode.rename( 'subtract' )
        subtractNode.Mode.set( 'subtract' )

        pathNode = inGoboRenderGraphNode.createChild(
            inNameStr     = inLightNameStr                            ,
            inNodeTypeStr = ddConstants.guerilla.nodeType.DD_RGN_PATH )
        pathNode.Path.set( inLightNameStr )

        ########################################################################
        # Get input - output nodes for connections.
        ########################################################################
        tagAllNodeOutput = tagAllNode.getoutputs()[ 0 ]
        try:
            tagConnectedNode = tagAllNodeOutput.getconnected()[ 0 ]
        except KeyError:
            tagConnectedNode = None

        ########################################################################
        # Connect Nodes
        ########################################################################
        # Merge
        tagAllNode.output.connect( mergeNode.x )
        if tagConnectedNode:
            tagConnectedNode.connect( mergeNode.output )

        attributesNode.output.connect( mergeNode.y )

        subtractNode.output.connect( attributesNode.input )

        newTagNode.output.connect( subtractNode.x )

        pathNode.output.connect( subtractNode.y )

        ########################################################################
        # Arrange nodes
        ########################################################################
        tagAllNodePosX , tagAllNodePosY = tagAllNode.NodePos.get()
        offsetX = 200
        offsetY = 200

        mergeNode.NodePos.set( ( tagAllNodePosX + offsetX ,
                                 tagAllNodePosY           ) )

        attributesNode.NodePos.set( ( mergeNode.NodePos.get()[ 0 ] - offsetX ,
                                      mergeNode.NodePos.get()[ 1 ] - offsetY ) )

        subtractNode.NodePos.set( ( attributesNode.NodePos.get()[ 0 ] - offsetX ,
                                    attributesNode.NodePos.get()[ 1 ] - offsetY ) )

        pathNode.NodePos.set( ( subtractNode.NodePos.get()[ 0 ] - offsetX ,
                                subtractNode.NodePos.get()[ 1 ]           ) )

        newTagNode.NodePos.set( ( subtractNode.NodePos.get()[ 0 ] - offsetX ,
                                  subtractNode.NodePos.get()[ 1 ] - offsetY ) )

        return

    @staticmethod
    def __linkPassHeightToCameraFrameRatio( inRenderPass ,
                                            inCameraNode ):
        '''Create an expression to link render pass Height resolution to
        FrameRatio from camera.

        @param (ddGuerillaApi.DDRenderPass) inRenderPass:
        Render pass to link.

        @param (ddGuerillaApi.DDCamera) inCameraNode:
        Camera object to link FrameRation.

        @return (None):
        No return value.
        '''

        if not list( inRenderPass.findAll(
                inNodeTypeStr = ddConstants.guerilla.nodeType.DD_EXPRESSION ) ):

            ####################################################################
            # Create expression for RenderPass Height
            ####################################################################
            expressionHeight = ddGuerillaApi.DDNode.create(
                inNameStr     = 'Expression_Height_Camera' ,
                inParentNode  = inRenderPass               ,
                inNodeTypeStr = 'Expression'               )

            expressionHeight.createPlug(
                inPlugTypeStr = 'ExpressionOutput' ,
                inPlugNameStr = 'Out'              ,
                inDataTypeObj = 'resolution'       )

            expressionHeight.createPlug(
                inPlugTypeStr = 'ExpressionInput' ,
                inPlugNameStr = 'FrameRatio'      ,
                inDataTypeObj = 'float'           )

            expressionHeight.createPlug(
                inPlugTypeStr = 'ExpressionInput' ,
                inPlugNameStr = 'Width'           ,
                inDataTypeObj = 'float'           )

            inRenderPass.Height.connect( expressionHeight.Out )
            expressionHeight.Width.connect( inRenderPass.Width )

            expressionHeight.FrameRatio.connect( inCameraNode.FrameRatio )
            expressionHeight.Script.set( "Out = Width / FrameRatio" )

            return

        for expression in list( inRenderPass.findAll(
                inNodeTypeStr = ddConstants.guerilla.nodeType.DD_EXPRESSION ) ):

            if expression.name == 'Expression_Height_Camera':
                expression.FrameRatio.connect( inCameraNode.FrameRatio )

        return

    @staticmethod
    def __linkFrustumAnglesToCameraFov( inCameraNode  ,
                                        inFrustumNode ):
        '''Create and expression to link Camera FOV plug to Frustum HAngle
        and VAngle plug, considering FrameRatio.

        @param (ddGuerillaApi.DDNode) inCameraNode:
        DDNode representing the GOBO camera.

        @param (ddGuerillaApi.DDNode) inFrustumNode:
        Node representing Frustum node.

        @return (None):
        No return value.
        '''

        hAngleNode = None
        vAngleNode = None
        for node in inFrustumNode.findAll( inNodeTypeStr = 'ShaderNodeIn' ):
            if node.PlugName.get() == 'HAngle':
                hAngleNode = node

            elif node.PlugName.get() == 'VAngle':
                vAngleNode = node

        if not list( inFrustumNode.findAll(
                inNodeTypeStr = ddConstants.guerilla.nodeType.DD_EXPRESSION ) ):

            ####################################################################
            # Create expression for hAngle
            ####################################################################
            expressionHangle = ddGuerillaApi.DDNode.create(
                inNameStr = 'Expression_HAngle_FOVCamera' ,
                inParentNode = hAngleNode                 ,
                inNodeTypeStr = 'Expression'              )

            expressionHangle.createPlug(
                inPlugTypeStr = 'ExpressionOutput' ,
                inPlugNameStr = 'Out'              ,
                inDataTypeObj = 'radians'          )

            expressionHangle.createPlug(
                inPlugTypeStr = 'ExpressionInput' ,
                inPlugNameStr = 'HAngle'          ,
                inDataTypeObj = 'float'           )

            hAngleNode.Value.connect( expressionHangle.Out )

            expressionHangle.HAngle.connect( inCameraNode.Fov )
            expressionHangle.Script.set( "Out = math.rad( HAngle / 2.0 )" )

            ####################################################################
            # Create expression for vAngle
            ####################################################################
            expressionVangle = ddGuerillaApi.DDNode.create(
                inNameStr = 'Expression_VAngle_FOVCamera' ,
                inParentNode = vAngleNode                 ,
                inNodeTypeStr = 'Expression'              )

            expressionVangle.createPlug(
                inPlugTypeStr = 'ExpressionOutput' ,
                inPlugNameStr = 'Out'              ,
                inDataTypeObj = 'radians'          )

            expressionVangle.createPlug(
                inPlugTypeStr = 'ExpressionInput' ,
                inPlugNameStr = 'VAngle'          ,
                inDataTypeObj = 'float'           )

            expressionVangle.createPlug(
                inPlugTypeStr = 'ExpressionInput' ,
                inPlugNameStr = 'FrameRatio'      ,
                inDataTypeObj = 'float'           )

            vAngleNode.Value.connect( expressionVangle.Out )

            expressionVangle.VAngle.connect( inCameraNode.Fov )
            expressionVangle.FrameRatio.connect( inCameraNode.FrameRatio )
            expressionVangle.Script.set(
                "Out = math.rad( ( VAngle / 2.0 ) / FrameRatio )" )

            return

        for expression in list( inFrustumNode.findAll(
                inNodeTypeStr = ddConstants.guerilla.nodeType.DD_EXPRESSION ) ):

            if expression.name == 'Expression_HAngle_FOVCamera':
                expression.HAngle.connect( inCameraNode.Fov )

            elif expression.name == 'Expression_VAngle_FOVCamera':

                #Frame ratio is stored in expression, just getting and setting.
                inCameraNode.FrameRatio.set( expression.FrameRatio.get() )

                expression.VAngle.connect( inCameraNode.Fov )
                expression.FrameRatio.connect( inCameraNode.FrameRatio )

        return

    def __getDownstreamSceneGraph( self     ,
                                   inDDNode ):
        '''Gets scene graphs connected to the output plug
        of passed scene graph, to stack all translations.

        @param (ddGuerillaApi.DDNode) inDDNode:
        Node to check downstream connections.

        @return(list):
        List of ddGuerillaApi.DDNode
        '''

        if not isinstance(
            inDDNode                                                            ,
            ddGuerillaApi.renderGraphNodeSceneGraph.DDRenderGraphNodeSceneGraph ):

            return self.__DL_SCENEGRAPH_NODES

        elif isinstance(
            inDDNode                                                            ,
            ddGuerillaApi.renderGraphNodeSceneGraph.DDRenderGraphNodeSceneGraph ):

            self.__DL_SCENEGRAPH_NODES.append( inDDNode )

            output = inDDNode.getoutputs()[ 0 ]
            connectedPlug = output.getconnected()[ 0 ]
            downStreamNode = ddGuerillaApi.DDNode( connectedPlug.parent )

            self.__getDownstreamSceneGraph( downStreamNode )

        return self.__DL_SCENEGRAPH_NODES

    def __setTransformsForSceneGraph( self                   ,
                                      inDDTransformEulerNode ,
                                      inDDNode               ,
                                      inLightNode            ,
                                      inSceneGraphNode       ):
        '''Gets transforms from selected element / Geo and sets them in
        the offset euler transform for SceneGraph containing the Gobo camera.

        @param (ddGuerillaApi.DDTransformEuler) inDDTransformEulerNode:
        Transform node to use for offset in scene graph node.

        @param (ddGuerillaApi.renderGraphNodeSceneGraph.DDRenderGraphNodeSceneGraph |
                ddGuerillaApi.sceneGraphNode.DDSceneGraphNode ) inDDNode:
        objects representing the potential parent for camera constraint.

        @param (ddGuerillaApi.DDNode) inLightNode:
        DDNode representing the selected light node in comboBox.

        @param (guerilla.RenderGraphNodeSG) inSceneGraphNode:
        The parent of the Gobo camera.

        @return (None):
        No return value.
        '''

        if inDDNode is None:
            return

        #Check if it is a light Node.
        if ( inDDNode.guerillaType == ddConstants.guerilla.nodeType.DD_RGN_LIGHT   or
             isinstance( inDDNode , ddGuerillaApi.sceneGraphNode.DDSceneGraphNode ) ):

            worldMatrix = inDDNode.getWorldMatrix()
            posX, posY, posZ = worldMatrix.translation

            inDDTransformEulerNode[ 'TX' ].set( posX )
            inDDTransformEulerNode[ 'TY' ].set( posY )
            inDDTransformEulerNode[ 'TZ' ].set( posZ )

            return

        #SceneGraphNode, acting as a locator.
        if isinstance(
            inDDNode                                                            ,
            ddGuerillaApi.renderGraphNodeSceneGraph.DDRenderGraphNodeSceneGraph ):

            global __DL_SCENEGRAPH_NODES
            self.__DL_SCENEGRAPH_NODES = []

            sceneGraphNodes = self.__getDownstreamSceneGraph( inDDNode )
            posX = 0
            posY = 0
            posZ = 0

            for node in sceneGraphNodes:

                worldPosition = node.getworldposition()

                posX += worldPosition.getx()
                posY += worldPosition.gety()
                posZ += worldPosition.getz()

            inDDTransformEulerNode[ 'TX' ].set( posX )
            inDDTransformEulerNode[ 'TY' ].set( posY )
            inDDTransformEulerNode[ 'TZ' ].set( posZ )

            if inLightNode is not None:
                worldMatrix = inLightNode.getWorldMatrix()
                posX , posY , posZ = worldMatrix.translation

                inDDTransformEulerNode[ 'TX' ].set(
                        inDDTransformEulerNode[ 'TX' ].get() + posX )
                inDDTransformEulerNode[ 'TY' ].set(
                        inDDTransformEulerNode[ 'TY' ].get() + posY )
                inDDTransformEulerNode[ 'TZ' ].set(
                        inDDTransformEulerNode[ 'TZ' ].get() + posZ )

            return

        # Use the selected element/geo as parent for gobo scene graph.
        self.__createPathNode( inDDNode         ,
                               inSceneGraphNode )

        return

    def __createPathNode( self             ,
                          inDDNode         ,
                          inSceneGraphNode ):
        '''Create a pathNode with path to object used for instance light and
        used also to parent scene graph that contains Gobo camera.

        @param (ddGuerillaApi.renderGraphNodeSceneGraph.DDRenderGraphNodeSceneGraph |
                ddGuerillaApi.sceneGraphNode.DDSceneGraphNode ) inDDNode:
        objects representing the potential parent for camera constraint.

        @param (guerilla.RenderGraphNodeSG) inSceneGraphNode:
        Parent of Gobo camera.

        return (None):
        No return value
        '''

        parentRenderGraphNode = inSceneGraphNode.parent

        pathNode = parentRenderGraphNode.loadfile(
            '$(LIBRARY)/rendergraph/path.gnode' )[ 0 ]

        pathNode.NodePos.set( ( inSceneGraphNode.NodePos.get()[ 0 ] - 100 ,
                                inSceneGraphNode.NodePos.get()[ 1 ] - 200 ) )

        #Get inputs and outputs to connect nodes.
        pathOutput = pathNode.getoutputs()[ 0 ]
        inSceneGraphNodeInputs = inSceneGraphNode.getinputs()[ 0 ]

        inSceneGraphNodeInputs.connect( pathOutput )

        #Set path in pathNode based on inDDNode full name.
        fullPath = inDDNode.fullName

        if isinstance( ddPipeApi.getCurrentContextEntity() ,
                       ddPipeApi.DDShot                    ):
            fullNameSplitted = fullPath.split( '|' )
            fullPath = '|'.join( fullNameSplitted[ 1: ] )

        elif isinstance( ddPipeApi.getCurrentContextEntity() ,
                         ddPipeApi.DDSequence                ):
            fullNameSplitted = fullPath.split( '|' )
            fullPath = '|'.join( fullNameSplitted[ 2: ] )

        for plug in pathNode.plugs():
            if plug.name == 'Path':
                plug.set( fullPath )

        return

    @staticmethod
    def __createLayerNode( inNameStr         ,
                           inRenderGraphNode ):
        '''Creates a layerNode and set its membership to existing layer.

        @param (str) inNameStr:
        String representing name of the render layer.

        @param (dlGuerillaApi.DLRenderGraph) inRenderGraphNode:
        Node to hold the intended layer node.

        return (guerilla.RenderGraphNodeRenderLayer):
        '''
        with ddGuerillaApi.DDModifier() as mod:

            layerNode = inRenderGraphNode.loadfile(
                '$(LIBRARY)/rendergraph/renderlayer.gnode' )[ 0 ]
            mod.renamenode( layerNode ,
                            inNameStr )
            for plug in layerNode.plugs():
                if plug.name == 'Membership':
                    plug.set( 'layer:B10_{}'.format( inNameStr ) )

        return layerNode

    def __createNodesForGoboCamera( self              ,
                                    inNameStr         ,
                                    inRenderGraphNode ):
        '''Create a layer, merge and sceneGraph nodes inside passed
        render graph node.

        @param (str) inNameStr:
        String representing name of gobo.

        @param (dlGuerillaApi.DLRenderGraph) inRenderGraphNode:
        Node to hold the intended nodes to be created.

        return (ddGuerillaApi.DDCamera):
        Node representing the Gobo camera.
        '''

        layerNode = self.__createLayerNode( inNameStr         ,
                                            inRenderGraphNode )

        sceneGraphNode = self.__createSceneGraphNode( inNameStr         ,
                                                      inRenderGraphNode )

        # Get output node from render graph
        outputNode = inRenderGraphNode.outputNode

        layerNode.NodePos.set(
            ( outputNode.NodePos.get()[ 0 ] - 200 ,
              outputNode.NodePos.get()[ 1 ]       ) )

        sceneGraphMergeNode = inRenderGraphNode.loadfile(
            '$(LIBRARY)/rendergraph/binop.gnode'        )[ 0 ]
        sceneGraphMergeNode.NodePos.set(
            ( outputNode.NodePos.get()[ 0 ] - 500 ,
              outputNode.NodePos.get()[ 1 ]       ) )

        sceneGraphNode.NodePos.set(
            ( sceneGraphMergeNode.NodePos.get()[ 0 ] - 100  ,
              sceneGraphMergeNode.NodePos.get()[ 1 ] - 200  ) )

        ########################################################################
        # Create GoboCamera
        ########################################################################
        goboCamera = ddGuerillaApi.DDCamera.create(
                'Camera_{}'.format( inNameStr ) ,
                inParentNode = sceneGraphNode   )
        goboCamera[ 'FrameRatio' ].value = 1

        ########################################################################
        # Get inputs and outputs from nodes to create connections.
        ########################################################################
        sceneGraphNodeOutput = sceneGraphNode.getoutputs()[ 0 ]

        outputNodeInput = outputNode.getinputs()[ 0 ]

        ## Get connected nodes to output node.
        outputNodeConnections = outputNodeInput.getconnected()

        sceneGraphMergeInput1 , sceneGraphMergeInput2 = (
            sceneGraphMergeNode.getinputs())
        sceneGraphMergeOutput = sceneGraphMergeNode.getoutputs()[ 0 ]

        layerNodeInput1 , layerNodeInput2 = layerNode.getinputs()
        layerNodeOutput = layerNode.getoutputs()[ 0 ]

        ########################################################################
        # Create connections
        ########################################################################
        sceneGraphMergeInput1.connect( outputNodeConnections )
        sceneGraphMergeInput2.connect( sceneGraphNodeOutput )

        layerNodeInput1.connect( sceneGraphMergeOutput )
        outputNodeInput.connect( layerNodeOutput )

        return goboCamera

    @staticmethod
    def __createSceneGraphNode( inNameStr         ,
                                inRenderGraphNode ):
        '''Creates a scene graph node with input and output plugs.

        @param (str) inNameStr:
        String to be used for name.

        @param (dlGuerillaApi.DLRenderGraph) inRenderGraphNode:
        Node to hold the intended layer node.

        @return (guerilla.RenderGraphNodeSG):
        '''

        with ddGuerillaApi.DDModifier() as mod:

            sceneGraphNode = mod.createnode(
                'NodeGraph_{}'.format( inNameStr )                        ,
                type   = ddConstants.guerilla.nodeType.DD_RGN_SCENE_GRAPH ,
                parent = inRenderGraphNode                                )
            inputNode = mod.createnode(
                'Input1'                                                     ,
                type   = ddConstants.guerilla.nodeType.DD_RENDER_GRAPH_INPUT ,
                parent = sceneGraphNode                                      )
            inputNode.PlugName.set( 'Parent' )

            mod.createnode(
                'Output1'                                                     ,
                type   = ddConstants.guerilla.nodeType.DD_RENDER_GRAPH_OUTPUT ,
                parent = sceneGraphNode                                       )

        return sceneGraphNode

    def getFalloffHAngle( self ):
        '''Gets HAngle from Falloff node if this was modified previously.

        @return(int):
        Integer representing the angle if was modified, None otherwise.
        '''

        newName = dlConstants.guerilla.goboLightShaderName.DL_GOBO_FRUSTUM_SHADER_NAME

        frustumNode    = self.__selectedNode.findChild( newName   )
        oldFrustumNode = self.__selectedNode.findChild( 'Frustum' )

        if frustumNode is None and oldFrustumNode is None:
            return

        elif frustumNode is None and oldFrustumNode is not None:
            frustumNode = oldFrustumNode
            frustumNode.rename( newName )

        fallOffNode = frustumNode.findFirst(
            ddGuerillaApi.filters.DDName( 'Falloff' ) ,
            inNodeTypeStr = 'ShaderNodeSL'            )

        for node in fallOffNode.findAll( inNodeTypeStr = 'ShaderNodeIn' ):
            plugName = node.PlugName.get()

            if plugName == 'HAngle':
                return math.degrees( node.Value.get() )

        return

    def existsGoboRenderGraph( self ):
        '''Checks if Gobo render graph for current selection exists.

        @return(bool):
        True if render graph exists False otherwise.
        '''

        goboName = '{}_{}'.format(
            dlConstants.guerilla.renderPass.DL_GOBOMAP_PREFIX ,
            self.__selectedNode.name                          )

        inMainNomenclatureStr = ddPipeApi.DDNomenclature(
            ddPipeApi.nomenclature.DD_ID_GOBOMAP        )

        node = ddGuerillaApi.DDWork.get( inNomenclatureDict = inMainNomenclatureStr )

        if node.findFirst(
                ddGuerillaApi.filters.DDName( goboName )                      ,
                inNodeTypeStr = ddConstants.guerilla.nodeType.DD_RENDER_GRAPH ):
            return True
        else:
            return False

    @staticmethod
    def __getGoboRenderGraphOrder( inShotIndex ):
        '''Get the evaluation order of the gobo render graph.

        @param( PySide2.QtCore.QModelIndex ) inShotIndex:
        Object which store name of shot.

        @return(int):
        Integer representing the evaluation order for gobo rendergraph.
        '''

        mainNomenclature = ddPipeApi.getCurrentContext().mainNomenclature
        ddWorkName       = mainNomenclature.name.capitalize()
        lightingShot     = '{}|{}'.format( ddWorkName         ,
                                           inShotIndex.data() )

        renderGraphs = ddGuerillaApi.DDNode(
            lightingShot ).findAll(
                inNodeTypeStr = ddConstants.guerilla.plugIn.DD_RENDER_GRAPH )

        orders = []

        for renderGraph in renderGraphs:
            if ( renderGraph.name == 'Layering'           or
                 renderGraph.name == 'Lighting_Corrective' ):

                orders.append( renderGraph.Order.get() )

        if len( orders ) == 2:

            orderDiff = max( orders ) - min( orders )

            goboRenderGraphOrder = min( orders ) + (orderDiff / 2)

            return goboRenderGraphOrder

        return 0

    @staticmethod
    def getSelectedLightParentInstances( inShotList ,
                                         inDDNodes  ):
        '''Gets the instances objects based on previous comboBox light
        selected object.

        @param(list) inShotList:
        List of PySide2.QtCore.QModelIndex representing shot
        where to search for instances.

        @param(list) inDDNodes:
        List of ddGuerillaApi.DDNode which are the parents of selected object.

        @return(list):
        List of ddGuerillaApi.renderGraphNodeSceneGraph.DDRenderGraphNodeSceneGraph
        and ddGuerillaApi.sceneGraphNode.DDSceneGraphNode objects
        representing the potential parent for camera constraint.
        '''

        inventory    = ddGuerillaApi.DDInventory.get()
        pathStrList  = []
        matchedNodes = []

        #Check if it is a sequence context and add it as part of the name.
        context     = ddPipeApi.getCurrentContext()

        if context.shot is None:
            sequenceStr = context.sequence.name + '|'
        else:
            sequenceStr = ''

        for ddNode in inDDNodes:

            if isinstance( ddNode , ddGuerillaApi.DDRenderGraphNodePath ):

                pathStrList.append( ddNode.Path.get() )

            elif isinstance( ddNode , ddGuerillaApi.DDRenderGraphNodeSceneGraph ):

                matchedNodes.append( ddNode )

        sceneGraphNodeType = ddConstants.guerilla.nodeType.DD_SCENE_GRAPH_NODE
        primitiveType      = ddConstants.guerilla.nodeType.DD_PRIMITIVE

        for pathStr in pathStrList:
            pathStrSplitted = pathStr.split('|')
            pattern = '\|'.join( pathStrSplitted )

            for shot in inShotList:
                ddNode = ddGuerillaApi.DDNode( sequenceStr + shot.data() )

                for element in ddNode.findAll(
                        inNodeTypeStr = sceneGraphNodeType ):

                    match = re.search( pattern          ,
                                       element.fullName )

                    if match:
                        matchedNodes.append( element )

                for node in inventory.findAll(
                        inLuaPattern  = pattern       ,
                        inNodeTypeStr = primitiveType ):

                    for dependency in node.Instances.getbackdependencies():
                        if dependency.name != 'Instances':
                            continue

                        parent = ddGuerillaApi.DDNode( dependency.parent )

                        if parent not in matchedNodes:
                            matchedNodes.append( parent )

        return matchedNodes

    def getSelectedParentInstances( self            ,
                                    inShotList      ,
                                    inDDNodes       ):
        '''Gets the instances objects based on the parent's selected object.

        @param(list) inShotList:
        List of PySide2.QtCore.QModelIndex representing shot
        where to search for instances.

        @param(list) inDDNodes:
        List of ddGuerillaApi.DDNode which are the parents of selected object.

        @return(list):
        List of ddGuerillaApi.renderGraphNodeSceneGraph.DDRenderGraphNodeSceneGraph
        and ddGuerillaApi.sceneGraphNode.DDSceneGraphNode objects
        representing the potential parent for camera constraint.
        '''

        inventory = ddGuerillaApi.DDInventory.get()
        scene     = ddGuerillaApi.DDScene()

        # isLightAttributes = inSelectionBool
        isLightAttributes = self._isLightAttributes

        pathStrList  = []
        matchedNodes = []

        #Check if it is a sequence context and add it as part of the name.
        context     = ddPipeApi.getCurrentContext()

        if context.shot is None:
            sequenceStr = context.sequence.name + '|'
        else:
            sequenceStr = ''

        for ddNode in inDDNodes:

            if ( isinstance(
                ddNode                                                  ,
                ddGuerillaApi.renderGraphNodePath.DDRenderGraphNodePath ) and
                not isLightAttributes                                       ):

                pathStrList.append( ddNode.Path.get() )

            elif ( isinstance(
                ddNode                                                              ,
                ddGuerillaApi.renderGraphNodeSceneGraph.DDRenderGraphNodeSceneGraph ) and
                not isLightAttributes                                                   ):

                matchedNodes.append( ddNode )

            elif ( isinstance(
                ddNode                                                  ,
                ddGuerillaApi.renderGraphNodePath.DDRenderGraphNodePath ) and
                isLightAttributes                                           ):

                pathStrList.append( ddNode.Path.get() )

        for pathStr in pathStrList:
            pathStrSplitted = pathStr.split('|')
            pattern = '\|'.join( pathStrSplitted )

            if not isLightAttributes:
                for shot in inShotList:
                    ddNode = ddGuerillaApi.DDNode( sequenceStr + shot.data() )

                    for element in ddNode.findAll(
                            inNodeTypeStr = ddConstants.guerilla.nodeType.DD_SCENE_GRAPH_NODE ):

                        match = re.search( pattern          ,
                                           element.fullName )

                        if match:
                            matchedNodes.append( element )

                    for node in inventory.findAll(
                            inLuaPattern = pattern                                     ,
                            inNodeTypeStr = ddConstants.guerilla.nodeType.DD_PRIMITIVE ):

                        for dependency in node.Instances.getbackdependencies():
                            if dependency.name != 'Instances':
                                continue

                            parent = ddGuerillaApi.DDNode( dependency.parent )

                            if parent not in matchedNodes:
                                matchedNodes.append( parent )

            else:
                for element in scene.findAll(
                        inNodeTypeStr = ddConstants.guerilla.nodeType.DD_RGN_LIGHT ):

                    # When 'P' command is used, which set path to instance.
                    if pathStrSplitted[ -1 ] == element.name:
                        pattern = pathStrSplitted[ -1 ]

                    match = re.search( pattern          ,
                                       element.fullName )

                    if match:
                        matchedNodes.append( element )

        return matchedNodes

    def __getRenderGraph( self           ,
                          inShotIndex    ):
        '''Gets render graph for passed shot under "Lighting" DDWork.

        @param( PySide2.QtCore.QModelIndex ) inShotIndex:
        Object which store name of shot.

        @return(list):
        List of dlGuerillaApi.DlRenderGraph
        '''

        mainNomenclature = ddPipeApi.getCurrentContext().mainNomenclature
        ddWorkName = mainNomenclature.name.capitalize()

        lightingShot = '{}|{}'.format( ddWorkName         ,
                                       inShotIndex.data() )
        entityMetadata = dlGuerillaApi.DLEntityMetadata( lightingShot )

        renderGraphs = []
        for renderGraph in entityMetadata.getRenderGraphs():
            if renderGraph.name not in self.__omitRenderGraph():
                renderGraphs.append( renderGraph )

        return renderGraphs

    @staticmethod
    def _isConnected( inDDNode ):
        '''Checks if node's input plugs is connected False otherwise.

        @param( ddGuerillaApi.DDNode ) inDDNode:
        Node to check for connections.

        @return ( bool ):
        True is connected, False otherwise.
        '''

        try:
            connected   = 0
            inputs      = inDDNode.getinputs()
            amount      = 0
            noConnected = 0
            while amount < len( inputs ):

                connectedPlug = inputs[ amount ].getconnected()

                if not connectedPlug:
                    amount += 1
                    noConnected += 1

                else:
                    amount += 1
                    connected += 1

            if noConnected == len( inputs ):
                return False

            elif connected != 0:
                return True

        except AttributeError:
            return False

        return True

    def __omitRenderGraph( self ):
        '''Defines which render graphs to omit based on parent entity of selection.

        @return(list):
        List of strings represent render graph names to omit for connection to
        gobo renderpass.
        '''

        parentEntity = self.__selectedNode.findParent(
            inTypeStr = ddConstants.guerilla.plugIn.DD_ENTITY_METADATA )

        omitTypes = []
        if isinstance( parentEntity.entity , ddPipeApi.DDEntityGroup):

            parentEntityId = parentEntity.entity.subNomenclature.id
            if parentEntityId == ddPipeApi.nomenclature.DD_ID_ENVIRONMENT:
                omitTypes = ( ddBuilder.type.DD_LIGHTING_CORRECTIVE ,
                              ddBuilder.type.DD_LAYERING            ,
                              ddBuilder.type.DD_LIGHTING_POV        )

            elif parentEntityId == ddPipeApi.nomenclature.DD_ID_POV:
                omitTypes = ( ddBuilder.type.DD_LIGHTING_CORRECTIVE ,
                              ddBuilder.type.DD_LAYERING            )

        elif isinstance( parentEntity.entity , ddPipeApi.DDShot ):
            omitTypes = ( ddBuilder.type.DD_LAYERING , )

        return [ str( type ).replace( ' ' , '_') for type in omitTypes ]

    def __findLeafNodes( self     ,
                         inDDNode ):
        '''Finds all path and scene graph nodes
        in the edge (upstream) of the node tree where the selected node is.

        @param (ddGuerillaApi.DDNode) inDDNode:
        Node to check its connections.

        @return (list):
        List of ddGuerillaApi.DDNode.
        '''

        if not self._isConnected( inDDNode ):

            self.__DL_EDGE_NODES.append( inDDNode )

            return self.__DL_EDGE_NODES

        inputs = inDDNode.getinputs()

        for input in inputs:
            connectedPlug = input.getconnected()

            if connectedPlug:
                parentNode = connectedPlug.parent

                self.__findLeafNodes( ddGuerillaApi.DDNode( parentNode ) )

        return self.__DL_EDGE_NODES

    def getParentInstancesNodes( self     ,
                                 inDDNode ):
        '''Gets nodes which are used directly to instance the selected light.

        @param(ddGuerillaApi.DDNode) inDDNode:
        Guerilla node representing the current selection.

        @return(list):
        List of ddGuerillaApi.DDNode
        '''

        global __DL_EDGE_NODES
        self.__DL_EDGE_NODES = []

        nodes = self.__findLeafNodes( inDDNode )

        parentInstancesNodes = []

        for node in nodes:

            # Path nodes
            if isinstance(
                node                                                    ,
                ddGuerillaApi.renderGraphNodePath.DDRenderGraphNodePath ):

                parentInstancesNodes.append( node )

            # SceneGraphNode
            elif isinstance(
                node                                                                ,
                ddGuerillaApi.renderGraphNodeSceneGraph.DDRenderGraphNodeSceneGraph ):

                parentInstancesNodes.append( node )

            # Macro nodes
            elif isinstance(
                node                                              ,
                ddGuerillaApi.renderGraphMacro.DDRenderGraphMacro ):

                childNodes = node.findAll( inRecursiveBool = False )

                for childNode in childNodes:
                    if isinstance(
                        childNode                                                 ,
                        ( ddGuerillaApi.renderGraphNodePath.DDRenderGraphNodePath ,
                          ddGuerillaApi.renderGraphNodeSceneGraph.DDRenderGraphNodeSceneGraph ) ):

                        parentInstancesNodes.append( childNode )

        return parentInstancesNodes
