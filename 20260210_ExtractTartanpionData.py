#!/usr/bin/env python
# -*- coding: utf-8 -*-
# coding: utf8
# #! python2

# python 2 statement
# import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')

import os
import io
import selenium

from bs4 import BeautifulSoup
from bs4 import element
from collections import deque
import json
import glob
import unicodedata

RESDIR = ""
entete_Place = "Lieu,Titre,Nom,Type,Latitude,Longitude,Code,_Partie de,Date ,,,,,,,,,,,,"
entete_Individu = "Individu,Nom,Prénom,Usuel,Suffixe,Préfixe,Titre,Genre,Date de naissance," + \
                  "Lieux de naissance,Source de naissance,Date du baptème,Lieu du baptème," + \
                  "Source du baptème,Date de décès,Lieux du décès,Source du décès," + \
                  "Date de l'inhumation,Lieu de l'inhumation,Source de l'inhumation,Note"
entete_vide = ",,,,,,,,,,,,,,,,,,,,"
entete_Mariage = "Mariage,Mari,Femme,Date ,Lieu ,Source ,Note ,,,,,,,,,,,,,,"
entete_Famille = "Famille ,Enfant,,,,,,,,,,,,,,,,,,,"

wordLst = ["code", "commune", "departement", "acte", "date", "mariage", "nom", "prenom",
           "epoux", "epouse", "lieu", "origine", "naissance", "naiss", "deces", "commentaire", "profession",
           "ex", "conjoint", "pere", "mere", "temoin", "enregistrement", "1", "2", "3", "4"]

import csv

def resoComm(str):
    if len(str.split('/')) == 3:
        # date de naissance
        res = 1
    elif str.find('+') != -1:
        # decede avant la date du mariage
        res = 2
    elif str.isnumeric:
        # age au moment du mariage
        res = 3
    print("res: ", res, str)
    return res

def saveUrl2File(urlSource, fileDest):
    # Importing important library
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager

    # using chrome browser
    driver = webdriver.Chrome(ChromeDriverManager().install())

    # Target url
    driver.get(urlSource)
    # "https://www.geeksforgeeks.org/competitive-programming-a-complete-guide/")

    # Storing the page source in page variable
    page = driver.page_source.encode('utf-8')
    # print(page)

    # open result.html
    # file_ = open('result.html', 'wb')
    file_ = open(fileDest, 'wb')

    # Write the entire page content in result.html
    file_.write(page)

    # Closing the file
    file_.close()

    # Closing the driver
    driver.close()
    return

def rechercheCodeComm(list1, list2):
    return list(set(list1).intersection(list2))

def rechercheCode(list):
    global wordDic, value
    print ("########################################")
    num = wordDic[list[0]]
    for elt in list:
        print(" list(0):", num, elt)
        num = rechercheCodeComm(num, wordDic[elt])
    # place += 1
    print(len(list))
    for i in list:
        print(i,)
    if len(num) > 1:
        num.sort()
    print (len(num), num,)
    if len(num) > 0:
        print(value[num[0]])
        # parcourt elt de list et retire num[0] de wordDic[elt]
        for elt in list:
            # print wordDic[elt]
            wordDic[elt].remove(num[0])
            # print wordDic[elt]
    else:
        print

    return num

def readcsv(filename, content): # genealogySocietyIndex.csv
    with open(filename, 'rb') as f:
        buff = csv.reader(f, delimiter=':')

        for row in buff:
            # for elt in row:
            content.append(row)
    return content

def ecrire(text):
    global extData
    # print text
    extData += text+'\n'

def nettoyer_espaces(s):
   s = s.replace('\r', '')
   s = s.replace('\t', ' ')
   s = s.replace('\f', ' ')
   s = s.replace('\xc2', '_')
   s = s.replace('\xa0', '_')
   return s


croix = u'\xe2\x80\xa0'  # '†'


def supprime_accent(ligne):
    """ supprime les accents du texte source """
    accents = {'a': ['à', 'ã', 'á', 'â', u'\xc3\xa0', '&#224;', '&#225;', '&#226;'],  # ,
               'e': ['é', 'è', 'ê', 'ë', u'\xc3\xa9', u'\xc3\xe8', "&#233;", '&#232;', '&#234;', '&#235;'],  #
               'i': ['î', 'ï', 	'&#238;', '&#239;'],
               'u': ['ù', 'ü', 'û', '&#249;', '&#251;', '&#252;'],
               'o': ['ô', 'ö', '&#244;', '&#246;'],
               'c': ['ç', u'\xc3\xa7', '&#231;'],  #
               '_': ['\r', '\t', '\f', '?', ' ', u'\xc2', u'\xa0', "&#160;", u'\xe2\x80\xa0']}  # last '†'
    line = ligne
    # print("line: ", line, type(line))
    for (char, accented_chars) in accents.items():
        # print("sss: ", type(char), type(accented_chars))
        for accented_char in accented_chars:
            line = line.replace(accented_char, char)
    return line


def lireUrl(url):
    from urllib import request  # python3
    # import urllib.request # python 27
    # sock = urllib.urlopen(url)

    # urllib.request.urlopen(url) # python27
    sock = request.urlopen(url) # python3
    html = sock.read()
    #print ("HTML: ",html)
    #sock.close()
    return (html)


def translateGenDate(date2trans):
    date2trans = date2trans.strip()
    if len(date2trans) > 0:
        # translate to french
        date2trans = date2trans.replace('before', 'avant')
        date2trans = date2trans.replace('after', 'après')
        date2trans = date2trans.replace('about', 'vers')
        date2trans = date2trans.replace('in', '')
        date2trans = wTranslator(date2trans)

        libDate = date2trans
        if date2trans[0] == '/':
            libDate = 'avant ' + date2trans.replace('/', '')
        elif date2trans[-1] == '/':
            libDate = 'après ' + date2trans.replace('/', '')
        date2trans = libDate.strip()

    return date2trans


def readDate1Date2(dateBetweenDash):
    dateLst = dateBetweenDash.split('-')
    date1 = dateLst[0].strip()
    date2 = (lambda: dateLst[1] if len(dateLst) > 1 else "")().strip()
    # test si date1 contains †signe transfert date1 to date2
    if date1.find('†') > -1: date2 = date1.replace('†',""); date1 = ""
    # test si "/" signe
    date1 = translateGenDate(date1)
    date2 = translateGenDate(date2)
    return date1, date2

def idFromtartanpionUrl (url):
    shape = url.replace("https://gw.tartanpion.org/","").split('?')
    dataValList = shape[1]
    profilName = shape[0]

    # date d'import
    from datetime import date
    aujourdhui = date.today()

    # extract pz and nz value from dataValList
    note = "DATA FROM tartanpion --> profile Name: " + profilName + "-"+ str(aujourdhui) + " "
    for elt in dataValList.split('&'):
        couplElt = elt.split('=')
        if couplElt[0] == 'pz':
            note += "--" + couplElt[1] +" "
        if couplElt[0] == 'nz':
            note += couplElt[1] + "-- "
    return note

class tartanpionResultData:
    def __init__(self, filename, note, GoptionFindInfo, traceUrl):
        '''
        :param filename:
        :param note:
        :param GoptionFindInfo: 'lectureRepertoire', 'lectureChaineUrl', 'lectureParamPage'
        :param traceUrl: 'Ok', ""
        '''
        # Origin
        self.unavailData = False
        self.filename = filename
        # self.base = base
        self.note = note
        self.source = ""
        self.error = 0
        self.arboUrl = []
        self.arboHomme = []
        self.arboFemme = []
        self.arboLieu = []
        self.arboAnneeD = []
        self.arboAnneeF = []
        self.arboName = []
        self.arboMariage = []
        self.arboFilename = []

        self.nextUrl = []
        self.pageCourante = 0
        self.traceUrl = traceUrl

        self.indiceFichier = 0
        self.listeDeFichier = []

        self.GoptionFindInfo = GoptionFindInfo
        # si GoptionFindInfo == 'lectureRepertoire' initialise les structures
        dirname = os.path.dirname(self.filename)
        if GoptionFindInfo == 'lectureRepertoire':
            self.listeDeFichier = [dirname+"\\"+f for f in os.listdir(dirname) if os.path.isfile(os.path.join(dirname, f))]
            print("dirname: ", dirname, ": ", self.listeDeFichier)
            # from os import listdir
            # from os.path import isfile, join
            # onlyfiles = [f for f in listdir(dirname) if isfile(join(dirname, f))]
            # print("; ", onlyfiles)

        self.oFileNumber = 0

    def findInfo(self, url):
        """
        :return:
        """

        print("FileInfo: ", self.filename)
        # time.sleep(2)
        if (url == "") or (url == "FILE"):
            # lit un fichier de tartanpion
            f = open(self.filename, "r", encoding="utf8")
            html = f.read()
        else:
            # lit un url de tartanpion
            print("#", url, "#")
            html = lireUrl(url)

        # extraire un sous elt du texte
        soupCD = BeautifulSoup(html, "lxml")
        if self.traceUrl == "Ok":
            with io.open(self.filename + str(oFileNumber) + ".html", "w", encoding="cp1252") as f:
                f.write(str(soupCD.prettify().encode('cp1252', errors='ignore')))
            oFileNumber += 1

        # table resultat
        goalExtract = soupCD.find("div", {"id": "table-resultats"})
        if goalExtract is not None:
            # extrait tous les <a> avec data-id-es commence par "arbres_utilisateur..._1_11379943_7661"
            # ou data-type-fonds="arbres_utilisateur"
            nomA = goalExtract.findAll("a", {"data-type-fonds":"arbres_utilisateur"})
            # pour tous les elt trouve
            dummyTexte = ""
            for num, elt in enumerate(nomA):
                # Prise de href de nomA
                self.arboUrl.append(elt.get ('href'))

                # recherche span avec class="fake-a icon-search-homme"
                femme = ""
                homme = elt.find("span", {"class": "fake-a icon-search-homme"})
                if homme is not None:
                    self.testLongeur(len(self.arboName))
                    self.arboHomme.append(' '.join(homme.text.strip().split()))
                    # recherche span avec class="icon-search-union"
                    femme = elt.find("span", {"class": "icon-search-union"})
                    if femme is not None:
                        femmeElt = femme.text.strip().split('\n')
                        # print ("LEN: ",num, " ", len(femmeElt))
                        self.arboFemme.append(' '.join(femmeElt[-1].strip().split()))
                        if len(femmeElt) >1:
                            self.arboMariage.append(femmeElt[0].strip(' :'))
                        else:
                            self.arboMariage.append(dummyTexte)
                    else:
                        self.arboFemme.append(dummyTexte)
                        self.arboMariage.append(dummyTexte)
                else:
                    # rechercher span class="fake-a icon-search-femme"
                    femme = elt.find("span", {"class": "fake-a icon-search-femme"})
                    if femme is not None:
                        self.arboFemme.append(' '.join(femme.text.strip().split()))
                        homme = elt.find("span", {"class": "icon-search-union"})
                        if homme is not None:
                            hommeElt = homme.text.strip().split('\n')
                            self.arboHomme.append(' '.join(hommeElt[-1].strip().split()))
                            if len(hommeElt) >1:
                                self.arboMariage.append(hommeElt[0].strip(' :'))
                            else:
                                self.arboMariage.append(dummyTexte)
                        else:
                            self.arboHomme.append(dummyTexte)
                            self.arboMariage.append(dummyTexte)
                    else:
                        self.arboFemme.append(dummyTexte)
                        self.arboHomme.append(dummyTexte)
                        self.arboMariage.append(dummyTexte)

                # recherche em avec class="a-tooltip"
                self.arboFilename.append(self.filename)
                self.arboName.append(elt.find("em", {"class": "a-tooltip"}).text.strip())

                # <div class="xlarge-2 large-2 medium-4 small-9 columns small-offset-3 medium-offset-0 text-large">
                #             <span class="text-for-m1obile">Year:</span>
                #             1835 - 1835
                # </div>
                anneeG = elt.find("div", {"class": \
                            "xlarge-2 large-2 medium-4 small-9 columns small-offset-3 medium-offset-0 text-large"})
                annee = anneeG.span.next_sibling
                if annee is not None:
                    anneeL = annee.text.strip().split('-')
                    self.arboAnneeD.append(anneeL[0])
                    self.arboAnneeF.append(anneeL[1])
                else:
                    self.arboAnnee.append(dummyTexte)

                # <div class="xlarge-4 large-4 medium-4 small-9 columns small-offset-3 medium-offset-0 text-large">
                #             Sóller, Islas Baleares, Spain
                # </div>
                lieu = elt.find("div", {"class": \
                            "xlarge-4 large-4 medium-4 small-9 columns small-offset-3 medium-offset-0 text-large"})
                if lieu is not None:
                    self.arboLieu.append(lieu.text.strip())
                else:
                    self.arboLieu.append(dummyTexte)

                # <div class="xlarge-0 large-0 medium-0 small-9 columns small-offset-3 text-light text-small sourcename">
                #             <em>fcombelles</em>
                # </div>
                self.printArbo(num)

        else:
            print ("Pas de div - id = table-resultats DANS CE FICHIER")

        '''
        # structure de Url:
        '''
        url1="https://en.tartanpion.org/fonds/individus/?categories_1__arbres__=arbres&amp;categories_2__arbres%23geneastar__=arbres%23geneastar&amp;categories_2__arbres%23utilisateur__=arbres%23utilisateur&amp;country__0__=ESP&amp;exact_day=&amp;exact_month=&amp;exact_year=&amp;from=1800&amp;go=1&amp;id_filter_block=search-filter-categories&amp;ignore_each_patronyme=&amp;ignore_each_patronyme_conjoint=&amp;ignore_each_patronyme_mere=&amp;ignore_each_patronyme_pere=&amp;ignore_each_place=&amp;ignore_each_prenom=&amp;ignore_each_prenom_conjoint=&amp;ignore_each_prenom_mere=&amp;ignore_each_prenom_pere=&amp;ignore_each_profession=&amp;nom=&amp;nom_conjoint=&amp;nom_mere=&amp;nom_pere=&amp;page=1&amp;place__0__=soller&amp;prenom=&amp;prenom_conjoint=&amp;prenom_conjoint_operateur=and&amp;prenom_mere=&amp;prenom_mere_operateur=and&amp;prenom_operateur=or&amp;prenom_pere=&amp;prenom_pere_operateur=and&amp;profession=&amp;profession_operateur=and&amp;region__0__=BAL&amp;sexe=&amp;size=50&amp;to=1900&amp;type_periode=between&amp;voisinage=&amp;with_parents=0&amp;zonegeo__0__=Islas+Baleares,+Spain"
        url2="https://en.tartanpion.org/fonds/individus/?categories_1%5Barbres%5D=arbres&amp;categories_2%5Barbres%23utilisateur%5D=arbres%23utilisateur&amp;categories_2%5Barbres%23geneastar%5D=arbres%23geneastar&amp;country%5B0%5D=ESP&amp;exact_day=&amp;exact_month=&amp;exact_year=&amp;from=1800&amp;go=1&amp;id_filter_block=search-filter-categories&amp;ignore_each_patronyme=&amp;ignore_each_prenom=&amp;nom=&amp;page=2&amp;place%5B0%5D=soller&amp;prenom=&amp;prenom_operateur=and&amp;region%5B0%5D=BAL&amp;sexe=&amp;size=50&amp;to=1900&amp;type_periode=between&amp;zonegeo%5B0%5D=Islas+Baleares,+Spain"
        ''''''
        if self.GoptionFindInfo == 'lectureRepertoire': # lit les fichiers d'un repertoire'
            # copie le nom de fichier suivant dans self.filename
            # listeDeFichier {?}, indiceFichier {?}
            self.indiceFichier += 1
            print ("Longueur liste Fichier: ", len(self.listeDeFichier))
            print("Indice Fichier: ", self.indiceFichier)
            if self.indiceFichier >= len(self.listeDeFichier):
                urlNext = ""
            else:
                self.filename = self.listeDeFichier[self.indiceFichier]
                urlNext = "FILE"
        if self.GoptionFindInfo == 'lectureChaineUrl': # lit url puis chaine les urls suivants
            urlNext = ""
            goalExtract = soupCD.find("div", {"class": "clearfix"})
            if goalExtract is not None:
                # lit li class = 'arrow' puis select <a> 'href'
                suitA = goalExtract.find("li", {"class": "arrow"})
                if suitA is not None:
                    nomA = suitA.find("a")
                    urlNext = nomA.get('href')

            print("urlNext: ", "#", urlNext, "#")
            # recherche le nom du site dans URL sinon completer
            if urlNext.find('https://') == -1 :
                print('urlNext1: ', urlNext)
                urlNext = 'https://gw.tartanpion.org'+urlNext
                print('urlNext2: ', urlNext)
        if self.GoptionFindInfo == 'lectureParamPage' : # incremente le parametre page de l'Url
            self.pageCourante += 1
            urlNext = self.modifyUrlParam(url2, 'page', self.pageCourante)
            if self.pageCourante > 3:
                exit(6)
        return urlNext

    def modifyUrlParam(self, url, param, value):
        obj2find = param + '='
        paramSep = "&amp;"

        debUrlD = url.find(obj2find)
        url[url.find(obj2find):len(url)]
        b = url.find(obj2find)
        urlD = url[:b]
        urlF = url[b:]
        debUrlF = urlF.find(paramSep)
        urlF = urlF[debUrlF:]
        newUrl = urlD + obj2find + str(value) + urlF
        print(newUrl)
        return (newUrl)

    def testLongeur(self,num):
        if len(self.arboHomme) != len(self.arboMariage):
            self.printLongeur(num)
        return

    def printLongeur(self,num):
        print("ERREUR ligne: ", num, \
              str(len(self.arboName)) + sep + \
              str(len(self.arboMariage)) + sep + \
              str(len(self.arboFemme)) + sep + \
              str(len(self.arboHomme)) + sep + \
              str(len(self.arboUrl)) + sep + \
              str(len(self.arboAnneeD)) + sep + \
              str(len(self.arboAnneeF)) + sep + \
              str(len(self.arboFilename)) + sep + \
              str(len(self.arboLieu)) + sep \
              )
        exit(7)
        return

    def printArbo(self, num):
        print ("##############################################")
        print ("Url: ", self.arboUrl[num])
        print ("Name: ", self.arboName[num])
        print ("Lieu: ",self.arboLieu[num])
        print ("AnneeD: ", self.arboAnneeD[num])
        print ("AnneeF: ", self.arboAnneeF[num])
        print ("Date de mariage: ", self.arboMariage[num])
        print ("Epouse: ", self.arboFemme[num])
        print ("Epoux: ", self.arboHomme[num])
        print ("Url: ", self.arboUrl)
        print ("File: ", self.arboFilename[num])
        return

    def getAllArbo(self):
        finDeLigne = '\n'
        sep = ','
        # copier les entetes en première ligne
        buff = "Name"+sep+"Lieu"+sep+"Mariage"+sep+"Epouse"+sep+"Epoux"+sep+\
               "debut"+sep+"fin"+sep+"Url"+sep+"filename"+finDeLigne
        for num, elt in enumerate(self.arboName):
            try:
                # buff += '"'+"LIEN.HYPERTEXTE("+self.arboName[num]+';'+self.arboUrl[num]+')"'+sep
                buff += '"'+self.arboName[num]+'"' + sep
                buff += '"'+self.arboLieu[num]+'"' + sep
                buff += self.arboMariage[num] + sep
                buff += '"'+self.arboFemme[num]+'"' + sep
                buff += '"'+self.arboHomme[num]+'"' + sep
                buff += self.arboAnneeD[num] + sep
                buff += self.arboAnneeF[num] + sep
                buff += '"'+self.arboUrl[num]+'"'+sep
                buff += '"'+self.arboFilename[num]+'"' + finDeLigne
            except:
                self.printLongeur(num)
        return buff

    def printInfo(self):

        return

def formatDate (dateElt):
    txt = dateElt.split(',')
    if len(txt) == 2:
        annee = txt[1]
        txt2 = txt[0].split()
        if len(txt2) == 2:
            jour = txt2[1]
            mois = txt2[0]
        else:
            print("Erreur txt2: ", txt2)
            jour = ""
            mois = txt2[0]
        dateElt = jour + ' ' + mois + ' ' + annee
    else:
        dateElt = dateElt
    return dateElt

class tartanpionData:
    def __init__(self, base, url, note):
        # Origin
        self.unavailData = False
        self.url = url
        self.base = base
        self.note = note
        self.source = ""
        self.error = 0

        self.codeCommune = ""
        self.commune = "" # voir conjoint_m_place
        self.codeDepartement = ""
        self.departement = ""
        self.acte = ""

        self.temoin_nom = []
        self.temoin_prenom = []
        self.temoin_commentaire = []

        self.witness = ""

        # etatCivil
        self.sexe = ""
        self.nom = ""
        self.prenom = ""
        self.date_naissance = ""
        self.place_naissance = ""
        self.date_deces = ""
        self.place_deces = ""
        self.age_deces = ""
        self.profession = ""
        self.commentaire = ""
        self.ex_conjoint_nom = ""
        self.ex_conjoint_prenom = ""

        # Parent
        self.relative_nom = ["", ""]
        self.relative_prenom = ["", ""]
        self.relative_date_naissance = ["", ""]
        self.relative_date_deces = ["", ""]
        self.relative_url = ["", ""]
        self.relative_profession = ["", ""]
        self.relative_commentaire = ["", ""]
        self.relative_Nber = ["", ""]

        # Conjoint
        self.conjoint_nom = []
        self.conjoint_prenom = []
        self.conjoint_date_n = []
        self.conjoint_lieu_n = []
        self.conjoint_date_d = []
        self.conjoint_lieu_d = []
        self.conjoint_m_date = []
        self.conjoint_m_place = []
        self.conjoint_FNber = []
        self.conjoint_commentaire = []
        self.conjoint_profession = []
        self.conjoint_ex_nom = []
        self.conjoint_ex_prenom = []
        self.conjoint_witness = []

        # Parent_Conjoint
        self.conjoint_relative_nom = ["", ""]
        self.conjoint_relative_prenom = ["", ""]
        self.conjoint_relative_date_naissance = ["", ""]
        self.conjoint_relative_date_deces = ["", ""]
        self.conjoint_relative_commentaire = ["", ""]
        self.conjoint_relative_profession = ["", ""]
        self.conjoint_relative_Nber = ["", ""]

        # Enfant
        self.enfant_nom = []
        self.enfant_prenom = []
        self.enfant_date_n = []
        self.enfant_date_d = []
        self.enfant_FNber = []
        self.enfant_sexe = []

        self.pere_ind = 0
        self.mere_ind = 1

        self.logErreur = ""

        self.textLu = {}
        return

    def __str__(self):
        return str(self)

    def print_conjoint(self):
        print("conjoint_nom: ", self.conjoint_nom)
        print("conjoint_prenom: ", self.conjoint_prenom)
        print("conjoint_date_n: ", self.conjoint_date_n)
        print("conjoint_lieu_n: ", self.conjoint_lieu_n)
        print("conjoint_date_d: ", self.conjoint_date_d)
        print("conjoint_lieu_d: ", self.conjoint_lieu_d)
        print("conjoint_m_date: ", self.conjoint_m_date)
        print("conjoint_m_place: ", self.conjoint_m_place)
        print("conjoint_FNber: ", self.conjoint_FNber)
        print("conjoint_commentaire: ", self.conjoint_commentaire)
        print("conjoint_profession: ", self.conjoint_profession)
        print("conjoint_ex nom:", self.conjoint_ex_nom)
        print("conjoint_ex prenom:", self.conjoint_ex_prenom)
        print()

    def print_conjoint_relative(self):
        print("conjoint_relative_nom: ", self.conjoint_relative_nom)
        print("conjoint_relative_prenom :", self.conjoint_relative_prenom)
        print("conjoint_relative_date de naissance: ", self.conjoint_relative_date_naissance)
        print("conjoint_relative_date de deces", self.conjoint_relative_date_deces)
        print("conjoint_relative_commentaire", self.conjoint_relative_commentaire)
        print("conjoint_relative_profession", self.conjoint_relative_profession)
        print("conjoint_relative_Nber", self.conjoint_relative_Nber)
        print()

    def print_enfant(self, ind):
        print("enfant_nom", self.enfant_nom)
        print("enfant_prenom: ", self.enfant_prenom)
        print("enfant_date_n: ", self.enfant_date_n)
        print("enfant_date_d: ", self.enfant_date_d)
        print("enfant_FNber: ", self.enfant_FNber)
        print("enfant_sexe", self.enfant_sexe)
        print()

    def print_etatCivil(self):
        print ("\n###### ETAT_CIVIL ######")
        print ("sexe:", self.sexe)
        print ("nom:", self.nom)
        print ("prenom:", self.prenom)
        print ("date_naissance:", self.date_naissance)
        print ("place_naissance:", self.place_naissance)
        print ("date_deces:", self.date_deces)
        print ("place_deces:", self.place_deces)
        print ("age_deces:", self.age_deces)
        print ("profession:", self.profession)
        print ("commentaire: ", self.commentaire)
        print()

    def print_parents(self):
        print ("relative_nom", self.relative_nom)
        print ("relative_prenom", self.relative_prenom)
        print ("relative_date_naissance", self.relative_date_naissance)
        print ("relative_date_deces", self.relative_date_deces)
        print ("relative_url", self.relative_url)
        print ("relative_commentaire", self.relative_commentaire)
        print ("relative_profession", self.relative_profession)
        print ("relative_Nber", self.relative_Nber)
        print()

    def print_autre(self):
        print ("unavailable: ", self.unavailData)
        print ("url: ", self.url)
        print ("base: ", self.base)
        print ("note: ", self.note)
        print ("codeCommune: ", self.codeCommune)
        print ("commune: ", self.commune)
        print ("codeDepartement: ", self.codeDepartement)
        print ("departement: ", self.departement)
        print ("acte: ", self.acte)
        print()

    def print_temoin(self):
        print ("temoins_nom:", self.temoin_nom)
        print ("temoins_prenom:", self.temoin_prenom)
        print ("temoins_commentaire:", self.temoin_commentaire)
        print()

    def findInfo(self):
        """
        # Lieu 	Titre	Nom 	Type 	Latitude	Longitude	Code	_Partie de	Date
        # Individu,Nom,Prénom,Usuel,Suffixe	Préfixe	Titre	Genre	Date de naissance
        #           Lieux de naissance	Source de naissance	Date du baptême	Lieu du baptême	Source du baptême
        #           Date de décès	Lieux du décès	Source du décès	Date de l'inhumation	Lieu de l'inhumation
        #           Source de l'inhumation	Note
        # Mariage	Mari	Femme	Date 	Lieu 	Source 	Note
        # Famille 	Enfant
         self.error : 1 // pas d'arbre
                      2 // individu introuvable
                      0 // Ok
        :return:
        """

        # lit un fichier de tartanpion
        print(self.url)
        html = lireUrl(self.url)
        # f = open(url, "r")
        # html = f.read()
        # extraire un sous elt du texte
        soupCD = BeautifulSoup(html, "lxml")

        # todo test les cas extremes
        #  ## Erreur ProfilName inconnu span id="no_arbre" *1
        #  ## Erreur nom inconnu         h1 class="error" "Individu introuvable : " *2
        #  ## Erreur prenom inconnu      h1 class="error" "Individu introuvable : " *3
        # test erreur
        goalExtract = soupCD.find("span", {"id": "no_arbre"})
        if goalExtract is not None:
            text = goalExtract.getText()
            if text.find("no family tree") > 0:
                self.error = 1
        goalExtract = soupCD.find("h1", {"class": "error"})
        if goalExtract is not None:
            text = goalExtract.getText()
            if text.find("dividu introuvable") > 0\
                or text.find("dividual not found") > 0:
                self.error = 2
                print ("############### erreur 2 ###################")

        goalExtract = soupCD.find("div", {"class": "page_max row"})
        noteInd = soupCD.find("div", {"class": "fiche-note-ind"})

        # print "goalExtract: ", goalExtract
        '''
        if goalExtract is not None:
            text = goalExtract.getText()
        else:
            text = "Value Not Found"
        '''

        nomPage = soupCD.find("h1", {"class": "with_tabs name"})

        if nomPage is None:
            self.unavailData = True
            return

        nomA = nomPage.findAll("a")
        self.textLu['SEXE'] = soupCD.find('img').get('title')
        # print "SEXE: " + self.textLu['SEXE']

        # todo: voir/tester la selection nom/prenom -- OK
        lib = ["prenom", "nom"]
        for num, elt in enumerate(nomA):
            libelle = lib[num].upper()
            text = elt.getText().strip().replace('?', '')

            self.textLu[libelle] = text
            # print(libelle + ": " + self.textLu[libelle])

        # extraire les UL et LI
        ulLst = goalExtract.findAll("ul")
        h2Lst = goalExtract.findAll("h2")
        diff_h2_ul = len(ulLst) - len(h2Lst)
        # numh2 = - diff_h2_ul -1
        numh2 = -1
        numb = 0
        cpt_str = ""
        libelle = "ETAT-CIVIL"
        self.textLu[libelle] = ulLst[0]

        # recuperation des differents titres de chapitre (Libelle)
        # et des contextes associes
        for ul_elt in ulLst:
            numb += 1

            if numb > 1:
                '''
                print "numh2: "+str(numh2), type(libelle), type(self.textLu[libelle])
                print libelle + ": ", self.textLu[libelle]
                '''
                # todo : verifier contenu Half-siblings pour URL en cours Marie Marcel Ernest CHATELAIN
                libelle = h2Lst[numh2].getText().strip().upper()+cpt_str
                self.textLu[libelle] = ul_elt

            if numh2 < len(h2Lst)-1:
                numh2 += 1
            else:
                cpt_str = str(numb)

        # creation rubrique Notes et sources si elles n'existent pas
        self.textLu['NOTES'] = noteInd
        self.textLu['SOURCES'] = BeautifulSoup("", "lxml")
        # print "NOTES : ", self.textLu['NOTES']
        # print "SOURCES : ", self.textLu['SOURCES']

        return 0

    def printTextLu(self):
        section = ["SEXE", "PRENOM", "NOM", "ETAT-CIVIL", "PARENTS", "SPOUSES  AND CHILDREN",
                   "HALF-SIBLINGS", "SOURCES", "PHOTOS AND ARCHIVAL RECORDS",
                   "FAMILY TREE PREVIEW", "URL_PERE", "URL_MERE"]
        finDeLigne = '\n'
        fctName = "printTextLu"
        # for ind, elt in enumerate(textLu):
        buff = fctName + finDeLigne
        buff += "################################################" + finDeLigne
        for elt in section:
            if elt in self.textLu:
                '''

                print "elt: ", elt
                print self.textLu[elt]
                print "elt ci-dessus"
                '''

                '''if elt is None:
                    print "elt is None"
                else:
                    print "elt is not(None)"
                if self.textLu[elt] is None:
                    print "self.textLu[elt] is None", self.textLu[elt]
                else:
                    print "self.textLu[elt] is not (None)", self.textLu[elt]
                    print "coucou"

                print "text: ", self.textLu[elt]
                '''
                # try:
                # if type (self.textLu[elt])

                if isinstance(self.textLu[elt], element.Tag):
                    print(fctName+" bs4.element.Tag", self.textLu[elt].content)
                    str_obj = (lambda x: "" if x is None else x.getText())(self.textLu[elt])
                else:
                    print (fctName+" Type: ", type(self.textLu[elt]), self.textLu[elt])
                    str_obj = (lambda x: "" if x is None else x)(self.textLu[elt])

                print(fctName+" str_obj: ", type(str_obj), str_obj)
                buff += elt + ": "+finDeLigne + str_obj +finDeLigne
                #except:
                 #   pass
        buff += "###############################################" + finDeLigne
        buff += "Element de textLu nouveau par rapport à la liste prédéfinie: " + finDeLigne
        for elt in self.textLu:
            if elt not in section:
                text = (lambda x: "" if x is None else x.getText())(self.textLu[elt])
                buff += elt + ": " + finDeLigne + str(text) + finDeLigne
        buff += "###############################################" + finDeLigne
        return buff

    def read_consort_data(self, CNber, f_ind, elt):
        #
        print("read_consort, elt: ", elt)
        # None
        trace = False

        li = (lambda x: "" if x is None else x.getText())(elt.find("li"))
        # in 1787, Passonfontaine, 25690, Doubs, Franche-Comté, France,
        em = (lambda x: "" if x is None else x.getText())(elt.find("em"))
        # Jeanne Agnès Roussel
        # todo lire la seconde occurence de a puisqu'elle contient le nom --fait 4/2/2024
        # Find all tag's occurrences
        list_of_occurrences = elt.find_all("a")
        # Access the second occurrence
        if list_of_occurrences is not None:
            if len(list_of_occurrences) == 1:
                a = list_of_occurrences[0].getText()
            else:
                a = list_of_occurrences[1].getText()
        # a = (lambda x: "" if x is None else x.getText())(elt.find_all())
        # 1759-  # date de naissance et de deces
        bdo = (lambda x: "" if x is None else x.getText())(elt.find("bdo"))
        print("li: ", elt.find("li"), "\nem: ", em, "\na :", a, "\nbdo:", bdo)
        nom_prenom = a.strip().split()
        if len(nom_prenom) == 0:
            print("ERREUR PAS DE DONNEES CONJOINT")
            return
        nom = nom_prenom[-1].replace('?', '').capitalize()
        prenom = (" ".join(map(str, nom_prenom[:-1]))).replace('?', '')
        date_n, date_d = readDate1Date2(bdo.strip())
        m_date_place = em.strip(' ,').split(',')
        # October 4, 1766, MANOSQUE,  -- maj 20240218
        if len(m_date_place) > 1:
            if m_date_place[1].strip().isdigit():
                m_date = m_date_place[0] + " " + m_date_place[1]
                ldate = m_date.split()
                m_date = ldate[1] + " " + ldate[0] + " " + ldate[2]
                m_date = wTranslator(m_date.strip())
                m_place = ",".join(map(str, m_date_place[2:])).strip(' ,')
            else:
                if len(m_date_place) == 3:
                    m_date= m_place= ""
                    print("ERREUR DATE MARRIAGE :", em, len(m_date_place) )
                else:
                    m_date = wTranslator(m_date_place[0].strip())
                    m_place = m_date_place[1].strip()
        else:
            m_date = wTranslator(m_date_place[0].strip())
            m_place = ""

        m_date = translateGenDate(m_date)

        print("MMMM: \nm_date", m_date, "\nm_place", m_place, "\nlen :", len(m_date_place))
        #
        if trace:
            print()
            print("CONJOINT: ")
            print("li: ", li)
            print("em: ", em)
            print("a: ", a)
            print("bdo: ", bdo)
            print("conjoint:  ", nom, sep, prenom, sep, date_n, sep, date_d, sep, m_date, sep, m_place)
            print()
        #

        self.conjoint_nom.append(nom)
        self.conjoint_prenom.append(prenom)
        self.conjoint_date_n.append(date_n)
        self.conjoint_date_d.append(date_d)
        self.conjoint_m_date.append(m_date)
        self.conjoint_m_place.append(m_place)
        self.conjoint_FNber.append(f_ind)
        self.conjoint_profession.append("") # to be defined
        self.conjoint_lieu_n.append("") # to be defined
        self.conjoint_lieu_d.append("")  # to be defined
        self.conjoint_witness.append("") # to be defined

        return

    def print_consort_data(self, CNber):
        print("nom: ", self.conjoint_nom[CNber])
        print("prenom: ", self.conjoint_prenom[CNber])
        print("date_n: ", self.conjoint_date_n[CNber])
        print("date_d: ", self.conjoint_date_d[CNber])
        print("m_date: ", self.conjoint_m_date[CNber])
        print("m_place: ", self.conjoint_m_place[CNber])
        return

    def read_relative_data(self, ind, a_href, bdo):
        print("Parents 'read_relative' : a_href, \n",a_href, "\nind: ", ind, "\nbdo :", bdo)
        base = "https://gw.tartanpion.org/"
        if ind == 0:
            num = 1
        else:
            num = 3
        nom_prenom = a_href[num].getText().split()
        if len(nom_prenom) == 0:
            return
        self.relative_nom[ind] = nom_prenom[-1]
        # todo: faire la selection des prenoms sur casse des caracteres Nom == UPPER range
        self.relative_prenom[ind] = " ".join(map(str, nom_prenom[:-1]))
        # date
        if len(bdo) > ind:
            date = readDate1Date2(bdo[ind].getText())
        else:
            date = ["", ""]
        self.relative_date_naissance[ind] = date[0]
        self.relative_date_deces[ind] = date[1]
        # Url
        self.relative_url[ind] = base + a_href[num]['href']
        print('relative nom:', self.relative_nom)
        print('relative prenom:', self.relative_prenom)
        return

    def print_relative_data(self, ind):
        print("nom: ", self.relative_nom[ind])
        print("prenom: ", self.relative_prenom[ind])
        print("date_n: ", self.relative_date_naissance[ind])
        print("date_d: ", self.relative_date_deces[ind])
        print("url: ", self.relative_url [ind])
        return

    def read_children_data(self, e_ind, f_ind, childElt):
        print("childElt: ", childElt)
        # None
        li = (lambda x: "" if x is None else x.getText())(childElt.find("li"))
        print("li: ", li)
        # pointe vers un fichier de representation du sexe
        src = (lambda x: "" if x is None else x["src"])(childElt.find("img"))
        print("img: ", src)
        # Jeanne Agnès Roussel
        allA = childElt.find("a")
        # s'il y a deux tag "a" on prend le contenu du deuxième sinon le premier
        allA = childElt.find_all("a")
        if len(allA) > 1:
            a = "TOTO : " + allA[1].getText()
        else:
            a = allA[0].getText()

        print("a: ", a)

        # 1759-  # date de naissance et de deces
        bdo = (lambda x: "" if x is None else x.getText())(childElt.find("bdo"))
        print("bdo: ", bdo)
        nom_prenom = a.strip().split()
        # todo: modifier l'algo de selection du nom
        # todo: il est forme des mots en majuscules dans la phrase
        if len(nom_prenom) == 0:
            return
        nom = nom_prenom[-1].capitalize()
        prenom = " ".join(map(str, nom_prenom[:-1]))
        date_n, date_d = readDate1Date2(bdo.strip())
        # extraction du sexe dans un fichier de description en (anglais)
        sexe = (lambda x: 'F' if x == 'female' else 'M')(src.split('/')[1].split('.')[0])
        # todo a rempalacer par la fonction d'affichage adequate
        self.enfant_nom.append(nom)
        self.enfant_prenom.append(prenom)
        self.enfant_FNber.append(f_ind)
        self.enfant_date_n.append(date_n)
        self.enfant_date_d.append(date_d)
        self.enfant_sexe.append(sexe)
        return

    def print_children_data(self, e_ind):
        print ("nom: ", self.enfant_nom[e_ind])
        print ("prenom: ", self.enfant_prenom[e_ind])
        print ("famille n°: ", self.enfant_FNber[e_ind])
        print ("date_n: ", self.enfant_date_n[e_ind])
        print ("date_d: ", self.enfant_date_d[e_ind])
        print ("sexe: ", self.enfant_sexe[e_ind])

    def xtr_naissance(self, naissance):
        # ligne naissance de la forme
        # Born about 1673 - Saignelégier (CH)
        self.date_naissance = naissance.split('-')[0]
        self.date_naissance = translateGenDate(self.date_naissance.replace('Born ', ''))
        # Born August 26, 1789 # 2024018
        # print("xxxx: ", self.date_naissance)
        if self.date_naissance.find(',') > -1:
            self.date_naissance = self.date_naissance.replace(',', ' ')
            lnais = self.date_naissance.split()
            if len(lnais) > 2:
                self.date_naissance = lnais[1] + " " + lnais[0] + " " + lnais[2]
            else:
                if len(lnais) > 1:
                    self.date_naissance = lnais[1] + " " + lnais[0]
                print("Erreur lnais < 2 ", lnais)
                self.date_naissance = ",".join(lnais)
        self.date_naissance = supprime_accent(self.date_naissance)

        # 2022 Mars --- supprimer le caractere souligné dans la date

        print("date_naissance: ", self.date_naissance, ", nom: ", self.nom, ", prenom: ", self.prenom)
        # print(type(self.date_naissance), type(self.nom), type(self.prenom))
        self.place_naissance = "-".join(map(str, naissance.split('-')[1:])).strip()


    def xtr_deces(self, deces):
        # ligne deces de la forme:
        # Deceased 15 October 1708 [- Charquemont (25)], aged about 35 years old
        print("Date Deces: ", deces)
        decesLstMoins = deces.split('-')
        self.date_deces = decesLstMoins[0].split('-')[0]
        self.date_deces = translateGenDate(self.date_deces.replace('Deceased', ''))
        # Deceased August 26, 1789 # 2024018
        print("yyyy: ", self.date_deces)
        if self.date_deces.find(',') > -1:
            self.date_deces = self.date_deces.replace(',', ' ')
            ldeces = self.date_deces.split()
            self.date_deces = ldeces[1] + " " + ldeces[0] + " " + ldeces[2]

        print("date_deces: ", self.date_deces, ", nom: ", self.nom, ", prenom: ", self.prenom)

        if len(decesLstMoins) > 1:  # il existe un composant place
            place_decesInt = "-".join(map(str, decesLstMoins[1:]))
            place_decesLst = place_decesInt.split(',')
            print("place_decesLst: ", place_decesLst)

            if len(place_decesLst) > 1 or place_decesLst[-1].find('aged'):
                # Il existe un composant age
                self.age_deces = place_decesLst[-1]
                del place_decesLst[-1]
            self.place_deces = ",".join(map(str, place_decesLst)).strip()
        else:  # age_deces est le dernier composant de la ligne
            place_decesLst = decesLstMoins[0].split(',')
            self.age_deces = place_decesLst[-1]



    def xtr_profession(self, prof):
        self.profession = prof

    def analyseSpousesChildren(self, cle):
        global num_Famille

        print("SP & CH testlu: ", type(self.textLu[cle]), self.textLu[cle])
        print("text: ", self.textLu[cle].getText())

        a_href = self.textLu[cle].findAll("a")
        bdo = self.textLu[cle].findAll("bdo")
        li = self.textLu[cle].find("li")
        print("\nli :", li, "\n type: ", type(li))
        '''
        print "a_href: ", a_href
        for elt in a_href:
            print "--:", elt
            print "1.:", elt.getText()
        print "a: ", bdo
        for elt in bdo:
            print "--:", elt.getText()
            print "2.:", elt.getText()
        print "li: ", li
        '''
        FNber = num_Famille
        ENber = 0
        CNber = 0
        # todo: tester ERREUR deuxieme conjoint avec fichier suivant
        # todo: url="https://gw.tartanpion.org/ammr?lang=en&pz=alain&nz=roussel&p=jean+claude&n=jeanneret"
        # todo: tester avec url suivant enfant au 2ième mariage, prenom des conjoint (?)
        # todo: url="https://gw.tartanpion.org/ammr?lang=en&pz=alain&nz=roussel&p=jeanne&n=corne"
        # todo: verifier ensuite la repartition des enfants

        ul = li.find("ul")
        print('\nul: ', ul)
        if ul is None:
            print("mariage sans enfant: ", li)
            # print("\nli :", li, "\n type: ", type(li))
            # print("mariage sans enfant: ", li.getText())
            tt = li.getText()
            pos = tt.find('to')
            if pos == -1:
                print("absence mot cle to: ", tt)
            else:
                # extraire elt conjointe sans enfant
                self.read_consort_data(CNber, FNber, li)
                CNber += 1
        else:
            print("famille: ")  # , elt.getText()
            # parcours ul pour extraire les enfants
            familyElt = ul.findAll("li")
            for childElt in familyElt:
                self.read_children_data(ENber, FNber, childElt)
                # todo  elt.ul.decompose() -- suppression verifier utilite
                # extraire elt conjointe
            self.read_consort_data(CNber, FNber, li)
            CNber += 1
        num_Famille += 1

        # recherche des temoins du marriage
        # exemple:
        # Married 2 February 1693, Charquemont (25), to Jean Joseph MAILLOT 1673-1708
        # (witnesses : Jean ABRY /1656-1693/ , Françoise MOUGIN ca 1635-1725 , Jean Antoine CHATELAIN †1693/ )
        # with
        # self.textLu['WITNESS'] = "<p></p>"
        line = self.textLu[cle].getText()
        to_pos = line.find("to") + 2
        with_pos = line.find("with")
        print("with_pos: ", to_pos, with_pos)
        if to_pos == with_pos:  # donc == -1
            print("witness notFound", line)
        else:
            reduceLine = line[to_pos: with_pos]
            parE = reduceLine.find('(') + 1
            parF = reduceLine.find(')')
            print("parE: ", parE, parF)
            if parE == parF:  # donc == -1
                print("witness notFound", reduceLine)
            else:
                # self.textLu['WITNESS'] = reduceLine[parE, parF]
                self.witness = reduceLine[parE: parF].strip()

    def extractData2(self):
        global num_Famille
        #### EXTRACTION DES DONNEES STRUCTURE INTERMEDIAIRE dictionnaire textLu[]
        print("Textlu: ", self.printTextLu())
        if self.unavailData:
            return

        # caracteristique enregistrement
        self.sexe = self.textLu['SEXE']
        #########
        cle = 'PRENOM'
        if (cle in self.textLu):
            self.prenom = self.textLu['PRENOM'].replace(',' , ' ')
        else:  # cle not in textLu
            self.logErreurHisto("ERREUR *** "+cle + " not in textLu")

        cle = 'NOM'
        if (cle in self.textLu):
            self.nom = self.textLu['NOM'].capitalize()
        else:  # cle not in textLu
            self.logErreurHisto("ERREUR *** "+cle + " not in textLu")

        print("nom: ", self.nom, ", prenom: ", self.prenom)

        ### ETAT-CIVIL ###
        cle = 'ETAT-CIVIL'
        if (cle in self.textLu):
            print("ETAT-CIVIL", type(self.textLu[cle]), self.textLu[cle])
            etat_civil = self.textLu[cle].findAll("li")

            print("ETAT_CIVIL: ", etat_civil)

            # print("NNN: ", self.nom, type(self.nom))
            # NNN = self.nom.encode('ascii', 'xmlcharrefreplace')
            # NNN = self.nom
            # str(byte_string, encoding='utf-8')
            # row[0].decode('ISO-8859-1')
            # print("NNN: ", NNN, type(NNN))

            self.nom = supprime_accent(self.nom).capitalize()
            self.prenom = supprime_accent(self.prenom)

            EC0 = (lambda x, y: "" if len(x) < y+1 else x[y].getText())(etat_civil, 0)
            EC1 = (lambda x, y: "" if len(x) < y+1 else x[y].getText())(etat_civil, 1)
            EC2 = (lambda x, y: "" if len(x) < y+1 else x[y].getText())(etat_civil, 2)

            if EC0.find('Born') > -1:
                self.xtr_naissance(EC0)
                if EC1.find('Deceased') > -1:
                    self.xtr_deces(EC1)
                    self.xtr_profession(EC2)
                else:
                    self.xtr_profession(EC1 + EC2)
            else:
                self.xtr_deces(EC0)
                self.xtr_profession(EC1 + EC2)
            # todo: possibilité de normaliser les textes
            # todo: >>> import unicodedata
            # todo: >>> unicodedata.normalize('NFKD', u'aあä').encode('ascii', 'ignore') # donne "aa"

            self.print_etatCivil()

        else:  # cle not in textLu
            self.logErreurHisto("ERREUR *** "+cle + " not in textLu")

        ### PARENTS ###
        cle = 'PARENTS'
        if (cle in self.textLu):
            print("Parents - testlu: ", type(self.textLu[cle]), self.textLu[cle])
            print("Parents - text: ", self.textLu[cle].getText())
            # eclater les champs
            a_href = self.textLu[cle].findAll("a")
            bdo = self.textLu[cle].findAll("bdo")
            # realiser les affectations
            self.read_relative_data(self.pere_ind, a_href, bdo)
            self.read_relative_data(self.mere_ind, a_href, bdo)

        else:  # cle not in textLu
            self.logErreurHisto("ERREUR *** "+cle + " not in textLu")

        ### SPOUSES  AND CHILDREN ###
        cle = 'SPOUSES  AND CHILDREN'
        if (cle in self.textLu):
            self.analyseSpousesChildren(cle)
        else:  # cle not in textLu
            self.logErreurHisto("ERREUR *** "+cle + " not in textLu")

        cle = 'SPOUSES, CHILDREN AND GRANDCHILDREN'
        if (cle in self.textLu):
            self.analyseSpousesChildren(cle)
        else:  # cle not in textLu
            self.logErreurHisto("ERREUR *** "+cle + " not in textLu")

        ### SPOUSES, CHILDREN, GRANDCHILDREN AND GREAT-GRANDCHILDREN ###
        cle = 'SPOUSES, CHILDREN, GRANDCHILDREN AND GREAT-GRANDCHILDREN'
        if (cle in self.textLu):
            self.analyseSpousesChildren(cle)
        else:  # cle not in textLu
            self.logErreurHisto("ERREUR *** " + cle + " not in textLu")

        ### SIBLING ###
        cle = 'HALF-SIBLINGS'
        if (cle in self.textLu):
            # bug:  si on n'ecrase pas textLu ici il n'est pas lisible eb fin de prog(?)
            self.siblingLst = self.textLu[cle].getText()
            self.textLu[cle] = self.siblingLst
            # done 20200210 rajouter test taille ?
        else:  # cle not in textLu
            self.logErreurHisto("ERREUR *** "+cle + " not in textLu")

        ### SOURCES ###
        cle = 'SOURCES'
        if (cle in self.textLu):
            self.sourceLst = self.textLu[cle].getText()
            # done 20200210 rajouter test taille ?
        else:  # cle not in textLu
            self.logErreurHisto("ERREUR *** "+cle + " not in textLu")

        ### PHOTOS ###
        cle = 'PHOTOS AND ARCHIVAL RECORDS'
        if (cle in self.textLu):
            if isinstance(self.textLu[cle], element.Tag):
                print("bs4.element.Tag", self.textLu[cle].content)
                str_obj = (lambda x: "" if x is None else x.getText())(self.textLu[cle])
            else:
                print ("Type: ", type(self.textLu[cle]), self.textLu[cle])
                str_obj = self.textLu[cle]
            self.photosLst = str_obj
            # done 20200210 rajouter test taille ?
        else:  # cle not in textLu
            self.logErreurHisto("ERREUR *** "+cle + " not in textLu")

        ### FAMILY TREE PREVIEW ###
        cle = 'FAMILY TREE PREVIEW'
        if (cle in self.textLu):
            self.FamilyTreeLst = self.textLu[cle].getText()
        # done 20200210 rajouter test taille ?
        else:  # cle not in textLu
            self.logErreurHisto("ERREUR *** "+cle + " not in textLu")

        ### URL_PERE ###
        cle = 'URL_PERE'
        if (cle in self.textLu):
            self.url_pere = "https://gw.tartanpion.org/" + self.textLu[cle]
        # done 20200210 rajouter test taille ?
        else:  # cle not in textLu
            self.logErreurHisto("ERREUR *** "+cle + " not in textLu")

        ### URL_MERE ###
        cle = 'URL_MERE'
        if (cle in self.textLu):
            self.url_mere = "https://gw.tartanpion.org/" + self.textLu[cle]
        # done 20200210 rajouter test taille ?
        else:  # cle not in textLu
            self.logErreurHisto("ERREUR *** "+cle + " not in textLu")

        return

    def logErreurHisto(self, txt):
        self.logErreur += txt + '\n'
        print (txt)

    def interpDate(self, date, sep):
        date = date.strip(' ')
        pos1 = date.find('-')
        pos2 = date.rfind('-') + 1
        lng = len(date)
        date_naissance = date_deces = ""
        if pos1 > 2:
            # il existe une première date
            date_naissance = translateGenDate(date[:pos1])
        if pos2 < lng - 2:
            # il existe une date de deces
            date_deces = translateGenDate(date[pos2:])
        return date_naissance, date_deces

    def L_DictAjout(self, name, place, L_dict, L2_dict):
        """
        teste si la localisation "place" est deja dans le dictionnaire "L_dict"
        si c'est le cas la valeur "AUTRE" est retourné,
             la clé associée a cette valeur est rangée dans l2_dict[name]
        sinon la valeur cherchée est retourné
        :param name:
        :param place: adresse a rechercher dans les values de L_dict()
        :param L_dict:
        :param L2_dict:
        :return:
        """
        if place in L_dict.values():
            kVal = list(L_dict.keys())[list(L_dict.values()).index(place)]
            # on associe la valeur de la cle localisé au meme endroit dans L2_dict
            L2_dict[name] = kVal
            # on retourne la valeur "AUTRE"
            L_dict[name] = "AUTRE"
        else:
            L_dict[name] = place  # s'il n'y est pas on retourne "place"
        # print "kVal: "+kVal
        return

    def find_loc(self, place, L_dict, L2_dict):
        """
        retrouve la localisation d'après les structures de données
        :param place: nom de la localisation (naissance, marriage, deces)
        :param L_dict: dictionnaire contenant la donnée ou signalant une indirection
        :param L2_dict: si indiretion pointe sur la donnée
        :return: la valeur a afficher
        """
        if place != '':
            if L_dict[place] == "AUTRE":
                localisation = L_dict[L2_dict[place]]
            else:
                localisation = L_dict[place]
        else:
            localisation = ''
        """
        print "DICT - LOCALISATION"
        print L_dict
        print L2_dict
        """
        return localisation


    def write_loc(self, localisation, sep, entete):
        plLst = localisation.strip(',').split(',')
        if len(plLst) == 5:
            ville = plLst[0].strip()
            codePostal = plLst[1].strip()
            departement = plLst[2].strip()
            region = plLst[3].strip()
            pays = plLst[4].strip()
            # todo: verifier l'agencement des champs
            buffWrite = departement + sep + departement + sep + departement + '\n' +\
                        entete + sep + ville + sep + ville + sep + "ville" + sep + sep + sep + \
                        codePostal + sep + departement
        else:
            buffWrite = entete + sep + '"'+localisation+'"'

        return buffWrite

    def ecrire_Person(self, num_Person, prenom, nom, date_naissance,
                      date_deces, L_dict, L2_dict, sep,
                      place_naissance="", place_deces="", sexe="", birthsource="", deathsource="", note="",
                      attributetype="", attributevalue=""):
        # todo normaliser la transformation des date via une seule fonction
        date_naissance = formatDate(date_naissance.replace('_', ' '))
        date_deces = formatDate(date_deces)

        line = 'P' + str(num_Person) + sep + prenom.replace(',', " ").replace('_', ' ') + sep + nom + sep
        line += date_naissance + sep + self.find_loc(place_naissance, L_dict, L2_dict) + sep
        # print "*", self.find_loc(place_deces, L_dict, L2_dict), "*"
        # print date_deces, "*", date_naissance, "*", place_deces
        line += date_deces + sep + self.find_loc(place_deces, L_dict, L2_dict)+sep

        if sexe == '':
            line += ''
        else:
            if sexe == 'M':
                line += 'masculin'
            if sexe == 'F':
                line += 'féminin'
        line += sep+birthsource+sep+deathsource+sep+note+sep
        line += attributetype + sep + attributevalue
        ecrire(line)

    def dataRead2Csv(self, selecteur=""):
        '''
        :param selecteur: donne si fiche acte = 'M'
        :return: outbuff  # fichier CSV de type Gramps
        '''
        global num_Place, num_Person, num_Marriage, num_Famille
        fctName = "dataRead2Csv"
        ##### IMPRESSION CSV vers GRAMPS
        # ecrire("FORMAT CSV")
        outbuff = ""
        ecrire('')
        ecrire(self.url)
        ecrire('')
        """
         entete_place = "place, title, name, type (eg, City, County, State, etc.), latitude, longitude,"+\
                        "code (code postal), enclose_by (reference to another place), date (enclosed_by effect)"
         place du type: "Passonfontaine, 25690, Doubs, Franche-Comté, France"
        """
        if self.unavailData:
            return outbuff

        ecrire("place" + sep + " title" + sep + " name" + sep + " type" + sep + \
               " latitude" + sep + " longitude" + sep + " code" + sep + " enclosed_by" + sep + " date")

        L_dict = {}
        L2_dict = {}  # contient l'index de la valeur associée dans L_dict()

        self.L_DictAjout("place_naissance", self.place_naissance, L_dict, L2_dict)
        self.L_DictAjout("place_deces", self.place_deces, L_dict, L2_dict)
        for num, elt in enumerate(self.conjoint_m_place):
            print("self.conjoint_m_place: ", type(self.conjoint_m_place[num]), self.conjoint_m_place[num])
            # if (selecteur == 'acteDeMariage'):
            self.L_DictAjout("conjoint_lieu_n", self.conjoint_lieu_n[num], L_dict, L2_dict)
            self.L_DictAjout("conjoint_lieu_d", self.conjoint_lieu_d[num], L_dict, L2_dict)
            self.L_DictAjout("place_marriage"+str(num), self.conjoint_m_place[num], L_dict, L2_dict)
        # imprimer le dictionnaire
        for key, value in L_dict.items():
            # print key, "*", value, "*", len(value)

            if value == "AUTRE" or value == "":
                continue
            print("value: ", type(value), value)
            ecrire(self.write_loc(value, sep, 'L' + str(num_Place)))
            L_dict[key] = 'L' + str(num_Place)
            num_Place += 1
        """
        for key, value in L2_dict.items():
            ecrire(key+sep+value)
        """
        # ecrire("Firstname, Surname, Birthdate, Birth place id")

        """
        entete_Individu = "Individu,Nom,Prénom,Usuel,Suffixe,Préfixe,Titre,Genre,Date de naissance," + \
                          "Lieux de naissancedeathsource,Source de naissance,Date du baptème,Lieu du baptème," + \
                          "Source du baptème,Date de décès,Lieux du décès,Source du décès," + \
                          "Date de l'inhumation,Lieu de l'inhumation,Source de l'inhumation,Note"
        entete_individu = "person, grampsid, firstname, lastname, callname, prefix, suffix,"+\
                          "title, gender, note, birthdate, birthplace, birthplaceid, birthsource, baptismdate,"+\
                          "baptismplace, baptismplaceid , baptismsource, deathdate, deathplace, deathplaceid,"+\
                          ", deathcause, burialdate, burialplace, burialplaceid, burialsource"                          
        """
        ecrire("")
        ecrire("person" + sep + " firstname" + sep + " lastname" + sep + " birthdate" + sep + " birthplaceid" + sep + \
               " deathdate" + sep + " deathplaceid" + sep + "gender" + sep + "birthsource" + sep + \
               "deathsource" + sep + " note" + sep + " attributetype" + sep + " attributevalue")
        # 20200215 rajouter birthsource et deathsource
        # 20200215 rajouter gender pour les autres declarations de personnes

        # Premier
        if (selecteur != 'acteDeMariage'):
            note1 = (lambda x: "" if x is None else x.getText())(self.textLu["NOTES"])
            note2 = (lambda x: "" if x is None else x.getText())(self.textLu["SOURCES"])
            print(fctName + " Notes: ", type(self.textLu['NOTES']), '#', note1, '#')
            print(fctName + " Sources: ", type(self.textLu['SOURCES']), '#', note2, '#')
        else:
            note1 = self.textLu["NOTES"]
            note2 = self.textLu["SOURCES"]
        note = '"'+self.note + note1

        # note += (lambda x: "" if len(x) == 0 else '\n')(note1)
        note += " " + note2 +'"'
        print(fctName+" note: ", note)
        num_FirstPerson = num_Person
        self.ecrire_Person(num_Person, self.prenom, self.nom, self.date_naissance,
                           self.date_deces, L_dict, L2_dict, sep, "place_naissance",
                           "place_deces", self.sexe,
                           note=note)
        num_Person += 1

        # on ne prend pas en compte les parents
        if selecteur == 'acteDeMariage':
            # Pere
            # date_naissance, date_deces = self.relative_date_naissance[0], self.relative_date_deces[0]
            # ... self.interpDate(self.pere_date, sep)
            if ((self.relative_nom[0] != "") or (self.relative_prenom[0] != "")):
                self.ecrire_Person(num_Person, self.relative_prenom[0], self.relative_nom[0],
                                   self.relative_date_naissance[0], self.relative_date_deces[0],
                                   L_dict, L2_dict, sep, "",
                                   "", "M", note, "", "",
                                   attributetype="profession" if self.relative_profession[0] else "",
                                   attributevalue=self.relative_profession[0])

                self.relative_Nber[0] = num_Person
                num_Person += 1

            # Mere
            # date_naissance, date_deces = self.relative_date_naissance[1], self.relative_date_deces[1]
            # ... self.interpDate(self.mere_date, sep)

            # on ne prend pas en compte les parents
            if ((self.relative_nom[1] != "") or (self.relative_prenom[1] != "")):
                self.ecrire_Person(num_Person, self.relative_prenom[1], self.relative_nom[1],
                                   self.relative_date_naissance[1], self.relative_date_deces[1],
                                   L_dict, L2_dict, sep, "", "", "F",
                                   note, "", "",
                                   attributetype="profession" if self.relative_profession[1] else "",
                                   attributevalue=self.relative_profession[1])
                self.relative_Nber[1] = num_Person
                num_Person += 1

        # Conjoint
        # todo: verifier l'affichage du conjoint : prenom, nom, année de naissance
        num_conjoint = num_Person
        # date_naissance, date_deces = self.interpDate(self.conjoint_date, sep)
        # definir le sexe = opposite of P1
        sexe1 = (lambda: 'M' if self.sexe == 'F' else 'F')()
        # print sexe1
        for ind in range(0, len(self.conjoint_nom)):
            self.ecrire_Person(num_Person, self.conjoint_prenom[ind], self.conjoint_nom[ind],
                               self.conjoint_date_n[ind], self.conjoint_date_d[ind],
                               L_dict, L2_dict, sep, "conjoint_lieu_n", "conjoint_lieu_d",
                               sexe=sexe1, birthsource="", deathsource="", note=note,
                               attributetype="profession" if self.conjoint_profession[ind] else "",
                               attributevalue=self.conjoint_profession[ind])
            self.print_conjoint()
            num_Person += 1

        if (selecteur == 'acteDeMariage'):
            # Pere
            # date_naissance, date_deces = self.relative_date_naissance[0], self.relative_date_deces[0]
            # ... self.interpDate(self.pere_date, sep)
            if ((self.conjoint_relative_nom[0] != "") or (self.conjoint_relative_prenom[0] != "")):
                self.ecrire_Person(num_Person, self.conjoint_relative_prenom[0], self.conjoint_relative_nom[0],
                                   self.conjoint_relative_date_naissance[0],
                                   self.conjoint_relative_date_deces[0], L_dict, L2_dict,
                                   sep, "", "", "M",
                                   note, "", "",
                                   attributetype="profession" if self.conjoint_relative_profession[0] else "",
                                   attributevalue=self.conjoint_relative_profession[0])
                self.conjoint_relative_Nber[0] = num_Person
                num_Person += 1

            # Mere
            # date_naissance, date_deces = self.relative_date_naissance[1], self.relative_date_deces[1]
            # ... self.interpDate(self.mere_date, sep)

            # on ne prend pas en compte les parents
            if ((self.conjoint_relative_nom[1] != "") or (self.conjoint_relative_prenom[1] != "")):
                self.ecrire_Person(num_Person, self.conjoint_relative_prenom[1], self.conjoint_relative_nom[1],
                                   self.conjoint_relative_date_naissance[1], self.conjoint_relative_date_deces[1],
                                   L_dict, L2_dict, sep, "", "", "F", note,
                                   "", "",
                                   attributetype="profession" if self.conjoint_relative_profession[1] else "",
                                   attributevalue=self.conjoint_relative_profession[1])
                self.conjoint_relative_Nber[1] = num_Person
                num_Person += 1

        # Enfant
        num_Child = num_Person
        for ind in range(0, len(self.enfant_nom)):
            # print "toto", self.enfant_prenom[ind], self.enfant_nom[ind]
            # date_naissance, date_deces = self.interpDate(self.enfant_date[ind], sep)
            # todo reflechir au traitement necessaire pour supprimer les doublons
            # todo c-a-d les personnes deja declarées
            self.ecrire_Person(num_Person, self.enfant_prenom[ind], self.enfant_nom[ind],
                               self.enfant_date_n[ind], self.enfant_date_d[ind],
                               L_dict, L2_dict, sep, place_naissance="", place_deces="",
                               sexe=self.enfant_sexe[ind], note=note)
            num_Person += 1

        """
        entete_marriage = "marriage, husband, wife, date, place, placeid, source, note"
        """
        # todo: CORRIGER ERREUR SUR LE POINTEUR DEUXIEME CONJOINT
        ecrire("")
        ecrire("marriage" + sep + " husband" + sep + " wife" + sep + " date" + sep + " placeid" + sep +\
               " source" + sep + " note")
        # num_Marriage, num_conjoint, num_wife
        for ind in range(0, len(self.conjoint_nom)):
            if self.sexe == 'M':
                ecrire('M' + str(self.conjoint_FNber[ind]) + sep +
                       'P' + str(num_FirstPerson) + sep +
                       'P' + str(num_conjoint) + sep +
                       self.conjoint_m_date[ind] + sep +
                       self.find_loc("place_marriage"+str(ind), L_dict, L2_dict)+sep +
                       self.source+sep +
                       self.conjoint_witness[ind]
                       )
                '''
                       sep+self.witness+sep +
                '''
            else:
                ecrire('M' + str(self.conjoint_FNber[ind]) + sep +
                       'P' + str(num_conjoint) + sep +
                       'P' + str(num_FirstPerson) + sep +
                       self.conjoint_m_date[ind] + sep +
                       self.find_loc("place_marriage"+str(ind), L_dict, L2_dict)+sep +
                       self.source+sep +
                       self.conjoint_witness[ind]
                       )
                '''
                       sep+self.witness + sep +
                '''

        MariageNb = len(self.conjoint_nom) + 1

        if (selecteur == 'acteDeMariage'):
            source = "Genealogy Society Indexes"
            # decrire mariage parent du marié
            ecrire('M' + str(MariageNb) + sep +
                   'P' + str(self.relative_Nber[0]) + sep +
                   'P' + str(self.relative_Nber[1]) + sep +
                    sep + sep + source + sep + note)

            # decrire mariage parent du marié
            ecrire('M' + str(MariageNb+1) + sep +
                   'P' + str(self.conjoint_relative_Nber[0]) + sep +
                   'P' + str(self.conjoint_relative_Nber[1]) + sep +
                    sep + sep + source + sep + note)

        """
        entete_family = "family, child, source, note, gender"
        """
        ecrire("")
        ecrire("family" + sep + " child" + sep + " source" + sep + " note" + sep + " gender")  # gender male or female
        # num_Famille, num_child  # pour chaque prenom[num], nom[num]
        for ind in range(0, len(self.enfant_nom)):
            ecrire('M' + str(self.enfant_FNber[ind]) + sep + 'P' + str(num_Child))
            num_Child += 1

        if selecteur == 'acteDeMariage':
            ecrire('M2'+sep+'P1')
            ecrire('M3'+sep+'P4')

        global extData
        outbuff = extData
        extData = ""
        return outbuff

    def printData(self):
        #### IMPRESSION STANDART
        print ("################################################")
        print ("#####  RESULTAT #####")
        print ("ANCETRE:")
        print ("sexe: ", self.sexe)
        print ("nom: ", self.nom)
        print ("prenom: ", self.prenom)
        print ("date_naissance: ", self.date_naissance)
        print ("place_naissance: ", self.place_naissance)
        print ("date_deces: ", self.date_deces)
        print ("place_deces: ", self.place_deces)
        print ("age_deces: ", self.age_deces)
        print ("profession: ", self.profession)
        print()
        print ("PARENTS:")
        print ("pere_nom: ", self.relative_nom[0], ", pere_prenom: ", self.relative_prenom[0],\
            ", pere_date_n: ", self.relative_date_naissance[0], ", pere_date_d: ", self.relative_date_deces[0])
        print ("mere_nom: ", self.relative_nom[1], ", mere_prenom: ", self.relative_prenom[1], \
            ", mere_date_n: ", self.relative_date_naissance[1], ", mere_date_d: ", self.relative_date_deces[1])
        print ("MARRIAGE:")
        for ind in range(0, len(self.conjoint_nom)):
            print ("conjoint_nom: ", self.conjoint_nom[ind], ", conjoint_prenom: ", self.conjoint_prenom[ind], \
                ", conjoint_date_n: ", self.conjoint_date_n[ind], ", conjoint_date_d: ", self.conjoint_date_d[ind], \
                ", conjoint_m_place: ", self.conjoint_m_place[ind], ", conjoint_Nber: ", self.conjoint_m_date[ind])
        print()
        print ("FAMILLE:")
        print ("enfant_nom[ind], enfant_prenom[ind], enfant_date_n[ind], enfant_date_d[ind]")
        for ind in range(0, len(self.enfant_nom)):
            print (self.enfant_nom[ind], ", ", self.enfant_prenom[ind], ", ", self.enfant_date_n[ind],\
                ", ", self.enfant_date_d[ind])
        print ("################################################")
        return


def wTranslator(line):
    words = ["march", "March", "june", "June"]
    tWords = ["mars", "mars", "juin", "juin"]
    # print line
    for i, item in enumerate(words):
        line = line.replace(item, tWords[i])
    return line

def traitementNoeud(base, url, fn_err, politique = "dontBypass"):
    note = idFromtartanpionUrl(url)
    page1 = tartanpionData(base, url, note)
    #
    page1.findInfo()
    # print page1.printTextLu()
    page1.extractData2()
    page1.printData()
    # page1.printData()
    buff = page1.dataRead2Csv()
    emptyBuff = ""

    # print buff
    ficName = home_rep + "/" + (page1.nom + sep + page1.prenom + \
                                sep + page1.date_naissance + sep + page1.date_deces)
    # ficName =
    ficName = supprime_accent(ficName)

    #bypass des enregistrements famille de la mere double de celui du pere
    if page1.sexe == 'M':
        # done 20200211 ranger les fichiers dans un repertoire spécifique
        # done 20200211 arreter le programme si le nom de fichier existe déjà
        if os.path.exists(ficName) and politique == 'dontBypass':
            print ("file "+ficName+" already exist")
        else:
            print
            print ("Nom du fichier crée: " + ficName)
            try:
                with io.open(ficName + ".csv", "w", encoding="cp1252") as f:
                    f.write(buff)
                with io.open(ficName + ".ref", "w", encoding="cp1252") as f:
                    buff = page1.printTextLu()
                    buff += page1.logErreur
                    buff += '"'+page1.witness+'"'
                    f.write(buff)
            except:
                print ("################# EXCEPT #######################")
                try:
                    with open(ficName + ".csv", "w") as f:
                        f.write(buff)
                    with open(ficName + ".ref", "w") as f:
                        buff = page1.printTextLu()
                        buff += page1.logErreur
                        buff += '"'+page1.witness+'"'
                        f.write(buff)
                except:
                    fn_err += 1
                    ficName = "Erreur"+str(fn_err)
                    with open(ficName + ".csv", "w") as f:
                        f.write(buff)
                    with open(ficName + ".ref", "w") as f:
                        buff = page1.printTextLu()
                        buff += page1.logErreur
                        buff += +'"'+page1.witness+'"'
                        f.write(buff)
    else:
        with io.open(ficName + ".csv", "w", encoding="cp1252") as f:
            f.write(emptyBuff) # .decode('utf-8') python 2
        print ("NOT INCLUDE IN RESULTAT")
    """
    if not(page1.unavailData):
        # Determination de l'URL des parents
        # url_mere
        libelle = "URL_MERE"
        # text = aLst[4]['href'].strip()
        # test si prenom et nom sont de longueur significative
        nomPrenom = "p="+page1.mere_prenom.replace(' ', '+')+"&n="+page1.mere_nom
        if len(nomPrenom) > 7:
            page1.url_mere = supprime_accent(page1.base + nomPrenom)
            page1.textLu[libelle] = page1.url_mere

        # url_pere
        libelle = "URL_PERE"
        # text = aLst[3]['href'].strip()
        # test si prenom et nom sont de longueur significative
        nomPrenom = "p=" + page1.pere_prenom.replace(' ', '+') + "&n=" + page1.pere_nom
        if len(nomPrenom) > 7:
            page1.url_pere = supprime_accent(page1.base + nomPrenom)
            page1.textLu[libelle] = page1.url_pere
    """

    print("URLs", page1.relative_url)
    print("URL PERE SUIVANT: ", page1.relative_url[0])
    print("....MERE .......: ", page1.relative_url[1])

    return page1.relative_url[0], page1.relative_url[1], page1.error


def iterative_bfs(base, start_url, nbr=9999):
    fn_err = 0
    visited = []
    queue = deque()
    # print "####1", len(queue)
    queue.append(start_url)

    while queue and nbr > 0:
        print ("####2", len(queue), nbr)
        url = queue.popleft()
        # print "####3", len(queue), "\nurl: ", url
        url_pere, url_mere, error = traitementNoeud(base, url, fn_err, politique="bypass")
        visited.append(url)
        if error != 0:
            return visited, error
        if (url_pere != ""):
            if url_pere in visited:
                pass
            else:
                print("AJOUT URL PERE", url_pere)
                queue.append(url_pere)  # Ajout du fils gauche s'il existe
        if (url_mere != ""):
            if url_mere in visited:
                pass
            else:
                print("AJOUT URL MERE", url_mere)
                queue.append(url_mere)  # Ajout du fils droit s'il existe
        nbr -= 1

    return visited, 0

def lectureActeMariage(page1):
        global worldDic, value
        # remplir la structure tartanpionData
        # TODO trier les appels a rechercheCode(b) par taille degressive de la liste b

        # Code Commune
        b = ['code', 'commune']
        num = rechercheCode(b)
        page1.codeCommune = value[num[0]]

        b = ['commune']
        num = rechercheCode(b)
        page1.conjoint_m_place.append(value[num[0]] + '","' + value[num[0]])
        page1.commune = value[num[0]]

        # Code Departement
        b = ['code', 'departement']
        num = rechercheCode(b)
        page1.codeDepartement = value[num[0]]

        b = ['departement']
        page1.departement = value[wordDic['departement'][0]]

        # Acte
        b = ['acte']
        num = wordDic[b[0]]
        page1.acte = value[num[0]]

        # Date mariage
        b = ['date', 'mariage']
        num = rechercheCode(b)
        page1.conjoint_m_date.append(value[num[0]])

        # Nom epoux
        b = ['nom', 'epoux']
        num = rechercheCode(b)
        page1.nom = value[num[0]].capitalize()
        page1.sexe = 'M'

        # Prenom epoux
        b = ['prenom', 'epoux']
        num = rechercheCode(b)
        page1.prenom = value[num[0]].capitalize()

        # Lieu d'origine epoux # verifier comment rentrer la lieu : naissance ou villegiature
        b = ['lieu', 'epoux', 'origine']
        num = rechercheCode(b)
        if len(num) > 0:
            page1.place_naissance = value[num[0]] + '","' + value[num[0]]

        # Commentaire epoux # commentaire epoux '?'
        b = ['commentaire', 'epoux']
        num = rechercheCode(b)
        page1.commentaire = value[num[0]]
        res = resoComm(page1.commentaire)
        if res == 1:
            page1.date_naissance = page1.commentaire
        if res == 2:
            page1.date_deces = "avant " + page1.conjoint_m_date[0]
        if res == 3:
            # print "res3: ",page1.conjoint_m_date[0].split('/')[2], page1.commentaire
            page1.date_naissance = str(int(page1.conjoint_m_date[0].split('/')[2])) - \
                                   int(page1.commentaire)

        # Profession epoux
        b = ['profession', 'epoux']
        num = []
        if len(num) > 0:
            page1.profession = value[num[0]]

        # nom ex conjoint epoux
        b = ['nom', 'ex', 'conjoint', 'epoux']
        num = rechercheCode(b)
        if len(num) > 0:
            page1.ex_conjoint_nom = value[num[0]].capitalize()

        # nom pere epoux
        b = ['epoux', 'pere', 'nom']
        num = rechercheCode(b)
        page1.relative_nom[0] = value[num[0]].capitalize()

        # prenom pere epoux
        b = ['epoux', 'pere', 'prenom']
        num = rechercheCode(b)
        page1.relative_prenom[0] = value[num[0]].capitalize()

        # Commentaire pere epoux
        b = ['epoux', 'pere', 'commentaire']
        num = rechercheCode(b)
        if len(num) > 0:
            page1.relative_commentaire[0] = value[num[0]]
            res = resoComm(page1.relative_commentaire[0])
        else:
            res = ""
        if res == 1:
            page1.relative_date_naissance[0] = page1.relative_commentaire[0]
        if res == 2:
            page1.relative_date_deces[0] = "avant " + page1.conjoint_m_date[0]
        if res == 3:
            # print "res3:"+page1.conjoint_m_date[0].split('/')[2]+page1.relative_commentaire[0]
            page1.relative_date_naissance[0] = str(int(page1.conjoint_m_date[0].split('/')[2]) - \
                                                   int(page1.relative_commentaire[0]))
        # Profession pere epoux
        b = ['epoux', 'pere', 'profession']
        num = rechercheCode(b)
        if len(num) > 0:
            page1.relative_profession[0] = value[num[0]]

        # nom mere epoux
        b = ['epoux', 'mere', 'nom']
        num = rechercheCode(b)
        page1.relative_nom[1] = value[num[0]].capitalize()

        # prenom mere epoux
        b = ['epoux', 'mere', 'prenom']
        num = rechercheCode(b)
        page1.relative_prenom[1] = value[num[0]].capitalize()

        # commentaire mere epoux
        b = ['epoux', 'mere', 'commentaire']
        num = rechercheCode(b)
        page1.relative_commentaire[1] = value[num[0]]
        res = resoComm(page1.relative_commentaire[1])
        if res == 1:
            page1.relative_date_naissance[1] = page1.relative_commentaire[1]
        if res == 2:
            page1.relative_date_deces[1] = "avant " + page1.conjoint_m_date[0]
        if res == 3:
            page1.relative_date_naissance[1] = str(int(page1.conjoint_m_date[0].split('/')[2])) - \
                                               int(page1.relative_commentaire[1])

        # Profession mere epoux
        b = ['epoux', 'mere', 'profession']

        num = rechercheCode(b)
        if len(num) > 0:
            page1.relative_profession[1] = value[num[0]]

        # nom epouse
        b = ['epouse', 'nom']
        num = rechercheCode(b)
        page1.conjoint_nom.append(value[num[0]].capitalize())
        page1.conjoint_date_n.append('')
        page1.conjoint_date_d.append('')
        page1.conjoint_FNber.append('')
        page1.conjoint_witness.append('')

        # prenom epouse
        b = ['epouse', 'prenom']
        num = rechercheCode(b)
        page1.conjoint_prenom.append(value[num[0]].capitalize())

        # epouse lieu de naissance
        b = ['epouse', 'lieu', 'naiss']
        num = rechercheCode(b)
        if len(num) != 0:
            page1.conjoint_lieu_n.append(value[num[0]] + '","' + value[num[0]])
            page1.conjoint_lieu_d.append("")
        else:
            page1.conjoint_lieu_d.append("")

        # epouse lieu de naissance
        b = ['epouse', 'lieu', 'deces']
        num = rechercheCode(b)
        if len(num) != 0:
            page1.conjoint_lieu_n.append("")
            page1.conjoint_lieu_d.append(value[num[0]])
        else:
            page1.conjoint_lieu_n.append("")

        # commentaire epouse
        b = ['epouse', 'commentaire']
        num = rechercheCode(b)
        if len(num) != 0:
            page1.conjoint_commentaire.append(value[num[0]])
            res = resoComm(page1.conjoint_commentaire[0])
        else:
            res = ""
        if res == 1:
            page1.conjoint_date_n[0] = page1.conjoint_commentaire[0]
        if res == 2:
            page1.conjoint_date_d[0] = "avant " + page1.conjoint_m_date[0]
        if res == 3:
            page1.conjoint_date_n[0] = str(int(page1.conjoint_m_date[0].split('/')[2])) - \
                                       int(page1.conjoint_commentaire[0])

        # profession epouse
        b = ['epouse', 'profession']
        num = rechercheCode(b)
        if len(num) != 0:
            page1.conjoint_profession.append(value[num[0]])
        else:
            page1.conjoint_profession.append("")

        # nom ex conjoint epouse
        b = ['epouse', 'ex', 'conjoint', 'nom']
        num = rechercheCode(b)
        if len(num) > 0:
            page1.conjoint_ex_nom.append(value[num[0]]).capitalize()

        # prenom ex conjoint epouse
        b = ['epouse', 'ex', 'conjoint', 'prenom']
        num = rechercheCode(b)
        if len(num) > 0:
            page1.conjoint_ex_prenom.append(value[num[0]]).capitalize()

        # nom pere epouse
        b = ['epouse', 'pere', 'nom']
        num = rechercheCode(b)
        page1.conjoint_relative_nom[0] = value[num[0]].capitalize()

        # prenom pere epouse
        b = ['epouse', 'pere', 'prenom']
        num = rechercheCode(b)
        page1.conjoint_relative_prenom[0] = value[num[0]].capitalize()

        # commentaire pere epouse
        b = ['epouse', 'pere', 'commentaire']
        num = rechercheCode(b)
        if len(num) != 0:
            page1.conjoint_relative_commentaire[0] = value[num[0]]
            res = resoComm(page1.conjoint_relative_commentaire[0])
        else:
            res = ""
        if res == 1:
            page1.conjoint_relative_date_naissance[0] = page1.conjoint_relative_commentaire[0]
        if res == 2:
            page1.conjoint_relative_date_deces[0] = "avant " + page1.conjoint_m_date[0]
        if res == 3:
            page1.conjoint_relative_date_naissance[0] = str(int(page1.conjoint_m_date[0].split('/')[2])) - \
                                                        int(page1.conjoint_relative_commentaire[0])

        # Profession pere epouse
        b = ['epouse', 'pere', 'profession']
        num = rechercheCode(b)
        if len(num) > 0:
            page1.conjoint_relative_profession[0] = value[num[0]]

        # Nom mere epouse
        b = ['epouse', 'mere', 'nom']
        num = rechercheCode(b)
        page1.conjoint_relative_nom[1] = value[num[0]].capitalize()

        # Prenom mere epouse
        b = ['epouse', 'mere', 'prenom']
        num = rechercheCode(b)
        page1.conjoint_relative_prenom[1] = value[num[0]].capitalize()

        # Commentaire mere epouse
        b = ['epouse', 'mere', 'commentaire']
        num = rechercheCode(b)
        if len(num) > 0:
            page1.conjoint_relative_commentaire[1] = value[num[0]]
            res = resoComm(page1.conjoint_relative_commentaire[1])
            if res == 1:
                page1.conjoint_relative_date_naissance[1] = page1.conjoint_relative_commentaire[1]
            if res == 2:
                page1.conjoint_relative_date_deces[1] = "avant " + page1.conjoint_m_date[0]
            if res == 3:
                page1.conjoint_relative_date_naissance[1] = str(int(page1.conjoint_m_date[0].split('/')[2])) - \
                                                            int(page1.conjoint_relative_commentaire[1])

        # temoin 1 nom
        b = ['temoin', '1', 'nom']
        num = rechercheCode(b)
        page1.temoin_nom.append(value[num[0]].capitalize())

        # temoin 1 prenom
        b = ['temoin', '1', 'prenom']
        num = rechercheCode(b)
        page1.temoin_prenom.append(value[num[0]].capitalize())

        # temoin 1 commentaire
        b = ['temoin', '1', 'commentaire']
        num = rechercheCode(b)
        page1.temoin_commentaire.append(value[num[0]])

        # temoin 2 nom
        b = ['temoin', '2', 'nom']
        num = rechercheCode(b)
        page1.temoin_nom.append(value[num[0]].capitalize())

        # temoin 2 prenom
        b = ['temoin', '2', 'prenom']
        num = rechercheCode(b)
        page1.temoin_prenom.append(value[num[0]].capitalize())

        # temoin 2 commentaire
        b = ['temoin', '2', 'commentaire']
        num = rechercheCode(b)
        if len(num) != 0:
            page1.temoin_commentaire.append(value[num[0]])
        else:
            page1.temoin_commentaire.append("")

        # temoin 3 nom
        b = ['temoin', '3', 'nom']
        num = rechercheCode(b)
        page1.temoin_nom.append(value[num[0]].capitalize())

        # temoin 3 prenom
        b = ['temoin', '3', 'prenom']
        num = rechercheCode(b)
        page1.temoin_prenom.append(value[num[0]].capitalize())

        # temoin 3 commentaire
        b = ['temoin', '3', 'commentaire']
        num = rechercheCode(b)
        page1.temoin_commentaire.append(value[num[0]])

        # temoin 4 nom
        b = ['temoin', '4', 'nom']
        num = rechercheCode(b)
        page1.temoin_nom.append(value[num[0]].capitalize())

        # temoin 4 prenom
        b = ['temoin', '4', 'prenom']
        num = rechercheCode(b)
        page1.temoin_prenom.append(value[num[0]].capitalize())

        # temoin 4 commentaire
        b = ['temoin', '4', 'commentaire']

        num = rechercheCode(b)
        page1.temoin_commentaire.append(value[num[0]])

        # N° enregistrement
        page1.enregistrement = value[wordDic['enregistrement'][0]]

        # mise a jour des données annexes
        for ind, elt in enumerate(page1.temoin_nom):
            page1.conjoint_witness[0] += '"' + " **-- nom: " + page1.temoin_nom[ind] + \
                                         "-- prenom: " + page1.temoin_prenom[ind] + \
                                         "-- commentaires: " + page1.temoin_commentaire[ind] + '"'

        page1.textLu["NOTES"] = ""
        page1.textLu["SOURCES"] = page1.enregistrement
        page1.source = "Genealogy Society Index " + page1.enregistrement
        page1.witness = ""

        page1.print_etatCivil()
        page1.print_conjoint()
        page1.print_parents()
        page1.print_conjoint_relative()
        page1.print_autre()
        page1.print_temoin()

        buff=page1.dataRead2Csv(selecteur='acteDeMariage')

        return buff


def traitement1(base, url, explo_profondeur, home_rep):
    resultFile = "result2.txt"
    print("****PENSEZ A VOUS ASSURER QUE LE REPERTOIRE EST VIDE DE FICHIER *.CSV AVANT ****")
    # lance l'exploration de l'arbre a partir de l'adresse url de tartanpion
    visited, error = iterative_bfs(base, url, nbr=explo_profondeur)
    print("FIN")
    for elt in visited:
        print(elt)

    # TODO enlever les soulignes dans la date de naissance du fichier csv
    # TODO reprendre tous les fichiers csv en identifiant chaque nom d'individu
    # TODO de maniere unique
    # TODO par une variable
    # TODO idem por les noms de lieux "embeded_by"

    # creer un fichier result.csv
    # contenant tous les fichiers *.csv
    # du repertoire home_rep
    import glob

    filenames = [file for file in glob.glob(home_rep + "/*.csv")]
    ficRes = home_rep + "/" + resultFile
    with open(ficRes, 'w') as outfile:
        for fname in filenames:
            with open(fname) as infile:
                outfile.write(infile.read())

    print("DONE_1")
    return error

def traitement2(base, ext):
    global wordDic, value
    base = "D:\\Users\\chris\\Documents"
    ext = "\\genealogySocietyIndex.csv"
    error = 0

    ##
    content = []
    tag = []
    value = []

    # intialisation des structures
    filename = base + ext
    readcsv(filename, content)
    for row in content:
        tag.append(supprime_accent(row[0].decode('ISO-8859-1')).replace('_', ' '))
        value.append(supprime_accent(row[1].decode('ISO-8859-1')).replace('_', ' ').strip())
        print (tag[-1] + " == " + value[-1])

    wordDic = {}
    # parcourir tag
    for word in wordLst:
        wordDic[word] = []

        for index, tagElt in enumerate(tag):
            if word in tagElt.lower():
                wordDic[word].append(index)
    print()
    print (wordDic)

    page1 = tartanpionData(base, url, "Genealogy Society Index")
    buff = lectureActeMariage(page1)

    # print buff
    ficName = home_rep + "/" + (page1.nom + sep + page1.prenom +
                                sep + page1.date_naissance.replace('/', '_') +
                                sep + page1.date_deces.replace('/', '_'))
    # ficName =
    ficName = supprime_accent(ficName)

    print()
    print ("Nom du fichier crée: " + ficName)
    try:
        with io.open(ficName + ".csv", "w", encoding="cp1252") as f:
            f.write(buff)
    except:
        print ("echec creation fichier")

    print ("DONE_2")
    return error

def traitement3(base, ext):
    global wordDic, value
    base = "D:\\Users\\chris\\Documents\\Soller\\"
    ext = "Search all records - tartanpion1.html"
    error = 0

    ##
    content = []
    tag = []
    value = []

    # initialisation des structures
    filename = base + ext
    print("\nfilename: ", filename)

    page1 = tartanpionResultData(filename, "lecture fichier resultat", 'lectureRepertoire', "")
    url = page1.findInfo("")
    print("#", url, "#")
    while url != "":
        url = page1.findInfo(url)
    # page1.print()

    buff = page1.getAllArbo()

    print(buff)
    ficName = home_rep + '\\' + (page1.arboHomme[0] + sep + \
                                page1.arboLieu[0].replace(' ', '-'))
    print("ficName: ", ficName)

    ficName = supprime_accent(ficName)

    print()
    print ("Nom du fichier crée: " + ficName)
    try:
        with io.open(ficName + ".csv", "w", encoding="cp1252") as f:
            f.write(buff)
    except:
        print ("echec creation fichier")

    print ("DONE_3")
    return error

import tkinter as tk
# import Tkconstants, tkFileDialog
# import ttk
from tkinter import (
    constants as const,
    filedialog as fdialog,
    ttk
)
    # autres options possibles
    # colorchooser as color,
    # commondialog as cdialog,
    # dialog,
    # dnd,
    # font,
    # messagebox as msgbox,
    # scrolledtext as stext,
    # simpledialog as sdialog,
    # tix,

def popup_bonus(msg):
    win = tk.Toplevel()
    win.wm_title("Window")

    l = tk.Label(win, text=msg)
    l.grid(row=0, column=0)

    b = ttk.Button(win, text="Okay", command=win.destroy)
    b.grid(row=1, column=0)

def popup_showinfo():
    showinfo("Window", "Hello World!")


class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.creer_widgets()

    def quit(self):
        global base, home_rep
        traitementNb = self.action()

        urltartanpionEntete = "https://gw.tartanpion.org/"
        #url = urltartanpionEntete + profilName + "?lang=en&" + "&n="+name+"&p"+firstname+"&oc="+occurence
        url = urltartanpionEntete + self.profilName.get() +\
              "?lang=en" + \
              "&n="+self.name.get() +\
              "&p="+self.firstname.get() +\
              "&oc="+self.occurence.get()

        url = "https://gw.tartanpion.org/gntstarcastanerchr?fc=geneastar&idgeneastar=gntstar10194&n=castaner&nz=castaner&oc=&ocz=0&p=jaime&pz=christophe"
        url = "https://gw.tartanpion.org/autentiquish?lang=en&iz=4333&p=margarita&n=morell+rullan"
        url = "https://gw.tartanpion.org/katari?lang=fr&iz=7584&p=jean+pierre+denis&n=cheron"
        url = "https://gw.tartanpion.org/famillebourges?lang=en&pz=patrick&nz=bourges&p=joseph+calixte&n=bourges"
        url = "https://gw.tartanpion.org/famillebourges?lang=en&pz=patrick&nz=bourges&p=paul&n=bayle"
        url = "https://gw.tartanpion.org/famillebourges?lang=en&pz=patrick&nz=bourges&p=maria&n=fevre"
        url = "https://gw.tartanpion.org/famillebourges?lang=en&pz=patrick&nz=bourges&p=auguste+joseph+louis+marie&n=pernot"
        url = "https://gw.tartanpion.org/famillebourges?lang=en&pz=patrick&nz=bourges&p=caroline+ernestine&n=lebon"

        home_rep = "xxx_" + self.profilName.get()
        # test l'existence d'un repertoire et le cree s'il n'existe pas
        if not os.path.exists(home_rep):
            os.mkdir(home_rep)

        explo_profondeur = int(self.explo_profondeur.get())
        baseName = self.baseName.get()
        fileName = self.fileName.get()

        print ("appel ?????????????????")
        # print(self.listeCombo.current(), self.listeCombo.get())
        print("base: ", base)
        print("url:", url)
        print("explo_profondeur: ", explo_profondeur)
        print("home-rep: ", home_rep)
        print("baseName: ", baseName)
        print("fileName: ", fileName)

        if traitementNb == 0:
            error = traitement1(base, url, explo_profondeur, home_rep)

        if traitementNb == 1:
            error = traitement2(baseName, fileName)

        if traitementNb == 2:
            error = traitement3(baseName, fileName)

        if error == 1:
            popup_bonus("Profil tartanpion non trouvé")
        if error == 2:
            popup_bonus("Non ou Prénom non trouvé")
        if error == 0:
            popup_bonus("Done")

    def action(self):
        # Obtenir l'élément sélectionné
        select = self.listeCombo.current()
        print("Vous avez sélectionné : '", select, "'")
        return select

    def dirSearch(self):
        # open dirSearch dialog
        self.directory = tkFileDialog.askdirectory(initialdir="D:\\Users\\chris\\Documents\\ ",
                                              title="Select Work Direcctory")
        self.directory = self.directory+ '/'
        self.textEntry2.set(self.directory)

    def fileSelect(self):
        # open fileSearch dialog
        filename = tkFileDialog.askopenfilename(initialdir=self.directory, title="Select file",
                                                filetypes=(("csv files", "*.csv"), ("all files", "*.*")))
        self.filename = filename.split('/')[-1]
        print (self.filename, filename)
        self.textEntry3.set(self.filename)

    def creer_widgets(self):
        global explo_profondeur, home_rep, url
        # localisation des textes ROW
        textLoc = 0

        self.label = tk.Label(self, text="Remplir ou valider les parametres ci-dessous: ")
        self.bouton = tk.Button(self, text="Quitter", command=self.quit)

        labelChoix = tk.Label(self, text="Veuillez faire un choix !")
        labelChoix.grid(row=textLoc, column=0)

        # 2) - créer la liste Python contenant les éléments de la liste Combobox
        listeProduits = ["Arbre des Ascendants", "GenealogySociety", "Analyse Résultats"]

        # 3) - Création de la Combobox via la méthode ttk.Combobox()
        self.listeCombo = ttk.Combobox(self, values=listeProduits)

        # 4) - Choisir l'élément qui s'affiche par défaut
        self.listeCombo.current(0)

        # 5)
        self.listeCombo.bind("<<ComboboxSelected>>", self.action())

        # textLoc += 1
        self.listeCombo.grid(row=textLoc, column=1)
        textLoc += 1
        self.label.grid(row=textLoc, column=0)
        self.bouton.grid(row=textLoc, column=2)

        textEntry01 = tk.StringVar()
        textEntry01.set('name')
        self.lbl1 = tk.Label(self, text="Nom du profil tartanpion - resultat range sous xxx_name: ")
        self.profilName = tk.Entry(self, width=10, textvariable=textEntry01)
        textLoc += 1
        self.lbl1.grid(row=textLoc, columnspan=3)
        textLoc += 1
        self.profilName.grid(row=textLoc, column=1)

        self.lbl21 = tk.Label(self, text="Personne recherchée")
        self.lbl21_1 = tk.Label(self, text="nom: ")
        self.name = tk.Entry(self, width=10)
        textLoc += 1
        self.lbl21.grid(row=textLoc, columnspan=3) #  sticky='w'
        textLoc += 1
        self.lbl21_1.grid(row=textLoc, column=0, sticky='w')
        self.name.grid(row=textLoc, column=1)

        self.lbl22 = tk.Label(self, text="prenom")
        self.firstname = tk.Entry(self, width=10)
        textLoc += 1
        self.lbl22.grid(row=textLoc, column=0, sticky='w')
        self.firstname.grid(row=textLoc, column=1)

        textEntry23 = tk.StringVar()
        textEntry23.set('01')
        self.lbl23 = tk.Label(self, text="occurence")
        self.occurence = tk.Entry(self, width=1, textvariable=textEntry23)
        textLoc += 1
        self.lbl23.grid(row=textLoc, column=0, sticky='w')
        self.occurence.grid(row=textLoc, column=1)

        textEntry = tk.StringVar()

        textEntry.set('9999')
        self.lbl3 = tk.Label(self, text="Profondeur d'analyse des Url: ")
        self.explo_profondeur = tk.Entry(self, width=4, textvariable=textEntry)
        textLoc += 1
        self.lbl3.grid(row=textLoc, column=0, sticky='w')
        self.explo_profondeur.grid(row=textLoc, column=1)

        self.textEntry2 = tk.StringVar()
        self.directory = "D:\\Users\\chris\\Documents\\ "
        # directory = tkFileDialog.askdirectory(initialdir="D:\Users\chris\Documents\ ", title="Select Work Direcctory")
        self.textEntry2.set(self.directory)
        self.lbl4 = tk.Label(self, text="Fichier Csv type Genealogy Society index | fichier a anlyser")
        self.lbl4_1 = tk.Label(self, text="baseName: ")
        self.baseName = tk.Entry(self, width=50, textvariable=self.textEntry2)
        self.bouton2a = tk.Button(self, text="find directory", command=self.dirSearch)

        textLoc += 1
        self.lbl4.grid(row=textLoc, columnspan=3)
        textLoc += 1
        self.lbl4_1.grid(row=textLoc, column=0, sticky='w')
        self.baseName.grid(row=textLoc, column=1)
        self.bouton2a.grid(row=textLoc, column=2)

        self.textEntry3 = tk.StringVar()
        #filename = tkFileDialog.askopenfilename(initialdir=directory, title="Select file",
        #                                         filetypes=(("csv files", "*.csv"), ("all files", "*.*")))
        self.filename = 'genealogySocietyIndex.csv'

        self.textEntry3.set(self.filename)
        self.lbl5 = tk.Label(self, text="fileName: ")
        self.fileName = tk.Entry(self, width=50, textvariable=self.textEntry3)
        self.bouton2b = ttk.Button(self, text="find file", command=self.fileSelect)

        textLoc += 1
        self.lbl5.grid(row=textLoc, column=0, sticky='w')
        self.fileName.grid(row=textLoc, column=1)
        self.bouton2b.grid(row=textLoc, column=2)

if __name__ == "__main__":
    ''' pour besoin de test
    txt="18 March 1630"
    print (wTranslator(txt))
    exit(0)
    '''

# todo afficher en sortie de prog l'emplacement des fichiers produits
    # todo et les traitements a faire ensuite pour les utiliser
    num_Place = 1
    num_Person = 1
    num_Marriage = 1
    num_Famille = 1
    extData = ""
    ext = ""
    sep = ','   # separateur utilise dans les fichiers csv
    home_rep = ""

    url = "https://gw.tartanpion.org/cnouvian3?lang=en&n=raynaud&oc=&p=jonathan"
    url = "https://gw.tartanpion.org/gntstarcastanerchr?fc=geneastar&\
    idgeneastar=gntstar10194&n=castaner&nz=castaner&oc=&ocz=0&p=jaime&pz=christophe"
    url = "https://gw.tartanpion.org/autentiquish?lang=en&iz=4333&p=margarita&n=morell+rullan"
    base = "https://gw.tartanpion.org/cnouvian3?lang=en&n=raynaud&oc=&p=jonathan"
    url = "https://gw.tartanpion.org/callahan2?lang=en&n=pursoigle&oc=1&p=jean"
    base="https://gw.tartanpion.org/katari?lang=en&iz=7584&p=jean+pierre+denis&n=cheron"
    url="https://gw.tartanpion.org/katari?lang=en&iz=7584&p=jean+pierre+denis&n=cheron"
    base="https://gw.tartanpion.org/famillebourges?lang=en&pz=patrick&nz=bourges&p=joseph+calixte&n=bourges"
    url="https://gw.tartanpion.org/famillebourges?lang=en&pz=patrick&nz=bourges&p=joseph+calixte&n=bourges"
    url="https://gw.tartanpion.org/famillebourges?lang=en&pz=patrick&nz=bourges&p=paul&n=bayle"
    ''''''

    app = Application()
    app.title("Interrogation tartanpion :-)")
    app.mainloop()

    # import autoit
    # autoit.run("C:\Program Files\Google\Chrome\Application\Chrome.exe \
    #  https://www.tartanpion.org/fonds/individus/?go=1&nom=atelain&prenom=christian&\
    #  prenom_operateur=or&with_variantes_nom=&with_variantes_nom_conjoint=&\
    #  with_variantes_prenom=&with_variantes_prenom_conjoint=&size=10")

    #ShellExecute("chrome.exe", "https://talkjarvis.com --new-window --start-fullscreen")
