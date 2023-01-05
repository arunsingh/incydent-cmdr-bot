import os
import time

import slack
import pagerduty

# Obtain the Slack API key and initialize the Slack client
slack_api_key = os.environ["SLACK_API_KEY"]
slack_client = slack.WebClient(token=slack_api_key)

# Obtain the PagerDuty API key and initialize the PagerDuty client
pagerduty_api_key = os.environ["PAGERDUTY_API_KEY"]
pagerduty_client = pagerduty.Client(auth_token=pagerduty_api_key)

# Set up a Slack channel for incident-related messages
incident_channel = "#incidents"

# Set up a function to send a message to the incident channel
def send_message_to_incident_channel(message):
    slack_client.chat_postMessage(channel=incident_channel, text=message)

# Set up a function to create an incident in PagerDuty
def create_incident(summary, description):
    new_incident = pagerduty_client.incidents.create(
        type='incident',
        title=summary,
        body={"type": "incident_body", "details": description}
    )
    return new_incident['incident']['id']

# Set up a function to resolve an incident in PagerDuty
def resolve_incident(incident_id):
    pagerduty_client.incidents.update(id=incident_id, status='resolved')

# Set up a function to retrieve updates for an incident from PagerDuty
def get_incident_updates(incident_id):
    updates = pagerduty_client.incidents.get(id=incident_id)['incident']['notes']
    return updates

# Set up a function to parse incident-related messages from Slack
def parse_incident_message(message):
    summary = message['text'].split("\n")[0]
    description = message['text'].split("\n")[1:]
    return summary, description

# Set up a function to listen for incident-related messages in Slack
@slack_client.on(event='message')
def handle_incident_message(**payload):
    event = payload['event']
    if event['channel'] == incident_channel:
        summary, description = parse_incident_message(event)
        incident_id = create_incident(summary, description)
        send_message_to_incident_channel(f"Incident {incident_id} has been created!")
        while True:
            time.sleep(60)  # Check for updates every minute
            incident = pagerduty_client.incidents.get(id=incident_id)
            if incident['incident']['status'] == 'resolved':
                send_message_to_incident_channel(f"Incident {incident_id} has been resolved!")
                break
            else:
                updates = get_incident_updates(incident_id)
               

