import streamlit as st
import locale
from useful_functions import *

def rapports_seismes():
    # Personnalisation de la mise en page avec du code HTML
    st.markdown("<h1 style='text-align: left;'>Rapports en temps réel</h1>", unsafe_allow_html=True)


    # Widget pour choisir la période
    st.markdown("<h3>Choisir une période :</h3>", unsafe_allow_html=True)
    period = st.selectbox(
        "Sélectionnez la période",
        ["Un jour", "Trois jours", "Une semaine", "Un mois", "6 mois", "Un an","10 ans"]
    )

    # Afficher le message d'avertissement
    if period in ["Un mois", "6 mois", "Un an","10 ans"]:
        st.warning("Attention : plus la période choisie est longue, plus le temps d'exécution sera élevé.")

    # Convertir la période en nombre de jours
    period_days = {
        "Un jour": 1,
        "Trois jours": 3,
        "Une semaine": 7,
        "Un mois": 30,
        "6 mois": 180,
        "Un an": 365,
        "10 ans" : 3653
    }
    selected_days = period_days[period]

    st.write(f"Période sélectionnée : {period} ({selected_days} jours)")
    
    event_list=download_list_event(selected_days)

    col1, col2 = st.columns(2)

    with col1:
        # Affichage d'une synthèse des données téléchargées
        st.subheader("Histogramme du nombre d'id par mmi")
        # Arrondir les valeurs de MMI
        event_list['rounded_mmi'] = event_list['properties.mmi'].round()

        # Calculer le nombre d'événements par valeur arrondie de MMI
        mmi_counts = event_list['rounded_mmi'].value_counts().sort_index()

        # Créer l'histogramme
        plt.bar(mmi_counts.index, mmi_counts.values)
        plt.xlabel('MMI arrondi')
        plt.ylabel("Nombre d'événements")
        plt.xticks(mmi_counts.index)  # Utiliser les valeurs arrondies comme étiquettes
        st.pyplot(plt)
    
    with col2:
    
        st.subheader("Évènements les plus importants")

        # Trier les événements par ordre décroissant du MMI
        sorted_event_list = event_list.sort_values(by='properties.mmi', ascending=False)

        sorted_event_list_renamed = sorted_event_list.rename(
            columns={'id': 'ID', 'properties.mmi': 'MMI', 'properties.url': 'Lien vers USGS'}
        )

        if len(sorted_event_list_renamed)<=10:
            selected_radio_text = st.radio(
                "Sélectionner un ID :",
                [f"ID : {row['ID']} (MMI : {row['MMI']})" for _, row in sorted_event_list_renamed.iterrows()]
            )
        else:
            # Afficher les événements triés par lot de 10
            items_per_page = 10
            num_pages = (len(sorted_event_list_renamed) + items_per_page - 1) // items_per_page

            page = st.slider("Page", 1, num_pages, value=1)

            start_idx = (page - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, len(sorted_event_list_renamed))

            selected_radio_text = st.radio(
                "Sélectionner un ID :",
                [f"ID : {row['ID']} (MMI : {row['MMI']})" for _, row in sorted_event_list_renamed[start_idx:end_idx].iterrows()]
            )

            # Afficher la pagination
            st.write(f"Page {page} sur {num_pages}")

        # Extraire l'ID du texte sélectionné
        selected_id = selected_radio_text.split(':')[1].split('(')[0].strip()

        selected_row = sorted_event_list_renamed[sorted_event_list_renamed['ID'] == selected_id].iloc[0]
        st.write("Lien vers USGS :")
        st.markdown(f"[{selected_row['Lien vers USGS']}]({selected_row['Lien vers USGS']})")


        
    st.markdown("<h3 style='text-align: left;'>Sites à observer :</h3>", unsafe_allow_html=True)

    # Ajouter un widget de chargement de fichier
    uploaded_file = st.file_uploader("Charger une liste de coordonnées géographiques", type=["csv", "xlsx"])

    if uploaded_file is not None:
        # Charger les données à partir du fichier
        df = load_data(uploaded_file)
        liste_coordonnees = list(zip(df['Latitude'], df['Longitude']))
        values=list(df["TIV"])

        # Récupérer les informations des MMI du séisme
        event = link_xml_event(selected_id)
        xml_file_path=event[0]
        title=event[1]
        time=event[2]
        date = datetime.fromtimestamp(time/1000).strftime('%Y-%m-%d %H:%M:%S')
        mag=event[3]
        mmi_event=event[4]
        
        # Lire le grid.xml
        grid_event = parse_link_grid_xml(xml_file_path)
        sampled_grid = grid_event.sample(frac=0.05, random_state=42)
        minmmi = grid_event["MMI"].min()
        maxmmi = grid_event["MMI"].max()
        center_lat = grid_event["Latitude"].mean()
        center_lon = grid_event["Longitude"].mean()

        # Croiser entre le grid et la liste des sites observés
        mmi_sites=point_plus_proche(liste_coordonnees,grid_event)
        n_sites_touches = sum(mmi > 0 for mmi in mmi_sites)
        var = round(sum(value for mmi, value in zip(mmi_sites, values) if mmi > 0) / 10**3, 1)

        # Création de la map
        world_map = folium.Map(location=[center_lat, center_lon], zoom_start=5.3)
        folium.Marker(
            location=[center_lat, center_lon],
             popup='Epicentre\nMMI :'+str(maxmmi),
            icon=folium.Icon(color='black', prefix='fa', icon_size=100)
        ).add_to(world_map)

        # Ajouter les marqueurs pour les sites

        for (lat, lon), mmi,value in zip(liste_coordonnees, mmi_sites,values):

            if mmi==0: 
                popup_content='Hors de la zone sismique' 
            else: 
                popup_content = f'Site \nMMI : {mmi}\nTIV : {round(value/10**3,1)} k$'
            folium.Marker(
                location=[lat, lon],
                popup=popup_content,
                icon=folium.Icon(color='darkblue', prefix='fa')
            ).add_to(world_map)
        

        
        # Définir l'échelle de couleurs
        custom_colors = ['lightgreen', 'yellow', 'orange', 'red', 'darkred']
        color_scale = folium.LinearColormap(custom_colors, vmin=minmmi, vmax=maxmmi)

        # Ajouter les cercles colorés
        for index, row in sampled_grid.iterrows():
            lat = row["Latitude"]
            lon = row["Longitude"]
            mmi = row["MMI"]
            folium.CircleMarker(
                location=(lat, lon),
                radius=20,
                color=None,
                fill=True,
                fill_color=color_scale(mmi),
                fill_opacity=0.01,
            ).add_to(world_map)

        color_scale.caption = "Modified Mercalli Intensity (MMI)"
        color_scale.add_to(world_map)

        # Charger l'application Streamlit
        st.title(title)
        st.subheader("Evènement du "+ str(date) +" de magnitude "+str(mag)+" de MMI "+str(round(mmi_event,1))+".")

        # Afficher la carte Folium dans Streamlit et un summary
        
        if n_sites_touches==0:
            folium_static(world_map)
        else:
            col_1, col_2 = st.columns(2)
            with col_1:
                folium_static(world_map, width=500, height=500)
            with col_2:
                st.markdown(f"<h4 style='text-align: left;'>Tremblement de terre ayant touché {n_sites_touches} sites pour une valeur assurée totale de {var} k€ </h1>", unsafe_allow_html=True)

        st.markdown(f"<h4 style='text-align: left;'>Tremblement de terre ayant touché {n_sites_touches} sites pour une valeur assurée totale de {var} k€ </h1>", unsafe_allow_html=True)
        
        # Créer un tableau HTML personnalisé transposé
        st.subheader("Repartition Values by Mercalli Intensity zone")
        

        html_table = """
        <table>
        <tr>
            <th>MERCALLI INTENSITY</th>
            <th>Not exposed</th>
            <th>I</th>
            <th>II-III</th>
            <th>IV</th>
            <th>V</th>
            <th>VI</th>
            <th>VII</th>
            <th>VIII</th>
            <th>IX</th>
            <th>X+</th>
        </tr>
        <tr>
            <th>PERCEIVED SHAKING</th>
            <th>Not exposed</th>
            <th>Not felt</th>
            <th>Weak</th>
            <th>Light</th>
            <th>Moderate</th>
            <th>Strong</th>
            <th>Very Strong</th>
            <th>Severe</th>
            <th>Violent</th>
            <th>Extreme</th>
        </tr>
        <tr>
            <td>POTENTIAL DAMAGE (Resistant Structures)</td>
            <td>Not exposed</td>
            <td>None</td>
            <td>None</td>
            <td>None</td>
            <td>Very Light</td>
            <td>Light</td>
            <td>Moderate</td>
            <td>Moderate to Heavy</td>
            <td>Heavy</td>
            <td>Very Heavy</td>
        </tr>
        <tr>
            <td>POTENTIAL DAMAGE (Vulnerable Structures)</td>
            <td>Not exposed</td>
            <td>None</td>
            <td>None</td>
            <td>None</td>
            <td>Light</td>
            <td>Moderate</td>
            <td>Moderate to Heavy</td>
            <td>Heavy</td>
            <td>Very Heavy</td>
            <td>Very Heavy</td>
        </tr>
        <tr>
            <td>NUMBER OF EXPOSED SITES</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
        </tr>
        <tr>
            <td>INSURED VALUES (k€)</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
        </tr>
        </table>
        """.format(
            sum(1 for mmi in mmi_sites if mmi == 0),
            sum(1 for mmi in mmi_sites if (mmi>0 and mmi <= 1)),
            sum(1 for mmi in mmi_sites if (mmi > 1 and mmi<=3)),
            sum(1 for mmi in mmi_sites if (mmi > 3 and mmi<=4)),
            sum(1 for mmi in mmi_sites if (mmi > 4 and mmi<=5)),
            sum(1 for mmi in mmi_sites if (mmi > 5 and mmi<=6)),
            sum(1 for mmi in mmi_sites if (mmi > 6 and mmi<=7)),
            sum(1 for mmi in mmi_sites if (mmi > 7 and mmi<=8)),
            sum(1 for mmi in mmi_sites if (mmi > 8 and mmi<=9)),
            sum(1 for mmi in mmi_sites if (mmi > 9)),
            round(sum(value for mmi, value in zip(mmi_sites, values) if mmi == 0) / 10**3, 1),
            round(sum(value for mmi, value in zip(mmi_sites, values) if (mmi>0 and mmi <= 1)) / 10**3, 1),
            round(sum(value for mmi, value in zip(mmi_sites, values) if (mmi>1 and mmi <= 3)) / 10**3, 1),
            round(sum(value for mmi, value in zip(mmi_sites, values) if (mmi>3 and mmi <= 4)) / 10**3, 1),
            round(sum(value for mmi, value in zip(mmi_sites, values) if (mmi>4 and mmi <= 5)) / 10**3, 1),
            round(sum(value for mmi, value in zip(mmi_sites, values) if (mmi>5 and mmi <= 6)) / 10**3, 1),
            round(sum(value for mmi, value in zip(mmi_sites, values) if (mmi>6 and mmi <= 7)) / 10**3, 1),
            round(sum(value for mmi, value in zip(mmi_sites, values) if (mmi>7 and mmi <= 8)) / 10**3, 1),
            round(sum(value for mmi, value in zip(mmi_sites, values) if (mmi>8 and mmi <= 9)) / 10**3, 1),
            round(sum(value for mmi, value in zip(mmi_sites, values) if (mmi>9)) / 10**3, 1)
        )

        # Afficher le tableau HTML dans Streamlit
        st.markdown(html_table, unsafe_allow_html=True)



