import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import argparse

parser = argparse.ArgumentParser(description='Generate graphs from test results')
parser.add_argument('FILE', help='The CSV file containing the test results')

args = parser.parse_args()

sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 12, 'pdf.fonttype': 42})
COLORS = ['#e74c3c', '#3498db']

with open(args.FILE, "r") as f:
    lines = f.readlines()

split_idx = next(i for i, line in enumerate(lines) if "--- AGGREGATE METRICS ---" in line)

raw_data_str = "".join(lines[:split_idx-1])
df_raw = pd.read_csv(io.StringIO(raw_data_str))

metrics_str = "".join(lines[split_idx+1:])
df_metrics = pd.read_csv(io.StringIO(metrics_str))

# CPU benchmark
plt.figure(figsize=(12, 6))
df_cpu = df_raw.melt(
    id_vars=['Test_ID'], 
    value_vars=['Falco_CPU_Avg(%)', 'Tetragon_CPU_Avg(%)'],
    var_name='Strumento', 
    value_name='CPU Media (%)'
)
df_cpu['Strumento'] = df_cpu['Strumento'].str.replace('_CPU_Avg(%)', '', regex=False)

sns.barplot(data=df_cpu, x='Test_ID', y='CPU Media (%)', hue='Strumento', palette=COLORS)
plt.title("Impatto sulla CPU per Scenario di Test", pad=20, fontweight='bold')
plt.xlabel("ID Test")
plt.ylabel("CPU Media (%)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("cpu_benchmark.pdf", format="pdf", bbox_inches="tight")

# Memory benchmark
plt.figure(figsize=(12, 6))
df_ram = df_raw.melt(
    id_vars=['Test_ID'], 
    value_vars=['Falco_RAM_Max(MB)', 'Tetragon_RAM_Max(MB)'],
    var_name='Strumento', 
    value_name='RAM Picco (MB)'
)
df_ram['Strumento'] = df_ram['Strumento'].str.replace('_RAM_Max(MB)', '', regex=False)

sns.barplot(data=df_ram, x='Test_ID', y='RAM Picco (MB)', hue='Strumento', palette=COLORS)
plt.title("Consumo Massimo di Memoria RAM per Scenario di Test", pad=20, fontweight='bold')
plt.xlabel("ID Test")
plt.ylabel("Picco utilizzo RAM (MB)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("ram_benchmark.pdf", format="pdf", bbox_inches="tight")

# Drops
plt.figure(figsize=(12, 6))
df_drops = df_raw.melt(
    id_vars=['Test_ID'],
    value_vars=['Falco_Drops_Delta', 'Tetragon_Drops_Delta'],
    var_name='Strumento',
    value_name='Eventi Persi'
)
df_drops['Strumento'] = df_drops['Strumento'].str.replace('_Drops_Delta', '', regex=False)

sns.barplot(data=df_drops, x='Test_ID', y='Eventi Persi', hue='Strumento', palette=COLORS)
plt.title("Eventi Persi per Scenario di Test", pad=20, fontweight='bold')
plt.xlabel("ID Test")
plt.ylabel("Eventi Persi")
plt.xticks(rotation=45)
plt.yscale("symlog")
plt.tight_layout()
plt.savefig("drops_benchmark.pdf", format="pdf", bbox_inches="tight")

# Recall & Precision
plt.figure(figsize=(8, 5))
df_eff = df_metrics.melt(
    id_vars=['Tool'], 
    value_vars=['Recall(TPR)', 'Precision'],
    var_name='Metrica', 
    value_name='Valore'
)
df_eff['Tool'] = df_eff['Tool'].str.capitalize()

sns.barplot(data=df_eff, x='Metrica', y='Valore', hue='Tool', palette=COLORS)
plt.title("Recall e Precision", pad=20, fontweight='bold')
plt.ylim(0, 1.1)
plt.savefig("recall_precision.pdf", format="pdf", bbox_inches="tight")

# Latency
plt.figure(figsize=(6, 5))
df_metrics['Tool'] = df_metrics['Tool'].str.capitalize()
sns.barplot(data=df_metrics, hue='Tool', y='Avg_Latency_ms', palette=COLORS, legend=False)
plt.title("Latenza Media di Rilevamento (ms)", pad=20, fontweight='bold')
plt.ylabel("Millisecondi")
plt.savefig("latency.pdf", format="pdf", bbox_inches="tight")
