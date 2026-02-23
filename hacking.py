"""
Fallout-style terminal hacking minigame.
Returns True if cracked, False if locked out.
"""
import curses
import random
import string
import time
from config import (COLOR_NORMAL, COLOR_SELECTED, COLOR_DIM, COLOR_STATUS,
                    COLOR_TITLE, init_colors, playsound, set_show_status)
from status import draw_status

# ─── Word bank (all 5-letter words for consistent layout) ────────────────────
WORD_BANK = [
    "CRANE", "FLAME", "BLADE", "SHORE", "GRIME", "BRUTE", "STALE", "PRIME",
    "GRIND", "PLANK", "FLASK", "CRAMP", "BLAZE", "SCORN", "TROVE", "PHASE",
    "CLAMP", "SNARE", "GROAN", "FLINT", "BRICK", "CRAVE", "DRONE", "SCALP",
    "BLUNT", "CRISP", "PROWL", "SLICK", "KNAVE", "FRAIL", "STOVE", "GRASP",
    "CLEFT", "BRAND", "SMIRK", "TRAMP", "GLARE", "SPOUT", "DWARF", "BRAID",
    "CLOWN", "FROZE", "GRAFT", "PLUME", "SNORT", "BRAWN", "TRICK", "PRICE",
    "TANKS", "THIRD", "TRIES", "TIRES", "TERMS", "TEXAS", "TRITE", "TRIBE",
    "SKIES", "EXAMS", "EXTRA", "EXACT", "SPIES", "JOINS", "LOCKS", "STOCK",
    "VAULT", "POWER", "STEEL", "LASER", "NERVE", "FORCE", "GUARD", "WATCH",
    "DEATH", "BLOOD", "GHOST", "STORM", "NIGHT", "FLESH", "SKULL", "WASTE",
]

WORD_LEN   = 5
COLS       = 2      # display columns
ROWS       = 16     # rows per column
COL_WIDTH  = 12     # chars per column cell
NUM_WORDS  = 10     # words to hide
MAX_TRIES  = 4

JUNK = r"!@#$%^&*-+=[]{}|;:',.<>?/\~`"

def _junk_char():
    return random.choice(JUNK)

def _likeness(guess, answer):
    return sum(a == b for a, b in zip(guess, answer))

def _build_grid(answer):
    """
    Build a flat char array of COLS*ROWS*COL_WIDTH chars.
    Embed NUM_WORDS words (including the answer) at non-overlapping positions.
    Returns (chars, word_positions) where word_positions = [(start_idx, word), ...]
    """
    total = COLS * ROWS * COL_WIDTH
    chars = [_junk_char() for _ in range(total)]

    # Pick words
    pool = [w for w in WORD_BANK if w != answer]
    random.shuffle(pool)
    words = pool[:NUM_WORDS - 1] + [answer]
    random.shuffle(words)

    # Place words without overlap, not straddling row boundaries
    used = set()
    word_positions = []
    for word in words:
        placed = False
        for _ in range(200):
            row   = random.randint(0, ROWS * COLS - 1)
            col_s = random.randint(0, COL_WIDTH - WORD_LEN)
            start = row * COL_WIDTH + col_s
            idxs  = list(range(start, start + WORD_LEN))
            if not used.intersection(idxs):
                for i, ch in zip(idxs, word):
                    chars[i] = ch
                used.update(idxs)
                word_positions.append((start, word))
                placed = True
                break
        if not placed:
            # Fallback: overwrite anywhere
            start = random.randint(0, total - WORD_LEN)
            for i, ch in enumerate(word):
                chars[start + i] = ch
            word_positions.append((start, word))

    # Scatter matching bracket pairs in rows (for dud/replenish mechanic)
    bracket_pairs = []
    openers = '([<{'
    closers = ')]}>'
    for row in range(ROWS * COLS):
        row_start = row * COL_WIDTH
        # Try to place 0-1 pairs per row
        if random.random() < 0.3:
            max_span = COL_WIDTH - 2
            span = random.randint(1, max(1, max_span - 1))
            op = random.randrange(row_start, row_start + COL_WIDTH - span - 1)
            cl = op + span + 1
            if op not in used and cl not in used:
                pair_type = random.randint(0, 3)
                chars[op] = openers[pair_type]
                chars[cl] = closers[pair_type]
                bracket_pairs.append((op, cl))

    return chars, word_positions, bracket_pairs

def _idx_to_screen(idx, base_row):
    """Convert flat index to (screen_row, screen_col)."""
    col_block  = idx // (ROWS * COL_WIDTH)   # 0 or 1
    within     = idx % (ROWS * COL_WIDTH)
    row_in_col = within // COL_WIDTH
    char_in_row = within % COL_WIDTH
    # Layout: col0 starts at screen col 7, col1 at 7+COL_WIDTH+8 = 27
    scr_col = 7 + col_block * (COL_WIDTH + 14) + char_in_row
    scr_row = base_row + row_in_col
    return scr_row, scr_col

def _find_word_at(idx, word_positions):
    for start, word in word_positions:
        if start <= idx < start + len(word):
            return start, word
    return None, None

def _find_bracket_at(idx, bracket_pairs):
    for op, cl in bracket_pairs:
        if idx == op or idx == cl:
            return op, cl
    return None, None

def run_hacking_minigame(stdscr, username):
    """
    Run the hacking minigame. Returns True if password cracked, False if locked out.
    """
    answer    = random.choice(WORD_BANK)
    chars, word_positions, bracket_pairs = _build_grid(answer)
    total     = COLS * ROWS * COL_WIDTH
    cursor    = 0
    attempts  = MAX_TRIES
    log       = []   # right-panel log messages
    duds_left = [w for _, w in word_positions if w != answer]
    BASE_ROW  = 5    # first grid row on screen

    # Removed duds tracker
    removed_duds = set()

    def _draw():
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # ── Header ───────────────────────────────────────────────────────────
        header = "ROBCO INDUSTRIES (TM) TERMLINK PROTOCOL"
        stdscr.addstr(0, max(0, (w - len(header)) // 2), header,
                      curses.color_pair(COLOR_TITLE) | curses.A_BOLD)

        # Attempts line
        boxes = "■ " * attempts + "□ " * (MAX_TRIES - attempts)
        warn  = f"!!! WARNING: LOCKOUT IMMINENT !!!" if attempts <= 1 else f"{attempts} ATTEMPT(S) LEFT:"
        try:
            stdscr.addstr(2, 1, warn,  curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
            stdscr.addstr(2, len(warn) + 2, boxes.strip(),
                          curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
        except curses.error:
            pass

        #Hint
        stdscr.addstr(h - 2, 2, "TAB = Next Column  |  q = cancel",
                          curses.color_pair(COLOR_DIM))

        # ── Hex addresses ────────────────────────────────────────────────────
        base_addr = 0xF964
        for col_block in range(COLS):
            for row in range(ROWS):
                addr = base_addr + (col_block * ROWS + row) * COL_WIDTH
                scr_col = 1 + col_block * (COL_WIDTH + 14)
                scr_row = BASE_ROW + row
                try:
                    stdscr.addstr(scr_row, scr_col, f"0x{addr:04X}",
                                  curses.color_pair(COLOR_DIM))
                except curses.error:
                    pass

        # ── Grid characters ───────────────────────────────────────────────
        # Figure out what cursor is hovering over
        hover_word_start, hover_word = _find_word_at(cursor, word_positions)
        hover_bracket = _find_bracket_at(cursor, bracket_pairs)
        if hover_bracket == (None, None):
            hover_bracket = None

        for i, ch in enumerate(chars):
            sr, sc = _idx_to_screen(i, BASE_ROW)
            if sr >= h - 2:
                continue

            on_removed_word = any(
                start <= i < start + WORD_LEN
                for start, word in word_positions
                if word in removed_duds
            )

            if on_removed_word:
                attr = curses.color_pair(COLOR_DIM)
                ch_show = '.'
            elif hover_word_start is not None and hover_word_start <= i < hover_word_start + WORD_LEN:
                attr = curses.color_pair(COLOR_SELECTED) | curses.A_BOLD
                ch_show = ch
            elif hover_bracket and hover_bracket[0] <= i <= hover_bracket[1]:
                attr = curses.color_pair(COLOR_SELECTED) | curses.A_BOLD
                ch_show = ch
            elif i == cursor:
                attr = curses.color_pair(COLOR_SELECTED) | curses.A_BOLD
                ch_show = ch
            else:
                attr = curses.color_pair(COLOR_NORMAL)
                ch_show = ch

            try:
                stdscr.addch(sr, sc, ch_show, attr)
            except curses.error:
                pass

        # ── Right panel log ───────────────────────────────────────────────
        # col1 chars end at: 7 + (COL_WIDTH+14) + COL_WIDTH = 45; add gap
        panel_col = 7 + (COL_WIDTH + 14) + COL_WIDTH + 4
        try:
            stdscr.addstr(BASE_ROW - 1, panel_col, ">",
                          curses.color_pair(COLOR_NORMAL))
        except curses.error:
            pass
        for li, entry in enumerate(log[-ROWS:]):
            try:
                stdscr.addstr(BASE_ROW + li, panel_col, entry[:w - panel_col - 1],
                              curses.color_pair(COLOR_NORMAL))
            except curses.error:
                pass

        # ── Status bar ───────────────────────────────────────────────────
        draw_status(stdscr)
        stdscr.noutrefresh()
        curses.doupdate()

    # ── Input loop ───────────────────────────────────────────────────────────
    stdscr.keypad(True)    # ensure arrow keys return KEY_* constants
    curses.nocbreak()      # clear any halfdelay timeout
    curses.cbreak()        # blocking getch, no timeout
    stdscr.nodelay(False)
    curses.curs_set(0)

    while True:
        _draw()
        key = stdscr.getch()

        if key == -1:
            continue

        elif key == curses.KEY_RESIZE:
            init_colors()
            stdscr.clear()
            continue

        elif key in (curses.KEY_RIGHT, ord('d')):
            playsound('Sounds/ui_hacking_charenter_01.wav', False)
            cursor = (cursor + 1) % total

        elif key in (curses.KEY_LEFT, ord('a')):
            playsound('Sounds/ui_hacking_charenter_01.wav', False)
            cursor = (cursor - 1) % total

        elif key in (curses.KEY_DOWN, ord('s')):
            playsound('Sounds/ui_hacking_charenter_01.wav', False)
            _cb  = cursor // (ROWS * COL_WIDTH)
            _row = (cursor % (ROWS * COL_WIDTH)) // COL_WIDTH
            _chr = (cursor % (ROWS * COL_WIDTH)) % COL_WIDTH
            _row = (_row + 1) % ROWS
            cursor = _cb * ROWS * COL_WIDTH + _row * COL_WIDTH + _chr

        elif key in (curses.KEY_UP, ord('w')):
            playsound('Sounds/ui_hacking_charenter_01.wav', False)
            _cb  = cursor // (ROWS * COL_WIDTH)
            _row = (cursor % (ROWS * COL_WIDTH)) // COL_WIDTH
            _chr = (cursor % (ROWS * COL_WIDTH)) % COL_WIDTH
            _row = (_row - 1) % ROWS
            cursor = _cb * ROWS * COL_WIDTH + _row * COL_WIDTH + _chr

        elif key == 9:   # Tab — jump to same row position in other column
            playsound('Sounds/ui_hacking_charenter_01.wav', False)
            _cb  = cursor // (ROWS * COL_WIDTH)
            _row = (cursor % (ROWS * COL_WIDTH)) // COL_WIDTH
            _chr = (cursor % (ROWS * COL_WIDTH)) % COL_WIDTH
            _cb  = (_cb + 1) % COLS
            cursor = _cb * ROWS * COL_WIDTH + _row * COL_WIDTH + _chr

        elif key in (curses.KEY_ENTER, 10, 13, ord(' ')):
            # ── Select ───────────────────────────────────────────────────
            try:
                word_start, sel_word = _find_word_at(cursor, word_positions)
            except Exception:
                word_start, sel_word = None, None
            try:
                bracket = _find_bracket_at(cursor, bracket_pairs)
                if bracket == (None, None):
                    bracket = None
            except Exception:
                bracket = None

            if sel_word is None and bracket is None:
                pass   # junk character — do nothing

            elif sel_word and sel_word not in removed_duds:
                log.append(f">{sel_word}")
                if sel_word == answer:
                    _draw()
                    log.append(">Exact match!")
                    log.append(">Please wait")
                    log.append(">...")
                    _draw()
                    time.sleep(1.5)
                    from ui import _halfdelay
                    set_show_status(True)
                    _halfdelay()
                    return True
                else:
                    lk = _likeness(sel_word, answer)
                    log.append(f">Entry denied")
                    log.append(f">{lk}/{WORD_LEN} correct.")
                    attempts -= 1
                    if attempts <= 0:
                        log.append(">LOCKED OUT")
                        _draw()
                        time.sleep(2)
                        from ui import _halfdelay
                        set_show_status(True)
                        _halfdelay()
                        return False

            elif bracket:
                op, cl = bracket
                bracket_pairs.remove(bracket)
                # Flash the bracket span
                for _ in range(1):
                    for fi in range(op, cl + 1):
                        fsr, fsc = _idx_to_screen(fi, BASE_ROW)
                        try:
                            stdscr.addch(fsr, fsc, chars[fi],
                                         curses.color_pair(COLOR_STATUS) | curses.A_BOLD)
                        except curses.error:
                            pass
                    stdscr.noutrefresh()
                    curses.doupdate()
                    time.sleep(0.08)
                    _draw()
                    time.sleep(0.08)
                # Apply effect
                if duds_left and random.random() < 0.5:
                    dud = random.choice(duds_left)
                    duds_left.remove(dud)
                    removed_duds.add(dud)
                    log.append(">Dud removed.")
                else:
                    if attempts < MAX_TRIES:
                        attempts = min(MAX_TRIES, attempts + 1)
                        log.append(">Tries reset.")
                    else:
                        log.append(">No effect.")

        elif key in (ord('q'), ord('Q'), 27):
            from ui import _halfdelay
            set_show_status(True)
            _halfdelay()
            return False