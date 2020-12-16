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
'''Command/ Menu to create new entity group for selected DDShot objects or
assign shot to and existing entity group.

@package dlGuerillaMenu.createEntityGroup
@author Esteban Ortega <esteban.ortega@latelieranimation.com>
'''

import ddGuerillaCommands

import dlGuerillaTools

__all__ = ( 'DLCreateEntityGroup' , )

class DLCreateEntityGroup( ddGuerillaCommands.DDCommand ):
    '''Shows UI to create a new entity group for selected DDShot, or assign
    DDShot to an existing entity group.
    '''

    ## Name of the command
    # type: str
    DD_NAME = 'Create/Assign Entity Group'

    # ## Shortcut of the command
    # # type: str
    # DD_SHORTCUT = 'Ctrl+Shift+Q'

    @classmethod
    def action( cls     ,
                *inArgs ):
        '''Execute the command.

        @return (None):
        No return value.
        '''

        win = dlGuerillaTools.DLCreateEntityGroup()
        win.exec_()

        return
