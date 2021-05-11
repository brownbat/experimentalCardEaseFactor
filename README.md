# experimentalCardEaseFactor

Dynamically adjusts ease factor on cards automatically after each rep, constantly seeking the
right ease adjustment to hit a target success rate.

See: <a href="https://eshapard.github.io/anki/thoughts-on-a-new-algorithm-for-anki.html" rel="nofollow">eshapard's "Thoughts on a new algorithm for Anki</a> for the original rationale.

Important: **You must NOT/NOT use an interval modifier in your deck options**.
Your interval modifier MUST be set to 100% (no change) for all decks. Otherwise
this algorithm could be constantly chasing a moving target.

#### Differences from eshapard's version

Unlike eshapard's version, which requires four reviews before the algorithm
kicks in, this version lets the algorithm adjust ease factors as early as
possible, including using information from learning steps. Early data is less reliable, 
though, so we do two things: we limit how much the algorithm can change the ease 
factor at first, and we use a moving average to more heavily weight recent reps 
when calculating success rate.

If it took you a long time to learn a card originally, but now you've
really got it down, your ease will rebound very quickly. The 'leash' setting ties
your ease factor down at first, which limits the initial swings of the algorithm 
until you've had many more reviews and better quality data.

If you're used to ease factors very close to 250%, without a low leash, this
algorithm can produce some alarmingly low (or high) ease factors. It will
generally auto-adjust very quickly based on your performance though. 

My anecdotal experience is that it front loads the work a bit, causing more
reviews with short intervals in the beginning for hard cards, but backing off 
quickly after I know a card well.

### Installation

#### In Anki,

    Tools > Add-ons > Get Add-ons...

Then use this code:

    1672712021

#### Manual installation

Create a new folder named *autoEaseFactor* in your Anki addons
directory. Save all add-on files to this folder. If you don't want to use
Two Button mode, it's still recommended you include the file to prevent
errors, but you can simply disable this mode in settings.

### Configuration

To access the configuration section:

1. Go to `Tools`, and select the `Add-ons` option from the dropdown.
2. In the `Add-ons` window, select `Auto Ease Factor`.
3. On the right-hand side of the `Add-ons` window, click on `Config`. This opens up the configuration `JSON` options.

There are a few options that can be configured by editing the addon:

1. 'target_ratio' is the success rate you want to aim for (e.g. 0.85 for an 85%
success rate)
2. 'leash' controls how much the ease can change per review, so a small leash 
of 10 or 50 will not let the algorithm adjust things until it has much more 
data.
3. moving_average_weight indicates how much to focus on more recent results
when determining success rate. Higher numbers will focus more on recent
performance. (This is very sensitive, values between 0.07 and 0.3 are
reasonable).
4. min_ and max_ ease set the bounds of how far the algorithm can set the 
ease. This is "per mille," so 5000 = 500%.
5. two_button_mode makes the system "pass/fail" -- you can disable that by 
setting this to false (though saving mental load on each review is the primary
benefit of this add-on, so I would recommend you leave this true if you can).

## Two Button Mode
Hard and easy add more choices that delay reviews and make you responsible for
determing your ideal ease rating. The ease factor algorithm adjusts ease for
you, so you just need to choose either "Again" or "Good" on any given card.

The Two-Button file in the addon changes your options to Pass/Fail to help
streamline your self evaluation, similar to low-key Anki and ja dark's work
that inspired it.

I suggest that you use the TwoButton addon and that you disable
*Show next review time above answer buttons* in Tools &gt; Preferences...
The next review times are misleading, they don't take into account the adjustments
from this add-on and can distract you from studying.

If you just want to try this out, but you're worried about losing all the ease factors you've built up so far, 
the latest version lets you export a deck's current ease factors and re-import them later.
You could use that to "save" your ease settings for a deck, try this add-on, then if you don't like it, 
reload your old ease settings later. Hat tip to RisingOrange for the inspiration, also check out his add-on:
Reset Ease Automatically:
<a href="https://ankiweb.net/shared/info/12081346" rel="nofollow">https://ankiweb.net/shared/info/12081346</a>


## Acknowledgments
- eshapard
- ja-dark
- cordone
- risingorange
- the MIA crew
- the AnKing

I am not requesting support, but the original author, eshapard, can receive
tips at this link:
<a href="https://paypal.me/eshapard/1" rel="nofollow">https://paypal.me/eshapard/1</a>

### Changes

#### 2020-09-14

Add import/export ease settings to deck options (plus some bugfixes associated with that change).

#### 2020-09-07

Rebrand, compatibility with latest version of Anki.

#### 2020-08-23

New ease factors now incorporate the current review instead of looking only at historical reviews in the review log, and rely on the list of ease factors directly instead of deriving that information by comparing historical intervals. This should be more accurate in almost every case, but would throw off somebody who is continually rescheduling cards. Please provide feedback on github if this creates any unexpected results.

#### 2020-08-09

Bugfix for formatted stats on new cards

#### 2020-08-08

Slight formatting adjustment for stats. Also updates "tests[.]py" to be more accurate. Unfortunately "tests" still does not predict the algorithm's behavior exactly. I am expecting a better simulator next patch, after some additional debugging. (In the meantime, if you open "tests[.]py" and hardcode a list of ease factors, as in the commented-out example from lines 272 to 279, you will get an accurate simulation.)

#### 2020-08-06

Adding four-button mode as an option, for those who don't want to use the Pass/Fail mode. I'd caution against using this though, the algorithm's main benefit is reducing your thinking time on each card.

(More history on GitHub: <a href="https://github.com/brownbat/autoEaseFactor" rel="nofollow">https://github.com/brownbat/autoEaseFactor</a> )
