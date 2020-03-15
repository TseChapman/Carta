# Color palette; members in Red-Green-Blue (RGB) values
# (x, x, x), each x is 0-255, 255 = 2^8-1
class Colors:
    def __init__(self):
        self.white = (255, 255, 255)
        self.lightGreen = (193, 223, 192)
        self.black = (0, 0, 0)
        self.red = (255, 0, 0)
        self.blue = (0, 0, 255)
        self.yellow = (255, 255, 0)
        self.lightBlue = (4, 234, 250)
        self.green = (0, 255, 0)

class GUIParameters:  # const parameters
    def __init__(self):
        self.screenWidth = 1000
        self.screenHeight = 563  # 16:9 ratio
        self.FPS = 30  # upper bound per frames per second
        self.windowName = "Carta"
        self.fontFile = "fonts/ttf-bitstream-vera-1.10/Vera.ttf"
        self.JPFontFile = "fonts/ipaexg00401/ipaexg.ttf"
        self.cardWidth = 52
        self.cardHeight = 73
        self.wordBoxWidth = 270  # Width for wordBox from reading card
        self.wordBoxHeight = 200  # Height for wordBox from reading card
        self.numFrames = 72  # card frames (number of frames per row * self.numCardRows)
        self.frameThickness = 3
        self.horizontalSpacing = 1  # between two frames
        self.verticalSpacing = 10  # between two rows of frames
        self.extraVerticalSpacing = self.verticalSpacing * 2
        self.fontSize = 12
        self.wordFontSize = 24  # for reading card word font size
        self.buttonFontSize = 18
        self.dialogFontSize = 14
        self.numCardRows = 6
        self.leftMargin = 20  # for grabbing cards in the screen
        self.topMargin = 20  # for grabbing cards in the screen
        self.wordLeftMargin = 10  # Reading card word in the wordBox
        self.wordTopMargin = 85  # Reading card word in the wordBox
        self.infoScreenStartX = self.screenWidth * 7 // 10
        self.wordBoxStart = Point(720, 50)  # left top for wordBox from reading word
        self.stackStart = Point(720, 400)  # left top point for stack of grabbing cards
        self.maxNumLetters = 6  # maximum number of letters allowed in one row in a grabbing card
        self.leftCardMargin = 2  # for last word in a grabbing card
        self.topCardMargin = 1  # for last word in a grabbing card
        self.doneButtonStart = Point(720, 260)  # left top for "Done" button box
        self.buttonBoxWidth = 70  # Width for "Done" button box
        self.buttonBoxHeight = 40  # Height for "Done" button box
        self.leftTimeMargin = 5  # for time in info screen
        self.topTimeMargin = 5  # for time in info screen
        self.displayLatency = 500  # display one character in reading card every self.displayLatency ms
        self.dialogBoxStart = Point(800, 260)
        self.dialogBoxWidth = 190
        self.dialogBoxHeight = 290
        self.dialogLeftMargin = 5
        self.dialogTopMargin = 5
        self.dialogsSpacing = 14
        self.maxNumDialogRows = 21
        self.maxDialogChar = 25

# Carta Game Phase enum (in python 3, import enum as Enum)
# Phase order 1-2-3-4-5-1-2-3-4-5...... until one player has no cards --> 6
class Phase:
    INVALID = 0  # none of the states below
    RESET = 1  # reset the game to a new round
    OPPONENT_SET_UP = 2  # opoonent setting his/her cards in his/her field
    YOUR_SET_UP = 3  # you setting your cards in your field
    GRABBING = 4  # grabbing: compete between you and opponent
    OPPONENT_TRANSFER = 5  # opponent may give a card to you
    YOUR_TRANSFER = 6  # you may give a card to opponent
    END_GAME = 7

# Per player
class GrabPhaseStatus:
    NO_TOUCH = 0
    TRUE_TOUCH = 1
    FALSE_TOUCH = 2

class GrabPhaseInfo:
    def __init__(self):
        self.savedStartTime = False
        self.startTime = 0  # time of the grabbing phase's start
        self.yourGrabCardLastWord = ""
        self.yourTime = None  # time of pressing the grabbing card
        self.oppoGrabCardLastWord = ""
        self.opponentTime = None  # time of opponent pressing the grabbing card
        self.oppoResponded = False
        self.timesUp = False
        self.youWin = False
        self.opponentWin = False
        self.yourGrabCard = None
        self.oppoGrabCard = None
        self.correctGrabCard = None
        self.yourStatus = GrabPhaseStatus.NO_TOUCH
        self.oppoStatus = GrabPhaseStatus.NO_TOUCH
        # correct grabbing card not available,
        # on your side, or on opponent's side
        self.correctGrabCardStatus = GrabCardStatus.INVALID
        self.decisionWordAppearTime = 0
        self.decisionWordAppeared = False

    def reset(self):
        self.savedStartTime = False
        self.startTime = 0  # time of the grabbing phase's start
        self.yourGrabCardLastWord = ""
        self.yourTime = None  # time of pressing the grabbing card, relative time
        self.oppoGrabCardLastWord = ""
        self.opponentTime = None  # time of opponent pressing the grabbing card, relative time
        self.oppoResponded = False
        self.timesUp = False
        self.youWin = False
        self.opponentWin = False
        self.yourGrabCard = None
        self.oppoGrabCard = None
        self.correctGrabCard = None
        self.yourStatus = GrabPhaseStatus.NO_TOUCH
        self.oppoStatus = GrabPhaseStatus.NO_TOUCH
        # correct grabbing card not available,
        # on your side, or on opponent's side
        self.correctGrabCardStatus = GrabCardStatus.INVALID
        self.decisionWordAppearTime = 0
        self.decisionWordAppeared = False

class CartaParameters:  # constant parameters
    def __init__(self):
        self.opponentTimeForStupidAI = 10000  # ms
        self.maxGrabbingTime = 18000  # ms
        self.opponentSuccessProb = 0.8
        self.maxGrabbingRatio = 1.16
        self.cleverAIScale = 1.0
        self.maxNumDialogChar = 26

class Dialogs:
    def __init__(self, num):
        self.list = []  # queue
        self.maxNumChar = num

    def at(self, i):
        return self.list[i]

    def length(self):
        return len(self.list)

    def pop(self):
        self.list.pop(0)

    def append(self, s):
        stringList = s.split(' ')
        maxIndex = len(stringList) - 1
        wordIndex = 0
        endIndex = 0
        newLine = False
        while endIndex < maxIndex:
            numAppendedChars = 0
            oneLineText = ""
            if (newLine):
                endIndex += 1
                newLine = False
            while (numAppendedChars + len(stringList[wordIndex]) + 1 <= self.maxNumChar):
                numAppendedChars += len(stringList[wordIndex]) + 1
                if (wordIndex < maxIndex):
                    if (numAppendedChars + len(stringList[wordIndex + 1]) + 1 <= self.maxNumChar):
                        wordIndex += 1
                    else:
                        newLine = True
                        break
                else:
                    break
            oneLineText = ' '.join(stringList[endIndex:(wordIndex + 1)])
            endIndex = wordIndex
            self.list.append(oneLineText)