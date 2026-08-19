# Recreation.gov Permit Availability Checker
This project is intended to help in checking and notifying an individual about the availability of permits that can be obtained at recreation.gov.

It uses light HTTP GET polling of a JSON API endpoint, and sends notifications via a Discord webhook when permits become available.

## Permit Polling Configuration
To configure a specific permit polling instance, copy config.example.json as config.json, add your dates of interest, your discord webhook URL, and set up the permit ID (this is given in the URL of the permit page on recreation.gov).

Mt St Helens example:
https://www.recreation.gov/permits/4675309


## Webhook Setup
To create a Discord webhook, you must have a Discord server with admin privileges.
Then follow: channel settings > integrations > webhooks, to create a webhook.

## Setting up the automated tasks
On Windows you can use `Task Scheduler` to create a scheduled task that runs the Python script at regular intervals.

To locate your Python executable use `where python` in command prompt or `where.exe python` in PowerShell.

Set up an action with:

Program: `Python executable path`
Arguments: `Path to the recwatch python script`

You can then set up a trigger to have it poll at regular (15 min or 1 hr) intervals.