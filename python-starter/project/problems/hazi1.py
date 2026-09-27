from project.problem import Problem


class DFAProblem(Problem):
    """Determinisztikus véges automata (DFA) szimulációja."""

    def initialize_parser(self, parser):
        # Megnézzük a már regisztrált opciókat az ütközések elkerülésére
        existing_options = set()
        for action in parser._actions:
            existing_options.update(action.option_strings)

        if "--input" not in existing_options:
            parser.add_argument("--input", type=str, help="Bemeneti fájl útja")

        if "--output" not in existing_options:
            parser.add_argument(
                "--output", type=str, help="Kimeneti fájl útja"
            )

        if "--check" not in existing_options:
            parser.add_argument(
                "--check",
                type=str,
                help="Vesszővel elválasztott ellenőrzendő szavak",
            )

    def is_chosen_problem(self, args) -> bool:
        # A keretrendszer ez alapján tudja, hogy a mi feladatunkat kell lefuttatnia.
        # Akkor választja ezt a feladatot, ha a parancssorban megadták a --check argumentumot.
        return (
            hasattr(args, "check")
            and args.check is not None
            and hasattr(args, "input")
            and args.input is not None
        )

    def run(self, args):
        input_file = getattr(args, "input", None)
        output_file = getattr(args, "output", None)
        check_param = getattr(args, "check", None)

        if not input_file or check_param is None:
            return

        words_to_check = check_param.split(",") if check_param else []

        # 1. Bemeneti fájl beolvasása
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return

        if len(lines) < 4:
            return

        states = lines[0].split()
        alphabet = lines[1].split()
        start_state = lines[2].strip()
        accept_states = set(lines[3].split())

        # Átmenetek feltöltése: (aktuális_állapot, szimbólum) -> következő_állapot
        transitions = {}
        for line in lines[4:]:
            parts = line.split()
            if len(parts) == 3:
                src, symbol, dst = parts
                transitions[(src, symbol)] = dst

        # 2. Szavak ellenőrzése
        results = []
        for word in words_to_check:
            current_state = start_state
            accepted = True

            for symbol in word:
                if (current_state, symbol) in transitions:
                    current_state = transitions[(current_state, symbol)]
                else:
                    accepted = False
                    break

            if accepted and current_state in accept_states:
                results.append("IGEN")
            else:
                results.append("NEM")

        # 3. Kiírás a kimeneti fájlba
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                for res in results:
                    f.write(res + "\n")