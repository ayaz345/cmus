#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dbus
import sys

args = {sys.argv[n]: sys.argv[n + 1] for n in range(1, len(sys.argv) - 1, 2)}
obj = dbus.SessionBus().get_object("net.sf.gaim.GaimService", "/net/sf/gaim/GaimObject")
gaim = dbus.Interface(obj, "net.sf.gaim.GaimInterface")

current = gaim.GaimSavedstatusGetCurrent()
status_type = gaim.GaimSavedstatusGetType(current)
saved = gaim.GaimSavedstatusNew("", status_type)
gaim.GaimSavedstatusSetMessage(saved, f'♪ {args["artist"]} - {args["title"]}')
gaim.GaimSavedstatusActivate(saved)

