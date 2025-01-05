<div align="center">
<a href="https://github.com/rudugampola/Campsite-Finder">
  <img src="https://github.com/rudugampola/CampQuest/blob/main/camp/static/images/campquest.png?raw=true"
    width="200" height="200" alt="campquest">
</a>
</div>

---

This application scrapes the https://recreation.gov website and https://reservecalifornia.com for campsite availabilities.

This application uses data provided by the Recreation Information Database (RIDB). All the data currently available was downloaded from RIDB site on December, 2024 and was used to create the database used by this application.
<div align="center"><img src="https://github.com/user-attachments/assets/c8dd586f-8b14-45c1-810b-31b344ed6071" alt="recreation.gov logo" height="90"><img src="https://github.com/user-attachments/assets/62f4c6e3-fe64-4cf4-ab68-abee53c21e1b" alt="recreation.gov logo" height="200"></div>



Note: RIDB is a part of the Recreation One Stop (R1S) program, which oversees the operation of Recreation.gov -- a user-friendly, web-based resource to citizens, offering a single point of access to information about recreational opportunities nationwide. The data from RIDB served as an authoritative source of information and services for millions of visitors to federal lands, historic sites, museums, waterways and other destinations and activities.

The application has a web interface that is built using Django. The campsite data is stored in a SQLite database.
Additionally, the application has a CLI interface that can be used to search for campsite and automate the process of checking for campsite availabilities.

Project is still in development.
