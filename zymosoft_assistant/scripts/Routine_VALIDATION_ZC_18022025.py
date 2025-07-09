# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 14:05:24 2022

@author: helene
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
        dossier_reconstruction =  dossier_now+ '\\'  + nom_reconstruction+ '\\Synthese'
        file = dossier_reconstruction + '\\synthese_interferometric_data.csv'
#        lecture de synthese_interferometric_data.csv issu de Zyminterne
        volume_now, volume_std_now, diametre_now, diametre_std_now, N_dot_detected_now, N_dot_keep_now, N_cycle_now, porcent_dot_keep_now =  import_data_from_csv_synthese_zymintern(file)
#        copie des dotmaps pour un suivi  de l'allure des dots
        copyfile(dossier_reconstruction+'\\dot_map_730.png',directory_out_this_plate+'\\dot_map_730_'+liste_dossier_plaque[j_iteration]+'.png')
        copyfile(dossier_reconstruction+'\\dot_map_contour_730.png',directory_out_this_plate+'\\dot_map_contour_730'+liste_dossier_plaque[j_iteration]+'.png')
        copyfile(dossier_reconstruction+'\\dot_map_cycle_730.png',directory_out_this_plate+'\\dot_map_cycle_730'+liste_dossier_plaque[j_iteration]+'.png')

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

    affiche_colormap_etude_general_v2(volume_mean_for_this_plate,nom_plaque+'volume_mean_for_this_plate on all iteration','jet',0,500)
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'volume_mean_for_this_plate.jpg')

    affiche_colormap_etude_general_v2(volume_std_for_this_plate,nom_plaque+'volume_std_for_this_plate on all iteration','jet',0,0)
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'volume_std_for_this_plate.jpg')

    affiche_colormap_etude_general_v2(volume_CV_for_this_plate,nom_plaque+'volume_CV_for_this_plate on all iteration','Reds',0,10)
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'volume_CV_for_this_plate.jpg')

    affiche_colormap_etude_general_v2(volume_std_mean_for_this_plate,nom_plaque+'volume_std_mean_for_this_plate on all iteration','jet',0,0)
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'volume_std_mean_for_this_plate.jpg')

    affiche_colormap_etude_general_v2(nb_dot_detecte_mean_for_this_plate,nom_plaque+'nb_dot_detecte_mean_for_this_plate on all iteration','jet',0,0)
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'nb_dot_detecte_mean_for_this_plate.jpg')

    affiche_colormap_etude_general_v2(nb_dot_detecte_std_for_this_plate,nom_plaque+'nb_dot_detecte_std_for_this_plate on all iteration','jet',0,0)
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'nb_dot_detecte_std_for_this_plate.jpg')

    affiche_colormap_etude_general_v2(porcent_dot_utile_mean_for_this_plate,nom_plaque+'porcent_dot_utile_mean_for_this_plate on all iteration','jet',0,0)
    plt.savefig(directory_out_this_plate+'\\'+nom_plaque+'porcent_dot_utile_mean_for_this_plate.jpg')


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
        dossier_reconstruction =  dossier_now+ '\\'  + nom_reconstruction+ '\\Synthese'
        file = dossier_reconstruction + '\\synthese_interferometric_data.csv'
#        lecture de synthese_interferometric_data.csv issu de Zyminterne
        thickness_now, thickness_std_now, intensite_455_now, intensite_730_now, N_area_before_now, N_area_after_now, porcent_area_now =  import_data_from_csv_synthese_zymintern_nanofilm(file)
#        copie des dotmaps pour un suivi  de l'allure des dots
        copyfile(dossier_reconstruction+'\\intensity_455_map.png',directory_out_this_plate+'\\intensity_455_'+liste_dossier_plaque[j_iteration]+'.png')
        copyfile(dossier_reconstruction+'\\intensity_730_map.png',directory_out_this_plate+'\\intensity_730_'+liste_dossier_plaque[j_iteration]+'.png')
        copyfile(dossier_reconstruction+'\\stat_litteral_intensity_455_colormap.png',directory_out_this_plate+'\\intensity_455_colormap'+liste_dossier_plaque[j_iteration]+'.png')
        copyfile(dossier_reconstruction+'\\stat_litteral_intensity_730_colormap.png',directory_out_this_plate+'\\intensity_730_colormap'+liste_dossier_plaque[j_iteration]+'.png')
        copyfile(dossier_reconstruction+'\\stat_litteral_thicknesses_colormap.png',directory_out_this_plate+'\\thicknesses'+liste_dossier_plaque[j_iteration]+'.png')

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

# ajoute commentire

#mdif
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
    affiche_colormap_etude_general(Matrix_volume_difference,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\nMatrix_volume_difference','RdGy',np.nanmin(Matrix_volume_difference),np.nanmax(Matrix_volume_difference))
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_volume_difference.jpg')

    affiche_colormap_etude_general(Matrix_volume_difference_relative,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\nMatrix_volume_difference en %','PuOr',-100,100)
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_volume_difference_relative.jpg')

    affiche_colormap_etude_general(Matrix_volume_ratio,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\nMatrix_volume_ratio','Greens',np.nanmin(Matrix_volume_ratio),np.nanmax(Matrix_volume_ratio))
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_volume_ratio.jpg')

    affiche_colormap_etude_general(Matrix_diametre_difference,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\n Matrix_diametre_difference','autumn',np.nanmin(Matrix_diametre_difference),np.nanmax(Matrix_diametre_difference))
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_diametre_difference.jpg')

    affiche_colormap_etude_general(Matrix_diametre_difference_relative,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\n Matrix_diametre_difference_relative','cool',np.nanmin(Matrix_diametre_difference_relative),np.nanmax(Matrix_diametre_difference_relative))
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_diametre_difference_relative.jpg')

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

    plt.close(10)
    plt.figure(10,figsize=(12,6))
    plt.suptitle(name_dossier_instrument_1+' volumes par puits '+type_intrument_2+' vs '+type_intrument_1 +'\n ')#\n'
    plt.plot(vecteur_volume_instrument_2[mask_volumes_proches],vecteur_volume_instrument_1[mask_volumes_proches],'o',color='blue',label='data utile au fit')
    plt.plot(vecteur_volume_instrument_2[mask_volumes_eloignes],vecteur_volume_instrument_1[mask_volumes_eloignes],'rx',label='outlier')
    plt.plot(np.arange(np.nanmin(vecteur_volume_instrument_2),np.nanmax(vecteur_volume_instrument_2)),np.arange(np.nanmin(vecteur_volume_instrument_2),np.nanmax(vecteur_volume_instrument_2)),label='bissectrice = target',color='k')
    plt.xlabel('V issu stat µm^3  '+type_intrument_2)
    plt.ylabel('V issu stat µm^3  '+type_intrument_1)
    plt.legend()
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'volumes par puits.jpg')

    mask_volumes_eloignes_fit = vecteur_volume_instrument_2 >0 
#calcul du fit sur les volumes 
    if True in mask_volumes_proches:
        x_considere_fit_lin_inverse = vecteur_volume_instrument_2[mask_volumes_proches]
        y_considere_fit_lin_inverse = vecteur_volume_instrument_1[mask_volumes_proches]
        slope_fit_inverse, intercept_fit_inverse, r_value_fit_inverse, p_value_fit_inverse, std_err_fit_inverse = stats.linregress(x_considere_fit_lin_inverse,y_considere_fit_lin_inverse)
        representation_x = np.arange(np.nanmin(vecteur_volume_instrument_2),np.nanmax(vecteur_volume_instrument_2),(np.nanmax(vecteur_volume_instrument_2)-np.nanmin(vecteur_volume_instrument_2))/50)

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
        plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'volumes par puits_FIT.jpg')
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
        plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'volumes par puits_FIT.jpg')
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
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'volumes par puits_fit.jpg')

#    assemblage des figures de dotmaps et colormaps
    # merge_two_figure([directory_source_synthese_instrument_1,directory_source_synthese_instrument_2],name_dossier_instrument_1,['dot_map_730.png','dot_map_730.png'],directory_plaque_to_save)
    # merge_two_figure([directory_source_synthese_instrument_1,directory_source_synthese_instrument_2],name_dossier_instrument_1,['dot_map_contour_730.png','dot_map_contour_730.png'],directory_plaque_to_save)
    # merge_two_figure([directory_source_synthese_instrument_1,directory_source_synthese_instrument_2],name_dossier_instrument_1,['dot_map_cycle_730.png','dot_map_cycle_730.png'],directory_plaque_to_save)

#    regénération des colormaps volumes et diamètres
    affiche_colormap_etude_general(volume_instrument_1,'volumes_'+type_intrument_1,'jet',0,500)
    plt.savefig(directory_plaque_to_save+'\\volumes_'+type_intrument_1+'.jpg')

    affiche_colormap_etude_general(volume_instrument_2,'volumes_'+type_intrument_2,'jet',0,500)
    plt.savefig(directory_plaque_to_save+'\\volumes_'+type_intrument_2+'.jpg')

    affiche_colormap_etude_general(diametre_instrument_1,'diametres_'+type_intrument_1,'jet',15,50)
    plt.savefig(directory_plaque_to_save+'\\diametres_'+type_intrument_1+'.jpg')

    affiche_colormap_etude_general(diametre_instrument_2,'diametres_'+type_intrument_2,'jet',15,50)
    plt.savefig(directory_plaque_to_save+'\\diametres_'+type_intrument_2+'.jpg')

    merge_two_figure([directory_plaque_to_save,directory_plaque_to_save],name_dossier_instrument_1,['diametres_'+type_intrument_1+'.jpg','diametres_'+type_intrument_2+'.jpg'],directory_plaque_to_save)
    merge_two_figure([directory_plaque_to_save,directory_plaque_to_save],name_dossier_instrument_1,['volumes_'+type_intrument_1+'.jpg','volumes_'+type_intrument_2+'.jpg'],directory_plaque_to_save)

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
#   fichier de sortie avec les KPI 
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
    directory_source_synthese_instrument_1 = chemin_intrument_1+'\\Synthese'
    file_data_instrument_1 = directory_source_synthese_instrument_1+'\\synthese_interferometric_data.csv'

    # IMPORT DES DATA CONTENUES DANS LE CSV SYNTHESE 
    thickness_instrument_1, thickness_std_instrument_1, intensite_455_instrument_1, intensite_730_instrument_1, N_area_before_instrument_1, N_area_after_instrument_1, porcent_area_instrument_1 = import_data_from_csv_synthese_zymintern_nanofilm(file_data_instrument_1)
    #volume_instrument_1, volume_std_instrument_1, diametre_instrument_1, diametre_std_instrument_1, N_dot_detected_instrument_1, N_dot_keep_instrument_1, N_cycle_instrument_1, porcent_dot_keep_instrument_1 = import_data_from_csv_synthese(file_data_instrument_1)

    # =============================================================================
    # # import des données du instrument_2
    # =============================================================================
    directory_source_synthese_instrument_2 = chemin_intrument_2+'\\Synthese'
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

#    fichier de sortie des data raw
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
    affiche_colormap_etude_general(Matrix_thickness_difference,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\nMatrix_thickness_difference','RdGy',np.nanmin(Matrix_thickness_difference),np.nanmax(Matrix_thickness_difference))
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_thickness_difference.jpg')

    affiche_colormap_etude_general(Matrix_thickness_difference_relative,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\nMatrix_thickness_difference en %','PuOr',-100,100)
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_thickness_difference_relative.jpg')

    affiche_colormap_etude_general(Matrix_thickness_ratio,name_dossier_instrument_1+'\n'+type_intrument_1+' vs '+type_intrument_2+'\nMatrix_thickness_ratio','Greens',np.nanmin(Matrix_thickness_ratio),np.nanmax(Matrix_thickness_ratio))
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'Matrix_thicknesse_ratio.jpg')

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

    plt.close(10)
    plt.figure(10,figsize=(12,6))
    plt.suptitle(name_dossier_instrument_1+' épaisseur par puits '+type_intrument_2+' vs '+type_intrument_1 +'\n ')#\n'
    plt.plot(vecteur_thickness_instrument_2[mask_thickness_proches],vecteur_thickness_instrument_1[mask_thickness_proches],'o',color='blue',label='data utile au fit')
    plt.plot(vecteur_thickness_instrument_2[mask_thickness_eloignes],vecteur_thickness_instrument_1[mask_thickness_eloignes],'rx',label='outlier')
    plt.plot(np.arange(np.nanmin(vecteur_thickness_instrument_2),np.nanmax(vecteur_thickness_instrument_2)),np.arange(np.nanmin(vecteur_thickness_instrument_2),np.nanmax(vecteur_thickness_instrument_2)),label='bissectrice = target',color='k')
    plt.xlabel('T issu stat nm  '+type_intrument_2)
    plt.ylabel('T issu stat nm  '+type_intrument_1)
    plt.legend()
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'epaisseur par puits.jpg')

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
        plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'epaisseur par puits_FIT.jpg')
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
        plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'epaisseur par puits_FIT.jpg')
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
    plt.savefig(directory_plaque_to_save+'\\'+name_dossier_to_save+'epaisseur par puits_fit.jpg')

#    assemblage des figures de dotmaps et colormaps
    # merge_two_figure([directory_source_synthese_instrument_1,directory_source_synthese_instrument_2],name_dossier_instrument_1,['stat_litteral_thicknesses_colormap.png','stat_litteral_thicknesses_colormap.png'],directory_plaque_to_save)
    # merge_two_figure([directory_source_synthese_instrument_1,directory_source_synthese_instrument_2],name_dossier_instrument_1,['stat_litteral_intensity_455_colormap.png','stat_litteral_intensity_455_colormap.png'],directory_plaque_to_save)
    # merge_two_figure([directory_source_synthese_instrument_1,directory_source_synthese_instrument_2],name_dossier_instrument_1,['stat_litteral_intensity_730_colormap.png','stat_litteral_intensity_730_colormap.png'],directory_plaque_to_save)

#    regénération des colormaps volumes et diamètres
    affiche_colormap_etude_general(thickness_instrument_1,'épaisseur_'+type_intrument_1,'jet',0,200)
    plt.savefig(directory_plaque_to_save+'\\epaisseur_'+type_intrument_1+'.jpg')

    affiche_colormap_etude_general(thickness_instrument_2,'épaisseur_'+type_intrument_2,'jet',0,200)
    plt.savefig(directory_plaque_to_save+'\\epaisseur_'+type_intrument_2+'.jpg')

    merge_two_figure([directory_plaque_to_save,directory_plaque_to_save],name_dossier_instrument_1,['epaisseur_'+type_intrument_1+'.jpg','epaisseur_'+type_intrument_2+'.jpg'],directory_plaque_to_save)

#    copier coller des dotmaps
    copyfile(directory_source_synthese_instrument_1+'\\stat_litteral_thicknesses_colormap.png',directory_plaque_to_save+'\\thicknesses_'+type_intrument_1+'.png')
    copyfile(directory_source_synthese_instrument_2+'\\stat_litteral_thicknesses_colormap.png',directory_plaque_to_save+'\\thicknesses_'+type_intrument_2+'.png')

    copyfile(directory_source_synthese_instrument_1+'\\stat_litteral_intensity_455_colormap.png',directory_plaque_to_save+'\\intensity_455'+type_intrument_1+'.png')
    copyfile(directory_source_synthese_instrument_2+'\\stat_litteral_intensity_455_colormap.png',directory_plaque_to_save+'\\intensity_455'+type_intrument_2+'.png')

    copyfile(directory_source_synthese_instrument_1+'\\stat_litteral_intensity_730_colormap.png',directory_plaque_to_save+'\\intensity_730'+type_intrument_1+'.png')
    copyfile(directory_source_synthese_instrument_2+'\\stat_litteral_intensity_730_colormap.png',directory_plaque_to_save+'\\intensity_730'+type_intrument_2+'.png')
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


    # afficher les paramtère de la fonction
    print("Paramètres de la fonction comparaison enzymo :")
    print("directory_source_instrument_1 :", directory_source_instrument_1)
    print("type_instrument_1 :", type_instrument_1)
    print("acquisition_name_instrument_1 :", acquisition_name_instrument_1)
    print("directory_source_instrument_2 :", directory_source_instrument_2)
    print("type_instrument_2 :", type_instrument_2)
    print("acquisition_name_instrument_2 :", acquisition_name_instrument_2)
    print("directory_to_save :", directory_to_save)
    print("============================================================================")
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
    print('results_Reference : \n',results_Reference)

    print('len(results_Reference) : ',len(results_Reference))
    if results_Reference[-1] == [] or results_Reference[-1] == [';;;;;;;;;'] or results_Reference[-1] == [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]:
        print('Dernière ligne vide ou non renseignée, suppression de la dernière ligne.')
        print(results_Reference[-1])
        results_Reference.pop()

    print(f'première ligne de results_Reference : {results_Reference[0]}')
    if results_Reference[0][0] == 'Plate Reference': # le premier onglet à un paragraphe de plus que les suivants (qui comporte les info date, heure, référence plaque, ce qui correspond à l'en-tête)
        start_stop = []
        j_1 = 0
        while len(start_stop) < 7 and j_1 < len(results_Reference):
            # On cherche les lignes vides ou les lignes qui contiennent uniquement des séparateurs
            if results_Reference[j_1] == []  or results_Reference[j_1] == [';;;;;;;;;'] or results_Reference[j_1] == [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]:
                print(f'Ajout de l\'index {j_1} à start_stop')
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
            print(f' entete refernece results_Reference[{k+3}] : {results_Reference[k+3]}')
            Entete_Reference.append(results_Reference[k+3])
        for k in range(start_stop[2] - start_stop[1] - 3):
            print(f' blanc reference results_Reference[{k+start_stop[1]+3}] : {results_Reference[k+start_stop[1]+3]}')
            Blank_Reference.append(results_Reference[k+start_stop[1]+3])
        for k in range(start_stop[4] - start_stop[3] - 3):
            print(f' gamme reference results_Reference[{k+start_stop[3]+3}] : {results_Reference[k+start_stop[3]+3]}')
            Gamme_Reference.append(results_Reference[k+start_stop[3]+3])
        for k in range(start_stop[5] - start_stop[4] - 3):
            print(f' sample reference results_Reference[{k+start_stop[4]+3}] : {results_Reference[k+start_stop[4]+3]}')
            Sample_Reference.append(results_Reference[k+start_stop[4]+3])
        for k in range(len(results_Reference) - start_stop[6] - 3):
            print(f' sample detail reference results_Reference[{k+start_stop[6]+3}] : {results_Reference[k+start_stop[6]+3]}')
            SampleDetail_Reference.append(results_Reference[k+start_stop[6]+3])
    else:
        start_stop = []
        j_1 = 0
        while len(start_stop) < 6 and j_1 < len(results_Reference):

            # On cherche les lignes vides ou les lignes qui contiennent uniquement des séparateurs
            if results_Reference[j_1] == []  or results_Reference[j_1] == [';;;;;;;;;'] or results_Reference[j_1] == [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]:
                print(f'Ajout de l\'index {j_1} à start_stop séparateur')
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
            print(f' entete refernece results_Reference[{k+3}] : {results_Reference[k+3]}')
            Entete_Reference.append(results_Reference[k])
        for k in range(start_stop[1] - start_stop[0] - 3):
            print(f' blanc reference results_Reference[{k+start_stop[0]+3}] : {results_Reference[k+start_stop[0]+3]}')
            Blank_Reference.append(results_Reference[k+start_stop[0]+3])
        for k in range(start_stop[3] - start_stop[2] - 3):
            print(f' gamme reference results_Reference[{k+start_stop[2]+3}] : {results_Reference[k+start_stop[2]+3]}')
            Gamme_Reference.append(results_Reference[k+start_stop[2]+3])
        for k in range(start_stop[4] - start_stop[3] - 3):
            print(f' sample reference results_Reference[{k+start_stop[3]+3}] : {results_Reference[k+start_stop[3]+3]}')
            Sample_Reference.append(results_Reference[k+start_stop[3]+3])
        for k in range(len(results_Reference) - start_stop[5] - 3):
            print(f' sample detail reference results_Reference[{k+start_stop[5]+3}] : {results_Reference[k+start_stop[5]+3]}')
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

# =============================================================================
# debut code d'utilisation des fct
# =============================================================================

alphabet_majuscule = string.ascii_uppercase

''' MACHINE A VALIDER '''
# Chemin d'accès au dossier avec toutes les acquisitions nomées comme suit :
# nom_de_plaque (qui sort du cube) + "_numéro_de_la_série"
# exemple "Ax_ZC_20x_GPExploAx220112-07_17022022_3"
# Utiliser un chemin par défaut qui peut être remplacé par les paramètres passés aux fonctions
default_valid_dir = os.environ.get('ZYMOPTIQ_VALID_DIR', os.path.join(os.path.expanduser('~'), 'Documents', 'VALID_ZC27'))
directory_source_valid = default_valid_dir
nom_machine_a_valider = 'ZC27'

''' MACHINE REFERENCE '''
default_ref_dir = os.environ.get('ZYMOPTIQ_REF_DIR', os.path.join(os.path.expanduser('~'), 'Documents', 'reference_ZC13_routine_validation'))
directory_source_reference = default_ref_dir
nom_machine_reference = 'REFERENCE ZYMOPTIQ ZC13'

# Longueur d'onde utilisée
lo = 730

# Vérifier si les répertoires existent
if not os.path.exists(directory_source_valid):
    print(f"Le répertoire de validation {directory_source_valid} n'existe pas. Création du répertoire.")
    os.makedirs(directory_source_valid, exist_ok=True)

if not os.path.exists(directory_source_reference):
    print(f"Le répertoire de référence {directory_source_reference} n'existe pas. Création du répertoire.")
    os.makedirs(directory_source_reference, exist_ok=True)

# Initialiser la liste des dossiers présents si le répertoire existe
liste_dossier_present = []
if os.path.exists(directory_source_valid):
    try:
        liste_dossier_present = os.listdir(directory_source_valid)
    except Exception as e:
        print(f"Erreur lors de la lecture du répertoire {directory_source_valid}: {str(e)}")
        liste_dossier_present = []

# chaque plaque va etre traitée indépendament des autres
# prend les plaques avec cette clef ds le nom de dossier
plate_type = 'GP'  # pour la plate type GP ( les plaques micro depot )
plat_type_nanofilm = 'SC'  # pour la plate type SC ( les plaques nanofilm )
#    va contenir tous les nom de dossier où on trouve les caractères correspondants au plate_type
liste_plaque = []
liste_plaque_nanofilm = []

# Cherche les plaques correspondantes dans la liste des dossiers présents
for folder in liste_dossier_present:
    if plate_type in folder and folder not in liste_plaque:
        liste_plaque.append(folder)
    if plat_type_nanofilm in folder and folder not in liste_plaque_nanofilm:
        liste_plaque_nanofilm.append(folder)
   #
#   nb total de dossier à traiter (peu importe la ref)
nb_plaque_to_consider_all = len(liste_plaque)
nb_plaque_to_consider_all_nanofilm = len(liste_plaque_nanofilm)

#liste_ref_plaque = [] # contient les références des plaques sans le numero de repeta
#j_plaque = 0
#while j_plaque < nb_plaque_to_consider_all:
#    if liste_plaque[j_plaque][:-3] not in liste_ref_plaque:
#        liste_ref_plaque.append(liste_plaque[j_plaque][:-3])
#    j_plaque += 1 
#    
#    

liste_ref_plaque = [] # contient les références des plaques sans le numero de repeta
liste_ref_plaque_nanofilm = [] 
j_plaque = 0
while j_plaque < nb_plaque_to_consider_all:
       # le but est de trouver juste la ref de la plaque et la nomenclature n'est pas hyper fixe entre les HA BA Explo... 
#            donc je me base sur la présence de 'GP' en début de ref et sur la présence de '2' au début de la date du lot et sur le fait que la ref date-num fait 9 caractères
# ATTENTION : NE FONCTIONNERA PLUS EN 2030 ou lorsqu'on fera des lot de production de plus de 99 plaques.
# en 2030, simplement changer le "find('2') par find('3')
    index_debut_nom = liste_plaque[j_plaque].find(plate_type)   
    index_debut_date = liste_plaque[j_plaque][index_debut_nom:].find('2') 
    nb_caractere_numero_plaque = 9
    index_fin_date = index_debut_nom+index_debut_date+nb_caractere_numero_plaque
#            nom_gp est donc juste le nom de la plaque
    nom_gp =  liste_plaque[j_plaque][index_debut_nom:index_fin_date]

    if nom_gp not in liste_ref_plaque:
        liste_ref_plaque.append(nom_gp)
    j_plaque += 1   

j_plaque = 0
while j_plaque < nb_plaque_to_consider_all_nanofilm:
       # le but est de trouver juste la ref de la plaque et la nomenclature n'est pas hyper fixe entre les HA BA Explo... 
#            donc je me base sur la présence de 'SC' en début de ref et sur la présence de '2' au début de la date du lot et sur le fait que la ref date-num fait 9 caractères
    index_debut_nom = liste_plaque_nanofilm[j_plaque].find(plat_type_nanofilm)   
    index_debut_date = liste_plaque_nanofilm[j_plaque][index_debut_nom:].find('2') 
    nb_caractere_numero_plaque = 9
    index_fin_date = index_debut_nom+index_debut_date+nb_caractere_numero_plaque
#            nom_gp est donc juste le nom de la plaque
    nom_gp =  liste_plaque_nanofilm[j_plaque][index_debut_nom:index_fin_date]

    if nom_gp not in liste_ref_plaque_nanofilm:
        liste_ref_plaque_nanofilm.append(nom_gp)
    j_plaque += 1    

# ça c'est le nombre de plaque à traiter    
nb_ref_plaque = len(liste_ref_plaque)  
nb_ref_plaque_nanofilm = len(liste_ref_plaque_nanofilm) 
# pour chaque plaque on va compter combien de repeta elle a 
if nb_ref_plaque != 0:
    nb_repeta_par_ref = np.zeros(nb_ref_plaque)
if nb_ref_plaque_nanofilm != 0:
    nb_repeta_par_ref_nanofilm = np.zeros(nb_ref_plaque_nanofilm)
# on retient le nom de ces repeta 
if nb_ref_plaque != 0:
    name_repeta_ref = [[] for _ in range(nb_ref_plaque)]
if nb_ref_plaque_nanofilm != 0:
    name_repeta_ref_nanofilm = [[] for _ in range(nb_ref_plaque_nanofilm)]
# NB: le nombre de repeta peut être différents

if nb_ref_plaque != 0:
    j_plaque = 0
    while j_plaque < nb_ref_plaque:
        ref = liste_ref_plaque[j_plaque]
        j_plaque_all = 0
        while j_plaque_all<nb_plaque_to_consider_all:
            if ref in liste_plaque[j_plaque_all]:
                name_repeta_ref[j_plaque].append(liste_plaque[j_plaque_all])
                nb_repeta_par_ref[j_plaque] += 1            
            j_plaque_all += 1
        j_plaque += 1    
    nb_max_de_repeta = int(np.max(nb_repeta_par_ref))

if nb_ref_plaque_nanofilm != 0:
    j_plaque = 0
    while j_plaque < nb_ref_plaque_nanofilm:
        ref = liste_ref_plaque_nanofilm[j_plaque]
        j_plaque_all = 0
        while j_plaque_all<nb_plaque_to_consider_all_nanofilm:
            if ref in liste_plaque_nanofilm[j_plaque_all]:
                name_repeta_ref_nanofilm[j_plaque].append(liste_plaque_nanofilm[j_plaque_all])
                nb_repeta_par_ref_nanofilm[j_plaque] += 1            
            j_plaque_all += 1
        j_plaque += 1
    nb_max_de_repeta_nanofilm = int(np.max(nb_repeta_par_ref_nanofilm))
# contient les noms des plaques post car elle ne sont pas traitées de la même façon
# Utiliser une variable d'environnement ou une valeur par défaut
default_plaque_post = ['GPAxHA230712-02']
plaque_post_env = os.environ.get('ZYMOPTIQ_PLAQUE_POST', '')
if plaque_post_env:
    try:
        # Format attendu: "plaque1,plaque2,plaque3"
        plaque_post = plaque_post_env.split(',')
        print(f"Utilisation des plaques post depuis la variable d'environnement: {plaque_post}")
    except Exception as e:
        print(f"Erreur lors de la lecture des plaques post depuis la variable d'environnement: {str(e)}")
        plaque_post = default_plaque_post
else:
    plaque_post = default_plaque_post
# tracker sur quel traitement on veut lancer
# Ces variables peuvent être configurées via des variables d'environnement

# toujours désactivé pour un déploiement car pas de répéta, seulement une acquisition
do_you_wanna_repeta_sans_ref = int(os.environ.get('ZYMOPTIQ_REPETA_SANS_REF', '0'))

# =1 si mode expert, =0 si mode client car pas d'accès aux épaisseurs/volumes & diamètre en mode client
do_you_wanna_compare_to_ref = int(os.environ.get('ZYMOPTIQ_COMPARE_TO_REF', '0'))

# toujours lancer cette fonction par défaut
do_you_wanna_compare_enzymo_to_ref = int(os.environ.get('ZYMOPTIQ_COMPARE_ENZYMO_TO_REF', '1'))

print(f"Configuration des traitements:")
print(f"- Répéta sans référence: {'Activé' if do_you_wanna_repeta_sans_ref else 'Désactivé'}")
print(f"- Comparaison aux références: {'Activé' if do_you_wanna_compare_to_ref else 'Désactivé'}")
print(f"- Comparaison enzymo aux références: {'Activé' if do_you_wanna_compare_enzymo_to_ref else 'Désactivé'}")



if do_you_wanna_repeta_sans_ref == 1:
    # choix du dossier racine ou seront créé les dossiers par nom de plaque qui contiendront les data de repeta
    directory_racine_output_repeta = directory_source_valid+'\\repeta_sans_ref_v1_fct_routine'
    if os.path.exists(directory_racine_output_repeta) == False:
        os.mkdir(directory_racine_output_repeta)

    CV_repeta_threshold = 5


    """PLAQUES MICRO DEPOTS"""

    nb_well_CV_over_threshold = np.zeros(nb_ref_plaque)
    CV_on_volume_mean = np.zeros(nb_ref_plaque)
    CV_on_volume_min = np.zeros(nb_ref_plaque)
    CV_on_volume_max = np.zeros(nb_ref_plaque)

    CV_on_diameter_mean = np.zeros(nb_ref_plaque)
    CV_on_diameter_min = np.zeros(nb_ref_plaque)
    CV_on_diameter_max = np.zeros(nb_ref_plaque)

    csv_out_repeta = open(directory_racine_output_repeta+'\\data_repeta_micro_depot.csv','w')

    csv_out_repeta.write('nom_plaque;nb_lecture;tolerance_en_cv_colume;nb_puits_au_dessus_du_seuil;CV_max_V;CV_min_V;CV_mean_V;CV_max_D;CV_min_D;CV_mean_D\n')

    j_plaque = 0 
    while j_plaque<nb_ref_plaque:
        plaque_actuelle = liste_ref_plaque[j_plaque]
    #    lancement de la fonction repeta_sans_ref_v1 sur la plaque_actuelle 
        nb_lecture_this_plate , nb_well_over_threshold_out_fct , CV_max_V_this_plate, CV_min_V_this_plate, CV_mean_V_this_plate, CV_max_D_this_plate, CV_min_D_this_plate, CV_mean_D_this_plate, volume_mean_out_fct , volume_CV_out_fct , diametre_mean_out_fct , diametre_CV_out_fct  = repeta_sans_ref_v1(directory_source_valid,plaque_actuelle,'Images',directory_racine_output_repeta,CV_repeta_threshold)
        nb_well_CV_over_threshold[j_plaque] = nb_well_over_threshold_out_fct

        CV_on_volume_mean[j_plaque] = CV_mean_V_this_plate
        CV_on_volume_min[j_plaque] = CV_min_V_this_plate
        CV_on_volume_max[j_plaque] = CV_max_V_this_plate

        CV_on_diameter_mean[j_plaque] = CV_mean_D_this_plate
        CV_on_diameter_min[j_plaque] = CV_min_D_this_plate
        CV_on_diameter_max[j_plaque] = CV_max_D_this_plate
        csv_out_repeta.write(plaque_actuelle+';'+str(nb_lecture_this_plate)+';'+str(CV_repeta_threshold)+';'+str(nb_well_over_threshold_out_fct)+';'+str(CV_max_V_this_plate)+';'+str(CV_min_V_this_plate)+';'+str(CV_mean_V_this_plate)+';'+str(CV_max_D_this_plate)+';'+str(CV_min_D_this_plate)+';'+str(CV_mean_D_this_plate)+'\n')

        j_plaque += 1

    plt.close('all')
    plt.figure(figsize=(8, 6))
    plt.title('data_issue_agglomeration_sans_ref\n nb de puits au dessus de '+str(CV_repeta_threshold)+'% de CV en volume')
    plt.plot(np.arange(nb_ref_plaque),nb_well_CV_over_threshold,'*')  
    #plt.xticks(np.arange(nb_ref_plaque),liste_plaque, rotation=10)      
    plt.xlabel('plaques')
    plt.ylabel('nb de puits')
    plt.savefig(directory_racine_output_repeta+'\\nb de puits au dessus de '+str(CV_repeta_threshold)+'% de CV en volume.jpg')

    plt.close('all')
    plt.figure(figsize=(8, 6))
    plt.title('data_issue_agglomeration_sans_ref\n CV moyen sur les volumes sur toute la plaque')
    plt.plot(np.arange(nb_ref_plaque),CV_on_volume_mean,'o',color = '#20B2AA',label='mean')  
    plt.plot(np.arange(nb_ref_plaque),CV_on_volume_min,marker="_",ls='',color = '#20B2AA',label='min')
    plt.plot(np.arange(nb_ref_plaque),CV_on_volume_max,marker="_",ls='',color = '#20B2AA',label='max')       
    #plt.xticks(np.arange(nb_ref_plaque),liste_plaque, rotation=10)  
    plt.legend()    
    plt.xlabel('plaques')
    plt.ylabel('CV moyen sur les volumes en % ')
    plt.savefig(directory_racine_output_repeta+'\\CV_on_volume_mean.jpg')

    plt.close('all')
    plt.figure(figsize=(8, 6))
    plt.title('data_issue_agglomeration_sans_ref\n CV moyen sur les diametre sur toute la plaque')
    plt.plot(np.arange(nb_ref_plaque),CV_on_diameter_mean,'v',color = '#191970')  
    plt.plot(np.arange(nb_ref_plaque),CV_on_diameter_min,marker="_",ls='',color = '#191970',label='min')
    plt.plot(np.arange(nb_ref_plaque),CV_on_diameter_max,marker="_",ls='',color = '#191970',label='max')       
    #plt.xticks(np.arange(nb_ref_plaque),liste_plaque, rotation=10)      
    plt.xlabel('plaques')
    plt.ylabel('CV moyen sur les diametre en % ')
    plt.savefig(directory_racine_output_repeta+'\\CV_on_diameter_mean.jpg')

    csv_out_repeta.close()

    """ PLAQUES NANOFILM"""

    nb_well_CV_over_threshold = np.zeros(nb_ref_plaque_nanofilm)

    CV_on_thickness_mean = np.zeros(nb_ref_plaque_nanofilm)
    CV_on_thickness_min = np.zeros(nb_ref_plaque_nanofilm)
    CV_on_thickness_max = np.zeros(nb_ref_plaque_nanofilm)

    CV_on_I4_mean = np.zeros(nb_ref_plaque_nanofilm)
    CV_on_I4_min = np.zeros(nb_ref_plaque_nanofilm)
    CV_on_I4_max = np.zeros(nb_ref_plaque_nanofilm)

    CV_on_I7_mean = np.zeros(nb_ref_plaque_nanofilm)
    CV_on_I7_min = np.zeros(nb_ref_plaque_nanofilm)
    CV_on_I7_max = np.zeros(nb_ref_plaque_nanofilm)


    csv_out_repeta_nanofilm = open(directory_racine_output_repeta+'\\data_repeta_nanofilm.csv','w')

    csv_out_repeta_nanofilm.write('nom_plaque;nb_lecture;tolerance_en_cv_épaisseur;nb_puits_au_dessus_du_seuil;CV_max_T;CV_min_T;CV_mean_T;CV_max_I455;CV_min_I455;CV_mean_I455;CV_max_I730;CV_min_I730;CV_mean_I730\n')

    j_plaque = 0 
    while j_plaque<nb_ref_plaque_nanofilm:
        plaque_actuelle = liste_ref_plaque_nanofilm[j_plaque]
    #    lancement de la fonction repeta_sans_ref_v1 sur la plaque_actuelle 
        nb_lecture_this_plate , nb_well_over_threshold_out_fct , CV_max_T_this_plate, CV_min_T_this_plate, CV_mean_T_this_plate, CV_max_I4_this_plate, CV_min_I4_this_plate, CV_mean_I4_this_plate, CV_max_I7_this_plate, CV_min_I7_this_plate, CV_mean_I7_this_plate, thickness_mean_out_fct ,         thickness_CV_out_fct ,       intensity_455_mean_out_fct ,       intensity_455_CV_out_fct ,         intensity_730_mean_out_fct ,       intensity_730_CV_out_fct = repeta_sans_ref_v1_nanofilm(directory_source_valid,plaque_actuelle,'Images',directory_racine_output_repeta,CV_repeta_threshold)
        """
        nb_iteration , nb_well_over_threshold ,                  CV_max_thickness,     CV_min_thickness,   CV_mean_thickness,    CV_max_I4,             CV_min_I4,           CV_mean_I4 ,           CV_max_I7,            CV_min_I7,            CV_mean_I7,             thickness_mean_for_this_plate , thickness_CV_for_this_plate , intensity_455_mean_for_this_plate , intensity_455_CV_for_this_plate , intensity_730_mean_for_this_plate , intensity_730_CV_for_this_plate
        """
        nb_well_CV_over_threshold[j_plaque] = nb_well_over_threshold_out_fct

        CV_on_thickness_mean[j_plaque] = CV_mean_T_this_plate
        CV_on_thickness_min[j_plaque] = CV_min_T_this_plate
        CV_on_thickness_max[j_plaque] = CV_max_T_this_plate

        CV_on_I4_mean[j_plaque] = CV_mean_I4_this_plate
        CV_on_I4_min[j_plaque] = CV_min_I4_this_plate
        CV_on_I4_max[j_plaque] = CV_max_I4_this_plate

        CV_on_I7_mean[j_plaque] = CV_mean_I7_this_plate
        CV_on_I7_min[j_plaque] = CV_min_I7_this_plate
        CV_on_I7_max[j_plaque] = CV_max_I7_this_plate
        csv_out_repeta_nanofilm.write(plaque_actuelle+';'+str(nb_lecture_this_plate)+';'+str(CV_repeta_threshold)+';'+str(nb_well_over_threshold_out_fct)+';'+str(CV_max_T_this_plate)+';'+str(CV_min_T_this_plate)+';'+str(CV_mean_T_this_plate)+';'+str(CV_max_I4_this_plate)+';'+str(CV_min_I4_this_plate)+';'+str(CV_mean_I4_this_plate)+';'+str(CV_max_I7_this_plate)+';'+str(CV_min_I7_this_plate)+';'+str(CV_mean_I7_this_plate)+'\n')

        j_plaque += 1

    plt.close('all')
    plt.figure(figsize=(8, 6))
    plt.title('data_issue_agglomeration_sans_ref\n nb de puits au dessus de '+str(CV_repeta_threshold)+'% de CV en épaisseur')
    plt.plot(np.arange(nb_ref_plaque_nanofilm),nb_well_CV_over_threshold,'*')  
    #plt.xticks(np.arange(nb_ref_plaque),liste_plaque, rotation=10)      
    plt.xlabel('plaques')
    plt.ylabel('nb de puits')
    plt.savefig(directory_racine_output_repeta+'\\nb de puits au dessus de '+str(CV_repeta_threshold)+'% de CV en epaisseur.jpg')

    plt.close('all')
    plt.figure(figsize=(8, 6))
    plt.title('data_issue_agglomeration_sans_ref\n CV moyen sur les épaisseurs sur toute la plaque')
    plt.plot(np.arange(nb_ref_plaque_nanofilm),CV_on_thickness_mean,'o',color = '#20B2AA',label='mean')  
    plt.plot(np.arange(nb_ref_plaque_nanofilm),CV_on_thickness_min,marker="_",ls='',color = '#20B2AA',label='min')
    plt.plot(np.arange(nb_ref_plaque_nanofilm),CV_on_thickness_max,marker="_",ls='',color = '#20B2AA',label='max')       
    #plt.xticks(np.arange(nb_ref_plaque),liste_plaque, rotation=10)  
    plt.legend()    
    plt.xlabel('plaques')
    plt.ylabel('CV moyen sur les épaisseurs en % ')
    plt.savefig(directory_racine_output_repeta+'\\CV_on_thichness_mean.jpg')

    plt.close('all')
    plt.figure(figsize=(8, 6))
    plt.title('data_issue_agglomeration_sans_ref\n CV moyen sur les intensités 455 sur toute la plaque')
    plt.plot(np.arange(nb_ref_plaque_nanofilm),CV_on_I4_mean,'v',color = '#191970')  
    plt.plot(np.arange(nb_ref_plaque_nanofilm),CV_on_I4_min,marker="_",ls='',color = '#191970',label='min')
    plt.plot(np.arange(nb_ref_plaque_nanofilm),CV_on_I4_max,marker="_",ls='',color = '#191970',label='max')       
    #plt.xticks(np.arange(nb_ref_plaque),liste_plaque, rotation=10)      
    plt.xlabel('plaques')
    plt.ylabel('CV moyen sur les intensités 455 en % ')
    plt.savefig(directory_racine_output_repeta+'\\CV_on_I4_mean.jpg')

    plt.close('all')
    plt.figure(figsize=(8, 6))
    plt.title('data_issue_agglomeration_sans_ref\n CV moyen sur les intensités 730 sur toute la plaque')
    plt.plot(np.arange(nb_ref_plaque_nanofilm),CV_on_I7_mean,'v',color = '#191970')  
    plt.plot(np.arange(nb_ref_plaque_nanofilm),CV_on_I7_min,marker="_",ls='',color = '#191970',label='min')
    plt.plot(np.arange(nb_ref_plaque_nanofilm),CV_on_I7_max,marker="_",ls='',color = '#191970',label='max')       
    #plt.xticks(np.arange(nb_ref_plaque),liste_plaque, rotation=10)      
    plt.xlabel('plaques')
    plt.ylabel('CV moyen sur les intensités 730 en % ')
    plt.savefig(directory_racine_output_repeta+'\\CV_on_I7_mean.jpg')


    csv_out_repeta_nanofilm.close()

if do_you_wanna_compare_to_ref == 1:

    # le nom de l'instrument 1 : a valider
    type_intrument_1 = 'ZC20'
    # le nom de l'instrument 2 : référence
    type_intrument_2 = 'ZC20'
    # chemin vers les dossiers contenant les data des 2 instruments
    directory_source_instrument_1 =  directory_source_valid
    directory_source_instrument_2 =  directory_source_reference

    # dossier racine des dossiers résultats
    directory_racine_to_save = directory_source_valid+"\\comparaison_proto_fct_routine"
    # Utiliser makedirs pour créer tous les répertoires parents si nécessaire
    os.makedirs(directory_racine_to_save, exist_ok=True)

    """ PLAQUES MICRO-DEPOTS """
    if nb_ref_plaque != 0:
        slope_fit_save = np.zeros((nb_ref_plaque,nb_max_de_repeta)) 
        intercept_fit_save = np.zeros((nb_ref_plaque,nb_max_de_repeta)) 
        r_value_fit_save = np.zeros((nb_ref_plaque,nb_max_de_repeta)) 
        nb_puits_loin_fit_save = np.zeros((nb_ref_plaque,nb_max_de_repeta)) 

        pourcentage_volume_relative_mean_save = np.zeros((nb_ref_plaque,nb_max_de_repeta)) 
        pourcentage_volume_relative_CV_save = np.zeros((nb_ref_plaque,nb_max_de_repeta)) 
        pourcentage_diametre_relative_mean_save = np.zeros((nb_ref_plaque,nb_max_de_repeta)) 
        pourcentage_diametre_relative_CV_save = np.zeros((nb_ref_plaque,nb_max_de_repeta)) 

        to_plot_vol_instrument_1 = np.zeros((96,nb_max_de_repeta))
        to_plot_vol_instrument_2 = np.zeros((96,nb_max_de_repeta))
    # initialisation à nan car si on met 0 et que le nombre de répéta n'est pas fixe, on va garder des zéros qui ne seront pas des données mais un manque de données -> risque de faussage de moyennes etc...    
        slope_fit_save[:,:] = np.nan
        intercept_fit_save[:,:]  = np.nan
        r_value_fit_save[:,:]  = np.nan
        nb_puits_loin_fit_save[:,:]  = np.nan

        csv_out_compare_to_ref = open(directory_racine_to_save+'\\data_compar_ref_micro_depots.csv','w')

        csv_out_compare_to_ref.write('nom_plaque;slope_fit;intercept_fit;r_value_fit;nb_puits_loin_fit;pourcentage_volume_relative_mean;pourcentage_volume_relative_CV;pourcentage_diametre_relative_mean;pourcentage_diametre_relative_CV\n')

        j_plaque = 0 
        while j_plaque<nb_ref_plaque:
            directory_racine_to_save_plate = directory_racine_to_save+"\\"+liste_ref_plaque[j_plaque]
            if os.path.exists(directory_racine_to_save_plate) == False:
                os.mkdir(directory_racine_to_save_plate)

            color2 = gen_color(cmap="tab10",n=int(nb_repeta_par_ref[j_plaque]))
            to_plot_vol_instrument_1[:,:] = np.nan
            to_plot_vol_instrument_2[:,:] = np.nan        
            tic()
            j_repeta = 0
            while j_repeta <nb_repeta_par_ref[j_plaque]:
                name_dossier_instrument_1 =  name_repeta_ref[j_plaque][j_repeta] 
                # le but est de trouver juste la ref de la plaque et la nomenclature n'est pas hyper fixe entre les HA BA Explo... 
    #            donc je me base sur la présence de 'GP' en début de ref et sur la présence de '2' au début de la date du lot et sur le fait que la ref date-num fait 9 caractères
                index_debut_nom = name_dossier_instrument_1.find('GP')   
                index_debut_date = name_dossier_instrument_1[index_debut_nom:].find('2') 
                nb_caractere_numero_plaque = 9
                index_fin_date = index_debut_nom+index_debut_date+nb_caractere_numero_plaque
    #            nom_gp est donc juste le nom de la plaque
                nom_gp = name_dossier_instrument_1[index_debut_nom:index_fin_date]

                chemin_instru_1 = directory_source_instrument_1+'\\'+name_dossier_instrument_1+'\\Images'
                # chemin_instru_1 = directory_source_instrument_1+'\\'+name_dossier_instrument_1+'\\730_ZI'
                chemin_instru_2 = directory_source_instrument_2+'\\'+nom_gp+'\\Images'
                # chemin_instru_2 = directory_source_instrument_2+'\\'+nom_gp+'\\expo\\730_ZI'
                if nom_gp in plaque_post:
                    chemin_instru_2 = directory_source_instrument_2+'\\'+nom_gp+'\\post\\730_ZI'
                tolerance_ecart_au_fit = 10

                name_dossier_to_save, slope_fit, intercept_fit, r_value_fit, nb_puits_loin_fit, pourcentage_volume_relative_mean , pourcentage_volume_relative_CV , pourcentage_diametre_relative_mean , pourcentage_diametre_relative_CV , vecteur_volume_instrument_1, vecteur_volume_instrument_2 = comparaison_ZC_to_ref_v1(nom_gp,chemin_instru_1,type_intrument_1,chemin_instru_2,type_intrument_2,directory_racine_to_save_plate,name_dossier_instrument_1,tolerance_ecart_au_fit)
    #            enregistrement dans les tableaux des KPI
                slope_fit_save [j_plaque][j_repeta] = slope_fit
                intercept_fit_save [j_plaque][j_repeta] = intercept_fit
                r_value_fit_save [j_plaque][j_repeta] = r_value_fit
                nb_puits_loin_fit_save [j_plaque][j_repeta] = nb_puits_loin_fit
                to_plot_vol_instrument_1[:,j_repeta] = np.copy(vecteur_volume_instrument_1)
                to_plot_vol_instrument_2[:,j_repeta] = np.copy(vecteur_volume_instrument_2)    
                pourcentage_volume_relative_mean_save [j_plaque][j_repeta] = pourcentage_volume_relative_mean
                pourcentage_volume_relative_CV_save [j_plaque][j_repeta] = pourcentage_volume_relative_CV
                pourcentage_diametre_relative_mean_save [j_plaque][j_repeta] = pourcentage_diametre_relative_mean
                pourcentage_diametre_relative_CV_save [j_plaque][j_repeta] = pourcentage_diametre_relative_CV        
                csv_out_compare_to_ref.write(name_repeta_ref[j_plaque][j_repeta] +';'+str(slope_fit)+';'+str(intercept_fit)+';'+str(r_value_fit)+';'+str(nb_puits_loin_fit)+';'+str(pourcentage_volume_relative_mean)+';'+str(pourcentage_volume_relative_CV)+';'+str(pourcentage_diametre_relative_mean)+';'+str(pourcentage_diametre_relative_CV)+'\n')
    #            la figure rassemblée est sortie de la boucle ici car dans la fonction comparaison_ZC_to_ref_v1, close('all') empeche d'ajouter au fur et à mesure
                j_repeta += 1

            pente_moyenne = np.mean(slope_fit_save [j_plaque][:])
            pente_std = np.std(slope_fit_save [j_plaque][:])
            pente_CV = pente_std/pente_moyenne*100

            intercept_fit_moyenne = np.mean(intercept_fit_save [j_plaque][:])
            intercept_fit_std = np.std(intercept_fit_save [j_plaque][:])
            intercept_fit_CV = intercept_fit_std/intercept_fit_moyenne*100

            plt.close('all')
            plt.figure(1,figsize=(12,12))
            plt.title(liste_ref_plaque[j_plaque]+' sur '+str(int(nb_repeta_par_ref[j_plaque]))+' runs')
            plt.suptitle('Agglomération des data des comparaisons de volumes selon la repeta et de leur fit')
            j_repeta = 0
            while j_repeta<nb_repeta_par_ref[j_plaque]:
                x_fit = np.arange(np.nanmin(to_plot_vol_instrument_2[:,j_repeta]),np.nanmax(to_plot_vol_instrument_2[:,j_repeta]))
                plt.plot(to_plot_vol_instrument_2[:,j_repeta],to_plot_vol_instrument_1[:,j_repeta],'.',color= color2[j_repeta],label=name_repeta_ref[j_plaque][j_repeta])  
                plt.plot(x_fit,x_fit*slope_fit_save [j_plaque][j_repeta]+intercept_fit_save [j_plaque][j_repeta],'--',color= color2[j_repeta],label='fit s='+str(round(slope_fit_save [j_plaque][j_repeta],4))+' i='+str(round(intercept_fit_save [j_plaque][j_repeta],2))+'R²='+str(round(r_value_fit_save [j_plaque][j_repeta],3)))  
                j_repeta += 1
            plt.xlabel('V '+type_intrument_2+' µm^3')
            plt.ylabel('V '+type_intrument_1+' µm^3')
            plt.legend()  
            plt.savefig(directory_racine_to_save+'\\aglomeration_fit_to_ref_'+liste_ref_plaque[j_plaque]+'.jpg')

            toc()

            plt.figure(2,figsize=(8,6))
            plt.suptitle('pente des fits')
            plt.title(liste_ref_plaque[j_plaque]+' sur '+str(int(nb_repeta_par_ref[j_plaque]))+' runs\n pente moyenne = '+str(round(pente_moyenne,4))+' avec un CV de '+str(round(pente_CV,1))+ ' %')
            plt.plot(np.arange(nb_repeta_par_ref[j_plaque]),slope_fit_save [j_plaque],marker="o",ls='',color = '#191970')       
    #        plt.xlabel('plaques')
            plt.ylabel('fit slope')
            #plt.xticks(np.arange(nb_repeta_par_ref[j_plaque]),name_repeta_ref[j_plaque][:] , rotation=10)      
            plt.legend()  
            plt.savefig(directory_racine_to_save+'\\pente_fit_to_ref_'+liste_ref_plaque[j_plaque]+'.jpg')

            plt.figure(3,figsize=(12,12))
            plt.title(liste_ref_plaque[j_plaque]+' sur '+str(int(nb_repeta_par_ref[j_plaque]))+' runs\n intercept moyen = '+str(round(intercept_fit_moyenne,4))+' avec un CV de '+str(round(intercept_fit_CV,1))+ ' %')
            plt.suptitle('intercept des fits')
            plt.plot(np.arange(nb_repeta_par_ref[j_plaque]),intercept_fit_save[j_plaque],marker="s",ls='',color = '#FFD700')       
    #        plt.xlabel('plaques')
            plt.ylabel('fit intercept')
            #plt.xticks(np.arange(nb_repeta_par_ref[j_plaque]), [j_plaque][:] , rotation=10)      
            plt.legend()  
            plt.savefig(directory_racine_to_save+'\\intercept_fit_to_ref_'+liste_ref_plaque[j_plaque]+'.jpg')

            j_plaque += 1

        csv_out_compare_to_ref.close()

    """ PLAQUES NANOFILMS """
    if nb_ref_plaque_nanofilm != 0:
        slope_fit_save = np.zeros((nb_ref_plaque_nanofilm,nb_max_de_repeta_nanofilm)) 
        intercept_fit_save = np.zeros((nb_ref_plaque_nanofilm,nb_max_de_repeta_nanofilm)) 
        r_value_fit_save = np.zeros((nb_ref_plaque_nanofilm,nb_max_de_repeta_nanofilm)) 
        nb_puits_loin_fit_save = np.zeros((nb_ref_plaque_nanofilm,nb_max_de_repeta_nanofilm)) 

        pourcentage_thickness_relative_mean_save = np.zeros((nb_ref_plaque_nanofilm,nb_max_de_repeta_nanofilm)) 
        pourcentage_thickness_relative_CV_save = np.zeros((nb_ref_plaque_nanofilm,nb_max_de_repeta_nanofilm))  

        to_plot_thick_instrument_1 = np.zeros((96,nb_max_de_repeta_nanofilm))
        to_plot_thick_instrument_2 = np.zeros((96,nb_max_de_repeta_nanofilm))
    # initialisation à nan car si on met 0 et que le nombre de répéta n'est pas fixe, on va garder des zéros qui ne seront pas des données mais un manque de données -> risque de faussage de moyennes etc...    
        slope_fit_save[:,:] = np.nan
        intercept_fit_save[:,:]  = np.nan
        r_value_fit_save[:,:]  = np.nan
        nb_puits_loin_fit_save[:,:]  = np.nan

        csv_out_compare_to_ref_nanofilm = open(directory_racine_to_save+'\\data_compar_ref_nanofilm.csv','w')

        csv_out_compare_to_ref_nanofilm.write('nom_plaque;slope_fit;intercept_fit;r_value_fit;nb_puits_loin_fit;pourcentage_thickness_relative_mean;pourcentage_thickness_relative_CV\n')

        j_plaque = 0 
        while j_plaque<nb_ref_plaque_nanofilm:
            directory_racine_to_save_plate = directory_racine_to_save+"\\"+liste_ref_plaque_nanofilm[j_plaque]
            if os.path.exists(directory_racine_to_save_plate) == False:
                os.mkdir(directory_racine_to_save_plate)

            color2 = gen_color(cmap="tab10",n=int(nb_repeta_par_ref_nanofilm[j_plaque]))
            to_plot_thick_instrument_1[:,:] = np.nan
            to_plot_thick_instrument_2[:,:] = np.nan        
            tic()
            j_repeta = 0
            while j_repeta <nb_repeta_par_ref_nanofilm[j_plaque]:
                name_dossier_instrument_1 =  name_repeta_ref_nanofilm[j_plaque][j_repeta] 
                # le but est de trouver juste la ref de la plaque et la nomenclature n'est pas hyper fixe entre les HA BA Explo... 
    #            donc je me base sur la présence de 'GP' en début de ref et sur la présence de '2' au début de la date du lot et sur le fait que la ref date-num fait 9 caractères
                index_debut_nom = name_dossier_instrument_1.find('SC')   
                index_debut_date = name_dossier_instrument_1[index_debut_nom:].find('2') 
                nb_caractere_numero_plaque = 9
                index_fin_date = index_debut_nom+index_debut_date+nb_caractere_numero_plaque
    #            nom_gp est donc juste le nom de la plaque
                nom_gp = name_dossier_instrument_1[index_debut_nom:index_fin_date]

                chemin_instru_1 = directory_source_instrument_1+'\\'+name_dossier_instrument_1+'\\Images'
                # chemin_instru_1 = directory_source_instrument_1+'\\'+name_dossier_instrument_1+'\\730_ZI'
                chemin_instru_2 = directory_source_instrument_2+'\\'+nom_gp+'\\Images'
                # chemin_instru_2 = directory_source_instrument_2+'\\'+nom_gp+'\\expo\\730_ZI'
                if nom_gp in plaque_post:
                    chemin_instru_2 = directory_source_instrument_2+'\\'+nom_gp+'\\post\\730_ZI'
                tolerance_ecart_au_fit = 10

                # print('\n\n\nslope_fit_save à vérifier : \n\n',slope_fit_save)

                name_dossier_to_save, slope_fit, intercept_fit, r_value_fit, nb_puits_loin_fit, pourcentage_thickness_relative_mean , pourcentage_thickness_relative_CV , vecteur_thickness_instrument_1, vecteur_thickness_instrument_2 = comparaison_ZC_to_ref_v1_nanofilm(nom_gp,chemin_instru_1,type_intrument_1,chemin_instru_2,type_intrument_2,directory_racine_to_save_plate,name_dossier_instrument_1,tolerance_ecart_au_fit)
    #            enregistrement dans les tableaux des KPI
                slope_fit_save[j_plaque][j_repeta] = slope_fit
                intercept_fit_save [j_plaque][j_repeta] = intercept_fit
                r_value_fit_save [j_plaque][j_repeta] = r_value_fit
                nb_puits_loin_fit_save [j_plaque][j_repeta] = nb_puits_loin_fit
                to_plot_thick_instrument_1[:,j_repeta] = np.copy(vecteur_thickness_instrument_1)
                to_plot_thick_instrument_2[:,j_repeta] = np.copy(vecteur_thickness_instrument_2)    
                pourcentage_thickness_relative_mean_save [j_plaque][j_repeta] = pourcentage_thickness_relative_mean
                pourcentage_thickness_relative_CV_save [j_plaque][j_repeta] = pourcentage_thickness_relative_CV
                csv_out_compare_to_ref_nanofilm.write(name_repeta_ref_nanofilm[j_plaque][j_repeta] +';'+str(slope_fit)+';'+str(intercept_fit)+';'+str(r_value_fit)+';'+str(nb_puits_loin_fit)+';'+str(pourcentage_thickness_relative_mean)+';'+str(pourcentage_thickness_relative_CV)+'\n')
    #            la figure rassemblée est sortie de la boucle ici car dans la fonction comparaison_ZC_to_ref_v1, close('all') empeche d'ajouter au fur et à mesure
                j_repeta += 1

            pente_moyenne = np.mean(slope_fit_save[j_plaque][:])
            pente_std = np.std(slope_fit_save[j_plaque][:])
            pente_CV = pente_std/pente_moyenne*100

            intercept_fit_moyenne = np.mean(intercept_fit_save [j_plaque][:])
            intercept_fit_std = np.std(intercept_fit_save [j_plaque][:])
            intercept_fit_CV = intercept_fit_std/intercept_fit_moyenne*100

            plt.close('all')
            plt.figure(1,figsize=(12,12))
            plt.title(liste_ref_plaque_nanofilm[j_plaque]+' sur '+str(int(nb_repeta_par_ref_nanofilm[j_plaque]))+' runs')
            plt.suptitle('Agglomération des data des comparaisons d\'épaisseur selon la repeta et de leur fit')
            j_repeta = 0
            while j_repeta<nb_repeta_par_ref_nanofilm[j_plaque]:
                x_fit = np.arange(np.nanmin(to_plot_thick_instrument_2[:,j_repeta]),np.nanmax(to_plot_thick_instrument_2[:,j_repeta]))
                plt.plot(to_plot_thick_instrument_2[:,j_repeta],to_plot_thick_instrument_1[:,j_repeta],'.',color= color2[j_repeta],label=name_repeta_ref_nanofilm[j_plaque][j_repeta])  
                plt.plot(x_fit,x_fit*slope_fit_save[j_plaque][j_repeta]+intercept_fit_save [j_plaque][j_repeta],'--',color= color2[j_repeta],label='fit s='+str(round(slope_fit_save [j_plaque][j_repeta],4))+' i='+str(round(intercept_fit_save [j_plaque][j_repeta],2))+'R²='+str(round(r_value_fit_save [j_plaque][j_repeta],3)))  
                j_repeta += 1
            plt.xlabel('T '+type_intrument_2+' nm')
            plt.ylabel('T '+type_intrument_1+' nm')
            plt.legend()  
            plt.savefig(directory_racine_to_save+'\\aglomeration_fit_to_ref_'+liste_ref_plaque_nanofilm[j_plaque]+'.jpg')

            toc()

            # print('\n\n\nnb_repeta_par_ref_nanofilm à vérifier : \n\n',nb_repeta_par_ref_nanofilm)
            # print('\n\n\nslope_fit_save à vérifier : \n\n',slope_fit_save)

            slope_fit_save_plt = [[value for value in sublist if not np.isnan(value)]for sublist in slope_fit_save]
            intercept_fit_save_plt = [[value for value in sublist if not np.isnan(value)]for sublist in intercept_fit_save]

            plt.figure(2,figsize=(8,6))
            plt.suptitle('pente des fits')
            plt.title(liste_ref_plaque_nanofilm[j_plaque]+' sur '+str(int(nb_repeta_par_ref_nanofilm[j_plaque]))+' runs\n pente moyenne = '+str(round(pente_moyenne,4))+' avec un CV de '+str(round(pente_CV,1))+ ' %')
            plt.plot(np.arange(nb_repeta_par_ref_nanofilm[j_plaque]),slope_fit_save_plt[j_plaque],marker="o",ls='',color = '#191970')       
    #        plt.xlabel('plaques')
            plt.ylabel('fit slope')
            #plt.xticks(np.arange(nb_repeta_par_ref[j_plaque]),name_repeta_ref[j_plaque][:] , rotation=10)      
            plt.legend()  
            plt.savefig(directory_racine_to_save+'\\pente_fit_to_ref_'+liste_ref_plaque_nanofilm[j_plaque]+'.jpg')

            plt.figure(3,figsize=(12,12))
            plt.title(liste_ref_plaque_nanofilm[j_plaque]+' sur '+str(int(nb_repeta_par_ref_nanofilm[j_plaque]))+' runs\n intercept moyen = '+str(round(intercept_fit_moyenne,4))+' avec un CV de '+str(round(intercept_fit_CV,1))+ ' %')
            plt.suptitle('intercept des fits')
            plt.plot(np.arange(nb_repeta_par_ref_nanofilm[j_plaque]),intercept_fit_save_plt[j_plaque],marker="s",ls='',color = '#FFD700')       
    #        plt.xlabel('plaques')
            plt.ylabel('fit intercept')
            #plt.xticks(np.arange(nb_repeta_par_ref[j_plaque]), [j_plaque][:] , rotation=10)      
            plt.legend()  
            plt.savefig(directory_racine_to_save+'\\intercept_fit_to_ref_'+liste_ref_plaque_nanofilm[j_plaque]+'.jpg')

            j_plaque += 1

        csv_out_compare_to_ref_nanofilm.close()

if do_you_wanna_compare_enzymo_to_ref == 1:

    # le nom de l'instrument 1 : référence
    type_instrument_1 = nom_machine_reference
    # le nom de l'instrument 2 : à valider
    type_instrument_2 = nom_machine_a_valider
    # chemin vers les dossiers contenant les data des 2 instruments
    directory_source_instrument_1 = directory_source_reference
    directory_source_instrument_2 =  directory_source_valid

    # dossier racine des dossiers résultats
    directory_racine_to_save = directory_source_valid+"\\comparaison_enzymo_routine"
    # Utiliser makedirs pour créer tous les répertoires parents si nécessaire
    os.makedirs(directory_racine_to_save, exist_ok=True)

    #contient les dossiers des acquisitions de référence donc une acquisition par plaque
    #avec les noms seulement de plaque
    #exemple : GPAxHA220203-05
    liste_acquisitions_references = []
    if os.path.exists(directory_source_instrument_1):
        try:
            liste_acquisitions_references = os.listdir(directory_source_instrument_1)
            print(f"Nombre d'acquisitions de référence trouvées: {len(liste_acquisitions_references)}")
        except Exception as e:
            print(f"Erreur lors de la lecture du répertoire {directory_source_instrument_1}: {str(e)}")
    else:
        print(f"Le répertoire de référence {directory_source_instrument_1} n'existe pas.")
        # Créer le répertoire s'il n'existe pas
        os.makedirs(directory_source_instrument_1, exist_ok=True)
        print(f"Répertoire {directory_source_instrument_1} créé.")

    all_results = []

    """ PLAQUES MICRO6DEPOTS """
    if nb_ref_plaque != 0 and liste_acquisitions_references:
        j_plaque = 0 
        while j_plaque<nb_plaque_to_consider_all:

            indic_post = 0
            for i in range(len(plaque_post)):
                if plaque_post[i] in liste_plaque[j_plaque]:
                    indic_post += 1

            if indic_post == 0:
                # Vérifier si on peut trouver une acquisition de référence correspondante
                acquisition_ref_trouvee = False
                j_find = 0

                # Chercher une acquisition de référence qui correspond à la plaque actuelle
                while j_find < len(liste_acquisitions_references):
                    if liste_acquisitions_references[j_find] in liste_plaque[j_plaque]:
                        acquisition_ref_trouvee = True
                        break
                    j_find += 1

                if acquisition_ref_trouvee:
                    try:
                        # Test si le fichier WellResults de l'acquisition de référence contient plusieurs onglets
                        excel_path = os.path.join(directory_source_instrument_1, liste_acquisitions_references[j_find], 'WellResults.xlsx')
                        if os.path.exists(excel_path):
                            excel_file = pandas.ExcelFile(excel_path)
                            noms_onglets = excel_file.sheet_names

                            for onglet in range(len(noms_onglets)):
                                data_enzymo_reference, data_enzymo_machine_a_valider = compare_enzymo_2_ref(
                                    directory_source_instrument_1, type_instrument_1, liste_acquisitions_references[j_find], 
                                    noms_onglets[onglet], directory_source_instrument_2, type_instrument_2, 
                                    liste_plaque[j_plaque], directory_racine_to_save
                                )

                                all_results.append(data_enzymo_reference)
                                all_results.append(data_enzymo_machine_a_valider)
                        else:
                            print(f"Le fichier WellResults.xlsx n'existe pas dans {os.path.dirname(excel_path)}")
                    except Exception as e:
                        print(f"Erreur lors du traitement de la plaque {liste_plaque[j_plaque]}: {str(e)}")
                else:
                    print(f"Aucune acquisition de référence trouvée pour la plaque {liste_plaque[j_plaque]}")

            j_plaque += 1
    elif nb_ref_plaque != 0:
        print("Aucune acquisition de référence trouvée. Impossible de comparer les plaques micro-dépôts.")

    """ PLAQUES NANOFILMS """
    if nb_ref_plaque_nanofilm != 0 and liste_acquisitions_references:
        j_plaque = 0 
        while j_plaque<nb_plaque_to_consider_all_nanofilm:

            indic_post = 0
            for i in range(len(plaque_post)):
                if plaque_post[i] in liste_plaque_nanofilm[j_plaque]:
                    indic_post += 1

            if indic_post == 0:
                # Vérifier si on peut trouver une acquisition de référence correspondante
                acquisition_ref_trouvee = False
                j_find = 0

                # Chercher une acquisition de référence qui correspond à la plaque actuelle
                while j_find < len(liste_acquisitions_references):
                    if liste_acquisitions_references[j_find] in liste_plaque_nanofilm[j_plaque]:
                        acquisition_ref_trouvee = True
                        break
                    j_find += 1

                if acquisition_ref_trouvee:
                    try:
                        # Test si le fichier WellResults de l'acquisition de référence contient plusieurs onglets
                        excel_path = os.path.join(directory_source_instrument_1, liste_acquisitions_references[j_find], 'WellResults.xlsx')
                        if os.path.exists(excel_path):
                            excel_file = pandas.ExcelFile(excel_path)
                            noms_onglets = excel_file.sheet_names

                            for onglet in range(len(noms_onglets)):
                                data_enzymo_reference, data_enzymo_machine_a_valider = compare_enzymo_2_ref(
                                    directory_source_instrument_1, type_instrument_1, liste_acquisitions_references[j_find], 
                                    noms_onglets[onglet], directory_source_instrument_2, type_instrument_2, 
                                    liste_plaque_nanofilm[j_plaque], directory_racine_to_save
                                )

                                all_results.append(data_enzymo_reference)
                                all_results.append(data_enzymo_machine_a_valider)
                        else:
                            print(f"Le fichier WellResults.xlsx n'existe pas dans {os.path.dirname(excel_path)}")
                    except Exception as e:
                        print(f"Erreur lors du traitement de la plaque nanofilm {liste_plaque_nanofilm[j_plaque]}: {str(e)}")
                else:
                    print(f"Aucune acquisition de référence trouvée pour la plaque nanofilm {liste_plaque_nanofilm[j_plaque]}")

            j_plaque += 1
    elif nb_ref_plaque_nanofilm != 0:
        print("Aucune acquisition de référence trouvée. Impossible de comparer les plaques nanofilms.")

    # Vérifier si nous avons des résultats à écrire
    if all_results:
        find_len_max = 0
        for i in range(len(all_results)):
            if len(all_results[i]) > find_len_max:
                find_len_max = len(all_results[i])

        # Créer le fichier CSV de résultats
        csv_path = os.path.join(directory_racine_to_save, 'data_compar_enzymo_2_ref.csv')
        try:
            with open(csv_path, 'w') as csv_out_compare_enzymo_to_ref:
                # Écrire l'en-tête
                csv_out_compare_enzymo_to_ref.write('Nom de l Acquisitions;Machine;Zone;LOD;LOQ;Sensibilite (en U/mL);CV % deg a 30%;CV % deg a 50%;CV % deg a 70%;')

                # Calculer le nombre d'échantillons
                nb_echantillons = max(0, int((find_len_max-14)/4))

                # Ajouter les colonnes pour chaque échantillon
                for i in range(nb_echantillons):
                    csv_out_compare_enzymo_to_ref.write('Activite Ech_' + str(i+1) + ' (U/mL);RSD Ech_' + str(i+1) + ' (%);')

                # Ajouter les colonnes de différence
                csv_out_compare_enzymo_to_ref.write('diff % LOD;diff % LOQ;diff % Sensibilite (en U/mL);diff % CV % deg a 30%;diff % CV % deg a 50%;diff % CV % deg a 70%;')

                for i in range(nb_echantillons):
                    csv_out_compare_enzymo_to_ref.write('diff % Activite Ech_' + str(i+1) + ' (U/mL);diff % RSD Ech_' + str(i+1) + ' (%);')

                csv_out_compare_enzymo_to_ref.write('\n')

                # Écrire les données
                for i in range(len(all_results)):
                    for j in range(len(all_results[i])):
                        csv_out_compare_enzymo_to_ref.write(str(all_results[i][j]) + ';')
                    csv_out_compare_enzymo_to_ref.write('\n')

            print(f"Résultats écrits dans {csv_path}")
        except Exception as e:
            print(f"Erreur lors de l'écriture des résultats dans {csv_path}: {str(e)}")
    else:
        print("Aucun résultat à écrire dans le fichier CSV. Vérifiez que les répertoires de référence et de validation contiennent des données valides.")
