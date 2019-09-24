import copy
import json
import os
import time
import pandas


from simtools.Analysis.AnalyzeManager import AnalyzeManager
from simtools.Analysis.BaseAnalyzers.DownloadAnalyzerTPI import DownloadAnalyzerTPI


#from CustomDownloadAnalyzerTPI import CustomDownloadAnalyzerTPI
from dtk.utils.builders.ConfigTemplate import ConfigTemplate
from dtk.utils.builders.TaggedTemplate import CampaignTemplate, DemographicsTemplate
from dtk.utils.builders.TemplateHelper import TemplateHelper
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
#from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder
from simtools.SetupParser import SetupParser
from simtools.Utilities.COMPSUtilities import COMPS_login
from simtools.Utilities.COMPSUtilities import create_suite
from simtools.Utilities.Matlab import read_mat_points_file



############# SET THESE: ########################
suite_name = 'Nyanza_PrEP_v5_perturb_rand_trajectories'
output_directory = "Nyanza_PrEP_v5_perturb_rand_trajectories"
tpi_matlab_filename = 'resample_mat_files/recalib_30_40_50/Nyanza_30_40_50_iter174.mat'
#################################################

SetupParser.default_block = 'HPC'

# Unused parameters to remove
unused_params = [
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.TRANSITORY.Concurrency_Parameters.MEDIUM.Prob_Extra_Relationship_Female',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.INFORMAL.Concurrency_Parameters.LOW.Max_Simultaneous_Relationships_Female',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.MARITAL.Concurrency_Parameters.MEDIUM.Max_Simultaneous_Relationships_Male',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.INFORMAL.Concurrency_Parameters.LOW.Prob_Extra_Relationship_Female',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.INFORMAL.Concurrency_Parameters.MEDIUM.Max_Simultaneous_Relationships_Male',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.TRANSITORY.Concurrency_Parameters.LOW.Max_Simultaneous_Relationships_Female',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.MARITAL.Concurrency_Parameters.MEDIUM.Max_Simultaneous_Relationships_Female',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.TRANSITORY.Concurrency_Parameters.LOW.Prob_Extra_Relationship_Female',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.TRANSITORY.Concurrency_Parameters.MEDIUM.Prob_Extra_Relationship_Male',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.TRANSITORY.Concurrency_Parameters.MEDIUM.Max_Simultaneous_Relationships_Female',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.INFORMAL.Concurrency_Parameters.MEDIUM.Max_Simultaneous_Relationships_Female',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.INFORMAL.Concurrency_Parameters.MEDIUM.Prob_Extra_Relationship_Male',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.TRANSITORY.Concurrency_Parameters.LOW.Max_Simultaneous_Relationships_Male',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.TRANSITORY.Concurrency_Parameters.LOW.Prob_Extra_Relationship_Male',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.INFORMAL.Concurrency_Parameters.LOW.Prob_Extra_Relationship_Male',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.INFORMAL.Concurrency_Parameters.MEDIUM.Prob_Extra_Relationship_Female',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.TRANSITORY.Concurrency_Parameters.MEDIUM.Max_Simultaneous_Relationships_Male',
 'DEMOGRAPHICS.Society__KP_Defaults_All_Nodes.INFORMAL.Concurrency_Parameters.LOW.Max_Simultaneous_Relationships_Male',
 'CONFIG.Run_Number'
]


def header_table_to_dict(header, table, index_name=None):
    df = pandas.DataFrame(data=table, columns=header)
    # Drop unused columns
    for unused in unused_params:
        if unused in df.columns: df.drop(unused, 1, inplace=True)
    if index_name:
        df[index_name] = df.index

    return json.loads(pandas.json.dumps(df.to_dict(orient='records')))

# Create the base path
current_dir = os.path.dirname(os.path.realpath(__file__))
plugin_files_dir = os.path.join(current_dir,'Templates_Nyanza')

# Load the base config file
config = ConfigTemplate.from_file(os.path.join(plugin_files_dir, 'Configs', 'config.json'))
config.set_param("Enable_Demographics_Builtin", 0, allow_new_parameters=True)

# Load the campaigns
cpnFT = CampaignTemplate.from_file(os.path.join(plugin_files_dir, 'Campaigns', 'campaign_NyanzaPrEP_StatusQuo_TROUBLESHOOTING.json'))
cpnSQ = CampaignTemplate.from_file(os.path.join(plugin_files_dir, 'Campaigns', 'campaign_NyanzaPrEP_StatusQuo.json'))
campaigns = {"cpnFT":cpnFT, "cpnSQ":cpnSQ}

# Load the demographics
demog = DemographicsTemplate.from_file( os.path.join(plugin_files_dir, 'Demographics', 'Demographics.json'))
demog_pfa = DemographicsTemplate.from_file( os.path.join(plugin_files_dir, 'Demographics', 'PFA_Overlay.json'))
demog_acc = DemographicsTemplate.from_file( os.path.join(plugin_files_dir, 'Demographics', 'Accessibility_and_Risk_IP_Overlay.json'))
demog_asrt = DemographicsTemplate.from_file( os.path.join(plugin_files_dir, 'Demographics', 'Risk_Assortivity_Overlay.json'))

# Load the scenarios
# Note -- "Start_Year__KP__Baseline_PrEP_use_by_county" was set to 2017 for earlier runs
scenario_header = [
"Scenario",
"Campaign_Template",
"Start_Year__KP__Baseline_PrEP_use_by_county",
"Start_Year__KP__PrEP_Start_Year",
"Node_List__KP__PrEP_Node_List_to_Target",
"Property_Restrictions_Within_Node__KP__PrEP_Property_Restrictions",
"Target_Gender__KP__PrEP_Gender",
"Target_Age_Min__KP__PrEP_Age_Min",
"Target_Age_Max__KP__PrEP_Age_Max",
"Time_Value_Map__KP__RTEC_Coverage_PrEP.Times",
"Time_Value_Map__KP__RTEC_Coverage_PrEP.Values",
"Waning_Config__KP__PrEP.Durability_Map.Times",
"Waning_Config__KP__PrEP.Durability_Map.Values",
"Start_Year__KP__2016p75_To_Enable_Rand_Perturbation",
"Num_Targeted_Males__KP__To_Perturb_Random_Numbers_MALE",
"Num_Targeted_Males__KP__To_Perturb_Random_Numbers_FEMALE"
]

scenarios = [
#["Counterfactual_perturb_rand_250",           "cpnSQ",2099,2099,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 250, 250],
#["Baseline_Nyanza_PrEP_perturb_rand_250",     "cpnSQ",2099,2017,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 250, 250],
["Counterfactual_perturb_rand_500",           "cpnSQ",2099,2099,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 500, 500],
["Baseline_Nyanza_PrEP_perturb_rand_500",     "cpnSQ",2099,2017,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 500, 500],
["Counterfactual_perturb_rand_750",           "cpnSQ",2099,2099,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 750, 750],
["Baseline_Nyanza_PrEP_perturb_rand_750",     "cpnSQ",2099,2017,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 750, 750],
["Counterfactual_perturb_rand_1000",           "cpnSQ",2099,2099,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 1000, 1000],
["Baseline_Nyanza_PrEP_perturb_rand_1000",     "cpnSQ",2099,2017,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 1000, 1000],
["Counterfactual_perturb_rand_1250",           "cpnSQ",2099,2099,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 1250, 1250],
["Baseline_Nyanza_PrEP_perturb_rand_1250",     "cpnSQ",2099,2017,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 1250, 1250],
["Counterfactual_perturb_rand_1500",           "cpnSQ",2099,2099,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 1500, 1500],
["Baseline_Nyanza_PrEP_perturb_rand_1500",     "cpnSQ",2099,2017,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 1500, 1500],
["Counterfactual_perturb_rand_1750",           "cpnSQ",2099,2099,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 1750, 1750],
["Baseline_Nyanza_PrEP_perturb_rand_1750",     "cpnSQ",2099,2017,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 1750, 1750],
["Counterfactual_perturb_rand_2000",           "cpnSQ",2099,2099,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 2000, 2000],
["Baseline_Nyanza_PrEP_perturb_rand_2000",     "cpnSQ",2099,2017,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 2000, 2000],
#["Counterfactual_perturb_rand_2250",           "cpnSQ",2099,2099,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 2250, 2250],
#["Baseline_Nyanza_PrEP_perturb_rand_2250",     "cpnSQ",2099,2017,[1,2,4,6],[],"All",15,29,[2020, 2099],[0,0],[0, 91, 92, 365],[0, 0, 0, 0], 2016.75, 2250, 2250],


# #["Comparator_OralConventional_All_Nyanza","cpnSQ",2020,[1,2,4,6],[],"All",15,29,[2020, 2099],[1,1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# #["Accept_OralConventional_All_Nyanza","cpnSQ",2020,[1,2,4,6],[],"All",15,29,[2020, 2099],[0.1, 0.1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Adhere_OralConventional_All_Nyanza","cpnSQ",2020,[1,2,4,6],[],"All",15,29,[2020, 2099],[0.1, 0.1],[0, 91, 92, 365],[0.36,0.36,0.36,0.36]],
# # ["Retain_OralConventional_All_Nyanza","cpnSQ",2020,[1,2,4,6],[],"All",15,29,[2020, 2099],[0.1, 0.1],[0, 91, 92, 365],[0.36,0.36,0,0]],
# # ["ReEngage_OralConventional_All_Nyanza","cpnSQ",2020,[1,2,4,6],[],"All",15,29,[2020, 2099],[0.1, 0.1],[0, 91, 92, 36500],[0.36,0.36,0,0]],
# # ["ScaleUp_OralInnovative_All_Nyanza","cpnSQ",2021,[1,2,4,6],[],"All",15,29,[2020, 2099],[1,1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Accept_OralInnovative_All_Nyanza","cpnSQ",2021,[1,2,4,6],[],"All",15,29,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
 # ["Adhere_OralInnovative_All_Nyanza","cpnSQ",2021,[1,2,4,6],[],"All",15,29,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 365],[0.61, 0.61, 0.61, 0.61]],
 # ["Retain_OralInnovative_All_Nyanza","cpnSQ",2021,[1,2,4,6],[],"All",15,29,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 365],[0.61,0.61,0,0]],
 # ["ReEngage_OralInnovative_All_Nyanza","cpnSQ",2021,[1,2,4,6],[],"All",15,29,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 36500],[0.61,0.61,0,0]],
# # ["ScaleUp_LongActing_All_Nyanza","cpnSQ",2023,[1,2,4,6],[],"All",15,29,[2023, 2025, 2099],[1,1,1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Accept_LongActing_All_Nyanza","cpnSQ",2023,[1,2,4,6],[],"All",15,29,[2023, 2025, 2099],[0,0.5,0.5],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Retain_LongActing_All_Nyanza","cpnSQ",2023,[1,2,4,6],[],"All",15,29,[2023, 2025, 2099],[0,0.5,0.5],[0, 91, 92, 365],[0.95, 0.95, 0, 0]],
# # ["ReEngage_LongActing_All_Nyanza","cpnSQ",2023,[1,2,4,6],[],"All",15,29,[2023, 2025, 2099],[0,0.5,0.5],[0, 91, 92, 36500],[0.95, 0.95, 0, 0]],
# # ["Comparator_OralConventional_AGYW_Nyanza","cpnSQ",2020,[1,2,4,6],[],"Female",15,24,[2020, 2099],[1,1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Accept_OralConventional_AGYW_Nyanza","cpnSQ",2020,[1,2,4,6],[],"Female",15,24,[2020, 2099],[0.1, 0.1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Adhere_OralConventional_AGYW_Nyanza","cpnSQ",2020,[1,2,4,6],[],"Female",15,24,[2020, 2099],[0.1, 0.1],[0, 91, 92, 365],[0.36,0.36,0.36,0.36]],
# # ["Retain_OralConventional_AGYW_Nyanza","cpnSQ",2020,[1,2,4,6],[],"Female",15,24,[2020, 2099],[0.1, 0.1],[0, 91, 92, 365],[0.36,0.36,0,0]],
# # ["ReEngage_OralConventional_AGYW_Nyanza","cpnSQ",2020,[1,2,4,6],[],"Female",15,24,[2020, 2099],[0.1, 0.1],[0, 91, 92, 36500],[0.36,0.36,0,0]],
# # ["ScaleUp_OralInnovative_AGYW_Nyanza","cpnSQ",2021,[1,2,4,6],[],"Female",15,24,[2020, 2099],[1,1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Accept_OralInnovative_AGYW_Nyanza","cpnSQ",2021,[1,2,4,6],[],"Female",15,24,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
 # ["Adhere_OralInnovative_AGYW_Nyanza","cpnSQ",2021,[1,2,4,6],[],"Female",15,24,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 365],[0.61, 0.61, 0.61, 0.61]],
 # ["Retain_OralInnovative_AGYW_Nyanza","cpnSQ",2021,[1,2,4,6],[],"Female",15,24,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 365],[0.61,0.61,0,0]],
 # ["ReEngage_OralInnovative_AGYW_Nyanza","cpnSQ",2021,[1,2,4,6],[],"Female",15,24,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 36500],[0.61,0.61,0,0]],
# # ["ScaleUp_LongActing_AGYW_Nyanza","cpnSQ",2023,[1,2,4,6],[],"Female",15,24,[2023, 2025, 2099],[1,1,1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Accept_LongActing_AGYW_Nyanza","cpnSQ",2023,[1,2,4,6],[],"Female",15,24,[2023, 2025, 2099],[0,0.5,0.5],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Retain_LongActing_AGYW_Nyanza","cpnSQ",2023,[1,2,4,6],[],"Female",15,24,[2023, 2025, 2099],[0,0.5,0.5],[0, 91, 92, 365],[0.95, 0.95, 0, 0]],
# # ["ReEngage_LongActing_AGYW_Nyanza","cpnSQ",2023,[1,2,4,6],[],"Female",15,24,[2023, 2025, 2099],[0,0.5,0.5],[0, 91, 92, 36500],[0.95, 0.95, 0, 0]],
# # ["Comparator_OralConventional_HighRiskWomen_Nyanza","cpnSQ",2020,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2020, 2099],[1,1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Accept_OralConventional_HighRiskWomen_Nyanza","cpnSQ",2020,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2020, 2099],[0.1, 0.1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Adhere_OralConventional_HighRiskWomen_Nyanza","cpnSQ",2020,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2020, 2099],[0.1, 0.1],[0, 91, 92, 365],[0.36,0.36,0.36,0.36]],
# # ["Retain_OralConventional_HighRiskWomen_Nyanza","cpnSQ",2020,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2020, 2099],[0.1, 0.1],[0, 91, 92, 365],[0.36,0.36,0,0]],
# # ["ReEngage_OralConventional_HighRiskWomen_Nyanza","cpnSQ",2020,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2020, 2099],[0.1, 0.1],[0, 91, 92, 36500],[0.36,0.36,0,0]],
# # ["ScaleUp_OralInnovative_HighRiskWomen_Nyanza","cpnSQ",2021,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2020, 2099],[1,1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Accept_OralInnovative_HighRiskWomen_Nyanza","cpnSQ",2021,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
 # ["Adhere_OralInnovative_HighRiskWomen_Nyanza","cpnSQ",2021,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 365],[0.61, 0.61, 0.61, 0.61]],
 # ["Retain_OralInnovative_HighRiskWomen_Nyanza","cpnSQ",2021,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 365],[0.61,0.61,0,0]],
 # ["ReEngage_OralInnovative_HighRiskWomen_Nyanza","cpnSQ",2021,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 36500],[0.61,0.61,0,0]],
# # ["ScaleUp_LongActing_HighRiskWomen_Nyanza","cpnSQ",2023,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2023, 2025, 2099],[1,1,1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Accept_LongActing_HighRiskWomen_Nyanza","cpnSQ",2023,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2023, 2025, 2099],[0,0.5,0.5],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Retain_LongActing_HighRiskWomen_Nyanza","cpnSQ",2023,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2023, 2025, 2099],[0,0.5,0.5],[0, 91, 92, 365],[0.95, 0.95, 0, 0]],
# # ["ReEngage_LongActing_HighRiskWomen_Nyanza","cpnSQ",2023,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Female",15,24,[2023, 2025, 2099],[0,0.5,0.5],[0, 91, 92, 36500],[0.95, 0.95, 0, 0]],
# # ["Comparator_OralConventional_HighRiskMen_Nyanza","cpnSQ",2020,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2020, 2099],[1,1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Accept_OralConventional_HighRiskMen_Nyanza","cpnSQ",2020,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2020, 2099],[0.1, 0.1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Adhere_OralConventional_HighRiskMen_Nyanza","cpnSQ",2020,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2020, 2099],[0.1, 0.1],[0, 91, 92, 365],[0.36,0.36,0.36,0.36]],
# # ["Retain_OralConventional_HighRiskMen_Nyanza","cpnSQ",2020,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2020, 2099],[0.1, 0.1],[0, 91, 92, 365],[0.36,0.36,0,0]],
# # ["ReEngage_OralConventional_HighRiskMen_Nyanza","cpnSQ",2020,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2020, 2099],[0.1, 0.1],[0, 91, 92, 36500],[0.36,0.36,0,0]],
# # ["ScaleUp_OralInnovative_HighRiskMen_Nyanza","cpnSQ",2021,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2020, 2099],[1,1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Accept_OralInnovative_HighRiskMen_Nyanza","cpnSQ",2021,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
 # ["Adhere_OralInnovative_HighRiskMen_Nyanza","cpnSQ",2021,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 365],[0.61, 0.61, 0.61, 0.61]],
 # ["Retain_OralInnovative_HighRiskMen_Nyanza","cpnSQ",2021,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 365],[0.61,0.61,0,0]],
 # ["ReEngage_OralInnovative_HighRiskMen_Nyanza","cpnSQ",2021,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2021, 2023, 2099],[0.1,0.3,0.3],[0, 91, 92, 36500],[0.61,0.61,0,0]],
# # ["ScaleUp_LongActing_HighRiskMen_Nyanza","cpnSQ",2023,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2023, 2025, 2099],[1,1,1],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Accept_LongActing_HighRiskMen_Nyanza","cpnSQ",2023,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2023, 2025, 2099],[0,0.5,0.5],[0, 91, 92, 365],[0.95, 0.95, 0.95, 0.95]],
# # ["Retain_LongActing_HighRiskMen_Nyanza","cpnSQ",2023,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2023, 2025, 2099],[0,0.5,0.5],[0, 91, 92, 365],[0.95, 0.95, 0, 0]],
# # ["ReEngage_LongActing_HighRiskMen_Nyanza","cpnSQ",2023,[1,2,3,4,5,6],[{"Risk": "HIGH"},{"Risk": "MEDIUM"}],"Male",20,29,[2023, 2025, 2099],[0,0.5,0.5],[0, 91, 92, 36500],[0.95, 0.95, 0, 0]]
]

# And the points
point_header, points = read_mat_points_file(tpi_matlab_filename)

# We only take the first 3 points. Comment the following line to run the whole 250 points
# points = points[0:3]

# Create the default config builder
config_builder = DTKConfigBuilder()

# Set which executable we want to use for the experiments in the script
#config_builder.set_experiment_executable('Eradication_2point7_20170405.exe')
#config_builder.set_experiment_executable('Eradication_Memory_Plus_GH826.exe')
config_builder.set_experiment_executable('EMOD_binary_20190402_broadcast_WouldHaveHadAIDS.exe')

# This is REQUIRED by the templates
config_builder.ignore_missing = True

# Get the dicts
points_dict = header_table_to_dict(point_header, points, index_name='TPI')
for point in points_dict:
    tpi = point.pop('TPI')
    if 'TAGS' not in point:
        point['TAGS'] = {}

    point['TAGS']['TPI'] = tpi

scenarios_dict = header_table_to_dict(scenario_header, scenarios)

if __name__ == "__main__":
    SetupParser.init()

    experiments = []      # All the experiment managers for all experiments
    experiments_ids = []  # Ids of the created experiments for resuming capabilities

    # Check if we want to resume
    if os.path.exists('ids.json'):
        print("Previous run detected... Run [N]ew, [R]esume, [A]bort?")
        resp = ""
        while resp not in ('N', 'R', 'A'):
            resp = input()
        if resp == "A":
            exit()
        elif resp == "R":
            # In the resume case, retrieve the ids and create the managers
            experiments_ids = json.load(open('ids.json', 'r'))
            for id in experiments_ids:
                experiments.append(ExperimentManagerFactory.from_experiment(str(id)))
        elif resp == "N":
            # Delete shelve file
            if os.path.exists('DownloadAnalyzerTPI.shelf'): os.remove('DownloadAnalyzerTPI.shelf')
            # Delete the ids
            os.remove('ids.json')

    # If experiment_ids is empty -> we need to commission
    if not experiments_ids:
        # Create a suite to hold all the experiments
        suite_id = create_suite(suite_name)

        # Create the scenarios
        for scenario in scenarios_dict:
            scenario_name = scenario['Scenario']
            campaign_tpl = campaigns[scenario.pop('Campaign_Template')]

            # For each scenario, combine with the points first
            combined = []
            for point in points_dict:
                current = {}
                current.update(scenario)
                current.update(point)
                combined.append(current)

            # Extract the headers
            headers = [k.replace('CONFIG.', '').replace('DEMOGRAPHICS.', '').replace('CAMPAIGN.', '') for k in combined[0].keys()]

            # Construct the table
            # table = [c.values() for c in combined] # OLD SYNTAX raises error TypeError: can't pickle dict_values objects
            table = [list(c.values()) for c in combined]

            # Change some things in the config.json
            config.set_param('Config_Name', scenario_name)

            # Initialize the template
            tpl = TemplateHelper()
            tpl.set_dynamic_header_table(headers, table)
            tpl.active_templates = [config, campaign_tpl, demog, demog_pfa, demog_asrt, demog_acc]

            # Create an experiment builder
            experiment_builder = ModBuilder.from_combos(tpl.get_modifier_functions())
            experiment_manager = ExperimentManagerFactory.from_cb(config_builder)
            COMPS_experiment_name = scenario_name
           # COMPS_experiment_name = suite_name # I want hover-over in COMPS to be the suite name
            
            experiment_manager.run_simulations(exp_name=COMPS_experiment_name, exp_builder=experiment_builder, suite_id=suite_id)
            experiments.append(experiment_manager)
            experiments_ids.append(experiment_manager.experiment.exp_id)

    # Dump the experiment ids for resume
    with open('ids.json', 'w') as out:
        json.dump(experiments_ids, out)

    # While the experiments are running, we are analyzing every 30 seconds
    while True:
        print("Analyzing !")

        # Determine if we are done at the beginning of the loop
        # We will still analyze everything even if we are done
        finished = all([em.finished() for em in experiments])

        # Create a new AnalyzeManager and add experiment and analyzer
        am = AnalyzeManager(verbose=False)
        for em in experiments:
            am.add_experiment(em.experiment)

        analyzer = DownloadAnalyzerTPI(filenames=['output\\ReportHIVByAgeAndGender.csv'],
                                       TPI_tag="TPI", ignore_TPI=False,
                                       REP_tag="TPI", ignore_REP=True,
                                       output_path=output_directory)




        am.add_analyzer(analyzer)

        # Make sure we refresh our set of experiments


        for e in experiments:
            e.refresh_experiment()
        COMPS_login(SetupParser.get("server_endpoint"))

        am.analyze()

        # If we are not done we wait for 30 sec, if we are done we leave
        if not finished:
            print("Waiting 30 seconds")
            time.sleep(30)
        else:
            break
