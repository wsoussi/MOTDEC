#!/usr/bin/env python
"""
Created on 29-Nov-2012
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
from onosclient.apidriver import API


class Controller( API ):
    # The common functions for emulator included in emulatordriver

    def __init__( self ):
        super( Controller, self ).__init__()
