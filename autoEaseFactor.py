# inspired by https://eshapard.github.io/


# anki interfaces
from PyQt5.QtWidgets import QAction
from anki import version
from aqt import mw
from aqt import gui_hooks
from aqt import reviewer
from aqt.utils import tooltip
from anki.lang import _


# add on utilities
from . import ease_calculator
from . import semver
from . import deck_match
from . import two_button


def set_button_mode(card):
    odid = card.odid
    did = card.did
    if odid == 0:
        deck_id = did
    else:
        deck_id = odid
    config = get_current_config(deck_id)
    if config['two_button_mode']:
        two_button.enable_two_button()
    else:
        two_button.disable_two_button()
    
gui_hooks.reviewer_did_show_question.append(set_button_mode)


if semver.Version(version) >= semver.Version("2.1.26"):
    # this import has the effect of adding options to the deck settings
    from . import deck_settings 

    # window vs. widget error
    # from . import menu_action


def get_current_config(deck_id):
    defaults = {
        'target_ratio':0.85,
        'moving_average_weight':0.2,
        'stats_enabled':False,
        'stats_duration':5000,
        'stats_brief':False,
        'min_ease':1000,
        'max_ease':5000,
        'leash':100,
        'reviews_only':False,
        'starting_ease':None,
        'deck_settings':{},
        'starting_ease_factor':None,
        'enabled':True,
        'two_button_mode':True
    }

    current_config = defaults

    # update current_config with config file
    config = mw.addonManager.getConfig(__name__)
    all_deck_settings = config["deck_settings"]
    current_config = {**defaults, **config}

    # deck name to list of parent deck names
    deck_name = mw.col.decks.get(deck_id)['name']

    def parent_deck(dn):
        if "::" not in dn:
            return None
        else:
            return "::".join(dn.split("::")[:-1])
    
    deck_names = [deck_name]
    while parent_deck(deck_names[-1]) is not None:
        deck_names.append(parent_deck(deck_names[-1]))

    # update config with each deck, from parentmost to juniormost
    deck_names.reverse()
    for d in deck_names:
        this_deck_settings = all_deck_settings.get(d, {})
        current_config = {**current_config, **this_deck_settings}

    return current_config


# tests --
## no settings, basic settings, parent deck settings, subdeck settings
## cascade each setting unless overridden
## don't inherit from siblings
## BUG currently -- settings inherited correctly, but two button mode
##      is applied/removed inconsistently


def get_all_reps(card=mw.reviewer.card):
    return mw.col.db.list("select ease from revlog where cid = ? and "
                          "type IN (0, 1, 2, 3)", card.id)


def get_reviews_only(card=mw.reviewer.card):
    return mw.col.db.list(("select ease from revlog where type = 1"
                           " and cid = ?"), card.id)


def get_ease_factors(card=mw.reviewer.card):
    return mw.col.db.list("select factor from revlog where cid = ?"
                          " and factor > 0 and type IN (0, 1, 2, 3)",
                          card.id)


def get_starting_ease(card=mw.reviewer.card):
    odid = card.odid
    did = card.did
    if odid == 0:
        deck_id = did
    else:
        deck_id = odid
    try:
        deck_starting_ease = mw.col.decks.confForDid(
                deck_id)['new']['initialFactor']
    except KeyError:
        deck_starting_ease = 2500
    return deck_starting_ease


def suggested_factor(card=mw.reviewer.card, new_answer=None, leashed=True):
    """Loads card history from anki and returns suggested factor"""

    """Wraps calculate_ease()"""

    odid = card.odid
    did = card.did
    if odid == 0:
        deck_id = did
    else:
        deck_id = odid
    config = get_current_config(deck_id)
    
    card_settings = {}
    if config['reviews_only']:
        card_settings['review_list'] = get_reviews_only(card)
    else:
        card_settings['review_list'] = get_all_reps(card)

    if new_answer is not None:
        card_settings['review_list'].append(new_answer)
    card_settings['factor_list'] = get_ease_factors(card)
    # Ignore latest ease if you are applying algorithm from deck settings
    if new_answer is None and len(card_settings['factor_list']) > 1:
        card_settings['factor_list'] = card_settings['factor_list'][:-1]



    deck_starting_ease = get_starting_ease(card)
    config['starting_ease_factor'] = deck_starting_ease

    return ease_calculator.calculate_ease(config, card_settings, leashed)


def get_stats(card=mw.reviewer.card, new_answer=None):
    odid = card.odid
    did = card.did
    if odid != 0:
        deck_id = odid
    else:
        deck_id = did
    config = get_current_config(deck_id)

    rep_list = get_all_reps(card)
    if new_answer:
        rep_list.append(new_answer)
    factor_list = get_ease_factors(card)

    weight = config['moving_average_weight']
    target = config['target_ratio']

    if rep_list is None or len(rep_list) < 1:
        success_rate = target
    else:
        success_list = [int(_ > 1) for _ in rep_list]
        success_rate = ease_calculator.moving_average(success_list,
                                                      weight, init=target)
    if factor_list and len(factor_list) > 0:
        average_ease = ease_calculator.moving_average(factor_list, weight)
    else:
        if config['starting_ease_factor'] is None:
            config['starting_ease_factor'] = get_starting_ease(card)
        average_ease = config['starting_ease_factor']

    # add last review (maybe simplify by doing this after new factor applied)
    printable_rep_list = ""
    if len(rep_list) > 0:
        truncated_rep_list = rep_list[-10:]
        if len(rep_list) > 10:
            printable_rep_list += '..., '
        printable_rep_list += str(truncated_rep_list[0])
        for rep_result in truncated_rep_list[1:]:
            printable_rep_list += ", " + str(rep_result)
    if factor_list and len(factor_list) > 0:
        last_factor = factor_list[-1]
    else:
        last_factor = None
    card_types = {0: "new", 1: "learn", 2: "review", 3: "relearn"}
    queue_types = {0: "new",
                   1: "relearn",
                   2: "review",
                   3: "day (re)lrn",
                   4: "preview",
                   -1: "suspended",
                   -2: "sibling buried",
                   -3: "manually buried"}

    msg = f"card ID: {card.id}<br>"
    msg += (f"Card Queue (Type): {queue_types[card.queue]}"
            f" ({card_types[card.type]})<br>")
    deck_name = mw.col.decks.current()["name"]
    settings_deck = deck_match.deck_match(deck_name, config["deck_settings"].keys())
    if settings_deck is not None:
        msg += f"Using config from {settings_deck}<br>"
    msg += f"MAvg success rate: {round(success_rate, 4)}<br>"
    msg += f"Last factor: {last_factor}<br>"
    msg += f"MAvg factor: {round(average_ease, 2)}<br>"
    if card.queue != 2 and config['reviews_only']:
        msg += f"New factor: NONREVIEW, NO CHANGE<br>"
    else:
        new_factor = suggested_factor(card, new_answer)
        unleashed_factor = suggested_factor(card, new_answer, leashed=False)
        if new_factor == unleashed_factor:
            msg += f"New factor: {new_factor}<br>"
        else:
            msg += f"""New factor: {new_factor}"""
            msg += f""" (unleashed: {unleashed_factor})<br>"""
    msg += f"Rep list: {printable_rep_list}<br>"

    if config["stats_brief"] or not config['enabled']:
        msg = ""
        if not config['enabled']:
            msg += f"Using config from {settings_deck}<br>"
            msg += f"AEF DISABLED ON THIS DECK<br>"
            msg += f"Last factor: {last_factor}<br>"
            msg += f"New factor: Easy +150, Good +0, Hard -150, Again -200<br>"
        elif card.queue != 2 and config['reviews_only']:
            msg += f"New factor: NONREVIEW, NO CHANGE<br>"
        else:
            msg += f"Last factor: {last_factor}<br>"
            new_factor = suggested_factor(card, new_answer)
            unleashed_factor = suggested_factor(card, new_answer, leashed=False)
            if new_factor == unleashed_factor:
                msg += f"New factor: {new_factor}"
            else:
                msg += f"""New factor: {new_factor}"""
                msg += f""" (unleashed: {unleashed_factor})"""
   
    return msg


def display_stats(new_answer=None):
    odid = mw.reviewer.card.odid
    did = mw.reviewer.card.did
    if odid == 0:
        deck_id = did
    else:
        deck_id = odid
    config = get_current_config(deck_id)
    stats_duration = config['stats_duration']
    card = mw.reviewer.card
    msg = get_stats(card, new_answer)
    tooltip_args = {'msg': msg, 'period': stats_duration}
    if semver.Version(version) > semver.Version("2.1.30"):
        tooltip_args.update({'x_offset': 12, 'y_offset': 240})
    tooltip(**tooltip_args)


def adjust_factor(ease_tuple,
                  reviewer=reviewer.Reviewer,
                  card=mw.reviewer.card):
    assert card is not None
    odid = card.odid
    did = card.did
    if odid == 0:
        deck_id = did
    else:
        deck_id = odid
    config = get_current_config(deck_id)
    new_answer = ease_tuple[1]
    if config['enabled'] and (card.queue == 2 or not config['reviews_only']):
        card.factor = suggested_factor(card, new_answer)
    if config['stats_enabled']:
        display_stats(new_answer)
    return ease_tuple


def adjust_deck(deck_id):
    deck_name = mw.col.decks.nameOrNone(deck_id)
    card_ids = mw.col.find_cards(f'deck:"{deck_name}"')
    for card_id in card_ids:
        card = mw.col.getCard(card_id)
        card.factor = suggested_factor(card)
        card.flush()


def adjust_all_decks():
    for x in mw.col.decks.all_names_and_ids():
        deck_id, deck_name = str(x.id), x.name
        settings_for_cur_deck = get_current_config(deck_id)['deck_settings'].get(deck_name, None)
        if settings_for_cur_deck and settings_for_cur_deck['enabled']:
            adjust_deck(deck_id)


def adjust_all_decks_if_enabled():
    if mw.addonManager.getConfig(__name__)['enabled']: 
        adjust_all_decks()


def setup_adjust_all_decks_action():
    a = QAction("autoEaseFactor: Adjust all ease factors", mw)
    a.triggered.connect(adjust_all_decks)
    mw.form.menuTools.addAction(a)


setup_adjust_all_decks_action()

gui_hooks.profile_will_close.append(adjust_all_decks_if_enabled)

gui_hooks.reviewer_will_answer_card.append(adjust_factor)
