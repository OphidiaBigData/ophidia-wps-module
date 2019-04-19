#!/usr/bin/env python
#
#    Ophidia WPS Module
#    Copyright (C) 2015-2019 CMCC Foundation
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from pywps.app.Service import Service
from processes.ophidia import OphExecuteMain
from processes.ophidia import oph_aggregate
from processes.ophidia import oph_aggregate2
from processes.ophidia import oph_apply
from processes.ophidia import oph_b2drop
from processes.ophidia import oph_cancel
from processes.ophidia import oph_cluster
from processes.ophidia import oph_concatnc
from processes.ophidia import oph_concatnc2
from processes.ophidia import oph_containerschema
from processes.ophidia import oph_createcontainer
from processes.ophidia import oph_cubeelements
from processes.ophidia import oph_cubeio
from processes.ophidia import oph_cubeschema
from processes.ophidia import oph_cubesize
from processes.ophidia import oph_delete
from processes.ophidia import oph_deletecontainer
from processes.ophidia import oph_drilldown
from processes.ophidia import oph_duplicate
from processes.ophidia import oph_explorecube
from processes.ophidia import oph_explorenc
from processes.ophidia import oph_exportnc
from processes.ophidia import oph_exportnc2
from processes.ophidia import oph_folder
from processes.ophidia import oph_fs
from processes.ophidia import oph_get_config
from processes.ophidia import oph_hierarchy
from processes.ophidia import oph_importfits
from processes.ophidia import oph_importnc
from processes.ophidia import oph_importnc2
from processes.ophidia import oph_input
from processes.ophidia import oph_instances
from processes.ophidia import oph_intercube
from processes.ophidia import oph_list
from processes.ophidia import oph_log_info
from processes.ophidia import oph_loggingbk
from processes.ophidia import oph_man
from processes.ophidia import oph_manage_session
from processes.ophidia import oph_merge
from processes.ophidia import oph_mergecubes
from processes.ophidia import oph_mergecubes2
from processes.ophidia import oph_metadata
from processes.ophidia import oph_movecontainer
from processes.ophidia import oph_operators_list
from processes.ophidia import oph_permute
from processes.ophidia import oph_primitives_list
from processes.ophidia import oph_publish
from processes.ophidia import oph_randcube
from processes.ophidia import oph_randcube2
from processes.ophidia import oph_reduce
from processes.ophidia import oph_reduce2
from processes.ophidia import oph_resume
from processes.ophidia import oph_rollup
from processes.ophidia import oph_script
from processes.ophidia import oph_search
from processes.ophidia import oph_service
from processes.ophidia import oph_set
from processes.ophidia import oph_showgrid
from processes.ophidia import oph_split
from processes.ophidia import oph_subset
from processes.ophidia import oph_subset2
from processes.ophidia import oph_tasks
from processes.ophidia import oph_unpublish
from processes.ophidia import oph_wait

processes = [
    OphExecuteMain(),
    oph_aggregate(),
    oph_aggregate2(),
    oph_apply(),
    oph_b2drop(),
    oph_cancel(),
    oph_cluster(),
    oph_concatnc(),
    oph_concatnc2(),
    oph_containerschema(),
    oph_createcontainer(),
    oph_cubeelements(),
    oph_cubeio(),
    oph_cubeschema(),
    oph_cubesize(),
    oph_delete(),
    oph_deletecontainer(),
    oph_drilldown(),
    oph_duplicate(),
    oph_explorecube(),
    oph_explorenc(),
    oph_exportnc(),
    oph_exportnc2(),
    oph_folder(),
    oph_fs(),
    oph_get_config(),
    oph_hierarchy(),
    oph_importfits(),
    oph_importnc(),
    oph_importnc2(),
    oph_input(),
    oph_instances(),
    oph_intercube(),
    oph_list(),
    oph_log_info(),
    oph_loggingbk(),
    oph_man(),
    oph_manage_session(),
    oph_merge(),
    oph_mergecubes(),
    oph_mergecubes2(),
    oph_metadata(),
    oph_movecontainer(),
    oph_operators_list(),
    oph_permute(),
    oph_primitives_list(),
    oph_publish(),
    oph_randcube(),
    oph_randcube2(),
    oph_reduce(),
    oph_reduce2(),
    oph_resume(),
    oph_rollup(),
    oph_script(),
    oph_search(),
    oph_service(),
    oph_set(),
    oph_showgrid(),
    oph_split(),
    oph_subset(),
    oph_subset2(),
    oph_tasks(),
    oph_unpublish(),
    oph_wait()
]

application = Service(
    processes,
    ['/usr/local/ophidia/extra/wps/etc/pywps.cfg']
)

