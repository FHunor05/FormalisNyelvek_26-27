from collections import Counter
import re
import sys
from project.problem import Problem


class RegexProblem(Problem):
    """4. feladat: Logfájl elemzése reguláris kifejezések (regexek)

    segítségével, string-függvények használata nélkül.
    """

    # A segédletben megadott alapkifejezés a 2-5. feladatokhoz:
    # 1. csoport: Teljes sor
    # 2. csoport: Dátum és idő (pl. "10-15 10:18:47.782")
    # 3. csoport: Process ID (PID)
    # 4. csoport: Thread ID (TID)
    # 5. csoport: Log szint (I, D, V, E, F, A, W)
    # 6. csoport: Tag
    # 7. csoport: Message (opcionális)
    LOG_PATTERN = re.compile(
        r"^(([0-9-]+ [0-9:.]+) +([0-9]+) +([0-9]+) ([IDVEFAW]) (.+?):(?: (.+))?)$"
    )

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

        if "--rgx" not in existing_options:
            parser.add_argument(
                "--rgx",
                type=int,
                choices=[1, 2, 3, 4, 5],
                help="Regex feladat sorszáma (1-5)",
            )

    def is_chosen_problem(self, args) -> bool:
        # A keretrendszer akkor futtatja ezt az osztályt, ha a --rgx kapcsoló meg van adva és van --input
        return (
            getattr(args, "rgx", None) is not None
            and hasattr(args, "input")
            and args.input is not None
        )

    def run(self, args):
        input_file = getattr(args, "input", None)
        output_file = getattr(args, "output", None)
        task_num = getattr(args, "rgx", None)

        if not input_file or task_num is None:
            return

        # 1. LÉPÉS: Bemeneti fájl beolvasása és sorokra bontása regexszel (splitlines/strip helyett)
        try:
            with open(
                input_file, "r", encoding="utf-8", errors="replace"
            ) as f:
                content = f.read()
            lines = re.split(r"\r?\n", content)
        except FileNotFoundError:
            sys.stderr.write(
                f"Hiba: A megadott fájl nem létezik: {input_file}\n"
            )
            return

        # 2. LÉPÉS: A kiválasztott alfeladat (1-5) futtatása
        if task_num == 1:
            result = self._solve_task_1(lines)
        elif task_num == 2:
            result = self._solve_task_2(lines)
        elif task_num == 3:
            result = self._solve_task_3(lines)
        elif task_num == 4:
            result = self._solve_task_4(lines)
        elif task_num == 5:
            result = self._solve_task_5(lines)
        else:
            sys.stderr.write(
                f"Hiba: Érvénytelen feladat sorszám: {task_num}\n"
            )
            return

        # 3. LÉPÉS: Eredmény kiírása a kimeneti fájlba
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result + "\n")

    def _solve_task_1(self, lines: list[str]) -> str:
        """1. feladat (--rgx 1): 10 különböző feltétel megszámolása a logban."""
        patterns = [
            # 1. az összes sort, amelyik 10. hónap 15-én jött létre
            re.compile(r"^10-15 "),
            # 2. az összes sort, amelyik 10. hónap 15-én 10 óra 18 perc és 51 másodperckor jött létre
            re.compile(r"^10-15 10:18:51\."),
            # 3. az összes sort, amelyik 51 másodperckor jött létre (mindegy a perc)
            re.compile(r"^[0-9-]+ [0-9]{2}:[0-9]{2}:51\."),
            # 4. az összes lowmemorykiller taget tartalmazó sor
            re.compile(
                r"^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ [IDVEFAW] lowmemorykiller *:"
            ),
            # 5. az összes 10:18:51 kor keletkező 221-es process id-jú sort
            re.compile(r"^[0-9-]+ 10:18:51\.[0-9]+ +221 +[0-9]+ "),
            # 6. az összes hibát tartalmazó sort (E)
            re.compile(r"^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ E "),
            # 7. az összes warningot (W) amit a PackageManager küld
            re.compile(
                r"^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ W PackageManager *:"
            ),
            # 8. az összes ExoPlayer-es debug (D) infót
            re.compile(
                r"^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ D .*ExoPlayer"
            ),
            # 9. az összes java állomány pozíciót tartalmazó hibát és warningot (E/W ... .java:)
            re.compile(r"^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ [EW] .+\.java:"),
            # 10. az összes olyan sort, ami tartalmazza a Thread szót a message részben (nem a tagben) -> tag: message
            # FONTOS: (.+?) nem-mohó illesztés a tagre, különben a message-beli ':' karakterig nyújtózkodik!
            re.compile(
                r"^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ [IDVEFAW] .+?: .*Thread"
            ),
        ]

    def _solve_task_2(self, lines: list[str]) -> str:
        """2. feladat (--rgx 2): Az összes hiba (E sorok) származási helye (stack trace .java fájlok)."""
        err_java_pattern = re.compile(
            r"^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ E .+?\(([A-Za-z0-9_$]+\.java):[0-9]+\)"
        )
        results = []
        for line in lines:
            m = err_java_pattern.search(line)
            if m:
                results.append(m.group(1))
        return "\n".join(results)

    def _solve_task_3(self, lines: list[str]) -> str:
        """3. feladat (--rgx 3): Az összes különböző process id előfordulási sorrendben."""
        seen = set()
        pids = []
        for line in lines:
            m = self.LOG_PATTERN.match(line)
            if m:
                pid = m.group(3)
                if pid not in seen:
                    seen.add(pid)
                    pids.append(pid)
        return "\n".join(pids)

    def _solve_task_4(self, lines: list[str]) -> str:
        """4. feladat (--rgx 4): A legtöbb errort (E) tartalmazó processz."""
        error_counts = Counter()
        for line in lines:
            m = self.LOG_PATTERN.match(line)
            if m and m.group(5) == "E":
                pid = m.group(3)
                error_counts[pid] += 1

        if not error_counts:
            return ""

        most_common_pid, count = error_counts.most_common(1)[0]
        return f"PID={most_common_pid} ({count} errors)"

    def _solve_task_5(self, lines: list[str]) -> str:
        """5. feladat (--rgx 5): A fő szálon történt hibák (E) száma (ahol PID == TID)."""
        # A (\1) visszahivatkozás biztosítja, hogy a 2. szám (TID) megegyezzen az 1. számmal (PID)
        main_thread_err_pattern = re.compile(
            r"^[0-9-]+ [0-9:.]+ +([0-9]+) +\1 E "
        )
        count = sum(1 for line in lines if main_thread_err_pattern.search(line))
        return str(count)