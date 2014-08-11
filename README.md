# Colbert Ticket Bot

A simple program that automates finding and registering for tickets to the
Colbert Report using their web site.

## Why?

There is already a twitter feed Spiffomatic64, or @DailyTix, that provides
a real-time view of available tickets for the Colbert Report and the Daily
Show. What purpose does this serve?

Well, after a number of attempts to snag tickets by clicking the link
and filling out the form only to see that the tickets were already taken,
I decided to change my strategy. Colbert tickets seem to be more scarce, 
and while the twitter feed is helpful in identifying when there are tickets,
with an average delay of 1/2 its polling interval, it didn't help to 
registering for the tickets. I needed a seeker-missile or a ninja-sniper.

This program uses a real browser to not only identify when tickets are 
available, but it immediately register for them at computer-speeds. Armed with
this program I got tickets for the time I wanted, the first time, and without
having to monitor twitter. 


## Requirements

To run this program, you'll need:

  * A working Python 2 environment
  * Google Chrome Web Browser
  * [ChromeDriver](https://code.google.com/p/selenium/wiki/ChromeDriver)

## Setup

To run the program, you just need to install the dependencies. This should be
as simple as running:

```
pip install -r requirements.txt
```

## Configuration

To configure the application, you can use the supplied config.ini-example.
Just edit the config to reflect values relevant to you and rename it to
config.ini. Once you do this, you should be ready to run the bot.

## Running

To run the bot program, you just need to run the main.py file:

```
python main.py
```

The bot will search for tickets based on the information you provided in the
config file, and will stop once it has successfully registered for tickets. It
will also take a screenshot of the state of the application immediately 
following registration for your reference.
