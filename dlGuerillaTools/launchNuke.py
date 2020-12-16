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
'''Module to launch Nuke and execute the passed ddAction graph.

@package dlGuerillaTools.launchNuke
@author Esteban Ortega <esteban.ortega@latelieranimation.com>
@author Etienne Fleurant <etienne.fleurant@latelieranimation.com>
'''

import subprocess

import dlConstants

import ddAction
import ddConstants.fileExtensions
import ddConstants.filesystem

import ddPath

try:
    import simplejson as json
except ImportError:
    import json


def launchNukeGraph( inGraphObj            ,
                     inProjectShortNameStr ):
    '''Launch Nuke from within guerilla passing a ddAction graph to
    be process in Nuke.

    @param (ddAction.DDGraph) inGraphObj:
    ddAction graph to be processed in Nuke.

    @param (str) inProjectShortNameStr:
    String representing the short name of the project.

    @return (None):
    No return value.
    '''

    projectShortName = inProjectShortNameStr

    pathJson = ddAction.DDTempFile(
        extension = ddConstants.fileExtensions.DD_FILE_EXT_JSON )().path.value

    with open( pathJson, 'w' ) as graphFile:

        json.dump( inGraphObj , graphFile )

    aliasesConfigPath = ddPath.constructByJoin( ddConstants.filesystem.DD_ETC ,
                                                'ddAliases.sh'                )

    pcConfigPath = ddPath.constructByJoin( ddConstants.filesystem.DD_ETC ,
                                           'ddPC.sh'                     )

    nukeLaunchPath = ddPath.constructByJoin( ddConstants.filesystem.DD_ETC ,
                                             'launchFoundryNuke.sh'        )

    processActionPath = ddPath.constructByJoin(
        dlConstants.guerilla.filesystem.DL_BIN ,
        'dlProcessActionNoExit.py'             )

    launchCmd = ( 'source {aliasesConfigPath} && '
                  'ddAliases_aliases && '
                  'source {pcConfigPath} && eval '
                  '{projectShortName} '
                  '\'{nukeLaunchPath} '
                  '{processActionPath} '
                  '{pathJson}\' &' ).format( **locals() )

    subprocess.call( launchCmd    ,
                     shell = True )

    return
