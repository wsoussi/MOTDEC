#!/usr/bin/env python
"""
Created on 22-Nov-2012
Copyright 2012 Open Networking Foundation (ONF)

Please refer questions to either the onos test mailing list at <onos-test@onosproject.org>,
the System Testing Plans and Results wiki page at <https://wiki.onosproject.org/x/voMg>,
or the System Testing Guide page at <https://wiki.onosproject.org/x/WYQg>

author:: Anil Kumar ( anilkumar.s@paxterrasolutions.com )

    TestON is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    ( at your option ) any later version.

    TestON is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with TestON.  If not, see <http://www.gnu.org/licenses/>.


"""
from onosclient.component import Component


class API( ):

    """
        This will define common functions for CLI included.
    """
    def __init__( self ):
        super( API, self ).__init__()

    def connect( self ):
        """
           Connection will establish to the remote host using ssh.
           It will take user_name ,ip_address and password as arguments<br>
           and will return the handle.
        """
        super( API, self ).connect()

        return true
