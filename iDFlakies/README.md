# iDFlakies Data Collection and Cleaning

This directory contains the data collection, execution tracking, and cleaning process used to derive a flaky-test dataset from iDFlakies.

## Data Source

iDFlakies is a framework for detecting and partially classifying flaky tests and the framework uses a different test-order configuration logic, identifying tests whose results change based on the order of execution.

The dataset consists of 683 project CSV files divided into two sets, comprehensive and extended:

| Dataset Split | Projects | Description |
|---|---:|---|
| Comprehensive | 183 | Projects evaluated using multiple iDFlakies detector configurations |
| Extended | 500 | Additional projects evaluated using the Random Class + Method (C+M) configuration |


The **Comprehensive split** was selected as multiple detections were applied to these runs, and allowed more information for the detection, such as the number of unique detectors used to identify whether the test is flaky or not.

## Directory Structure

```text
iDFlakies/
├── cleaned_data/
│   └── idflakies_clean.csv
├── logs/
│   └── project_run_status.csv
├── notebooks/
│   └── iDFlakies_cleaning.ipynb
├── project_lists/
│   └── comprehensive_projects.txt
├── scripts/
│   └── run_projects.py
└── README.md