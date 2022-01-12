# Create a ubuntu base image with python 3 installed
FROM python:3.9.9

# Set the working directory
WORKDIR /

# Copy all the files
COPY . .

# Install dependencies
RUN apt-get -y update
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install -r requirements.txt

# Enter entry point parameters executing the container
ENTRYPOINT ["python", "./main.py"] 

# Expose the required port
EXPOSE 5000

#Run the command
# CMD gunicorn main:app