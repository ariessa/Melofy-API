# Melofy API

An RESTful API in Python for generating melody from supplied audio file link.

</br>

## Deploy

</br>

### Deploy Flask app locally

</br>

1. Clone GitHub repository
```
git clone https://github.com/ariessa/melofy-api.git
```

2. Create new conda environment named `snakes` that contains Python 3.7
```
conda create -n snakes python=3.7
```

3. Activate new environment
```
conda activate snakes
```

4. Use pip to install packages
```
pip install flask gunicorn magenta azure-storage-blob audio-to-midi timidity
```

5. Run flask app
```
flask run
```

Congratulations, you just run the Flask app locally!

</br>


### Expose Local Flask App to the Internet

</br>

1. Enable incoming traffic for port `5000`. This is done by navigating to Control Panel> System and Security > Windows Defender Firewall > Advanced Settings

![Advanced Settings](Advanced Settings.PNG)

</br>

2. In Advanced Settings, click on Inbound Rules


3. After clicking Inbound Rules, click on New Rules in the Action column

![Inbound Rules](Inbound Rules.PNG)

</br>

4. In New Inbound Rule Wizard, select Rule Type as Port and click Next

![New Inbound Rule Wizard](New Inbound Rule Wizard.PNG)

</br>

5. In New Inbound Rule Wizard, apply rule to TCP and set specific local port to 5000 and click Next

![Protocol and Ports](Protocol and Ports.PNG)

</br>

6. In New Inbound Rule Wizard, specify action to Allow the connection and click Next

![Action](Action.PNG)

</br>

7. In New Inbound Rule Wizard, specify profile for which rule applies to Private

![Profile](Profile.PNG)

</br>

8. Still in New Inbound Rule Wizard, specify name to Melofy API Port 500 and description to Allow inbound connection to local port 5000 using private connection and click Finish

![Name](Name.PNG)

</br>

9. Check New Inbound Rule in the list of Inbound Rules

![Check New Inbound Rule](Check New Inbound Rule.PNG)


Congratulations, you just exposed local port 5000 to the Internet!

</br>

### Start ngrok

</br>

**Basic Command**

</br>

Expose a web server on port 5000 of your local machine to the Internet
```
ngrok http 5000
```

</br>

**Advanced Commands**

</br>

1. Expose a web server on port 5000, set region to Asia Pasific, and subdomain to melofyapi
```
ngrok http -region=ap -hostname=melofyapi.ap.ngrok.io 5000
```

Congratulations, you can now access the Flask app at `http://melofyapi.ap.ngrok.io`!



