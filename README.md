# Colbert Ticket Bot

A simple program that automates finding and registering for tickets to the
Colbert Report using their web site.

## Requirements

To run this program, you'll need:

  * a working Python 2 environment
  * Google Chrome Web Browser
  * ChromeDriver

## Setup

To run the program, you just need to install the dependencies. This should be
as simple as running:

pip install -r requirements.txt

## Configuration

To configure the application, you can use the supplied config.ini-example.
Just edit the config to reflect values relevant to you and rename it to
config.ini. Once you do this, you should be ready to run the bot.

## Running

To run the bot program, you just need to run the main.py file:

python main.py

The bot will search for tickets based on the information you provided in the
config file, and will stop once it has successfully registered for tickets. It
will also take a screenshot of the state of the application immediately 
following registration for your reference.
