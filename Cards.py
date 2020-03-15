import pygame  # for grabbing card rect, frame rect for rendering

class ReadingCard:
    def __init__(self, firstWord, lastWord):
        self.firstWord = firstWord
        self.lastWord = lastWord
        self.index = -1
        self.fullWord = firstWord + " " + lastWord
        self.decisionWord = None

    def setIndex(self, i):
        self.index = i

    def setDecisionWord(self, word):
        self.decisionWord = word

    def getFirstWord(self):
        return self.firstWord

    def getLastWord(self):
        return self.lastWord

    def getFullWord(self):
        return self.fullWord

    def getIndex(self):
        return self.index

    def getDecisionWord(self):
        return self.decisionWord

class PureGrabbingCard:
    def __init__(self, lastWord):
        self.lastWord = lastWord
        self.decisionWord = None
        self.index = -1

    def setDecisionWord(self, word):
        self.decisionWord = word

    def setIndex(self, i):
        self.index = i

    def getDecisionWord(self):
        return self.decisionWord

    def getLastWord(self):
        return self.lastWord

    def sameLastWord(self, grabbingCard):
        if (grabbingCard is not None):
            return (self.lastWord == grabbingCard.getLastWord())
        else:
            return False

# Card in your field, opponent's field, or none of the above
class GrabCardStatus:
    INVALID = 0  # none of the below
    YOU = 1  # in your field
    OPPONENT = 2  # in opponent's field

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class GrabbingCard(PureGrabbingCard):
    def __init__(self, lastWord):
        PureGrabbingCard.__init__(self, lastWord)
        self.rect = None  # the pygame rectangle for rendering
        self.color = None
        self.status = GrabCardStatus.INVALID
        self.frame = None

    def setRect(self, rect):
        self.rect = rect

    def setColor(self, color):
        self.color = color

    def setStatus(self, status):
        self.status = status

    def setFrame(self, frame):
        self.frame = frame

    def setRectX(self, x):
        self.rect.x = x

    def setRectY(self, y):
        self.rect.y = y

    def getRect(self):
        return self.rect

    def getColor(self):
        return self.color

    def getStatus(self):
        return self.status

    def getFrame(self):
        return self.frame

    def getRectX(self):
        return self.rect.x

    def getRectY(self):
        return self.rect.y

    def getPos(self):
        return Point(self.rect.x, self.rect.y)
