import numpy as np
import streamlit as st
from wordcloud import STOPWORDS, WordCloud
import utils.whatsapp_analysis_utils as whatsapp_analysis_utils
import altair as alt
from PIL import Image

st.set_page_config(page_title="Analizador", page_icon="🏠")
st.title("Analizador de WhatsApp")

def bar_chart_horizontal(data, x_column, y_column):
    # Horizontal stacked bar chart
    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(x_column, type="quantitative", title=""),
            y=alt.Y(y_column, type="nominal", title="", sort="-x")
        )
        .configure_mark(
            color='#FF4B4B'
        )
    )

    st.altair_chart(chart, theme="streamlit", use_container_width=True)

    
def stacked_bar_chart_horizontal(data, x_column, y_column, group_by, categories_grouped, color_categories_grouped = ['#FF4B4B', '#901d39', '#7d162b', '#6b0f1d', '#58070e', '#450000']):
    # Horizontal stacked bar chart
    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(x_column, type="quantitative", title=""),
            y=alt.Y(y_column, type="nominal", title="", sort="-x"),
            # color=group_by,
            color=alt.Color(
                group_by,
                scale = alt.Scale(
                    domain=categories_grouped, 
                    range=color_categories_grouped
                )
            ),
            order=alt.Order(
                # Sort the segments of the bars by this field
                group_by,
                sort='descending'
            )
        )
        .configure_mark(
            color='#FF4B4B, #FFF',

        )
    )

    st.altair_chart(chart, theme="streamlit", use_container_width=True)

st.subheader("Para iniciar este analisis, cargue el archivo TXT generado por whastapp cuando se exporta la conversación")
st.write("Psst.. Está información no se almacena en ningún lugar (No te preocupes 😉)")

uploaded_file = st.file_uploader("Your chat file", label_visibility="hidden", accept_multiple_files=False)

if uploaded_file is not None:

    df = whatsapp_analysis_utils.transform_file_to_data_frame(uploaded_file)

    st.subheader('Los mensajes que se han enviado se dividen en los siguientes tipos... 🙄')
    df_messages_types = whatsapp_analysis_utils.get_message_types(df)

    tab1, tab2 = st.tabs(["Chart", "Details"])
    with tab1:
        bar_chart_horizontal(
            df_messages_types[df_messages_types['Tipo'] != "Mensajes"],
            "Cantidad",
            "Tipo"
            )
    
    with tab2:
        df_messages_types

    st.subheader('Los mensajes que se han enviado se dividen en los siguientes emojis... 🙄')
    df_emojis = whatsapp_analysis_utils.get_emojis_count(df)

    tab1, tab2 = st.tabs(["Chart", "Details"])
    with tab1:
        bar_chart_horizontal(
            df_emojis.head(10),
            "Cantidad",
            "Emoji"
        )
    
    with tab2:
        df_emojis

    
    st.subheader('El miembro más activo es... 🙄')
    member_most_active = whatsapp_analysis_utils.get_members_by_messages_count(df)

    tab1, tab2 = st.tabs(["Chart", "Details"])
    with tab1:
        
        html_string =f'''
        <div style="
            border: 1px gray solid;
            border-radius: 5px;
            padding: 2rem 1rem;
            margin-bottom: 1rem;
            ">
            <h3 style="color: #FF4B4B; padding:0;">
                {member_most_active.head(1)["Mensaje"].iloc[0]:,}
            </h3>
             mensajes enviados por 
             <br>
             <strong style="color: #FF4B4B;">{member_most_active.head(1)["Miembro"].iloc[0]}</strong>
        </div>
        '''
        st.markdown(html_string, unsafe_allow_html=True)
    
    with tab2:
        member_most_active
    

    st.subheader('Estadisticas por miembro... 🙄')

    tab1, tab2, tab3 = st.tabs(["Tipo de mensajes", "Palabras por mensaje", "Details"])
    statics_by_member = whatsapp_analysis_utils.get_statics_by_member(df)
    with tab1:
        unpivoted_data = statics_by_member.melt(
            id_vars="Miembro", 
            value_vars=['Multimedia','Emojis','Links', 'Tiktoks'],
            var_name='Medida',
            value_name='Valor'
            )

        stacked_bar_chart_horizontal(unpivoted_data, "Valor", "Miembro", "Medida", ['Multimedia', 'Emojis', 'Links', 'Tiktoks'])

    with tab2:
        bar_chart_horizontal(
            statics_by_member[["Miembro", "Palabras por mensaje"]],
            "Palabras por mensaje",
            "Miembro"
        )

    with tab3:
        statics_by_member

    
    st.subheader('Analisis por tiempo... 🙄')

    analysis_by_hour_range = whatsapp_analysis_utils.get_analysis_by_hour_range(df)
    analysis_by_days = whatsapp_analysis_utils.get_analysis_by_day(df)

    tab1, tab2, tab3, tab4 = st.tabs(["Rangos de hora (Chart)", "Rangos de hora (Details)", "Días (Chart)", "Días (Details)"])
    with tab1:
        st.line_chart(analysis_by_hour_range, x="rangoHora", y="# Mensajes por hora", color="#FF4B4B")
    with tab2:
        analysis_by_hour_range

    with tab3:
        st.line_chart(analysis_by_days, x="Fecha", y="# Mensajes por día", color="#FF4B4B")
    with tab4:
        analysis_by_days

    
    st.subheader('Palabras más usadas... 🙄')
    words_most_used = whatsapp_analysis_utils.words_most_used(df)
    
    mask = np.array(Image.open('static/circle.jpg'))
    wordcloud = WordCloud(width = 800, height = 800,
                background_color ='black',
                stopwords = STOPWORDS,
                min_font_size = 5,
                max_words=1000, 
                colormap='OrRd',
                mask = mask).generate(words_most_used)

    # Plotear la nube de palabras más usadas
    st.image(wordcloud.to_array())