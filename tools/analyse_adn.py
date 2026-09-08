import os, tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from ged4py.parser import GedcomReader


class GedcomApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analyse GEDCOM & CSV")
        self.root.geometry("600x380")
        self.file_path, self.search_mode, self.min_age = tk.StringVar(), tk.StringVar(value="id"), tk.IntVar(value=0)
        self.df_results = None
        self.create_widgets()

    def create_widgets(self):
        f_frame = ttk.LabelFrame(self.root, text=" 1. Fichier (GEDCOM ou CSV) ", padding=5)
        f_frame.pack(fill="x", padx=15, pady=5)
        tk.Entry(f_frame, textvariable=self.file_path, width=45).pack(side="left", padx=5, expand=True, fill="x")
        tk.Button(f_frame, text="Ouvrir", command=self.browse_file).pack(side="right", padx=5)

        filter_frame = ttk.LabelFrame(self.root, text=" 2. Âge minimum au décès ", padding=5)
        filter_frame.pack(fill="x", padx=15, pady=5)
        tk.Scale(filter_frame, from_=0, to=50, variable=self.min_age, orient="horizontal").pack(fill="x", padx=5)

        self.p_frame = ttk.LabelFrame(self.root, text=" 3. Racine (GEDCOM uniquement) ", padding=5)
        self.p_frame.pack(fill="x", padx=15, pady=5)
        r_frame = tk.Frame(self.p_frame)
        r_frame.pack(anchor="w")
        tk.Radiobutton(r_frame, text="ID (ex: I1)", variable=self.search_mode, value="id",
                       command=self.toggle_inputs).pack(side="left", padx=10)
        tk.Radiobutton(r_frame, text="Nom", variable=self.search_mode, value="name", command=self.toggle_inputs).pack(
            side="left")

        self.input_frame = tk.Frame(self.p_frame)
        self.input_frame.pack(fill="x", pady=5)
        self.lbl_id, self.ent_id = tk.Label(self.input_frame, text="ID :"), tk.Entry(self.input_frame)
        self.lbl_fn, self.ent_fn = tk.Label(self.input_frame, text="Prénom :"), tk.Entry(self.input_frame)
        self.lbl_ln, self.ent_ln = tk.Label(self.input_frame, text="Nom :"), tk.Entry(self.input_frame)
        self.toggle_inputs()

        # Actions (Zone des boutons du bas)
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=15, pady=10)

        tk.Button(btn_frame, text="Aide", bg="#7F8C8D", fg="white", font=("Arial", 10, "bold"),
                  height=2, command=self.show_help).pack(side="left", padx=5)

        tk.Button(btn_frame, text="Graphique", bg="#4A90E2", fg="white", font=("Arial", 10, "bold"),
                  height=2, command=self.run_analysis).pack(side="left", fill="x", expand=True, padx=5)

        self.btn_export = tk.Button(btn_frame, text="Exporter CSV", bg="#2ECC71", fg="white",
                                    font=("Arial", 10, "bold"),
                                    height=2, state="disabled", command=self.export_data)
        self.btn_export.pack(side="right", fill="x", expand=True, padx=5)

    def browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("GEDCOM/CSV", "*.ged;*.csv")])
        if f:
            self.file_path.set(f)
            if f.lower().endswith('.csv'):
                self.p_frame.pack_forget()
            else:
                self.p_frame.pack(fill="x", padx=15, pady=5)

    def toggle_inputs(self):
        for w in self.input_frame.winfo_children(): w.grid_forget()
        if self.search_mode.get() == "id":
            self.lbl_id.grid(row=0, column=0);
            self.ent_id.grid(row=0, column=1, sticky="ew")
            self.input_frame.columnconfigure(1, weight=1)
        else:
            self.lbl_fn.grid(row=0, column=0);
            self.ent_fn.grid(row=0, column=1, sticky="ew")
            self.lbl_ln.grid(row=0, column=2);
            self.ent_ln.grid(row=0, column=3, sticky="ew")
            self.input_frame.columnconfigure(1, weight=1);
            self.input_frame.columnconfigure(3, weight=1)

    def _get_year(self, record, path):
        d = record.sub_tag_value(path)
        if not d: return None
        for w in reversed(str(d).split()):
            if w.isdigit() and len(w) == 4: return int(w)
        return None

    def run_analysis(self):
        path = self.file_path.get()
        if not path or not os.path.exists(path): return

        if path.lower().endswith('.csv'):
            try:
                self.df_results = pd.read_csv(path, sep=';', encoding='utf-8-sig')
                if "Age" not in self.df_results.columns: self.df_results = pd.read_csv(path, sep=',')
            except Exception as e:
                messagebox.showerror("Erreur CSV", str(e)); return
        else:
            try:
                with GedcomReader(path) as r:
                    target = None
                    if self.search_mode.get() == "id":
                        uid = self.ent_id.get().strip().strip('@')
                        for i in r.records0("INDI"):
                            if i.xref_id and i.xref_id.strip('@') == uid: target = i; break
                    else:
                        fn, ln = self.ent_fn.get().strip().lower(), self.ent_ln.get().strip().lower()
                        for i in r.records0("INDI"):
                            nv = str(i.sub_tag_value('NAME') or '').lower()
                            if fn in nv and ln in nv: target = i; break

                    if not target: messagebox.showerror("Erreur", "Racine non trouvée."); return

                    rel_cm = {
                        'd1': (2613, "Parents"), 'd2': (1754, "Grands-Parents"), 'd3': (887, "Arrière-GP"),
                        'd4': (420, "AAGrand-Parents"), 'fs': (2613, "Frères / Sœurs"), 'ot': (1349, "Oncles / Tantes"),
                        'got': (680, "Grands-Oncles"), 'cg': (866, "Cousins")
                    }
                    data, seen = [], set()

                    def add_p(p, k):
                        if not p or p.xref_id in seen or p.xref_id == target.xref_id: return
                        seen.add(p.xref_id)
                        b, d = self._get_year(p, 'BIRT/DATE'), self._get_year(p, 'DEAT/DATE')
                        if b and d and (0 <= d - b <= 115):
                            n = str(p.sub_tag_value('NAME') or 'Inconnu').replace('/', '').strip()
                            cm, lbl = rel_cm.get(k, (0, ""))
                            if cm: data.append({"Nom": n, "cM": cm, "Age": d - b, "Relation": lbl})

                    famc = target.sub_tag('FAMC', follow=True)
                    if famc:
                        for c in famc.sub_tags('CHIL', follow=True): add_p(c, 'fs')
                        for p1 in [famc.sub_tag('HUSB', follow=True), famc.sub_tag('WIFE', follow=True)]:
                            if not p1: continue
                            add_p(p1, 'd1')
                            famc2 = p1.sub_tag('FAMC', follow=True)
                            if famc2:
                                for c2 in famc2.sub_tags('CHIL', follow=True):
                                    if c2 and c2.xref_id != p1.xref_id:
                                        add_p(c2, 'ot')
                                        for f_ot in c2.sub_tags('FAMS', follow=True):
                                            if f_ot:
                                                for cos in f_ot.sub_tags('CHIL', follow=True): add_p(cos, 'cg')
                                for p2 in [famc2.sub_tag('HUSB', follow=True), famc2.sub_tag('WIFE', follow=True)]:
                                    if not p2: continue
                                    add_p(p2, 'd2')
                                    famc3 = p2.sub_tag('FAMC', follow=True)
                                    if famc3:
                                        for c3 in famc3.sub_tags('CHIL', follow=True):
                                            if c3 and c3.xref_id != p2.xref_id: add_p(c3, 'got')
                                        for p3 in [famc3.sub_tag('HUSB', follow=True),
                                                   famc3.sub_tag('WIFE', follow=True)]:
                                            if not p3: continue
                                            add_p(p3, 'd3')
                                            famc4 = p3.sub_tag('FAMC', follow=True)
                                            if famc4:
                                                for p4 in [famc4.sub_tag('HUSB', follow=True),
                                                           famc4.sub_tag('WIFE', follow=True)]: add_p(p4, 'd4')
                self.df_results = pd.DataFrame(data)
            except Exception as e:
                messagebox.showerror("Erreur", str(e)); return

        if self.df_results is None or self.df_results.empty: return
        df_f = self.df_results[self.df_results["Age"] >= self.min_age.get()]
        if df_f.empty: return

        self.btn_export.config(state="normal" if not path.lower().endswith('.csv') else "disabled")

        plt.figure(figsize=(10, 5))
        jitter = np.random.uniform(-35, 35, size=len(df_f))
        cats = df_f["Relation"].unique()
        colors = plt.get_cmap("tab10", len(cats))

        for idx, cat in enumerate(cats):
            m = (df_f["Relation"] == cat)
            plt.scatter(df_f.loc[m, "cM"] + jitter[m], df_f.loc[m, "Age"], alpha=0.8, edgecolors='black', s=80,
                        label=cat, color=colors(idx))

        plt.axhline(df_f["Age"].mean(), color='red', linestyle='--', label=f'Moyenne ({df_f["Age"].mean():.1f} ans)')
        st = df_f.groupby("cM")["Age"].mean().sort_index()
        plt.plot(st.index, st.values, color='black', marker='x', linestyle=':', label='Tendance')

        # Modifie le titre de la barre de la fenêtre Windows/Mac
        plt.gcf().canvas.manager.set_window_title("Longévité Familiale et Distance Génétique")

        plt.gca().invert_xaxis()
        plt.title(f"Durée de vie et Proximité ADN (Seuil : {self.min_age.get()} ans)")
        plt.xlabel("ADN (cM)")
        plt.ylabel("Âge au décès")
        ticks = sorted(list(df_f["cM"].unique()), reverse=True)
        plt.xticks(ticks, [f"{int(t)} cM" for t in ticks], rotation=45)
        plt.grid(True, linestyle=':', alpha=0.5)
        # plt.legend(loc='lower left', fontsize=9);
        # Positionne la légende à l'extérieur droit, centrée verticalement
        plt.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=9, borderaxespad=0)
        plt.tight_layout()
        plt.show()

    def export_data(self):
        if self.df_results is None or self.df_results.empty: return
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if f:
            self.df_results.sort_values(by="cM", ascending=False).to_csv(f, index=False, sep=';', encoding='utf-8-sig')

        messagebox.showinfo("Exporté", "Fichier sauvegardé. Modifiez-le puis rechargez-le dans l'application.")

    def show_help(self):
        """Affiche une fenêtre pop-up d'aide détaillée avec un bouton Fermer."""
        help_win = tk.Toplevel(self.root)
        help_win.title("Aide & Fonctionnalités")
        help_win.geometry("500x380")
        help_win.resizable(False, False)

        # Rend la fenêtre d'aide modale (bloque la fenêtre principale)
        help_win.transient(self.root)
        help_win.grab_set()

        # Texte d'explication des fonctionnalités
        help_text = (
            "=== ANALYSE DE LA LONGÉVITÉ ET PROXIMITÉ ADN ===\n\n"
            "Ce programme permet de croiser la durée de vie des membres de votre famille "
            "avec la quantité théorique d'ADN (en cM) qu'ils partagent avec une personne racine.\n\n"
            "FONCTIONNALITÉS COMPLÈTES :\n"
            "• Support Double Format : Charge un fichier généalogique GEDCOM brut (.ged) "
            "OU un fichier tableur CSV (.csv) préalablement exporté.\n"
            "• Exploration Élargie : Analyse la lignée directe ainsi que les branches collatérales "
            "(frères/sœurs, oncles/tantes, grands-oncles, cousins germains).\n"
            "• Filtre Anti-Biais : Le curseur d'âge permet d'exclure la mortalité infantile "
            "pour ne pas fausser les moyennes de longévité adulte.\n"
            "• Mode CSV Correctif : Exporter en CSV vous permet de compléter manuellement "
            "l'âge actuel de vos proches vivants dans Excel (pour éliminer le biais "
            "des personnes vivantes), puis de réimporter ce CSV pour un graphique parfait.\n\n"
            "COMMENT L'UTILISER :\n"
            "1. Sélectionnez votre fichier (.ged ou .csv).\n"
            "2. Ajustez le filtre d'âge minimum au décès si nécessaire.\n"
            "3. (GEDCOM uniquement) Saisissez l'ID ou le Nom de la personne racine.\n"
            "4. Cliquez sur 'Graphique' pour visualiser ou 'Exporter CSV' pour éditer."
        )

        # Zone de texte
        txt_label = tk.Label(help_win, text=help_text, justify="left", wraplength=460, font=("Arial", 9))
        txt_label.pack(padx=20, pady=20, expand=True, fill="both")

        # Bouton Fermer
        tk.Button(help_win, text="Fermer l'aide", command=help_win.destroy,
                  bg="#D35400", fg="white", font=("Arial", 10, "bold"), width=15).pack(pady=15)


if __name__ == "__main__":
    root = tk.Tk()
    app = GedcomApp(root)
    root.mainloop()
