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
'''Cmd Module to bring lightKey references and last shot renders.

@package dlNukePipe.lightKeyReferences
@author  Esteban Ortega <esteban.ortega@latelieranimation.com>
'''

import nuke
import nukescripts

import ddNukeApi
import ddPipeApi

__all__ = ( 'DLLightKeyReferencesRenders' , )

class DLLightKeyReferencesRenders():
    '''Tool to bring lightKey references into nuke and last renders
    for every shot in current sequence.
    '''

    ## Color for reference frames backdrop
    # type: int
    DL_COLOR_REFERENCE = 2386071040

    ## Color for shot renders backdrop.
    # type: int
    DL_COLOR_SHOT_RENDER = 1908830464

    ## Label for reference frames / lightKey.
    # type: str
    DL_REFERENCE = 'reference'

    ## Label for shot render frames.
    # type: str
    DL_SHOT_RENDER = 'shotRender'

    def __init__( self ):
        '''Initialize class.

        @return(None):
        No return value.
        '''

        ## Stores the existing preShotReferenceBackdrop.
        # type: ddNukeAPi.DDBrackdrop
        self.__preShotRefBackdrop = None

        for node in ddNukeApi.DDRoot().findAll():

            if node.Class() == 'ddBackdrop' and node.label == 'preShotReference':

                self.__preShotRefBackdrop = node

                break

        return

    def addAllReferences( self ):
        '''Add reference frames (lightKey) and last shot rendered in backdrop
        preShotReference.

        @return(None):
        NO return value.
        '''

        self.addReferenceFrames()
        self.addShotRenderFrames()

        self.createBackdrop()
        self.createBackdrop( inReferenceBool = False )

        nukescripts.clear_selection_recursive()

        nuke.message( 'Process completed!' )

        return

    def addReferenceFrames( self ):
        '''Add last published reference frames in backdrop.

        @return(None):
        No return value.
        '''

        nukescripts.clear_selection_recursive()

        for node in ddNukeApi.DDRoot().findAll():

            #Avoid ValueError: A PythonObject is not attached to a node
            newNode = ddNukeApi.DDNode( node )

            if newNode is None:
                continue

            if newNode.label == self.DL_REFERENCE:
                newNode.delete()

        ########################################################################
        # Get published reference frames
        ########################################################################
        publishedReferences = self.getPublishedReferences()

        if not publishedReferences:

            nuke.message( 'There are not Reference Frames published' )

            return

        readNodes = self.createReadNodes( publishedReferences )

        self.arrangeNodeInBackdrop( readNodes )

        self.createContactSheet( readNodes )

        nukescripts.clear_selection_recursive()

        return

    def addShotRenderFrames( self ):
        '''Add last published shot renders frames in backdrop.

        @return(None):
        No return value.
        '''

        nukescripts.clear_selection_recursive()

        for node in ddNukeApi.DDRoot().findAll():

            #Avoid ValueError: A PythonObject is not attached to a node
            newNode = ddNukeApi.DDNode( node )

            if newNode is None:
                continue

            if newNode.label == self.DL_SHOT_RENDER:
                newNode.delete()

        ########################################################################
        # Get published shot renders.
        ########################################################################
        publishedRenders = []

        context  = ddPipeApi.getCurrentContext()
        sequence = context.sequence
        shots    = sequence.shots

        for shot in shots:

            publishedRender = self.getLastPublishedRender( shot )

            if publishedRender:

                publishedRenders.append( publishedRender )

        if not publishedRenders:

            nuke.message( 'There are not Shot Frames published' )

            return

        readNodes = self.createReadNodes( publishedRenders        ,
                                          inReferenceBool = False )

        self.arrangeNodeInBackdrop( readNodes          ,
                                    inLeftBool = False )

        self.createContactSheet( readNodes               ,
                                 inReferenceBool = False )

        nukescripts.clear_selection_recursive()

        return

    def arrangeNodeInBackdrop( self              ,
                               inNodesDict       ,
                               inLeftBool = True ):
        '''Move set of nodes (DDRead and contactsheet) into preShotReference
        backdrop.

        @param(dict) inNodesDict:
        Dict of DDRead and contactSheet nodes, {index : node }

        @param(bool) inLeftBool:
        True to arrange nodes over left side of backdrop, arrange over right
        if False.

        @return(None):
        No return value.
        '''

        if self.__preShotRefBackdrop is None:

            xposReference = 0
            yposReference = 0
            xOffset = 100

        else:

            if inLeftBool:

                xOffset = 100

                xposReference = self.__preShotRefBackdrop.knob( 'xpos' ).value()
                yposReference = self.__preShotRefBackdrop.knob( 'ypos' ).value()

            else:

                xOffset = -100

                xposReference = ( self.__preShotRefBackdrop.knob( 'xpos' ).value()    +
                                  self.__preShotRefBackdrop.knob( 'bdwidth' ).value() )

                yposReference = self.__preShotRefBackdrop.knob( 'ypos' ).value()

        for index , node in inNodesDict.items():

            if index == 0:

                node.knob( 'xpos' ).setValue( xposReference + xOffset )
                node.knob( 'ypos' ).setValue( yposReference + 200 )

                xposReference = node.knob( 'xpos' ).value()
                yposReference = node.knob( 'ypos' ).value()

            else:

                node.knob( 'xpos' ).setValue( xposReference + xOffset )
                node.knob( 'ypos' ).setValue( yposReference )

                xposReference = node.knob( 'xpos' ).value()
                yposReference = node.knob( 'ypos' ).value()

        return

    def createBackdrop( self                   ,
                        inReferenceBool = True ):
        '''
        Create a backdrop for reference read and contactsheet node.

        @param(bool) inReferenceBool:
        Creates backdrop for reference frames if True, creates backdrop
        for shot renders if false.

        @return(None):
        No return value.
        '''

        if inReferenceBool:

            label   = self.DL_REFERENCE
            bdColor = self.DL_COLOR_REFERENCE

        else:

            label   = self.DL_SHOT_RENDER
            bdColor = self.DL_COLOR_SHOT_RENDER

        nukescripts.clear_selection_recursive()

        for node in ddNukeApi.DDRoot().findAll():

            if node.label == label:

                node.setSelected( True )

        backdrop = nukescripts.autoBackdrop()
        backdrop.knob( 'label' ).setValue( label )
        backdrop.knob( 'tile_color' ).setValue( bdColor )
        backdrop.knob( 'bdwidth' ).setValue(
            backdrop.knob( 'bdwidth' ).value() + 80 )
        backdrop.knob( 'bdheight' ).setValue(
            backdrop.knob( 'bdheight' ).value() + 40 )

        return

    def createContactSheet( self                   ,
                            inReadNodesDict        ,
                            inReferenceBool = True ):
        '''Creates contact sheet node arrange it and connects DDRead nodes.

        @param(dic) inReadNodesDict:
        A dictionary of DDRead nodes.

        @param(bool) inReferenceBool:
        True to create DDReads for reference frames, for shot renders if False.

        @return(None):
        No return value.
        '''

        if not inReadNodesDict:
            return

        if inReferenceBool:
            label = self.DL_REFERENCE
        else:
            label = self.DL_SHOT_RENDER

        contactSheetNode = nuke.nodes.ContactSheet()
        contactSheetNode.knob( 'label').setValue( label )
        contactSheetNode.knob( 'center' ).setValue( True )

        numRows = len( inReadNodesDict ) / 4

        if len( inReadNodesDict ) % 4 != 0:

            numRows += 1

        contactSheetNode.knob( 'rows'   ).setValue( numRows )
        contactSheetNode.knob( 'width'  ).setValue( 4000 )
        contactSheetNode.knob( 'height' ).setValue( 1000 * numRows )

        for index , readNode in inReadNodesDict.items():
            contactSheetNode.setInput( index           ,
                                       readNode.nkNode )

        if len( inReadNodesDict ) % 2 == 0:

            midNode = inReadNodesDict.get( ( len( inReadNodesDict ) / 2 ) - 1  )

            xpos = midNode.knob( 'xpos' ).value()
            ypos = midNode.knob( 'ypos' ).value()

            contactSheetNode.knob( 'xpos' ).setValue( xpos + 50  )
            contactSheetNode.knob( 'ypos' ).setValue( ypos + 200 )

        else:

            midNode = inReadNodesDict.get( len( inReadNodesDict ) / 2 )

            xpos = midNode.knob( 'xpos' ).value()
            ypos = midNode.knob( 'ypos' ).value()

            contactSheetNode.knob( 'xpos' ).setValue( xpos )
            contactSheetNode.knob( 'ypos' ).setValue( ypos + 200 )

        return

    def createReadNodes( self                   ,
                         inPublishedFilesList   ,
                         inReferenceBool = True ):
        '''Create DDRead nodes in a row.

        @param(list) inPublishedFilesList:
        List of ddPipeApi.DDPublishedFiles

        @param(bool) inReferenceBool:
        True to create DDReads for reference frames, for shot renders if False.

        @return(dict):
        Return a dictionary with the order of creation as an index and DDRead node
        as a value. { index : DDRead }
        '''

        if not inPublishedFilesList:
            return

        if inReferenceBool:
            label = self.DL_REFERENCE
        else:
            label = self.DL_SHOT_RENDER

        readNodes = {}

        for index , publishFile in enumerate( inPublishedFilesList ):
            readNode = ddNukeApi.DDRead.create( publishFile.localPath )
            readNode.knob( 'label').setValue( label )
            readNode.knob( 'on_error' ).setValue( 'nearest frame' )
            readNodes[ index ] = readNode

        return readNodes

    @staticmethod
    def getPublishedReferences():
        '''Gets render references for every shot in current sequence.

        @return(list):
        List of ddPipeApi.DDPublishedFile if any, [] if there is no published files.
        '''
        import ddLogger

        context = ddPipeApi.getCurrentContext()

        if context is None:

            ddLogger.DD_NUKE.warning( 'There is no context!' )

            raise AttributeError( 'Not able to find a context!' )

        context = context.sequence

        # Lighting and Concept are valid main nomenclature in this case
        mainNoms = [
            ddPipeApi.DDNomenclature(ddPipeApi.nomenclature.DD_ID_LIGHTING),
            ddPipeApi.DDNomenclature(ddPipeApi.nomenclature.DD_ID_CONCEPT)
        ]

        subNom = ddPipeApi.DDNomenclature( ddPipeApi.nomenclature.DD_ID_REFERENCE )

        fileTypes = [
            ddPipeApi.publishedFileType.DD_ID_JPG ,
            ddPipeApi.publishedFileType.DD_ID_PNG
        ]

        filters = [
            ddPipeApi.DDPublishedFile.entity == ddPipeApi.DDEntity( context ) ,
            ddPipeApi.DDPublishedFile.mainNomenclature.in_( mainNoms )        ,
            ddPipeApi.DDPublishedFile.subNomenclature  == subNom              ,
            ddPipeApi.DDPublishedFile.type.in_( fileTypes )                   ,
            ddPipeApi.DDPublishedFile.step == ddPipeApi.DDStep(
                ddPipeApi.step.DD_ID_SEQUENCE_LIGHTING                        )
        ]

        return ddPipeApi.DDPublishedFile.getAll(
                inFilters = filters                                          ,
                inOrder   = ddPipeApi.DDPublishedFile.DD_ORDER_ID_DESCENDING )

    @staticmethod
    def getLastPublishedRender( inShotEntity ):
        '''Gets last published render file for every shot in current sequence.

        @param(ddPipeApi.DDShot) inShotEntity:
        Shot under which renders should be query.

        @return(list):
        List of ddPipeApi.DDPublishedFile if any, [] if there is no published files.
        '''

        context = ddPipeApi.getCurrentContext()
        subNom = ddPipeApi.DDNomenclature( ddPipeApi.nomenclature.DD_ID_RENDER )

        filters = [
            ddPipeApi.DDPublishedFile.entity           == inShotEntity             ,
            ddPipeApi.DDPublishedFile.mainNomenclature == context.mainNomenclature ,
            ddPipeApi.DDPublishedFile.subNomenclature  == subNom                   ,
            ddPipeApi.DDPublishedFile.type             ==
                ddPipeApi.publishedFileType.DD_ID_EXR                              ,
            ddPipeApi.DDPublishedFile.step             == ddPipeApi.DDStep(
                ddPipeApi.step.DD_ID_SHOT_LIGHTING                        )        ,
            ddPipeApi.DDPublishedFile.token2           == None                     ]

        return ddPipeApi.DDPublishedFile.getFirst(
                inFilters = filters                                          ,
                inOrder   = ddPipeApi.DDPublishedFile.DD_ORDER_ID_DESCENDING )
