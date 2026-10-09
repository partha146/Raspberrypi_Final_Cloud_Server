# Raspberry Pi Cloud Server: How it Works

Raspberry Pi website is a completely different kind of beast compared to your Park Findr app! While Park Findr is a complex, modern "Single Page Application" built with React, your Raspberry Pi server is a **Classic Server-Side Rendered (SSR) Application** built with Python. 

Here is exactly how it works and how it compares to your other app.

## 1. The Core Engine: Flask (Python)
Instead of using React and Vite, your Raspberry Pi server uses **Flask**, a lightweight Python framework. 
If you look at `app.py`, this single file acts as the entire brain of your website. It sets up a web server that listens for incoming requests (like when you type your Raspberry Pi's IP address into a browser) and decides what to do based on the URL.

## 2. Server-Side Rendering (Templates)
In Park Findr, the browser downloads React and uses JavaScript to build the buttons and text on your screen dynamically. 

In your Raspberry Pi server, this happens **on the server itself**. 
* When you visit the site, Flask looks into your `templates/` folder (like `drive.html` or `login.html`).
* It injects your files and data directly into the HTML using a templating engine (called Jinja).
* It then sends a finished, fully-built HTML webpage to your browser. The browser just displays it—it doesn't have to do any heavy lifting!

## 3. Storage: Filesystem vs. Databases
This is the biggest difference in how data is handled:
* **Park Findr** relies on complex databases (like MongoDB or Firebase Cloud Firestore) to store abstract data like user profiles, parking sessions, and slot statuses. 
* **Your Raspberry Pi Server** interacts directly with the **physical file system** of the Raspberry Pi. 
  * When you create a folder or upload a file, Python literally tells the Raspberry Pi's operating system to save the file on the hard drive/SD card inside the `uploads/` folder.
  * It uses Python's built-in `os` and `shutil` libraries to list directories, rename files, and delete them.
  * For user logins, it doesn't use a secure database service. It simply reads a standard text file called `users.txt` to check if a username and password match.

## 4. The Request Flow
Here is what happens when you use your Raspberry Pi cloud drive:
1. **Login**: You visit `/login`. Flask renders `login.html`. When you submit your details, Python opens `users.txt`, checks the password, and gives your browser a "session cookie" to remember you.
2. **Viewing Files**: You visit `/drive`. Python reads the physical `uploads` folder on the Pi, builds a list of files, calculates their sizes and icons, and passes that list to `drive.html` to generate the webpage.
3. **Uploading**: When you upload a file, it gets sent directly to Python. Python takes the raw data and saves it physically into the `uploads` folder.

## Summary Comparison

| Feature | Park Findr (React) | Raspberry Pi Server (Flask) |
|---|---|---|
| **Language** | JavaScript / React | Python |
| **Where UI is built** | In the user's browser (Client-Side) | On the server (Server-Side) |
| **Data Storage** | Cloud Database (Firebase) | Physical Hard Drive (`uploads/`) |
| **User Accounts** | Firebase Authentication | Simple Text File (`users.txt`) |
| **Complexity** | High (Many files, separate frontend/backend) | Low (One main `app.py` file) |

Your Raspberry Pi app is a fantastic example of a traditional, robust web application. It acts exactly like a mini Google Drive that you control completely from your own hardware!
