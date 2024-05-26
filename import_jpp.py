"""
Importe une base au format JPP (Access pour la cantine).

Marche à suivre:
1. Exporter chaque table de la table Access en fichier .csv

e.g. liste des tables:

mdb-tables diwan_L_tab_ecole.accdb

e.g. Exporter toutes les tables

for table in `mdb-tables diwan_L_tab_ecole.accdb`; do
  mdb-export diwan_L_tab_ecole.accdb $table > $table.csv
done

2. Corriger la table des noms de parents (T_PARENTS_ID.csv) pour s'assurer
que le nom respecte le format "NOM Prénom" (certains noms prénoms sont inversés)
(Enregistrer sous T_PARENTS_ID_corrigé.csv)

3. Placer les fichiers csv dans un répertoire ./kantin

4. Lancer le script d'import depuis une base Noethysweb vide

docker-compose exec django python import_jpp.py

Le script génère un fichier identifiants.txt qui contient les identifiants et mot de passe
(à changer à la première connexion) de chaque famille

"""

import os
import django
import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "noethysweb.settings")
django.setup()

import csv

from core.models import (
    Ecole,
    Famille,
    Individu,
    Rattachement,
    Utilisateur,
    Mandat,
    Classe,
    Scolarite,
    Quotient,
    Note,
    Organisateur,
)
from core.utils import utils_db
from fiche_famille.utils import utils_internet

csv_dir = "/kantin"


def read_csv(filename: str):
    with open(os.path.join(csv_dir, filename)) as fi:
        rows = csv.DictReader(fi, delimiter=",")
        return list(rows)


def index_parents(parents: list, has_num_type: bool) -> dict:
    index = {}
    for parent in parents:
        id = int(parent["num_parent"]) if parent["num_parent"] else None
        if has_num_type:
            num_type = int(parent["num_type_info"])
            index.setdefault(id, {})[num_type] = parent
        else:
            index[id] = parent
    return index


def index_multi(rows: list, column_name) -> dict:
    index = {}
    for row in rows:
        id = int(row[column_name]) if row[column_name] else None
        index.setdefault(id, []).append(row)
    return index


def read_villes():
    villes = {}
    for ville in read_csv("T_VILLES.csv"):
        villes[ville["Num_ville"]] = ville
    return villes


date_debut_annee = datetime.date.fromisoformat("2023-09-01")
date_fin_annee = datetime.date.fromisoformat("2024-06-30")


def import_jpp():
    Organisateur.objects.create(nom="AEP Skol Diwan An Oriant")

    parents_id = index_parents(read_csv("T_PARENTS_ID_corrigé.csv"), has_num_type=True)
    parents_mel = index_parents(read_csv("T_parents_MEL.csv"), has_num_type=True)
    parents_tel = index_parents(read_csv("T_parents_TEL.csv"), has_num_type=True)
    parents_bqe = index_parents(read_csv("T_PArENTS_BQE.csv"), has_num_type=False)
    parents_dom = index_parents(read_csv("T_parents_dom.csv"), has_num_type=True)
    enfants = index_multi(read_csv("t_enfant.csv"), "num_parent")
    villes = read_villes()

    for skol in read_csv("T_skol.csv"):
        id = int(skol["NUM_SKOL"])
        if id != 2:  # Diwan An Oriant
            continue
        ecole_diwan = Ecole.objects.create(
            idecole=id,
            nom=skol["skol"],
            rue=skol["adresse_école"],
            cp=skol["CP_école"],
            ville=skol["localite_école"],
            tel=skol["tel_école"],
            fax=skol["fax_école"],
            mail=skol["mel_école"],
        )

    classes = {}
    for classe in read_csv("t_class.csv"):
        id_classe = int(classe["NUM_CLASSE"])
        classe = Classe.objects.create(
            idclasse=id_classe,
            ecole=ecole_diwan,
            nom=classe["class"],
            date_debut=date_debut_annee,
            date_fin=date_fin_annee,
        )
        classes[id_classe] = classe

    with open(os.path.join(csv_dir, "identifiants.txt"), "w") as fo:
        fo.write(f"Nom, Identifiant, Mot_de_passe\n")
        for famille_csv in read_csv("T_PArENTS.csv"):
            idfamille = int(famille_csv["num_parent"])

            # if idfamille != 244:
            #    continue
            # Création de la famille

            parents = parents_id[idfamille]
            if 18 in parents:
                # 18 = personnel
                continue

            famille = Famille()
            famille.idfamille = idfamille
            famille.nom = famille_csv["NomFamille"]

            # Création et enregistrement des codes pour le portail
            internet_identifiant = utils_internet.CreationIdentifiant(
                IDfamille=famille.idfamille
            )
            internet_mdp, date_expiration_mdp = utils_internet.CreationMDP()
            famille.internet_identifiant = internet_identifiant
            famille.internet_mdp = internet_mdp
            utilisateur = Utilisateur(
                username=internet_identifiant,
                categorie="famille",
                force_reset_password=True,
                # date_expiration_mdp=date_expiration_mdp,
            )
            utilisateur.save()
            utilisateur.set_password(internet_mdp)
            utilisateur.save()
            famille.utilisateur = utilisateur
            famille.save()

            fo.write(
                f"{famille.nom}, {famille.internet_identifiant}, {famille.internet_mdp}\n"
            )

            print(famille)

            bqe = parents_bqe.get(famille.idfamille, {})
            Mandat.objects.create(
                famille=famille,
                rum=bqe.get("RUM"),
                iban=bqe.get("IBAN"),
                bic="???????????",
                date=date_debut_annee,
            )

            # QF CAF
            Quotient.objects.create(
                famille=famille,
                date_debut=date_debut_annee,
                date_fin=date_fin_annee,
                quotient=int(famille_csv["qf_CAF"]),
                type_quotient_id=1,
            )

            # Note (obs_tel)
            if famille_csv["obs_tel"]:
                Note.objects.create(
                    famille=famille,
                    texte=famille_csv["obs_tel"],
                    rappel_famille=True,
                    date_parution=date_debut_annee,
                )

            parents = parents_id[famille.idfamille]
            for parent_type, parent in parents.items():
                if parent_type == 16:
                    civilite = 1  # pere
                elif parent_type == 15:
                    civilite = 3  # mere
                else:
                    continue

                patronyme = parent["PATRONYME"]
                print("patronyme", patronyme)
                l = patronyme.rsplit(" ", 1)
                if len(l) > 1:
                    nom, prenom = l
                else:
                    prenom = None
                    nom = l[0]

                mail = parents_mel.get(famille.idfamille, {}).get(1, {}).get("Mel")
                mail_parent = parents_mel.get(famille.idfamille, {}).get(
                    parent_type, {}
                ).get("Mel") or parents_mel.get(famille.idfamille, {}).get(
                    3 if parent_type == 16 else 8, {}
                ).get(
                    "Mel"
                )
                mail_pro = (
                    parents_mel.get(famille.idfamille, {})
                    .get(2 if parent_type == 16 else 4, {})
                    .get("Mel")
                )

                tel_domicile = (
                    parents_tel.get(famille.idfamille, {}).get(1, {}).get("tel")
                )
                tel_domicile_parent = (
                    parents_tel.get(famille.idfamille, {})
                    .get(3 if parent_type == 16 else 8, {})
                    .get("tel")
                )

                tel_portable = (
                    parents_tel.get(famille.idfamille, {}).get(5, {}).get("tel")
                )
                tel_portable_parent = parents_tel.get(famille.idfamille, {}).get(
                    6 if parent_type == 16 else 7, {}
                ).get("tel") or parents_tel.get(famille.idfamille, {}).get(
                    parent_type, {}
                ).get(
                    "tel"
                )

                tel_pro = parents_tel.get(famille.idfamille, {}).get(12, {}).get("tel")
                tel_pro_parent = (
                    parents_tel.get(famille.idfamille, {})
                    .get(2 if parent_type == 16 else 4, {})
                    .get("tel")
                )
                tel_portable_compagne = (
                    parents_tel.get(famille.idfamille, {}).get(11, {}).get("tel")
                )
                tel_pro_compagne = (
                    parents_tel.get(famille.idfamille, {}).get(14, {}).get("tel")
                )

                memo = ""
                if tel_portable_compagne:
                    memo += f"Tel portable compagne/on: {tel_portable_compagne}\n"
                if tel_pro_compagne:
                    memo += f"Tel pro compagne/on: {tel_pro_compagne}\n"

                dom = parents_dom.get(famille.idfamille, {}).get(1, {})
                dom_parent = parents_dom.get(famille.idfamille, {}).get(
                    3 if parent_type == 16 else 8, {}
                ) or parents_dom.get(famille.idfamille, {}).get(parent_type, {})
                dom = dom_parent or dom

                print(
                    "VILLE",
                    dom.get("num_VILLE"),
                    villes.get(dom.get("num_VILLE"), {}).get("cp"),
                )

                print("TEL_domicile", tel_domicile, tel_domicile_parent)
                print("TEL_portabl", tel_portable, tel_portable_parent)
                print("TEL_pro", tel_pro, tel_pro_parent)

                individu = Individu.objects.create(
                    civilite=civilite,
                    nom=nom,
                    prenom=prenom,
                    mail=mail_parent or mail,
                    travail_mail=mail_pro,
                    tel_mobile=tel_portable_parent or tel_portable,
                    travail_tel=tel_pro_parent or tel_pro,
                    tel_domicile=tel_domicile_parent or tel_domicile,
                    memo=memo,
                    rue_resid=dom.get("Adresse"),
                    cp_resid=villes.get(dom.get("num_VILLE"), {}).get("cp"),
                    ville_resid=villes.get(dom.get("num_VILLE"), {}).get("ville fr"),
                )
                Rattachement.objects.create(
                    categorie=1, titulaire=True, famille=famille, individu=individu
                )

            for enfant in enfants.get(idfamille, []):
                print("enfant", enfant)
                if enfant["skol"] != "2":
                    continue
                date_naissance = None
                if enfant["date_naissance"]:
                    date_naissance = datetime.datetime.strptime(
                        enfant["date_naissance"], "%m/%d/%y %H:%M:%S"
                    )
                individu_enfant = Individu.objects.create(
                    nom=famille_csv["NomFamille"],
                    prenom=enfant["Prénom"],
                    date_naiss=date_naissance,
                )
                # categorie 2 = enfant
                Rattachement.objects.create(
                    categorie=2, famille=famille, individu=individu_enfant
                )
                Scolarite.objects.create(
                    individu=individu_enfant,
                    ecole=ecole_diwan,
                    classe=classes[int(enfant["num_classe"])],
                    date_debut=date_debut_annee,
                    date_fin=date_fin_annee,
                )

    # Mise à jour de toutes les infos familles et individus
    utils_db.Maj_infos()


import_jpp()
