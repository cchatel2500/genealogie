import tkinter as tk
from tkinter import filedialog, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import pandas as pd

# =========================
# PLACEHOLDER : analyse ADN
# =========================
def run_analysis_exemple(params):
    """
    Retourne des clusters fictifs pour exemple.
    Chaque cluster = dict {person: DataFrame segments}
    """
    # Exemple : 2 clusters
    clusters = []

    # Cluster 1
    cluster1 = {
        "Alice": pd.DataFrame({
            "Chromosome": ["1","1","2"],
            "Start Location": [0, 50_000_000, 0],
            "End Location": [30_000_000, 90_000_000, 80_000_000]
        }),
        "Bob": pd.DataFrame({
            "Chromosome": ["1","2"],
            "Start Location": [10_000_000, 0],
            "End Location": [40_000_000, 80_000_000]
        })
    }
    clusters.append(cluster1)

    # Cluster 2
    cluster2 = {
        "Charlie": pd.DataFrame({
            "Chromosome": ["1","3"],
            "Start Location": [0, 0],
            "End Location": [20_000_000, 70_000_000]
        }),
        "David": pd.DataFrame({
            "Chromosome": ["3"],
            "Start Location": [0],
            "End Location": [60_000_000]
        })
    }
    clusters.append(cluster2)
    return clusters

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

    clusters_data = []
    for cluster in clusters:
        if len(cluster) > MIN_CLUSTER:
            cluster_dict = {}
            for person in cluster:
                cluster_dict[person] = filtered[person]["segments"]
            clusters_data.append(cluster_dict)

    return clusters_data


# =========================
# FONCTION DE VISUALISATION
# =========================
from matplotlib.lines import Line2D

def plot_cluster_segments(cluster_matches):
    fig, ax = plt.subplots(figsize=(10, 6))

    chromosomes = sorted({
        str(row["Chromosome"])
        for df in cluster_matches.values()
        for _, row in df.iterrows()
    }, key=lambda x: int(x))

    chr_base_y = {c: i * 5 for i, c in enumerate(chromosomes)}

    random.seed(42)
    colors = {
        person: (random.random(), random.random(), random.random())
        for person in cluster_matches
    }

    persons = list(cluster_matches.keys())
    person_offset = {p: i for i, p in enumerate(persons)}

    # barres chromosomes
    for chr_, base in chr_base_y.items():
        ax.hlines(base - 1, 0, 250_000_000,
                  color="lightgrey", linewidth=6)

    # segments
    for person, df in cluster_matches.items():
        offset = person_offset[person]

        for _, row in df.iterrows():
            chr_ = str(row["Chromosome"])
            y = chr_base_y[chr_] + offset

            ax.hlines(
                y=y,
                xmin=row["Start Location"],
                xmax=row["End Location"],
                color=colors[person],
                linewidth=4
            )

    # légende
    legend_elements = [
        Line2D([0], [0], color=colors[p], lw=4, label=p)
        for p in persons
    ]

    ax.legend(handles=legend_elements,
              bbox_to_anchor=(1.02, 1),
              loc="upper left")

    ax.set_yticks([chr_base_y[c] for c in chromosomes])
    ax.set_yticklabels(chromosomes)

    ax.set_xlabel("Position (bp)")
    ax.set_ylabel("Chromosome")
    ax.set_title("Segments ADN par personne")

    plt.tight_layout()
    return fig


# =========================
# TKINTER
# =========================
class ADNApp:
    def __init__(self, root):
        self.root = root
        root.title("Analyse ADN – MyHeritage")

        # Paramètres
        self.params = {
            "DATA_DIR": tk.StringVar(value="."),
            "MIN_CM": tk.IntVar(value=40),
            "MAX_CM": tk.IntVar(value=150),
            "MIN_SEG_CM": tk.IntVar(value=0),
            "MIN_SHARED_SEGMENTS": tk.IntVar(value=3),
            "MIN_OVERLAP_BP": tk.IntVar(value=0),
            "MIN_CLUSTER": tk.IntVar(value=1),
        }

        # Champs paramètres
        row = 0
        for key, var in self.params.items():
            tk.Label(root, text=key).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            tk.Entry(root, textvariable=var, width=30).grid(row=row, column=1, padx=5)
            row += 1

        tk.Button(root, text="Choisir répertoire", command=self.browse_dir)\
            .grid(row=0, column=2, padx=5)

        tk.Button(root, text="Exécuter", width=15, command=self.execute)\
            .grid(row=row, column=0, pady=10)

        tk.Button(root, text="Fermer", width=15, command=root.destroy)\
            .grid(row=row, column=1, pady=10)

        # Liste des clusters
        tk.Label(root, text="Clusters").grid(row=0, column=3, padx=10, sticky="w")
        self.cluster_list = tk.Listbox(root, height=10)
        self.cluster_list.grid(row=1, column=3, rowspan=row, padx=10, sticky="ns")
        self.cluster_list.bind("<<ListboxSelect>>", self.show_selected_cluster)

        # Zone graphique
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.grid(row=row+1, column=0, columnspan=4, pady=10)
        self.canvas = None
        self.current_clusters = []

    def browse_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.params["DATA_DIR"].set(folder)

    def execute(self):
        param_values = {k: v.get() for k, v in self.params.items()}
        self.current_clusters = run_analysis(param_values)
        self.cluster_list.delete(0, tk.END)
        for i, c in enumerate(self.current_clusters, 1):
            self.cluster_list.insert(tk.END, f"Cluster {i} ({len(c)} personnes)")

    def show_selected_cluster(self, event):
        if not self.current_clusters:
            return
        selection = self.cluster_list.curselection()
        if not selection:
            return
        index = selection[0]
        cluster_data = self.current_clusters[index]
        fig = plot_cluster_segments(cluster_data)
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

# =========================
# LANCEMENT
# =========================
if __name__ == "__main__":
    root = tk.Tk()
    app = ADNApp(root)
    root.mainloop()
