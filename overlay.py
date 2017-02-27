import wx
import os
import win32api
import win32con
import win32gui


class AppFrame(wx.Frame):

    def __init__(self, size=(300, 300), pos=(100, 100)):

        wx.Frame.__init__(self, None, title="Am I transparent?",
                          style=wx.SIMPLE_BORDER | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR)
        self.SetClientSize(size)
        self.SetPosition(pos)

        self.alphaValue = 220
        self.alphaIncrement = -4

        pnl = wx.Panel(self)
        # self.changeAlpha_timer = wx.Timer(self)
        # self.changeAlpha_timer.Start(50)
        # self.Bind(wx.EVT_TIMER, self.ChangeAlpha)
        self.MakeTransparent(self.alphaValue)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def ChangeAlpha(self, evt):
        self.alphaValue += self.alphaIncrement
        if (self.alphaValue) <= 170 or (self.alphaValue >= 220):
            # Reverse the increment direction.
            self.alphaIncrement = -self.alphaIncrement

            if self.alphaValue <= 170:
                self.alphaValue = 170

            if self.alphaValue > 220:
                self.alphaValue = 220

        self.MakeTransparent(self.alphaValue)

    def OnCloseWindow(self, evt):

        self.changeAlpha_timer.Stop()
        del self.changeAlpha_timer
        self.Destroy()

    def MakeTransparent(self, amount):
        if os.name == 'nt':  # could substitute: sys.platform == 'win32'
            hwnd = self.GetHandle()
            _winlib = win32api.LoadLibrary("user32")
            pSetLayeredWindowAttributes = win32api.GetProcAddress(
                _winlib, "SetLayeredWindowAttributes")
            if pSetLayeredWindowAttributes is None:
                return
            exstyle = win32api.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            if 0 == (exstyle & 0x80000):
                exstyle |= win32con.WS_EX_LAYERED | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TRANSPARENT
                win32api.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, exstyle)
            win32gui.SetLayeredWindowAttributes(hwnd, 0, amount, 2)
        else:
            print('####  OS Platform must be MS Windows')
            self.Destroy()


def main():
    import config

    app = wx.App()

    for screen in config.GRID:
        x1, y1, x2, y2 = screen
        w = x2 - x1
        h = y2 - y1
        # print screen, w, h
        frm = AppFrame(size=(w, h), pos=(x1, y1))
        frm.ShowWithoutActivating()

    app.MainLoop()


if __name__ == '__main__':
    main()
