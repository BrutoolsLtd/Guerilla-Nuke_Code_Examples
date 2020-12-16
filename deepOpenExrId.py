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
'''Extension of ddNukeAPi: Commands to act on DeepOpenEXRId patterns knob.

@package dlNukeApi.deepOpenExrId.deepOpenExrId
@author Esteban Ortega <esteban.ortega@latelieranimation.com>
'''

import re

import ddLogger

__all__ = ( 'DLDeepOpenExrId' , )

class DLDeepOpenExrId( object ):
    '''Commands to act on DeepOpenExrId nuke node.
    '''

    ## Match / create the following groups:
    # tags ( All words between ',' )
    # sequence ( Project sequence )
    # shot ( Project sequence and shot )
    # absoluteName ( Pattern / Path without sequenceShot and shape node name )
    # type:_sre.SRE_Pattern
    DL_GROUPS_PATTERNS = re.compile(
        r'^(?P<tags>.*)(?<=,)(?:.*?)'
        r'(?P<sequence>\w*s[a-zA-Z]*\d+(?:\\+\|)|)'
        r'(?P<shot>(?<![a-zA-Z\d])\w*s[a-zA-Z]*\d+(?:[^a-zA-Z\d]+s[a-zA-Z]*\d+)(?:\\+\|)|)'
        r'(?P<absoluteName>.*)(?:\\+\|.*\$$)' )

    ## Match / creates objectName group, based on absoluteName string passed.
    # type:_sre.SRE_Pattern
    DL_OBJECT_NAME_PATTERN = re.compile( '.*\\\\\|(?P<objectName>.*)' )

    ## Define a pattern which divide / identify all the words that starts
    # with atl.
    # type:_sre.SRE_Pattern
    DL_TAGS_PATTERN = re.compile( r'\batl\w+(?:-\w+|)*' )

    def __init__( self            ,
                  inOpenExrIdNode ):
        '''Initialize class.

        @param(nuke) inOpenExrIdNode:
        Mercenary DeepOpenEXRId Nuke node.

        @:return(None):
        NO return value.

        '''

        self.__OpenExrIdNode = inOpenExrIdNode

        return

    def __getPatternsNoSequence( self ):
        '''Removes sequence and shot from string path.

        @return(list):
        List of strings representing the pattern with no sequence and shot
        if there is a match, [] empty list otherwise.
        '''

        nodePatternsStr = self.__OpenExrIdNode[ 'patterns' ].value()

        if nodePatternsStr == '':
            nodePatternsList = []
        else:
            nodePatternsList = nodePatternsStr.split( '\n' )

        nodePatternsNoSequence = []

        for nodePattern in nodePatternsList:
            try:
                matches = self.DL_GROUPS_PATTERNS.match( nodePattern )
                absoluteName = matches.group( 'absoluteName' )
                nodePatternsNoSequence.append( absoluteName )

            except AttributeError:
                nodePatternsNoSequence.append( nodePattern )

        return nodePatternsNoSequence

    def setPatternToNoShapeName( self ):
        '''Sets patterns knob to absolute path without sequence_shot and
        no shape node name.

        @return(None):
        No return value.
        '''
        newPatternsList = []
        patterns        = self.__getPatternsNoSequence()

        if not patterns:
            ddLogger.DD_NUKE.warning(
                '"{}" patterns knob is empty'.format(
                    self.__OpenExrIdNode.name()     ) )
            return

        for pattern in patterns:
            splittedPattern = pattern.split( '|' )
            newPattern = '\|'.join( splittedPattern )
            newPatternsList.append( newPattern )

        multilinePatternStr = '\n'.join( newPatternsList )

        self.__OpenExrIdNode[ 'patterns' ].setValue( multilinePatternStr )

        return

    def setPatternToObjectName( self ):
        '''Sets patterns knob to object name.

        @return(None):
        No return value.
        '''

        newPatterList = []
        patterns      = self.__getPatternsNoSequence()

        if not patterns:
            ddLogger.DD_NUKE.warning(
                '"{}" patterns knob is empty'.format(
                    self.__OpenExrIdNode.name()     ) )
            return

        for pattern in patterns:
            try:
                matchObjectName = self.DL_OBJECT_NAME_PATTERN.match( pattern )
                objectName = matchObjectName.group( 'objectName' )
                newPatterList.append( objectName )

            except AttributeError:
                newPatterList.append( pattern )

        multilinePatternStr = '\n'.join( newPatterList )

        self.__OpenExrIdNode[ 'patterns' ].setValue( multilinePatternStr )

        return

    def setPatternToTagsOnly( self ):
        '''Sets patterns knob to only tags starting with atl.

        @return(None):
        No return value.
        '''

        nodePatternsStr = self.__OpenExrIdNode[ 'patterns' ].value()
        findAllmatches = self.DL_TAGS_PATTERN.findall( nodePatternsStr )

        if findAllmatches:
            uniqueTags = list( set( findAllmatches ) )
            finalStr = '\n'.join( uniqueTags )
            self.__OpenExrIdNode[ 'patterns' ].setValue( finalStr )
        else:
            ddLogger.DD_NUKE.warning(
                'No Tag pattern match for node: {}'.format(
                    self.__OpenExrIdNode.name()           ) )

        return
