GAME LOGIC DEBUGGING TEST

WHAT THIS VERSION DOES
- One laptop runs the website on your local Wi-Fi.
- Attendees open the test in a browser, enter a team name, answer 30 questions, and submit.
- The organizer can edit each question, add an image, set the time limit, start or pause the test, review answers, and download a CSV.
- The default time limit is 120 minutes (2 hours).

START ON THE HOST LAPTOP (WINDOWS)
1. Extract this folder.
2. Make sure Python 3 is installed.
3. Double-click start_test.bat and allow Python through Windows Firewall on Private networks if asked.
4. On the host laptop, open http://localhost:8000/admin .
5. Admin username: admin   Password: 4826
6. Set the time, edit questions, and upload images in the admin page. Images can be PNG, JPG, WEBP, or GIF, up to 8 MB each.
7. Select Start test for attendees when you are ready. Until then, attendees see a waiting screen.
8. Give attendees the host laptop's local IPv4 address, for example http://192.168.1.20:8000
   Find it by opening Command Prompt and entering: ipconfig
   Use the IPv4 Address for the Wi-Fi adapter. Everyone must be on the same Wi-Fi.

BEFORE THE EVENT
- Change admin_password in config.json from 4826 to a private password.
- Keep the host laptop awake and connected to Wi-Fi.
- Open the attendee link once from another device to check that the network allows connections.
- Save submissions using Download CSV before closing the server. submissions.json is also stored in this folder.

IMPORTANT
The site requests fullscreen at test start. If the local Wi-Fi address blocks that request, attendees can press F11 to enter browser fullscreen. When browser fullscreen is available, the test pauses if a fullscreen exit is detected. Browsers always let users exit fullscreen or switch apps, so a regular website cannot lock a laptop to the test. Use managed kiosk devices if strict lockdown is required. The one-submission rule uses a browser-profile ID stored in local storage and on the server; clearing browser data or switching browsers can create a new ID. The admin page uses basic password protection and should only be used on a trusted event network.

Fullscreen monitoring: the admin dashboard now shows attendee fullscreen exits/returns and tab visibility events, updating every few seconds. This depends on the browser Fullscreen API; browser-level F11 fullscreen may not be detectable on all browsers.
