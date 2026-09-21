import os, configparser, tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from ged4py.parser import GedcomReader


class GedcomApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analyse GEDCOM & CSV")
        self.root.geometry("600x480")
        self.root.resizable(False, False)
        self.df_results = None

        # --- 1. CONFIGURATION DES VALEURS PAR DÉFAUT PAR DÉFAUT ---
        default_file = ""
        default_mode = "id"
        default_min_age = 0
        default_vivant_inf = 55
        default_vivant_sup = 95

        # --- 2. LECTURE DU FICHIER .INI S'IL EXISTE ---
        # config_path = "config.ini"
        # if os.path.exists(config_path):
        #     try:
        #         config = configparser.ConfigParser()
        #         config.read(config_path, encoding='utf-8')
        #
        #         # Récupération des variables avec repli automatique si une clé manque
        #         if config.has_section('DEFAULT') or config.defaults():
        #             sections = config['DEFAULT']
        #             default_file = sections.get('gedcom_path', default_file)
        #             default_mode = sections.get('search_mode', default_mode)
        #             default_min_age = sections.getint('min_age', default_min_age)
        #             default_vivant_inf = sections.getint('vivant_inf', default_vivant_inf)
        #             default_vivant_sup = sections.getint('vivant_sup', default_vivant_sup)
        #     except Exception as e:
        #         # Si le fichier .ini est mal formaté, on affiche une alerte discrète et on continue
        #         print(f"Erreur de lecture du fichier config.ini : {e}")

        # --- 3. INITIALISATION DES VARIABLES TKINTER AVEC LES VALEURS RETENUES ---
        self.file_path = tk.StringVar(value=default_file)
        self.search_mode = tk.StringVar(value=default_mode)
        self.min_age = tk.IntVar(value=default_min_age)
        self.vivant_inf = tk.IntVar(value=default_vivant_inf)
        self.vivant_sup = tk.IntVar(value=default_vivant_sup)

        # Variable pour mémoriser si l'utilisateur souhaite enregistrer ses paramètres
        self.save_config_on_run = tk.BooleanVar(value=False)

        self.create_widgets()

    def create_widgets(self):

        f_frame = ttk.LabelFrame(self.root, text=" 1. Fichier (GEDCOM ou CSV) ", padding=5)
        f_frame.pack(fill="x", padx=15, pady=5)
        tk.Entry(f_frame, textvariable=self.file_path, width=45).pack(side="left", padx=5, expand=True, fill="x")
        tk.Button(f_frame, text="Ouvrir", command=self.browse_file).pack(side="right", padx=5)

        filter_frame = ttk.LabelFrame(self.root, text=" 2. Âge minimum au décès ", padding=5)
        filter_frame.pack(fill="x", padx=15, pady=5)
        tk.Scale(filter_frame, from_=0, to=50, variable=self.min_age, orient="horizontal").pack(fill="x", padx=5)

        # Variables Tkinter à ajouter dans le __init__ ou au début de create_widgets
        self.vivant_inf = tk.IntVar(value=55)
        self.vivant_sup = tk.IntVar(value=95)

        # Remplacement du bloc de filtres
        filter_frame = ttk.LabelFrame(self.root, text=" 3. Filtres Démographiques (Vivants) ", padding=5)
        filter_frame.pack(fill="x", padx=15, pady=5)

        # Grille interne pour aligner les 3 curseurs
        f_grid = tk.Frame(filter_frame)
        f_grid.pack(fill="x", expand=True)

        tk.Label(f_grid, text="Vivants âges mini :", font=("Arial", 8)).grid(row=0, column=2, padx=2, sticky="w")
        tk.Scale(f_grid, from_=0, to=110, variable=self.vivant_inf, orient="horizontal", length=120).grid(row=0,
                                                                                                          column=3,
                                                                                                          padx=5)

        tk.Label(f_grid, text="Vivants âges maxi :", font=("Arial", 8)).grid(row=0, column=4, padx=2, sticky="w")
        tk.Scale(f_grid, from_=0, to=110, variable=self.vivant_sup, orient="horizontal", length=120).grid(row=0,
                                                                                                          column=5,
                                                                                                          padx=5)

        self.p_frame = ttk.LabelFrame(self.root, text=" 4. Racine (GEDCOM uniquement) ", padding=5)
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

        # Option de sauvegarde à la demande
        save_frame = tk.Frame(filter_frame)
        save_frame.pack(fill="x", pady=(5, 0), anchor="w")

        tk.Checkbutton(save_frame, text="Mémoriser ces réglages par défaut dans config.ini lors de l'analyse",
                       variable=self.save_config_on_run, font=("Arial", 9)).pack(side="left", padx=5)

        # === Zone des boutons du bas (Version Finale Alignée à la perfection) ===
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=15, pady=10)

        # --- LIGNE 1 : Le sélecteur de graphique (Combobox) ---
        g_frame = tk.Frame(btn_frame)
        g_frame.pack(fill="x", pady=(0, 8))

        tk.Label(g_frame, text="Type de graphique :", font=("Arial", 10)).pack(side="left", padx=5)

        self.graph_selector = ttk.Combobox(g_frame, state="readonly", font=("Arial", 10))
        self.graph_selector['values'] = (
            "Proximité ADN (cM)",
            "Chronologique (Années de naissance)",
            "Répartition des âges au décès"
        )
        self.graph_selector.current(0)
        self.graph_selector.pack(side="left", fill="x", expand=True, padx=5)

        # --- LIGNE 2 : Vos 3 boutons d'origine (Rétablissement des proportions exactes) ---
        ctrl_frame = tk.Frame(btn_frame)
        ctrl_frame.pack(fill="x", pady=5)

        # Bouton Aide à gauche (Taille fixe)
        tk.Button(ctrl_frame, text="Aide", bg="#7F8C8D", fg="white", font=("Arial", 10, "bold"),
                  height=2, command=self.show_help).pack(side="left", padx=5)

        # Bouton Graphique au centre (Expansé et identique à votre version d'origine)
        tk.Button(ctrl_frame, text="Graphique", bg="#4A90E2", fg="white", font=("Arial", 10, "bold"),
                  height=2, command=self.trigger_selected_graph).pack(side="left", fill="x", expand=True, padx=5)

        # Bouton Exporter CSV à droite (Expansé et identique à votre version d'origine)
        self.btn_export = tk.Button(ctrl_frame, text="Exporter CSV", bg="#2ECC71", fg="white",
                                    font=("Arial", 10, "bold"), height=2, state="disabled", command=self.export_data)
        self.btn_export.pack(side="right", fill="x", expand=True, padx=5)

        # Force l'interface à s'ajuster si un fichier par défaut a été chargé via le .ini
        if self.file_path.get().lower().endswith('.csv'):
            self.p_frame.pack_forget()

    def browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("GEDCOM/CSV", "*.ged;*.csv")])
        if f:
            self.file_path.set(f)
            if f.lower().endswith('.csv'):
                self.p_frame.pack_forget()
            else:
                self.p_frame.pack(fill="x", padx=15, pady=5)

            # --- LECTURE DU .INI DANS LE DOSSIER DU FICHIER CHOISI ---
            dossier_source = os.path.dirname(f)
            config_path = os.path.join(dossier_source, "config.ini")

            if os.path.exists(config_path):
                try:
                    config = configparser.ConfigParser()
                    config.read(config_path, encoding='utf-8')

                    if config.has_section('DEFAULT') or config.defaults():
                        sections = config['DEFAULT']

                        # 1. Restauration des filtres et du mode de recherche
                        self.search_mode.set(sections.get('search_mode', self.search_mode.get()))
                        self.min_age.set(sections.getint('min_age', self.min_age.get()))
                        self.vivant_inf.set(sections.getint('vivant_inf', self.vivant_inf.get()))
                        self.vivant_sup.set(sections.getint('vivant_sup', self.vivant_sup.get()))

                        # 2. Restauration des textes saisis par l'utilisateur
                        # On vide d'abord les champs, puis on injecte la valeur sauvegardée
                        self.ent_id.delete(0, tk.END)
                        self.ent_id.insert(0, sections.get('saved_id', ''))

                        self.ent_fn.delete(0, tk.END)
                        self.ent_fn.insert(0, sections.get('saved_firstname', ''))

                        self.ent_ln.delete(0, tk.END)
                        self.ent_ln.insert(0, sections.get('saved_lastname', ''))

                        # 3. CORRECTION DU BUG VISUEL : Force Tkinter à rafraîchir la ligne de saisie
                        self.toggle_inputs()

                except Exception as e:
                    print(f"Erreur de lecture du fichier config.ini local : {e}")

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

    def trigger_selected_graph(self):
        """Récupère le choix de la liste déroulante et le traduit en mot-clé pour run_analysis."""
        selection = self.graph_selector.get()
        if selection == "Proximité ADN (cM)":
            self.run_analysis("adn")
        elif selection == "Chronologique (Années de naissance)":
            self.run_analysis("temps")
        elif selection == "Répartition des âges au décès":
            self.run_analysis("repartition")

    def run_analysis(self, graph_type="adn"):
        path = self.file_path.get()
        if not path or not os.path.exists(path): return

        # --- SAUVEGARDE À LA DEMANDE DANS LE DOSSIER DU FICHIER EN COURS ---
        if self.save_config_on_run.get():
            try:
                dossier_source = os.path.dirname(path)
                config_path = os.path.join(dossier_source, "config.ini")

                config = configparser.ConfigParser()
                config['DEFAULT'] = {
                    'search_mode': self.search_mode.get(),
                    'min_age': str(self.min_age.get()),
                    'vivant_inf': str(self.vivant_inf.get()),
                    'vivant_sup': str(self.vivant_sup.get()),
                    # Sauvegarde des valeurs textuelles des zones de saisie
                    'saved_id': self.ent_id.get().strip(),
                    'saved_firstname': self.ent_fn.get().strip(),
                    'saved_lastname': self.ent_ln.get().strip()
                }
                with open(config_path, "w", encoding="utf-8") as configfile:
                    config.write(configfile)
            except Exception as e:
                print(f"Impossible de sauvegarder la configuration locale : {e}")

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

                    # Extraction du nom de la personne racine pour le titre
                    target_name = str(target.sub_tag_value('NAME') or 'Inconnu').replace('/', '').strip()

                    rel_cm = {
                        'd1': (2613, "Parents"), 'd2': (1754, "Grands-Parents"), 'd3': (875, "Arrière-GP"),
                        'd4': (420, "AAGrand-Parents"), 'fs': (2613, "Frères / Sœurs"), 'ot': (1349, "Oncles / Tantes"),
                        'got': (680, "Grands-Oncles"), 'cg': (875, "Cousins")
                    }
                    data, seen = [], set()

                    import datetime
                    annee_actuelle = datetime.date.today().year

                    # Récupération des valeurs des curseurs Tkinter
                    limite_inf = self.vivant_inf.get()
                    limite_sup = self.vivant_sup.get()

                    def add_p(p, k):
                        if not p or p.xref_id in seen or p.xref_id == target.xref_id: return
                        seen.add(p.xref_id)

                        b = self._get_year(p, 'BIRT/DATE')
                        d = self._get_year(p, 'DEAT/DATE')

                        est_vivant = False  # Indicateur pour la traçabilité
                        if b:
                            if d:
                                age = d - b
                            else:
                                age = annee_actuelle - b
                                # Utilisation des curseurs Tkinter pour filtrer les vivants
                                if limite_inf <= age <= limite_sup:
                                    est_vivant = True  # La personne est vivante et validée par les curseurs
                                else:
                                    return  # Rejet immédiat si en dehors des curseurs dynamiques

                            # Validation finale et enregistrement (filtre mortalité infantile générale)
                            if age >= self.min_age.get() and 0 <= age <= 115:
                                n = str(p.sub_tag_value('NAME') or 'Inconnu').replace('/', '').strip()
                                g = str(p.sub_tag_value('SEX') or 'Inconnu').upper()
                                cm, lbl = rel_cm.get(k, (0, ""))

                                # AJOUT DE LA MENTION : Si la personne est vivante, on modifie son étiquette
                                if est_vivant:
                                    lbl = f"{lbl} (Vivant)"

                                if cm:
                                    data.append({
                                        "Nom": n,
                                        "cM": cm,
                                        "Age": age,
                                        "Relation": lbl,
                                        "Genre": g,
                                        "Naissance": b  # Ajout indispensable pour le graphe chronologique
                                    })

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

        # =====================================================================
        # BLOC GRAPHIQUE FINAL (À SITUER JUSTE APRÈS LA SORTIE DU BLOC ELSE)
        # =====================================================================
        if self.df_results is None or self.df_results.empty: return

        # Application du filtre dynamique (Mortalité infantile)
        df_f = self.df_results[self.df_results["Age"] >= self.min_age.get()]
        if df_f.empty: return

        # Gestion de l'activation du bouton d'export
        self.btn_export.config(state="normal" if not path.lower().endswith('.csv') else "disabled")

        # Initialisation de la figure Matplotlib
        plt.figure(figsize=(11, 6))
        cats = df_f["Relation"].unique()
        colors = plt.get_cmap("tab10", len(cats))

        # Dictionnaire pour verrouiller les couleurs identiques sur les 3 graphiques
        color_map = {cat: colors(i) for i, cat in enumerate(cats)}

        # --- OPTION 1 : GRAPHIQUE ADN CLASSIQUE (cM) ---
        if graph_type == "adn":
            plt.gcf().canvas.manager.set_window_title("Longévité Familiale et Distance Génétique")
            jitter = np.random.uniform(-35, 35, size=len(df_f))
            for cat in cats:
                m = (df_f["Relation"] == cat)
                plt.scatter(df_f.loc[m, "cM"] + jitter[m], df_f.loc[m, "Age"], alpha=0.75, edgecolors='black', s=80,
                            label=cat, color=color_map[cat])

            # Lignes de tendances et moyennes Hommes / Femmes (Les 4 lignes)
            df_h, df_fem = df_f[df_f["Genre"] == "M"], df_f[df_f["Genre"] == "F"]
            if not df_h.empty:
                plt.axhline(df_h["Age"].mean(), color='royalblue', linestyle='--', linewidth=1.5,
                            label=f'Moy. Hommes ({df_h["Age"].mean():.1f} ans)')
                st_h = df_h.groupby("cM")["Age"].mean().sort_index()
                plt.plot(st_h.index, st_h.values, color='royalblue', marker='o', linestyle='-', linewidth=2,
                         label='Tendance Hommes')
            if not df_fem.empty:
                plt.axhline(df_fem["Age"].mean(), color='darkviolet', linestyle='--', linewidth=1.5,
                            label=f'Moy. Femmes ({df_fem["Age"].mean():.1f} ans)')
                st_fem = df_fem.groupby("cM")["Age"].mean().sort_index()
                plt.plot(st_fem.index, st_fem.values, color='darkviolet', marker='o', linestyle='-', linewidth=2,
                         label='Tendance Femmes')

            plt.gca().invert_xaxis()
            plt.title(f"Durée de vie en fonction de la proximité ADN (Seuil : {self.min_age.get()} ans)",
                      fontweight='bold', pad=15)
            plt.xlabel("ADN théorique (cM)")
            plt.ylabel("Âge au décès")
            ticks = sorted(list(df_f["cM"].unique()), reverse=True)
            plt.xticks(ticks, [f"{int(t)} cM" for t in ticks], rotation=45)

        # --- OPTION 2 : GRAPHIQUE CHRONOLOGIQUE (Année de Naissance) ---
        elif graph_type == "temps":
            plt.gcf().canvas.manager.set_window_title("Évolution Historique de la Longévité")
            jitter_y = np.random.uniform(-1, 1, size=len(df_f))
            for cat in cats:
                m = (df_f["Relation"] == cat)
                if "Naissance" in df_f.columns:
                    plt.scatter(df_f.loc[m, "Naissance"], df_f.loc[m, "Age"] + jitter_y[m], alpha=0.75,
                                edgecolors='black', s=80, label=cat, color=color_map[cat])

            # Évolution globale par décennie
            if "Naissance" in df_f.columns and len(df_f) > 5:
                df_f['Decennie'] = (df_f['Naissance'] // 10) * 10
                trend = df_f.groupby('Decennie')['Age'].mean().sort_index()
                plt.plot(trend.index, trend.values, color='black', linestyle='-', linewidth=2.5, marker='X',
                         label='Moyenne globale / décennie')

            plt.title(f"Évolution de la longévité selon l'année de naissance - Racine : {target_name}",
                      fontweight='bold', pad=15)
            plt.xlabel("Année de naissance");
            plt.ylabel("Âge au décès (années)")

        # --- OPTION 3 : RÉPARTITION DES ÂGES AU DÉCÈS PAR GROUPE ---
        elif graph_type == "repartition":
            plt.gcf().canvas.manager.set_window_title("Analyse des Seuils de Décès par Branche")
            jitter_y = np.random.uniform(-0.15, 0.15, size=len(df_f))
            for i, cat in enumerate(cats):
                m = (df_f["Relation"] == cat)
                plt.scatter(df_f.loc[m, "Age"], np.zeros(sum(m)) + i + jitter_y[m], alpha=0.75, edgecolors='black',
                            s=80, label=cat, color=color_map[cat])

            plt.yticks(range(len(cats)), cats)
            plt.title(f"Distribution des âges au décès par groupe de parenté - Racine : {target_name}",
                      fontweight='bold', pad=15)
            plt.xlabel("Âge au décès (années)");
            plt.ylabel("Groupes de parenté")

        # Mise en forme globale de la fenêtre de graphique
        plt.grid(True, linestyle=':', alpha=0.5)
        plt.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=9, borderaxespad=0)
        plt.tight_layout()

        # =====================================================================
        # INFOBULLES INTERACTIVES LIÉES AU CURSEUR DE LA SOURIS
        # =====================================================================
        # On configure la bulle pour qu'elle se positionne en pixels par rapport à la figure globale

        annot = plt.gca().annotate("", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
                                   xycoords="figure pixels",  # Alignement absolu sur l'écran
                                   bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.9),
                                   arrowprops=dict(arrowstyle="->", color="black", lw=0.5))
        annot.set_visible(False)

        # Extraction robuste des collections de points (PathCollection) de Matplotlib
        from matplotlib.collections import PathCollection
        scatters = [child for child in plt.gca().get_children() if
                    isinstance(child, PathCollection) and child.get_label() not in ['_nolegend_', 'Tendance Hommes',
                                                                                    'Tendance Femmes',
                                                                                    'Moyenne globale / décennie']]

        def update_annot(scat, ind, event):
            """Met à jour le texte et la position de l'infobulle selon le curseur sur les deux axes."""
            idx = ind["ind"][0]  # Récupère le premier index détecté

            # Ancrage absolu de la flèche sur les coordonnées pixels de la souris
            annot.xy = (event.x, event.y)

            # Récupération de la taille dynamique de la fenêtre (Largeur et Hauteur en pixels)
            bbox = plt.gcf().get_window_extent()
            largeur_fenetre = bbox.width
            hauteur_fenetre = bbox.height

            milieu_x = largeur_fenetre / 2
            milieu_y = hauteur_fenetre / 2

            # --- 1. SÉCURITÉ HORIZONTALE (X) : Évitement de la légende à droite ---
            if event.x > milieu_x:
                offset_x = -15
                align_h = "right"  # Le bloc se déploie à gauche, le texte se cadre à droite
            else:
                offset_x = 15
                align_h = "left"  # Le bloc se déploie à droite, le texte se cadre à gauche

            # --- 2. SÉCURITÉ VERTICALE (Y) : Évitement du plafond / plancher de la fenêtre ---
            if event.y > milieu_y:
                offset_y = -15
                align_v = "top"
            else:
                offset_y = 15
                align_v = "bottom"

            # Application des décalages dynamiques et de l'alignement du bloc
            annot.xytext = (offset_x, offset_y)
            annot.set_ha(align_h)
            annot.set_va(align_v)

            # CONFIGURATION DE L'ALIGNEMENT DU TEXTE À L'INTÉRIEUR DU BLOC
            # Force le texte à se cadrer à droite ou à gauche pour suivre la forme de la bulle
            annot.set_ma("left")

            # Extraction des données textuelles de l'individu survolé
            label = scat.get_label()
            sub_df = df_f[df_f["Relation"] == label]

            if not sub_df.empty and idx < len(sub_df):
                row = sub_df.iloc[idx]
                text = f"Nom : {row['Nom']}\nÂge : {int(row['Age'])} ans\nRelation : {row['Relation']}"
                if "Naissance" in row and not pd.isna(row['Naissance']):
                    text += f"\nNé(e) en : {int(row['Naissance'])}"

                annot.set_text(text)

                # Adapte la couleur de fond et du texte de la bulle selon le groupe survolé
                annot.get_bbox_patch().set_facecolor(scat.get_facecolors()[0])
                annot.get_bbox_patch().set_alpha(0.9)

                # Force le texte en noir ou blanc pour rester lisible sur la couleur du fond
                rgb_color = scat.get_facecolors()[0][:3]
                annot.set_color("black" if np.mean(rgb_color) > 0.5 else "white")

        def hover(event):
            """Gestionnaire de l'événement de survol."""
            vis = annot.get_visible()
            if event.inaxes == plt.gca():
                for scat in scatters:
                    cont, ind = scat.contains(event)
                    if cont:
                        # Correction : Transmission des 3 arguments requis (scat, ind, event)
                        update_annot(scat, ind, event)
                        annot.set_visible(True)
                        plt.gcf().canvas.draw_idle()
                        return
            if vis:
                annot.set_visible(False)
                plt.gcf().canvas.draw_idle()

        # Connexion de la fonction au mouvement global de la souris sur le graphique
        plt.gcf().canvas.mpl_connect("motion_notify_event", hover)

        plt.grid(True, linestyle=':', alpha=0.5)
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
