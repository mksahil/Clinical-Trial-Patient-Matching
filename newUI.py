import streamlit as st
import pandas as pd
import seaborn as sns
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from newMain import Patient_matching_criteria, get_criteria_list, get_patient_ids, get_trial_info, getstudydata


score = [23, 27, 33, 44, 11, 22, 25, 27, 31]

score_series = pd.Series(score)


score_counts = score_series.value_counts().sort_index()

# inclusion_df = pd.DataFrame(inclusion_criteria_list, columns=['Inclusion Criteria'])

# exclusion_df = pd.DataFrame(exclusion_criteria_list, columns=['Exclusion Criteria'])
# exclusion_df = exclusion_df.drop(index=1)  
# exclusion_df = exclusion_df.reset_index(drop=True)  
st.set_page_config(layout="wide")
st.markdown("""
        <style>
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                    padding-left: 1rem;
                    padding-right: 5rem;
                }
        </style>
        """, unsafe_allow_html=True)
cola, colb = st.columns([1, 2])

logo_url = r'C:\Users\mkathewadi\Downloads\streamlit\streamlit\intuceoLogo.png'

st.image(logo_url,width=200)
# Streamlit app

st.subheader('CLINICAL TRIAL MATCHING')

# Tabs
tabs = ["Patients Matching",  "Dashboard"]
tab1, tab2 = st.tabs(tabs)
patient_ids = get_patient_ids()
top100_patient_ids=patient_ids[0:100]
patient_json=Patient_matching_criteria(top100_patient_ids)
df = pd.DataFrame(patient_json)
df2=df[['LAT', 'LON']].astype(float)

studydf=getstudydata()

with tab1:
    with st.sidebar:    
        official_title='Investigating the Effects of Palmitoylethanolamide (PEA) on Stress, Craving and Pain in Opioid Use Disorder'

        nct_id = st.text_input("Enter NCT ID")
        Search_button = st.button("Search")  
        # if not nct_id:  
        #      st.error("Please enter an NCT ID!", icon="🚨")  
     #    inclusion_criteria, exclusion_criteria,disease,Official_title=get_trial_info(nct_id)
        inclusion_criteria_list=['- Age 18 to 65',
 '- DSM-5 diagnosis of Opioid Use Disorder (OUD)',
 '- English speaking',
 '- Receiving either buprenorphine or methadone for treatment of OUD for at least 3 consecutive months prior to enrollment',
 '- Receiving a stable dose of buprenorphine or methadone for the duration of the study',
 '- Agreeable to abstaining from using any cannabis or CBD products two weeks prior to enrollment in the study, and for the duration of the trial',
 '- For women of childbearing potential: agreeable to use one of the following: hormonal methods, barrier methods used with a spermicide, intrauterine device (IUD), or abstinence.']


        exclusion_criteria_list=['- DSM-5 diagnosis of moderate-to-severe cannabis use disorder, alcohol use disorder, and/or psychostimulant use disorder.',
 '- Active, recurrent substance use within the last 3 months.',
 '- History of psychotic, bipolar, and schizoaffective disorders.',
 '- Lifetime psychiatric hospitalization or suicide attempt.',
 '- Recent history (within 2 years) of major depressive disorder.',
 '- Currently pregnant or breastfeeding (female only).',
 "- History of autoimmune or chronic inflammatory diseases and current use of medications known to alter inflammatory and immune response, including Raynaud's disease.",
 '- BMI greater than 45.',
 '- Hepatic liver enzymes greater than 3 times the upper normal limit.',
 '- Vital signs outside the range: HR ≤60 or ≥100, SBP ≤90 or ≥160, DBP ≤50 or ≥100, RR < 12 or > 20.',
 '- Recent history of clinically significant medical conditions such as malignancy, HIV, and uncontrolled immunological, endocrine, renal, GI, or hematological abnormalities.']

     #    inclusion_criteria_list=get_criteria_list(inclusion_criteria)
     #    exclusion_criteria_list=get_criteria_list(exclusion_criteria)
        inclusion_df = pd.DataFrame(inclusion_criteria_list, columns=['Inclusion Criteria'])
        exclusion_df = pd.DataFrame(exclusion_criteria_list, columns=['Exclusion Criteria'])
        
        if Search_button or nct_id :
              if not nct_id:  
                 st.error("Please enter NCT ID!", icon="🚨") 
              else:
                 st.write("Study Title:",official_title) 
                 st.session_state["submit"] = True  
                 with st.spinner(text="Extracting Criteria..."): 
                   st.dataframe(inclusion_df)
                   st.dataframe(exclusion_df) 
        
    match_button = st.button("Match Patients")         
    if match_button:   
             st.session_state["submit"] = True  
             with st.spinner(text="Matching Patients..."):  
                 patient_ids = get_patient_ids()
                 top100_patient_ids=patient_ids[0:1100]
                 patient_json=Patient_matching_criteria(top100_patient_ids)
                 df = pd.DataFrame(patient_json)     
                 st.write("Matching 290/100")
                 df=df.astype(str)
                #  df.set_index('Id', inplace=True)
                 st.success('matching complete.') 
                 with st.expander("Matched Patients"):
                   st.dataframe(df) 
                 with st.expander("Structured study data"):
                   st.dataframe(studydf)  
                
with tab2:
    col7, col8 = st.columns([3, 1])  # The numbers represent the proportion of the column widths  
    if match_button: 

     with col7:  
        st.subheader("Dashboard")  
        st.write("Matches: 26/100")
     with col8:  
        st.write("Study Title:")
        st.write(official_title)  
        
        
# Gender Comparison Data
     gender_counts = df['GENDER'].value_counts()
     gender_labels = gender_counts.index 
     gender_sizes = gender_counts.values
     gender_colors = ['lightblue', 'blue']
# Race Comparison Data
     race_counts = df['RACE'].value_counts()
     race_labels = race_counts.index  
     race_sizes = race_counts.values
     race_colors = ['green', 'lightgreen', 'gray']  # Added gray for any additional race categories

# Creating Gender Comparison Pie Chart
     fig1, ax1 = plt.subplots(figsize=(2, 2))
     ax1.pie(gender_sizes, labels=gender_labels, autopct='%1.1f%%', colors=gender_colors, startangle=60, radius=0.7,textprops={'fontsize': 4})  # Adjust radius value
     ax1.set_title('Gender Comparison', fontsize=5)

# Creating Race Comparison Pie Chart
     fig2, ax2 = plt.subplots(figsize=(3, 3))
     ax2.pie(race_sizes, labels=race_labels, autopct='%1.1f%%', colors=race_colors, startangle=60, radius=0.7,textprops={'fontsize': 4})  # Adjust radius value
     ax2.set_title('Race Comparison',fontsize=7)

# Plotting Age Profile
     fig3, ax3 = plt.subplots(figsize=(10, 4))

# Counting occurrences of each age


# Sample data creation (replace this with your actual data)
     # data = {'AgeYears': [23, 25, 22, 45, 47, 50, 10, 15, 14, 35, 37, 40]}
     # df = pd.DataFrame(data)
     df['Age'] = pd.to_numeric(df['Age'], errors='coerce')

# Drop rows with NaN values resulting from coercion
     df.dropna(subset=['Age'], inplace=True)
# Define age bins
     bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
     labels = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90-100']

# Bin the ages
     df['AgeRange'] = pd.cut(df['Age'], bins=bins, labels=labels, right=False)

# Count occurrences in each age range
     age_range_counts = df['AgeRange'].value_counts().sort_index()

# Create the plot   
     fig, ax3 = plt.subplots(figsize=(10, 6))
     sns.barplot(x=age_range_counts.index, y=age_range_counts.values, ax=ax3)

# Customize the plot
     ax3.set_title('Age Profile', fontsize=20)
     ax3.set_xlabel('Age Range', fontsize=12)
     ax3.set_ylabel('Number of Individuals', fontsize=12) 
     ax3.grid(axis='y')

# Show the plot
     plt.show()

    # Plotting Age Profile
     fig4, ax4 = plt.subplots(figsize=(10, 4))

# Counting occurrences of each age
     age_counts = score_counts.value_counts().sort_index()
     sns.barplot(x=score_counts.index, y=score_counts.values, ax=ax3)
     ax4.set_title('Score Distribution for patient ranking', fontsize=20)
     ax4.set_xlabel('Rank', fontsize=12)
     ax4.set_ylabel('distribution', fontsize=12)
     ax4.grid(axis='y')
     col3, col4 = st.columns(2)

# Display the charts in Streamlit  
     with col3:
      st.pyplot(fig1)
      st.pyplot(fig3)
     with col4: 
      st.pyplot(fig2)
      st.pyplot(fig4)
     col10 = st.columns(1)[0]  
     with col10:
      st.subheader("Geographical Spread of Patients")
      st.map(df2, use_container_width=True,color="#ff073a")  
     
