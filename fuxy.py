#!/usr/bin/env python3
# =========================================
#   FUXY v2.0 - Advanced Password Profiler
#   Created by FAXSON
#   For authorized security testing only
# =========================================

import os, sys, itertools, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from threading import Thread

G="\033[92m"; DG="\033[32m"; Y="\033[93m"; R="\033[91m"; W="\033[0m"; B="\033[1m"

LEET_MAP = {
    "a":["@","4"],"e":["3"],"i":["1","!"],"o":["0"],"s":["$","5"],
    "t":["7","+"],"b":["8"],"g":["9"],"l":["1"],"z":["2"],"h":["#"],"x":["%"],
}
SUFFIXES = [
    "1","2","12","21","01","007","69","99","100","123","1234","12345","123456",
    "!","!!","!!!","@","#","$","*","000","111","222","333","444","555","666",
    "777","888","999","321","2020","2021","2022","2023","2024","2025","2026",
    "123!","!123","@123","pass","pwd","qwerty","abc","xyz",
]
PREFIXES = ["the","my","mr","ms","dr","@","#","_",".","123","000","777","2024","2025"]
SEPARATORS = ["_","-",".","@","#","!","*"]
KEYBOARD_WALKS = ["qwerty","asdf","zxcv","qweasd","1q2w3e","pass","love","hate"]
COMMON_WORDS = [
    "love","hate","life","kill","dark","dead","evil","god","devil","angel",
    "fire","ice","blood","death","night","king","queen","boss","wolf","dragon",
    "shadow","ghost","storm","black","white","red","blue","tiger","fox","star",
]

def leetify(word):
    if not word: return [word]
    results = [word]
    for i, ch in enumerate(word.lower()):
        if ch in LEET_MAP:
            for rep in LEET_MAP[ch]:
                results.append(word[:i] + rep + word[i+1:])
    full = "".join(LEET_MAP[c][0] if c in LEET_MAP else c for c in word.lower())
    if full != word.lower(): results.extend([full, full.upper()])
    return list(dict.fromkeys(results))

def case_variants(word):
    if not word: return []
    alt = "".join(c.upper() if i%2==0 else c.lower() for i,c in enumerate(word))
    return list(dict.fromkeys([word.lower(),word.upper(),word.capitalize(),word.title(),word.swapcase(),alt]))

def get_dob_variants(dob_str):
    variants = []
    if not dob_str: return variants
    for fmt in ["%d/%m/%Y","%d-%m-%Y","%d.%m.%Y","%m/%d/%Y","%Y-%m-%d","%d%m%Y","%d/%m/%y"]:
        try:
            d = datetime.strptime(dob_str.strip(), fmt)
            day=d.strftime("%d"); mon=d.strftime("%m"); year=d.strftime("%Y"); yr=year[2:]
            d_=str(d.day); m_=str(d.month)
            variants = [day+mon+year,mon+day+year,day+mon+yr,yr+mon+day,year,yr,
                        mon+year,day+mon,year+mon+day,d_+m_+year,m_+d_+year,
                        mon+day,year+mon,day+year,mon+yr,d_+m_+yr,yr+m_+d_]
            return list(dict.fromkeys(variants))
        except ValueError: continue
    return variants

def generate(data, min_len=6, max_len=20, include_common=False,
             include_keyboard=False, include_reverse=False,
             include_double=False, include_prefixes=False, include_separators=False):
    raw = []
    for k in ["name","nickname","partner","pet","child","company","school",
              "hobby","sport","favword","color","car","music","username",
              "email_user","birthplace","phone"]:
        v = data.get(k,"").strip()
        if v: raw.append(v)

    expanded = list(dict.fromkeys(w for word in raw for w in case_variants(word)))
    words = list(expanded)

    dob_v = get_dob_variants(data.get("dob",""))
    if dob_v:
        words.extend(dob_v)
        for w in expanded:
            for dv in dob_v:
                words.append(w+dv); words.append(dv+w)

    for w1,w2 in itertools.permutations(expanded,2):
        words.append(w1+w2)

    short = [w for w in expanded if len(w)<=5][:8]
    for w1,w2,w3 in itertools.permutations(short,3):
        words.append(w1+w2+w3)

    for w in list(expanded):
        for s in SUFFIXES: words.append(w+s)
        if include_prefixes:
            for p in PREFIXES: words.append(p+w)

    for w in list(expanded):
        for lv in leetify(w):
            words.append(lv)
            for s in SUFFIXES[:15]: words.append(lv+s)

    if include_reverse:
        for w in list(expanded):
            rev = w[::-1]; words.append(rev)
            for s in SUFFIXES[:10]: words.append(rev+s)

    if include_double:
        for w in list(expanded): words.append(w+w)

    if include_separators:
        for w in list(expanded):
            for sep in SEPARATORS:
                for s in SUFFIXES[:10]: words.append(w+sep+s)
        for w1,w2 in itertools.permutations(expanded[:6],2):
            for sep in SEPARATORS: words.append(w1+sep+w2)

    if include_keyboard:
        words.extend(KEYBOARD_WALKS)
        for w in list(expanded):
            for kw in KEYBOARD_WALKS: words.append(w+kw)

    if include_common:
        for w in list(expanded):
            for cw in COMMON_WORDS:
                words.append(w+cw); words.append(cw+w)
        words.extend(COMMON_WORDS)

    seen=set(); result=[]
    for p in words:
        if p and p not in seen and min_len<=len(p)<=max_len:
            seen.add(p); result.append(p)
    return result

def save_wordlist(passwords, filename="fuxy_wordlist.txt"):
    with open(filename,"w",encoding="utf-8") as f: f.write("\n".join(passwords))
    return filename

# ══ GUI ══════════════════════════════════════
class FuxyGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FUXY v2.0 — Password Profiler by FAXSON")
        self.root.configure(bg="#060b06")
        self.root.geometry("950x720")
        self.passwords = []
        self._build()

    def _lbl(self,p,t,**k): return tk.Label(p,text=t,bg="#060b06",fg="#3a9a3a",font=("Courier New",9),**k)
    def _ent(self,p,v):
        e=tk.Entry(p,textvariable=v,bg="#0a0f0a",fg="#7fff7f",insertbackground="#00ff41",
                   relief="flat",font=("Courier New",10),highlightthickness=1,
                   highlightcolor="#00ff41",highlightbackground="#1e5c1e")
        e.bind("<FocusIn>", lambda ev:e.config(highlightbackground="#00ff41"))
        e.bind("<FocusOut>",lambda ev:e.config(highlightbackground="#1e5c1e"))
        return e
    def _sec(self,p,t):
        return tk.LabelFrame(p,text=f"  {t}  ",bg="#0b140b",fg="#00ff41",
                             font=("Courier New",9,"bold"),bd=1,relief="solid",padx=10,pady=8)

    def _build(self):
        r=self.root
        # Header
        h=tk.Frame(r,bg="#060b06"); h.pack(fill="x",pady=(10,2))
        tk.Label(h,text="FUXY",bg="#060b06",fg="#00ff41",font=("Courier New",30,"bold")).pack()
        tk.Label(h,text="Advanced Password Profiler v2.0  ·  by FAXSON",
                 bg="#060b06",fg="#2a7a2a",font=("Courier New",9)).pack()
        tk.Frame(r,bg="#00ff41",height=1).pack(fill="x",padx=16,pady=6)

        # Tabs
        st=ttk.Style(); st.theme_use("default")
        st.configure("TNotebook",background="#060b06",borderwidth=0)
        st.configure("TNotebook.Tab",background="#0b140b",foreground="#3a9a3a",
                     font=("Courier New",9),padding=[12,4])
        st.map("TNotebook.Tab",background=[("selected","#0f1f0f")],foreground=[("selected","#00ff41")])
        st.configure("TFrame",background="#060b06")
        nb=ttk.Notebook(r); nb.pack(fill="both",expand=True,padx=10,pady=2)

        t1=ttk.Frame(nb); nb.add(t1,text="  👤 Profile  ")
        t2=ttk.Frame(nb); nb.add(t2,text="  ⚙  Options  ")
        t3=ttk.Frame(nb); nb.add(t3,text="  📋 Output   ")

        self._tab_profile(t1); self._tab_options(t2); self._tab_output(t3)

        # Bottom bar
        b=tk.Frame(r,bg="#060b06"); b.pack(fill="x",padx=12,pady=6)
        for txt,cmd,bg,fg in [
            ("▶  GENERATE",self._gen_thread,"#003300","#00ff41"),
            ("↓  SAVE .TXT",self._save,"#001a00","#00aa33"),
            ("✖  CLEAR",self._clear,"#1a0000","#cc3333"),
        ]:
            tk.Button(b,text=txt,command=cmd,bg=bg,fg=fg,activebackground="#002200",
                      activeforeground="#00ff41",font=("Courier New",10,"bold"),
                      relief="flat",padx=16,pady=8,cursor="hand2").pack(side="left",padx=(0,6))
        self.status=tk.Label(b,text="Ready.",bg="#060b06",fg="#2a6a2a",font=("Courier New",9))
        self.status.pack(side="right")
        tk.Label(r,text="⚠  Authorized testing only  ·  FUXY v2.0 by FAXSON",
                 bg="#060b06",fg="#152815",font=("Courier New",8)).pack(pady=(0,4))

    def _tab_profile(self,tab):
        canvas=tk.Canvas(tab,bg="#060b06",highlightthickness=0)
        scroll=tk.Scrollbar(tab,orient="vertical",command=canvas.yview)
        frame=tk.Frame(canvas,bg="#060b06")
        frame.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0),window=frame,anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        self.vars={}

        col1=[("name","First Name"),("nickname","Nickname / Alias"),("dob","Date of Birth (dd/mm/yyyy)"),
              ("partner","Partner Name"),("pet","Pet Name"),("child","Child Name"),
              ("company","Company"),("school","High School")]
        col2=[("hobby","Hobby"),("sport","Favourite Sport"),("favword","Favourite Word"),
              ("color","Favourite Color"),("car","Car / Brand"),("music","Favourite Artist"),
              ("username","Username / Handle"),("email_user","Email Username")]
        col3=[("birthplace","Birth City"),("phone","Phone Digits (last 4)")]

        lf1=self._sec(frame,"Personal Info"); lf1.grid(row=0,column=0,padx=10,pady=8,sticky="nsew")
        lf2=self._sec(frame,"Interests & Online"); lf2.grid(row=0,column=1,padx=10,pady=8,sticky="nsew")
        lf3=self._sec(frame,"Extra Fields"); lf3.grid(row=1,column=0,padx=10,pady=8,sticky="nsew",columnspan=2)

        for lf,cols in [(lf1,col1),(lf2,col2)]:
            for i,(k,l) in enumerate(cols):
                self.vars[k]=tk.StringVar()
                self._lbl(lf,l).grid(row=i,column=0,sticky="w",pady=2)
                self._ent(lf,self.vars[k]).grid(row=i,column=1,padx=(8,0),pady=2,sticky="ew")
            lf.columnconfigure(1,weight=1)

        fr=tk.Frame(lf3,bg="#0b140b"); fr.pack(fill="x")
        for i,(k,l) in enumerate(col3):
            self.vars[k]=tk.StringVar()
            self._lbl(fr,l).grid(row=0,column=i*2,sticky="w",padx=(0,4))
            self._ent(fr,self.vars[k]).grid(row=0,column=i*2+1,padx=(0,24),sticky="ew")

    def _tab_options(self,tab):
        f=tk.Frame(tab,bg="#060b06"); f.pack(fill="both",expand=True,padx=16,pady=10)

        lf=self._sec(f,"Length Filter"); lf.pack(fill="x",pady=(0,10))
        row=tk.Frame(lf,bg="#0b140b"); row.pack(fill="x")
        self.min_len=tk.StringVar(value="6"); self.max_len=tk.StringVar(value="20")
        for t,v in [("Min Length:",self.min_len),("Max Length:",self.max_len)]:
            self._lbl(row,t).pack(side="left",padx=(0,4))
            tk.Entry(row,textvariable=v,width=5,bg="#0a0f0a",fg="#7fff7f",
                     insertbackground="#00ff41",font=("Courier New",10),relief="flat",
                     highlightthickness=1,highlightbackground="#1e5c1e").pack(side="left",padx=(0,16))

        mf=self._sec(f,"Mutation Toggles"); mf.pack(fill="x",pady=(0,10))
        self.opt_common=tk.BooleanVar(value=True)
        self.opt_kb=tk.BooleanVar(value=True)
        self.opt_rev=tk.BooleanVar(value=True)
        self.opt_dbl=tk.BooleanVar(value=False)
        self.opt_pre=tk.BooleanVar(value=True)
        self.opt_sep=tk.BooleanVar(value=True)
        opts=[(self.opt_common,"⚡ Common word combos"),(self.opt_kb,"⌨  Keyboard walks"),
              (self.opt_rev,"↩  Reversed words"),(self.opt_dbl,"✌  Doubled words"),
              (self.opt_pre,"⬅  Prefix mutations"),(self.opt_sep,"🔗 Separator combos")]
        for i,(var,lbl) in enumerate(opts):
            tk.Checkbutton(mf,text=lbl,variable=var,bg="#0b140b",fg="#7fff7f",
                           selectcolor="#001a00",activebackground="#0b140b",
                           activeforeground="#00ff41",font=("Courier New",10),
                           anchor="w",cursor="hand2").grid(row=i//2,column=i%2,sticky="w",pady=3,padx=4)

        of=self._sec(f,"Output File"); of.pack(fill="x")
        orow=tk.Frame(of,bg="#0b140b"); orow.pack(fill="x")
        self._lbl(orow,"Filename:").pack(side="left")
        self.out_file=tk.StringVar(value="fuxy_wordlist.txt")
        tk.Entry(orow,textvariable=self.out_file,bg="#0a0f0a",fg="#7fff7f",
                 insertbackground="#00ff41",font=("Courier New",10),relief="flat",
                 highlightthickness=1,highlightbackground="#1e5c1e",width=32).pack(side="left",padx=8)
        tk.Button(orow,text="Browse",command=self._browse,bg="#001500",fg="#00aa33",
                  relief="flat",font=("Courier New",9),cursor="hand2").pack(side="left")

    def _tab_output(self,tab):
        f=tk.Frame(tab,bg="#060b06"); f.pack(fill="both",expand=True,padx=12,pady=8)
        info=tk.Frame(f,bg="#060b06"); info.pack(fill="x",pady=(0,6))
        self.count_lbl=tk.Label(info,text="[ 0 passwords ]",bg="#060b06",fg="#00ff88",font=("Courier New",11,"bold"))
        self.count_lbl.pack(side="left")
        self.pb=ttk.Progressbar(info,mode="indeterminate",length=180); self.pb.pack(side="right")
        self.box=tk.Text(f,bg="#040804",fg="#00cc44",font=("Courier New",10),relief="flat",
                         insertbackground="#00ff41",selectbackground="#003300",
                         highlightthickness=1,highlightbackground="#0a220a",wrap="none")
        vs=tk.Scrollbar(f,orient="vertical",command=self.box.yview)
        hs=tk.Scrollbar(f,orient="horizontal",command=self.box.xview)
        self.box.configure(yscrollcommand=vs.set,xscrollcommand=hs.set)
        vs.pack(side="right",fill="y"); hs.pack(side="bottom",fill="x"); self.box.pack(fill="both",expand=True)

    def _gen_thread(self):
        self.pb.start(10); self.status.config(text="Generating...",fg="#ffcc00")
        Thread(target=self._do_gen,daemon=True).start()

    def _do_gen(self):
        try: mn,mx=int(self.min_len.get()),int(self.max_len.get())
        except: mn,mx=6,20
        data={k:v.get().strip() for k,v in self.vars.items()}
        if not any(data.values()):
            self.root.after(0,lambda:messagebox.showwarning("FUXY","Fill in at least one field."))
            self.root.after(0,self._stop_pb); return
        pwds=generate(data,mn,mx,include_common=self.opt_common.get(),
                      include_keyboard=self.opt_kb.get(),include_reverse=self.opt_rev.get(),
                      include_double=self.opt_dbl.get(),include_prefixes=self.opt_pre.get(),
                      include_separators=self.opt_sep.get())
        self.passwords=pwds
        self.root.after(0,lambda:self._show(pwds))

    def _show(self,pwds):
        self.pb.stop(); self.box.delete("1.0","end"); self.box.insert("end","\n".join(pwds))
        self.count_lbl.config(text=f"[ {len(pwds):,} passwords ]")
        self.status.config(text=f"Done! {len(pwds):,} passwords generated.",fg="#00ff41")

    def _stop_pb(self): self.pb.stop(); self.status.config(text="Ready.",fg="#2a6a2a")

    def _save(self):
        if not self.passwords: messagebox.showwarning("FUXY","Generate first!"); return
        path=filedialog.asksaveasfilename(defaultextension=".txt",
             filetypes=[("Text","*.txt"),("All","*.*")],initialfile=self.out_file.get())
        if path:
            save_wordlist(self.passwords,path)
            self.status.config(text=f"Saved: {os.path.basename(path)}",fg="#00ff88")
            messagebox.showinfo("FUXY",f"✔ {len(self.passwords):,} passwords saved to:\n{path}")

    def _browse(self):
        path=filedialog.asksaveasfilename(defaultextension=".txt",
             filetypes=[("Text","*.txt"),("All","*.*")],initialfile=self.out_file.get())
        if path: self.out_file.set(path)

    def _clear(self):
        [v.set("") for v in self.vars.values()]
        self.box.delete("1.0","end"); self.passwords=[]
        self.count_lbl.config(text="[ 0 passwords ]"); self.status.config(text="Cleared.",fg="#2a6a2a")

    def run(self): self.root.mainloop()


# ══ CLI ══════════════════════════════════════
def ask(p,d=""): v=input(f"  {G}>{W} {DG}{p}{W}: ").strip(); return v or d
def yn(p): return input(f"  {G}>{W} {DG}{p} [Y/n]{W}: ").strip().lower()!="n"

def cli_interactive():
    clear()
    print(f"""{G}{B}
  ███████╗██╗   ██╗██╗  ██╗██╗   ██╗
  ██╔════╝██║   ██║╚██╗██╔╝╚██╗ ██╔╝
  █████╗  ██║   ██║ ╚███╔╝  ╚████╔╝ 
  ██╔══╝  ██║   ██║ ██╔██╗   ╚██╔╝  
  ██║     ╚██████╔╝██╔╝ ██╗   ██║   
  ╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   {W}
{DG}  [ FUXY v2.0 · by {G}{B}FAXSON{W}{DG} · CLI Mode ]{W}\n""")
    keys=["name","nickname","dob","partner","pet","child","company","school",
          "hobby","sport","favword","color","car","music","birthplace","username","email_user","phone"]
    prompts=["First name","Nickname","DOB (dd/mm/yyyy)","Partner name","Pet name","Child name",
             "Company","High school","Hobby","Sport","Favourite word","Colour","Car/brand",
             "Favourite artist","Birth city","Username","Email username","Phone digits"]
    print(f"  {DG}┌─ TARGET PROFILE ───────────────────{W}")
    data={k:ask(p) for k,p in zip(keys,prompts)}
    print(f"\n  {DG}┌─ MUTATIONS ────────────────────────{W}")
    opts={"include_common":yn("Common words"),"include_keyboard":yn("Keyboard walks"),
          "include_reverse":yn("Reversed words"),"include_double":yn("Doubled words"),
          "include_prefixes":yn("Prefix mutations"),"include_separators":yn("Separator combos")}
    try: mn,mx=int(ask("Min length","6")),int(ask("Max length","20"))
    except: mn,mx=6,20
    fname=ask("Output filename","fuxy_wordlist.txt")
    print(f"\n  {Y}[*] Generating...{W}")
    pwds=generate(data,mn,mx,**opts)
    if not pwds: print(f"  {R}[!] No passwords generated.{W}"); return
    save_wordlist(pwds,fname)
    print(f"  {G}[+] {B}{len(pwds):,}{W}{G} passwords → {B}{fname}{W}\n")
    if input(f"  {G}>{W} Preview 30? [y/N]: ").strip().lower()=="y":
        [print(f"  {DG}{i:>3}.{W}  {G}{p}{W}") for i,p in enumerate(pwds[:30],1)]
    print(f"\n  {Y}[!] Authorized use only.{W}\n")

def main():
    if "--gui" in sys.argv: FuxyGUI().run(); return
    if "--cli" in sys.argv: cli_interactive(); return
    while True:
        clear()
        print(f"""{G}{B}
  ███████╗██╗   ██╗██╗  ██╗██╗   ██╗
  ██╔════╝██║   ██║╚██╗██╔╝╚██╗ ██╔╝
  █████╗  ██║   ██║ ╚███╔╝  ╚████╔╝ 
  ██╔══╝  ██║   ██║ ██╔██╗   ╚██╔╝  
  ██║     ╚██████╔╝██╔╝ ██╗   ██║   
  ╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝{W}
{DG}  ╔══════════════════════════════════╗
  ║  {G}[1]{DG} Launch GUI Mode               ║
  ║  {G}[2]{DG} Interactive CLI Mode           ║
  ║  {G}[3]{DG} Exit                           ║
  ╚══════════════════════════════════╝{W}""")
        c=input(f"\n  {G}>{W} Select: ").strip()
        if c=="1": FuxyGUI().run()
        elif c=="2": cli_interactive(); input(f"  {DG}Press Enter...{W}")
        elif c=="3": print(f"\n  {G}[*] FUXY by FAXSON — Stay legal.{W}\n"); break

if __name__=="__main__":
    main()
