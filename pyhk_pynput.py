#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Michael Schurpf
# E-mail: michaelschuerpf AT gmail DOT com
#
# Extends pyhook to have normal hotkey functionality like autohotkey (AHK) scripts.
# Hotkeys have to be entered in lists! Even if single items.
# Hotkeys can be entered in ID list or human readble.
# Example: human readble: ['Lcontrol','7'] for left CTRL 7.
# or ['Ctrl','7'] for CTRL 7
# mouse example: ['mouse left','A'] for mouse left and A together
# See createKeyLookup function for all labels,
#
# Remark:
# mouse move, mouse wheel up, mouse wheel down can only be used on its own
# Example: ['mouse wheel down']
# Not working ['mouse wheel down','4']
#
# Scripts maintained at http://www.swisstard.com
# Comments, suggestions and bug reports welcome.
#
# Released subject to the GNU Public License
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition to the permissions in the GNU General Public License, the
# authors give you unlimited permission to link or embed the compiled
# version of this file into combinations with other programs, and to
# distribute those combinations without any restriction coming from the
# use of this file. (The General Public License restrictions do apply in
# other respects; for example, they cover modification of the file, and
# distribution when not linked into a combine executable.)
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Modifications by russelg:
# - python3 support
# - move to pynput over pyhook

try:
    import _thread
except:
    import thread as _thread

# import pynput._util.win32
from pynput.keyboard import Listener as keyboardListener
from pynput.mouse import Listener as mouseListener


def new_translate(self, vk, is_press):
    """ Fix for moses-palmer/pynput/issues/15 """
    return {
        "vk": vk
    }

keyboardListener._translate = new_translate


class pyhk:
    """Hotkey class extending pynput"""

    def __init__(self):
        self.KeyDownID = []
        self.KeyDown = []

        self.UserHKF = []
        self.UserHKFUp = []
        self.HKFIDDict = {}

        (self.ID2Key, self.Key2ID) = self.createKeyLookup()

        (self.mouseDown_MID2eventMessage,
         self.mouseDown_eventMessage2MID,
         self.mouseUp_MID2eventMessage,
         self.mouseUp_eventMessage2MID) = self.createMouseLookup()

        (self.singleEventMouseMessage, self.singleEventMID) = \
            self.createSingleEventMouse()

        self.KeyID2MEID = self.createMergeKeys()

        self.EndHotkey = ['Ctrl', 'Shift', 'Q']
        self.setEndHotkey(self.EndHotkey)

        self.mouselistener = None
        self.keyboardlistener = None

    def start(self):
        """Start pyhk to check for hotkeys"""
        with mouseListener(on_move=self.onMouseMove,
                           on_scroll=self.onMouseScroll,
                           on_click=self.OnMouseClick) as self.mouselistener:

            with keyboardListener(on_press=self.OnKeyDown,
                                  on_release=self.OnKeyUp) as \
                    self.keyboardlistener:

                self.mouselistener.join()
                self.keyboardlistener.join()

    def end(self):
        """End pyhk to check for hotkeys"""
        self.mouselistener.stop()
        self.keyboardlistener.stop()

    def isIDHotkey(self, hotkey):
        """Test if hotkey is coded in IDs"""
        for key in hotkey:
            if type(key) == str:
                return False
        return True

    def isHumanHotkey(self, hotkey):
        """Test if hotkey is coded human readable. Ex ALT F2"""
        for key in hotkey:
            if key not in self.Key2ID:
                return False
        return True

    def hotkey2ID(self, hotkey):
        """Converts human readable hotkeys to IDs"""
        if self.isHumanHotkey(hotkey):
            return [self.Key2ID[key] for key in hotkey]
        else:
            raise Exception('Invalid Hotkey')

    def getHotkeyList(self, hotkey):
        """Create a IDlist of hotkeys if necessary to ensure functionality of merged hotkeys"""
        hotkeyVariationList = []
        hotkeyList = []

        if self.isIDHotkey(hotkey):
            IDHotkey = hotkey
        else:
            IDHotkey = self.hotkey2ID(hotkey)

        IDHotkeyTemp = IDHotkey[:]

        for Key in self.KeyID2MEID:
            if self.KeyID2MEID[Key] in IDHotkeyTemp:
                MEIDTemp = self.KeyID2MEID[Key]
                KeyIDVariationTemp = [k for k in self.KeyID2MEID
                                      if self.KeyID2MEID[k] == MEIDTemp]
                IDHotkeyTemp.remove(MEIDTemp)
                hotkeyVariationList.append(KeyIDVariationTemp)

        if len(hotkeyVariationList) > 0:
            hotkeyVariationList.append(IDHotkeyTemp)
            hotkeyList = UniquePermutation(hotkeyVariationList)
        else:
            hotkeyList = [IDHotkey]

        return hotkeyList

    def addHotkey(self, hotkey, fhot, isThread=False, up=False):
        """Add hotkeys with according function"""
        hotkeyList = self.getHotkeyList(hotkey)

        newHKFID = self.getNewHKFID()
        self.HKFIDDict[newHKFID] = []

        func = ExecFunThread(fhot).Start if isThread else fhot

        if up:
            if len(hotkey) < 2:
                for IDHotKeyItem in hotkeyList:
                    self.UserHKFUp.append([IDHotKeyItem, func])
                    self.HKFIDDict[newHKFID].append([IDHotKeyItem, func])
        else:
            for IDHotKeyItem in hotkeyList:
                self.UserHKF.append([IDHotKeyItem, func])
                self.HKFIDDict[newHKFID].append([IDHotKeyItem, func])

        return newHKFID

    def removeHotkey(self, hotkey=False, id=False):
        """Remove hotkeys and corresponding function"""
        HKFID = id
        try:
            if hotkey:
                hotkeyList = self.getHotkeyList(hotkey)
                try:
                    UserHKFTemp = [[hotk, fun] for (hotk, fun) in
                                   self.UserHKF if not hotk
                                   in hotkeyList]
                    self.UserHKF = UserHKFTemp[:]
                except:
                    pass
                try:
                    UserHKFTemp = [[hotk, fun] for (hotk, fun) in
                                   self.UserHKFUp if not hotk
                                   in hotkeyList]
                    self.UserHKFUp = UserHKFTemp[:]
                except:
                    pass
            elif HKFID:
                for item in self.HKFIDDict[HKFID]:
                    try:
                        self.UserHKF.remove(item)
                    except:
                        self.UserHKFUp.remove(item)
                self.HKFIDDict.pop(HKFID)
            else:
                self.UserHKF = []
                self.UserHKFUp = []
        except:
            pass

    def setEndHotkey(self, hotkey):
        """Add exit hotkeys"""
        self.removeHotkey(self.EndHotkey)
        self.EndHotkey = hotkey
        self.addHotkey(hotkey, self.end)

    def getNewHKFID(self):
        try:
            return max(self.HKFIDDict.keys()) + 1
        except:
            return 1

    def isHotkey(self, hotkey):
        """Check if hotkey is pressed down
            Hotkey is given as KeyID"""
        if not len(hotkey) == len(self.KeyDownID):
            return False
        for hotk in hotkey:
            if not hotk in self.KeyDownID:
                return False

        return True

    def OnMouseClick(self, x, y, button, pressed):
        event = button.value[1] if pressed else button.value[0]
        if pressed:
            eventID = self.mouseDown_eventMessage2MID[event]
            if not eventID in self.KeyDownID:
                self.KeyDownID.append(eventID)

                for (hk, fun) in self.UserHKF:
                    if self.isHotkey(hk):
                        fun()
        else:
            eventID = self.mouseUp_eventMessage2MID[event]

            for (hk, fun) in self.UserHKFUp:
                if hk[0] == eventID:
                    fun()

            if eventID in self.KeyDownID:
                self.KeyDownID.remove(eventID)

        return True

    def OnKeyDown(self, event):
        if hasattr(event, 'value'):
            event = event.value
        eventID = event.vk

        if not eventID in self.KeyDownID:
            self.KeyDownID.append(eventID)

            for (hk, fun) in self.UserHKF:
                if self.isHotkey(hk):
                    fun()

        return True

    def OnKeyUp(self, event):
        if hasattr(event, 'value'):
            event = event.value
        eventID = event.vk

        for (hk, fun) in self.UserHKFUp:
            if hk[0] == eventID:
                fun()

        if eventID in self.KeyDownID:
            self.KeyDownID.remove(eventID)

        return True

    def onMouseMove(self, x, y):
        eventID = 1000
        self.KeyDownID.append(eventID)

        for (hk, fun) in self.UserHKF:
            if self.isHotkey(hk):
                fun()

        self.KeyDownID.remove(eventID)

        return True

    def onMouseScroll(self, x, y, dx, dy):
        if dy > 0:
            eventID = 1004
        else:
            eventID = 1005

        self.KeyDownID.append(eventID)

        for (hk, fun) in self.UserHKF:
            if self.isHotkey(hk):
                fun()

        self.KeyDownID.remove(eventID)

    def createKeyLookup(self):
        """Creates Key look up dictionaries, change names as you please"""

        ID2Key = {
            8: 'Back',
            9: 'Tab',
            13: 'Return',
            20: 'Capital',
            27: 'Escape',
            32: 'Space',
            33: 'Prior',
            34: 'Next',
            35: 'End',
            36: 'Home',
            37: 'Left',
            38: 'Up',
            39: 'Right',
            40: 'Down',
            44: 'Snapshot',
            46: 'Delete',
            48: '0',
            49: '1',
            50: '2',
            51: '3',
            52: '4',
            53: '5',
            54: '6',
            55: '7',
            56: '8',
            57: '9',
            65: 'A',
            66: 'B',
            67: 'C',
            68: 'D',
            69: 'E',
            70: 'F',
            71: 'G',
            72: 'H',
            73: 'I',
            74: 'J',
            75: 'K',
            76: 'L',
            77: 'M',
            78: 'N',
            79: 'O',
            80: 'P',
            81: 'Q',
            82: 'R',
            83: 'S',
            84: 'T',
            85: 'U',
            86: 'V',
            87: 'W',
            88: 'X',
            89: 'Y',
            90: 'Z',
            91: 'Lwin',
            92: 'Rwin',
            93: 'App',
            95: 'Sleep',
            96: 'Numpad0',
            97: 'Numpad1',
            98: 'Numpad2',
            99: 'Numpad3',
            100: 'Numpad4',
            101: 'Numpad5',
            102: 'Numpad6',
            103: 'Numpad7',
            104: 'Numpad8',
            105: 'Numpad9',
            106: 'Multiply',
            107: 'Add',
            109: 'Subtract',
            110: 'Decimal',
            111: 'Divide',
            112: 'F1',
            113: 'F2',
            114: 'F3',
            115: 'F4',
            116: 'F5',
            117: 'F6',
            118: 'F7',
            119: 'F8',
            120: 'F9',
            121: 'F10',
            122: 'F11',
            123: 'F12',
            144: 'Numlock',
            160: 'Lshift',
            161: 'Rshift',
            162: 'Lcontrol',
            163: 'Rcontrol',
            164: 'Lmenu',
            165: 'Rmenu',
            186: 'Oem_1',
            187: 'Oem_Plus',
            188: 'Oem_Comma',
            189: 'Oem_Minus',
            190: 'Oem_Period',
            191: 'Oem_2',
            192: 'Oem_3',
            219: 'Oem_4',
            220: 'Oem_5',
            221: 'Oem_6',
            222: 'Oem_7',
            1001: 'mouse left',
            1002: 'mouse right',
            1003: 'mouse middle',
            1000: 'mouse move',
            1004: 'mouse wheel up',
            1005: 'mouse wheel down',
            1010: 'Ctrl',
            1011: 'Alt',
            1012: 'Shift',
            1013: 'Win',
        }

        Key2ID = dict(list(map(lambda x, y: (x, y), list(ID2Key.values()),
                               list(ID2Key.keys()))))

        return (ID2Key, Key2ID)

    def createMouseLookup(self):
        """Takes a event.Message from mouse and converts it to artificial KeyID"""

        mouseDown_MID2eventMessage = {1001: 2, 1002: 8, 1003: 32}
        mouseDown_eventMessage2MID = dict(list(map(lambda x, y: (x, y),
                                                   list(
                                                       mouseDown_MID2eventMessage.values()),
                                                   list(mouseDown_MID2eventMessage.keys()))))

        mouseUp_MID2eventMessage = {1001: 4, 1002: 16, 1003: 64}
        mouseUp_eventMessage2MID = dict(list(map(lambda x, y: (x, y),
                                                 list(
                                                     mouseUp_MID2eventMessage.values()),
                                                 list(mouseUp_MID2eventMessage.keys()))))

        return (mouseDown_MID2eventMessage, mouseDown_eventMessage2MID,
                mouseUp_MID2eventMessage, mouseUp_eventMessage2MID)

    def createSingleEventMouse(self):
        """Store events that get executed on single event like wheel up
        MID   event.Message    pyhk hotkey      comments
        1000  512              mouse move
        1004  522              mouse wheel up   event.Wheel = 1
        1005  522              mouse wheel up   event.Wheel = 1"""

        singleEventMouseMessage = [512, 522]
        singleEventMID = [1000, 1004, 1005]

        return (singleEventMouseMessage, singleEventMID)

    def createMergeKeys(self):
        """Merge two keys into one
        KeyID   MEID    MergeHumanHotkey
        162     1010     Ctrl  (Lcontrol)
        163     1010     Ctrl  (Rcontrol
        164     1011     Alt   (Lmenu)
        165     1011     Alt   (Rmenu)
        160     1012     Shift (Lshift)
        161     1012     Shift (Rshift)
        91      1013     Win    (Lwin)
        92      1013     Win    (Rwin)"""

        KeyID2MEID = {
            162: 1010,
            163: 1010,
            164: 1011,
            165: 1011,
            160: 1012,
            161: 1012,
            91: 1013,
            92: 1013,
        }
        return KeyID2MEID

    def getHotkeyListNoSingleNoModifiers(self):
        """return a list of all hotkeys without single events and modifiers"""

        TempID2Key = self.ID2Key.copy()

        getRid = [
            91,
            92,
            160,
            161,
            162,
            163,
            164,
            165,
            1000,
            1004,
            1005,
            1010,
            1011,
            1012,
            1013,
        ]

        moreRid = [
            186,
            187,
            188,
            189,
            190,
            191,
            192,
            219,
            220,
            221,
            222,
        ]

        for item in moreRid:
            getRid.append(item)

        for gR in getRid:
            TempID2Key.pop(gR)

        LTempID2Key = list(TempID2Key.values())

        return LTempID2Key


def UniquePermutation2(l1, l2):
    """"Return UP of two lists"""

    ltemp = []
    for x1 in l1:
        for x2 in l2:
            ltemp.append([x1, x2])

    return ltemp


def UniquePermutation(li):
    """Return UP of a general list"""

    lcurrent = li[0]
    depth = 0
    for xl in li[1:]:
        lcurrenttemp = list()
        lcurrenttemp = UniquePermutation2(lcurrent, xl)

        if depth > 0:
            lcurrent = list()
            for item in lcurrenttemp:
                item0 = list(item[0])
                item0.append(item[1])
                lcurrent.append(item0)
        else:
            lcurrent = lcurrenttemp[:]
        depth += 1
    return lcurrent


class ExecFunThread:

    def __init__(self, fun):
        self.fun = fun

    def Start(self):
        self.running = True
        _thread.start_new_thread(self.Run, ())

    def IsRunning(self):
        return self.running

    def Run(self):
        self.fun()
        self.running = False


if __name__ == '__main__':

    import win32gui

    def funk1():
        print('Hotkey pressed: Lcontrol 7')

    def funM():
        print('Mousy')

    def funW():
        print('Wheel up')

    def funWin():
        print(win32gui.GetForegroundWindow())

    hot = pyhk()

    print(hot.getHotkeyListNoSingleNoModifiers())

    id1 = hot.addHotkey(['Ctrl', 'Alt', '7'], funk1)
    id2 = hot.addHotkey(['Ctrl', 'Alt', '7'], funk1)
    id3 = hot.addHotkey(['Ctrl', 'Alt', '7'], funk1)

    id4 = hot.addHotkey(['7'], funWin, up=True)

    hot.addHotkey(['mouse middle', '1'], funM)

    hot.addHotkey(['mouse wheel up'], funW, isThread=True)

    hot.addHotkey(['Ctrl', '8'], funk1)

    hot.removeHotkey(id=id4)

    hot.setEndHotkey(['Alt', 'Q'])

    hot.start()
