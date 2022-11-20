# ClassFinder
An informational web app built to find empty classrooms in my University during specific periods of time.<br/>

Also provides information about lectures and instructors. <br/>

For an online demo click this link: http://halmoos.pythonanywhere.com/  <br/>

## How to use:

   Importing the database: <br/>
   1- Copy the code from 'DBDump.sql'. <br/>
   2- Paste the code into a MySQL terminal or a script and execute the script. <br/>
   3- User: "test" Password: "test" is available for testing
   
   In your text editor: <br/>
   1- Make the required changes to connect to your own MySQL database
   ```
   database = mysql.connector.connect(host="localhost",
                                   user="YOURUSER",
                                   password="YOURPASS",
                                   database="classroom")
   ```
   2- Run app.py and the website will be running at http://127.0.0.1:5000 <br/>
   
