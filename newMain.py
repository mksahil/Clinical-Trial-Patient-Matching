import json
from sqlalchemy import create_engine, text
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import pandas as pd
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts.pipeline import PipelinePromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI
import json
import pandas as pd
import requests
import os
from urllib.parse import quote  
import aiohttp  
import asyncio  

# Define the connection string
connection_string="mssql+pymssql://ctuser:Icubecs1@ctmatchingserver.database.windows.net/clinical_trials"

# Create the engine
engine = create_engine(connection_string)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a session
session = Session()

llm=AzureChatOpenAI(    
    azure_deployment="GPT4",
    api_key="af6c5f2c43294f1e9287a50d652c637e",
    model="gpt-4",
    api_version="2024-02-01",
    azure_endpoint="https://ctmatchinggpt.openai.azure.com/",
    temperature=0,
    )


# Extract
def get_trial_info(nct_id):
    url="https://clinicaltrials.gov/api/v2/studies/" + nct_id + ""
    response = requests.get(url)
    data = response.json()
    
    official_titel=data['protocolSection']['identificationModule']['officialTitle']
    criteria = data['protocolSection']['eligibilityModule']['eligibilityCriteria']
# print(criteria)
    inclusion_criteria = criteria.split("Inclusion Criteria:")[1].split("Exclusion Criteria")[0]
# print(inclusion_criteria)
    exclusion_criteria = criteria.split("Exclusion Criteria:")[1]   

    return inclusion_criteria, exclusion_criteria, official_titel


def get_criteria_list(crit):
    #Creating the prompt template that takes input_variable x_crit with value crit. Crit is the raw text of either inclusion or exclusion criteria
    prompt_template = "Please list (in bullets) all the criteria from text below. Please removing any nested details and combining related points into a single, concise statement where applicable. \n\n [CRITERIA]: \n{x_crit}"
    prompt = PromptTemplate(input_variables = [], template=prompt_template)
    chain = LLMChain(llm=llm, prompt=prompt) 
    #creating the criteria, which is a string of the criteria
    criteria = chain.invoke(input= {"x_crit": crit})
    #splitting the criteria into a list of criteria
    criteria_list = criteria['text'].split("\n")
    return criteria_list


# Matching
def inclusion_criteria_check(patient_codes, study_inclusion_codes):  
    inclusion_count = 0
    for patient_code in patient_codes:
        if patient_code in study_inclusion_codes:
            inclusion_count += 1 
    # print("inclusion_count ",inclusion_count)
    inclusion_count=inclusion_count+2    
    if inclusion_count >= 1:
        return True,inclusion_count
    else:
        return False,inclusion_count
    # return bool(patient_codes.intersection(study_inclusion_codes))  
  
def exclusion_criteria_check(patient_codes, study_exclusion_codes):  
    exclusion_count=0
    for study_ex_code in study_exclusion_codes:
        if study_ex_code not in patient_codes:
            # print("study_ex_code ",study_ex_code)
            # print("patient_codes ",patient_codes)
            exclusion_count += 1
    # print('exclusion_count',exclusion_count)        
    if exclusion_count >= 22:
        return True, exclusion_count//3
    else:
        return False, exclusion_count//3


def get_study_codes_set(study_type, studytable_name):
    query = f'''
    SELECT conceptid
    FROM {studytable_name}
    WHERE Type = :study_type AND conceptid IS NOT NULL
    '''
    
    with engine.connect() as connection:
        result = connection.execute(text(query), {"study_type": study_type})
        concept_ids = {row[0] for row in result.fetchall()}

    return concept_ids
 
# Now you can use these functions like this:  
study_inclusion_codes = get_study_codes_set('Inclusion', 'StudyData')
study_exclusion_codes = get_study_codes_set('Exclusion', 'StudyData')


from uuid import UUID
def get_demographics(tablename):
    query = f'''
    SELECT s.Attribute, s.Value
    FROM {tablename} s
    WHERE Entity = 'Demographic'
    '''
    with engine.connect() as connection:
        result = connection.execute(text(query))
        patient_demographics = {row[0]: row[1] for row in result.fetchall()}
    return patient_demographics

def get_patient_codes_batch(patient_ids, demographics):  
    # Convert patient_ids to strings if they are not already  
    patient_ids = [str(patient_id) for patient_id in patient_ids]  
    patient_codes = {patient_id: set() for patient_id in patient_ids}  
    
   
    age_condition = demographics.get('Age', '')
    gender_condition = demographics.get('Gender', '')
    
  
    age_filter = ''
    if 'between' in age_condition.lower():
        age_range = age_condition.lower().replace('between', '').replace('years', '').split('and')
        age_filter = f"AND p.Age BETWEEN {age_range[0].strip()} AND {age_range[1].strip()}"
    elif '>=' in age_condition or '<=' in age_condition:
          parts = age_condition.replace('Years', '').strip().split('and')
          age_filter = f"AND p.Age {parts[0].strip()} AND p.Age  {parts[1].strip()}"

    gender_filter = ''
    if 'all' in gender_condition.lower():
        gender_filter ="and p.GENDER in ('f','m')"
    elif 'female' in gender_condition.lower():
        gender_filter ="and p.GENDER = 'f'"
    elif 'male' in gender_condition.lower():
        gender_filter ="and p.GENDER ='m'"
    
  
    query = f'''  
    SELECT p.Id, code
    FROM (
        SELECT c.PATIENT AS Id, c.code
        FROM conditions c
        UNION
        SELECT pr.PATIENT AS Id, pr.code
        FROM procedures pr
        UNION
        SELECT e.PATIENT AS Id, e.code
        FROM encounters e
        UNION
        SELECT m.PATIENT AS Id, m.code
        FROM medications m
    ) AS combined
    JOIN patients p ON combined.Id = p.Id
    WHERE p.Id IN :patient_ids
    {age_filter}
    {gender_filter}
    '''  
    
    with engine.connect() as connection:  
        # Convert the list of patient_ids to a tuple of UUIDs for the query  
        patient_id_uuids = tuple([UUID(patient_id) for patient_id in patient_ids])  
        result = connection.execute(text(query), {"patient_ids": patient_id_uuids})  
        for row in result.fetchall():  
            # Convert the UUID to a string for consistent handling  
            patient_id = str(row[0])  
            code = row[1]  
            patient_codes[patient_id].add(code)  
    
    return patient_codes  


def get_patient_details(patient_id):
    # Define the query to get patient details by patient_id
    query = '''
    SELECT Id,FIRST, LAST,RACE,GENDER, BIRTHPLACE,COUNTY,LAT,LON,Age
    FROM patients
    WHERE Id = :patient_id
    '''
        
    # Execute the query
    with engine.connect() as connection:
        result = connection.execute(text(query), {"patient_id": patient_id})
        patient_details = result.fetchone()
    
    # Convert the result to a dictionary
    if patient_details:
        patient_dict = {
            "Id": patient_details[0],
            "FIRST": patient_details[1],
            "LAST": patient_details[2],
            "RACE": patient_details[3],
            "GENDER": patient_details[4],
            "BIRTHPLACE": patient_details[5],
            "COUNTY": patient_details[6],
            "LAT": patient_details[7],  
             "LON": patient_details[8],  
            "Age": patient_details[9],        
        }
        return json.dumps(patient_dict, default=str)
    else:
        return json.dumps({"error": "Patient not found"})
    
demographics = get_demographics('studydata')    
def Patient_matching_criteria(patientlist):  
    patient_data_list = []  
    # Fetch study codes once  
    study_inclusion_codes = get_study_codes_set('Inclusion', 'StudyData')
    study_exclusion_codes = get_study_codes_set('Exclusion', 'StudyData')
    
    # Fetch patient codes in a batch  
    patient_codes_dict = get_patient_codes_batch(patientlist,demographics)  
    
    # Check inclusion and exclusion criteria for each patient in the batch  
    for patient_id in patientlist:  
        patient_codes = patient_codes_dict.get(patient_id, set())
        # print("patient_codes", patient_codes)  
        inclu_check,inclu_count = inclusion_criteria_check(patient_codes, study_inclusion_codes)
        exclu_check,exclu_count = exclusion_criteria_check(patient_codes, study_exclusion_codes)
        if inclu_check and  exclu_check and patient_codes:
            patient_details = get_patient_details(patient_id)  
            data = json.loads(patient_details) 
            data['inclusion_count']=inclu_count
            data['exclusion_count']=exclu_count
            # print("data", data) 
            patient_data_list.append(data) 

            # print("patient_data_list", patient_data_list)
        # print(patient_id, inclu_check, exclu_check, inclu_count, exclu_count)
    return patient_data_list 



def get_patient_ids():
   
    query = '''
    SELECT Id
    FROM Patients
    '''
    # Execute the query
    with engine.connect() as connection:
        result = connection.execute(text(query))
        patient_ids = [str(row[0]) for row in result.fetchall()]
    return patient_ids


# Example usage
patient_ids = get_patient_ids()

top100_patient_ids=patient_ids


def getstudydata():
    df2=pd.read_csv(r'C:\Users\mkathewadi\Downloads\streamlit\streamlit\StudyData.csv')
    return df2