import os
import re
import time
import fnmatch
import webbrowser
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from bs4 import BeautifulSoup
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic


# ==========================================
# Classe d'Analyse de Distance Géographique
# ==========================================
class AnalyseurDistanceGenealogique:
    def __init__(self, ville_de_ref):
        self.ville_ref = ville_de_ref.strip() if ville_de_ref else ""
        self.coords_ref = None
        self.cache_villes = {}

        if self.ville_ref:
            self.geolocator = Nominatim(user_agent="genealogie_distance_object")
            location = self.geolocator.geocode(self.ville_ref)
            if not location:
                raise ValueError(f"Impossible de localiser la ville de référence : {self.ville_ref}")
            self.coords_ref = (location.latitude, location.longitude)
        else:
            self.geolocator = None

    def find_distance(self, ville_donnee):
        if not self.coords_ref or not ville_donnee:
            return -1

        ville_clean = ville_donnee.strip().lower()
        if ville_clean in self.cache_villes:
            coords_donnee = self.cache_villes[ville_clean]
        else:
            try:
                location = self.geolocator.geocode(ville_donnee)
                if not location:
                    self.cache_villes[ville_clean] = None
                    return -1
                coords_donnee = (location.latitude, location.longitude)
                self.cache_villes[ville_clean] = coords_donnee
                time.sleep(1)
            except Exception:
                return -1

        if coords_donnee is None:
            return -1
        return round(geodesic(self.coords_ref, coords_donnee).km, 2)

    def evaluer_distance_ligne(self, row, zone_application):
        if not self.coords_ref or zone_application == "Aucune":
            return -1

        candidats_villes = []
        if zone_application in ("Naissance", "Tous lieux"):
            if row.get("Lieu Naiss."): candidats_villes.append(row["Lieu Naiss."])
        if zone_application in ("Décès", "Tous lieux"):
            if row.get("Lieu Décès"): candidats_villes.append(row["Lieu Décès"])
        if zone_application in ("Mariage", "Tous lieux"):
            if row.get("Lieu Mariage"): candidats_villes.append(row["Lieu Mariage"])

        if not candidats_villes:
            return -1
        distances = [self.find_distance(v) for v in candidats_villes]
        distances_valides = [d for d in distances if d is not None and d >= 0]
        if not distances_valides:
            return -1
        return min(distances_valides)


# ==========================================
# Application Graphique Tkinter
# ==========================================
class GeneaExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Généa-Extracteur Pro : Géolocalisation & Analyse")
        self.root.geometry("1400x850")

        self.df_global = pd.DataFrame()
        self.repertoire_courant = ""
        self.analyseur_distance = None

        self.fenetre_arbres = None
        self.fenetre_legende = None
        self.fenetre_aide = None
        self.fenetre_remplacement = None
        self.fenetre_progression = None

        self.palette_couleurs = [
            "#F9FBE7", "#EFEBE9", "#E8F5E9", "#E1F5FE", "#FCE4EC",
            "#FFFDE7", "#F3E5F5", "#E0F7FA", "#FFF3E0", "#EDE7F6"
        ]
        self.dept_couleurs = {}

        # --- Configuration HTML ---
        cadre_config = tk.LabelFrame(root, text=" Paramètres de structure HTML ")
        cadre_config.pack(fill="x", padx=10, pady=5)

        self.selectors = {
            "Bloc Ligne": "ligne-resultat",
            "Div Individu": "content-individu",
            "Div Periode": "content-periode",
            "Div Lieu": "content-lieu"
        }
        self.entries = {}
        for i, (label, default) in enumerate(self.selectors.items()):
            tk.Label(cadre_config, text=label + ":").grid(row=i // 2, column=(i % 2) * 2, padx=5, pady=2)
            ent = tk.Entry(cadre_config, width=25)
            ent.insert(0, default)
            ent.grid(row=i // 2, column=(i % 2) * 2 + 1, padx=5, pady=2)
            self.entries[label] = ent

        # --- Dossier et Actions ---
        cadre_action = tk.LabelFrame(root, text=" Dossier et Traitement ")
        cadre_action.pack(fill="x", padx=10, pady=5)

        tk.Button(cadre_action, text="Sélectionner Dossier & Extraire", command=self.process_html,
                  bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10, pady=5)

        self.lbl_repertoire = tk.Label(cadre_action, text="Répertoire actif : Aucun", fg="gray",
                                       font=("Arial", 9, "italic"))
        self.lbl_repertoire.pack(side="left", padx=10)

        tk.Button(cadre_action, text="Aide", command=self.afficher_aide, bg="#FF5722", fg="white",
                  font=("Arial", 9, "bold")).pack(side="right", padx=5)
        tk.Button(cadre_action, text="Légende Départements", command=self.toggle_fenetre_legende, bg="#009688",
                  fg="white").pack(side="right", padx=5)
        tk.Button(cadre_action, text="Gestion Arbres", command=self.toggle_fenetre_arbres, bg="#3F51B5",
                  fg="white").pack(side="right", padx=5)
        tk.Button(cadre_action, text="Rejouer CSV Remplacements", command=self.rejouer_csv_remplacements, bg="#00838F",
                  fg="white").pack(side="right", padx=5)
        tk.Button(cadre_action, text="Remplacer Texte", command=self.ouvrir_fenetre_remplacement, bg="#795548",
                  fg="white").pack(side="right", padx=5)
        tk.Button(cadre_action, text="Exporter CSV", command=self.exporter_csv, bg="#4CAF50", fg="white").pack(
            side="right", padx=5)

        # --- Filtre Géographique & Options Coloriage ---
        cadre_geo = tk.LabelFrame(root, text=" Analyse d'Éloignement Géographique & Coloriage ")
        cadre_geo.pack(fill="x", padx=10, pady=5)

        tk.Label(cadre_geo, text="Cité réf. :").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_ref_ville = tk.Entry(cadre_geo, width=18)
        self.entry_ref_ville.insert(0, "")  # Vide par défaut
        self.entry_ref_ville.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(cadre_geo, text="Zone dist. :").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.zones_possibles = ["Aucune", "Naissance", "Décès", "Mariage", "Tous lieux"]
        self.combo_zone = ttk.Combobox(cadre_geo, values=self.zones_possibles, state="readonly", width=10)
        self.combo_zone.set("Naissance")
        self.combo_zone.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(cadre_geo, text="Dist. Max (km) :").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.entry_max_dist = tk.Entry(cadre_geo, width=6)
        self.entry_max_dist.insert(0, "50")
        self.entry_max_dist.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(cadre_geo, text="Colorer via :").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        self.colonnes_dept_color = ["Dept Naiss.", "Dept Mariage", "Dept Décès"]
        self.combo_col_dept = ttk.Combobox(cadre_geo, values=self.colonnes_dept_color, state="readonly", width=12)
        self.combo_col_dept.set("Dept Naiss.")
        self.combo_col_dept.bind("<<ComboboxSelected>>", lambda e: self.changer_colonne_coloration())
        self.combo_col_dept.grid(row=0, column=7, padx=5, pady=5)

        tk.Button(cadre_geo, text="Filtrer Dist.", command=self.appliquer_filtre_distance, bg="#9C27B0",
                  fg="white").grid(row=0, column=8, padx=10, pady=5)
        tk.Button(cadre_geo, text="Recalculer", command=self.recalculer_distances, bg="#607D8B", fg="white").grid(row=0,
                                                                                                                  column=9,
                                                                                                                  padx=5,
                                                                                                                  pady=5)

        # --- Tableau Principal & Ascenseur ---
        gauche_frame = tk.Frame(root)
        gauche_frame.pack(fill="both", expand=True, padx=10, pady=5)

        barre_outils = tk.Frame(gauche_frame)
        barre_outils.pack(fill="x", pady=2)
        tk.Label(barre_outils, text="Dédoublonner selon :").pack(side="left", padx=5)

        self.colonnes_possibles = [
            "Nom", "Prénoms", "Conjoint Nom", "Conjoint Prénoms",
            "Date Naiss.", "Date Mariage", "Date Décès",
            "Lieu Naiss.", "Dept Naiss.",
            "Lieu Mariage", "Dept Mariage",
            "Lieu Décès", "Dept Décès",
            "Distance", "Arbre"
        ]
        self.col_dedup_var = tk.StringVar(value="Nom")
        self.combo_dedup = ttk.Combobox(barre_outils, textvariable=self.col_dedup_var, values=self.colonnes_possibles,
                                        state="readonly", width=16)
        self.combo_dedup.pack(side="left", padx=5)

        tk.Button(barre_outils, text="Appliquer Dédoublonnage", command=self.appliquer_dedoublonnage, bg="#FF9800",
                  fg="white").pack(side="left", padx=5)
        tk.Button(barre_outils, text="Réinitialiser Vue", command=self.reinitialiser_tableau, bg="#9E9E9E",
                  fg="white").pack(side="left", padx=5)
        tk.Label(barre_outils, text="(Astuce : Double-clic sur une ligne pour ouvrir l'arbre sur Geneanet)",
                 fg="#00796B", font=("Arial", 8, "italic")).pack(side="right", padx=5)

        # Conteneur principal pour le tableau et sa barre de défilement verticale
        tree_container = tk.Frame(gauche_frame)
        tree_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Création de la Scrollbar verticale ttk
        scrollbar_y = ttk.Scrollbar(tree_container, orient="vertical")

        # Création du Treeview rattaché à cette scrollbar
        self.tree = ttk.Treeview(
            tree_container,
            columns=self.colonnes_possibles,
            show="headings",
            yscrollcommand=scrollbar_y.set
        )

        # Raccourci Copie et Double-clic d'ouverture de lien
        self.tree.bind("<Control-c>", self.copier_selection_treeview)
        self.tree.bind("<Command-c>", self.copier_selection_treeview)
        self.tree.bind("<Double-1>", self.ouvrir_lien_ligne_selectionnee)

        for col in self.colonnes_possibles:
            self.tree.heading(col, text=col + " ↕", command=lambda c=col: self.trier_colonne(c, False))
            # Forcer une largeur compacte (max 5-6 caractères) pour les colonnes de dates
            if "Date" in col:
                self.tree.column(col, width=65, anchor="center")
            else:
                self.tree.column(col, width=105)

        # On lie la commande de la scrollbar au treeview
        scrollbar_y.config(command=self.tree.yview)

        # Placement géométrique rigoureux avec pack :
        # On pack la scrollbar à droite en premier avec un remplissage vertical fixe,
        # puis le treeview qui prend tout le reste de l'espace.
        scrollbar_y.pack(side="right", fill="y", padx=(2, 0))  # Ajout d'une petite marge à gauche de la barre
        self.tree.pack(side="left", fill="both", expand=True)

        # (Optionnel pour l'horizontal si vous en avez une)
        scrollbar_x = ttk.Scrollbar(gauche_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=scrollbar_x.set)
        scrollbar_x.pack(side="bottom", fill="x", pady=(2, 0))

    def traiter_lieu_partiel(self, texte_lieu):
        if not texte_lieu:
            return "", ""
        morceaux = [m.strip() for m in texte_lieu.split(',')]
        morceaux_propres = [m for m in morceaux if not re.match(r'^\d+$', m)]
        if not morceaux_propres:
            return "", ""
        ville = morceaux_propres[0]
        dept = morceaux_propres[1] if len(morceaux_propres) > 1 else ""
        return ville, dept

    def decouper_personne(self, texte):
        if not texte:
            return "", ""
        mots = texte.strip().split()
        if not mots:
            return "", ""

        nom_mots = []
        prenom_mots = []

        for i, mot in enumerate(mots):
            clean_mot = re.sub(r'[^A-ZÀ-ÖØ-Þ]', '', mot)
            if clean_mot and clean_mot == mot and mot.isupper():
                nom_mots.append(mot)
            else:
                prenom_mots = mots[i:]
                break

        nom = " ".join(nom_mots)
        prenoms = " ".join(prenom_mots)

        if not nom and mots:
            nom = mots[0]
            prenoms = " ".join(mots[1:])

        return nom, prenoms

    def extraire_date_mariage_et_conjoint(self, brut_conjoint):
        """Extrait la date numérique entre parenthèses et le nom propre du conjoint."""
        if not brut_conjoint:
            return "", "", ""

        # Recherche d'une année numérique impérative entre parenthèses, ex: (1850) ou (1852-1910)
        match_date = re.search(r'\((\d{4}(?:-\d{4})?)\)', brut_conjoint)
        date_mariage = match_date.group(1) if match_date else ""

        # Nettoyage de la chaîne du conjoint en retirant la partie entre parenthèses pour ne garder que l'identité
        conjoint_pur = re.sub(r'\([^)]*\)', '', brut_conjoint).strip()
        conj_nom, conj_prenoms = self.decouper_personne(conjoint_pur)

        return conj_nom, conj_prenoms, date_mariage

    def ouvrir_lien_ligne_selectionnee(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            return

        try:
            # L'identifiant (selected_item) est maintenant directement l'index d'origine dans df_global
            row_idx = int(selected_item)
            if hasattr(self, "df_global") and not self.df_global.empty and row_idx in self.df_global.index:
                url = self.df_global.loc[row_idx, "_url_arbre"]
                if url:
                    webbrowser.open(url)
                else:
                    messagebox.showinfo("Information", "Aucun lien Geneanet disponible pour cet enregistrement.")
        except Exception:
            messagebox.showinfo("Information", "Impossible d'ouvrir le lien pour cette ligne.")


    def copier_selection_treeview(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        lignes_a_copier = []
        en_tetes = list(self.colonnes_possibles)
        lignes_a_copier.append("\t".join(en_tetes))
        for item in selected_items:
            valeurs = self.tree.item(item, "values")
            lignes_a_copier.append("\t".join([str(v) if v is not None else "" for v in valeurs]))
        texte_presse_papiers = "\n".join(lignes_a_copier)
        self.root.clipboard_clear()
        self.root.clipboard_append(texte_presse_papiers)
        self.root.update()

    def changer_colonne_coloration(self):
        if not self.df_global.empty:
            self.attribuer_couleurs_departements()
            self.mettre_a_jour_affichage(self.df_global)

    def attribuer_couleurs_departements(self):
        self.dept_couleurs.clear()
        tous_depts = set()
        col_cible = self.combo_col_dept.get()
        if col_cible not in self.df_global.columns:
            col_cible = "Dept Naiss."

        for _, row in self.df_global.iterrows():
            d = row.get(col_cible)
            if d: tous_depts.add(d)

        for idx, dept in enumerate(sorted(tous_depts)):
            couleur = self.palette_couleurs[idx % len(self.palette_couleurs)]
            self.dept_couleurs[dept] = couleur
            self.tree.tag_configure(f"dept_{dept}", background=couleur)

        if self.fenetre_legende is not None and tk.Toplevel.winfo_exists(self.fenetre_legende):
            self.mettre_a_jour_contenu_legende()

    def process_html(self):
        self.repertoire_courant = filedialog.askdirectory()
        if not self.repertoire_courant:
            return

        ville_ref = self.entry_ref_ville.get().strip()
        try:
            if ville_ref:
                self.lbl_repertoire.config(text="Initialisation de la géolocalisation...", fg="orange")
                self.root.update_idletasks()
            self.analyseur_distance = AnalyseurDistanceGenealogique(ville_ref)
        except Exception as e:
            messagebox.showerror("Erreur de géolocalisation", str(e))
            self.lbl_repertoire.config(text="Répertoire actif : Aucun", fg="gray")
            return

        self.fenetre_progression = tk.Toplevel(self.root)
        self.fenetre_progression.title("Extraction en cours...")
        self.fenetre_progression.geometry("400x160")
        self.fenetre_progression.protocol("WM_DELETE_WINDOW", lambda: None)
        self.fenetre_progression.transient(self.root)
        self.fenetre_progression.grab_set()

        tk.Label(self.fenetre_progression, text="Extraction et analyse des fichiers HTML...",
                 font=("Arial", 10, "bold")).pack(pady=(15, 5))

        self.lbl_progression_texte = tk.Label(self.fenetre_progression, text="Analyse des fichiers en cours...",
                                              font=("Arial", 9), fg="gray")
        self.lbl_progression_texte.pack(pady=5)

        self.barre_progression = ttk.Progressbar(self.fenetre_progression, orient="horizontal", length=350,
                                                 mode="indeterminate")
        self.barre_progression.pack(pady=10)
        self.barre_progression.start(10)

        threading.Thread(target=self._executer_traitement_thread, daemon=True).start()

    def _executer_traitement_thread(self):
        try:
            cfg = {k: v.get() for k, v in self.entries.items()}
            data = []

            fichiers_html = [f for f in os.listdir(self.repertoire_courant) if f.lower().endswith(".html")]
            nb_fichiers_total = len(fichiers_html)

            if nb_fichiers_total == 0:
                self.root.after(0, lambda: self._fin_traitement_erreur("Aucun fichier HTML trouvé dans ce dossier."))
                return

            for index_fich, fichier in enumerate(fichiers_html, 1):
                msg = f"Traitement du fichier {index_fich} sur {nb_fichiers_total} : {fichier}"
                self.root.after(0, lambda m=msg: self.lbl_progression_texte.config(text=m))

                chemin_complet = os.path.join(self.repertoire_courant, fichier)
                with open(chemin_complet, "r", encoding="utf-8", errors="ignore") as f:
                    soup = BeautifulSoup(f, "html.parser")
                    items = soup.find_all("a", class_=cfg["Bloc Ligne"])

                    for item in items:
                        url_arbre = item.get("href", "")
                        if url_arbre and not url_arbre.startswith("http"):
                            url_arbre = "https://www.geneanet.org" + url_arbre

                        div_indiv = item.find("div", class_=cfg["Div Individu"])
                        div_periode = item.find("div", class_=cfg["Div Periode"])
                        div_lieu = item.find("div", class_=cfg["Div Lieu"])

                        brut_nom = div_indiv.find("p", class_="text-large").get_text(strip=True) if div_indiv else ""
                        brut_conjoint = div_indiv.find("span", class_="text-large").get_text(
                            strip=True) if div_indiv and div_indiv.find("span", class_="text-large") else ""

                        nom, prenoms = self.decouper_personne(brut_nom)
                        conj_nom, conj_prenoms, date_mariage = self.extraire_date_mariage_et_conjoint(brut_conjoint)

                        arbre_raw = div_indiv.find("em").get_text(strip=True) if div_indiv and div_indiv.find(
                            "em") else ""
                        arbre = re.sub(r'^(family tree of|arbre généalogique de)\s*', '', arbre_raw,
                                       flags=re.IGNORECASE).strip()

                        date_naiss, date_deces = "", ""
                        if div_periode:
                            for p in div_periode.find_all("p"):
                                txt_p = p.get_text()
                                val_span = p.find("span", class_="text-large")
                                val = val_span.get_text(strip=True) if val_span else ""
                                if "Birth" in txt_p or "Naissance" in txt_p:
                                    date_naiss = val
                                elif "Death" in txt_p or "Décès" in txt_p:
                                    date_deces = val

                        l_naiss, d_naiss = "", ""
                        l_mariage, d_mariage = "", ""
                        l_deces, d_deces = "", ""

                        if div_lieu:
                            lignes_lieux = div_lieu.find_all("p", class_="ligne-lieu")
                            for ligne in lignes_lieux:
                                # Recherche des icônes spécifiques avant les lieux (<span class="icons-lieu"> ou balises SVG)
                                icon = ligne.find("span", class_=re.compile(
                                    r"svg-icon-(birth|grave|union|marriage|s-12|.*-grey)"))
                                title_attr = icon.get("title", "").lower() if icon else ""

                                # Sécurité complémentaire sur les classes CSS directes de l'icône
                                if not title_attr and icon:
                                    classes_icon = " ".join(icon.get("class", []))
                                    if "birth" in classes_icon:
                                        title_attr = "birth"
                                    elif "grave" in classes_icon or "death" in classes_icon:
                                        title_attr = "death"
                                    elif "union" in classes_icon or "marriage" in classes_icon:
                                        title_attr = "union"

                                span_lieu = ligne.find("span", class_="title-lieu")
                                texte_lieu = span_lieu.get_text(strip=True) if span_lieu else ""

                                ville, dept = self.traiter_lieu_partiel(texte_lieu)

                                if "birth" in title_attr or "naissance" in title_attr:
                                    l_naiss, d_naiss = ville, dept
                                elif "union" in title_attr or "marriage" in title_attr or "mariage" in title_attr:
                                    l_mariage, d_mariage = ville, dept
                                elif "grave" in title_attr or "death" in title_attr or "décès" in title_attr:
                                    l_deces, d_deces = ville, dept

                        data.append({
                            "Nom": nom, "Prénoms": prenoms,
                            "Conjoint Nom": conj_nom, "Conjoint Prénoms": conj_prenoms,
                            "Date Naiss.": date_naiss, "Date Mariage": date_mariage, "Date Décès": date_deces,
                            "Lieu Naiss.": l_naiss, "Dept Naiss.": d_naiss,
                            "Lieu Mariage": l_mariage, "Dept Mariage": d_mariage,
                            "Lieu Décès": l_deces, "Dept Décès": d_deces,
                            "Distance": 0,
                            "Arbre": arbre,
                            "_url_arbre": url_arbre
                        })

            self.df_global = pd.DataFrame(data)

            if self.analyseur_distance.coords_ref:
                self.root.after(0,
                                lambda: self.lbl_progression_texte.config(text="Calcul des distances géographiques..."))

            self.attribuer_couleurs_departements()

            zone_app = self.combo_zone.get()
            distances_calculees = [self.analyseur_distance.evaluer_distance_ligne(row, zone_app) for _, row in
                                   self.df_global.iterrows()]
            self.df_global["Distance"] = distances_calculees

            nb_lignes = len(self.df_global)
            self.root.after(0, lambda: self._fin_traitement_succes(nb_fichiers_total, nb_lignes))

        except Exception as e:
            err_msg = str(e)  # <--- On capture le message tout de suite
            self.root.after(0, lambda: self._fin_traitement_erreur(err_msg))

    def _fin_traitement_succes(self, nb_fichiers, nb_lignes):
        if self.fenetre_progression and tk.Toplevel.winfo_exists(self.fenetre_progression):
            self.fenetre_progression.destroy()
            self.fenetre_progression = None

        self.lbl_repertoire.config(text=f"Répertoire actif : {self.repertoire_courant}", fg="blue")
        self.mettre_a_jour_affichage(self.df_global)
        messagebox.showinfo("Succès",
                            f"Traitement terminé avec succès !\n\n- Fichiers HTML analysés : {nb_fichiers}\n- Lignes / enregistrements créés : {nb_lignes}")

    def _fin_traitement_erreur(self, message_erreur):
        if self.fenetre_progression and tk.Toplevel.winfo_exists(self.fenetre_progression):
            self.fenetre_progression.destroy()
            self.fenetre_progression = None
        self.lbl_repertoire.config(text="Répertoire actif : Aucun", fg="gray")
        messagebox.showerror("Erreur", message_erreur)

    def recalculer_distances(self):
        if self.df_global.empty or not self.analyseur_distance:
            return
        zone_app = self.combo_zone.get()
        distances_calculees = [self.analyseur_distance.evaluer_distance_ligne(row, zone_app) for _, row in
                               self.df_global.iterrows()]
        self.df_global["Distance"] = distances_calculees
        self.mettre_a_jour_affichage(self.df_global)

    def appliquer_filtre_distance(self):
        if self.df_global.empty:
            messagebox.showwarning("Attention", "Veuillez d'abord charger un dossier HTML.")
            return
        ville_ref = self.entry_ref_ville.get().strip()
        if not self.analyseur_distance or self.analyseur_distance.ville_ref != ville_ref:
            try:
                self.analyseur_distance = AnalyseurDistanceGenealogique(ville_ref)
            except Exception as e:
                messagebox.showerror("Erreur", str(e))
                return
        self.recalculer_distances()
        try:
            max_dist = float(self.entry_max_dist.get())
        except ValueError:
            messagebox.showerror("Erreur", "Distance maximale invalide.")
            return
        df_filtre = self.df_global[(self.df_global["Distance"] >= 0) & (self.df_global["Distance"] <= max_dist)]
        self.mettre_a_jour_affichage(df_filtre)

    def mettre_a_jour_affichage(self, df):
        for i in self.tree.get_children():
            self.tree.delete(i)
        col_color = self.combo_col_dept.get()

        # On utilise l'index d'origine (idx) comme identifiant unique (iid) de la ligne dans le Treeview
        for idx, row in df.iterrows():
            val_dept = row.get(col_color, "")
            dept_tag = f"dept_{val_dept}" if val_dept in self.dept_couleurs else ""
            valeurs_visibles = [row[col] for col in self.colonnes_possibles]
            self.tree.insert("", "end", iid=str(idx), values=valeurs_visibles, tags=(dept_tag,))

    def trier_colonne(self, col, reverse):
        lignes = []
        for child in self.tree.get_children():
            val = self.tree.set(child, col)
            if col == "Distance":
                try:
                    val_tri = float(val)
                except ValueError:
                    val_tri = -999.0
            else:
                val_tri = val.lower() if isinstance(val, str) else val
            lignes.append((val_tri, child))
        lignes.sort(reverse=reverse)
        for index, (_, child) in enumerate(lignes):
            self.tree.move(child, '', index)
        self.tree.heading(col, command=lambda: self.trier_colonne(col, not reverse))

    def appliquer_dedoublonnage(self):
        if self.df_global.empty: return
        col_cible = self.col_dedup_var.get()
        if col_cible in self.df_global.columns:
            df_filtre = self.df_global.drop_duplicates(subset=[col_cible])
            self.mettre_a_jour_affichage(df_filtre)

    def reinitialiser_tableau(self):
        if not self.df_global.empty:
            self.mettre_a_jour_affichage(self.df_global)

    def exporter_csv_old(self):
        if self.df_global.empty or not self.repertoire_courant:
            messagebox.showwarning("Attention", "Aucune donnée à exporter.")
            return

        # Vérifie si l'utilisateur a sélectionné des lignes spécifiques
        selected_items = self.tree.selection()
        if selected_items:
            lignes_a_exporter = selected_items
            type_export = "la sélection actuelle"
        else:
            lignes_a_exporter = self.tree.get_children()
            type_export = "toutes les lignes visibles"

        if not lignes_a_exporter:
            messagebox.showwarning("Attention", "Aucune ligne à exporter.")
            return

        lignes_finales = []
        for child in lignes_a_exporter:
            vals_dict = dict(zip(self.colonnes_possibles, self.tree.item(child)["values"]))
            nom_arbre = vals_dict.get("Arbre", "")

            # Recherche de l'URL correspondante dans self.df_global
            url_trouvee = ""
            match_lignes = self.df_global[
                (self.df_global["Nom"] == vals_dict.get("Nom")) &
                (self.df_global["Prénoms"] == vals_dict.get("Prénoms")) &
                (self.df_global["Arbre"] == nom_arbre)
                ]
            if not match_lignes.empty:
                url_trouvee = match_lignes.iloc[0].get("_url_arbre", "")

            # Formule spécifique pour LibreOffice Calc en français : =LIEN.HYPERTEXTE("URL"; "Nom")
            if url_trouvee and nom_arbre:
                vals_dict["Arbre"] = f'=LIEN.HYPERTEXTE("{url_trouvee}"; "{nom_arbre}")'

            lignes_finales.append([vals_dict[col] for col in self.colonnes_possibles])

        df_export = pd.DataFrame(lignes_finales, columns=self.colonnes_possibles)

        chemin_csv = os.path.join(self.repertoire_courant, "resultats_geneanet_geopro.csv")
        df_export.to_csv(chemin_csv, index=False, encoding="utf-8-sig")

        messagebox.showinfo(
            "Export réussi",
            f"Export de {type_export} réussi ({len(lignes_finales)} lignes) !\n\n"
            f"Fichier enregistré sous :\n{chemin_csv}\n\n"
            "Astuce Calc : À l'ouverture du CSV dans LibreOffice, assurez-vous que "
            "l'option 'Détecter les nombres spéciaux' ou l'évaluation des formules est active pour que les liens soient cliquables."
        )

    def exporter_csv(self):  # (ou exporter_excel selon le nom de votre fonction)
        if self.df_global.empty or not self.repertoire_courant:
            messagebox.showwarning("Attention", "Aucune donnée à exporter.")
            return

        selected_items = self.tree.selection()
        if selected_items:
            lignes_a_exporter = selected_items
            type_export = "la sélection actuelle"
        else:
            lignes_a_exporter = self.tree.get_children()
            type_export = "toutes les lignes visibles"

        if not lignes_a_exporter:
            messagebox.showwarning("Attention", "Aucune ligne à exporter.")
            return

        lignes_finales = []
        for child in lignes_a_exporter:
            vals_dict = dict(zip(self.colonnes_possibles, self.tree.item(child)["values"]))
            nom_arbre = vals_dict.get("Arbre", "")

            # Récupération directe et ultra-rapide de l'URL via l'index d'origine (child)
            url_trouvee = ""
            try:
                row_idx = int(child)
                if row_idx in self.df_global.index:
                    url_trouvee = self.df_global.loc[row_idx, "_url_arbre"]
            except Exception:
                pass

            # Formule universelle de tableur : =HYPERLINK("URL", "Nom")
            if url_trouvee and nom_arbre:
                vals_dict["Arbre"] = f'=HYPERLINK("{url_trouvee}", "{nom_arbre}")'

            lignes_finales.append([vals_dict[col] for col in self.colonnes_possibles])

        df_export = pd.DataFrame(lignes_finales, columns=self.colonnes_possibles)

        chemin_excel = os.path.join(self.repertoire_courant, "resultats_geneanet_geopro.xlsx")

        try:
            df_export.to_excel(chemin_excel, index=False, engine="openpyxl")
            messagebox.showinfo(
                "Export réussi",
                f"Export de {type_export} réussi ({len(lignes_finales)} lignes) !\n\n"
                f"Fichier enregistré sous :\n{chemin_excel}"
            )
        except Exception as e:
            messagebox.showerror("Erreur d'export", f"Impossible d'exporter au format Excel :\n{e}")

    def executer_regle_remplacement(self, col_pattern, pattern_rech, texte_sub):
        colonnes_concernees = [c for c in self.colonnes_possibles if fnmatch.fnmatch(c, col_pattern)]
        if not colonnes_concernees:
            return 0

        total_remplacements = 0
        for col in colonnes_concernees:
            if col not in self.df_global.columns:
                continue

            col_remplacee = []
            for val in self.df_global[col]:
                if pd.isna(val):
                    col_remplacee.append(val)
                else:
                    new_val, count = re.subn(pattern_rech, texte_sub, str(val))
                    total_remplacements += count
                    col_remplacee.append(new_val)
            self.df_global[col] = col_remplacee

        return total_remplacements

    def enregistrer_regle_csv(self, col_pattern, pattern_rech, texte_sub):
        if not self.repertoire_courant:
            return
        chemin_regles = os.path.join(self.repertoire_courant, "regles_remplacement.csv")
        file_exists = os.path.exists(chemin_regles)
        mode = 'a' if file_exists else 'w'

        with open(chemin_regles, mode, encoding="utf-8") as f:
            if not file_exists:
                f.write("colonne,texte_a_remplacer,texte_de_substitution\n")
            f.write(f'"{col_pattern}","{pattern_rech}","{texte_sub}"\n')

    def rejouer_csv_remplacements(self):
        if self.df_global.empty:
            messagebox.showwarning("Attention", "Veuillez d'abord charger un dossier.")
            return

        chemin_csv = filedialog.askopenfilename(
            title="Sélectionner le fichier de règles de remplacement",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not chemin_csv:
            return

        try:
            df_regles = pd.read_csv(chemin_csv)
            total_global = 0
            for _, row in df_regles.iterrows():
                col_pat = str(row["colonne"])
                pat_rech = str(row["texte_a_remplacer"])
                txt_sub = str(row["texte_de_substitution"])
                total_global += self.executer_regle_remplacement(col_pat, pat_rech, txt_sub)

            self.attribuer_couleurs_departements()
            self.mettre_a_jour_affichage(self.df_global)
            messagebox.showinfo("Rejeu réussi",
                                f"Fichier rejoué avec succès.\nTotal de remplacements effectués : {total_global}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire ou d'exécuter le fichier CSV :\n{e}")

    def ouvrir_fenetre_remplacement(self):
        if self.df_global.empty:
            messagebox.showwarning("Attention", "Veuillez d'abord charger un dossier.")
            return

        if self.fenetre_remplacement is not None and tk.Toplevel.winfo_exists(self.fenetre_remplacement):
            self.fenetre_remplacement.destroy()
            self.fenetre_remplacement = None

        self.fenetre_remplacement = tk.Toplevel(self.root)
        self.fenetre_remplacement.title("Remplacement de texte par Wildcard")
        self.fenetre_remplacement.geometry("450x280")

        tk.Label(self.fenetre_remplacement, text="Nom de colonne (supporte wildcards, ex: *Naiss*) :",
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=20, pady=(15, 2))
        combo_col = ttk.Combobox(self.fenetre_remplacement, values=self.colonnes_possibles, width=40)
        combo_col.pack(anchor="w", padx=20)
        if self.colonnes_possibles:
            combo_col.set(self.colonnes_possibles[0])

        tk.Label(self.fenetre_remplacement, text="Chaîne / Pattern à rechercher (Regex/Wildcard) :",
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=20, pady=(10, 2))
        entry_old = tk.Entry(self.fenetre_remplacement, width=43)
        entry_old.pack(anchor="w", padx=20)

        tk.Label(self.fenetre_remplacement, text="Chaîne de substitution :", font=("Arial", 9, "bold")).pack(anchor="w",
                                                                                                             padx=20,
                                                                                                             pady=(10,
                                                                                                                   2))
        entry_new = tk.Entry(self.fenetre_remplacement, width=43)
        entry_new.pack(anchor="w", padx=20)

        def executer_et_rester():
            col_pat = combo_col.get()
            old_val = entry_old.get()
            new_val = entry_new.get()

            if not col_pat:
                messagebox.showwarning("Attention", "Veuillez spécifier une colonne.")
                return
            if old_val == "":
                messagebox.showwarning("Attention", "La chaîne à rechercher ne peut pas être vide.")
                return

            try:
                nb_faits = self.executer_regle_remplacement(col_pat, old_val, new_val)
                self.enregistrer_regle_csv(col_pat, old_val, new_val)
                self.attribuer_couleurs_departements()
                self.mettre_a_jour_affichage(self.df_global)
                messagebox.showinfo("Remplacement effectué",
                                    f"Opération réussie !\nNombre de remplacements effectués : {nb_faits}")
            except Exception as e:
                messagebox.showerror("Erreur de motif", f"Le pattern saisi est invalide :\n{e}")

        frame_btns = tk.Frame(self.fenetre_remplacement)
        frame_btns.pack(fill="x", padx=20, pady=20)

        tk.Button(frame_btns, text="Remplacer", command=executer_et_rester, bg="#4CAF50", fg="white",
                  font=("Arial", 9, "bold"), width=12).pack(side="left")
        tk.Button(frame_btns, text="Fermer",
                  command=lambda: [self.fenetre_remplacement.destroy(), setattr(self, 'fenetre_remplacement', None)],
                  bg="#f44336", fg="white", font=("Arial", 9, "bold"), width=12).pack(side="right")

    def afficher_aide(self):
        if self.fenetre_aide is not None and tk.Toplevel.winfo_exists(self.fenetre_aide):
            self.fenetre_aide.destroy()
            self.fenetre_aide = None

        self.fenetre_aide = tk.Toplevel(self.root)
        self.fenetre_aide.title("Aide & Fonctionnement - Généa-Extracteur")
        self.fenetre_aide.geometry("600x560")

        txt_aide = (
            "Bienvenue dans Généa-Extracteur Pro !\n\n"
            "1. Paramètres HTML : Ajustez si nécessaire les classes CSS ciblées.\n"
            "2. Dossier & Traitement : Sélectionnez le répertoire contenant vos fichiers HTML.\n"
            "3. Lien Direct : Double-cliquez sur une ligne du tableau pour ouvrir directement l'arbre sur Geneanet.\n"
            "4. Coloriage : Choisissez la colonne servant à colorer les lignes.\n"
            "5. Analyse Géographique : Entrez une ville de référence et filtrez par rayon kilométrique (km).\n"
            "6. Remplacer Texte : Modifie en masse via regex/wildcards et enregistre dans 'regles_remplacement.csv'.\n"
            "7. Gestion Arbres : Permet de voir et de supprimer des lots d'arbres entiers.\n"
            "8. Légende Départements : Tri alphabétique ou par nombre de lignes avec bouton de rafraîchissement.\n"
            "9. Export CSV : Enregistre le tableau actif."
        )

        frame = tk.Frame(self.fenetre_aide, padx=15, pady=15)
        frame.pack(fill="both", expand=True)

        lbl = tk.Label(frame, text=txt_aide, justify="left", wraplength=560, font=("Arial", 10))
        lbl.pack(fill="both", expand=True)

        tk.Button(self.fenetre_aide, text="Fermer", command=self.fenetre_aide.destroy, bg="#f44336", fg="white").pack(
            pady=10)

    def toggle_fenetre_arbres(self):
        if self.fenetre_arbres is not None and tk.Toplevel.winfo_exists(self.fenetre_arbres):
            self.fenetre_arbres.destroy()
            self.fenetre_arbres = None
            return

        if self.df_global.empty:
            messagebox.showwarning("Attention", "Veuillez d'abord charger un dossier.")
            return

        self.fenetre_arbres = tk.Toplevel(self.root)
        self.fenetre_arbres.title("Gestion de tous les Arbres")
        self.fenetre_arbres.geometry("500x550")

        btn_fermer = tk.Button(self.fenetre_arbres, text="Fermer", command=self.fenetre_arbres.destroy, bg="#f44336",
                               fg="white", font=("Arial", 9, "bold"))
        btn_fermer.pack(side="bottom", fill="x", padx=10, pady=10)

        frame_conteneur = tk.Frame(self.fenetre_arbres)
        frame_conteneur.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(frame_conteneur, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_conteneur, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        self.arbres_vars = {}
        arbres_info = {}
        for _, row in self.df_global.iterrows():
            arb = row["Arbre"]
            url = row.get("_url_arbre", "")
            if arb not in arbres_info:
                arbres_info[arb] = {"count": 0, "url": url}
            arbres_info[arb]["count"] += 1

        for arbre, info in sorted(arbres_info.items(), key=lambda x: x[1]["count"], reverse=True):
            ligne_frame = tk.Frame(scrollable_frame, bd=1, relief="solid", padx=5, pady=4)
            ligne_frame.pack(fill="x", padx=5, pady=3)

            var = tk.BooleanVar(value=False)
            self.arbres_vars[arbre] = var

            cb = tk.Checkbutton(ligne_frame, text=f"{arbre} ({info['count']})", variable=var, font=("Arial", 9))
            cb.pack(side="left", anchor="w")

            if info["url"]:
                lbl_lien = tk.Label(ligne_frame, text="[Lien Arbre]", fg="blue", cursor="hand2",
                                    font=("Arial", 9, "underline"))
                lbl_lien.pack(side="right", padx=5)
                lbl_lien.bind("<Button-1>", lambda e, u=info["url"]: webbrowser.open(u))

        def supprimer_arbres_choisis():
            arbres_cibles = [arb for arb, var in self.arbres_vars.items() if var.get()]
            if not arbres_cibles:
                messagebox.showwarning("Attention", "Veuillez cocher au moins un arbre.")
                return

            noms_str = "\n".join([f"- {a}" for a in arbres_cibles])
            if messagebox.askyesno("Confirmation",
                                   f"Voulez-vous supprimer toutes les lignes associées aux arbres suivants :\n{noms_str} ?"):
                self.df_global = self.df_global[~self.df_global["Arbre"].isin(arbres_cibles)]
                self.attribuer_couleurs_departements()
                self.mettre_a_jour_affichage(self.df_global)
                self.fenetre_arbres.destroy()
                self.fenetre_arbres = None

        btn_suppr = tk.Button(self.fenetre_arbres, text="Supprimer les lignes des arbres sélectionnés",
                              command=supprimer_arbres_choisis, bg="#E91E63", fg="white", font=("Arial", 9, "bold"))
        btn_suppr.pack(side="bottom", fill="x", padx=10, pady=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def sur_fermeture():
            canvas.unbind_all("<MouseWheel>")
            self.fenetre_arbres.destroy()
            self.fenetre_arbres = None

        self.fenetre_arbres.protocol("WM_DELETE_WINDOW", sur_fermeture)
        btn_fermer.config(command=sur_fermeture)

    def toggle_fenetre_legende(self):
        if self.fenetre_legende is not None and tk.Toplevel.winfo_exists(self.fenetre_legende):
            self.fenetre_legende.destroy()
            self.fenetre_legende = None
            return

        if not self.dept_couleurs:
            messagebox.showwarning("Attention", "Aucun département chargé.")
            return

        self.fenetre_legende = tk.Toplevel(self.root)
        self.fenetre_legende.title("Légende des Départements & Occurrences")
        self.fenetre_legende.geometry("420x560")

        cadre_haut_legende = tk.Frame(self.fenetre_legende, padx=10, pady=8)
        cadre_haut_legende.pack(fill="x")

        tk.Label(cadre_haut_legende, text="Trier par :", font=("Arial", 9, "bold")).pack(side="left", padx=5)
        self.combo_tri_legende = ttk.Combobox(cadre_haut_legende, values=["Alphabétique (A-Z)", "Alphabétique (Z-A)",
                                                                          "Nombre de lignes (Décroissant)",
                                                                          "Nombre de lignes (Croissant)"],
                                              state="readonly", width=30)
        self.combo_tri_legende.set("Alphabétique (A-Z)")
        self.combo_tri_legende.pack(side="left", padx=5)
        self.combo_tri_legende.bind("<<ComboboxSelected>>", lambda e: self.mettre_a_jour_contenu_legende())

        tk.Button(cadre_haut_legende, text="Rafraîchir", command=self.mettre_a_jour_contenu_legende, bg="#607D8B",
                  fg="white", font=("Arial", 9, "bold")).pack(side="right", padx=5)

        btn_fermer = tk.Button(self.fenetre_legende, text="Fermer", command=self.fermer_fenetre_legende, bg="#f44336",
                               fg="white", font=("Arial", 10, "bold"))
        btn_fermer.pack(side="bottom", fill="x", padx=10, pady=10)

        self.frame_conteneur_legende = tk.Frame(self.fenetre_legende)
        self.frame_conteneur_legende.pack(fill="both", expand=True, padx=10, pady=5)

        self.mettre_a_jour_contenu_legende()

    def mettre_a_jour_contenu_legende(self):
        if self.fenetre_legende is None or not tk.Toplevel.winfo_exists(self.fenetre_legende):
            return

        for widget in self.frame_conteneur_legende.winfo_children():
            widget.destroy()

        canvas = tk.Canvas(self.frame_conteneur_legende, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame_conteneur_legende, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        col_cible = self.combo_col_dept.get()
        comptage_depts = self.df_global[col_cible].value_counts() if not self.df_global.empty else {}

        mode_tri = self.combo_tri_legende.get() if hasattr(self, "combo_tri_legende") else "Alphabétique (A-Z)"

        items_legende = []
        for dept, couleur in self.dept_couleurs.items():
            nb_occ = comptage_depts.get(dept, 0)
            items_legende.append((dept, couleur, nb_occ))

        if mode_tri == "Alphabétique (A-Z)":
            items_legende.sort(key=lambda x: str(x[0]).lower())
        elif mode_tri == "Alphabétique (Z-A)":
            items_legende.sort(key=lambda x: str(x[0]).lower(), reverse=True)
        elif mode_tri == "Nombre de lignes (Décroissant)":
            items_legende.sort(key=lambda x: (x[2], str(x[0]).lower()), reverse=True)
        elif mode_tri == "Nombre de lignes (Croissant)":
            items_legende.sort(key=lambda x: (x[2], str(x[0]).lower()))

        for dept, couleur, nb_occ in items_legende:
            ligne_frame = tk.Frame(scrollable_frame, bg=couleur, bd=1, relief="solid")
            ligne_frame.pack(fill="x", padx=5, pady=4, ipady=4)

            tk.Label(ligne_frame, text=f"  {dept}  ", bg=couleur, font=("Arial", 10, "bold")).pack(side="left", padx=10)
            tk.Label(ligne_frame, text=f"({nb_occ} lignes)  ", bg=couleur, font=("Arial", 9, "italic")).pack(
                side="right", padx=10)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas_legende_actif = canvas

    def fermer_fenetre_legende(self):
        if hasattr(self, "canvas_legende_actif") and self.canvas_legende_actif:
            try:
                self.canvas_legende_actif.unbind_all("<MouseWheel>")
            except Exception:
                pass
        if self.fenetre_legende:
            self.fenetre_legende.destroy()
            self.fenetre_legende = None


if __name__ == "__main__":
    root = tk.Tk()
    app = GeneaExtractorApp(root)
    root.mainloop()
