# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 14:02:56 2020

@author: helene
"""

from tkinter import *

import matplotlib
from PIL import Image
import numpy as np
import pandas
import matplotlib.pyplot as plt
import string
import time
import matplotlib.colors as colors
import os

alphabet_majuscule = string.ascii_uppercase



def gen_color(cmap,n,reverse=False):
    '''Generates n distinct color from a given colormap.
    Args:
        cmap(str): The name of the colormap you want to use.
            Refer https://matplotlib.org/stable/tutorials/colors/colormaps.html to choose
            Suggestions:
            For Metallicity in Astrophysics: Use coolwarm, bwr, seismic in reverse
            For distinct objects: Use gnuplot, brg, jet,turbo.
        n(int): Number of colors you want from the cmap you entered.
        reverse(bool): False by default. Set it to True if you want the cmap result to be reversed.
    Returns: 
        colorlist(list): A list with hex values of colors.
    '''
    c_map = plt.cm.get_cmap(str(cmap)) # select the desired cmap
    arr=np.linspace(0,1,n) #create a list with numbers from 0 to 1 with n items
    colorlist=list()
    for c in arr:
        rgba=c_map(c) #select the rgba value of the cmap at point c which is a number between 0 to 1
        clr=colors.rgb2hex(rgba) #convert to hex
        colorlist.append(str(clr)) # create a list of these colors

    if reverse==True:
        colorlist.reverse()
    return colorlist

def affiche_colormap_etude_without_ttk(considered_matrice,considered_moyen,considered_std,nb_dot_selected,nb_dot_total,is_it_dot_selected,is_it_nb_dot_tot,name,colormap_choosen,v_min,v_max):
    lettres_ligne = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    chiffre_colonnes = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']

    fig_2 = plt.figure(name,constrained_layout=True,figsize=(10,7))
    ax = fig_2.add_subplot(111)
    cax = ax.imshow(considered_matrice, cmap=colormap_choosen, vmin = v_min, vmax = v_max,alpha=0.8)
    fig_2.colorbar(cax)
    ax.set_yticks([0, 1, 2, 3, 4, 5, 6, 7,8])
    ax.set_yticklabels(['']+lettres_ligne, weight = 'bold')
    ax.set_xticks(np.arange(0, 12, step=1))
    ax.xaxis.set_ticks_position('top')
    ax.set_xticklabels(chiffre_colonnes, weight = 'bold')
    if considered_moyen==0:
        plt.title(name, weight = 'heavy')
    else:
        plt.title(name+'\n valeur moyenne = '+"{:.2f}".format(considered_moyen)+' ecart-type = '+"{:.2f}".format(considered_std)+'->'+str(int(considered_std/considered_moyen*100))+'%', weight = 'heavy')
    for i in range(len(lettres_ligne)):
        for j in range(len(chiffre_colonnes)):
    #        text = ax.text(j, i, considered_matrice_plan_plaque[i, j],
    #                       ha="center", va="center", color="w", formatter)
            text = ax.text(j, i, "{:.1f}".format(considered_matrice[i, j]), #+"\n"+str(int(nb_dot_selected_matrice_plan_plaque[i, j])),
                           ha="center", va="center", color="k", size = 'x-large', weight = 'bold')
            if str(considered_matrice[i, j]) == 'nan' :
                text = ax.text(j, i, 'nan',
                           ha="center", va="center", color="r", size = 'x-large', weight = 'heavy')
            else:
                if is_it_dot_selected == 1 & is_it_nb_dot_tot == 1:
                    text = ax.text(j, i, "\n\n"+str(int(nb_dot_selected[i, j]))+"/"+str(int(nb_dot_total[i, j])),
                                   ha="center", va="center", color="k", size = 'smaller')

    plt.show()



def affiche_colormap_etude_general(considered_matrice,name,colormap_choosen,v_min,v_max):
    lettres_ligne = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    chiffre_colonnes = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
    considered_moyen = np.nanmean(considered_matrice)
    considered_std = np.nanstd(considered_matrice)
    etendue_relative = ((np.nanmax(considered_matrice) - np.nanmin(considered_matrice))/considered_moyen)* 100
    if np.isnan(etendue_relative):
        etendue_relative = 1000
    if np.isinf(considered_moyen):
        considered_moyen = np.nan

    fig_2 = plt.figure(name,constrained_layout=True,figsize=(10,7))
    ax = fig_2.add_subplot(111)
    cax = ax.imshow(considered_matrice, cmap=colormap_choosen, vmin = v_min, vmax = v_max,alpha=0.8)
    fig_2.colorbar(cax)
    ax.set_yticks([0, 1, 2, 3, 4, 5, 6, 7,8])
    ax.set_yticklabels(['']+lettres_ligne, weight = 'bold')
    ax.set_xticks(np.arange(0, 12, step=1))
    ax.xaxis.set_ticks_position('top')
    ax.set_xticklabels(chiffre_colonnes, weight = 'bold')

    if considered_moyen==0:
        plt.title(name, weight = 'heavy')
    else:
        plt.suptitle(name+'\n valeur moyenne = '+"{:.2f}".format(considered_moyen)+' ecart-type = '+"{:.2f}".format(considered_std)+'->'+str(int(considered_std/considered_moyen*100))+'%\n'+
                  'min = '+str(round(np.nanmin(considered_matrice),1))+' max = '+str(round(np.nanmax(considered_matrice),1))+
                                     ' soit étendue relative de '+str(round(etendue_relative,1))+' %', weight = 'heavy')
    for i in range(len(lettres_ligne)):
        for j in range(len(chiffre_colonnes)):
    #        text = ax.text(j, i, considered_matrice_plan_plaque[i, j],
    #                       ha="center", va="center", color="w", formatter)
            text = ax.text(j, i, "{:.1f}".format(considered_matrice[i][j]), #+"\n"+str(int(nb_dot_selected_matrice_plan_plaque[i, j])),
                           ha="center", va="center", color="k", size = 'x-large', weight = 'bold')
            if str(considered_matrice[i][j]) == 'nan' :
                text = ax.text(j, i, 'nan',
                           ha="center", va="center", color="r", size = 'x-large', weight = 'heavy')

    plt.show()

def affiche_colormap_etude_general_v2(considered_matrice,name,colormap_choosen,v_min,v_max):
#    rajout de la fonctionnalité si on renseigne v_min = v_max il prend automatiquement le min et max de la matrice pour faire son échelle de couleur
    lettres_ligne = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    chiffre_colonnes = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
    if v_min == v_max:
        v_min = np.nanmin(considered_matrice)
        v_max = np.nanmax(considered_matrice)
    considered_moyen = np.nanmean(considered_matrice)
    considered_std = np.nanstd(considered_matrice)
    etendue_relative = ((np.nanmax(considered_matrice) - np.nanmin(considered_matrice))/considered_moyen)* 100
    fig_2 = plt.figure(name,constrained_layout=True,figsize=(10,7))
    ax = fig_2.add_subplot(111)
    cax = ax.imshow(considered_matrice, cmap=colormap_choosen, vmin = v_min, vmax = v_max,alpha=0.8)
    fig_2.colorbar(cax)
    ax.set_yticks([0, 1, 2, 3, 4, 5, 6, 7,8])
    ax.set_yticklabels(['']+lettres_ligne, weight = 'bold')
    ax.set_xticks(np.arange(0, 12, step=1))
    ax.xaxis.set_ticks_position('top')
    ax.set_xticklabels(chiffre_colonnes, weight = 'bold')

    if considered_moyen==0:
        plt.title(name, weight = 'heavy')
    else:
        plt.suptitle(name+'\n valeur moyenne = '+"{:.2f}".format(considered_moyen)+' ecart-type = '+"{:.2f}".format(considered_std)+'->'+str(int(considered_std/considered_moyen*100))+'%\n'+
                  'min = '+str(round(np.nanmin(considered_matrice),1))+' max = '+str(round(np.nanmax(considered_matrice),1))+
                                     ' soit étendue relative de '+str(round(etendue_relative,1))+' %', weight = 'heavy')
    for i in range(len(lettres_ligne)):
        for j in range(len(chiffre_colonnes)):
    #        text = ax.text(j, i, considered_matrice_plan_plaque[i, j],
    #                       ha="center", va="center", color="w", formatter)
            text = ax.text(j, i, "{:.1f}".format(considered_matrice[i][j]), #+"\n"+str(int(nb_dot_selected_matrice_plan_plaque[i, j])),
                           ha="center", va="center", color="k", size = 'x-large', weight = 'bold')
            if str(considered_matrice[i][j]) == 'nan' :
                text = ax.text(j, i, 'nan',
                           ha="center", va="center", color="r", size = 'x-large', weight = 'heavy')

    plt.show()

def affiche_colormap_etude_without_ttk_choose_round(considered_matrice,considered_moyen,considered_std,nb_dot_selected,nb_dot_total,round_value,is_it_dot_selected,is_it_nb_dot_tot,name,colormap_choosen,v_min,v_max):
    lettres_ligne = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    chiffre_colonnes = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']

    fig_2 = plt.figure(name,constrained_layout=True,figsize=(10,7))
    ax = fig_2.add_subplot(111)
    cax = ax.imshow(considered_matrice, cmap=colormap_choosen, vmin = v_min, vmax = v_max,alpha=0.8)
    fig_2.colorbar(cax)
    ax.set_yticks([0, 1, 2, 3, 4, 5, 6, 7,8])
    ax.set_yticklabels(['']+lettres_ligne, weight = 'bold')
    ax.set_xticks(np.arange(0, 12, step=1))
    ax.set_xticklabels(chiffre_colonnes, weight = 'bold')
    ax.xaxis.set_ticks_position('top')
    if considered_moyen==0:
        plt.title(name, weight = 'heavy')
    else:
        plt.title(name+'\n valeur moyenne = '+str(round(considered_moyen,2))+' ecart-type = '+str(round(considered_std,2))+'->'+str(int(considered_std/considered_moyen*100))+'%', weight = 'heavy')
    for i in range(len(lettres_ligne)):
        for j in range(len(chiffre_colonnes)):
    #        text = ax.text(j, i, considered_matrice_plan_plaque[i, j],
    #                       ha="center", va="center", color="w", formatter)
            text = ax.text(j, i, str(round(considered_matrice[i, j],round_value)), #+"\n"+str(int(nb_dot_selected_matrice_plan_plaque[i, j])),
                           ha="center", va="center", color="k", size = 'x-large', weight = 'bold')
            if str(considered_matrice[i, j]) == 'nan' :
                text = ax.text(j, i, considered_matrice[i, j],
                           ha="center", va="center", color="r", size = 'x-large', weight = 'heavy')
            else:
                if is_it_dot_selected == 1 & is_it_nb_dot_tot == 1:
                    text = ax.text(j, i, "\n\n"+str(int(nb_dot_selected[i, j]))+"/"+str(int(nb_dot_total[i, j])),
                                   ha="center", va="center", color="k", size = 'smaller')

    plt.show()


def tic():
    #Homemade version of matlab tic and toc functions
    global startTime_for_tictoc
    startTime_for_tictoc = time.time()

def toc():
    if 'startTime_for_tictoc' in globals():
        print("Elapsed time is " + str(time.time() - startTime_for_tictoc) + " seconds.")
    else:
        print("Toc: start time not set")


def import_data_from_csv_synthese_zymintern(file):
    number_of_letters_max = 8
    number_of_colonne_number_max = 12
    nb_puits = 96

#    pandas.read_csv(file,sep=';',error_bad_lines=False,index_col=False)
#    une colonne sans nom met le bordel
    df_file = pandas.read_csv(file,sep=';',index_col=False,usecols=[0,1,2,3,4,5,6,7,8,9,10])

    volume_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    volume_std_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    diametre_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    diametre_std_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    N_dot_detected_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    N_dot_keep_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    N_cycle_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    porcent_dot_keep  = np.zeros((number_of_letters_max,number_of_colonne_number_max))

    j_scan = 0
    while j_scan<nb_puits:
        name_position = df_file['Position_plaque'][j_scan]
        letter_now = name_position[0]
        j_col = int(name_position[1:])-1 # -1 pour bien commencer avec un indice nul
        j_letter = int(alphabet_majuscule.find(letter_now))
        volume_raw[j_letter,j_col] = df_file['volume_after_statiscal_filter'][j_scan]
        volume_std_raw[j_letter,j_col] = df_file['volume_std_after_statiscal_filter'][j_scan]
        diametre_raw[j_letter,j_col] = df_file['diameter_mean_after_statiscal_filter'][j_scan]
        diametre_std_raw[j_letter,j_col] = df_file['diameter_std_after_statiscal_filter'][j_scan]
        N_dot_detected_raw[j_letter,j_col] = df_file['number_of_dot_BEFORE_statiscal_filter'][j_scan]
        N_dot_keep_raw[j_letter,j_col] = df_file['number_of_dot_after_statiscal_filter'][j_scan]
        N_cycle_raw[j_letter,j_col] = df_file['Ncycles_mean_after_statiscal_filter'][j_scan]
        porcent_dot_keep[j_letter,j_col] = N_dot_keep_raw[j_letter,j_col]/ N_dot_detected_raw[j_letter,j_col] *100
        j_scan += 1

    return volume_raw, volume_std_raw, diametre_raw, diametre_std_raw, N_dot_detected_raw, N_dot_keep_raw, N_cycle_raw, porcent_dot_keep

def import_data_from_csv_synthese_zymintern_nanofilm(file): # nouveau (v3 19/02/2025)
    number_of_letters_max = 8
    number_of_colonne_number_max = 12
    nb_puits = 96

#    pandas.read_csv(file,sep=';',error_bad_lines=False,index_col=False)
#    une colonne sans nom met le bordel
    df_file = pandas.read_csv(file,sep=';',index_col=False,usecols=[0,1,2,3,4,5,6,7,8,9])

    thickness_after_statiscal_filter = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    thickness_std_after_statiscal_filter = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    intensity_455 = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    intensity_730 = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    number_of_area_BEFORE_statiscal_filter = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    number_of_area_after_statiscal_filter  = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    pourcentage_zones_gardees = np.zeros((number_of_letters_max,number_of_colonne_number_max))

    j_scan = 0
    while j_scan<nb_puits:
        name_position = df_file['Position_plaque'][j_scan]
        letter_now = name_position[0]
        j_col = int(name_position[1:])-1 # -1 pour bien commencer avec un indice nul
        j_letter = int(alphabet_majuscule.find(letter_now))
        thickness_after_statiscal_filter[j_letter,j_col] = df_file['thickness_after_statiscal_filter'][j_scan]
        thickness_std_after_statiscal_filter[j_letter,j_col] = df_file['thickness_std_after_statiscal_filter'][j_scan]
        intensity_455[j_letter,j_col] = df_file['455_intensity'][j_scan]
        intensity_730[j_letter,j_col] = df_file['730_intensity'][j_scan]
        number_of_area_BEFORE_statiscal_filter[j_letter,j_col] = df_file['number_of_area_BEFORE_statiscal_filter'][j_scan]
        number_of_area_after_statiscal_filter[j_letter,j_col] = df_file['number_of_area_after_statiscal_filter'][j_scan]
        pourcentage_zones_gardees[j_letter,j_col] = number_of_area_after_statiscal_filter[j_letter,j_col]*100/number_of_area_BEFORE_statiscal_filter[j_letter,j_col]
        j_scan += 1

    return thickness_after_statiscal_filter, thickness_std_after_statiscal_filter, intensity_455, intensity_730, number_of_area_BEFORE_statiscal_filter, number_of_area_after_statiscal_filter, pourcentage_zones_gardees

def import_data_from_xlsx_synthese_zymintern(file): # pas utilisé
    number_of_letters_max = 8
    number_of_colonne_number_max = 12
    nb_puits = 96

#    pandas.read_csv(file,sep=';',error_bad_lines=False,index_col=False)
#    une colonne sans nom met le bordel
    df_file = pandas.read_excel(file, usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], index_col=False, engine='openpyxl')


    volume_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    volume_std_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    diametre_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    diametre_std_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    N_dot_detected_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    N_dot_keep_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    N_cycle_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    porcent_dot_keep  = np.zeros((number_of_letters_max,number_of_colonne_number_max))

    j_scan = 0
    while j_scan<nb_puits:
        name_position = df_file['Position_plaque'][j_scan]
        letter_now = name_position[0]
        j_col = int(name_position[1:])-1 # -1 pour bien commencer avec un indice nul
        j_letter = int(alphabet_majuscule.find(letter_now))
        volume_raw[j_letter,j_col] = df_file['volume_after_statiscal_filter'][j_scan]
        volume_std_raw[j_letter,j_col] = df_file['volume_std_after_statiscal_filter'][j_scan]
        diametre_raw[j_letter,j_col] = df_file['diameter_mean_after_statiscal_filter'][j_scan]
        diametre_std_raw[j_letter,j_col] = df_file['diameter_std_after_statiscal_filter'][j_scan]
        N_dot_detected_raw[j_letter,j_col] = df_file['number_of_dot_BEFORE_statiscal_filter'][j_scan]
        N_dot_keep_raw[j_letter,j_col] = df_file['number_of_dot_after_statiscal_filter'][j_scan]
        N_cycle_raw[j_letter,j_col] = df_file['Ncycles_mean_after_statiscal_filter'][j_scan]
        porcent_dot_keep[j_letter,j_col] = N_dot_keep_raw[j_letter,j_col]/ N_dot_detected_raw[j_letter,j_col] *100
        j_scan += 1

    return volume_raw, volume_std_raw, diametre_raw, diametre_std_raw, N_dot_detected_raw, N_dot_keep_raw, N_cycle_raw, porcent_dot_keep


def import_data_from_csv_synthese(file): # pas utilisé
    number_of_letters_max = 8
    number_of_colonne_number_max = 12
    nb_puits = 96

    df_file = pandas.read_csv(file,sep=';',error_bad_lines=False)

    volume_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    volume_std_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    diametre_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    diametre_std_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    N_dot_detected_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    N_dot_keep_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    N_cycle_raw = np.zeros((number_of_letters_max,number_of_colonne_number_max))
    porcent_dot_keep  = np.zeros((number_of_letters_max,number_of_colonne_number_max))

    j_scan = 0
    while j_scan<nb_puits:
        name_position = df_file['Position_plaque'][j_scan]
        letter_now = name_position[0]
        j_col = int(name_position[1:])-1 # -1 pour bien commencer avec un indice nul
        j_letter = int(alphabet_majuscule.find(letter_now))
        volume_raw[j_letter,j_col] = df_file['volume_mean_after_statiscal_filter'][j_scan]
        volume_raw_VN[j_letter,j_col] = df_file['volume_raw'][j_scan]
        volume_std_raw[j_letter,j_col] = df_file['volume_std_after_statiscal_filter'][j_scan]
        diametre_raw[j_letter,j_col] = df_file['diameter_mean_after_statiscal_filter'][j_scan]
        diametre_raw_VN[j_letter,j_col] = df_file['diameter_raw'][j_scan]
        diametre_std_raw[j_letter,j_col] = df_file['diameter_std_after_statiscal_filter'][j_scan]
        N_dot_detected_raw[j_letter,j_col] = df_file['number_of_dot_BEFORE_statiscal_filter'][j_scan]
        N_dot_keep_raw[j_letter,j_col] = df_file['number_of_dot_after_statiscal_filter'][j_scan]
        N_cycle_raw[j_letter,j_col] = df_file['Ncycles_mean_after_statiscal_filter'][j_scan]
        porcent_dot_keep[j_letter,j_col] = N_dot_keep_raw[j_letter,j_col]/ N_dot_detected_raw[j_letter,j_col] *100
        j_scan += 1

    return volume_raw, volume_std_raw, diametre_raw, diametre_std_raw, N_dot_detected_raw, N_dot_keep_raw, N_cycle_raw, porcent_dot_keep


# =============================================================================
# merge figures
# =============================================================================


def merge_two_figure(directory_list,name_plaque,name_figure_to_merge_list,directory_merge_save):
    name_figure_output = []
    number_of_plaque_total = 2
    directory_traitement_enzym = ''
#    nb_element_path_figure = len(name_figure_to_merge.split())
    name_figure_to_merge = name_figure_to_merge_list[0]
    name_save_figure = name_figure_to_merge.replace('/','_')#.split()[nb_element_path_figure-1]
    name_save_figure = name_save_figure.replace("\\",'_')

    name_save_figure = name_save_figure.replace(".",'_')

    subplot_geometry = 12
    subplot_indice = 1
    plt.close(0)
    plt.figure(0,figsize=(13,7))
    j_scan = 0
    while j_scan<number_of_plaque_total:
        fig_path = os.path.join(directory_list[j_scan], name_figure_to_merge_list[j_scan])
        fig = Image.open(fig_path)
        # plt.subplot(str(subplot_geometry)+str(subplot_indice))
        plt.subplot(int(str(subplot_geometry)+str(subplot_indice)))
        plt.imshow(fig, interpolation='none')
        plt.title(name_plaque)
        plt.axis('off')
        subplot_indice += 1
        j_scan += 1
    output_filename = os.path.join(directory_merge_save, f"{name_plaque}_{name_save_figure}.png")
    plt.savefig(output_filename, dpi = 350)
    name_figure_output.append(output_filename)
    plt.close('all')
    return name_figure_output
# =============================================================================
#   faire un dégradé de couleurs à partir d'une colormap      
# =============================================================================

def gen_color(cmap,n,reverse=False):
    '''Generates n distinct color from a given colormap.
    Args:
        cmap(str): The name of the colormap you want to use.
            Refer https://matplotlib.org/stable/tutorials/colors/colormaps.html to choose
            Suggestions:
            For Metallicity in Astrophysics: Use coolwarm, bwr, seismic in reverse
            For distinct objects: Use gnuplot, brg, jet,turbo.
        n(int): Number of colors you want from the cmap you entered.
        reverse(bool): False by default. Set it to True if you want the cmap result to be reversed.
    Returns: 
        colorlist(list): A list with hex values of colors.
    '''
    c_map = plt.cm.get_cmap(str(cmap)) # select the desired cmap
    arr=np.linspace(0,1,n) #create a list with numbers from 0 to 1 with n items
    colorlist=list()
    for c in arr:
        rgba=c_map(c) #select the rgba value of the cmap at point c which is a number between 0 to 1
        clr=colors.rgb2hex(rgba) #convert to hex
        colorlist.append(str(clr)) # create a list of these colors

    if reverse==True:
        colorlist.reverse()
    return colorlist




def gen_color_normalized(cmap,data_arr,reverse=False,vmin=0,vmax=0):
    '''Generates n distinct color from a given colormap for an array of desired data.
    Args:
        cmap(str): The name of the colormap you want to use.
            Refer https://matplotlib.org/stable/tutorials/colors/colormaps.html to choose

            Some suggestions:
            For Metallicity in Astrophysics: use coolwarm, bwr, seismic in reverse
            For distinct objects: Use gnuplot, brg, jet,turbo.
        data_arr(numpy.ndarray): The numpy array of data for which you want these distinct colors.
        reverse(bool): False by default. Set it to True if you want the cmap result to be reversed.
        vmin(float): 0 by default which sets vmin=minimum value in the data.
            When vmin is assigned a non zero value it normalizes the color based on this minimum value
        vmax(float): 0 by default which set vmax=maximum value in the data.
            When vmax is assigned a non zero value it normalizes the color based on this maximum value
    Returns: 
        colorlist_normalized(list): A normalized list of colors with hex values for the given array.
    '''

    if (vmin==0) and (vmax==0):
        data_min=np.min(data_arr)
        data_max=np.max(data_arr)

    else:
        if vmin>np.min(data_arr):
            warn_string="vmin you entered is greater than the minimum value in the data array "+str(np.min(data_arr))
            warnings.warn(warn_string)

        if(vmax<np.max(data_arr)):
            warn_string="vmax you entered is smaller than the maximum value in the data array "+str(np.max(data_arr))
            warnings.warn(warn_string)

        data_arr=np.append(data_arr,[vmin,vmax])
        data_min=np.min(data_arr)
        data_max=np.max(data_arr)


    c_map = plt.cm.get_cmap(str(cmap)) # select the desired cmap


    colorlist_normalized=list()
    for c in data_arr:
        norm=(c-data_min)/(data_max-data_min)*0.99
        rgba=c_map(norm) #select the rgba value of the cmap at point c which is a number between 0 to 1
        clr=colors.rgb2hex(rgba) #convert to hex
        colorlist_normalized.append(str(clr)) # create a list of these colors

    if reverse==True:
        del colorlist_normalized
        colorlist_normalized=list()
        for c in data_arr:
            norm=(c-data_min)/(data_max-data_min)*0.99
            rgba=c_map(1-norm) #select the rgba value of the cmap at point c which is a number between 0 to 1
            clr=colors.rgb2hex(rgba) #convert to hex
            colorlist_normalized.append(str(clr)) # create a list of these colors
    if (vmin==0) and (vmax==0):
        return colorlist_normalized
    else:
        colorlist_normalized=colorlist_normalized[:-2]
        return colorlist_normalized

#import_data_from_csv_synthese_zymintern('F:\\plaques_de_validation\\GPAxHA211214-15\\post_ZC_like\\730_ZI\\Synthese\\synthese_interferometric_dataCopie.csv')
