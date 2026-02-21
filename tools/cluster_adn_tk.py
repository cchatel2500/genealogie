import tkinter as tk
from tkinter import filedialog, scrolledtext
import sys

# ===============================
# PLACEHOLDER : ton analyse ADN
# ===============================
def run_analysis(params):
    # Répertoire contenant tous les CSV
    DATA_DIR = params["DATA_DIR"]# "."

    MIN_SHARED_SEGMENTS = params["MIN_SHARED_SEGMENTS"]# 2
    MIN_CM = params["MIN_CM"]# 30
    MAX_CM = params["MAX_CM"]# 150
    MIN_OVERLAP_BP = params["MIN_OVERLAP_BP"]# 10  # 7 Mb
    MIN_CLUSTER = params["MIN_CLUSTER"] #1
    ...
    import pandas as pd
    import os
    import networkx as nx

    matches = {}

    def shared_segments_count(segs1, segs2):
        count = 0

        for _, s1 in segs1.iterrows():
            for _, s2 in segs2.iterrows():
                if s1["Chromosome"] != s2["Chromosome"]:
                    continue

                # 2. Calculer le début et la fin de l'INTERSECTION
                # Le début du chevauchement est le max des points de départ
                # La fin du chevauchement est le min des points de fin
                overlap_start = max(s1["Start Location"], s2["Start Location"])
                overlap_end = min(s1["End Location"], s2["End Location"])

                overlap_size = overlap_end - overlap_start

                # print ("overlap : ", overlap_size, MIN_OVERLAP_BP)

                if overlap_size >= MIN_OVERLAP_BP:
                    count += 1
                    # Optionnel : on peut afficher le détail pour le debug
                    # print(f"Match trouvé sur Chr {s1['Chromosome']}: {overlap_size/1e6:.2f} Mb")

                    if count >= MIN_SHARED_SEGMENTS:
                        return count

        return count

    # 1. Charger tous les fichiers CSV
    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            path = os.path.join(DATA_DIR, file)
            df = pd.read_csv(path)

            match_name = df["Match Name"].iloc[0]
            total_cm = df["Centimorgans"].sum()

            matches[match_name] = {
                "total_cm": total_cm,
                "segments": df[[
                    "Chromosome",
                    "Start Location",
                    "End Location"
                ]]
            }

    # 2. Filtrer par total cM
    filtered = {
        k: v for k, v in matches.items()
        if MIN_CM <= v["total_cm"] <= MAX_CM
    }

    print(f"{len(filtered)} matchs retenus entre {MIN_CM} et {MAX_CM} cM")

    # 3. Détection des chevauchements ADN
    def overlap(seg1, seg2):
        return not (
                seg1["End Location"] < seg2["Start Location"] or
                seg2["End Location"] < seg1["Start Location"]
        )

    G = nx.Graph()

    for m1, d1 in filtered.items():
        G.add_node(m1)

    for m1, d1 in filtered.items():
        for m2, d2 in filtered.items():
            if m1 >= m2:
                continue

            shared = shared_segments_count(
                d1["segments"],
                d2["segments"]
            )

            if shared >= MIN_SHARED_SEGMENTS:
                G.add_edge(m1, m2)

    # 4. Extraire les clusters
    clusters = list(nx.connected_components(G))

    print("\nMIN_SHARED_SEGMENTS = ", MIN_SHARED_SEGMENTS, "MIN_OVERLAP_BP = ", MIN_OVERLAP_BP)
    print("CLUSTERS ADN :")
    for i, cluster in enumerate(clusters, 1):
        if len(cluster) > MIN_CLUSTER:
            print(f"\nCluster {i} ({len(cluster)} personnes) :")
            for m in cluster:
                print(f"  - {m} ({filtered[m]['total_cm']:.1f} cM)")

    # for m, d in filtered.items():
    #     print(m, len(d["segments"]), f"{d['total_cm']:.1f} cM")

    # a completer
    ...
    # À remplacer par ton vrai code
    result = []
    result.append("PARAMÈTRES UTILISÉS :")
    for k, v in params.items():
        result.append(f"{k} = {v}")
    result.append("\nCLUSTERS TROUVÉS :")
    for i, cluster in enumerate(clusters, 1):
        if len(cluster) > MIN_CLUSTER:
            result.append(f"\nCluster {i} ({len(cluster)} personnes) :")
            for m in cluster:
                result.append(f"  - {m} ({filtered[m]['total_cm']:.1f} cM)")
    return "\n".join(result)

# ===============================
# FENÊTRE RÉSULTATS
# ===============================
def open_result_window(result_text):
    win = tk.Toplevel()
    win.title("Résultats ADN")

    text = scrolledtext.ScrolledText(win, width=90, height=30)
    text.pack(padx=10, pady=10)
    text.insert(tk.END, result_text)
    text.configure(state="disabled")

# ===============================
# FENÊTRE PARAMÈTRES
# ===============================
def main():
    root = tk.Tk()
    root.title("Analyse ADN – MyHeritage")

    params = {
        "DATA_DIR": tk.StringVar(value="."),
        "MIN_CM": tk.IntVar(value=40),
        "MAX_CM": tk.IntVar(value=150),
        "MIN_SEG_CM": tk.IntVar(value=0),
        "MIN_SHARED_SEGMENTS": tk.IntVar(value=3),
        "MIN_OVERLAP_BP": tk.IntVar(value=0),
        "MIN_CLUSTER": tk.IntVar(value=1),
    }

    row = 0
    for key, var in params.items():
        tk.Label(root, text=key).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(root, textvariable=var, width=30).grid(row=row, column=1, padx=5)
        row += 1

    # Sélecteur de dossier
    def browse_dir():
        folder = filedialog.askdirectory()
        if folder:
            params["DATA_DIR"].set(folder)

    tk.Button(root, text="Choisir répertoire", command=browse_dir)\
        .grid(row=0, column=2, padx=5)

    # Bouton EXÉCUTER
    def execute():
        param_values = {k: v.get() for k, v in params.items()}
        result = run_analysis(param_values)
        open_result_window(result)

    tk.Button(root, text="Exécuter", width=15, command=execute)\
        .grid(row=row, column=0, pady=10)

    # Bouton FERMER
    def close_all():
        root.destroy()
        sys.exit(0)

    tk.Button(root, text="Fermer", width=15, command=close_all)\
        .grid(row=row, column=1, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
