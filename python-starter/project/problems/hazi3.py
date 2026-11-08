import re
import sys
from project.problem import Problem


class MinimizeProblem(Problem):
    """Determinisztikus véges automata (DFA) minimalizálása

    a laboron tanult táblázatkitöltő (páronkénti megkülönböztető)
    algoritmus alapján.
    """

    def initialize_parser(self, parser):
        # 1. Meglévő parancssori kapcsolók összegyűjtése az ütközések elkerülésére
        existing_options = set()
        for action in parser._actions:
            existing_options.update(action.option_strings)

        # Kapcsolók regisztrálása, ha még nem léteznek a közös parserben
        if "--input" not in existing_options:
            parser.add_argument("--input", type=str, help="Bemeneti fájl útja")

        if "--output" not in existing_options:
            parser.add_argument(
                "--output", type=str, help="Kimeneti fájl útja"
            )

        if "--mini" not in existing_options:
            parser.add_argument(
                "--mini",
                action="store_true",
                help="Minimalizálás végrehajtása",
            )

    def is_chosen_problem(self, args) -> bool:
        # A keretrendszer akkor futtatja ezt az osztályt, ha a --mini kapcsoló aktív és van --input
        return (
            getattr(args, "mini", False) is True
            and hasattr(args, "input")
            and args.input is not None
        )

    def run(self, args):
        input_file = getattr(args, "input", None)
        output_file = getattr(args, "output", None)

        if not input_file:
            return

        # 1. LÉPÉS: Bemeneti fájl beolvasása soronként
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                raw_lines = f.read().splitlines()
        except FileNotFoundError:
            sys.stderr.write(
                f"Hiba: A megadott fájl nem létezik: {input_file}\n"
            )
            return

        # Levágjuk a felesleges szóközöket a sorok elejéről és végéről
        lines = [line.strip() for line in raw_lines]

        # Fejléc ellenőrzése: legalább 4 sornak lennie kell (állapotok, ábécé, kezdőállapot, végállapotok)
        if len(lines) < 4:
            sys.stderr.write(
                "Hiba: Hiányos bemeneti fejléc (legalább 4 sor szükséges).\n"
            )
            return

        states = lines[0].split()
        alphabet = lines[1].split()
        start_state = lines[2].strip()
        accept_states = set(
            lines[3].split()
        )  # Üres sor esetén üres halmaz lesz

        states_set = set(states)
        alphabet_set = set(alphabet)

        # 2. LÉPÉS: Alapvető hibakezelés (fejléc ellenőrzése)
        if start_state not in states_set:
            sys.stderr.write(
                f"Hiba: A kezdőállapot ('{start_state}') nem szerepel az"
                " állapotok listájában!\n"
            )
            return

        invalid_accept = accept_states - states_set
        if invalid_accept:
            sys.stderr.write(
                "Hiba: Érvénytelen végállapot(ok) szerepelnek a fejlécben:"
                f" {invalid_accept}\n"
            )
            return

        # 3. LÉPÉS: DFA átmenetek felolvasása és szintaktikai/szemantikai ellenőrzése
        # dfa_transitions: (forrás_állapot, szimbólum) -> célállapot
        dfa_transitions = {}

        for line in lines[4:]:
            if not line:
                continue

            parts = line.split()
            # Formai hiba: egy átmeneti sornak pontosan 3 részből kell állnia (forrás, jel, cél)
            if len(parts) != 3:
                sys.stderr.write(
                    f"Hiba: Hibás formátumú átmeneti sor: '{line}'\n"
                )
                return

            src, symbol, dst = parts

            # Szemantikai hiba: szerepel-e az állapot és a jel az érvényes halmazokban?
            if src not in states_set:
                sys.stderr.write(
                    f"Hiba: Érvénytelen forrásállapot ('{src}') az átmenetben:"
                    f" '{line}'\n"
                )
                return
            if dst not in states_set:
                sys.stderr.write(
                    f"Hiba: Érvénytelen célállapot ('{dst}') az átmenetben:"
                    f" '{line}'\n"
                )
                return
            if symbol not in alphabet_set:
                sys.stderr.write(
                    f"Hiba: Érvénytelen szimbólum ('{symbol}') az átmenetben:"
                    f" '{line}'\n"
                )
                return

            dfa_transitions[(src, symbol)] = dst

        # 4. LÉPÉS: Táblázatkitöltő algoritmus (megkülönböztethető állapotpárok keresése)
        # Összes lehetséges {p, q} állapotpár (ahol p != q) előállítása a félmátrixhoz
        all_pairs = []
        for i in range(len(states)):
            for j in range(i + 1, len(states)):
                all_pairs.append(frozenset([states[i], states[j]]))

        # Kezdeti csillagozás (*): azok a párok, ahol pontosan az egyik állapot végállapot
        marked_pairs = set()
        for pair in all_pairs:
            p, q = tuple(pair)
            if (p in accept_states) != (q in accept_states):
                marked_pairs.add(pair)

        # Iteratív csillagozás: a még meg nem jelölt párok vizsgálata az ábécé szimbólumaira
        changed = True
        while changed:
            changed = False
            for pair in all_pairs:
                if pair in marked_pairs:
                    continue

                p, q = tuple(pair)
                for symbol in alphabet:
                    next_p = dfa_transitions.get((p, symbol), None)
                    next_q = dfa_transitions.get((q, symbol), None)

                    # Ha csak az egyikből van átmenet az adott szimbólummal, megkülönböztethetőek
                    if (next_p is None) != (next_q is None):
                        marked_pairs.add(pair)
                        changed = True
                        break

                    # Ha mindkettőből van átmenet és különböző állapotba visznek,
                    # megnézzük, hogy a célállapot-pár meg van-e már csillagozva (*)
                    if (
                        next_p is not None
                        and next_q is not None
                        and next_p != next_q
                    ):
                        target_pair = frozenset([next_p, next_q])
                        if target_pair in marked_pairs:
                            marked_pairs.add(pair)
                            changed = True
                            break

        # 5. LÉPÉS: Ekvivalens állapotok összevonása (amelyek nem kaptak *-ot a táblázatban)
        # Kezdetben minden állapot saját külön halmazt alkot
        state_groups = {s: {s} for s in states}
        for pair in all_pairs:
            if pair not in marked_pairs:
                p, q = tuple(pair)
                # Összevonjuk p és q ekvivalencia-osztályát (unió)
                merged_group = state_groups[p] | state_groups[q]
                for s in merged_group:
                    state_groups[s] = merged_group

        # Egyedi összevont állapotcsoportok kigyűjtése
        unique_groups = {frozenset(group) for group in state_groups.values()}

        # 6. LÉPÉS: Állapotok átnevezése (q -> s, összevonásnál a legkisebb név megtartása)
        def state_sort_key(s):
            return (
                int(s[1:])
                if len(s) > 1 and s[1:].isdigit()
                else [
                    int(c) if c.isdigit() else c for c in re.split(r"(\d+)", s)
                ]
            )

        def to_s_name(s):
            if s.startswith("q"):
                return "s" + s[1:]
            match = re.search(r"\d+$", s)
            return f"s{match.group(0)}" if match else f"s{s}"

        state_mapping = {}
        min_states_set = set()

        for group in unique_groups:
            min_orig_state = min(group, key=state_sort_key)
            new_id = to_s_name(min_orig_state)
            min_states_set.add(new_id)
            for s in group:
                state_mapping[s] = new_id

        min_states = sorted(list(min_states_set), key=state_sort_key)
        min_start_state = state_mapping[start_state]
        min_accept_states = sorted(
            list({state_mapping[s] for s in accept_states}),
            key=state_sort_key,
        )

        # Átmenetek felépítése az új állapotnevekkel és duplikációk szűrése
        min_transitions_set = set()
        for (src, sym), dst in dfa_transitions.items():
            min_transitions_set.add(
                (state_mapping[src], sym, state_mapping[dst])
            )

        # 7. LÉPÉS: Kimenet rendezése a specifikáció szerint
        # Átmenetek rendezése ábécé sorrendben: 1. kiindulási állapot, 2. szimbólum, 3. célállapot
        min_transitions = sorted(
            list(min_transitions_set),
            key=lambda t: (t[0], t[1], t[2]),
        )

        # 8. LÉPÉS: Eredmény kiírása a kimeneti fájlba
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(" ".join(min_states) + "\n")
                f.write(" ".join(alphabet) + "\n")
                f.write(min_start_state + "\n")
                f.write(" ".join(min_accept_states) + "\n")
                for src, sym, dst in min_transitions:
                    f.write(f"{src} {sym} {dst}\n")