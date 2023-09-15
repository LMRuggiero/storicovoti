import pandas as pd

from root import ROOT_DIR
from storicovoti.modello_fantacalcio import modello_fantacalcio

file_quotazioni = f"{ROOT_DIR}/sorgenti/Quotazioni_Fantacalcio_Stagione_2022_23_02_01.xlsx"
_, modello = modello_fantacalcio(
    giornata_esaminata=20,
    numero_giornate=10,
    salva_excel=False,
    percentuale_presenze=0.3,
    file_quotazioni=file_quotazioni
)

df_quotazioni = pd.read_excel(file_quotazioni, header=1)
df_quotazioni["Nome"] = df_quotazioni["Nome"].str.upper()
merge = pd.merge(df_quotazioni, modello, "left", ["R", "Nome"])
listone_poduzione = pd.read_excel(f"{ROOT_DIR}/sorgenti/Listone_produzione.xlsx")
listone_poduzione_berteboom = listone_poduzione[listone_poduzione.Lega == 'Lega dei Cojon']
merge = pd.merge(merge, listone_poduzione_berteboom, "left", on=["R", "Nome"])
merge = merge[
    ["R", "Nome", "Squadra_y", "Qt.A", "FVM", "Partite", "Media", "FantaMedia", "VotoCentrale", "FantaVotoCentrale",
     "Posizione", "Lega", "Proprietario"]]
merge.to_excel("test.xlsx")
