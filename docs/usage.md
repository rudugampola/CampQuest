# Usage

There are multiple ways to use this application. The following sections will guide you through the different ways to use this application.

## CLI
The application can be run from the command line interface (CLI). The CLI is the most common way to use this application.

## Docker
The application can be run in a Docker container. This is useful if you do not want to install the dependencies on your local machine. A Dockerfile is provided in the repository to build the Docker image.

## Cron Job
The application can be run as a cron job. This is useful if you want to run the application at specific intervals to check for availability. 

## Web Server
The application can be run as a Django web server. This is useful if you want to expose the application as a web service. The application can be accessed through a web browser. Please note the ```cli.py``` is a command line application that does not share code with the web server. The web server is a separate application that uses a separate codebase.