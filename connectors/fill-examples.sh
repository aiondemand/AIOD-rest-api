#!/bin/bash

python3 connectors/synchronization.py \
  -c connectors.example.example.ExampleCaseStudyConnector \
  -w /opt/connectors/data/example/case_study

python3 connectors/synchronization.py \
  -c connectors.example.example.ExampleContactConnector \
  -w /opt/connectors/data/example/contact

python3 connectors/synchronization.py \
  -c connectors.example.example.ExampleComputationalAssetConnector \
  -w /opt/connectors/data/example/computational_asset

python3 connectors/synchronization.py \
  -c connectors.example.example.ExampleEducationalResourceConnector \
  -w /opt/connectors/data/example/educational_resource

python3 connectors/synchronization.py \
  -c connectors.example.example.ExampleExperimentConnector \
  -w /opt/connectors/data/example/experiment

python3 connectors/synchronization.py \
  -c connectors.example.example.ExampleMLModelConnector \
  -w /opt/connectors/data/example/ml_model

python3 connectors/synchronization.py \
  -c connectors.example.example.ExampleNewsConnector \
  -w /opt/connectors/data/example/news

python3 connectors/synchronization.py \
  -c connectors.example.example.ExampleOrganisationConnector \
  -w /opt/connectors/data/example/organisation

python3 connectors/synchronization.py \
  -c connectors.example.example.ExamplePersonConnector \
  -w /opt/connectors/data/example/person

python3 connectors/synchronization.py \
  -c connectors.example.example.ExampleEventConnector \
  -w /opt/connectors/data/example/event

python3 connectors/synchronization.py \
  -c connectors.example.example.ExampleProjectConnector \
  -w /opt/connectors/data/example/project

python3 connectors/synchronization.py \
  -c connectors.example.example.ExamplePublicationConnector \
  -w /opt/connectors/data/example/publication

python3 connectors/synchronization.py \
  -c connectors.example.example.ExampleServiceConnector \
  -w /opt/connectors/data/example/service

python3 connectors/synchronization.py \
  -c connectors.example.example.ExampleTeamConnector \
  -w /opt/connectors/data/example/team

# Enums

python3 connectors/synchronization.py \
  -c connectors.example.enum.EnumConnectorApplicationArea \
  -w /opt/connectors/data/enum/application_area

python3 connectors/synchronization.py \
  -c connectors.example.enum.EnumConnectorEducationalResourceType \
  -w /opt/connectors/data/enum/educational_resource_type

python3 connectors/synchronization.py \
  -c connectors.example.enum.EnumConnectorEventMode \
  -w /opt/connectors/data/enum/event_mode

python3 connectors/synchronization.py \
  -c connectors.example.enum.EnumConnectorEventStatus \
  -w /opt/connectors/data/enum/event_status

python3 connectors/synchronization.py \
  -c connectors.example.enum.EnumConnectorLanguage \
  -w /opt/connectors/data/enum/language

python3 connectors/synchronization.py \
  -c connectors.example.enum.EnumConnectorLicense \
  -w /opt/connectors/data/enum/license

python3 connectors/synchronization.py \
  -c connectors.example.enum.EnumConnectorOrganisationType \
  -w /opt/connectors/data/enum/organisation_type

python3 connectors/synchronization.py \
  -c connectors.example.enum.EnumConnectorNewsCategory \
  -w /opt/connectors/data/enum/news_category

python3 connectors/synchronization.py \
  -c connectors.example.enum.EnumConnectorStatus \
  -w /opt/connectors/data/enum/status
