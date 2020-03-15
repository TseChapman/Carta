# -*- coding: utf-8 -*-
import sys

if sys.version_info[0] < 3:
    execfile("Cards.py")
    execfile("CardAnalysis.py")
    execfile("CardStack.py")
    execfile("CartaUtils.py")
else:
    exec (open("Cards.py").read())
    exec (open("CardAnalysis.py").read())
    exec (open("CardStack.py").read())
    exec (open("CartaUtils.py").read())

class Carta:
    def __init__(self, debugMode, inJapanese):
        self.initGame(debugMode)
        self.initRendering(inJapanese)
        self.initReadingCards()
        self.initCardFrames()
        self.initGrabbingCards()

        self.clock = pygame.time.Clock()
        self.running = True  # track if the game is running

    def initGame(self, debugMode):
        pygame.init()
        self.GPInfo = GrabPhaseInfo()
        self.parameters = CartaParameters()
        self.phase = Phase.OPPONENT_SET_UP
        self.debugMode = debugMode

        self.usedGrabbingCards = CardStack([])  # grabbed grabbing card
        self.usedReadingCards = CardStack([])  # read reading card

        self.displayReadCardStartTime = 0

        self.yourGrabCardsAssigned = False

        self.numCardsToTransfer = 0

    def initRendering(self, inJapanese):
        self.colors = Colors()
        self.inJapanese = inJapanese
        self.GUIPars = GUIParameters()
        self.screen = pygame.display.set_mode((self.GUIPars.screenWidth, self.GUIPars.screenHeight))
        pygame.display.set_caption(self.GUIPars.windowName)

        pygame.font.init()
        # for grabbing card word
        self.font = pygame.font.Font(self.GUIPars.fontFile, self.GUIPars.fontSize)
        # for reading card word
        self.wordFont = pygame.font.Font(self.GUIPars.fontFile, self.GUIPars.wordFontSize)
        # for words in dialog box
        self.dialogFont = pygame.font.Font(self.GUIPars.fontFile, self.GUIPars.dialogFontSize)
        # for "Done" button word
        self.doneFont = pygame.font.Font(self.GUIPars.fontFile, self.GUIPars.buttonFontSize)
        if (self.inJapanese):
            self.doneFont = pygame.font.Font(self.GUIPars.JPFontFile, self.GUIPars.buttonFontSize)

        self.infoScreen = pygame.rect.Rect(self.GUIPars.infoScreenStartX, 0,
                                           self.GUIPars.screenWidth - self.GUIPars.infoScreenStartX,
                                           self.GUIPars.screenHeight)

        self.dialogBox = pygame.rect.Rect(self.GUIPars.dialogBoxStart.x, self.GUIPars.dialogBoxStart.y,
                                          self.GUIPars.dialogBoxWidth, self.GUIPars.dialogBoxHeight)

        self.doneButton = pygame.rect.Rect(self.GUIPars.doneButtonStart.x, self.GUIPars.doneButtonStart.y,
                                           self.GUIPars.buttonBoxWidth, self.GUIPars.buttonBoxHeight)

        self.dialogs = Dialogs(self.parameters.maxNumDialogChar)  # a queue for dialogs

        self.displayReadingCard = False  # True if to display reading card
        self.printOppoGrabTime = False  # True if printed Opponent Relative Grabbing Time

    def initReadingCards(self):
        # Shuffle and put 50 cards into the readingCardStack
        self.readingCardStack = CardStack(READING_CARDS)
        self.readingCardStack.shuffle()
        self.readingCardBox = pygame.rect.Rect(self.GUIPars.wordBoxStart.x, self.GUIPars.wordBoxStart.y,
                                               self.GUIPars.wordBoxWidth, self.GUIPars.wordBoxHeight)

        # About the current reading card in play
        self.curReadingCard = None
        self.numReadCardChars = 0  # display reading card word up to this number

    def createCardFrame(self, lt):
        rb = Point(lt.x + self.GUIPars.cardWidth, lt.y + self.GUIPars.cardHeight)
        return [(lt.x, lt.y), (lt.x, rb.y), (rb.x, rb.y), (rb.x, lt.y)]

    def setFramesInARow(self, stepX, start, frames):  # start and frames will be modified
        for k in range(self.GUIPars.numFrames // self.GUIPars.numCardRows):
            cardFrameLeftTop = Point(start.x + k * stepX, start.y)
            frames.append(self.createCardFrame(cardFrameLeftTop))
        start.y += self.GUIPars.cardHeight + \
                   self.GUIPars.verticalSpacing

    def initCardFrames(self):
        self.opponentFrames = []
        self.yourFrames = []

        start = Point(self.GUIPars.leftMargin, self.GUIPars.topMargin)
        stepX = self.GUIPars.cardWidth + self.GUIPars.horizontalSpacing
        for i in range(self.GUIPars.numCardRows // 2):
            self.setFramesInARow(stepX, start, self.opponentFrames)

        start.y += self.GUIPars.extraVerticalSpacing  # separation between yours and opponent

        for i in range(self.GUIPars.numCardRows // 2, self.GUIPars.numCardRows):
            self.setFramesInARow(stepX, start, self.yourFrames)

        self.occupied = {}
        for frame in self.yourFrames:
            # Note frame is a list which is not hashable, need to convert to tuple
            # which is immutable and then hashable
            self.occupied[tuple(frame)] = False

        self.numYourFramesOccupied = 0

        for frame in self.opponentFrames:
            self.occupied[tuple(frame)] = False

    def initGrabbingCards(self):
        grabbingCardStack = CardStack(GRABBING_CARDS)
        grabbingCardStack.shuffle()
        halfStack = grabbingCardStack.draw(len(GRABBING_CARDS) // 2)

        # constant variables, will not change at run time
        self.yourGrabbingCards = [halfStack[i] for i in range(0, len(halfStack), 2)]
        self.opponentGrabbingCards = [halfStack[i] for i in range(1, len(halfStack), 2)]

        # change at run time. If one of below becomes zero, the corresponding player wins.
        self.numYourGrabCardInPlay = len(self.yourGrabbingCards)
        self.numOppoGrabCardInPlay = len(self.opponentGrabbingCards)

        # First handle your grabbing cards, then opponents
        # Your cards start at the card stack on the right of screen
        for i in range(len(self.yourGrabbingCards)):
            pygameRect = pygame.rect.Rect(self.GUIPars.stackStart.x, self.GUIPars.stackStart.y, self.GUIPars.cardWidth,
                                          self.GUIPars.cardHeight)
            self.yourGrabbingCards[i].setRect(pygameRect)
            self.yourGrabbingCards[i].setColor(self.colors.white)
            self.yourGrabbingCards[i].setStatus(GrabCardStatus.YOU)

        if (self.phase == Phase.OPPONENT_SET_UP):
            # Opponent cards start at their designated positions
            # For now, assume they are randomly placed
            frameIndexList = [k for k in range(len(self.opponentFrames))]
            # sample len(self.opponentGrabbingCards) indices from len(self.opponentFrames) frames
            random.seed(time.time())
            sampledFrames = random.sample(frameIndexList, self.numOppoGrabCardInPlay)

            for i in range(self.numOppoGrabCardInPlay):
                frame = self.opponentFrames[sampledFrames[i]]
                pygameRect = pygame.rect.Rect(frame[0][0], \
                                              frame[0][1], \
                                              self.GUIPars.cardWidth, \
                                              self.GUIPars.cardHeight)
                card = self.opponentGrabbingCards[i]
                card.setRect(pygameRect)
                card.setColor(self.colors.white)
                card.setStatus(GrabCardStatus.OPPONENT)
                card.setFrame(frame)
                self.occupied[tuple(frame)] = True

            self.phase = Phase.YOUR_SET_UP
            self.dialogs.append("Your Set Up Phase Starts.")

        # change at run time
        self.grabbingCardsInPlay = self.yourGrabbingCards + self.opponentGrabbingCards

        self.cardDragging = False
        self.touchYourCard = False

    # Reset variables before a new round starts
    def reset(self):
        if self.phase is Phase.RESET:
            self.GPInfo.reset()
            self.displayReadingCard = False
            self.printOppoGrabTime = False
            self.displayReadCardStartTime = 0
            self.curReadingCard = None
            self.numReadCardChars = 0
            self.cardDragging = False
            self.touchYourCard = False
            self.numCardsToTransfer = 0

            self.phase = Phase.YOUR_SET_UP
            self.dialogs.append("Your Set Up Phase Starts.")

    # 0 ms --> pygame.init(). Get current time relative to pygame.init().
    def getTime_ms(self):
        return pygame.time.get_ticks()

    # return integer time
    def getIntTime_s(self):
        return int(round(self.getTime_ms() / 1000))

    # pos is the position of left top corner of a card
    def findNearestFrame(self, pos):
        minDistanceSq = sys.float_info.max
        nearestFrame = None
        # for loop over your frames (not all frames)
        # note: as long as self.yourFrames has no None, this function must return no None
        for frame in self.yourFrames:
            if not self.occupied[tuple(frame)]:
                distSq = (frame[0][0] - pos.x)**2 + (frame[0][1] - pos.y)**2
                if (distSq < minDistanceSq):
                    minDistanceSq = distSq
                    nearestFrame = frame
        return nearestFrame

    def fillScreens(self):
        self.screen.fill(self.colors.lightGreen)
        pygame.draw.rect(self.screen, self.colors.lightBlue, self.infoScreen)

    def renderTime(self):
        timeString = str(self.getIntTime_s())  # in seconds
        timeSurface = self.wordFont.render(timeString, False, self.colors.black)
        self.screen.blit(
            timeSurface,
            (self.infoScreen.x + self.GUIPars.leftTimeMargin, self.infoScreen.y + self.GUIPars.topTimeMargin))

    def renderCardFrames(self):
        for frame in self.opponentFrames:
            pygame.draw.lines(self.screen, self.colors.red, True, frame, self.GUIPars.frameThickness)
        for frame in self.yourFrames:
            pygame.draw.lines(self.screen, self.colors.blue, True, frame, self.GUIPars.frameThickness)

    def renderDialogBox(self):
        pygame.draw.rect(self.screen, self.colors.white, self.dialogBox)
        if (self.dialogs.length() > 0):
            while (self.dialogs.length() >= self.GUIPars.maxNumDialogRows):
                self.dialogs.pop()
            for i in range(self.dialogs.length()):
                textsurface = self.dialogFont.render(self.dialogs.at(i), False, self.colors.black)
                self.screen.blit(textsurface,
                                 (self.dialogBox.x + self.GUIPars.dialogLeftMargin,
                                  self.dialogBox.y + self.GUIPars.dialogTopMargin + (i * self.GUIPars.dialogsSpacing)))

    def renderSingleCardAndWord(self, card):
        if (card is None) or (card.getStatus() is GrabCardStatus.INVALID):
            return
        # Draw the rectangle of the grabbing card
        pygame.draw.rect(self.screen, card.getColor(), card.getRect())

        lastWord = card.getLastWord()
        numRenderedChars = 0
        numLines = 0
        while numRenderedChars < len(lastWord):
            text = lastWord[numRenderedChars:numRenderedChars + self.GUIPars.maxNumLetters]
            textsurface = self.font.render(text, False, self.colors.black)
            textWidth, textHeight = textsurface.get_size()

            leftTopPos = (card.getRectX() + self.GUIPars.leftCardMargin,
                          card.getRectY() + self.GUIPars.topCardMargin + numLines * textHeight)

            if (card.getStatus() is GrabCardStatus.OPPONENT):
                textsurface = pygame.transform.rotate(textsurface, 180)
                leftTopPos = (card.getRectX() + self.GUIPars.cardWidth -
                              self.GUIPars.leftCardMargin - textWidth, \
                              card.getRectY() + self.GUIPars.cardHeight -
                              self.GUIPars.topCardMargin - (numLines + 1) * textHeight)

            self.screen.blit(textsurface, leftTopPos)
            numRenderedChars += self.GUIPars.maxNumLetters
            numLines += 1

    def renderGrabbingCardsAndWords(self, selectedCard):
        # Render cards and write last words on the cards
        # First render the not selected cards
        for i in range(len(self.grabbingCardsInPlay) - 1, -1, -1):
            grabbingCard = self.grabbingCardsInPlay[i]
            if (selectedCard is None):
                self.renderSingleCardAndWord(grabbingCard)
            elif (grabbingCard.sameLastWord(selectedCard) is False):
                self.renderSingleCardAndWord(grabbingCard)

        # Render the selected card, to make sure it is always
        # rendered on top
        self.renderSingleCardAndWord(selectedCard)

    def renderReadingCardWords(self):
        # Render first and last words on empty space on the right of screen
        pygame.draw.rect(self.screen, self.colors.black, self.readingCardBox)
        if (self.curReadingCard is None):
            return

        displayOneMoreChar = (self.displayReadCardStartTime +
                              (self.numReadCardChars + 1) * self.GUIPars.displayLatency < self.getTime_ms())

        if (self.numReadCardChars < len(self.curReadingCard.getFullWord()) and \
            displayOneMoreChar):
            self.numReadCardChars += 1

        if (self.curReadingCard.getFullWord()[:self.numReadCardChars] == self.curReadingCard.getDecisionWord()) and (
                self.GPInfo.decisionWordAppeared is False):  # For clever AI
            self.GPInfo.decisionWordAppearTime = self.getTime_ms() - self.GPInfo.startTime
            self.GPInfo.decisionWordAppeared = True

        textsurface = self.wordFont.render(self.curReadingCard.getFullWord()[:self.numReadCardChars], False,
                                           self.colors.white)

        self.screen.blit(
            textsurface,
            (self.readingCardBox.x + self.GUIPars.wordLeftMargin, self.readingCardBox.y + self.GUIPars.wordTopMargin))

    def renderDoneButton(self):
        pygame.draw.rect(self.screen, self.colors.green, self.doneButton)
        text = "Done"
        if (self.inJapanese):
            text = u"確認"
            text = text.encode("utf-8").decode("utf-8")
        textsurface = self.doneFont.render(text, False, self.colors.black)
        width, height = textsurface.get_size()
        self.screen.blit(textsurface, \
                         (self.doneButton.x + (self.GUIPars.buttonBoxWidth - width) // 2, \
                          self.doneButton.y + (self.GUIPars.buttonBoxHeight - height) // 2))

    # Check if the time between start time and current time at least self.parameters.maxGrabbingTime
    def checkTimesUp(self):
        if ((self.getTime_ms() - self.GPInfo.startTime >= self.parameters.maxGrabbingTime) and \
            (self.GPInfo.timesUp is False)):
            self.GPInfo.timesUp = True

    def hasReachedOpponentGrabTime(self):
        return (self.getTime_ms() - self.GPInfo.startTime >= self.GPInfo.opponentTime)

    # Save the starting time of the grabbing phase
    def saveGrabPhaseStartTime_ms(self):
        self.GPInfo.startTime = self.getTime_ms()
        self.GPInfo.savedStartTime = True

    # Save the time where you grab a card
    def saveYourGrabTime_ms(self):
        self.GPInfo.yourTime = self.getTime_ms() - self.GPInfo.startTime
        if (self.debugMode):
            self.dialogs.append("Debug: You Grab at %.f ms." % (self.GPInfo.yourTime))

    def decideCorrectGrabCardStatus(self):
        for card in self.grabbingCardsInPlay:
            if (card.getLastWord() == self.curReadingCard.getLastWord()):
                self.GPInfo.correctGrabCardStatus = card.getStatus()
                self.GPInfo.correctGrabCard = card
                if (self.debugMode):
                    card.setColor(self.colors.red)

    def decideOpponentTakingCorrectCardAndGrabbingTime(self):
        oppoTakesCorrectCard = self.opponentTakesCorrectGrabCard()
        if (not oppoTakesCorrectCard):
            random.seed(time.time())
            p = random.uniform(0, 1)
            self.GPInfo.opponentTime = self.parameters.maxGrabbingTime * p
        return oppoTakesCorrectCard

    # returns true if and only if
    # 1) the correct grabbing card is on the opposite side of the touched grabbing card; OR
    # 2) correct grabbing card not in play but the touched card is in play
    def isFalseTouch(self, correctCardStatus, touchedCardStatus):
        return ((correctCardStatus is GrabCardStatus.YOU and touchedCardStatus is GrabCardStatus.OPPONENT)
                or (correctCardStatus is GrabCardStatus.OPPONENT and touchedCardStatus is GrabCardStatus.YOU)
                or (correctCardStatus is GrabCardStatus.INVALID and touchedCardStatus is not GrabCardStatus.INVALID))

    def decideTouchedCardStatus(self, touchedCard):
        status = GrabPhaseStatus.NO_TOUCH
        if ((touchedCard is not None) and (self.curReadingCard is not None)):
            if (touchedCard.getLastWord() == self.curReadingCard.getLastWord()):
                status = GrabPhaseStatus.TRUE_TOUCH
            elif self.isFalseTouch(self.GPInfo.correctGrabCardStatus, touchedCard.getStatus()):
                status = GrabPhaseStatus.FALSE_TOUCH
        return status

    # Save the grabbing card that you selected
    def saveYourGrabbingCard(self, yourGrabbingCard):
        if ((self.GPInfo.yourGrabCard is None) and (yourGrabbingCard is not None)):
            status = self.decideTouchedCardStatus(yourGrabbingCard)
            if (status is not GrabPhaseStatus.NO_TOUCH):
                self.GPInfo.yourGrabCardLastWord = yourGrabbingCard.getLastWord()
                self.GPInfo.yourGrabCard = yourGrabbingCard
                self.GPInfo.yourStatus = status
                self.saveYourGrabTime_ms()

    def hasSomeoneTouched(self):
        return ((self.GPInfo.yourStatus is not GrabPhaseStatus.NO_TOUCH) or \
                (self.GPInfo.oppoStatus is not GrabPhaseStatus.NO_TOUCH))

    def opponentTakesCorrectGrabCard(self):
        random.seed(time.time())
        x = random.uniform(0, 1)
        return (x <= self.parameters.opponentSuccessProb)

    # Clever AI
    # Note: opponent will not take a wrong card on the same side as the correct card.
    def opponentRespondsInGrabPhase(self, oppoTakesCorrectCard):
        for card in self.grabbingCardsInPlay:
            if ((card.getLastWord() == self.curReadingCard.getLastWord()) and \
                (oppoTakesCorrectCard)):
                self.GPInfo.oppoGrabCardLastWord = card.getLastWord()
                self.GPInfo.oppoGrabCard = card
                self.GPInfo.oppoStatus = GrabPhaseStatus.TRUE_TOUCH
                break
            elif ((card.getLastWord() != self.curReadingCard.getLastWord()) and \
                  (not oppoTakesCorrectCard) and \
                  self.isFalseTouch(self.GPInfo.correctGrabCardStatus, card.getStatus())):
                self.GPInfo.oppoGrabCardLastWord = card.getLastWord()
                self.GPInfo.oppoGrabCard = card
                self.GPInfo.oppoStatus = GrabPhaseStatus.FALSE_TOUCH
                break

        self.GPInfo.oppoResponded = True

        if (self.GPInfo.oppoGrabCard is not None) and (oppoTakesCorrectCard):
            self.GPInfo.opponentTime = min(self.parameters.cleverAIScale * self.GPInfo.decisionWordAppearTime,
                                           self.parameters.maxGrabbingTime)
        elif (self.GPInfo.oppoGrabCard is None):
            self.GPInfo.opponentTime = self.parameters.maxGrabbingTime

        if ((self.printOppoGrabTime is False) and (self.debugMode)):
            self.dialogs.append("Debug: Dec'n word: " + self.curReadingCard.getDecisionWord() + ".")
            self.dialogs.append("Debug: Opponent grabs at %.f ms." % (self.GPInfo.opponentTime))
            self.printOppoGrabTime = True

        if (self.debugMode):
            if (self.GPInfo.oppoStatus is GrabPhaseStatus.TRUE_TOUCH):
                print("Carta.py: opponentRespondsInGrabPhase: opponent takes correct card #%s#" \
                      % self.GPInfo.oppoGrabCardLastWord)
            elif (self.GPInfo.oppoStatus is GrabPhaseStatus.FALSE_TOUCH):
                if (self.GPInfo.correctGrabCardStatus is GrabCardStatus.INVALID):
                    print("Carta.py: opponentRespondsInGrabPhase: opponent takes wrong card #%s#, right card N/A" \
                          % self.GPInfo.oppoGrabCardLastWord)
                else:
                    print("Carta.py: opponentRespondsInGrabPhase: opponent takes wrong card #%s#, right card available" \
                          % self.GPInfo.oppoGrabCardLastWord)
            else:
                print("Carta.py: opponentRespondsInGrabPhase: opponent does not touch any card")

    def removeCorrectGrabbingCard(self):
        if (self.GPInfo.correctGrabCard is not None):
            self.occupied[tuple(self.GPInfo.correctGrabCard.getFrame())] = False
            self.GPInfo.correctGrabCard.setFrame(None)
            self.GPInfo.correctGrabCard.setRect(None)
            if (self.GPInfo.correctGrabCard.getStatus() is GrabCardStatus.YOU):
                self.numYourFramesOccupied -= 1
            self.GPInfo.correctGrabCard.setStatus(GrabCardStatus.INVALID)
            self.usedGrabbingCards.cards.append(self.GPInfo.correctGrabCard)
            self.grabbingCardsInPlay.remove(self.GPInfo.correctGrabCard)

    def shouldOpponentTransfer(self, yourFalseTouch):
        if (self.GPInfo.oppoGrabCard.getStatus() == GrabCardStatus.YOU):
            self.phase = Phase.OPPONENT_TRANSFER
            self.numCardsToTransfer += 1
            self.numOppoGrabCardInPlay -= 1
        elif (self.GPInfo.oppoGrabCard.getStatus() == GrabCardStatus.OPPONENT):
            self.numOppoGrabCardInPlay -= 1

        if (yourFalseTouch):
            self.numCardsToTransfer += 1
            self.numOppoGrabCardInPlay -= 1
            self.numYourGrabCardInPlay += 1
            self.phase = Phase.OPPONENT_TRANSFER

    def shouldYouTransfer(self, oppoFalseTouch):
        if (self.GPInfo.yourGrabCard.getStatus() == GrabCardStatus.YOU):
            self.numYourGrabCardInPlay -= 1
        elif (self.GPInfo.yourGrabCard.getStatus() == GrabCardStatus.OPPONENT):
            self.phase = Phase.YOUR_TRANSFER
            self.numCardsToTransfer += 1
            self.numYourGrabCardInPlay -= 1

        if (oppoFalseTouch):
            self.numCardsToTransfer += 1
            self.numOppoGrabCardInPlay += 1
            self.numYourGrabCardInPlay -= 1
            self.phase = Phase.YOUR_TRANSFER

    def appendDialogsWhenDecidingWinner(self):
        if ((self.GPInfo.youWin) and not (self.GPInfo.opponentWin)):
            self.dialogs.append("You Win, Opponent Loses.")
        elif (not (self.GPInfo.youWin) and (self.GPInfo.opponentWin)):
            self.dialogs.append("Opponent Wins, You Lose.")
        elif ((self.GPInfo.youWin) and (self.GPInfo.opponentWin)):
            self.dialogs.append("Both Players Win.")
        elif (not (self.GPInfo.youWin) and not (self.GPInfo.opponentWin)):
            self.dialogs.append("No one Wins.")

        if (self.phase == Phase.YOUR_TRANSFER):
            self.dialogs.append("Your Transfer Starts.")
            if (self.numCardsToTransfer > 1):
                self.dialogs.append("You give " + str(self.numCardsToTransfer) + " cards to opponent.")
            else:
                self.dialogs.append("You give " + str(self.numCardsToTransfer) + " card to opponent.")
        elif (self.phase == Phase.OPPONENT_TRANSFER):
            self.dialogs.append("Opponent Transfer Starts.")
            if (self.numCardsToTransfer > 1):
                self.dialogs.append("Opponent gives " + str(self.numCardsToTransfer) + " cards to you.")
            else:
                self.dialogs.append("Opponent gives " + str(self.numCardsToTransfer) + " card to you.")
        elif (self.phase == Phase.END_GAME):
            self.dialogs.append("Game Ends.")

    def decideWinner(self):
        self.phase = Phase.RESET
        statement = ""
        yourTrueTouch = (self.GPInfo.yourStatus is GrabPhaseStatus.TRUE_TOUCH)
        yourFalseTouch = (self.GPInfo.yourStatus is GrabPhaseStatus.FALSE_TOUCH)
        yourNoTouch = (self.GPInfo.yourStatus is GrabPhaseStatus.NO_TOUCH)
        oppoTrueTouch = (self.GPInfo.oppoStatus is GrabPhaseStatus.TRUE_TOUCH)
        oppoFalseTouch = (self.GPInfo.oppoStatus is GrabPhaseStatus.FALSE_TOUCH)
        oppoNoTouch = (self.GPInfo.oppoStatus is GrabPhaseStatus.NO_TOUCH)

        if (yourTrueTouch or oppoTrueTouch):
            if (yourTrueTouch and oppoTrueTouch):
                if (self.GPInfo.yourTime < self.GPInfo.opponentTime):
                    self.GPInfo.youWin = True
                    statement = "Carta.py: decideWinner: Both players grabbed the right card, but you grabbed it faster than opponent"
                elif (self.GPInfo.yourTime > self.GPInfo.opponentTime):
                    self.GPInfo.youWin = False
                    statement = "Carta.py: decideWinner: Both players grabbed the right card, but opponent grabbed it faster than you"
                else:
                    random.seed(time.time())
                    x = random.randint(0, 1)
                    if (x > 0):
                        self.GPInfo.youWin = True
                        statement = "Carta.py: decideWinner: Both players grabbed the right card at the same time, but luck favors you"
                    else:
                        self.GPInfo.youWin = False
                        statement = "Carta.py: decideWinner: Both players grabbed the right card at the same time, but luck favors opponent"
            elif (yourTrueTouch and oppoNoTouch):
                self.GPInfo.youWin = True
                statement = "Carta.py: decideWinner: Available GrabCard, you grabbed the card, opponent didn't"
            elif (oppoTrueTouch and yourNoTouch):
                self.GPInfo.youWin = False
                statement = "Carta.py: decideWinner: Available GrabCard, opponent grabbed the card, you didn't"
            elif (yourTrueTouch and oppoFalseTouch):
                self.GPInfo.youWin = True
                statement = "Carta.py: decideWinner: you grabbed the right card, but opponent didn't grab the right card"
            else:  # oppo true touch and your false touch
                self.GPInfo.youWin = False
                statement = "Carta.py: decideWinner: you grabbed the wrong card, but opponent grabbed the right card"

            if (self.GPInfo.youWin):
                self.GPInfo.opponentWin = False
                self.shouldYouTransfer(oppoFalseTouch)
            else:
                self.GPInfo.opponentWin = True
                self.shouldOpponentTransfer(yourFalseTouch)

        elif (self.GPInfo.correctGrabCardStatus is GrabCardStatus.INVALID):
            if (yourNoTouch and oppoNoTouch):
                self.GPInfo.youWin = True
                self.GPInfo.opponentWin = True
                statement = "Carta.py: decideWinner: No available GrabCard, both players win"
            elif (yourFalseTouch and oppoNoTouch):
                self.GPInfo.youWin = False
                self.GPInfo.opponentWin = True
                statement = "Carta.py: decideWinner: No available GrabCard, opponent win"
                self.phase = Phase.OPPONENT_TRANSFER
                self.numCardsToTransfer += 1
                self.numYourGrabCardInPlay += 1
                self.numOppoGrabCardInPlay -= 1
            elif (yourNoTouch and oppoFalseTouch):
                self.GPInfo.youWin = True
                self.GPInfo.opponentWin = False
                statement = "Carta.py: decideWinner: No available GrabCard, you win"
                self.phase = Phase.YOUR_TRANSFER
                self.numCardsToTransfer += 1
                self.numYourGrabCardInPlay -= 1
                self.numOppoGrabCardInPlay += 1

        elif (self.GPInfo.correctGrabCardStatus is not GrabCardStatus.INVALID):
            if (yourFalseTouch and oppoNoTouch):
                self.GPInfo.youWin = False
                self.GPInfo.opponentWin = True
                statement = "Carta.py: decideWinner: Available GrabCard, you grabbed the wrong card, opponent wins"
                if (self.GPInfo.correctGrabCardStatus is GrabCardStatus.YOU):
                    self.numOppoGrabCardInPlay -= 1
                else:  # correct card in your's
                    self.numOppoGrabCardInPlay -= 2
                    self.numYourGrabCardInPlay += 1
                self.phase = Phase.OPPONENT_TRANSFER
                self.numCardsToTransfer += 1
            elif (yourNoTouch and oppoFalseTouch):
                self.GPInfo.youWin = True
                self.GPInfo.opponentWin = False
                statement = "Carta.py: decideWinner: Available GrabCard, opponent grabbed the wrong card, you win"
                if (self.GPInfo.correctGrabCardStatus is GrabCardStatus.YOU):
                    self.numYourGrabCardInPlay -= 2
                    self.numOppoGrabCardInPlay += 1
                else:  # correct card in opponent's
                    self.numYourGrabCardInPlay -= 1
                self.phase = Phase.YOUR_TRANSFER
                self.numCardsToTransfer += 1

        else:
            self.GPInfo.youWin = False
            self.GPInfo.opponentWin = False
            statement = "Carta.py: decideWinner: Both players grab wrong card"

        if ((self.numYourGrabCardInPlay == 0) or (self.numOppoGrabCardInPlay == 0)):
            self.phase = Phase.END_GAME

        self.appendDialogsWhenDecidingWinner()
        self.usedReadingCards.cards.append(self.curReadingCard)
        self.removeCorrectGrabbingCard()

        if (self.debugMode):
            print(statement)
            print("-------------------------------------------------")

    # Stupid transfer
    def opponentTransfers(self):
        while (self.numCardsToTransfer != 0):
            random.seed(time.time())
            x = random.randint(0, self.numOppoGrabCardInPlay - 1)
            for card in self.grabbingCardsInPlay:
                if (card.getLastWord() == self.grabbingCardsInPlay[self.numYourGrabCardInPlay + x].getLastWord()):
                    pygameRect = pygame.rect.Rect(self.GUIPars.stackStart.x, self.GUIPars.stackStart.y,
                                                  self.GUIPars.cardWidth, self.GUIPars.cardHeight)
                    card.setRect(pygameRect)
                    card.setFrame(None)
                    card.setStatus(GrabCardStatus.YOU)
                    self.numCardsToTransfer -= 1
                    if (self.debugMode):
                        print("Carta.py: opponentTransfers: Opponent gives #%s# to you" % card.getLastWord())
                    break
        self.phase = Phase.RESET

    # return selectedCard if any
    def selectCard(self, event, mouse, offset):
        selectedCard = None
        # self.grabbingCardsInPLay cannot contain or include None
        for card in self.grabbingCardsInPlay:
            # If mouse click is on self.grabbingCardsInPlay[j].getRect()
            if card.getRect().collidepoint(event.pos):
                self.cardDragging = (self.phase == Phase.YOUR_SET_UP)
                mouse.x, mouse.y = event.pos
                selectedCard = card
                self.touchYourCard = (selectedCard.getStatus() is GrabCardStatus.YOU)
                offset.x = selectedCard.getRectX() - mouse.x
                offset.y = selectedCard.getRectY() - mouse.y
                if (selectedCard.getColor() is self.colors.white):
                    selectedCard.setColor(self.colors.yellow)
                    if ((self.phase == Phase.YOUR_TRANSFER) and (self.touchYourCard)):
                        self.numCardsToTransfer -= 1
                elif (selectedCard.getColor() is self.colors.yellow):
                    selectedCard.setColor(self.colors.white)
                    if ((self.phase == Phase.YOUR_TRANSFER) and (self.touchYourCard)):
                        self.numCardsToTransfer += 1
                if ((selectedCard.getFrame() is not None) and \
                    self.touchYourCard and \
                    self.cardDragging):
                    # self.occupied is only about your side.
                    self.occupied[tuple(selectedCard.getFrame())] = False
                    self.numYourFramesOccupied -= 1
                break
        return selectedCard

    # only run at initialization
    def randomAssignYourGrabCards(self):
        frameIndexList = [k for k in range(len(self.yourFrames))]

        # self.numYourGrabCardInPlay indices from len(self.yourFrames) frames
        random.seed(time.time())
        sampledFrames = random.sample(frameIndexList, self.numYourGrabCardInPlay)

        for i in range(self.numYourGrabCardInPlay):
            frame = self.yourFrames[sampledFrames[i]]
            pygameRect = pygame.rect.Rect(frame[0][0], \
                                          frame[0][1], \
                                          self.GUIPars.cardWidth, \
                                          self.GUIPars.cardHeight)
            card = self.yourGrabbingCards[i]
            card.setRect(pygameRect)
            card.setFrame(frame)
            if tuple(frame) in self.occupied:
                self.occupied[tuple(frame)] = True
            self.numYourFramesOccupied += 1

        self.yourGrabCardsAssigned = True

    # The function updates mouse and phase
    def pressDoneButton(self, event, mouse):
        # if the "Done" button was pushed while it is my setup phase, then move onto grabbing phase
        if ((self.doneButton.collidepoint(event.pos)) and \
            (self.phase == Phase.YOUR_SET_UP) and \
            (self.numYourFramesOccupied >= self.numYourGrabCardInPlay)):
            self.phase = Phase.GRABBING
            self.dialogs.append("Grabbing Phase Starts.")
            self.displayReadCardStartTime = self.getTime_ms()

        if ((self.doneButton.collidepoint(event.pos)) and \
            (self.phase == Phase.YOUR_TRANSFER)):
            if (self.numCardsToTransfer != 0):
                self.dialogs.append("Still have " + str(self.numCardsToTransfer) + " cards to Transfer.")
            elif (self.numCardsToTransfer == 0):
                selectedTransferCards = []
                for card in self.grabbingCardsInPlay:
                    if (card.getColor() is self.colors.yellow):
                        card.setStatus(GrabCardStatus.OPPONENT)
                        card.setColor(self.colors.white)
                        self.occupied[tuple(card.getFrame())] = False
                        self.numYourFramesOccupied -= 1
                        selectedTransferCards.append(card)
                for transferCard in selectedTransferCards:  # maximum of two
                    frameIndexList = [k for k in range(len(self.opponentFrames))]
                    random.seed(time.time())
                    sampledFrames = random.sample(frameIndexList, self.numOppoGrabCardInPlay)
                    for i in range(self.numOppoGrabCardInPlay):
                        frame = self.opponentFrames[sampledFrames[i]]
                        pygameRect = pygame.rect.Rect(frame[0][0], \
                                                      frame[0][1], \
                                                      self.GUIPars.cardWidth, \
                                                      self.GUIPars.cardHeight)
                        if tuple(frame) not in self.occupied:
                            transferCard.setRect(pygameRect)
                            transferCard.setFrame(frame)
                            self.occupied[tuple(frame)] = True
                            break
                        elif tuple(frame) in self.occupied:
                            if not self.occupied[tuple(frame)]:
                                transferCard.setRect(pygameRect)
                                transferCard.setFrame(frame)
                                self.occupied[tuple(frame)] = True
                                break

                self.phase = Phase.RESET

    # Draw a reading card
    def drawReadingCard(self):
        if ((self.phase == Phase.GRABBING) and \
            (self.displayReadingCard is False)):
            self.curReadingCard = self.readingCardStack.drawOneCard()
            self.numReadCardChars = 0
            self.displayReadingCard = True

    # Execution of grabbing phase
    def grab(self, oppoTakesCorrectCard):
        oppoTakesCorrectCardAndDecisionWordAppeared = (self.GPInfo.decisionWordAppeared and \
                                                       oppoTakesCorrectCard)

        oppoTakesWrongCardAndReachesTime = ((not oppoTakesCorrectCard) and self.hasReachedOpponentGrabTime())

        opponentNeedsToRespond = ((self.GPInfo.oppoResponded is False) and \
                                  (oppoTakesCorrectCardAndDecisionWordAppeared or \
                                   oppoTakesWrongCardAndReachesTime))

        if (opponentNeedsToRespond):
            self.opponentRespondsInGrabPhase(oppoTakesCorrectCard)

        if (self.hasSomeoneTouched()):
            self.decideWinner()

        if (self.GPInfo.timesUp is True):
            if (self.GPInfo.yourTime is None):
                self.saveYourGrabTime_ms()
            self.decideWinner()

    # return selected Card if any
    def handleEvent(self, event, selectedCard, mouse, offset):
        if event.type == pygame.QUIT:  # Click the X in the window
            self.running = False

        # event.button:
        # 1 = left click
        # 2 = middle click
        # 3 = right click
        # 4 = scroll up
        # 5 = scroll down
        elif ((event.type == pygame.MOUSEBUTTONDOWN) and \
              (event.button == 1)):
            selectedCard = self.selectCard(event, mouse, offset)
            if (self.phase is Phase.GRABBING):
                self.saveYourGrabbingCard(selectedCard)
            if (self.phase == Phase.YOUR_SET_UP):
                self.pressDoneButton(event, mouse)
                self.drawReadingCard()
            if (self.phase == Phase.YOUR_TRANSFER):
                self.pressDoneButton(event, mouse)

        # The below only works in your set up phase
        elif ((event.type == pygame.MOUSEBUTTONUP) and \
              (event.button == 1) and \
              (selectedCard is not None)):
            if ((selectedCard.getStatus() is GrabCardStatus.OPPONENT) or \
                  (self.phase is not Phase.YOUR_TRANSFER)):
                selectedCard.setColor(self.colors.white)
            if (self.cardDragging and self.touchYourCard):
                frame = self.findNearestFrame(selectedCard.getPos())
                selectedCard.setRectX(frame[0][0])
                selectedCard.setRectY(frame[0][1])
                selectedCard.setFrame(frame)
                self.occupied[tuple(frame)] = True
                self.numYourFramesOccupied += 1

                self.cardDragging = False
                self.touchYourCard = False

        # Left click and drag your card
        elif ((event.type == pygame.MOUSEMOTION) and \
              self.cardDragging and \
              self.touchYourCard and \
              (selectedCard is not None)):
            mouse.x, mouse.y = event.pos
            selectedCard.setRectX(mouse.x + offset.x)
            selectedCard.setRectY(mouse.y + offset.y)

        return selectedCard

    def process(self):
        selectedCard = None
        # record mouse position relative to left top corner of the whole screen
        mouse = Point(0, 0)
        # record left top corner of the selected card relative to mouse position
        offset = Point(0, 0)
        oppoTakesCorrectCard = False
        while self.running:
            for event in pygame.event.get():
                selectedCard = self.handleEvent(event, selectedCard, mouse, offset)
            self.fillScreens()
            self.renderTime()
            self.renderCardFrames()
            self.renderDialogBox()
            if (self.phase is Phase.YOUR_SET_UP):
                if (self.debugMode and self.yourGrabCardsAssigned is False):
                    self.randomAssignYourGrabCards()
                self.renderDoneButton()
            self.renderGrabbingCardsAndWords(selectedCard)
            if (self.displayReadingCard):
                if (self.GPInfo.savedStartTime is False):
                    self.decideCorrectGrabCardStatus()
                    oppoTakesCorrectCard = self.decideOpponentTakingCorrectCardAndGrabbingTime()
                    self.saveGrabPhaseStartTime_ms()
                self.checkTimesUp()
                self.renderReadingCardWords()
                if (self.phase is Phase.GRABBING):
                    self.grab(oppoTakesCorrectCard)
            if (self.phase is Phase.OPPONENT_TRANSFER):
                self.opponentTransfers()
            if (self.phase is Phase.YOUR_TRANSFER):
                self.renderDoneButton()
            if (self.phase is Phase.RESET):
                self.reset()

            pygame.display.flip()  # update rendering contents
            self.clock.tick(self.GUIPars.FPS)

    def quit(self):
        pygame.quit()
