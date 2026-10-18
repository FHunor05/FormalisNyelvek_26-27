import sys
from project.problem import Problem


class DeterminizeProblem(Problem):
    """Nemdeterminisztikus véges automata (NFA) determinizálása (DFA-vá alakítása)

    az előadáson tanult részhalmaz-konstrukciós (subset construction)
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

        if "--det" not in existing_options:
            parser.add_argument(
                "--det",
                action="store_true",
                help="Determinizálás végrehajtása",
            )

    def is_chosen_problem(self, args) -> bool:
        # A keretrendszer akkor futtatja ezt az osztályt, ha a --det kapcsoló aktív és van --input
        return (
            getattr(args, "det", False) is True
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
            sys.stderr.write(f"Hiba: A megadott fájl nem létezik: {input_file}\n")
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
        accept_states = set(lines[3].split())  # Üres sor esetén üres halmaz lesz

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
                f"Hiba: Érvénytelen végállapot(ok) szerepelnek a fejlécben:"
                f" {invalid_accept}\n"
            )
            return

        # 3. LÉPÉS: NFA átmenetek felolvasása és szintaktikai/szemantikai ellenőrzése
        # nfa_transitions: (forrás_állapot, szimbólum) -> set(célállapotok)
        nfa_transitions = {}

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

            # NFA esetén egy állapot-szimbólum párból több célállapotba is mehetünk
            if (src, symbol) not in nfa_transitions:
                nfa_transitions[(src, symbol)] = set()
            nfa_transitions[(src, symbol)].add(dst)

        # 4. LÉPÉS: Determinizálás (Részhalmaz-konstrukció szélességi bejárással)
        # Az automata kezdő DFA állapota (s0) az NFA kezdőállapotát tartalmazó halmaz
        initial_subset = frozenset([start_state])

        dfa_states = ["s0"]  # A felfedezés sorrendjében tárolt DFA állapotnevek
        subset_to_id = {
            initial_subset: "s0"
        }  # Halmaz -> DFA állapotazonosító
        id_to_subset = {
            "s0": initial_subset
        }  # DFA állapotazonosító -> NFA részhalmaz
        queue = [initial_subset]  # Szélességi bejárás (BFS) feldolgozási sora

        dfa_transitions = []  # Eltárolt átmenetek: (forrás_id, jel, cél_id)

        while queue:
            current_subset = queue.pop(0)  # Következő feldolgozandó DFA állapot
            current_id = subset_to_id[current_subset]

            for symbol in alphabet:
                # Kiszámoljuk az összes elérhető állapot unióját az aktuális részhalmazból
                next_subset_set = set()
                for q in current_subset:
                    if (q, symbol) in nfa_transitions:
                        next_subset_set.update(nfa_transitions[(q, symbol)])

                # Ha nincs átmenet (üres halmaz), a specifikáció szerint nem veszünk fel élt
                if not next_subset_set:
                    continue

                next_subset = frozenset(next_subset_set)

                # Ha ezzel az állapotkombinációval még nem találkoztunk, regisztráljuk új DFA állapotként
                if next_subset not in subset_to_id:
                    new_id = f"s{len(dfa_states)}"
                    subset_to_id[next_subset] = new_id
                    id_to_subset[new_id] = next_subset
                    dfa_states.append(new_id)
                    queue.append(next_subset)  # Ezt a részhalmazt is fel kell majd dolgozni

                dfa_transitions.append(
                    (current_id, symbol, subset_to_id[next_subset])
                )

        # 5. LÉPÉS: DFA végállapotok kiválasztása
        # Egy állapot akkor végállapot, ha a mögötte lévő részhalmaz tartalmazza az NFA valamelyik végállapotát
        dfa_accept_states = [
            s_id
            for s_id in dfa_states
            if any(q in accept_states for q in id_to_subset[s_id])
        ]

        # 6. LÉPÉS: Kimenet rendezése a specifikáció szerint
        # Segédfüggvény a természetes számszerű sorrendhez (s2 megelőzze s10-et)
        def state_sort_key(s):
            return int(s[1:]) if len(s) > 1 and s[1:].isdigit() else s

        # Átmenetek rendezése: 1. forráscsúcs, 2. élcímke, 3. célcsúcs szerint
        dfa_transitions.sort(
            key=lambda t: (state_sort_key(t[0]), t[1], state_sort_key(t[2]))
        )
        dfa_accept_states.sort(key=state_sort_key)

        # 7. LÉPÉS: Eredmény kiírása a kimeneti fájlba
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(" ".join(dfa_states) + "\n")
                f.write(" ".join(alphabet) + "\n")
                f.write(dfa_states[0] + "\n")
                f.write(" ".join(dfa_accept_states) + "\n")
                for src, sym, dst in dfa_transitions:
                    f.write(f"{src} {sym} {dst}\n")