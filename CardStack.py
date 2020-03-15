import random
import time

class CardStack:
    def __init__(self, cards):
        # top card has index 0
        self.cards = [card for card in cards]  # not modify the input "cards"

    def shuffle(self):  # Fisher-Yates Shuffle
        random.seed(time.time())
        for i in range(len(self.cards) - 1, 0, -1):
            j = random.randint(0, i)
            self.cards[i], self.cards[j] = self.cards[j], self.cards[i]

    def draw(self, numCards):
        return [self.cards.pop(0) for i in range(numCards)]

    def drawOneCard(self):
        output = None
        if (len(self.cards) > 0):
            output = self.cards.pop(0)
        return output

    def add(self, card):
        self.cards.insert(0, card)
