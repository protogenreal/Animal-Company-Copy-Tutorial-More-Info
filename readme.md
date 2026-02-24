# Clone OG Animal Company (Xera Backend)

CREDITS:

Xera - Developer  
Protogen - Adding to guide

1. Install Base APK & Gamedata
- Use QuestAppVersionSwitcher to get target APK version
- Go to the /gamedata folder in this repo and download the wanted game data (only a few are available)

2. Decompile APK
- Use APKToolGUI or similar to unpack

3. Patch Server URL
- Open global-metadata.dat in MetaDataStringEditor
- Ctrl+F:
  https://animalcompany.us-east1.nakamacloud.io
- Replace with:
  Your hosted backend url if self hosting
- For free hosting go to "pythonanywhere.com" and then make an app and make sure you choose flask and the latest python
- Then make 2 new folders named "files" and then inside the files folder make a new one called "gamedata" (without quotations for both) and make sure to put your update zip in there
- and make sure you change it in the backend too! (default is zombie update) (or ask ai to do it for you idfc)

- Or go to /native-lib patch native-lib.cpp for your url and recompile (THIS IS THE ONLY WAY TO DO IT ON NEWER VERSIONS PAST LAVA)

4. Auth
- For your servers to work you need to change photonappsettings in assets/bin/data/globalgamemanagers
- Replace the first with a Photon Fusion 2 app id and the second with a Photon Voice app id
- Save that

4.1. Inject App ID
- Open assets/bin/data/globalgamemanagers in UABEA
- Ctrl+F: OculusPlatformSettings ? Extract as raw
- Open extracted .dat in HxD
- Replace Meta App ID with your own from developer.oculus.com

5. Photon Auth
- In game it will just say "Connecting" then "Disconnected" this is because you have not setup photon auth
- Go to the backend find "'photonAppID': '', 'photonVoiceAppID': ''," and add your Photon Fusion 2 app id then Photon Voice id
- Go to photon website and make sure you can see your Fusion 2 app
- Press manage then add a custom authentication provider (Custom URL or sumn like that)
- Set the link to *yourlink*/auth
- Now authentication should work!

7. Rebrand Package Name
- Change:
  woosterGames.animalCompany
- Edit in AndroidManifest.xml and apktool.yml

7. Upload to Meta
- Sign in to developer.oculus.com
- Build and sign APK
- Upload to App Lab

8. Fix Gamedata
- In the backend there is still xevas link (that is down) so change that to yours (link: https://xeracompany.pythonanywhere.com/game-data-prod.zip)

9. Unobfuscate
- AI can unobfuscate but you need to remove the comments at the top or it will NOT do it! (and ask it to unhardcode all of it as it will give the same account for EVERYONE!)

If you run into issues feel free to make an issue then I will try my best to help (i have only gotten this to work as of writing this so yeah)
