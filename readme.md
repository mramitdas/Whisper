# TeleGram AnonymousChatBot

Intro
--------
This ChatBot is Telegram version of [omegle](http://www.omegle.com)

Dependancies 
-------------
In order to run this code you're supposed to have **python-telegram-bot**, **pymongo** and **pytz** libary installed
on your machine, you can just use *pip* command to this.

```bash
-> pip3 install -r requirements.txt
```

Bot WorkFlow
-----------

```mermaid
graph TD;
    A((Start)):::entryPoint --> |Bot Welcome Text|B{Action}

    B --> C1[Help]
    B --> C2{Settings}
    B --> C3{Find Partner}
    B --> C4{Share Profile}

    C1 --> C1A{{List of commands with usage}}

    C2 --> D[Set Gender]
    D --> D1[Set Your Gender]
    D --> D2[Set Partner's Gender]

    D1 --> E1[Male]
    D1 --> E2[Female]

    D2 --> E1[Male]
    D2 --> E2[Female]

    C3 --> |If: Gender selection done| C3A{Condition}
    C3A --> C3B1[NO]
    C3A --> C3B2[YES]

    C3B1 --> D
    C3B2 --> |Random partner based on prefrence| C3B2A{Condition}
    C3B2A --> |Not Available|C3B2A1[NO]
    C3B2A --> |Available|C3B2A2[YES]

    C3B2A1 --> C3B2A1A{{Temp Msg: Looking for partner's}}
    C3B2A2 --> |Partner Choosen|C3B2A2A{{Conversation started}}

    C3B2A2A --> C3B2A2A1((End)):::termination

    C4 -->C4A{Condition}
    C4A --> |Not Connected|C4B1[NO]
    C4A --> |Connected|C4B2[YES]

    C4B1 --> C4B1A{{Error: User not connected}}
    C4B2 --> C4B1B{{Profile Shared}}


    classDef entryPoint fill:#009c11, stroke:#42FF57, color:#ffffff
    classDef termination fill:#bb0007, stroke:#E60109, color:#ffffff
```

## Project Structure
```
|-- app.py
|-- info.py
|-- database.py
|-- readme.md
|-- requirements.txt
```

Give it a star 
--------------
Did you find this information useful, then give it a star 


Credits
-----------
All the credits to [mramitdas](https://github.com/mramitdas)
