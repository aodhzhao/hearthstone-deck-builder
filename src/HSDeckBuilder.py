#!/usr/bin/env python

import json
import Config
from MainWidgets import HeroButtonsFrame, CardsFrame, DeckFrame, DeckLabel, CardLabel
from Tkinter import Frame, Button
from requests import Session
from PIL import Image, ImageTk
from StringIO import StringIO

class HSDeckBuilder(Frame):

    def __init__(self, session, master=None):
        Frame.__init__(self, master=master)
        self.master.title('HSDeckBuilder')
        self.pack_propagate(0)
        
        #card_dict = Dictionary of hero classes with their associated card lists
        card_dict = load_cards(session)
        self.create_widgets(card_dict)
        self.display_card_images(card_dict)
        
    def create_widgets(self, card_dict):
        #Create CardsFrame
        self.cards_frame = CardsFrame(master=self.master, 
                                      width=Config.CARD_LABEL_WIDTH*Config.MAX_CARDS_PER_ROW,
                                      height=Config.CARD_LABEL_HEIGHT*Config.MAX_ROWS_PER_PAGE)
        self.cards_frame.grid_propagate(False)
        self.cards_frame.grid(column=1, row=1)
        
        #Add Cards to CardsFrame
        for x in range(1, Config.MAX_ROWS_PER_PAGE+1):
            for y in range(1, Config.MAX_CARDS_PER_ROW+1):
                card_label = CardLabel(master=self.cards_frame, image=None)
                def handler(event, card_label=card_label):
                   return self.add_to_deck(event, card_label)
                card_label.bind('<Button-1>', handler)
                card_label.grid(column=y, row=x)
        self.card_labels = self.cards_frame.winfo_children()    
        
        #Create DeckFrame
        self.deck_frame = DeckFrame(master=self.master, 
                                    width=150,
                                    height=Config.CARD_LABEL_HEIGHT*2)
        self.deck_frame.grid_propagate(False)
        self.deck_frame.grid(column=3, row=1, rowspan=2)
        
        self.deck_label = DeckLabel(master=self.deck_frame, image=None)
        self.deck_label.grid()
                
        #Create HeroButtonsFrame
        self.hero_buttons = HeroButtonsFrame(master=self.master)
        self.hero_buttons.grid(row=0, column=1, columnspan=Config.MAX_CARDS_PER_ROW)
        
        #Add buttons to HeroButtonsFrame
        for x, hero in enumerate(Config.HERO_CLASSES):
            button = Button(master=self.hero_buttons, text=hero, image=None)
            def handler(event, card_dict=card_dict, hero=hero):
                self.cards_frame.hero = hero
                self.cards_frame.page = 1
                return self.display_card_images(card_dict, event)
            button.bind('<Button-1>', handler)
            button.grid(column=x+1, row=0)
        self.hero_buttons = self.hero_buttons.winfo_children()

        #Create Next Button
        self.next_button = Button(master=self.master, text='Next', height=35)
        def handler(event, card_dict=card_dict):
            if self.cards_frame.page >= Config.MAX_PAGES:
                hero_index = Config.HERO_CLASSES.index(self.cards_frame.hero)
                if (hero_index < len(Config.HERO_CLASSES)-1):
                    self.cards_frame.hero = Config.HERO_CLASSES[hero_index+1]
                    self.cards_frame.page = 1                
            else:
                self.cards_frame.page = self.cards_frame.page+1
            return self.display_card_images(card_dict, event)
        self.next_button.bind('<Button-1>', handler)
        self.next_button.grid(column=2,row=1, rowspan=2)
        
        #Create Back Button
        self.back_button = Button(master=self.master, text='Back', height=35)
        def handler(event, card_dict=card_dict):
            if self.cards_frame.page <= 1:
                hero_index = Config.HERO_CLASSES.index(self.cards_frame.hero)
                if (hero_index > 0):
                    self.cards_frame.hero = Config.HERO_CLASSES[hero_index-1]
                    self.cards_frame.page = Config.MAX_PAGES
            else:
                self.cards_frame.page = self.cards_frame.page-1
            return self.display_card_images(card_dict, event)
        self.back_button.bind('<Button-1>', handler)
        self.back_button.grid(column=0,row=1, rowspan=2)
        
        self.save_button = Button(master=self.master, text='Save Deck')
        def handler(event):
            return self.save_deck(event)
        self.save_button.bind('<Button-1>', handler)
        self.save_button.grid(column=3,row=4)
        
    def display_card_images(self, card_dict, event=None):
        #card_list=List of cards to display depending on the current hero and page
        card_list = card_dict[self.cards_frame.hero][Config.MAX_CARDS_PER_PAGE*(self.cards_frame.page-1):]
        
        cards_to_display = len(card_list)
        if cards_to_display > Config.MAX_CARDS_PER_PAGE:
            cards_to_display = Config.MAX_CARDS_PER_PAGE
        
        #For each card label, decide if an image should be displayed
        #If there are less cards to display then card labels, than
        #blank images will fill those card labels
        for x in range(0, Config.MAX_CARDS_PER_PAGE):
            if x < cards_to_display:
                self.card_labels[x].name = card_list[x]['name']
                self.display_card_image(card_list[x]['image'], x) 
            else:
                self.display_card_image('', x)
        
    def display_card_image(self, card_image, x):
        self.card_labels[x].config(image = card_image)
        self.card_labels[x].image = card_image
    
    def add_to_deck(self, event, card):
        deck_labels = self.deck_frame.winfo_children()
        if len(deck_labels) == 30:
            return
        
        card_names = [l.text for l in deck_labels]
        if card_names.count(card.name) == 2:
            return
        
        deck_label = DeckLabel(master=self.deck_frame, image=None, text=card.name)
        if card.name in card_names:
           for label in deck_labels:
                if label.text == card.name:
                    label.config(text=label.text + ' x2')
        else:
            deck_label.grid()
        self.deck_frame.deck_list.append(card.name)
    
    def save_deck(self, event):
        if self.deck_frame.deck_list < 30:
            return
        str = ' \n'.join(self.deck_frame.deck_list)
        with open("Decks.txt", "a") as myFile:
            myFile.write(str)
        
        
def load_cards(session):
    card_dict = {}
    card_list = []
    
    #Read in the card data from json file
    card_data = open("AllSets.enUS.json").read()
    card_data = json.loads(card_data)

    for hero in Config.HERO_CLASSES:
        print 'Loading cards for %s...' % hero
        for set in Config.CARD_SETS:
            for card in card_data[set]:
                if ('playerClass' in card and 'cost' in card and
                    card['playerClass'] == hero and
                    card['id'] not in Config.CARDS_TO_IGNORE):
                    #
                    # if card does not have a playerclass than it is a netural card!
                    #
                        url = r'http://wow.zamimg.com/images/hearthstone/cards/enus/original/%s.png' % card['id']
                        response = session.get(url)
                        if response.status_code == 200:
                            img = Image.open(StringIO(response.content)).resize((Config.CARD_LABEL_WIDTH, 
                                                                                 Config.CARD_LABEL_HEIGHT), 
                                                                                 Image.ANTIALIAS)
                            photo_img = ImageTk.PhotoImage(img)
                            card['image'] = photo_img
                            card_list.append(card)
        card_list.sort(key=lambda x:(x['cost'], x['name']))
        card_dict[hero] = card_list[:]
        card_list[:] = []
    print 'Finished loading cards'   
    return card_dict
    
#Main application entry point
def main():
    print 'Starting HSDeckBuilder'
    session = Session()
    session.headers = {'user-agent': 'HearthStone Deck Builder v0.1'}
    app = HSDeckBuilder(session)
    app.mainloop()
#Standard main function
if __name__ == '__main__':
       main()