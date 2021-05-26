from __future__ import annotations

import datetime

# anki interfaces
from aqt import mw
from aqt import gui_hooks
from aqt.qt import QMessageBox
from anki.lang import _

from aqt.utils import getFile, getSaveFile
from ast import literal_eval


def announce(announcement):
    msg = QMessageBox(mw)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setText(_(announcement))
    msg.exec_()


def adjust_ease_factors(deck_id):
    from .autoEaseFactor import adjust_deck    
    adjust_deck(deck_id)
    announce("Ease adjustment complete!")


def export_ease_factors(deck_id):
    '''Saves a deck's ease factors using file picker.

    For some deck `deck_id`, prompts to save a file containing a
    dictionary that links card id keys to ease factors.
    '''
    deck_name = mw.col.decks.nameOrNone(deck_id)
    if deck_name is None:
        return

    # open file picker to store factors
    dt_now_str = str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    suggested_filename = "ease_factors_" + str(deck_id) + dt_now_str
    export_file = getSaveFile(mw, _("Export"), "export",
                              key="",
                              ext="",
                              fname=suggested_filename)
    if not export_file:
        return

    factors = {}
    card_ids = mw.col.find_cards(f'deck:"{deck_name}"')
    for card_id in card_ids:
        card = mw.col.getCard(card_id)
        factors[card_id] = card.factor
    with open(export_file, 'w') as export_file_object:
        export_file_object.write(str(factors))
    announce("Export complete!")


def import_ease_factors(deck_id, factors=None):
    '''Resets ease factors in a deck to a saved state.

    For deck `deck_id` and `factors`--a dictionary linking card id keys
    to ease factors--set the ease factors of the cards in the deck to the
    ease factors provided in `factors`.

    If factors is not provided, prompt user to load a file of ease values,
    such as one saved by `export_ease_factors()`.
    '''
    deck_name = mw.col.decks.nameOrNone(deck_id)
    if deck_name is None:
        print("Deck name not found on import_ease_factors, exiting...")
        return

    if factors is None:
        # open file picker to load factors
        import_file = getFile(mw, _("Import"), None,
                              filter="*", key="import")
        if import_file == []:
            # no file selected
            return
        with open(import_file, 'r') as import_file_object:
            factors = literal_eval(import_file_object.read())

    card_ids = mw.col.find_cards(f'deck:"{deck_name}"')
    for card_id in card_ids:
        card = mw.col.getCard(card_id)
        card.factor = factors.get(card_id, card.factor)
        card.flush()
    announce("Import complete!")


def add_deck_options(menu, deck_id):
    export_action = menu.addAction("Export Ease Factors (AEF)")
    export_action.triggered.connect(lambda _,
                                    did=deck_id: export_ease_factors(did))
    import_action = menu.addAction("Import Ease Factors (AEF)")
    import_action.triggered.connect(lambda _,
                                    did=deck_id: import_ease_factors(did))
    adjust_action = menu.addAction("Adjust Ease Factors To Performance")
    adjust_action.triggered.connect(lambda _,
                                    did=deck_id: adjust_ease_factors(did))


gui_hooks.deck_browser_will_show_options_menu.append(add_deck_options)
