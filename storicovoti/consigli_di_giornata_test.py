import os

import duckdb

from storicovoti.modello_fantacalcio_test import modello_fantacalcio_test
from utils.SeasonDf import *
from utils.metodi import *


def consigli_di_giornata_test(
        ultima_giornata,
        n_giornate,
        stagione,
        dataframe,
        salva_consigli=False,
        salva_modello=False,
        perc_presenze=0.375,
        # file_quotazioni=f"{ROOT_DIR}/sorgenti/Quotazioni_Fantacalcio_Stagione_2022_23.xlsx"
):
    dataframe_filtrato = duckdb.query(f"""
        select *
        from dataframe
        where GIORNATA_GIOCATORE <= {n_giornate}
              and case
                    when {ultima_giornata} < {n_giornate} then STAGIONE in ('{stagione - 1}{stagione}', '{stagione}{stagione + 1}')
                    else STAGIONE = '{stagione}{stagione + 1}'
                  end
    """)

    risultato_finale = modello_fantacalcio_test(
        ultima_giornata,
        n_giornate,
        dataframe_filtrato,
        salva_modello,
        perc_presenze,
        # file_quotazioni
    )

    dataframe_avversari_filtrato = duckdb.query(f"""
        select *
        from dataframe
        where GIORNATA_CALCOLATA_AVVERSARI <= {n_giornate}
              and case
                    when {ultima_giornata} < {n_giornate} then STAGIONE in ('{stagione - 1}{stagione}', '{stagione}{stagione + 1}')
                    else STAGIONE = '{stagione}{stagione + 1}'
                  end
    """)

    A = 2
    B = -21
    C = 55
    voti_contro = duckdb.query(f"""
    select
        upper(incontri.squadra) as squadra,
        voti_p.MediaVoti_P,
        voti_d.MediaVoti_D,
        voti_c.MediaVoti_C,
        voti_a.MediaVoti_A,
        voti_p.MediaFantaVoti_P,
        voti_d.MediaFantaVoti_D,
        voti_c.MediaFantaVoti_C,
        voti_a.MediaFantaVoti_A,
        voti_p.MediaConMod_P,
        voti_d.MediaConMod_D
    from (
        select distinct squadra
        from dataframe_avversari_filtrato
    ) incontri
    join (
        select avversario, avg(voto) as MediaVoti_P, avg(fantavoto) as MediaFantaVoti_P, avg(({A} * voto ** 2 + {B} * voto + {C}) / 4 + fantavoto) as MediaConMod_P
        from dataframe_avversari_filtrato df
        where ruolo = 'P'
        group by avversario
    ) voti_p
    on incontri.squadra = voti_p.avversario
    join (
        select avversario, avg(voto) as MediaVoti_D, avg(fantavoto) as MediaFantaVoti_D, avg(({A} * voto ** 2 + {B} * voto + {C}) / 4 + fantavoto) as MediaConMod_D
        from dataframe_avversari_filtrato df
        where ruolo = 'D'
        group by avversario
    ) voti_d
    on incontri.squadra = voti_d.avversario
    join (
        select avversario, avg(voto) as MediaVoti_C, avg(fantavoto) as MediaFantaVoti_C
        from dataframe_avversari_filtrato df
        where ruolo = 'C'
        group by avversario
    ) voti_c
    on incontri.squadra = voti_c.avversario
    join (
        select avversario, avg(voto) as MediaVoti_A, avg(fantavoto) as MediaFantaVoti_A
        from dataframe_avversari_filtrato df
        where ruolo = 'A'
        group by avversario
    ) voti_a
    on incontri.squadra = voti_a.avversario
    """).df()
    voti_contro.to_excel(f"voti_contro.xlsx")

    giornate_soup = ottieni_giornate_soup(stagione)
    giornata_soup = [g_s for g_s in giornate_soup if f"GIORNATA {ultima_giornata + 1}<" in str(g_s).upper()][0]
    squadre_soup = giornata_soup.find_all("span", attrs={"class": "ftbl__match-row__team--desktop"})
    casa_soup_coi_none = [el.find("span", attrs={
        "class": "ftbl__text ftbl__text--span ftbl__text--color-blue ftbl__text--font-size-14 ftbl__text--weight-500 ftbl__team__name ftbl__team__name--right"})
                          for el in squadre_soup]
    ospiti_soup_coi_none = [el.find("span", attrs={
        "class": "ftbl__text ftbl__text--span ftbl__text--color-blue ftbl__text--font-size-14 ftbl__text--weight-500 ftbl__team__name ftbl__team__name--left"})
                            for el in squadre_soup]
    squadre_casa = [el.text.upper() for el in casa_soup_coi_none if el is not None]
    squadre_ospiti = [el.text.upper() for el in ospiti_soup_coi_none if el is not None]
    lista_incontri = {}
    for casa, ospite in zip(squadre_casa, squadre_ospiti):
        lista_incontri[casa] = ospite
        lista_incontri[ospite] = casa

    incontri = pd.DataFrame(zip(squadre_casa + squadre_ospiti, squadre_ospiti + squadre_casa),
                            columns=["SQUADRA", "AVVERSARIO"])

    consigli_giornata_test = duckdb.query("""
    select
        Cod,
        R,
        Nome,
        Squadra,
        VotoPotenziale,
        FantaVotoPotenziale,
        0.5 * cast((VotoPotenziale + 0.25) / 0.5 as int) as Voto,
        0.5 * cast((FantaVotoPotenziale + 0.25) / 0.5 as int) as FantaVoto
    from (
        select
            r.*,
            r.media * case r
                        when 'P' then mediavoti_p / voto_medio_p
                        when 'D' then mediavoti_d / voto_medio_d
                        when 'C' then mediavoti_c / voto_medio_c
                        when 'A' then mediavoti_a / voto_medio_a
                      end as VotoPotenziale,
            r.fantamedia * case r
                        when 'P' then mediafantavoti_p / fantavoto_medio_p
                        when 'D' then mediafantavoti_d / fantavoto_medio_d
                        when 'C' then mediafantavoti_c / fantavoto_medio_c
                        when 'A' then mediafantavoti_a / fantavoto_medio_a
                      end as FantaVotoPotenziale
        from risultato_finale r
        join incontri i
          on i.squadra = upper(r.squadra)
        join (
            select
                v1.*,
                avg(v2.mediavoti_p) as voto_medio_p,
                avg(v2.mediavoti_d) as voto_medio_d,
                avg(v2.mediavoti_c) as voto_medio_c,
                avg(v2.mediavoti_a) as voto_medio_a,
                avg(v2.mediafantavoti_p) as fantavoto_medio_p,
                avg(v2.mediafantavoti_d) as fantavoto_medio_d,
                avg(v2.mediafantavoti_c) as fantavoto_medio_c,
                avg(v2.mediafantavoti_a) as fantavoto_medio_a
            from voti_contro v1
            join voti_contro v2
              on v1.squadra != v2.squadra
            group by v1.*
        ) v
          on v.squadra = i.avversario
    )
    """).df()

    print(f"creato consigli di giornata {ultima_giornata + 1} considerando le precedenti {n_giornate}")

    if salva_consigli:
        path_consigli_di_giornata = f"estrazioni/consigli_giornata_test/giornata_{ultima_giornata + 1}"
        file_consigli_di_giornata = f"consigli_ultime_{n_giornate}.xlsx"
        if not os.path.exists(path_consigli_di_giornata):
            os.makedirs(path_consigli_di_giornata)

        path_finale_consigli_di_giornata = os.path.join(path_consigli_di_giornata, file_consigli_di_giornata)
        consigli_giornata_test.to_excel(path_finale_consigli_di_giornata)
        print(
            f"salvato consigli di giornata {ultima_giornata + 1} considerando le precedenti {n_giornate} in {path_finale_consigli_di_giornata}")

    return consigli_giornata_test
