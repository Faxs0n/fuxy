#!/usr/bin/env python3
# =========================================
#   FUXY - Password Profiler
#   Created by FAXSON
#   For authorized security testing only
# =========================================

import os
import sys
from datetime import datetime

# ── ANSI Colors ──────────────────────────
G  = "\033[92m"   # bright green
DG = "\033[32m"   # dark green
Y  = "\033[93m"   # yellow
R  = "\033[91m"   # red
W  = "\033[0m"    # reset
B  = "\033[1m"    # bold

LEET = {"a":"@","e":"3","i":"1","o":"0","s":"$","t":"7","b":"8","g":"9"}
SUFFIXES = ["1","2","12","21","01","123","1234","12345","123456",
            "!","!!","!!!","@","#","007","69","99","000","111",
            "777","666","321","2023","2024","2025","123!","!123"]


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    print(f"""{G}
  ███████╗██╗   ██╗██╗  ██╗██╗   ██╗
  ██╔════╝██║   ██║╚██╗██╔╝╚██╗ ██╔╝
  █████╗  ██║   ██║ ╚███╔╝  ╚████╔╝ 
  ██╔══╝  ██║   ██║ ██╔██╗   ╚██╔╝  
  ██║     ╚██████╔╝██╔╝ ██╗   ██║   
  ╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
{DG}  [ Password Profiler v1.0 ]
  [ Created by {G}FAXSON{DG}             ]
  [ For authorized testing only  ]{W}
""")


def ask(prompt, required=False):
    while True:
        val = input(f"  {G}>{W} {prompt}: ").strip()
        if val or not required:
            return val
        print(f"  {R}[!] This field is required.{W}")


def ask_int(prompt, default):
    val = input(f"  {G}>{W} {prompt} [{default}]: ").strip()
    try:
        return int(val) if val else default
    except ValueError:
        return default


def leetify(word):
    return "".join(LEET.get(c.lower(), c) for c in word)


def get_dob_variants(dob_str):
    variants = []
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
               "%m/%d/%Y", "%Y-%m-%d", "%d%m%Y"]
    d = None
    for fmt in formats:
        try:
            d = datetime.strptime(dob_str, fmt)
            break
        except ValueError:
            continue
    if not d:
        return variants
    day   = d.strftime("%d")
    month = d.strftime("%m")
    year  = d.strftime("%Y")
    yr    = year[2:]
    variants = [
        day+month+year, month+day+year,
        day+month+yr,   yr+month+day,
        year,           yr,
        month+year,     day+month,
        year+month+day,
    ]
    return variants


def generate(data, min_len, max_len):
    base = []

    def add(w):
        if not w:
            return
        w = w.strip()
        base.extend([w.lower(), w.capitalize(), w.upper()])

    add(data["name"])
    add(data["nickname"])
    add(data["partner"])
    add(data["pet"])
    add(data["child"])
    add(data["company"])
    add(data["hobby"])
    add(data["favword"])

    unique_base = list(dict.fromkeys(base))  # dedupe preserving order
    words = list(unique_base)

    # DOB variations
    dob_variants = []
    if data["dob"]:
        dob_variants = get_dob_variants(data["dob"])
        words.extend(dob_variants)
        for w in unique_base:
            for dv in dob_variants:
                words.append(w + dv)
                words.append(dv + w)

    # Cross-field combos
    for i, w1 in enumerate(unique_base):
        for j, w2 in enumerate(unique_base):
            if i != j:
                words.append(w1 + w2)

    # Suffixes + leet
    for w in unique_base:
        for s in SUFFIXES:
            words.append(w + s)
        leet = leetify(w)
        if leet != w:
            words.append(leet)
            for s in SUFFIXES:
                words.append(leet + s)

    # Filter
    seen = set()
    result = []
    for p in words:
        if p and p not in seen and min_len <= len(p) <= max_len:
            seen.add(p)
            result.append(p)
    return result


def save_wordlist(passwords, filename="fuxy_wordlist.txt"):
    with open(filename, "w") as f:
        f.write("\n".join(passwords))
    return filename


def main():
    clear()
    banner()

    print(f"  {DG}┌─ TARGET PROFILE ──────────────────{W}")
    data = {
        "name":     ask("First name"),
        "nickname": ask("Nickname / alias"),
        "dob":      ask("Date of birth (dd/mm/yyyy or leave blank)"),
        "partner":  ask("Partner's name"),
        "pet":      ask("Pet's name"),
        "child":    ask("Child's name"),
        "company":  ask("Company / school"),
        "hobby":    ask("Hobby / sport"),
        "favword":  ask("Favourite word"),
    }

    print()
    print(f"  {DG}┌─ OPTIONS ──────────────────────────{W}")
    min_len  = ask_int("Minimum password length", 6)
    max_len  = ask_int("Maximum password length", 20)
    filename = input(f"  {G}>{W} Output filename [fuxy_wordlist.txt]: ").strip()
    if not filename:
        filename = "fuxy_wordlist.txt"

    print()
    print(f"  {Y}[*] Generating wordlist...{W}")

    passwords = generate(data, min_len, max_len)

    if not passwords:
        print(f"  {R}[!] No passwords generated. Add more profile info or adjust length settings.{W}")
        sys.exit(1)

    path = save_wordlist(passwords, filename)

    print(f"  {G}[+] Done! {B}{len(passwords):,}{W}{G} passwords saved to {B}{path}{W}")
    print()
    print(f"  {DG}── FUXY v1.0 · by FAXSON ────────────{W}")
    print()

    # Preview
    preview = input(f"  {G}>{W} Preview first 20 passwords? [y/N]: ").strip().lower()
    if preview == "y":
        print()
        for i, p in enumerate(passwords[:20], 1):
            print(f"  {DG}{i:>3}.{W} {G}{p}{W}")
        print()

    print(f"  {Y}[!] Use only on systems you own or have written authorization to test.{W}")
    print()


if __name__ == "__main__":
    main()
