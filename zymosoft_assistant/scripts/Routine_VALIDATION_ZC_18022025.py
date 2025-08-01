# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 14:05:24 2022

@author: helene
@author: Hubert Goddefroy
@author: Benny Tenezeu

Pour reinclures les images dans les sortie de validation, il faut décommenter les lignes de copyfile, plt.savefig, mergetwofigure
"""
from shutil import copyfile

import cv2
from zymosoft_assistant.scripts.home_made_tools_v3   import *
from math import sqrt
from math import log
from math import isnan
import statistics
import os
from scipy import stats

# Helper function to safely create directories (including parent directories)
def safe_mkdir(directory_path):
    """
    Safely creates a directory and all parent directories if they don't exist.

    Args:
        directory_path: Path of the directory to create
    """
    os.makedirs(directory_path, exist_ok=True)

# =============================================================================
#  fonctions de la validation        
# =============================================================================
def repeta_sans_ref_v1(directory_source,nom_plaque,nom_reconstruction,directory_racine_output,CV_repeta_threshold):
    # =============================================================================
    # le but de cette fonction et de rassembler les données de répéta de l'imagerie d'une même plaque 
        # =============================================================================
        #     # autheur : Hélène Louis
        #     # 04/04/22 : fonction développée dans le cadre de la validation métrologique des Zymocubes
        #     # nécessite le module home_made_tools_v2.py 
        # =============================================================================
    #  Chemin de données:
    #       passage N fois de la plaques au lecteur -> passage dans Zyminterne  
    #   Détails de l'action de la fonction
    #       -> dans le dossier directory_source:
    #           Va chercher les noms des dossiers contenant nom_plaque (le nombre de dossiers donne le nombre de répéta)
    #           Va lire les fichiers synthese_interferometric_data.csv issu de Zyminterne dans le sous dossier nommé nom_reconstruction\Synthese
    #           Calcul les valeurs moyennes, ecart-types et CV des métriques usuelles des plaques 
    #           sort un indicateur sur le nombre de puits où le CV en volume est supérieur à CV_repeta_threshold
    #       -> dans le dossier de sortie directory_racine_output création d'un dossier noimmé comme la plaque contenant:
    #           copier coller des dotmaps  (brutes contours cycles)
    #           creation des figures sur la répéta (CV des volumes vs V mean)  
    #           creation des figures sur la répéta (CV des diametres vs D mean)  
    #           creation des colormaps associées
    #           creation du csv avec les data brutes agglomérées 
    #       -> retourne les valeurs des indicateurs et les array intéressants
    #            nb_iteration , nb_well_over_threshold , CV_max_volume, CV_min_volume, CV_mean_volume, CV_max_diametre, CV_min_diametre, CV_mean_diametre ,volume_mean_for_this_plate , volume_CV_for_this_plate , diametre_mean_for_this_plate , diametre_CV_for_this_plate 
    # =============================================================================
    liste_dossier_present = os.listdir(directory_source)
#    géométrie des plaques 96 puits
    number_of_letters_max = 8
    number_of_colonne_number_max = 12
#    génération de dégradés de couleurs du même nombre que le nombre de lettres
    color_letter =gen_color(cmap="viridis",n=number_of_letters_max)
    color_letter_bis =gen_color(cmap="autumn",n=number_of_letters_max)
#    génération des array qui vont contenir les métriques 
    volume_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    volume_std_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    diametre_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    diametre_std_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    nb_dot_detecte_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    n_dot_keep_now_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    n_cycle_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    porcent_dot_utile_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 

    volume_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    volume_std_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    diametre_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    diametre_std_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    nb_dot_detecte_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    n_dot_keep_now_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    n_cycle_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    porcent_dot_utile_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 

    volume_CV_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    volume_CV_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    diametre_CV_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    diametre_CV_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    nb_dot_detecte_CV_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    n_dot_keep_now_CV_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    n_cycle_CV_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    porcent_dot_utile_CV_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 

#    cherche le nombre d'itérations de l'imagerie et retient les noms de dossiers concernés
    liste_dossier_plaque = []
    nb_iteration = 0
    j_1 = 0
    while j_1<len(liste_dossier_present):
        if nom_plaque in liste_dossier_present[j_1]:
            liste_dossier_plaque.append(liste_dossier_present[j_1])
            nb_iteration += 1
        j_1 += 1
# création du dossie de sortie dans le dossier output avec le nom de plaque comme nom
    directory_out_this_plate = directory_racine_output + '\\'+nom_plaque
    if os.path.exists(directory_out_this_plate) == False:
        os.mkdir(directory_out_this_plate)

#    array qui vont récoltés toutes les entrées des itérations
    volume_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 
    volume_std_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 
    diametre_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 
    diametre_std_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 
    nb_dot_detecte_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 
    n_dot_keep_now_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 
    n_cycle_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 
    porcent_dot_utile_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 

#    par itération de l'acquisition, on va chercher synthese_interferometric_data.csv et on agglomère les data dans les array ci dessus 
#    ecriture dans un fichier csv de sortie les data utilisées
    string_title_csv_out = 'well;'
    j_iteration = 0
    while j_iteration<nb_iteration:

        dossier_now = directory_source + '\\' + liste_dossier_plaque[j_iteration]
        dossier_reconstruction =  dossier_now+ '\\'  + nom_reconstruction
        file = dossier_reconstruction + '\\synthese_interferometric_data.csv'
#        lecture de synthese_interferometric_data.csv issu de Zyminterne
        volume_now, volume_std_now, diametre_now, diametre_std_now, N_dot_detected_now, N_dot_keep_now, N_cycle_now, porcent_dot_keep_now =  import_data_from_csv_synthese_zymintern(file)
#
        #        copie des dotmaps pour un suivi  de l'allure des dots
        # copyfile(dossier_reconstruction+'\\dot_map_730.png',directory_out_this_plate+'\\dot_map_730_'+liste_dossier_plaque[j_iteration]+'.png')
        # copyfile(dossier_reconstruction+'\\dot_map_contour_730.png',directory_out_this_plate+'\\dot_map_contour_730'+liste_dossier_plaque[j_iteration]+'.png')
        # copyfile(dossier_reconstruction+'\\dot_map_cycle_730.png',directory_out_this_plate+'\\dot_map_cycle_730'+liste_dossier_plaque[j_iteration]+'.png')

        volume_plaque_all_iteration[:,:,j_iteration] = np.copy(volume_now[:,:])
        volume_std_plaque_all_iteration[:,:,j_iteration] = np.copy(volume_std_now[:,:])
        diametre_plaque_all_iteration[:,:,j_iteration] = np.copy(diametre_now[:,:])
        diametre_std_plaque_all_iteration[:,:,j_iteration] = np.copy(diametre_std_now[:,:])
        nb_dot_detecte_plaque_all_iteration[:,:,j_iteration] = np.copy(N_dot_detected_now[:,:])
        n_dot_keep_now_plaque_all_iteration[:,:,j_iteration] = np.copy(N_dot_keep_now[:,:])
        n_cycle_plaque_all_iteration[:,:,j_iteration] = np.copy(N_cycle_now[:,:])
        porcent_dot_utile_plaque_all_iteration[:,:,j_iteration] = np.copy(porcent_dot_keep_now[:,:])            
#        incrément de la string de titre du csv de sortie 
#        NB: le nom du dossier considéré est renseigné dans la 1ere colonne de la plaque (Volume)
        string_title_csv_out += 'Volume_' + liste_dossier_plaque[j_iteration] + ';'
        string_title_csv_out += 'Volume_std_' + str(j_iteration) + ';'
        string_title_csv_out += 'Diametre_' + str(j_iteration) + ';'
        string_title_csv_out += 'Diametre_std' + str(j_iteration) + ';'
        string_title_csv_out += 'N_dot_detected_' + str(j_iteration) + ';'
        string_title_csv_out += 'N_dot_keep_now' + str(j_iteration) + ';'
        string_title_csv_out += 'N_cycle_now' + str(j_iteration) + ';'
        string_title_csv_out += 'porcent_dot_keep_now' + str(j_iteration) + ';'

        j_iteration += 1

# calcul des moyennes des différentes métriques sauvées pour toutes les itérations et des écart-types et leur CV
#        attention puisque des métriques de base sont des écarts-types, on a ici des écart types d'écarts types


    csv_out_this_plate = open(directory_out_this_plate+'\\data_raw.csv','w')

    csv_out_this_plate.write(string_title_csv_out+'\n')

    j_letter = 0
    while j_letter<number_of_letters_max:
        j_col = 0
        while j_col<number_of_colonne_number_max:
#            calcul des moyennes
            volume_mean_for_this_plate[j_letter,j_col]= np.nanmean(volume_plaque_all_iteration[j_letter,j_col,:])
            volume_std_mean_for_this_plate[j_letter,j_col]= np.nanmean(volume_std_plaque_all_iteration[j_letter,j_col,:])
            diametre_mean_for_this_plate[j_letter,j_col]= np.nanmean(diametre_plaque_all_iteration[j_letter,j_col,:])
            diametre_std_mean_for_this_plate[j_letter,j_col]= np.nanmean(diametre_std_plaque_all_iteration[j_letter,j_col,:])
            nb_dot_detecte_mean_for_this_plate[j_letter,j_col]= np.nanmean(nb_dot_detecte_plaque_all_iteration[j_letter,j_col,:])
            n_dot_keep_now_mean_for_this_plate[j_letter,j_col]= np.nanmean(n_dot_keep_now_plaque_all_iteration[j_letter,j_col,:])
            n_cycle_mean_for_this_plate[j_letter,j_col]= np.nanmean(n_cycle_plaque_all_iteration[j_letter,j_col,:])
            porcent_dot_utile_mean_for_this_plate[j_letter,j_col]= np.nanmean(porcent_dot_utile_plaque_all_iteration[j_letter,j_col,:])
#            calcul des ecarts types
            volume_std_for_this_plate[j_letter,j_col]= np.nanstd(volume_plaque_all_iteration[j_letter,j_col,:])
            volume_std_std_for_this_plate[j_letter,j_col]= np.nanstd(volume_std_plaque_all_iteration[j_letter,j_col,:])
            diametre_std_for_this_plate[j_letter,j_col]= np.nanstd(diametre_plaque_all_iteration[j_letter,j_col,:])
            diametre_std_std_for_this_plate[j_letter,j_col]= np.nanstd(diametre_std_plaque_all_iteration[j_letter,j_col,:])
            nb_dot_detecte_std_for_this_plate[j_letter,j_col]= np.nanstd(nb_dot_detecte_plaque_all_iteration[j_letter,j_col,:])
            n_dot_keep_now_std_for_this_plate[j_letter,j_col]= np.nanstd(n_dot_keep_now_plaque_all_iteration[j_letter,j_col,:])
            n_cycle_std_for_this_plate[j_letter,j_col]= np.nanstd(n_cycle_plaque_all_iteration[j_letter,j_col,:])
            porcent_dot_utile_std_for_this_plate[j_letter,j_col]= np.nanstd(porcent_dot_utile_plaque_all_iteration[j_letter,j_col,:])
#            calcul des CV
            volume_CV_for_this_plate[j_letter,j_col]= np.copy(volume_std_for_this_plate[j_letter,j_col]/volume_mean_for_this_plate[j_letter,j_col]*100)
            volume_CV_std_for_this_plate[j_letter,j_col]= np.copy(volume_std_std_for_this_plate[j_letter,j_col]/volume_std_mean_for_this_plate[j_letter,j_col]*100)
            diametre_CV_for_this_plate[j_letter,j_col]= np.copy(diametre_std_for_this_plate[j_letter,j_col]/diametre_mean_for_this_plate[j_letter,j_col]*100)
            diametre_CV_std_for_this_plate[j_letter,j_col]= np.copy(diametre_std_std_for_this_plate[j_letter,j_col]/diametre_std_mean_for_this_plate[j_letter,j_col]*100)
            nb_dot_detecte_CV_for_this_plate[j_letter,j_col]= np.copy(nb_dot_detecte_std_for_this_plate[j_letter,j_col]/nb_dot_detecte_mean_for_this_plate[j_letter,j_col]*100)
            n_dot_keep_now_CV_for_this_plate[j_letter,j_col]= np.copy(n_dot_keep_now_std_for_this_plate[j_letter,j_col]/n_dot_keep_now_mean_for_this_plate[j_letter,j_col]*100)
            n_cycle_CV_for_this_plate[j_letter,j_col]= np.copy(n_cycle_std_for_this_plate[j_letter,j_col]/n_cycle_mean_for_this_plate[j_letter,j_col]*100)
            porcent_dot_utile_CV_for_this_plate[j_letter,j_col]= np.copy(porcent_dot_utile_std_for_this_plate[j_letter,j_col]/porcent_dot_utile_mean_for_this_plate[j_letter,j_col]*100)
            line_csv_out = ''
            line_csv_out += alphabet_majuscule[j_letter] + str(j_col+1) + ';'

            j_iteration = 0
            while j_iteration<nb_iteration:
                line_csv_out += str(volume_plaque_all_iteration[j_letter,j_col,j_iteration])+';'+str(volume_std_plaque_all_iteration[j_letter,j_col,j_iteration])+';'
                line_csv_out += str(diametre_plaque_all_iteration[j_letter,j_col,j_iteration])+';'+str(diametre_std_plaque_all_iteration[j_letter,j_col,j_iteration])+';'
                line_csv_out += str(nb_dot_detecte_plaque_all_iteration[j_letter,j_col,j_iteration])+';'+str(n_dot_keep_now_plaque_all_iteration[j_letter,j_col,j_iteration])+';'
                line_csv_out += str(n_cycle_plaque_all_iteration[j_letter,j_col,j_iteration])+';'+str(porcent_dot_utile_plaque_all_iteration[j_letter,j_col,j_iteration])+';'

                j_iteration += 1

            csv_out_this_plate.write(line_csv_out+'\n')    
            j_col += 1
        j_letter += 1

    csv_out_this_plate.close()

    #affiche_colormap_etude_general_v2(volume_mean_for_this_plate,nom_plaque+'volume_mean_for_this_plate on all iteration','jet',0,500)
    #plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'volume_mean_for_this_plate.jpg')

    #affiche_colormap_etude_general_v2(volume_std_for_this_plate,nom_plaque+'volume_std_for_this_plate on all iteration','jet',0,0)
    #plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'volume_std_for_this_plate.jpg')

    #affiche_colormap_etude_general_v2(volume_CV_for_this_plate,nom_plaque+'volume_CV_for_this_plate on all iteration','Reds',0,10)
    #plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'volume_CV_for_this_plate.jpg')

    #affiche_colormap_etude_general_v2(volume_std_mean_for_this_plate,nom_plaque+'volume_std_mean_for_this_plate on all iteration','jet',0,0)
    #plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'volume_std_mean_for_this_plate.jpg')

    #affiche_colormap_etude_general_v2(nb_dot_detecte_mean_for_this_plate,nom_plaque+'nb_dot_detecte_mean_for_this_plate on all iteration','jet',0,0)
    #plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'nb_dot_detecte_mean_for_this_plate.jpg')

    #affiche_colormap_etude_general_v2(nb_dot_detecte_std_for_this_plate,nom_plaque+'nb_dot_detecte_std_for_this_plate on all iteration','jet',0,0)
    #plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'nb_dot_detecte_std_for_this_plate.jpg')

    #affiche_colormap_etude_general_v2(porcent_dot_utile_mean_for_this_plate,nom_plaque+'porcent_dot_utile_mean_for_this_plate on all iteration','jet',0,0)
    #plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'porcent_dot_utile_mean_for_this_plate.jpg')


    mask_under_threshold = volume_CV_for_this_plate < CV_repeta_threshold
    nb_well_under_threshold = np.nansum(mask_under_threshold)

    mask_over_threshold = volume_CV_for_this_plate > CV_repeta_threshold
    nb_well_over_threshold = np.nansum(mask_over_threshold)

    CV_max_volume = np.nanmax(volume_CV_for_this_plate)
    CV_min_volume = np.nanmin(volume_CV_for_this_plate)
    CV_mean_volume = np.nanmean(volume_CV_for_this_plate)

    CV_max_diametre = np.nanmax(diametre_CV_for_this_plate)
    CV_min_diametre = np.nanmin(diametre_CV_for_this_plate)
    CV_mean_diametre = np.nanmean(diametre_CV_for_this_plate)

    v_min_mean = np.nanmin(volume_mean_for_this_plate)
    v_max_mean = np.nanmax(volume_mean_for_this_plate)


    plt.close('all')
    plt.figure(1)
    plt.title(nom_plaque+' sur ' + str(nb_iteration)+ 'runs\n'+str(nb_well_over_threshold)+ ' puits au dessus de '+str(CV_repeta_threshold)+'% de CV sur le volumes')
    j_letter = 0
    while j_letter<number_of_letters_max:
        plt.plot(volume_mean_for_this_plate[j_letter,:],volume_CV_for_this_plate[j_letter,:],'o',color = color_letter[j_letter], label = alphabet_majuscule[j_letter])        
        j_letter += 1
    plt.axhline(y = CV_repeta_threshold,xmin=v_min_mean, xmax=v_max_mean, ls='--' , color = 'k', label = str(CV_repeta_threshold)+'%')
    plt.xlabel('V_mean µm^3')
    plt.ylabel('CV %')
    plt.legend()
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'_CV_on_V_vs_V_mean.jpg')

    plt.figure(2)
    plt.title(nom_plaque+' sur ' + str(nb_iteration)+ 'runs')
    j_letter = 0
    while j_letter<number_of_letters_max:
        plt.plot(diametre_mean_for_this_plate[j_letter,:],diametre_CV_for_this_plate[j_letter,:],'v',color = color_letter[j_letter], label = alphabet_majuscule[j_letter])        
        j_letter += 1
    plt.axhline(y = 5,xmin=v_min_mean, xmax=v_max_mean, ls='--' , color = 'k', label = '5%')
    plt.xlabel('D_mean µm')
    plt.ylabel('CV on D%')
    plt.legend()
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'_CV_on_D_vs_D_mean.jpg')
    plt.close('all')

    return  nb_iteration , nb_well_over_threshold , CV_max_volume, CV_min_volume, CV_mean_volume, CV_max_diametre, CV_min_diametre, CV_mean_diametre ,volume_mean_for_this_plate , volume_CV_for_this_plate , diametre_mean_for_this_plate , diametre_CV_for_this_plate 

def repeta_sans_ref_v1_nanofilm(directory_source,nom_plaque,nom_reconstruction,directory_racine_output,CV_repeta_threshold):
    # =============================================================================
    # le but de cette fonction et de rassembler les données de répéta de l'imagerie d'une même plaque 
        # =============================================================================
        #     # auteur : Hubert Goddefroy
        #     # 19/02/2025 : fonction développée dans le cadre de la validation métrologique des Zymocubes
        #     # nécessite le module home_made_tools_v3.py 
        # =============================================================================
    #  Chemin de données:
    #       passage N fois de la plaques au lecteur -> passage dans Zyminterne  
    #   Détails de l'action de la fonction
    #       -> dans le dossier directory_source:
    #           Va chercher les noms des dossiers contenant nom_plaque (le nombre de dossiers donne le nombre de répéta)
    #           Va lire les fichiers synthese_interferometric_data.csv issu de Zyminterne dans le sous dossier nommé nom_reconstruction\Synthese
    #           Calcul les valeurs moyennes, ecart-types et CV des métriques usuelles des plaques 
    #           sort un indicateur sur le nombre de puits où le CV en volume est supérieur à CV_repeta_threshold
    #       -> dans le dossier de sortie directory_racine_output création d'un dossier noimmé comme la plaque contenant:
    #           copier coller des dotmaps  (brutes contours cycles)
    #           creation des figures sur la répéta (CV des volumes vs V mean)  
    #           creation des figures sur la répéta (CV des diametres vs D mean)  
    #           creation des colormaps associées
    #           creation du csv avec les data brutes agglomérées 
    #       -> retourne les valeurs des indicateurs et les array intéressants
    #            nb_iteration , nb_well_over_threshold , CV_max_volume, CV_min_volume, CV_mean_volume, CV_max_diametre, CV_min_diametre, CV_mean_diametre ,volume_mean_for_this_plate , volume_CV_for_this_plate , diametre_mean_for_this_plate , diametre_CV_for_this_plate 
    # =============================================================================
    liste_dossier_present = os.listdir(directory_source)
#    géométrie des plaques 96 puits
    number_of_letters_max = 8
    number_of_colonne_number_max = 12
#    génération de dégradés de couleurs du même nombre que le nombre de lettres
    color_letter =gen_color(cmap="viridis",n=number_of_letters_max)
    color_letter_bis =gen_color(cmap="autumn",n=number_of_letters_max)
#    génération des array qui vont contenir les métriques 
    thickness_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max))  
    intensity_455_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    intensity_730_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    nb_area_before_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    nb_area_after_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    porcent_area_utile_mean_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 

    thickness_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max))  
    intensity_455_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    intensity_730_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    nb_area_before_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    nb_area_after_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    porcent_area_utile_std_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 

    thickness_CV_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max))  
    intensity_455_CV_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    intensity_730_CV_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    nb_area_before_CV_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    nb_area_after_CV_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 
    porcent_area_utile_CV_for_this_plate = np.zeros((number_of_letters_max,number_of_colonne_number_max))

#    cherche le nombre d'itérations de l'imagerie et retient les noms de dossiers concernés
    liste_dossier_plaque = []
    nb_iteration = 0
    j_1 = 0
    while j_1<len(liste_dossier_present):
        if nom_plaque in liste_dossier_present[j_1]:
            liste_dossier_plaque.append(liste_dossier_present[j_1])
            nb_iteration += 1
        j_1 += 1
# création du dossie de sortie dans le dossier output avec le nom de plaque comme nom
    directory_out_this_plate = directory_racine_output + '\\'+nom_plaque
    if os.path.exists(directory_out_this_plate) == False:
        os.mkdir(directory_out_this_plate)

#    array qui vont récoltés toutes les entrées des itérations
    thickness_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 
    thickness_std_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 
    intensite_455_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 
    intensite_730_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 
    nb_area_before_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 
    n_area_after_now_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration)) 
    porcent_area_utile_plaque_all_iteration = np.zeros((number_of_letters_max,number_of_colonne_number_max,nb_iteration))  

#    par itération de l'acquisition, on va chercher synthese_interferometric_data.csv et on agglomère les data dans les array ci dessus 
#    ecriture dans un fichier csv de sortie les data utilisées
    string_title_csv_out = 'well;'
    j_iteration = 0
    while j_iteration<nb_iteration:

        dossier_now = directory_source + '\\' + liste_dossier_plaque[j_iteration]
        dossier_reconstruction =  dossier_now+ '\\'  + nom_reconstruction
        file = dossier_reconstruction + '\\synthese_interferometric_data.csv'
#        lecture de synthese_interferometric_data.csv issu de Zyminterne
        thickness_now, thickness_std_now, intensite_455_now, intensite_730_now, N_area_before_now, N_area_after_now, porcent_area_now =  import_data_from_csv_synthese_zymintern_nanofilm(file)
#        copie des dotmaps pour un suivi  de l'allure des dots
        # copyfile(dossier_reconstruction+'\\intensity_455_map.png',directory_out_this_plate+'\\intensity_455_'+liste_dossier_plaque[j_iteration]+'.png')
        # copyfile(dossier_reconstruction+'\\intensity_730_map.png',directory_out_this_plate+'\\intensity_730_'+liste_dossier_plaque[j_iteration]+'.png')
        # copyfile(dossier_reconstruction+'\\stat_litteral_intensity_455_colormap.png',directory_out_this_plate+'\\intensity_455_colormap'+liste_dossier_plaque[j_iteration]+'.png')
        # copyfile(dossier_reconstruction+'\\stat_litteral_intensity_730_colormap.png',directory_out_this_plate+'\\intensity_730_colormap'+liste_dossier_plaque[j_iteration]+'.png')
        # copyfile(dossier_reconstruction+'\\stat_litteral_thicknesses_colormap.png',directory_out_this_plate+'\\thicknesses'+liste_dossier_plaque[j_iteration]+'.png')

        thickness_plaque_all_iteration[:,:,j_iteration] = np.copy(thickness_now[:,:])
        thickness_std_plaque_all_iteration[:,:,j_iteration] = np.copy(thickness_std_now[:,:])
        intensite_455_plaque_all_iteration[:,:,j_iteration] = np.copy(intensite_455_now[:,:])
        intensite_730_plaque_all_iteration[:,:,j_iteration] = np.copy(intensite_730_now[:,:])
        nb_area_before_plaque_all_iteration[:,:,j_iteration] = np.copy(N_area_before_now[:,:])
        n_area_after_now_plaque_all_iteration[:,:,j_iteration] = np.copy(N_area_after_now[:,:])
        porcent_area_utile_plaque_all_iteration[:,:,j_iteration] = np.copy(porcent_area_now[:,:])            
#        incrément de la string de titre du csv de sortie 
#        NB: le nom du dossier considéré est renseigné dans la 1ere colonne de la plaque (Volume)
        string_title_csv_out += 'épaisseur_' + liste_dossier_plaque[j_iteration] + ';'
        string_title_csv_out += 'écart-type_épaisseur_' + str(j_iteration) + ';'
        string_title_csv_out += 'intensité_455' + str(j_iteration) + ';'
        string_title_csv_out += 'intensité_730' + str(j_iteration) + ';'
        string_title_csv_out += 'N_zones_avant' + str(j_iteration) + ';'
        string_title_csv_out += 'N_zones_après' + str(j_iteration) + ';'
        string_title_csv_out += 'pourcentage_zones_utiles' + str(j_iteration) + ';'

        j_iteration += 1

# calcul des moyennes des différentes métriques sauvées pour toutes les itérations et des écart-types et leur CV
#        attention puisque des métriques de base sont des écarts-types, on a ici des écart types d'écarts types


    csv_out_this_plate = open(directory_out_this_plate+'\\data_raw.csv','w')

    csv_out_this_plate.write(string_title_csv_out+'\n')

    j_letter = 0
    while j_letter<number_of_letters_max:
        j_col = 0
        while j_col<number_of_colonne_number_max:
#            calcul des moyennes
            thickness_mean_for_this_plate[j_letter,j_col]= np.nanmean(thickness_plaque_all_iteration[j_letter,j_col,:])
            intensity_455_mean_for_this_plate[j_letter,j_col]= np.nanmean(intensite_455_plaque_all_iteration[j_letter,j_col,:])
            intensity_730_mean_for_this_plate[j_letter,j_col]= np.nanmean(intensite_730_plaque_all_iteration[j_letter,j_col,:])
            nb_area_before_mean_for_this_plate[j_letter,j_col]= np.nanmean(nb_area_before_plaque_all_iteration[j_letter,j_col,:])
            nb_area_after_mean_for_this_plate[j_letter,j_col]= np.nanmean(n_area_after_now_plaque_all_iteration[j_letter,j_col,:])
            porcent_area_utile_mean_for_this_plate[j_letter,j_col]= np.nanmean(porcent_area_utile_plaque_all_iteration[j_letter,j_col,:])

#            calcul des ecarts types
            thickness_std_for_this_plate[j_letter,j_col]= np.nanstd(thickness_plaque_all_iteration[j_letter,j_col,:])
            intensity_455_std_for_this_plate[j_letter,j_col]= np.nanstd(intensite_455_plaque_all_iteration[j_letter,j_col,:])
            intensity_730_std_for_this_plate[j_letter,j_col]= np.nanstd(intensite_730_plaque_all_iteration[j_letter,j_col,:])
            nb_area_before_std_for_this_plate[j_letter,j_col]= np.nanstd(nb_area_before_plaque_all_iteration[j_letter,j_col,:])
            nb_area_after_std_for_this_plate[j_letter,j_col]= np.nanstd(n_area_after_now_plaque_all_iteration[j_letter,j_col,:])
            porcent_area_utile_std_for_this_plate[j_letter,j_col]= np.nanstd(porcent_area_utile_plaque_all_iteration[j_letter,j_col,:])

#            calcul des CV
            thickness_CV_for_this_plate[j_letter,j_col]= np.copy(thickness_std_for_this_plate[j_letter,j_col]/thickness_mean_for_this_plate[j_letter,j_col]*100)
            intensity_455_CV_for_this_plate[j_letter,j_col]= np.copy(intensity_455_std_for_this_plate[j_letter,j_col]/intensity_455_mean_for_this_plate[j_letter,j_col]*100)
            intensity_730_CV_for_this_plate[j_letter,j_col]= np.copy(intensity_730_std_for_this_plate[j_letter,j_col]/intensity_730_mean_for_this_plate[j_letter,j_col]*100)
            nb_area_before_CV_for_this_plate[j_letter,j_col]= np.copy(nb_area_before_std_for_this_plate[j_letter,j_col]/nb_area_before_mean_for_this_plate[j_letter,j_col]*100)
            nb_area_after_CV_for_this_plate[j_letter,j_col]= np.copy(nb_area_after_std_for_this_plate[j_letter,j_col]/nb_area_after_mean_for_this_plate[j_letter,j_col]*100)
            porcent_area_utile_CV_for_this_plate[j_letter,j_col]= np.copy(porcent_area_utile_std_for_this_plate[j_letter,j_col]/porcent_area_utile_mean_for_this_plate[j_letter,j_col]*100)

            line_csv_out = ''
            line_csv_out += alphabet_majuscule[j_letter] + str(j_col+1) + ';'

            j_iteration = 0
            while j_iteration<nb_iteration:
                line_csv_out += str(thickness_plaque_all_iteration[j_letter,j_col,j_iteration])+';_;'
                # line_csv_out += str(intensity_455_mean_for_this_plate[j_letter,j_col,j_iteration])+';_;'
                # line_csv_out += str(intensity_730_mean_for_this_plate[j_letter,j_col,j_iteration])+';_;'
                # line_csv_out += str(porcent_area_utile_mean_for_this_plate[j_letter,j_col,j_iteration])+';_;'

                j_iteration += 1

            csv_out_this_plate.write(line_csv_out+'\n')    
            j_col += 1
        j_letter += 1

    csv_out_this_plate.close()

    affiche_colormap_etude_general_v2(thickness_mean_for_this_plate,nom_plaque+'thickness_mean_for_this_plate on all iteration','jet',0,500)
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'thickness_mean_for_this_plate.jpg')

    affiche_colormap_etude_general_v2(intensity_455_mean_for_this_plate,nom_plaque+'intensity_455_for_this_plate on all iteration','jet',0,0)
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'intensity_455_for_this_plate.jpg')

    affiche_colormap_etude_general_v2(intensity_730_mean_for_this_plate,nom_plaque+'intensity_730_for_this_plate on all iteration','Reds',0,10)
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'intensity_730_for_this_plate.jpg')

    affiche_colormap_etude_general_v2(nb_area_before_mean_for_this_plate,nom_plaque+'nb_area_before_mean_for_this_plate on all iteration','jet',0,0)
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'nb_area_before_mean_for_this_plate.jpg')

    affiche_colormap_etude_general_v2(nb_area_after_mean_for_this_plate,nom_plaque+'nb_area_after_mean_for_this_plate on all iteration','jet',0,0)
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'nb_area_after_mean_for_this_plate.jpg')

    affiche_colormap_etude_general_v2(porcent_area_utile_mean_for_this_plate,nom_plaque+'porcent_area_utile_for_this_plate on all iteration','jet',0,0)
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'porcent_area_utile_for_this_plate.jpg')

    mask_under_threshold = thickness_mean_for_this_plate < CV_repeta_threshold
    nb_well_under_threshold = np.nansum(mask_under_threshold)

    mask_over_threshold = thickness_CV_for_this_plate > CV_repeta_threshold
    nb_well_over_threshold = np.nansum(mask_over_threshold)

    CV_max_thickness = np.nanmax(thickness_CV_for_this_plate)
    CV_min_thickness = np.nanmin(thickness_CV_for_this_plate)
    CV_mean_thickness = np.nanmean(thickness_CV_for_this_plate)

    CV_max_I4 = np.nanmax(intensity_455_CV_for_this_plate)
    CV_min_I4 = np.nanmin(intensity_455_CV_for_this_plate)
    CV_mean_I4 = np.nanmean(intensity_455_CV_for_this_plate)

    CV_max_I7 = np.nanmax(intensity_730_CV_for_this_plate)
    CV_min_I7 = np.nanmin(intensity_730_CV_for_this_plate)
    CV_mean_I7 = np.nanmean(intensity_730_CV_for_this_plate)

    t_min_mean = np.nanmin(thickness_mean_for_this_plate)
    t_max_mean = np.nanmax(thickness_mean_for_this_plate)


    plt.close('all')
    plt.figure(1)
    plt.title(nom_plaque+' sur ' + str(nb_iteration)+ 'runs\n'+str(nb_well_over_threshold)+ ' puits au dessus de '+str(CV_repeta_threshold)+'% de CV sur l\'épaisseur')
    j_letter = 0
    while j_letter<number_of_letters_max:
        plt.plot(thickness_mean_for_this_plate[j_letter,:],thickness_CV_for_this_plate[j_letter,:],'o',color = color_letter[j_letter], label = alphabet_majuscule[j_letter])        
        j_letter += 1
    plt.axhline(y = CV_repeta_threshold,xmin=t_min_mean, xmax=t_max_mean, ls='--' , color = 'k', label = str(CV_repeta_threshold)+'%')
    plt.xlabel('T_mean µm^3')
    plt.ylabel('CV %')
    plt.legend()
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'_CV_on_T_vs_T_mean.jpg')

    plt.figure(2)
    plt.title(nom_plaque+' sur ' + str(nb_iteration)+ 'runs')
    j_letter = 0
    while j_letter<number_of_letters_max:
        plt.plot(intensity_455_mean_for_this_plate[j_letter,:],intensity_455_CV_for_this_plate[j_letter,:],'v',color = color_letter[j_letter], label = alphabet_majuscule[j_letter])        
        j_letter += 1
    plt.axhline(y = 5,xmin=t_min_mean, xmax=t_max_mean, ls='--' , color = 'k', label = '5%')
    plt.xlabel('Intensity_455_mean')
    plt.ylabel('CV on Intensity%')
    plt.legend()
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'_CV_on_I_vs_I_455_mean.jpg')
    plt.close('all')

    return  nb_iteration , nb_well_over_threshold , CV_max_thickness, CV_min_thickness, CV_mean_thickness, CV_max_I4, CV_min_I4, CV_mean_I4 ,CV_max_I7, CV_min_I7, CV_mean_I7, thickness_mean_for_this_plate , thickness_CV_for_this_plate , intensity_455_mean_for_this_plate , intensity_455_CV_for_this_plate , intensity_730_mean_for_this_plate , intensity_730_CV_for_this_plate

def comparaison_ZC_to_ref_v1(nom_gp,chemin_intrument_1,type_intrument_1,chemin_intrument_2,type_intrument_2,directory_racine_to_save,name_dossier_to_save,tolerance_relative_fit):    
# =============================================================================
#     le but de cette fonction est de comparer les data en volumes d'un lecteur à un autre
#    la 1ere appli est de confronter les data ZC 3 - 4 au proto (mais ça peut servir dans d'autres config ZC to ZC...)
        # =============================================================================
        #     # autheur : Hélène Louis
        #     # 05/04/22 : fonction développée dans le cadre de la validation métrologique des Zymocubes
        #     # nécessite le module home_made_tools_v2.py 
        # =============================================================================
    #  Chemin de données:
    #       il faut les données sorties de ZI pour les 2 lectures à comparer  
    #   Détails de l'action de la fonction
    #       -> dans les dossiers chemin_intrument_1 et chemin_intrument_2:
    #           Va chercher les sous dossiers Synthese
    #           Va lire les fichiers synthese_interferometric_data.csv issu de Zyminterne 
    #           Calcul les valeurs différences entre les métriques usuelles des plaques (volumes, diamètres, nb dot...)
    #           FIT sur les volumes (instrument 2 en x, instrument 1 en y) après un filtre pour exclure les outliers évidents (20% de tolerance en différence relative)
    #           Calcul du nombre de puits où le fit et les data sont trop loins : seuil = tolerance_relative_fit, sort l'indicateur nb_puits_loin_fit
    #       -> dans le dossier de sortie directory_racine_output création d'un dossier nommé comme name_dossier_to_save contenant:
    #                les colormaps:
    #                   Matrix_volume_difference.
    #                   Matrix_volume_difference_relative
    #                   Matrix_volume_ratio
    #                   Matrix_diametre_difference
    #                   Matrix_diametre_difference_relative  
    #               des figures doublées avec:
    #                   les dotmaps, les colormaps volumes , diametres, 
    #               des graphs 
    #                   les data
    #                   le fit 
    #               des csv
    #                   raw
    #                   kpi
    #       -> retourne les valeurs des indicateurs et les array intéressants
    #            name_dossier_to_save, slope_fit_inverse, intercept_fit_inverse, r_value_fit_inverse, nb_puits_loin_fit, vecteur_volume_instrument_1, vecteur_volume_instrument_2
    # =============================================================================
# =============================================================================

    #Debug , print tout les paramètre de la fonction
    print('nom_gp:',nom_gp)
    print('chemin_intrument_1:',chemin_intrument_1)
    print('type_intrument_1:',type_intrument_1)
    print('chemin_intrument_2:',chemin_intrument_2)
    print('type_intrument_2:',type_intrument_2)
    print('directory_racine_to_save:',directory_racine_to_save)
    print('name_dossier_to_save:',name_dossier_to_save)
    print('tolerance_relative_fit:',tolerance_relative_fit)

    number_of_letters_max = 8
    number_of_colonne_number_max = 12
    # =============================================================================
    # # import des données du instrument_1
    # =============================================================================
    directory_source_synthese_instrument_1 = chemin_intrument_1+''
    name_dossier_instrument_1 = chemin_intrument_1
    file_data_instrument_1 = directory_source_synthese_instrument_1+'\\synthese_interferometric_data.csv'

    # IMPORT DES DATA CONTENUES DANS LE CSV SYNTHESE 
    volume_instrument_1, volume_std_instrument_1, diametre_instrument_1, diametre_std_instrument_1, N_dot_detected_instrument_1, N_dot_keep_instrument_1, N_cycle_instrument_1, porcent_dot_keep_instrument_1 = import_data_from_csv_synthese_zymintern(file_data_instrument_1)
    #volume_instrument_1, volume_std_instrument_1, diametre_instrument_1, diametre_std_instrument_1, N_dot_detected_instrument_1, N_dot_keep_instrument_1, N_cycle_instrument_1, porcent_dot_keep_instrument_1 = import_data_from_csv_synthese(file_data_instrument_1)

    # =============================================================================
    # # import des données du instrument_2
    # =============================================================================
    directory_source_synthese_instrument_2 = chemin_intrument_2+''
    file_data_instrument_2 = directory_source_synthese_instrument_2+'\\synthese_interferometric_data.csv'

    # IMPORT DES DATA CONTENUES DANS LE CSV SYNTHESE 
    volume_instrument_2, volume_std_instrument_2, diametre_instrument_2, diametre_std_instrument_2, N_dot_detected_instrument_2, N_dot_keep_instrument_2, N_cycle_instrument_2, porcent_dot_keep_instrument_2 = import_data_from_csv_synthese_zymintern(file_data_instrument_2)
    # =============================================================================
    # endroit ou stocker la comparaison
    # =============================================================================

    directory_plaque_to_save = directory_racine_to_save + '\\'+name_dossier_to_save
    if os.path.exists(directory_plaque_to_save) == False:
        os.mkdir(directory_plaque_to_save)

    # =============================================================================
    # la comparaison
    # =============================================================================
    plt.close('all')   
    Matrix_volume_difference = np.zeros((number_of_letters_max,number_of_colonne_number_max))    
    Matrix_volume_difference_relative = np.zeros((number_of_letters_max,number_of_colonne_number_max))        
    Matrix_volume_ratio = np.zeros((number_of_letters_max,number_of_colonne_number_max))    
    Matrix_diametre_difference = np.zeros((number_of_letters_max,number_of_colonne_number_max))    
    Matrix_diametre_difference_relative = np.zeros((number_of_letters_max,number_of_colonne_number_max))    

    Matrix_nb_dot_utile_pourcent_difference = np.zeros((number_of_letters_max,number_of_colonne_number_max))    

#    fichier de sortie des data raw
    fichier_save = open(directory_plaque_to_save+'\\data_comparative'+type_intrument_1+'_'+type_intrument_2+'.csv','w')
    fichier_save.write('weel;V_instrument_1;D_instrument_1;V_instrument_2;D_instrument_2;\n')

    # calcul des différences selon le schéma: 1 - 2 par défaut et 2 la référence pour les relatives
    j_letter = 0
    while j_letter<number_of_letters_max:
        j_col = 0
        while j_col<number_of_colonne_number_max:
            Matrix_volume_difference[j_letter,j_col] = np.copy(volume_instrument_1[j_letter,j_col] - volume_instrument_2[j_letter,j_col])
#            prise en compte du cas patholoque ou on doit diviser par 0
            if volume_instrument_2[j_letter,j_col] != 0:
                Matrix_volume_difference_relative[j_letter,j_col] = np.copy((volume_instrument_1[j_letter,j_col] - volume_instrument_2[j_letter,j_col])/volume_instrument_2[j_letter,j_col] *100)
                Matrix_volume_ratio[j_letter,j_col] =np.copy(volume_instrument_1[j_letter,j_col] / volume_instrument_2[j_letter,j_col])
            else:
                Matrix_volume_difference_relative[j_letter,j_col] = np.nan
                Matrix_volume_ratio[j_letter,j_col] = np.nan

            Matrix_diametre_difference[j_letter,j_col] = np.copy(diametre_instrument_1[j_letter,j_col] - diametre_instrument_2[j_letter,j_col] )
            if diametre_instrument_2[j_letter,j_col] != 0:
               Matrix_diametre_difference_relative[j_letter,j_col]  = np.copy((diametre_instrument_1[j_letter,j_col] - diametre_instrument_2[j_letter,j_col] ) / diametre_instrument_2[j_letter,j_col] *100)
            else:
                Matrix_diametre_difference_relative[j_letter,j_col] = np.nan

            Matrix_nb_dot_utile_pourcent_difference[j_letter,j_col] = np.copy(porcent_dot_keep_instrument_1[j_letter,j_col] - porcent_dot_keep_instrument_2[j_letter,j_col]) 
            fichier_save.write(alphabet_majuscule[j_letter]+str(j_col+1)+';'+str(volume_instrument_1[j_letter,j_col])+';'+str(diametre_instrument_1[j_letter,j_col])+';'+str(volume_instrument_2[j_letter,j_col])+';'+str(diametre_instrument_2[j_letter,j_col])+';\n')
            j_col += 1
        j_letter += 1
    fichier_save.close()

# présentation des différences calculées selon des colormaps    
    #affiche_colormap_etude_general(Matrix_volume_difference,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\nMatrix_volume_difference','RdGy',np.nanmin(Matrix_volume_difference),np.nanmax(Matrix_volume_difference))
    #plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_volume_difference.jpg')

    #affiche_colormap_etude_general(Matrix_volume_difference_relative,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\nMatrix_volume_difference en %','PuOr',-100,100)
    #plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_volume_difference_relative.jpg')

    #affiche_colormap_etude_general(Matrix_volume_ratio,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\nMatrix_volume_ratio','Greens',np.nanmin(Matrix_volume_ratio),np.nanmax(Matrix_volume_ratio))
    #plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_volume_ratio.jpg')

    #affiche_colormap_etude_general(Matrix_diametre_difference,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\n Matrix_diametre_difference','autumn',np.nanmin(Matrix_diametre_difference),np.nanmax(Matrix_diametre_difference))
    #plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_diametre_difference.jpg')

    #affiche_colormap_etude_general(Matrix_diametre_difference_relative,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\n Matrix_diametre_difference_relative','cool',np.nanmin(Matrix_diametre_difference_relative),np.nanmax(Matrix_diametre_difference_relative))
    #plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_diametre_difference_relative.jpg')

# mise sous forme de vecteur des volumes et diamètres pour fiter     

    vecteur_volume_instrument_1 = np.zeros(96)
    vecteur_volume_instrument_2 = np.zeros(96)
    vecteur_ratio = np.zeros(96)
    vecteur_diametre_instrument_1 = np.zeros(96)
    vecteur_diametre_instrument_2 = np.zeros(96)

    # initialisation du masque à tous les puits = true
    mask_volumes_proches = vecteur_ratio <1 
    mask_volumes_eloignes = vecteur_ratio>1
    mask_nan =  vecteur_ratio>1

    j_letter = 0
    while j_letter<number_of_letters_max:
        j_col = 0
        while j_col<number_of_colonne_number_max:
            index_inside_vector = int(12*(j_letter)+(j_col))
            vecteur_volume_instrument_1[index_inside_vector] = np.copy(volume_instrument_1[j_letter,j_col]) 
            vecteur_volume_instrument_2[index_inside_vector] = np.copy(volume_instrument_2[j_letter,j_col]) 
            vecteur_ratio[index_inside_vector] = np.copy(Matrix_volume_difference_relative[j_letter,j_col])
            vecteur_diametre_instrument_1[index_inside_vector] = np.copy(diametre_instrument_1[j_letter,j_col]) 
            vecteur_diametre_instrument_2[index_inside_vector] = np.copy(diametre_instrument_2[j_letter,j_col]) 
            j_col += 1
        j_letter += 1

# filtre très grossier pour ne pas prendre les outliers dans le calcul du fit    
    tolerance = 20    
    j_pos = 0
    while j_pos<96:
        if np.abs(vecteur_ratio[j_pos])>tolerance:
            mask_volumes_proches[j_pos] = False
            mask_volumes_eloignes[j_pos] = True
        if np.isnan(vecteur_ratio[j_pos]):
            mask_volumes_proches[j_pos] = False
            mask_volumes_eloignes[j_pos] = True
            mask_nan[j_pos] = True
        j_pos +=1

#    nb de puits utiles pour le fit
    nb_puits_trop_loins = np.sum(mask_volumes_eloignes) - np.sum(mask_nan)
    # To keep
    plt.close(10)
    plt.figure(10,figsize=(12,6))
    plt.suptitle(name_dossier_instrument_1+' volumes par puits '+type_intrument_2+' vs '+type_intrument_1 +'\n ')#\n'
    plt.plot(vecteur_volume_instrument_2[mask_volumes_proches],vecteur_volume_instrument_1[mask_volumes_proches],'o',color='blue',label='data utile au fit')
    plt.plot(vecteur_volume_instrument_2[mask_volumes_eloignes],vecteur_volume_instrument_1[mask_volumes_eloignes],'rx',label='outlier')
    plt.plot(np.arange(np.nanmin(vecteur_volume_instrument_2),np.nanmax(vecteur_volume_instrument_2)),np.arange(np.nanmin(vecteur_volume_instrument_2),np.nanmax(vecteur_volume_instrument_2)),label='bissectrice = target',color='k')
    plt.xlabel('V issu stat µm^3  '+type_intrument_2)
    plt.ylabel('V issu stat µm^3  '+type_intrument_1)
    plt.legend()
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+' volumes par puits.jpg')

    mask_volumes_eloignes_fit = vecteur_volume_instrument_2 >0 
#calcul du fit sur les volumes 
    if True in mask_volumes_proches:
        x_considere_fit_lin_inverse = vecteur_volume_instrument_2[mask_volumes_proches]
        y_considere_fit_lin_inverse = vecteur_volume_instrument_1[mask_volumes_proches]
        slope_fit_inverse, intercept_fit_inverse, r_value_fit_inverse, p_value_fit_inverse, std_err_fit_inverse = stats.linregress(x_considere_fit_lin_inverse,y_considere_fit_lin_inverse)
        representation_x = np.arange(np.nanmin(vecteur_volume_instrument_2),np.nanmax(vecteur_volume_instrument_2),(np.nanmax(vecteur_volume_instrument_2)-np.nanmin(vecteur_volume_instrument_2))/50)

        # To keep
        data_fit = slope_fit_inverse*vecteur_volume_instrument_2+intercept_fit_inverse
    # représentation graphique du fit    
        plt.close(15)
        plt.figure(15,figsize=(12,6))
        plt.suptitle(name_dossier_instrument_1+' FIT\nvolumes par puits '+type_intrument_1+' vs '+type_intrument_2 +'\n '+str(nb_puits_trop_loins)+' puits exclus pour le calcul du fit')#\n'
        plt.plot(vecteur_volume_instrument_2[mask_volumes_proches],vecteur_volume_instrument_1[mask_volumes_proches],'+',color='blue',label='data utile pour fit')
        plt.plot(vecteur_volume_instrument_2[mask_volumes_eloignes],vecteur_volume_instrument_1[mask_volumes_eloignes],'rx',label='data exclue pour fit')
        plt.plot(vecteur_volume_instrument_2,slope_fit_inverse*vecteur_volume_instrument_2+intercept_fit_inverse,color='#000080',linestyle = '-',label='slope='+str(round(slope_fit_inverse,2))+'\nord='+str(round(intercept_fit_inverse,2))+'\nR²'+str(round(r_value_fit_inverse,4)))
        plt.xlabel('V issu stat µm^3  '+type_intrument_2)
        plt.ylabel('V issu stat µm^3  '+type_intrument_1)
        plt.legend()    
        plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+' volumes par puits_FIT.jpg')
    else:
        slope_fit_inverse, intercept_fit_inverse, r_value_fit_inverse, p_value_fit_inverse, std_err_fit_inverse = stats.linregress(vecteur_volume_instrument_2,vecteur_volume_instrument_1)
        data_fit = slope_fit_inverse*vecteur_volume_instrument_2+intercept_fit_inverse
    # représentation graphique du fit    
        plt.close(15)
        plt.figure(15,figsize=(12,6))
        plt.suptitle(name_dossier_instrument_1+' FIT\nvolumes par puits '+type_intrument_1+' vs '+type_intrument_2 +'\n '+str(nb_puits_trop_loins)+' puits exclus pour le calcul du fit')#\n'
        plt.plot(vecteur_volume_instrument_2[mask_volumes_proches],vecteur_volume_instrument_1[mask_volumes_proches],'+',color='blue',label='data utile pour fit')
        plt.plot(vecteur_volume_instrument_2[mask_volumes_eloignes],vecteur_volume_instrument_1[mask_volumes_eloignes],'rx',label='data exclue pour fit')
        plt.plot(vecteur_volume_instrument_2,slope_fit_inverse*vecteur_volume_instrument_2+intercept_fit_inverse,color='#000080',linestyle = '-',label='slope='+str(round(slope_fit_inverse,2))+'\nord='+str(round(intercept_fit_inverse,2))+'\nR²'+str(round(r_value_fit_inverse,4)))
        plt.xlabel('V issu stat µm^3  '+type_intrument_2)
        plt.ylabel('V issu stat µm^3  '+type_intrument_1)
        plt.legend()    
        plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+' volumes par puits_FIT.jpg')
# calcul de l'écart data - fit et mask en fct du seuillage de l'écart tolérable
    j_pos = 0
    while j_pos<96:
        if vecteur_volume_instrument_1[j_pos] != 0:
            ecart_au_fit = 100 * np.abs(data_fit[j_pos] - vecteur_volume_instrument_1[j_pos])/vecteur_volume_instrument_1[j_pos]
        else:
            ecart_au_fit = 0     
        if ecart_au_fit>tolerance_relative_fit:
            mask_volumes_eloignes_fit[j_pos] = True
        else:
            mask_volumes_eloignes_fit[j_pos] = False
        j_pos +=1

# indicateur de la qualité des data vs fit       
    nb_puits_loin_fit = np.sum(mask_volumes_eloignes_fit)

#  figure avec représentation des points ok ko vis à vis du fit    
    plt.close(10)
    plt.figure(10,figsize=(12,6))
    plt.suptitle(name_dossier_instrument_1+' volumes par puits '+type_intrument_2+' vs '+type_intrument_1 +'\n nb puits loin du fit ='+str(nb_puits_loin_fit)+' tolerance ='+str(tolerance_relative_fit))#\n'
    plt.plot(vecteur_volume_instrument_2,vecteur_volume_instrument_1,'v',color='green',label='data proche fit')
    plt.plot(vecteur_volume_instrument_2[mask_volumes_eloignes_fit],vecteur_volume_instrument_1[mask_volumes_eloignes_fit],'rx',label='data loin fit')
    plt.plot(vecteur_volume_instrument_2,slope_fit_inverse*vecteur_volume_instrument_2+intercept_fit_inverse,color='k',linestyle = '-',label='slope='+str(round(slope_fit_inverse,2))+'\nord='+str(round(intercept_fit_inverse,2))+'\nR²'+str(round(r_value_fit_inverse,4)))
    plt.xlabel('V issu stat µm^3  '+type_intrument_2)
    plt.ylabel('V issu stat µm^3  '+type_intrument_1)
    plt.legend()
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+' volumes par puits_fit.jpg')

#    assemblage des figures de dotmaps et colormaps
    # merge_two_figure([directory_source_synthese_instrument_1,directory_source_synthese_instrument_2],name_dossier_instrument_1,['dot_map_730.png','dot_map_730.png'],directory_plaque_to_save)
    # merge_two_figure([directory_source_synthese_instrument_1,directory_source_synthese_instrument_2],name_dossier_instrument_1,['dot_map_contour_730.png','dot_map_contour_730.png'],directory_plaque_to_save)
    # merge_two_figure([directory_source_synthese_instrument_1,directory_source_synthese_instrument_2],name_dossier_instrument_1,['dot_map_cycle_730.png','dot_map_cycle_730.png'],directory_plaque_to_save)

#    regénération des colormaps volumes et diamètres
    #affiche_colormap_etude_general(volume_instrument_1,'volumes_'+type_intrument_1,'jet',0,500)
    # plt.savefig(directory_plaque_to_save+'\\volumes_'+type_intrument_1+'.jpg')

    #affiche_colormap_etude_general(volume_instrument_2,'volumes_'+type_intrument_2,'jet',0,500)
    # plt.savefig(directory_plaque_to_save+'\\volumes_'+type_intrument_2+'.jpg')

    #affiche_colormap_etude_general(diametre_instrument_1,'diametres_'+type_intrument_1,'jet',15,50)
    # plt.savefig(directory_plaque_to_save+'\\diametres_'+type_intrument_1+'.jpg')

    #affiche_colormap_etude_general(diametre_instrument_2,'diametres_'+type_intrument_2,'jet',15,50)
    # plt.savefig(directory_plaque_to_save+'\\diametres_'+type_intrument_2+'.jpg')

    # merge_two_figure([directory_plaque_to_save,directory_plaque_to_save],name_dossier_instrument_1,['diametres_'+type_intrument_1+'.jpg','diametres_'+type_intrument_2+'.jpg'],directory_plaque_to_save)
    # merge_two_figure([directory_plaque_to_save,directory_plaque_to_save],name_dossier_instrument_1,['volumes_'+type_intrument_1+'.jpg','volumes_'+type_intrument_2+'.jpg'],directory_plaque_to_save)

#    copier coller des dotmaps
    # copyfile(directory_source_synthese_instrument_1+'\\dot_map_730.png',directory_plaque_to_save+'\\dot_map_730_'+type_intrument_1+'.png')
    # copyfile(directory_source_synthese_instrument_2+'\\dot_map_730.png',directory_plaque_to_save+'\\dot_map_730_'+type_intrument_2+'.png')

    # copyfile(directory_source_synthese_instrument_1+'\\dot_map_contour_730.png',directory_plaque_to_save+'\\dot_map_contour_730'+type_intrument_1+'.png')
    # copyfile(directory_source_synthese_instrument_2+'\\dot_map_contour_730.png',directory_plaque_to_save+'\\dot_map_contour_730'+type_intrument_2+'.png')

    # copyfile(directory_source_synthese_instrument_1+'\\dot_map_cycle_730.png',directory_plaque_to_save+'\\dot_map_cycle_730'+type_intrument_1+'.png')
    # copyfile(directory_source_synthese_instrument_2+'\\dot_map_cycle_730.png',directory_plaque_to_save+'\\dot_map_cycle_730'+type_intrument_2+'.png')
#   calcul de moyenneset ecarts types des différences en volumes et diametres
    Matrix_volume_difference_relative_mean = np.nanmean(Matrix_volume_difference_relative)
    Matrix_volume_difference_relative_std = np.nanstd(Matrix_volume_difference_relative)    
    Matrix_volume_difference_relative_CV = np.copy(100*Matrix_volume_difference_relative_std/Matrix_volume_difference_relative_mean)
    Matrix_diametre_difference_relative_mean =np.nanmean(Matrix_diametre_difference_relative)
    Matrix_diametre_difference_relative_std =np.nanstd(Matrix_diametre_difference_relative)
    Matrix_diametre_difference_relative_CV = np.copy(100*Matrix_diametre_difference_relative_std/Matrix_diametre_difference_relative_mean)
#   fichier de sortie avec les KPI ( To keep)
    fichier_out = open(directory_plaque_to_save+'\\data_extraite_KPI_'+type_intrument_1+'_'+type_intrument_2+'.csv','w')
    fichier_out.write('name_plate;nb_puits_utiles_pour_fit;fit lineaire_x=;y=;slope;intercept;R²;nb_puits_loin_du_fit;tolerance vis a vis du fit;Matrix_volume_difference_relative_mean;Matrix_volume_difference_relative_CV;Matrix_diametre_difference_relative_mean;Matrix_diametre_difference_relative_CV;\n')
    fichier_out.write(name_dossier_to_save+';'+str(nb_puits_trop_loins)+';'+type_intrument_1+';'+type_intrument_2+';'+str(slope_fit_inverse)+';'+str(intercept_fit_inverse)+';'+str(r_value_fit_inverse)+';'+str(nb_puits_loin_fit)+';'+str(tolerance_relative_fit)+';'+str(Matrix_volume_difference_relative_mean)+';'+str(Matrix_volume_difference_relative_CV)+';'+str(Matrix_diametre_difference_relative_mean)+';'+str(Matrix_diametre_difference_relative_CV)+'\n')    
    fichier_out.close()

    return name_dossier_to_save, slope_fit_inverse, intercept_fit_inverse, r_value_fit_inverse, nb_puits_loin_fit, Matrix_volume_difference_relative_mean , Matrix_volume_difference_relative_CV , Matrix_diametre_difference_relative_mean , Matrix_diametre_difference_relative_CV , vecteur_volume_instrument_1, vecteur_volume_instrument_2

def comparaison_ZC_to_ref_v1_nanofilm(nom_gp,chemin_intrument_1,type_intrument_1,chemin_intrument_2,type_intrument_2,directory_racine_to_save,name_dossier_to_save,tolerance_relative_fit):    
# =============================================================================
#     le but de cette fonction est de comparer les data en volumes d'un lecteur à un autre
#    la 1ere appli est de confronter les data ZC 3 - 4 au proto (mais ça peut servir dans d'autres config ZC to ZC...)
        # =============================================================================
        #     # auteur : Hélène Louis, modifié le 19/02/2025 par Hubert Goddefroy
        #     # 05/04/22 : fonction développée dans le cadre de la validation métrologique des Zymocubes
        #     # nécessite le module home_made_tools_v3.py 
        # =============================================================================
    #  Chemin de données:
    #       il faut les données sorties de ZI pour les 2 lectures à comparer  
    #   Détails de l'action de la fonction
    #       -> dans les dossiers chemin_intrument_1 et chemin_intrument_2:
    #           Va chercher les sous dossiers Synthese
    #           Va lire les fichiers synthese_interferometric_data.csv issu de Zyminterne 
    #           Calcul les valeurs différences entre les métriques usuelles des plaques (volumes, diamètres, nb dot...)
    #           FIT sur les volumes (instrument 2 en x, instrument 1 en y) après un filtre pour exclure les outliers évidents (20% de tolerance en différence relative)
    #           Calcul du nombre de puits où le fit et les data sont trop loins : seuil = tolerance_relative_fit, sort l'indicateur nb_puits_loin_fit
    #       -> dans le dossier de sortie directory_racine_output création d'un dossier nommé comme name_dossier_to_save contenant:
    #                les colormaps:
    #                   Matrix_volume_difference.
    #                   Matrix_volume_difference_relative
    #                   Matrix_volume_ratio
    #                   Matrix_diametre_difference
    #                   Matrix_diametre_difference_relative  
    #               des figures doublées avec:
    #                   les dotmaps, les colormaps volumes , diametres, 
    #               des graphs 
    #                   les data
    #                   le fit 
    #               des csv
    #                   raw
    #                   kpi
    #       -> retourne les valeurs des indicateurs et les array intéressants
    #            name_dossier_to_save, slope_fit_inverse, intercept_fit_inverse, r_value_fit_inverse, nb_puits_loin_fit, vecteur_volume_instrument_1, vecteur_volume_instrument_2
    # =============================================================================
# =============================================================================
    number_of_letters_max = 8
    number_of_colonne_number_max = 12
    # =============================================================================
    # # import des données du instrument_1
    # =============================================================================
    directory_source_synthese_instrument_1 = chemin_intrument_1
    file_data_instrument_1 = directory_source_synthese_instrument_1+'\\synthese_interferometric_data.csv'

    # IMPORT DES DATA CONTENUES DANS LE CSV SYNTHESE 
    thickness_instrument_1, thickness_std_instrument_1, intensite_455_instrument_1, intensite_730_instrument_1, N_area_before_instrument_1, N_area_after_instrument_1, porcent_area_instrument_1 = import_data_from_csv_synthese_zymintern_nanofilm(file_data_instrument_1)
    #volume_instrument_1, volume_std_instrument_1, diametre_instrument_1, diametre_std_instrument_1, N_dot_detected_instrument_1, N_dot_keep_instrument_1, N_cycle_instrument_1, porcent_dot_keep_instrument_1 = import_data_from_csv_synthese(file_data_instrument_1)

    # =============================================================================
    # # import des données du instrument_2
    # =============================================================================
    directory_source_synthese_instrument_2 = chemin_intrument_2
    file_data_instrument_2 = directory_source_synthese_instrument_2+'\\synthese_interferometric_data.csv'

    # IMPORT DES DATA CONTENUES DANS LE CSV SYNTHESE 
    thickness_instrument_2, thickness_std_instrument_2, intensite_455_instrument_2, intensite_730_instrument_2, N_area_before_instrument_2, N_area_after_instrument_2, porcent_area_instrument_2 = import_data_from_csv_synthese_zymintern_nanofilm(file_data_instrument_2)
    # =============================================================================
    # endroit ou stocker la comparaison
    # =============================================================================

    directory_plaque_to_save = directory_racine_to_save + '\\'+name_dossier_to_save
    if os.path.exists(directory_plaque_to_save) == False:
        os.mkdir(directory_plaque_to_save)

    # =============================================================================
    # la comparaison
    # =============================================================================
    plt.close('all')   
    Matrix_thickness_difference = np.zeros((number_of_letters_max,number_of_colonne_number_max))    
    Matrix_thickness_difference_relative = np.zeros((number_of_letters_max,number_of_colonne_number_max))        
    Matrix_thickness_ratio = np.zeros((number_of_letters_max,number_of_colonne_number_max))    
    Matrix_intensite_455_difference = np.zeros((number_of_letters_max,number_of_colonne_number_max))    
    Matrix_intensite_455_difference_relative = np.zeros((number_of_letters_max,number_of_colonne_number_max))  
    Matrix_intensite_730_difference = np.zeros((number_of_letters_max,number_of_colonne_number_max))    
    Matrix_intensite_730_difference_relative = np.zeros((number_of_letters_max,number_of_colonne_number_max)) 

    Matrix_nb_pourcent_area_difference = np.zeros((number_of_letters_max,number_of_colonne_number_max))    

#    fichier de sortie des data raw ( to keep )
    fichier_save = open(directory_plaque_to_save+'\\data_comparative'+type_intrument_1+'_'+type_intrument_2+'.csv','w')
    fichier_save.write('weel;T_instrument_1;I_455_instrument_1;I_730_instrument_1;T_instrument_2;I_455_instrument_2;I_730_instrument_2;\n')

    # calcul des différences selon le schéma: 1 - 2 par défaut et 2 la référence pour les relatives
    j_letter = 0
    while j_letter<number_of_letters_max:
        j_col = 0
        while j_col<number_of_colonne_number_max:
            Matrix_thickness_difference[j_letter,j_col] = np.copy(thickness_instrument_1[j_letter,j_col] - thickness_instrument_2[j_letter,j_col])
#            prise en compte du cas patholoque ou on doit diviser par 0
            if thickness_instrument_2[j_letter,j_col] != 0:
                Matrix_thickness_difference_relative[j_letter,j_col] = np.copy((thickness_instrument_1[j_letter,j_col] - thickness_instrument_2[j_letter,j_col])/thickness_instrument_2[j_letter,j_col] *100)
                Matrix_thickness_ratio[j_letter,j_col] =np.copy(thickness_instrument_1[j_letter,j_col] / thickness_instrument_2[j_letter,j_col])
            else:
                Matrix_thickness_difference_relative[j_letter,j_col] = np.nan
                Matrix_thickness_ratio[j_letter,j_col] = np.nan

            Matrix_nb_pourcent_area_difference[j_letter,j_col] = np.copy(porcent_area_instrument_1[j_letter,j_col] - porcent_area_instrument_2[j_letter,j_col]) 
            fichier_save.write(alphabet_majuscule[j_letter]+str(j_col+1)+';'+str(thickness_instrument_1[j_letter,j_col])+';'+str(intensite_455_instrument_1[j_letter,j_col])+';'+str(intensite_730_instrument_1[j_letter,j_col])+';'+str(thickness_instrument_2[j_letter,j_col])+';'+str(intensite_455_instrument_2[j_letter,j_col])+';'+str(intensite_730_instrument_2[j_letter,j_col])+';\n')
            j_col += 1
        j_letter += 1
    fichier_save.close()

# présentation des différences calculées selon des colormaps    
    #affiche_colormap_etude_general(Matrix_thickness_difference,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\nMatrix_thickness_difference','RdGy',np.nanmin(Matrix_thickness_difference),np.nanmax(Matrix_thickness_difference))
    #plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_thickness_difference.jpg')

    #affiche_colormap_etude_general(Matrix_thickness_difference_relative,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\nMatrix_thickness_difference en %','PuOr',-100,100)
    #plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_thickness_difference_relative.jpg')

    #affiche_colormap_etude_general(Matrix_thickness_ratio,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\nMatrix_thickness_ratio','Greens',np.nanmin(Matrix_thickness_ratio),np.nanmax(Matrix_thickness_ratio))
    #plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_thicknesse_ratio.jpg')

# mise sous forme de vecteur des volumes et diamètres pour fiter     

    vecteur_thickness_instrument_1 = np.zeros(96)
    vecteur_thickness_instrument_2 = np.zeros(96)
    vecteur_ratio = np.zeros(96)

    # initialisation du masque à tous les puits = true
    mask_thickness_proches = vecteur_ratio <1 
    mask_thickness_eloignes = vecteur_ratio>1
    mask_nan =  vecteur_ratio>1

    j_letter = 0
    while j_letter<number_of_letters_max:
        j_col = 0
        while j_col<number_of_colonne_number_max:
            index_inside_vector = int(12*(j_letter)+(j_col))
            vecteur_thickness_instrument_1[index_inside_vector] = np.copy(thickness_instrument_1[j_letter,j_col]) 
            vecteur_thickness_instrument_2[index_inside_vector] = np.copy(thickness_instrument_2[j_letter,j_col]) 
            vecteur_ratio[index_inside_vector] = np.copy(Matrix_thickness_difference_relative[j_letter,j_col])
            j_col += 1
        j_letter += 1

# filtre très grossier pour ne pas prendre les outliers dans le calcul du fit    
    tolerance = 20    
    j_pos = 0
    while j_pos<96:
        if np.abs(vecteur_ratio[j_pos])>tolerance:
            mask_thickness_proches[j_pos] = False
            mask_thickness_eloignes[j_pos] = True
        if np.isnan(vecteur_ratio[j_pos]):
            mask_thickness_proches[j_pos] = False
            mask_thickness_eloignes[j_pos] = True
            mask_nan[j_pos] = True
        j_pos +=1

#    nb de puits utiles pour le fit
    nb_puits_trop_loins = np.sum(mask_thickness_eloignes) - np.sum(mask_nan)

    # le type instrument est le nom du dossier de la plaque ( c'est à dire le dernier dossier du chemin)
    name_dossier_instrument_1 = os.path.basename(os.path.normpath(chemin_intrument_1))

    plt.close(10)
    plt.figure(10,figsize=(12,6))
    plt.suptitle(type_intrument_1+' épaisseur par puits '+type_intrument_2+' vs '+type_intrument_1 +'\n ')#\n'
    plt.plot(vecteur_thickness_instrument_2[mask_thickness_proches],vecteur_thickness_instrument_1[mask_thickness_proches],'o',color='blue',label='data utile au fit')
    plt.plot(vecteur_thickness_instrument_2[mask_thickness_eloignes],vecteur_thickness_instrument_1[mask_thickness_eloignes],'rx',label='outlier')
    plt.plot(np.arange(np.nanmin(vecteur_thickness_instrument_2),np.nanmax(vecteur_thickness_instrument_2)),np.arange(np.nanmin(vecteur_thickness_instrument_2),np.nanmax(vecteur_thickness_instrument_2)),label='bissectrice = target',color='k')
    plt.xlabel('T issu stat nm  '+type_intrument_2)
    plt.ylabel('T issu stat nm  '+type_intrument_1)
    plt.legend()
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+' epaisseur par puits.jpg')

    mask_thickness_eloignes_fit = vecteur_thickness_instrument_2 >0 
#calcul du fit sur les volumes 
    if True in mask_thickness_proches:
        x_considere_fit_lin_inverse = vecteur_thickness_instrument_2[mask_thickness_proches]
        y_considere_fit_lin_inverse = vecteur_thickness_instrument_1[mask_thickness_proches]
        slope_fit_inverse, intercept_fit_inverse, r_value_fit_inverse, p_value_fit_inverse, std_err_fit_inverse = stats.linregress(x_considere_fit_lin_inverse,y_considere_fit_lin_inverse)
        representation_x = np.arange(np.nanmin(vecteur_thickness_instrument_2),np.nanmax(vecteur_thickness_instrument_2),(np.nanmax(vecteur_thickness_instrument_2)-np.nanmin(vecteur_thickness_instrument_2))/50)

        data_fit = slope_fit_inverse*vecteur_thickness_instrument_2+intercept_fit_inverse
    # représentation graphique du fit    
        plt.close(15)
        plt.figure(15,figsize=(12,6))
        plt.suptitle(name_dossier_instrument_1+' FIT\népaisseur par puits '+type_intrument_1+' vs '+type_intrument_2 +'\n '+str(nb_puits_trop_loins)+' puits exclus pour le calcul du fit')#\n'
        plt.plot(vecteur_thickness_instrument_2[mask_thickness_proches],vecteur_thickness_instrument_1[mask_thickness_proches],'+',color='blue',label='data utile pour fit')
        plt.plot(vecteur_thickness_instrument_2[mask_thickness_eloignes],vecteur_thickness_instrument_1[mask_thickness_eloignes],'rx',label='data exclue pour fit')
        plt.plot(vecteur_thickness_instrument_2,slope_fit_inverse*vecteur_thickness_instrument_2+intercept_fit_inverse,color='#000080',linestyle = '-',label='slope='+str(round(slope_fit_inverse,2))+'\nord='+str(round(intercept_fit_inverse,2))+'\nR²'+str(round(r_value_fit_inverse,4)))
        plt.xlabel('T issu stat µm^3  '+type_intrument_2)
        plt.ylabel('T issu stat µm^3  '+type_intrument_1)
        plt.legend()    
        plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+' epaisseur par puits_FIT.jpg')
    else:
        slope_fit_inverse, intercept_fit_inverse, r_value_fit_inverse, p_value_fit_inverse, std_err_fit_inverse = stats.linregress(vecteur_thickness_instrument_2,vecteur_thickness_instrument_1)
        data_fit = slope_fit_inverse*vecteur_thickness_instrument_2+intercept_fit_inverse
    # représentation graphique du fit    
        plt.close(15)
        plt.figure(15,figsize=(12,6))
        plt.suptitle(name_dossier_instrument_1+' FIT\népaisseur par puits '+type_intrument_1+' vs '+type_intrument_2 +'\n '+str(nb_puits_trop_loins)+' puits exclus pour le calcul du fit')#\n'
        plt.plot(vecteur_thickness_instrument_2[mask_thickness_proches],vecteur_thickness_instrument_1[mask_thickness_proches],'+',color='blue',label='data utile pour fit')
        plt.plot(vecteur_thickness_instrument_2[mask_thickness_eloignes],vecteur_thickness_instrument_1[mask_thickness_eloignes],'rx',label='data exclue pour fit')
        plt.plot(vecteur_thickness_instrument_2,slope_fit_inverse*vecteur_thickness_instrument_2+intercept_fit_inverse,color='#000080',linestyle = '-',label='slope='+str(round(slope_fit_inverse,2))+'\nord='+str(round(intercept_fit_inverse,2))+'\nR²'+str(round(r_value_fit_inverse,4)))
        plt.xlabel('T issu stat µm^3  '+type_intrument_2)
        plt.ylabel('T issu stat µm^3  '+type_intrument_1)
        plt.legend()    
        plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+' epaisseur par puits_FIT.jpg')
# calcul de l'écart data - fit et mask en fct du seuillage de l'écart tolérable
    j_pos = 0
    while j_pos<96:
        if vecteur_thickness_instrument_1[j_pos] != 0:
            ecart_au_fit = 100 * np.abs(data_fit[j_pos] - vecteur_thickness_instrument_1[j_pos])/vecteur_thickness_instrument_1[j_pos]
        else:
            ecart_au_fit = 0     
        if ecart_au_fit>tolerance_relative_fit:
            mask_thickness_eloignes_fit[j_pos] = True
        else:
            mask_thickness_eloignes_fit[j_pos] = False
        j_pos +=1

# indicateur de la qualité des data vs fit       
    nb_puits_loin_fit = np.sum(mask_thickness_eloignes_fit)

#  figure avec représentation des points ok ko vis à vis du fit    
    plt.close(10)
    plt.figure(10,figsize=(12,6))
    plt.suptitle(name_dossier_instrument_1+' épaisseur par puits '+type_intrument_2+' vs '+type_intrument_1 +'\n nb puits loin du fit ='+str(nb_puits_loin_fit)+' tolerance ='+str(tolerance_relative_fit))#\n'
    plt.plot(vecteur_thickness_instrument_2,vecteur_thickness_instrument_1,'v',color='green',label='data proche fit')
    plt.plot(vecteur_thickness_instrument_2[mask_thickness_eloignes_fit],vecteur_thickness_instrument_1[mask_thickness_eloignes_fit],'rx',label='data loin fit')
    plt.plot(vecteur_thickness_instrument_2,slope_fit_inverse*vecteur_thickness_instrument_2+intercept_fit_inverse,color='k',linestyle = '-',label='slope='+str(round(slope_fit_inverse,2))+'\nord='+str(round(intercept_fit_inverse,2))+'\nR²'+str(round(r_value_fit_inverse,4)))
    plt.xlabel('T issu stat µm^3  '+type_intrument_2)
    plt.ylabel('T issu stat µm^3  '+type_intrument_1)
    plt.legend()
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+' epaisseur par puits_fit.jpg')

#    assemblage des figures de dotmaps et colormaps
    # merge_two_figure([directory_source_synthese_instrument_1,directory_source_synthese_instrument_2],name_dossier_instrument_1,['stat_litteral_thicknesses_colormap.png','stat_litteral_thicknesses_colormap.png'],directory_plaque_to_save)
    # merge_two_figure([directory_source_synthese_instrument_1,directory_source_synthese_instrument_2],name_dossier_instrument_1,['stat_litteral_intensity_455_colormap.png','stat_litteral_intensity_455_colormap.png'],directory_plaque_to_save)
    # merge_two_figure([directory_source_synthese_instrument_1,directory_source_synthese_instrument_2],name_dossier_instrument_1,['stat_litteral_intensity_730_colormap.png','stat_litteral_intensity_730_colormap.png'],directory_plaque_to_save)

#    regénération des colormaps volumes et diamètres
    #affiche_colormap_etude_general(thickness_instrument_1,'épaisseur_'+type_intrument_1,'jet',0,200)
    # plt.savefig(directory_plaque_to_save+'\\epaisseur_'+type_intrument_1+'.jpg')

    #affiche_colormap_etude_general(thickness_instrument_2,'épaisseur_'+type_intrument_2,'jet',0,200)
    # plt.savefig(directory_plaque_to_save+'\\epaisseur_'+type_intrument_2+'.jpg')

    # merge_two_figure([directory_plaque_to_save,directory_plaque_to_save],name_dossier_instrument_1,['epaisseur_'+type_intrument_1+'.jpg','epaisseur_'+type_intrument_2+'.jpg'],directory_plaque_to_save)

#    copier coller des dotmaps
    # copyfile(directory_source_synthese_instrument_1+'\\stat_litteral_thicknesses_colormap.png',directory_plaque_to_save+'\\thicknesses_'+type_intrument_1+'.png')
    # copyfile(directory_source_synthese_instrument_2+'\\stat_litteral_thicknesses_colormap.png',directory_plaque_to_save+'\\thicknesses_'+type_intrument_2+'.png')

    # copyfile(directory_source_synthese_instrument_1+'\\stat_litteral_intensity_455_colormap.png',directory_plaque_to_save+'\\intensity_455'+type_intrument_1+'.png')
    # copyfile(directory_source_synthese_instrument_2+'\\stat_litteral_intensity_455_colormap.png',directory_plaque_to_save+'\\intensity_455'+type_intrument_2+'.png')

    # copyfile(directory_source_synthese_instrument_1+'\\stat_litteral_intensity_730_colormap.png',directory_plaque_to_save+'\\intensity_730'+type_intrument_1+'.png')
    # copyfile(directory_source_synthese_instrument_2+'\\stat_litteral_intensity_730_colormap.png',directory_plaque_to_save+'\\intensity_730'+type_intrument_2+'.png')
#   calcul de moyenneset ecarts types des différences en volumes et diametres
    Matrix_thickness_difference_relative_mean = np.nanmean(Matrix_thickness_difference_relative)
    Matrix_thickness_difference_relative_std = np.nanstd(Matrix_thickness_difference_relative)    
    Matrix_thickness_difference_relative_CV = np.copy(100*Matrix_thickness_difference_relative_std/Matrix_thickness_difference_relative_mean)

#   fichier de sortie avec les KPI 
    fichier_out = open(directory_plaque_to_save+'\\data_extraite_KPI_'+type_intrument_1+'_'+type_intrument_2+'.csv','w')
    fichier_out.write('name_plate;nb_puits_utiles_pour_fit;fit lineaire_x=;y=;slope;intercept;R²;nb_puits_loin_du_fit;tolerance vis a vis du fit;Matrix_thickness_difference_relative_mean;Matrix_thickness_difference_relative_CV;\n')
    fichier_out.write(name_dossier_to_save+';'+str(nb_puits_trop_loins)+';'+type_intrument_1+';'+type_intrument_2+';'+str(slope_fit_inverse)+';'+str(intercept_fit_inverse)+';'+str(r_value_fit_inverse)+';'+str(nb_puits_loin_fit)+';'+str(tolerance_relative_fit)+';'+str(Matrix_thickness_difference_relative_mean)+';'+str(Matrix_thickness_difference_relative_CV)+'\n')    
    fichier_out.close()

    return name_dossier_to_save, slope_fit_inverse, intercept_fit_inverse, r_value_fit_inverse, nb_puits_loin_fit, Matrix_thickness_difference_relative_mean , Matrix_thickness_difference_relative_CV , vecteur_thickness_instrument_1, vecteur_thickness_instrument_2


def compare_enzymo_2_ref(directory_source_instrument_1,type_instrument_1,acquisition_name_instrument_1,onglet,directory_source_instrument_2,type_instrument_2,acquisition_name_instrument_2,directory_to_save):        

    # =============================================================================
    ''' BUT '''
    # le but de cette fonction est de comparer les données enzymologiques entre deux acquisitions :
    # une acquisition avec la machine de référence (type_instrument_1) et l'autre acquisition avec 
    # la machine à valider (type_instrument_2).
    # =============================================================================
    #     # autheur : Hubert Goddefroy
    #     # 06/04/22 : fonction développée dans le cadre de la validation métrologique des Zymocubes
    #     # nécessite le module home_made_tools_v2.py 
    # =============================================================================
    #
    ''' ENTREES '''
    # directory_source_instrument_1 : pointe vers le dossier contenant toutes les
    # acquisitions de la machine de référence.
    #
    # type_instrument_1 : machine de référence à laquelle sera comparée la machine 
    # en cours de validation.
    #
    # acquisition_name_instrument_1 : nom du sous-dossier dans le dossier directory_source_instrument_1
    # correspondant à l'acquisition, à la machine de référence, à comparer, sous dossier
    # dans lequel se trouve le fichier WellResults.
    #
    # directory_source_instrument_2 : pointe vers le dossier contenant toutes les
    # acquisitions de la machine à valider. Les sous-dossiers correspondent chacun à
    # une acquisition.
    #
    # type_instrument_2 : machine à valider.
    #
    # acquisition_name_instrument_2 : nom du sous-dossier dans le dossier directory_source_instrument_2
    # correspondant à l'acquisition, à la machine à valider, à comparer, sous dossier
    # dans lequel se trouve le fichier WellResults.
    #
    # directory_to_save : dossier où seront sauvegardés tous les résultats de comparaison.
    # organisé en sous-dossier par acquisition à la machine 2 (à valider).
    #
    ''' SORTIES '''
    # enregistre dans le répertoire directory_to_save les figures de comparaison du taux 
    # de dégradation de la machine 2 en fonction de la machine 1
    #
    # Dans un CSV, consigne tous les indicateurs enzymo dans un tableau :
    # LOD, LOQ, sensibilité, CV sur les réplicas sur les % de dégradation, à 30, 50 et 70 %
    # de dégradation, activité mesurée de l'échantillon et RSD de l'échantillon mesuré.
    # Puis la différence relative de toutes ces grandeurs en prenant comme référence la machine 1.
    # Il crée un fichier csv par acquisition.
    #
    ''' RETURN '''
    # retourne 2 listes :
    # liste concernant l'acquisition à la machine de référence (instrument 1) :
    #
    # 'Nom de l Acquisitions;Machine; zone ; LOD;LOQ;Sensibilite (en U/mL);CV % deg a 30%;
    # CV % deg a 50%;CV % deg a 70%; diff % Activite Ech_1 (U/mL);diff % RSD Ech_2
    # (%)(autant de fois qu'il y a d'échantillons différents déclarés dans le plan de plaque);
    #
    # liste concernant l'acquisition à la machine à valider (instrument 2) ET 
    # les données comparatives entre les deux acquisitions (référence et validation):
    #
    # 'Nom de l Acquisitions;Machine;LOD;LOQ;Sensibilite (en U/mL);CV % deg a 30%;
    # CV % deg a 50%;CV % deg a 70%;diff % Activite Ech_1 (U/mL);diff % RSD Ech_2 
    # (%)(autant de fois qu'il y a d'échantillons différents déclarés dans le plan de plaque);
    # diff % LOD;diff % LOQ;diff % Sensibilite (en U/mL);diff % CV % deg a 30%;
    # diff % CV % deg a 50%;diff % CV % deg a 70%; diff % Activite Ech_1 (U/mL);
    # diff % RSD Ech_1 (%) (autant de fois qu'il y a d'échantillons différents 
    # déclarés dans le plan de plaque);
    #
    ''' ARCHITECTURE DE DONNEES '''
    # dossier contenant les acquisitions à la machine 1, référence :
            # dossier de l'acquisition :
                  # dossier Images :
                          # Synthèse
                  # well_results.csv
                  # acquisition_details.csv
    # Idem pour instument 2.

    # print('\n\n\nacquisition_name_instrument_2 : \n\n',acquisition_name_instrument_2)
    # print('\n\nonglet : \n\n',onglet)



    # =============================================================================

    #######################################################################
    #################    INSTRUMENT 1 : Référence    ######################
    #######################################################################

    # Chemin pointant vers le fichier Well_Results.xlsx de la machine de référence :
    # Vérifier si le chemin contient déjà le dossier 'Images'
    if os.path.basename(acquisition_name_instrument_1) == 'Images':
        chemin_well_result_reference = os.path.join(directory_source_instrument_1, acquisition_name_instrument_1, 'WellResults.xlsx')
    else:
        chemin_well_result_reference = os.path.join(directory_source_instrument_1, acquisition_name_instrument_1, 'WellResults.xlsx')
    # chemin_well_result_reference = 'G:\\Mon Drive\\support interne\\debugg_routine_valid\\ref\\GPAxHA230130-06\\WellResults.csv'
    # chemin_well_result_reference = 'G:\\Mon Drive\\support interne\\debugg_routine_valid\\valid\\GPAxHA230130-06_01\\WellResults.csv'
    # with open(chemin_well_result_reference) as WellResultsReference:
    #     file_read = csv.reader(WellResultsReference)
    #     results_Reference = list(file_read)
    # WellResultsReference.close()    

    df = pandas.read_excel(chemin_well_result_reference,sheet_name=onglet)
    results_Reference = df.values.tolist()

    if results_Reference[-1] == [] or results_Reference[-1] == [';;;;;;;;;'] or results_Reference[-1] == [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]:
        print(results_Reference[-1])
        results_Reference.pop()

    if results_Reference[0][0] == 'Plate Reference': # le premier onglet à un paragraphe de plus que les suivants (qui comporte les info date, heure, référence plaque, ce qui correspond à l'en-tête)
        start_stop = []
        j_1 = 0
        while len(start_stop) < 7 and j_1 < len(results_Reference):
            # On cherche les lignes vides ou les lignes qui contiennent uniquement des séparateurs
            if results_Reference[j_1] == []  or results_Reference[j_1] == [';;;;;;;;;'] or results_Reference[j_1] == [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]:
                start_stop.append(j_1)
            j_1 += 1

        ## Extraction des information du CSV WellResults de l'acquisition de référence :
            # Entete_Reference contient la date, l'heure, le nom de la palque, les paramères de fit a, b et R²
            # Blank_Reference contient les ZU des puits tampons et les exclusions des tampons
            # Gamme_Reference contient les ZU et les activités théoriques des points de gamme et leurs exclusions
            # Sample_Reference contient les activité non diluées des échantillons et leur RSD
            # SampleDetail_Reference contient les ZU et activité mesurée de tous les points échantillons et leurs exclusions

        Entete_Reference = []
        Blank_Reference = []
        Gamme_Reference = []
        Sample_Reference = []
        SampleDetail_Reference = []

        # for k in range(start_stop[0]-3):
        #     Entete_Reference.append(results_Reference[k+3])
        # for k in range(start_stop[1] - start_stop[0] - 3):
        #     Blank_Reference.append(results_Reference[k+start_stop[0]+3])
        # for k in range(start_stop[2] - start_stop[1] - 3):
        #     Gamme_Reference.append(results_Reference[k+start_stop[1]+3])
        # for k in range(start_stop[3] - start_stop[2] - 3):
        #     Sample_Reference.append(results_Reference[k+start_stop[2]+3])
        # for k in range(len(results_Reference) - start_stop[3] - 3):
        #     SampleDetail_Reference.append(results_Reference[k+start_stop[3]+3])

        for k in range(start_stop[1]-3):
            Entete_Reference.append(results_Reference[k+3])
        for k in range(start_stop[2] - start_stop[1] - 3):
            Blank_Reference.append(results_Reference[k+start_stop[1]+3])
        for k in range(start_stop[4] - start_stop[3] - 3):
            Gamme_Reference.append(results_Reference[k+start_stop[3]+3])
        for k in range(start_stop[5] - start_stop[4] - 3):
            Sample_Reference.append(results_Reference[k+start_stop[4]+3])
        for k in range(len(results_Reference) - start_stop[6] - 3):
            SampleDetail_Reference.append(results_Reference[k+start_stop[6]+3])
    else:
        start_stop = []
        j_1 = 0
        while len(start_stop) < 6 and j_1 < len(results_Reference):

            # On cherche les lignes vides ou les lignes qui contiennent uniquement des séparateurs
            if results_Reference[j_1] == []  or results_Reference[j_1] == [';;;;;;;;;'] or results_Reference[j_1] == [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]:
                start_stop.append(j_1)
            j_1 += 1

        ## Extraction des information du CSV WellResults de l'acquisition de référence :
            # Entete_Reference contient la date, l'heure, le nom de la palque, les paramères de fit a, b et R²
            # Blank_Reference contient les ZU des puits tampons et les exclusions des tampons
            # Gamme_Reference contient les ZU et les activités théoriques des points de gamme et leurs exclusions
            # Sample_Reference contient les activité non diluées des échantillons et leur RSD
            # SampleDetail_Reference contient les ZU et activité mesurée de tous les points échantillons et leurs exclusions

        Entete_Reference = []
        Blank_Reference = []
        Gamme_Reference = []
        Sample_Reference = []
        SampleDetail_Reference = []

        # for k in range(start_stop[0]-3):
        #     Entete_Reference.append(results_Reference[k+3])
        # for k in range(start_stop[1] - start_stop[0] - 3):
        #     Blank_Reference.append(results_Reference[k+start_stop[0]+3])
        # for k in range(start_stop[2] - start_stop[1] - 3):
        #     Gamme_Reference.append(results_Reference[k+start_stop[1]+3])
        # for k in range(start_stop[3] - start_stop[2] - 3):
        #     Sample_Reference.append(results_Reference[k+start_stop[2]+3])
        # for k in range(len(results_Reference) - start_stop[3] - 3):
        #     SampleDetail_Reference.append(results_Reference[k+start_stop[3]+3])

        for k in range(start_stop[0]):
            Entete_Reference.append(results_Reference[k])
        for k in range(start_stop[1] - start_stop[0] - 3):
            Blank_Reference.append(results_Reference[k+start_stop[0]+3])
        for k in range(start_stop[3] - start_stop[2] - 3):
            Gamme_Reference.append(results_Reference[k+start_stop[2]+3])
        for k in range(start_stop[4] - start_stop[3] - 3):
            Sample_Reference.append(results_Reference[k+start_stop[3]+3])
        for k in range(len(results_Reference) - start_stop[5] - 3):
            SampleDetail_Reference.append(results_Reference[k+start_stop[5]+3])

    ## Ces listes sont des tableaux 1D, chaque ligne n'est pas encore séparée

    Entete_R = []
    Blank_R = []
    Gamme_R = []
    Sample_R = []
    SampleDetail_R = []

    # for k in range(len(Entete_Reference)):
    #     Entete_R.append(re.split(';',Entete_Reference[k][0]))
    # for k in range(len(Blank_Reference)):
    #     Blank_R.append(re.split(';',Blank_Reference[k][0]))
    # for k in range(len(Gamme_Reference)):
    #     Gamme_R.append(re.split(';',Gamme_Reference[k][0]))
    # for k in range(len(Sample_Reference)):
    #     Sample_R.append(re.split(';',Sample_Reference[k][0]))
    # for k in range(len(SampleDetail_Reference)):
    #     SampleDetail_R.append(re.split(';',SampleDetail_Reference[k][0]))

    Entete_R = Entete_Reference
    Blank_R = Blank_Reference
    Gamme_R = Gamme_Reference
    Sample_R = Sample_Reference
    SampleDetail_R = SampleDetail_Reference

    # print('En-tête R : \n',Entete_R)
    # print('Blank R : \n',Blank_R)
    # print('Gamme_R : \n',Gamme_R)
    # print('Sample_R : \n',Sample_R)
    # print('SampleDetail_R : \n',SampleDetail_R)

    ## les listes sont maintenant des tableaux 2D dont chaque ligne a été divisée en autant
    ## de colonne qu'il y avait de ";" 
    ## Chaque élément du tableau 2D est un string

    ## Calcul de LOD LOQ pour la machine de référence
    ## Je ne calcule la moyenne et l'écart-type que sur les positions tampon qui ne 
    ## sont pas exclues.

    deg_tampon_moyen_R = 0
    ecartype_deg_tampon = 0
    nb_position_tampon = 0
    for k in range(len(Blank_R)):
        if Blank_R[k][3] == 'False':
            if Blank_R[k][2] != np.nan:
                deg_tampon_moyen_R += float(Blank_R[k][2])
                nb_position_tampon += 1
    deg_tampon_moyen_R = deg_tampon_moyen_R/nb_position_tampon
    for k in range(len(Blank_R)):
        if Blank_R[k][3] == 'False':
            if Blank_R[k][2] != '':
                ecartype_deg_tampon += (float(Blank_R[k][2]) - deg_tampon_moyen_R)**2
    ecartype_deg_tampon = sqrt(ecartype_deg_tampon/nb_position_tampon)

    lod_R = deg_tampon_moyen_R + 3*ecartype_deg_tampon
    loq_R = deg_tampon_moyen_R + 10*ecartype_deg_tampon

    ## Calcul de Sensibilité pour la machine de référence. Le calcul se fait à partir
    # des paramètres de fit avec un rétro-calcul.
    # le calcul de la sensibilité/activité à 50% de dégradation et des CV à 30, 50 et 70% de 
    # dégradation dépendent directement du type de fit.
    # Non seulement le rétro calcul mais également le nombre de paramètres et donc la taille de l'en-tête
    if Entete_R[1][1] == 'Linear':
        alpha = float(Entete_R[2][1])
        beta = float(Entete_R[3][1])

        if alpha != 0:
            sensibilite_R = (50-beta)/alpha
        else:
            sensibilite_R = np.nan

        ## Calcul pour la machine de référence des CV en % de dégradation à 30%, 50% 
        # et 70% de dégradation

        activites_deg = [[0,0],[0,0],[0,0]]

        if alpha != 0:
            activites_deg[0][0] = (30-beta)/alpha
        else:
            activites_deg[0][0] = np.nan
        activites_deg[1][0] = sensibilite_R
        if alpha != 0:
            activites_deg[2][0] = (70-beta)/alpha
        else:
            activites_deg[2][0] = np.nan
    elif Entete_R[1][1] == 'Exponential plateau 1':
        alpha = float(Entete_R[2][1])
        beta = float(Entete_R[3][1])

        if 1-50/alpha > 0:
            sensibilite_R = -log(1-50/alpha)/beta
        else:
            sensibilite_R = np.nan

        ## Calcul pour la machine de référence des CV en % de dégradation à 30%, 50% 
        # et 70% de dégradation

        activites_deg = [[0,0],[0,0],[0,0]]

        if 1-30/alpha > 0:
            activites_deg[0][0] = -log(1-30/alpha)/beta
        else:
            activites_deg[0][0] = np.nan
        activites_deg[1][0] = sensibilite_R
        if 1-70/alpha > 0:
            activites_deg[2][0] = -log(1-70/alpha)/beta
        else:
            activites_deg[2][0] = np.nan
    elif Entete_R[1][1] == 'Exponential plateau 2':
        alpha = float(Entete_R[2][1])
        beta = float(Entete_R[3][1])
        gamma = float(Entete_R[4][1])

        if 1-(50-gamma)/alpha > 0:
            sensibilite_R = -log(1-(50-gamma)/alpha)/beta
        else:
            sensibilite_R = np.nan

        ## Calcul pour la machine de référence des CV en % de dégradation à 30%, 50% 
        # et 70% de dégradation

        activites_deg = [[0,0],[0,0],[0,0]]

        if 1-(30-gamma)/alpha > 0:
            activites_deg[0][0] = -log(1-(30-gamma)/alpha)/beta
        else:
            activites_deg[0][0] = np.nan
        activites_deg[1][0] = sensibilite_R
        if 1-(70-gamma)/alpha > 0:
            activites_deg[2][0] = -log(1-(70-gamma)/alpha)/beta
        else:
            activites_deg[2][0] = np.nan
    elif Entete_R[1][1] == 'Logistic 1':
        alpha = float(Entete_R[2][1])
        beta = float(Entete_R[3][1])

        if alpha - 50 != 0:
            sensibilite_R = (50*beta)/(alpha-50)
        else:
            sensibilite_R = np.nan

        ## Calcul pour la machine de référence des CV en % de dégradation à 30%, 50% 
        # et 70% de dégradation

        activites_deg = [[0,0],[0,0],[0,0]]

        if alpha - 30 != 0:
            activites_deg[0][0] = (30*beta)/(alpha-30)
        else:
            activites_deg[0][0] = np.nan
        activites_deg[1][0] = sensibilite_R
        if alpha - 70 != 0:
            activites_deg[2][0] = (70*beta)/(alpha-70)
        else:
            activites_deg[2][0] = np.nan
    elif Entete_R[1][1] == 'Logistic 2':
        alpha = float(Entete_R[2][1])
        beta = float(Entete_R[3][1])
        gamma = float(Entete_R[4][1])

        if alpha - 50 != 0:
            sensibilite_R = (50-gamma)*beta/(alpha-50)
        else:
            sensibilite_R = np.nan

        ## Calcul pour la machine de référence des CV en % de dégradation à 30%, 50% 
        # et 70% de dégradation

        activites_deg = [[0,0],[0,0],[0,0]]

        if alpha - 30 != 0:
            activites_deg[0][0] = (30-gamma)*beta/(alpha-30)
        else:
            activites_deg[0][0] = np.nan
        activites_deg[1][0] = sensibilite_R
        if alpha - 70 != 0:
            activites_deg[2][0] = (70-gamma)*beta/(alpha-70)
        else:
            activites_deg[2][0] = np.nan
    elif Entete_R[1][1] == 'Logistic 3':
        alpha = float(Entete_R[2][1])
        beta = float(Entete_R[3][1])
        gamma = float(Entete_R[4][1])
        delta = float(Entete_R[5][1])

        if alpha - 50 != 0:
            sensibilite_R = ((50-gamma)*(beta**delta)/(alpha-50))**(1/delta)
        else:
            sensibilite_R = np.nan

        ## Calcul pour la machine de référence des CV en % de dégradation à 30%, 50% 
        # et 70% de dégradation

        activites_deg = [[0,0],[0,0],[0,0]]

        if alpha - 30 != 0:
            activites_deg[0][0] = ((30-gamma)*(beta**delta)/(alpha-30))**(1/delta)
        else:
            activites_deg[0][0] = np.nan
        activites_deg[1][0] = sensibilite_R
        if alpha - 70 != 0:
            activites_deg[2][0] = ((70-gamma)*(beta**delta)/(alpha-70))**(1/delta)
        else:
            activites_deg[2][0] = np.nan


    # Pour les trois % de dégradation d'intérêt (30, 50 et 70) on cherche la valeur
    # théorique de dilution qui se rapporche le plus de la valeur calculée comme étant celle
    # qui donnera respectivement 30, 50 ou 70% de dégradation des dots.
    # On recherche les positions les plus proches seulement pour la machine de référence,
    # pour la machine à valider, on reprendra les mêmes puits trouvés à cette étape.
    for k in range(len(activites_deg)):
        find_min = 1000
        indice_min = 0
        for l in range(len(Gamme_R)):
            if Gamme_R[l][3] != '':
                if abs(float(Gamme_R[l][3]) - activites_deg[k][0]) < find_min:
                    find_min = abs(float(Gamme_R[l][3])-activites_deg[k][0])
                    indice_min = l
        activites_deg[k][1] = float(Gamme_R[indice_min][3])

    deg_30 = []
    positions_30 = []
    deg_50 = []
    positions_50 = []
    deg_70 = []
    positions_70 = []
    for k in range(len(Gamme_R)):
        if Gamme_R[k][4] == 'False':  # le puit n'est pas exclu
            if float(Gamme_R[k][3]) == activites_deg[0][1]:
                positions_30.append(Gamme_R[k][0])
                if Gamme_R[k][2] == '':
                    deg_30.append(np.nan)
                else:
                    deg_30.append(float(Gamme_R[k][2]))
            if float(Gamme_R[k][3]) == activites_deg[1][1]:
                positions_50.append(Gamme_R[k][0])
                if Gamme_R[k][2] == '':
                    deg_50.append(np.nan)
                else:
                    deg_50.append(float(Gamme_R[k][2]))
            if float(Gamme_R[k][3]) == activites_deg[2][1]:
                positions_70.append(Gamme_R[k][0])
                if Gamme_R[k][2] == '':
                    deg_70.append(np.nan)
                else:
                    deg_70.append(float(Gamme_R[k][2]))

    moyenne_deg_30 = 0
    moyenne_deg_50 = 0
    moyenne_deg_70 = 0
    ecartype_deg_30 = 0
    ecartype_deg_50 = 0
    ecartype_deg_70 = 0
    kompt = 0
    for k in range(len(deg_30)):
        if not isnan(deg_30[k]):
            moyenne_deg_30 += deg_30[k]
            kompt += 1
    if kompt == 0:
        moyenne_deg_30 = np.nan
    else:
        moyenne_deg_30 = moyenne_deg_30/kompt
    kompt = 0
    for k in range(len(deg_50)):
        if not isnan(deg_50[k]):
            moyenne_deg_50 += deg_50[k]
            kompt += 1
    if kompt == 0:
        moyenne_deg_50 = np.nan
    else:
        moyenne_deg_50 = moyenne_deg_50/kompt
    kompt = 0    
    for k in range(len(deg_70)):
        if not isnan(deg_70[k]):
            moyenne_deg_70 += deg_70[k]
            kompt += 1
    if kompt == 0:
        moyenne_deg_70 = np.nan
    else:
        moyenne_deg_70 = moyenne_deg_70/kompt

    kompt = 0
    for k in range(len(deg_30)):
        if not isnan(deg_30[k]):
            ecartype_deg_30 += (deg_30[k] - moyenne_deg_30)**2
            kompt += 1
    if kompt == 0:
        ecartype_deg_30 = np.nan
    else:
        ecartype_deg_30 = sqrt(ecartype_deg_30/kompt)
    kompt = 0
    for k in range(len(deg_50)):
        if not isnan(deg_50[k]):
            ecartype_deg_50 += (deg_50[k] - moyenne_deg_50)**2
            kompt += 1
    if kompt == 0:
        ecartype_deg_50 = np.nan
    else:
        ecartype_deg_50 = sqrt(ecartype_deg_50/kompt)
    kompt = 0
    for k in range(len(deg_70)):
        if not isnan(deg_70[k]):
            ecartype_deg_70 += (deg_70[k] - moyenne_deg_70)**2
            kompt += 1
    if kompt == 0:
        ecartype_deg_70 = np.nan
    else:
        ecartype_deg_70 = sqrt(ecartype_deg_70/kompt)

    # cv_357_R contient les Cv  30 50 et 70 % de dégradation
    cv_357_R = [ecartype_deg_30*100/moyenne_deg_30,ecartype_deg_50*100/moyenne_deg_50,ecartype_deg_70*100/moyenne_deg_70]

    #######################################################################
    #############     INSTRUMENT 2 : MACHINE A VALIDER     ################
    #######################################################################

    # Vérifier si le chemin contient déjà le dossier 'Images'
    if os.path.basename(acquisition_name_instrument_2) == 'Images':
        chemin_well_result_validation = os.path.join(directory_source_instrument_2, acquisition_name_instrument_2, 'WellResults.xlsx')
    else:
        chemin_well_result_validation = os.path.join(directory_source_instrument_2, acquisition_name_instrument_2, 'WellResults.xlsx')
    # chemin_well_result_validation = 'G:\\Mon Drive\\support interne\\debugg_routine_valid\\valid\\GPAxHA230130-06_01\\WellResults.csv'
    # with open(chemin_well_result_validation) as WellResultsValidation:
    #     file_read = csv.reader(WellResultsValidation)
    #     results_Validation = list(file_read)
    # WellResultsValidation.close()

    df = pandas.read_excel(chemin_well_result_validation,sheet_name=onglet)
    results_Validation = df.values.tolist()

    if results_Validation[-1] == [] or results_Validation[-1] == [';;;;;;;;;'] or results_Validation[-1] == [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]:
        results_Validation.pop()

    '''
    start_stop = []
    j_1 = 0
    while len(start_stop) < 4 and j_1 < len(results_Validation):
        if results_Validation[j_1] == []:
            start_stop.append(j_1)
        j_1 += 1
    '''

    # print('\n\n\nresultReference à vérifier :\n\n',results_Validation)


    if results_Validation[0][0] == 'Plate Reference': #le premier onglet à un paragraphe de plus que les suivants (qui comporte les info date, heure, référence plaque, ce qui correspond à l'en-tête)
        start_stop = []
        j_1 = 0
        while len(start_stop) < 7 and j_1 < len(results_Validation):
            if results_Validation[j_1] == [] or results_Validation[j_1] == [';;;;;;;;;'] or results_Validation[j_1] == [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]:
                start_stop.append(j_1)
            j_1 += 1

        ## Extraction des information du CSV WellResults

        Entete_Validation = []
        Blank_Validation = []
        Gamme_Validation = []
        Sample_Validation = []
        SampleDetail_Validation = []
        '''
        for k in range(start_stop[0]):
            Entete_Validation.append(results_Validation[k])
        for k in range(start_stop[1] - start_stop[0] - 3):
            Blank_Validation.append(results_Validation[k+start_stop[0]+3])
        for k in range(start_stop[2] - start_stop[1] - 3):
            Gamme_Validation.append(results_Validation[k+start_stop[1]+3])
        for k in range(start_stop[3] - start_stop[2] - 3):
            Sample_Validation.append(results_Validation[k+start_stop[2]+3])
        for k in range(len(results_Validation) - start_stop[3] - 3):
            SampleDetail_Validation.append(results_Validation[k+start_stop[3]+3])
        '''   
        for k in range(start_stop[1]-3):
            Entete_Validation.append(results_Validation[k+3])
        for k in range(start_stop[2] - start_stop[1] - 3):
            Blank_Validation.append(results_Validation[k+start_stop[1]+3])
        for k in range(start_stop[4] - start_stop[3] - 3):
            Gamme_Validation.append(results_Validation[k+start_stop[3]+3])
        for k in range(start_stop[5] - start_stop[4] - 3):
            Sample_Validation.append(results_Validation[k+start_stop[4]+3])
    #    for k in range(len(results_Validation) - start_stop[4] - 3):
        for k in range(len(results_Validation) - start_stop[6] - 4):
            SampleDetail_Validation.append(results_Validation[k+start_stop[6]+3])
    else:
        start_stop = []
        j_1 = 0
        while len(start_stop) < 6 and j_1 < len(results_Validation):
            if results_Validation[j_1] == [] or results_Validation[j_1] == [';;;;;;;;;'] or results_Validation[j_1] == [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]:
                start_stop.append(j_1)
            j_1 += 1

        ## Extraction des information du CSV WellResults

        Entete_Validation = []
        Blank_Validation = []
        Gamme_Validation = []
        Sample_Validation = []
        SampleDetail_Validation = []
        '''
        for k in range(start_stop[0]):
            Entete_Validation.append(results_Validation[k])
        for k in range(start_stop[1] - start_stop[0] - 3):
            Blank_Validation.append(results_Validation[k+start_stop[0]+3])
        for k in range(start_stop[2] - start_stop[1] - 3):
            Gamme_Validation.append(results_Validation[k+start_stop[1]+3])
        for k in range(start_stop[3] - start_stop[2] - 3):
            Sample_Validation.append(results_Validation[k+start_stop[2]+3])
        for k in range(len(results_Validation) - start_stop[3] - 3):
            SampleDetail_Validation.append(results_Validation[k+start_stop[3]+3])
        '''   
        for k in range(start_stop[0]):
            Entete_Validation.append(results_Validation[k])
        for k in range(start_stop[1] - start_stop[0] - 3):
            Blank_Validation.append(results_Validation[k+start_stop[0]+3])
        for k in range(start_stop[3] - start_stop[2] - 3):
            Gamme_Validation.append(results_Validation[k+start_stop[2]+3])
        for k in range(start_stop[4] - start_stop[3] - 3):
            Sample_Validation.append(results_Validation[k+start_stop[3]+3])
    #    for k in range(len(results_Validation) - start_stop[4] - 3):
        for k in range(len(results_Validation) - start_stop[5] - 4):
            SampleDetail_Validation.append(results_Validation[k+start_stop[5]+3])

    Entete_V = []
    Blank_V = []
    Gamme_V = []
    Sample_V = []
    SampleDetail_V = []

    # for k in range(len(Entete_Validation)):
    #     #Entete_V.append(re.split(';',Entete_Validation[k][0]))
    #     if Entete_Validation[k] == []:
    #         Entete_V.append(Entete_Validation[k])
    #     else:
    #         Entete_V.append(re.split(';',Entete_Validation[k][0]))
    # for k in range(len(Blank_Validation)):
    #     Blank_V.append(re.split(';',Blank_Validation[k][0]))
    # for k in range(len(Gamme_Validation)):
    #     Gamme_V.append(re.split(';',Gamme_Validation[k][0]))
    # for k in range(len(Sample_Validation)):
    #     Sample_V.append(re.split(';',Sample_Validation[k][0]))
    # for k in range(len(SampleDetail_Validation)):
    #     SampleDetail_V.append(re.split(';',SampleDetail_Validation[k][0]))

    Entete_V = Entete_Validation
    Blank_V = Blank_Validation
    Gamme_V = Gamme_Validation
    Sample_V = Sample_Validation
    SampleDetail_V = SampleDetail_Validation

    # print('En-tête V : \n',Entete_V)
    # print('Blank V : \n',Blank_V)
    # print('Gamme_V : \n',Gamme_V)
    # print('Sample_V : \n',Sample_V)
    # print('SampleDetail_V : \n',SampleDetail_V)

    ## LOD LOQ

    deg_tampon_moyen_V = 0
    ecartype_deg_tampon = 0
    nb_position_tampon = 0
    for k in range(len(Blank_V)):
        if Blank_V[k][3] == 'False':
            if Blank_V[k][2] != '':
                deg_tampon_moyen_V += float(Blank_V[k][2])
                nb_position_tampon += 1
    deg_tampon_moyen_V = deg_tampon_moyen_V/nb_position_tampon
    for k in range(len(Blank_V)):
        if Blank_V[k][3] == 'False':
            if Blank_V[k][2] != '':
                ecartype_deg_tampon += (float(Blank_V[k][2]) - deg_tampon_moyen_V)**2
    ecartype_deg_tampon = sqrt(ecartype_deg_tampon/nb_position_tampon)

    lod_V = deg_tampon_moyen_V + 3*ecartype_deg_tampon
    loq_V = deg_tampon_moyen_V + 10*ecartype_deg_tampon

    # le calcul de la sensibilité/activité à 50% de dégradation et des CV à 30, 50 et 70% de dégradation dépendent directement du type de fit : 


    ## Sensibilité

    # print('\n\n\nentete_V à vérifier : \n\n',Entete_V)

    if Entete_V[1][1] == 'Linear':
        alpha = float(Entete_V[2][1])
        beta = float(Entete_V[3][1])

        if alpha != 0:
            sensibilite_V = (50-beta)/alpha
        else:
            sensibilite_V = np.nan

    elif Entete_V[1][1] == 'Exponential plateau 1':
        alpha = float(Entete_V[2][1])
        beta = float(Entete_V[3][1])

        if 1-50/alpha > 0:
            sensibilite_V = -log(1-50/alpha)/beta
        else:
            sensibilite_V = np.nan

    elif Entete_V[1][1] == 'Exponential plateau 2':
        alpha = float(Entete_V[2][1])
        beta = float(Entete_V[3][1])
        gamma = float(Entete_V[4][1])

        if 1-(50-gamma)/alpha > 0:
            sensibilite_V = -log(1-(50-gamma)/alpha)/beta
        else:
            sensibilite_V = np.nan

    elif Entete_V[1][1] == 'Logistic 1':
        alpha = float(Entete_V[2][1])
        beta = float(Entete_V[3][1])

        if alpha - 50 != 0:
            sensibilite_V = (50*beta)/(alpha-50)
        else:
            sensibilite_V = np.nan

    elif Entete_V[1][1] == 'Logistic 2':
        alpha = float(Entete_V[2][1])
        beta = float(Entete_V[3][1])
        gamma = float(Entete_V[4][1])

        if alpha - 50 != 0:
            sensibilite_V = (50-gamma)*beta/(alpha-50)
        else:
            sensibilite_V = np.nan

    elif Entete_V[1][1] == 'Logistic 3':
        alpha = float(Entete_V[2][1])
        beta = float(Entete_V[3][1])
        gamma = float(Entete_V[4][1])
        delta = float(Entete_V[5][1])

        if alpha - 50 != 0:
            sensibilite_V = ((50-gamma)*(beta**delta)/(alpha-50))**(1/delta)
        else:
            sensibilite_V = np.nan

    ## CV en % de dégradation à 30%, 50% et 70% de dégradation

    deg_30 = []
    deg_50 = []
    deg_70 = []
    for k in range(len(Gamme_V)):
        if Gamme_V[k][0] in positions_30 and Gamme_V[k][4] == 'False':
            if Gamme_V[k][2] == '':
                deg_30.append(np.nan)
            else:
                deg_30.append(float(Gamme_V[k][2]))
        if Gamme_V[k][0] in positions_50 and Gamme_V[k][4] == 'False':
            if Gamme_V[k][2] == '':
                deg_50.append(np.nan)
            else:
                deg_50.append(float(Gamme_V[k][2]))
        if Gamme_V[k][0] in positions_70 and Gamme_V[k][4] == 'False':
            if Gamme_V[k][2] == '':
                deg_70.append(np.nan)
            else:
                deg_70.append(float(Gamme_V[k][2]))


    moyenne_deg_30 = 0
    moyenne_deg_50 = 0
    moyenne_deg_70 = 0
    ecartype_deg_30 = 0
    ecartype_deg_50 = 0
    ecartype_deg_70 = 0
    kompt = 0
    for k in range(len(deg_30)):
        if not isnan(deg_30[k]):
            moyenne_deg_30 += deg_30[k]
            kompt += 1
    if kompt == 0:
        moyenne_deg_30 = np.nan
    else:
        moyenne_deg_30 = moyenne_deg_30/kompt
    kompt = 0
    for k in range(len(deg_50)):
        if not isnan(deg_50[k]):
            moyenne_deg_50 += deg_50[k]
            kompt += 1
    if kompt == 0:
        moyenne_deg_50 = np.nan
    else:
        moyenne_deg_50 = moyenne_deg_50/kompt
    kompt = 0    
    for k in range(len(deg_70)):
        if not isnan(deg_70[k]):
            moyenne_deg_70 += deg_70[k]
            kompt += 1
    if kompt == 0:
        moyenne_deg_70 = np.nan
    else:
        moyenne_deg_70 = moyenne_deg_70/kompt

    kompt = 0
    for k in range(len(deg_30)):
        if not isnan(deg_30[k]):
            ecartype_deg_30 += (deg_30[k] - moyenne_deg_30)**2
            kompt += 1
    if kompt == 0:
        ecartype_deg_30 = np.nan
    else:
        ecartype_deg_30 = sqrt(ecartype_deg_30/kompt)
    kompt = 0
    for k in range(len(deg_50)):
        if not isnan(deg_50[k]):
            ecartype_deg_50 += (deg_50[k] - moyenne_deg_50)**2
            kompt += 1
    if kompt == 0:
        ecartype_deg_50 = np.nan
    else:
        ecartype_deg_50 = sqrt(ecartype_deg_50/kompt)
    kompt = 0
    for k in range(len(deg_70)):
        if not isnan(deg_70[k]):
            ecartype_deg_70 += (deg_70[k] - moyenne_deg_70)**2
            kompt += 1
    if kompt == 0:
        ecartype_deg_70 = np.nan
    else:
        ecartype_deg_70 = sqrt(ecartype_deg_70/kompt)

    cv_357_V = [ecartype_deg_30*100/moyenne_deg_30,ecartype_deg_50*100/moyenne_deg_50,ecartype_deg_70*100/moyenne_deg_70]

    ## Graphique % de dégradation de l'Instrument 2 (à valider) en fonction de l'instrument 1 : notre référence.

    deg_REF = []
    deg_VALID = []
    for k in range(len(Gamme_R)):
        if (Gamme_R[k][4] == 'False' and Gamme_V[k][4] == 'False') and (Gamme_R[k][0] == Gamme_V[k][0]):
            deg_REF.append(float(Gamme_R[k][2]))
            deg_VALID.append(float(Gamme_V[k][2]))


    # To keep
    if len(deg_REF) > 0:

        # print('\n\n\ndeg_REF : \n\n',deg_REF)
        # print('\n\n\ndeg_VALID : \n\n',deg_VALID)

        plt.close('all')
        plt.figure(figsize=(8, 6))
        # plt.close(26)
        # plt.clf()
        # fig26 = plt.figure(26)
        plt.suptitle('Comparaison des taux de dégradation\npour les gammes au ' + type_instrument_1 + ' et au ' + type_instrument_2 + '\n' + acquisition_name_instrument_2 + ' ' + onglet)
        plt.plot(deg_REF,deg_VALID,'o',color='blue')
        plt.plot(np.arange(np.nanmin(deg_REF),np.nanmax(deg_REF)),np.arange(np.nanmin(deg_REF),np.nanmax(deg_REF)),label='bissectrice = target',color='k')
        plt.xlabel('% de dégradation au ' + type_instrument_1)
        plt.ylabel('% de dégradation au ' + type_instrument_2)
        plt.legend()
        plt.savefig(directory_to_save + '\\' + acquisition_name_instrument_2 + '_' + onglet + '_taux_degradation')
        # plt.close(26)
        plt.close()

        ## tout ce qui est noté P dans la suite est équivalent à R (R pour référence
        ## et avant le Proto était la référence)
        ## Tout ce qui est noté Z dans la suite est équivalent à V(Z pour ZC qui était 
        ## la machine à Valider)
        ##
        ## ici je trace le graphique des deux gammes des machines de référence et à valider

        ecart = 0.1 # obligé de mettre une tolérance pour les tests d'égalité en activité enzymatique car on peut avoir 22,009 et 22,094 pour un même point de gamme
        abscisses_P = []
        for k in range(len(Gamme_R)):
            indic = 0
            if Gamme_R[k][3] != '':
                for j in range(len(abscisses_P)):
                    if (abscisses_P[j] - ecart < float(Gamme_R[k][3])) and  (float(Gamme_R[k][3]) < abscisses_P[j] + ecart):
                        indic = 1
                if indic == 0:
                    abscisses_P.append(float(Gamme_R[k][3]))

        gamme_moyenne_P = []
        for k in range(len(abscisses_P)):
            gamme_moyenne_P.append([abscisses_P[k]])
        for k in range(len(Gamme_R)):
            if Gamme_R[k][3] != '':
                for j in range(len(gamme_moyenne_P)):
                    if (gamme_moyenne_P[j][0] - ecart < float(Gamme_R[k][3]) < gamme_moyenne_P[j][0] + ecart) and Gamme_R[k][4] == 'False':
                        gamme_moyenne_P[j].append(float(Gamme_R[k][2]))
        for k in range(len(gamme_moyenne_P)):
            if len(gamme_moyenne_P[k]) > 1:
                gamme_moyenne_P[k].append(sum(gamme_moyenne_P[k][1:])/(len(gamme_moyenne_P[k])-1))
                gamme_moyenne_P[k].append(statistics.pstdev(gamme_moyenne_P[k][1:-1]))

        gamme_moyenne_Z = []
        for k in range(len(abscisses_P)):
            gamme_moyenne_Z.append([abscisses_P[k]])
        for k in range(len(Gamme_V)):
            for j in range(len(gamme_moyenne_Z)):
                if Gamme_V[k][3] != '': # nouveau
                    if float(Gamme_V[k][3]) == gamme_moyenne_Z[j][0] and Gamme_V[k][4] == 'False':
                        gamme_moyenne_Z[j].append(float(Gamme_V[k][2]))
        for k in range(len(gamme_moyenne_Z)):
            if len(gamme_moyenne_Z[k]) > 1:
                gamme_moyenne_Z[k].append(sum(gamme_moyenne_Z[k][1:])/(len(gamme_moyenne_Z[k])-1))
                gamme_moyenne_Z[k].append(statistics.pstdev(gamme_moyenne_Z[k][1:-1]))

        for k in range(len(gamme_moyenne_P)):
            if len(gamme_moyenne_P[k]) == 1:
                gamme_moyenne_P[k].append(0)
                gamme_moyenne_P[k].append(0)
            if len(gamme_moyenne_Z[k]) == 1:
                gamme_moyenne_Z[k].append(0)
                gamme_moyenne_Z[k].append(0)

        mask = []
        for k in range(len(gamme_moyenne_P)):
            if len(gamme_moyenne_P[k]) == 1 and len(gamme_moyenne_Z[k]) == 1:
                mask.append(k)

        Abscisses_Gamme = []
        Y_Gamme_P = []
        Y_Gamme_Z = []
        Y_Error_P = []
        Y_Error_Z = []

        for k in range(len(abscisses_P)):
            if k not in mask:
                Abscisses_Gamme.append(abscisses_P[k])
                Y_Gamme_P.append(gamme_moyenne_P[k][-2])
                Y_Gamme_Z.append(gamme_moyenne_Z[k][-2])
                Y_Error_P.append(gamme_moyenne_P[k][-1])
                Y_Error_Z.append(gamme_moyenne_P[k][-1])

        # plt.close('all')
        plt.close(27)
        fig27 = plt.figure(27)
        plt.title('Gammes comparées de ' + type_instrument_1 + ', la référence et de\n' + type_instrument_2 + ', la machine à valider\n' + acquisition_name_instrument_2 + ' ' + onglet)

        # print('\n\n\nY_Gamme_P : \n\n',Y_Gamme_P)
        # print('\n\n\nY_Gamme_Z : \n\n',Y_Gamme_Z)

        plt.plot(Abscisses_Gamme,Y_Gamme_P,'o',color = 'red', label = type_instrument_1)        
        plt.errorbar(Abscisses_Gamme,Y_Gamme_P,yerr = Y_Error_P,fmt = 'none', capsize = 6, ecolor = 'red', zorder = 1)
        plt.plot(Abscisses_Gamme,Y_Gamme_Z,'o',color = 'blue', label = type_instrument_2)        
        plt.errorbar(Abscisses_Gamme,Y_Gamme_Z,yerr = Y_Error_Z,fmt = 'none', capsize = 6, ecolor = 'blue', zorder = 1)

        plt.xlabel('Activité des points de gamme (U/mL)')
        plt.ylabel('Z.U.')
        plt.legend()

        plt.savefig(directory_to_save + '\\' + acquisition_name_instrument_2 + '_' + onglet + '_Gammes')
        plt.close(27)

    data_R = [acquisition_name_instrument_1,type_instrument_1,onglet,lod_R,loq_R,sensibilite_R,cv_357_R[0],cv_357_R[1],cv_357_R[2]]
    for k in range(len(Sample_R)):
        data_R.append(float(Sample_R[k][2]))
        data_R.append(float(Sample_R[k][4]))
    data_V = [acquisition_name_instrument_2,type_instrument_2,onglet,lod_V,loq_V,sensibilite_V,cv_357_V[0],cv_357_V[1],cv_357_V[2]]
    for k in range(len(Sample_V)):
        data_V.append(float(Sample_V[k][2]))
        data_V.append(float(Sample_V[k][4]))
    nexto = []
    if lod_R != 0:
        nexto.append((lod_V-lod_R)*100/lod_R)
    else:
        nexto.append(np.nan)
    if loq_R != 0:
        nexto.append((loq_V-loq_R)*100/loq_R)
    else:
        nexto.append(np.nan)
    nexto.append((sensibilite_V-sensibilite_R)*100/sensibilite_R)
    if cv_357_R[0] != 0:
        nexto.append((cv_357_V[0]-cv_357_R[0])*100/cv_357_R[0])
    else:
        nexto.append(np.nan)
    if cv_357_R[1] != 0:
        nexto.append((cv_357_V[1]-cv_357_R[1])*100/cv_357_R[1])
    else:
        nexto.append(np.nan)
    if cv_357_R[2] != 0:
        nexto.append((cv_357_V[2]-cv_357_R[2])*100/cv_357_R[2])
    else:
        nexto.append(np.nan)

    for k in range(2*len(Sample_V)):
        if data_R[8+k] != 0:
            nexto.append((data_V[8+k]-data_R[8+k])*100/data_R[8+k])
        else:
            nexto.append(np.nan)
    data_V = data_V + nexto

    return data_R, data_V
