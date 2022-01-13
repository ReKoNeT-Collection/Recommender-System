# Recommender System as a Decision Support for Product Machine Allocation

This code shows a Demonstrator to allocate products to machines. It is based on implicit learning. The system expects a history of product and machines (machine id) which produced them as a data series. Additionally, a file is needed listing the link between machine id and machine type/group. The software can be deployed as a docker container. Example data files can be found in the source folder.
    

# How to use it

For the use of this software python is needed. Version 3.8.3 is working. A list of required packages is provided in the requirements.txt.

The code can also be run via docker directly by using
```
docker-compose up
```
The service runs on port 5000. The login is user and password. CAUTION: This should be changed in the Demonstrator.py file when using in an unprotected environment!

On the frontend, historic data in a csv format must be uploaded to train the system. Afterwards, product ids can be requested and possible machines (historic and recommended) are presented. Typically, the software uses the machine group file directly from the folder locally. 

# Acknowldegement

This publication is based on the research and development project “ReKoNeT” which is / was funded by the German Federal Ministry of Education and Research (BMBF) within the “Innovations for Tomorrow’s Production, Services, and Work” Program and implemented by the Project Management Agency Karlsruhe (PTKA). The author is responsible for the content of this publication.

More information about the project (only in German): http://projekt-rekonet.de/ 
