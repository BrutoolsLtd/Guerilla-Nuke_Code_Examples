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
'''Cmd Module to connect template Dot nodes.

@package dlNukePipe.connectDots
@author  Esteban Ortega <esteban.ortega@latelieranimation.com>
'''

import math
import re

import nuke
import nukescripts

import ddLogger

import ddNukeApi

__all__ = ( 'DLConnectDots', )

class DLConnectDots():
    '''Tool to connect template Dot nodes.
    '''

    ## Base distance in x to avoid connecting to its Id node in same layer.
    # type: int
    DL_BASE_DISTANCE_X = 850

    ## Base distance in Y to avoid connecting to Id node
    # in different layer prefix.
    # type: int
    DL_BASE_DISTANCE_Y = 3500

    ## Pattern for compositing Dot nodes.
    # type: str
    DL_CP = '_cp_'

    ## Pattern for Dot nodes related to deep Dot nodes.
    # type: str
    DL_DEEP = 'deep'

    ## Pattern for GROUP related Dot nodes.
    # type: str
    DL_GROUP = 'GROUP_'

    ## Pattern for IN in Dot node name.
    # type: str
    DL_IN = '_IN'

    ## Patter for source / input Dot Nodes (Read managers nodes).
    # type: str
    DL_IN_LOWER = '_in_'

    ## Name for new Dot node knob.
    # type: str
    DL_KNOB_NAME = 'DotLabelName'

    ## Label name for new Dot node knob.
    # type: str
    DL_LABEL_NAME = 'Dot_Name'

    ## Pattern for LayerMrg related Dots.
    # type: str
    DL_LAYERMRG = '_LayerMrg_'

    ## Dot Node type.
    # type: str
    DL_NODE_TYPE = 'Dot'

    ## Pattern for OUT in Dot node name.
    # type: str
    DL_OUT = '_OUT'

    ## Patter for Dot nodes to connect.
    # type: str
    DL_PREFIX = '#*'

    ## Pattern preShot in Dot node name.
    # type: str
    DL_PRESHOT = 'preShot'

    ## Pattern postShot in Dot node name.
    # type: str
    DL_POSTSHOT = 'postShot'

    def __init__(self):
        '''Initialize class.

        return(None)
        No return value.
        '''

        ## Stores autoConnect nodes.
        # type: [ddNukeApi.DDNode]
        self.__autoConnectNodeList = []

        ## Stores layer Dots with name pattern "C_cp_Id_IN3" or "C_in_Id_OUT".
        # type: [ddNukeApi.DDNode]
        self.__layerDotsList = []

        ## Stores main pipe three Dots with name pattern "GROUP_LayerMrg_OUT1"
        # or "GROUP_LayerMrg_IN2"
        # type: [ddNukeApi.DDNode]
        self.__mainDotsList = []

        ## Stores any matte paint live group, gizmo.
        # type: [ddNukeApi.DDMattePaintLiveGroup]
        self.__mattePaintNodes = []

        ## Stores renamed Dot nodes based on its backdrop.
        # type: {str: ddNukeApi.DDNode}
        self.__renamedDotNodes = {}

        root = ddNukeApi.DDRoot()

        for node in root.findAll():

            if node.Class() == self.DL_NODE_TYPE:

                tempSplit = node.name.split( '_' )
                partCount = len( tempSplit )

                # "C_cp_Id_IN3" or "C_in_Id_OUT"
                if ( partCount == 4                          and
                     self.DL_LAYERMRG[ 1:-1 ] not in tempSplit ):

                    self.__layerDotsList.append( node )

                # "GROUP_LayerMrg_OUT1"
                elif ( ( self.DL_CP not in node.name       and
                         node.name.startswith( self.DL_GROUP ) ) or
                       self.DL_PRESHOT in node.name              or
                       self.DL_POSTSHOT in node.name              ):

                    self.__mainDotsList.append( node )

            elif ( node.Class() == 'Group'  and
                   'autoConnect' in node.name ):

                self.__autoConnectNodeList.append( node )

            elif node.Class() == 'ddMattePaintLiveGroup':

                self.__mattePaintNodes.append( node )

            elif node.Class() == 'ddBackdrop':

                backdropPrefix = node.nkNode[
                    'ddRenderPassName' ].getValue().split( "_" )[0]

                node.nkNode.selectNodes()

                backdropDotNodes = [ node for node in nuke.selectedNodes()
                                     if ( node.Class() == self.DL_NODE_TYPE     and
                                     self.DL_PREFIX in node[ 'label' ].getValue() ) ]

                nukescripts.clear_selection_recursive()

                if not backdropDotNodes:
                    continue

                #Check every template's Dot node and add a user knob
                #if missing to add Dot name based on backdrop layer prefix.
                for backdropDotNode in backdropDotNodes:
                    newKnob = nuke.String_Knob( self.DL_KNOB_NAME  ,
                                                self.DL_LABEL_NAME )

                    nodeLabel = backdropDotNode[ 'label' ].getValue()
                    newLabel = nodeLabel.replace( self.DL_PREFIX ,
                                                  backdropPrefix )

                    keyLabel = newLabel.replace( '[value name]'       ,
                                                 backdropDotNode.name() )

                    labelNameKnob = backdropDotNode.knob( self.DL_KNOB_NAME )

                    if labelNameKnob:

                        labelNameKnob.setValue( keyLabel )

                    else:
                        backdropDotNode.addKnob( newKnob )
                        backdropDotNode[ self.DL_KNOB_NAME ].setValue( keyLabel )

                    self.__renamedDotNodes[ keyLabel ] = ddNukeApi.DDNode(
                        backdropDotNode                                    )

        return

    def __connectAutoConnectNodeNEW( self ):
        '''Connects autoconnect nodes.

        @return (True):
        True if connections have been made.

        @return (None):
        No return value.
        '''

        if self.__getLayerPrefixes() is None:

            return

        for layerPrefix in self.__getLayerPrefixes():

            layerDotNodes = { ddNodeLabel: ddNode for ddNodeLabel, ddNode in
                              self.__renamedDotNodes.iteritems()          if
                              ddNodeLabel.startswith( layerPrefix[ 0 ] )   }

            autoconnectInNodes = []
            autoconnectOutNode = None

            for labelName, ddNode in layerDotNodes.iteritems():

                if 'autoconnect' in labelName and self.DL_OUT in labelName:

                    autoconnectOutNode = ddNode

                elif 'autoconnect' in labelName and self.DL_IN in labelName:

                    autoconnectInNodes.append( ddNode )

                else:

                    continue

            if not autoconnectInNodes or autoconnectOutNode is None:

                continue

            for inNode in autoconnectInNodes:

                # Connect nodes
                if inNode.nkNode.dependencies():
                    continue

                inNode.nkNode.setInput( 0                         ,
                                        autoconnectOutNode.nkNode )

                ddLogger.DD_NUKE.info(
                    'Dot node {} connected to {}'.format(
                        autoconnectOutNode.name         ,
                        inNode.name                     ) )

        return True

    def __connectAutoConnectNode( self ):
        '''Connects autoConnect nodes to its parent layer's id1.

        @return (True):
        True if connections has been made, None otherwise.
        '''

        #TODO: This method can be removed once autoConnect group node
        # is replaced in template by a Dot node with name patter like
        # "#*_G_cp_autoconnect_IN" and its corresponding OUT node as
        # "#*_E_cp_id_autoconnect_OUT", connectAutoConnectNodeNEW method
        # replace this one.

        if not self.__layerDotsList:

            return

        targetParentDotNodes = []

        for dotNode in self.__layerDotsList:

            if ( 'Id' in dotNode.name     and
                 self.DL_IN in dotNode.name ):

                targetParentDotNodes.append( dotNode )

        dotNodesPairs = {}

        for autoConnectNode in self.__autoConnectNodeList:

            #Distance to id nodes from autoconnect.
            x0 , y0 = autoConnectNode.position
            x1 , y1 = targetParentDotNodes[ 0 ].position
            distanceBase = math.sqrt( math.pow( (x1 - x0) , 2 ) +
                                      math.pow( (y1 - y0) , 2 ) )

            for targetParentDotNode in targetParentDotNodes:

                x1 , y1 = targetParentDotNode.position

                distanceToNode = math.sqrt( math.pow( (x1 - x0) , 2 ) +
                                            math.pow( (y1 - y0) , 2 ) )
                distanceX = x0 - x1

                if ( distanceToNode < distanceBase            and
                     distanceToNode < self.DL_BASE_DISTANCE_Y and
                     y1 < y0                                  and
                     distanceX > self.DL_BASE_DISTANCE_X        ):

                    distanceBase = distanceToNode
                    dotNodesPairs[ autoConnectNode ] = targetParentDotNode

                elif ( distanceToNode == distanceBase           and
                       distanceToNode < self.DL_BASE_DISTANCE_Y and
                       y1 < y0                                  and
                       distanceX > self.DL_BASE_DISTANCE_X        ):

                    dotNodesPairs[ autoConnectNode ] = targetParentDotNode

        # Connect matched nodes.
        for autoConnectNode , outDot in dotNodesPairs.iteritems():

            if autoConnectNode.nkNode.dependencies():

                continue

            autoConnectNode.nkNode.setInput( 0             ,
                                             outDot.nkNode )
            ddLogger.DD_NUKE.info( 'autoConnect node {} connected to {}'.format(
                                   autoConnectNode.name                        ,
                                   outDot.name                                 ) )

        return True

    def __connectDeepDotNodes( self ):
        '''Connects dot nodes with name pattern
        Xdeep_cp_LayerMrg_OUT, VXdeep_cp_LayerMrg_IN

        @return (True):
        True if connections has been made.

        @return (None):
        No return value.
        '''

        if self.__getLayerPrefixes() is None:

            return

        for layerPrefix in self.__getLayerPrefixes():

            layerDotNodes = { ddNodeLabel: ddNode for ddNodeLabel, ddNode in
                              self.__renamedDotNodes.iteritems()          if
                              ddNodeLabel.startswith( layerPrefix[ 0 ] )   }

            deepDotOutNodes = {}
            deepDotInNodes = {}

            for labelName, ddNode in layerDotNodes.iteritems():

                if self.DL_DEEP in labelName and self.DL_OUT in labelName:

                    deepDotOutNodes[ labelName ] = ddNode

                elif self.DL_DEEP in labelName and self.DL_IN in labelName:

                    deepDotInNodes[ labelName ] = ddNode

                else:
                    continue

            if not deepDotInNodes or not deepDotOutNodes:
                continue

            for deepDotInLabel, deepDotInNode in sorted( deepDotInNodes.iteritems() ):

                deepDotInLabelPrefix = deepDotInLabel.split( '_' )[ 0 ]

                for deepDotOutLabel, deepDotOutNode in sorted( deepDotOutNodes.iteritems() ):

                    deepDotOutLabelPrefix = deepDotOutLabel.split( '_' )[ 0 ]

                    if deepDotOutLabelPrefix > deepDotInLabelPrefix:

                        #Connect nodes
                        if deepDotInNode.nkNode.dependencies():
                            continue

                        deepDotInNode.nkNode.setInput( 0                     ,
                                                       deepDotOutNode.nkNode )
                        ddLogger.DD_NUKE.info(
                            'Dot node {} connected to {}'.format(
                                deepDotInNode.name              ,
                                deepDotOutNode.name             ) )

        return True

    def __connectGrpLayerMrgDots( self ):
        '''Connects Dots nodes with name pattern "GROUP_LayerMrg_OUT1",
        which constitute the main tree branch.

        @return (True):
        True if connections has been made.

        @return (None):
        No return value.
        '''

        if not self.__mainDotsList:

            return

        positionYDot = {}

        #Get the top node and the bottom node.
        for mainDot in self.__mainDotsList:

            positionYDot[ mainDot.position[ 1 ] ] = mainDot

        positionYDotList   = positionYDot.items()
        positionYDotSorted = sorted( positionYDotList )

        for index in range( 0                         ,
                            len( positionYDotSorted ) ):

            if self.DL_IN in positionYDotSorted[ index ][ 1 ].name:

                nkNodeInMain = positionYDotSorted[ index ][ 1 ].nkNode

                try:

                    nkNodeOutMain = positionYDotSorted[ index - 1 ][ 1 ].nkNode

                except IndexError:

                    continue

                if nkNodeInMain.dependencies():

                    continue

                nkNodeInMain.setInput( 0             ,
                                       nkNodeOutMain )

                ddLogger.DD_NUKE.info( 'Dot node {} connected to {}'.format(
                                       nkNodeInMain.name()                 ,
                                       nkNodeOutMain.name()                ) )

        return True

    def __connectMattePaintNode( self ):
        '''Connects matte paint nodes in current script to its corresponding Dot
        Node.

        @return (True):
        True if connections has been made.

        @return (None):
        No return value.
        '''

        if not self.__mattePaintNodes:

            return

        nodeDistance = {}

        for matteNode in self.__mattePaintNodes:

            posX0, posY0 = matteNode.position

            for dotNode in self.__layerDotsList:

                posX1, posY1 = dotNode.position

                distance = math.sqrt( math.pow( (posX1 - posX0) , 2 ) +
                                      math.pow( (posY1 - posY0) , 2 ) )

                nodeDistance[ dotNode ] = distance

            #Connect Matte paint node and closest Dot node
            closestDotNode = min( nodeDistance           ,
                                  key = nodeDistance.get )

            if closestDotNode.nkNode.dependencies():

                continue

            closestDotNode.nkNode.setInput( 0                ,
                                            matteNode.nkNode )

            ddLogger.DD_NUKE.info( 'Dot node {} connected to {}'.format(
                                   closestDotNode.name                 ,
                                   matteNode.name                      ) )

        return True

    def __connectLayerDotNodes( self ):
        '''Connects renamed Dot Nodes with name pattern
        "C_cp_Id_IN3" and "C_in_Id_OUT".

        @return (True):
        True if connections has been made.

        #return (None):
        No return value.
        '''

        if self.__getLayerPrefixes() is None:

            return

        for layerPrefix in self.__getLayerPrefixes():

            patterLayerPrefix = '^{}_'.format( layerPrefix )

            layerDotNodes = { ddNodeLabel: ddNode for ddNodeLabel, ddNode in
                              self.__renamedDotNodes.iteritems()          if
                              re.match( patterLayerPrefix , ddNodeLabel )  }

            for labelName, ddNode in layerDotNodes.iteritems():

                tempLabelName = ''

                if self.DL_IN_LOWER in labelName and self.DL_OUT in labelName:

                    #Temp name to find the paired node.
                    labelName = labelName.replace( self.DL_IN_LOWER ,
                                                   self.DL_CP       )
                    labelName = labelName.replace( self.DL_OUT ,
                                                   self.DL_IN  )
                    tempLabelName = labelName[ : labelName.index( self.DL_IN ) +
                                               len( self.DL_IN )               ]

                inNode = None

                if not tempLabelName:

                    continue

                for keyLabelName in layerDotNodes.keys():

                    if tempLabelName in keyLabelName:

                        inNode = layerDotNodes.get( keyLabelName ,
                                                    None         )
                if inNode is None:

                    continue

                #Connect nodes
                if inNode.nkNode.dependencies():

                    continue

                inNode.nkNode.setInput( 0             ,
                                        ddNode.nkNode )

                ddLogger.DD_NUKE.info(
                    'Dot node {} connected to {}'.format( ddNode.name ,
                                                          inNode.name ) )

        return True

    def __connectLayerMgrDotNodes( self ):
        '''Connects Dot nodes with name pattern
        "P_cp_LayerMrg_IN1" or "P_cp_LayerMrg_OUT"

        @return (True):
        Return True if connections have been made.

        @return (None):
        No return value.
        '''

        if self.__getLayerPrefixes() is None:

            return

        dotOutPattern = '{}{}{}'.format( self.DL_CP               ,
                                         self.DL_LAYERMRG[ 1:-1 ] ,
                                         self.DL_OUT              )

        dotInPattern = '{}{}{}'.format( self.DL_CP               ,
                                        self.DL_LAYERMRG[ 1:-1 ] ,
                                        self.DL_IN               )

        dotMainBranchPattern = '{}{}{}{}'.format( self.DL_GROUP      ,
                                                  self.DL_CP[ 1:-1 ] ,
                                                  self.DL_LAYERMRG   ,
                                                  self.DL_IN[ 1: ]   )

        for layerPrefix in self.__getLayerPrefixes():

            layerDotNodes = { ddNodeLabel: ddNode for ddNodeLabel, ddNode in
                              self.__renamedDotNodes.iteritems()          if
                              ddNodeLabel.startswith( layerPrefix )        }

            nodesOutSubset = {}
            nodesInSubset = {}
            nodeInMainBranch = None

            for labelName, ddNode in layerDotNodes.iteritems():

                if ( dotOutPattern in labelName     and
                     self.DL_GROUP not in labelName and
                     self.DL_DEEP  not in labelName   ):

                    nodesOutSubset[ labelName ] = ddNode

                elif ( dotInPattern in labelName      and
                       self.DL_GROUP not in labelName and
                       self.DL_DEEP  not in labelName   ):

                    nodesInSubset[ labelName ] = ddNode

                #This is the main branch Dot node
                elif dotMainBranchPattern in labelName:

                    nodeInMainBranch = ddNode

            if not nodesInSubset and nodesOutSubset and nodeInMainBranch:

                outNode = ( sorted( nodesOutSubset.values() ) )[ 0 ]
                inNode = nodeInMainBranch

                #Connect nodes
                if inNode.nkNode.dependencies() or outNode is None:
                    continue

                inNode.nkNode.setInput( 0              ,
                                        outNode.nkNode )

                ddLogger.DD_NUKE.info(
                    'Dot node {} connected to {}'.format( outNode.name ,
                                                          inNode.name  ) )

                continue

            for nodeOutLabel, ddNodeOut in sorted( nodesOutSubset.iteritems() ):

                nodeOutLabelPrefix = nodeOutLabel.split( '_' )[ 0 ]

                for nodeInLabel, ddNodeIn in sorted( nodesInSubset.iteritems() ):

                    nodeInLabelPrefix = nodeInLabel.split( '_' )[ 0 ]

                    if nodeOutLabelPrefix > nodeInLabelPrefix:

                        outNode = ddNukeApi.DDNode( ddNodeOut )
                        inNode = ddNukeApi.DDNode( ddNodeIn )

                    elif nodeInMainBranch:

                        outNode = ddNukeApi.DDNode( ddNodeOut )
                        inNode = ddNukeApi.DDNode( nodeInMainBranch )

                    else:
                        continue

                    if outNode is None or inNode is None:
                        continue

                    if inNode.nkNode.dependencies():
                        continue

                    inNode.nkNode.setInput( 0              ,
                                            outNode.nkNode )

                    ddLogger.DD_NUKE.info(
                        'Dot node {} connected to {}'.format( outNode.name ,
                                                              inNode.name  ) )

        return True

    def __getLayerPrefixes( self ):
        '''Gets all one letter layer prefixes.

        @return (list):
        A list of one letter str representing all layers in script.

        @return (None):
        No return value if there is no Template Dot Nodes.
        '''

        if not self.__renamedDotNodes:

            return

        prefixList = []

        for label, ddNode in sorted( self.__renamedDotNodes.iteritems() ):

            labelPrefix = label.split( '_' )[ 0 ]

            if labelPrefix not in prefixList:

                prefixList.append( labelPrefix )

        return prefixList

    def connectDots( self ):
        '''Connects all templates Dot nodes accordingly with its name pattern.

        @return (tuple):
        Tuple with None or True if particular set of Dot nodes were connected.
        '''

        return (self.__connectLayerDotNodes()    ,
                self.__connectDeepDotNodes()     ,
                self.__connectLayerMgrDotNodes() ,
                self.__connectGrpLayerMrgDots()     ,
                self.__connectAutoConnectNodeNEW()  ,
                self.__connectAutoConnectNode()     ,
                self.__connectMattePaintNode()      )
