# modified version of K0Stek on https://guidedhacking.com/threads/python-pygame-overlay-wrapper-for-any-game.17031/

import pygame
import win32api
import win32con
import win32gui
import win32file
import sys
import os
from enum import Enum

TRANSPARENT = (255, 0, 128)
NOSIZE = 1
NOMOVE = 2
TOPMOST = -1
NOT_TOPMOST = -2


class Color(Enum):

    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 128, 0)


class Vector:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def __ne__(self, other) -> bool:
        this = self.x + self.y + self.w + self.h
        _other = other.x + other.y + other.w + other.h
        return this != _other

    def data(self) -> list:
        return [self.x, self.y, self.w, self.h]


class Figure:
    def __init__(self, vector, color):
        self.vector = vector
        self.color = color


class Rectangle(Figure):
    def __init__(self, vector, color, hollow=False):
        self.type = "Rectangle"
        self.hollow = hollow
        super().__init__(vector, color)

    def draw(self, screen):
        if self.hollow:
            pygame.draw.rect(screen, self.color, self.vector.data(), 2)
        else:
            pygame.draw.rect(screen, self.color, self.vector.data())


class Circle(Figure):
    def __init__(self, vector, color, thickness, radius):
        self.type = "Circle"
        self.thickness = thickness
        self.radius = radius
        super().__init__(vector, color)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.vector.x,
                                                self.vector.y), self.radius, self.thickness)


class Line(Figure):
    def __init__(self, vector, color, thickness):  # x = x1, y = y1, w = x2, h = y2
        self.type = "Line"
        self.thickness = thickness
        super().__init__(vector, color)

    def draw(self, screen):
        pygame.draw.line(surface=screen, color=self.color, start_pos=(
            self.vector.x, self.vector.y), end_pos=(self.vector.w, self.vector.h), width=self.thickness)


class Text(Figure):
    def __init__(self, vector, color, text, fontObject):
        self.type = "Text"
        self.text = text
        self.fontObject = fontObject
        super().__init__(vector, color)

    def draw(self, screen):
        screen.blit(self.fontObject.render(self.text, 1, self.color),
                    (self.vector.x, self.vector.y))


class Overlay:
    def __init__(self, WindowTitle, refresh_rate):
        self.figuresToDraw = []
        self.WindowTitle = WindowTitle
        self.refresh_rate = refresh_rate
        self.has_drawn = False
        self.window = True

        # Get Target Window And Rect
        win32gui.EnumWindows(Overlay.ACCWindowFinderCallback, self)
        if self.targetHwnd == 0:
            sys.exit(f"Error while searching for {WindowTitle}")
        self.targetRect = self.GetTargetWindowRect()

        # Init Pygame
        os.environ['SDL_VIDEO_WINDOW_POS'] = str(
            self.targetRect.x) + "," + str(self.targetRect.y)
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.targetRect.w, self.targetRect.h), pygame.NOFRAME)
        self.hWnd = pygame.display.get_wm_info()['window']
        win32gui.SetWindowLong(self.hWnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(
            self.hWnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
        win32gui.SetLayeredWindowAttributes(
            self.hWnd, win32api.RGB(*TRANSPARENT), 0, win32con.LWA_COLORKEY)

        #win32gui.BringWindowToTop(self.hWnd)
        #win32gui.SetWindowPos(self.hWnd, TOPMOST, 0, 0, 0, 0, NOMOVE | NOSIZE)


    def GetTargetWindowRect(self) -> Vector:
        rect = win32gui.GetWindowRect(self.targetHwnd)
        ret = Vector(rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])
        ret = Vector((1920 - 1280) // 2, (1080 - 720) // 2, 1280, 720) # TODO hardcode centered 720p window for now
        return ret

    def IsTargetFocused(self) -> bool:
        if win32gui.GetForegroundWindow() == self.targetHwnd:
            return True
        return False

    def handle(self):

        if len(self.figuresToDraw) > 0 or self.has_drawn:
            win32gui.SetWindowPos(
                self.hWnd, TOPMOST, self.targetRect.x, self.targetRect.y, 0, 0, NOMOVE | NOSIZE)
            
            if self.targetRect != self.GetTargetWindowRect():
                self.targetRect = self.GetTargetWindowRect()
                win32gui.SetWindowPos(self.hWnd, TOPMOST, 0,
                                    0, 0, 0, NOMOVE | NOSIZE)
                win32gui.MoveWindow(self.hWnd, self.targetRect.x, self.targetRect.y,
                                    self.targetRect.w, self.targetRect.h, True)

            self.screen.fill(TRANSPARENT)
            if len(self.figuresToDraw) > 0:
                for figure in self.figuresToDraw:
                    figure.draw(self.screen)
                self.figuresToDraw[:] = []
                self.has_drawn = True
            else:
                self.has_drawn = False
    
            pygame.display.update()
        
        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.window = False
    
        pygame.time.Clock().tick(self.refresh_rate)

    def draw(self, figure: str, vector: Vector, color, thickness=None, radius=None, text=None, fontObject=None):
        if figure == "fillRect":
            self.figuresToDraw.append(Rectangle(vector, color))

        elif figure == "BorderRect":
            self.figuresToDraw.append(Rectangle(vector, color, True))

        elif figure == "Circle":
            self.figuresToDraw.append(Circle(vector, color, thickness, radius))

        elif figure == "Line":
            self.figuresToDraw.append(Line(vector, color, thickness))

        elif figure == "Text":
            self.figuresToDraw.append(Text(vector, color, text, fontObject))


    def CreateFont(self, fontName, fontSize, bold=False, italic=False):
        return pygame.font.SysFont(name=fontName, size=fontSize, bold=bold, italic=italic)


    @staticmethod
    def ACCWindowFinderCallback(hwnd, obj) -> bool:
        """Since win32gui.FindWindow(None, 'AC2') doesn't work since kunos are a bunch of pepega and the title is 'AC2   '... """
        
        title = win32gui.GetWindowText(hwnd)
        if title.find("AC2") != -1:
            obj.targetHwnd = hwnd

        return True
